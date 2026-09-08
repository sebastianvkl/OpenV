"""Dalus transport and OAuth. Engineering operations use MCP exclusively.

Tool mappings are populated after authenticated discovery, never guessed.
Credentials and discovered private responses stay in the ignored .openv folder.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

AUTH_DIR = Path(os.environ.get("OPENV_AUTH_DIR", ".openv"))


class FileTokenStorage:
    def __init__(self,allow_reauthorization=False):
        self.allow_reauthorization=allow_reauthorization

    def _read(self, name, schema):
        path = AUTH_DIR / name
        return schema.model_validate_json(path.read_text()) if path.exists() else None

    def _write(self, name, record):
        AUTH_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = AUTH_DIR / name
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(record.model_dump_json())

    async def get_tokens(self):
        tokens=self._read("dalus-tokens.json", OAuthToken)
        if not tokens:return None
        expiry=AUTH_DIR/"dalus-expiry.json"
        expires_at=json.loads(expiry.read_text()).get("expires_at",0) if expiry.exists() else 0
        if expires_at>time.time()+120:return tokens
        # MCP 1.30 does not restore persisted token expiry and treats a resource
        # 401 as a new interactive authorization. Refresh before opening a short
        # MCP session. No engineering data is accessed through these OAuth calls.
        info=await self.get_client_info()
        if not tokens.refresh_token or not info or not info.issuer:
            if self.allow_reauthorization:return None
            raise RuntimeError("Dalus session expired; run python -m openv.dalus login")
        issuer=str(info.issuer).rstrip("/")
        expected=os.environ.get("DALUS_MCP_URL","https://app.dalus.io/api/mcp")
        origin=urlsplit(expected)
        if issuer!=f"{origin.scheme}://{origin.netloc}" or origin.scheme!="https":
            raise RuntimeError("Stored Dalus OAuth issuer does not match the configured service")
        async with httpx.AsyncClient(timeout=20,follow_redirects=False) as client:
            response=await client.get(issuer+"/.well-known/oauth-authorization-server")
            response.raise_for_status();metadata=response.json()
            endpoint=urlsplit(metadata["token_endpoint"])
            if str(metadata.get("issuer","")).rstrip("/")!=issuer or (endpoint.scheme,endpoint.netloc)!=(origin.scheme,origin.netloc):
                raise RuntimeError("Dalus OAuth metadata changed issuer or token origin")
            # Discovery adds load-balancer cookies. This registered CLI uses
            # refresh-token authentication, not browser cookie authentication.
            client.cookies.clear()
            response=await client.post(metadata["token_endpoint"],data={"grant_type":"refresh_token",
                "refresh_token":tokens.refresh_token,"client_id":info.client_id,"resource":issuer+"/"})
            if response.status_code!=200:
                if self.allow_reauthorization:return None
                raise RuntimeError(f"Dalus refresh rejected (HTTP {response.status_code}); run python -m openv.dalus login")
            fresh=OAuthToken.model_validate(response.json())
            if not fresh.refresh_token:fresh=fresh.model_copy(update={"refresh_token":tokens.refresh_token})
            await self.set_tokens(fresh)
            return fresh

    async def set_tokens(self, tokens):
        self._write("dalus-tokens.json", tokens)
        path=AUTH_DIR/"dalus-expiry.json"
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,"w") as stream:
            json.dump({"expires_at":time.time()+(tokens.expires_in or 0)},stream)

    async def get_client_info(self):
        return self._read("dalus-client.json", OAuthClientInformationFull)

    async def set_client_info(self, client_info):
        self._write("dalus-client.json", client_info)


async def unavailable_redirect(url):
    raise RuntimeError("Dalus authorization required. Run: python -m openv.dalus login")


@asynccontextmanager
async def session(redirect=unavailable_redirect, callback=None):
    url = os.environ.get("DALUS_MCP_URL", "https://app.dalus.io/api/mcp")
    auth = OAuthClientProvider(
        server_url=url,
        client_metadata=OAuthClientMetadata(
            client_name="OpenV engineering pipeline",
            redirect_uris=["http://localhost:8766/callback"],
            grant_types=["authorization_code", "refresh_token"], response_types=["code"],
            token_endpoint_auth_method="none", scope="openid profile email offline_access mcp:read mcp:write"),
        storage=FileTokenStorage(allow_reauthorization=callback is not None), redirect_handler=redirect, callback_handler=callback,
    )
    async with httpx.AsyncClient(auth=auth, timeout=60) as client:
        async with streamable_http_client(url, http_client=client) as (read, write, _):
            async with ClientSession(read, write) as connection:
                await connection.initialize()
                yield connection


async def discover(connection):
    records, cursor = [], None
    while True:
        page = await connection.list_tools(cursor=cursor)
        records.extend(t.model_dump(mode="json") for t in page.tools)
        cursor = page.nextCursor
        if not cursor:
            break
    AUTH_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    (AUTH_DIR / "dalus-tools.json").write_text(json.dumps(records, indent=2))
    print(json.dumps({"connected": True, "tools": [r["name"] for r in records]}), flush=True)
    return records


async def login():
    loop = asyncio.get_running_loop()
    response = loop.create_future()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlsplit(self.path)
            if parsed.path != "/callback":
                self.send_error(404)
                return
            query = parse_qs(parsed.query)
            code, state = query.get("code", [None])[0], query.get("state", [None])[0]
            if not code:
                self.send_error(400, "Authorization did not complete")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>OpenV received the authorization callback.</h1><p>You can return to Codex. The client will validate the connection.</p>")
            loop.call_soon_threadsafe(lambda: response.set_result((code, state)) if not response.done() else None)

        def log_message(self, *_):
            pass  # Callback codes must never appear in logs.

    server = HTTPServer(("127.0.0.1", 8766), Handler)
    import threading
    threading.Thread(target=server.serve_forever, daemon=True).start()

    async def redirect(url):
        (AUTH_DIR / "dalus-login-url.txt").write_text(url)
        print(f"Open this authorization URL: {url}", flush=True)

    async def callback():
        return await asyncio.wait_for(response, timeout=900)

    try:
        async with session(redirect, callback) as connection:
            await discover(connection)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        asyncio.run(login())
    else:
        async def main():
            async with session() as connection:
                await discover(connection)
        asyncio.run(main())
