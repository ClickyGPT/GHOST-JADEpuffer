#!/usr/bin/env bash
# ──── GHOST-HUNT // C2 KIT-DNS — Takedown / Burn (Playbook §12.2.5) ────
# Run on the C2 server as root after the operation is complete.
set -euo pipefail

# 1. Stop + disable dnscat2
systemctl stop dns-c2 2>/dev/null || true
systemctl disable dns-c2 2>/dev/null || true

# 2. Remove unit
rm -f /etc/systemd/system/dns-c2.service
systemctl daemon-reload

# 2b. Close the firewall port bootstrap-dns-server.sh opened (leave ufw active, deny-all)
#     If you deployed on a non-default PORT, delete that port instead.
ufw delete allow 53/udp >/dev/null 2>&1 || true
ufw delete allow 53/tcp >/dev/null 2>&1 || true

# 3. Local hygiene
unset HISTFILE
history -c 2>/dev/null || true
rm -f ~/.bash_history ~/.zsh_history

echo "[*] Burn complete. Verify:"
echo "  ☐ service:  $(systemctl is-active dns-c2 2>/dev/null || echo 'dns-c2 inactive')"
echo "  ☐ unit:     $(ls /etc/systemd/system/dns-c2.service 2>/dev/null || echo 'removed')"
echo "  ☐ NEXT:     let the domain expire or transfer to a burner registrar; terminate the VPS"
