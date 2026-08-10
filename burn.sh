#!/usr/bin/env bash
# ──── GHOST-HUNT // C2 KIT — Takedown / Burn (Playbook §12.1.5) ────
# Run on the C2 server as root after data is verified and pulled.
#   bash burn.sh <domain>
set -euo pipefail

DOMAIN="${1:-${DOMAIN:-}}"
[[ -n "$DOMAIN" ]] || { echo "[!] Usage: bash burn.sh <domain>"; exit 1; }

echo "[*] Burning C2 for $DOMAIN"

# 1. Stop + disable handler
systemctl stop cdn-cache 2>/dev/null || true
systemctl disable cdn-cache 2>/dev/null || true

# 2. Shred data + handler, remove tree
shred -vfz /opt/c2/incoming/* 2>/dev/null || true
shred -vfz /opt/c2/handler.py 2>/dev/null || true
rm -rf /opt/c2

# 3. Remove systemd unit
rm -f /etc/systemd/system/cdn-cache.service
systemctl daemon-reload

# 4. Revoke cert + remove nginx site
certbot delete --cert-name "$DOMAIN" --non-interactive 2>/dev/null || true
rm -f /etc/nginx/sites-available/c2 /etc/nginx/sites-enabled/c2
nginx -t && systemctl restart nginx

# 4b. Close the firewall ports bootstrap-server.sh opened (leave ufw active, deny-all)
ufw delete allow 80/tcp  >/dev/null 2>&1 || true
ufw delete allow 443/tcp >/dev/null 2>&1 || true
ufw delete allow 22/tcp  >/dev/null 2>&1 || true

# 5. Local hygiene
unset HISTFILE
history -c 2>/dev/null || true
rm -f ~/.bash_history ~/.zsh_history

echo "[*] Burn complete. Verify:"
echo "  ☐ handler:   $(systemctl is-active cdn-cache 2>/dev/null || echo 'cdn-cache inactive')"
echo "  ☐ incoming:  $(ls /opt/c2/incoming 2>/dev/null | wc -l) files remain (expect 0)"
echo "  ☐ nginx:     $(ls /etc/nginx/sites-enabled/ 2>/dev/null | tr '\n' ' ')"
echo "  ☐ certs:     $(certbot certificates 2>/dev/null | grep -c 'Certificate Name' || true) remain (expect 0)"
echo "  ☐ NEXT:      terminate the VPS from the provider panel"
