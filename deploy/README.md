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

For a private engineering host, set `OPENAI_API_KEY`, `OPENV_STORE=dalus`, `DALUS_TEAM_ID`, and
`OPENV_PUBLIC_URL` in the root-readable `/etc/openv.env`. Provision the OAuth
client/token files into `/var/lib/openv/auth` owned by `openv`, mode 600. Never
put keys/tokens in Git, cloud-init/user-data, public artifacts, or frontend code.
The service reads them on restart. Use separate OAuth credentials for independently
running deployments; refresh-token rotation can invalidate duplicated sessions.

The public demo must set `OPENV_READ_ONLY=1` in `/etc/openv.env` and leave
`OPENAI_API_KEY` empty. It serves recorded runs and artifacts, but every
`POST /api/runs` is rejected with HTTP 403 before any worker or artifact write,
including verification-only, fixture and repair requests. `/api/config` exposes
this mode so the UI shows recorded examples and local setup instructions.
Enforce the flag on the Python origin itself; hiding buttons or protecting only
the Vercel URL is insufficient. The deployed public demo has no model API key.

A private service with `OPENV_READ_ONLY=0` runs one engineering process at a time, with daily admission,
experiment, model-call, and wall-time limits. Configure these limits to match the
operator's API budget. Persist `/var/lib/openv` across service updates. Restarted
jobs are marked interrupted; they do not resume or gain a verification verdict.

The host and its storage continue to incur normal hosting charges until stopped
or deleted. Keep provider resource IDs in private operator records; the public
repo contains no credentials or shared-infrastructure identifiers. Retain/download
artifacts before deleting the host.

## Vercel website

The user-selected website host is Vercel. The repository-root `vercel.json`
installs/builds `web/` and serves `web/dist`. External rewrites forward API and
artifact requests to the Python host; run polling is explicitly uncached.
For a new installation, replace the two backend destinations in `vercel.json`
with your HTTPS engineering API origin. Keep its job admission/time/resource
limits enabled. Set `OPENV_PUBLIC_URL` on the Python host to the stable website
URL after deployment, so new Dalus evidence references use the public site.

Use `vercel login` and `vercel --prod` from the repository root, or import the
repository with its Vite configuration. `.vercelignore` excludes local secrets,
auth sessions, generated engineering artifacts and virtual environments. The
frontend contains no Astra/Dalus credentials; live jobs use the backend's
restricted environment and OAuth files.


Do not expose a run-enabled service with the operator's credentials to anonymous
visitors. Authentication or user-owned billing is a separate future feature.
The local app uses its own `.env` and may keep engineering enabled; the public
read-only flag is a deployment setting, not a hostname or browser-header check.
