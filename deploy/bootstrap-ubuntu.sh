#!/usr/bin/env bash
# Bootstrap an isolated Ubuntu 24.04 host. No credentials belong in this file.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3.12-venv python3-pip git caddy libgl1 libglu1-mesa libxrender1 libxext6 libgomp1
id openv >/dev/null 2>&1 || useradd --system --create-home --home-dir /var/lib/openv openv
git clone https://github.com/sebastianvkl/OpenV.git /opt/openv
python3.12 -m venv /opt/openv/.venv
/opt/openv/.venv/bin/pip install -e /opt/openv
install -d -o openv -g openv -m 700 /var/lib/openv/auth
install -d -o openv -g openv /var/lib/openv/artifacts
cat > /etc/openv.env <<'EOF'
OPENV_ARTIFACTS=/var/lib/openv/artifacts
OPENV_AUTH_DIR=/var/lib/openv/auth
OPENV_STORE=local
OPENV_MAX_DAILY_RUNS=20
OPENV_MAX_EXPERIMENTS=5
OPENV_RUN_TIMEOUT=1800
EOF
chmod 600 /etc/openv.env
cat > /etc/systemd/system/openv.service <<'EOF'
[Unit]
Description=OpenV engineering pipeline
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=openv
Group=openv
WorkingDirectory=/opt/openv
EnvironmentFile=/etc/openv.env
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/openv/.venv/bin/uvicorn openv.server:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=/var/lib/openv
MemoryMax=3G
TasksMax=256

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now openv
# Configure a verified public hostname and deploy web/dist before exposing Caddy.
systemctl stop caddy
touch /var/lib/openv/bootstrap-complete
