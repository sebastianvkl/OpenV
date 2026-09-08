import asyncio
import json
import time

import httpx
import pytest
from mcp.shared.auth import OAuthClientInformationFull,OAuthToken

from openv import dalus


@pytest.mark.parametrize('foreign_endpoint',[False,True])
def test_expired_session_refreshes_with_bound_issuer_and_without_browser_cookies(tmp_path,monkeypatch,foreign_endpoint):
    monkeypatch.setattr(dalus,'AUTH_DIR',tmp_path)
    monkeypatch.setenv('DALUS_MCP_URL','https://app.dalus.io/api/mcp')
    storage=dalus.FileTokenStorage();requests=[]
    async def prepare():
        await storage.set_client_info(OAuthClientInformationFull(client_id='test-client',
            redirect_uris=['http://localhost:8766/callback'],issuer='https://app.dalus.io/',token_endpoint_auth_method='none'))
        await storage.set_tokens(OAuthToken(access_token='old-test-access',refresh_token='test-refresh',token_type='Bearer',expires_in=3600))
    asyncio.run(prepare())
    (tmp_path/'dalus-expiry.json').write_text(json.dumps({'expires_at':time.time()-10}))
    def respond(request):
        requests.append(request)
        if request.method=='GET':
            return httpx.Response(200,json={'issuer':'https://app.dalus.io',
                'token_endpoint':'https://foreign.invalid/token' if foreign_endpoint else 'https://app.dalus.io/api/auth/mcp/token'},
                headers={'set-cookie':'AWSALB=test-lb-cookie; Path=/'})
        assert 'cookie' not in request.headers
        assert b'grant_type=refresh_token' in request.content
        return httpx.Response(200,json={'access_token':'new-test-access','token_type':'Bearer','expires_in':3600})
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(respond),**kwargs))
    if foreign_endpoint:
        with pytest.raises(RuntimeError,match='changed issuer'):asyncio.run(storage.get_tokens())
        assert len(requests)==1 # Never send credentials to an unbound destination.
    else:
        refreshed=asyncio.run(storage.get_tokens())
        assert refreshed.access_token=='new-test-access'
        assert refreshed.refresh_token=='test-refresh'
        assert asyncio.run(storage.get_tokens()).access_token=='new-test-access'
        assert len(requests)==2 # Reloading a fresh stored session needs no refresh.
