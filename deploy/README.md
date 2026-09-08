# Single-host deployment

OpenV needs native CAD/solver libraries and bounded background execution. The
reference deployment uses one Ubuntu 24.04 host with Python 3.12, systemd and
Caddy. `bootstrap-ubuntu.sh` prepares the host without model/MCP credentials.

Build the frontend locally (`cd web && npm ci && npm run build`), copy `web/dist`
to `/opt/openv/web/dist`, and restart `openv`. Serve it through Caddy with:

```caddy
your-domain.example {
    encode gzip zstd
    request_body {
        max_size 32KB
    }
    reverse_proxy 127.0.0.1:8000
}
```

Set `OPENAI_API_KEY`, `OPENV_STORE=dalus`, `DALUS_TEAM_ID`, and
`OPENV_PUBLIC_URL` in the root-readable `/etc/openv.env`. Provision the OAuth
client/token files into `/var/lib/openv/auth` owned by `openv`, mode 600. Never
put keys/tokens in Git, cloud-init/user-data, public artifacts, or frontend code.
The service reads them on restart. Use separate OAuth credentials for independently
running deployments; refresh-token rotation can invalidate duplicated sessions.

The public service runs one engineering process at a time, with daily admission,
experiment, model-call, and wall-time limits. Configure these limits to match the
operator's API budget. Persist `/var/lib/openv` across service updates. Restarted
jobs are marked interrupted; they do not resume or gain a verification verdict.

The host and its storage continue to incur normal hosting charges until stopped
or deleted. Keep provider resource IDs in private operator records; the public
repo contains no credentials or shared-infrastructure identifiers. Retain/download
artifacts before deleting the host.
