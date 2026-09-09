# Hosting OpenV

## Current public demo: static hosting

The public site uses Vercel Hobby and serves recorded files only. It requires no
EC2 host, serverless functions, API keys, OAuth session or active engineering
worker. Hobby usage caps still apply; free hosting is not unlimited bandwidth.

`npm run build:static --prefix web` builds the viewer, downloads the public archive
pinned in `deploy/static-demo.json`, checks its SHA-256 and each exported file,
and places its 20 run snapshots and artifacts in `web/dist`. The large immutable
archive is a GitHub Release asset, keeping generated geometry out of Git history.
Normal `npm run build --prefix web` remains the local live-engineering build.

Vercel routes the existing `/api/config`, `/api/runs` and `/api/runs/<id>` GET
paths to static JSON. Write methods return 403 using static routing. Artifact
paths stay unchanged. The viewer stops polling when `static_demo` is true.
No route forwards requests to the retired AWS origin.

For offline static builds, set `OPENV_STATIC_ARCHIVE` to a downloaded archive with
the pinned checksum. To publish a new snapshot, run `deploy/export-static-demo.py`
with a public artifact folder and its run-index JSON, then publish a new archive
asset and update the metadata. The exporter includes only the same file types as
the artifact API; credentials, operational logs and symlinks are excluded.
Historical evidence and candidate-package bytes must be preserved.

The AWS retirement backup is private local operator data, separate from the
public archive. Do not commit or upload its OAuth/configuration files.

## Optional private engineering host

The following setup is retained for users who choose to pay for a server that
executes native engineering tools. It is not required by the public demo.


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

If exposing this optional Python host as a recorded demo, set `OPENV_READ_ONLY=1` in `/etc/openv.env` and leave
`OPENAI_API_KEY` empty. It serves recorded runs and artifacts, but every
`POST /api/runs` is rejected with HTTP 403 before any worker or artifact write,
including verification-only, fixture and repair requests. `/api/config` exposes
this mode so the UI shows recorded examples and local setup instructions.
Enforce the flag on the Python origin itself; hiding buttons or protecting only
the Vercel URL is insufficient. The current static public demo does not run this service.

A private service with `OPENV_READ_ONLY=0` runs one engineering process at a time, with daily admission,
experiment, model-call, and wall-time limits. Configure these limits to match the
operator's API budget. Persist `/var/lib/openv` across service updates. Restarted
jobs are marked interrupted; they do not resume or gain a verification verdict.

The host and its storage continue to incur normal hosting charges until stopped
or deleted. Keep provider resource IDs in private operator records; the public
repo contains no credentials or shared-infrastructure identifiers. Retain/download
artifacts before deleting the host.

## Connecting a private live website

The repository's Vercel configuration intentionally contains no live backend
rewrites. A self-hosted live installation would need its own protected API origin,
explicit routing, authentication and operator-managed budgets. Do not expose an
anonymous run-enabled service with your API credentials. Local development on
127.0.0.1 remains the supported way to run new experiments with your own account.
