# GHOST-HUNT // C2 KITS — VALIDATION REPORT

> **Scope:** HTTPS Receiver (`GHOST-HUNT-C2-KIT/`) + DNS Tunnel (`GHOST-HUNT-C2-KIT-DNS/`)
> **Session:** 2026-08-10 — all tests run locally on the operator dev box (Git Bash / Windows, Python 3.14, `cryptography 47.0.0`)
> **Reference:** `DEPLOYMENT_CHECKLIST_C2_KITS.md` §0 — this file is the source of the measured throughput numbers it quotes.

---

## 1. QUALITY GATES (run before load testing)

| Gate | Command | HTTPS Kit | DNS Kit |
|---|---|---|---|
| Round-trip smoke | `python test/local_harness.py` / `local_dns_harness.py` | ✅ exit 0 | ✅ exit 0 |
| Cover self-test | `python test/local_harness.py --self-test-cover` | ✅ 6/6 caught | ✅ 6/6 caught |
| Ruff lint | `python -m ruff check *.py test/ --config ../pyproject.toml` | ✅ 0 findings | ✅ 0 findings |
| Pyright typecheck | `python -m pyright *.py --pythonversion 3.6` | ✅ 0 errors | ✅ 0 errors |
| GNU make | `make test / lint / typecheck / test-cover` | ✅ all pass | ✅ all pass |

> `run.sh` equivalents exist in both kit dirs for machines without make.

---

## 2. MEASURED THROUGHPUT — HTTPS KIT

Localhost, no TLS/nginx (raw handler on 127.0.0.1). Elapsed via `time`; throughput = payload / wall time.

| Test | Payload | Chunk size | Chunks | Elapsed | Throughput | Result |
|---|---|---|---|---|---|---|
| Baseline | 5 MB | 1 MB | 7 | ~4 s* | ~1.3 MB/s | ✅ sha256 match |
| **Stress** | **50 MB** | **1 MB** | **67** | **7.14 s** | **~7.4 MB/s** | ✅ sha256 match |
| **Ceiling** | **200 MB** | **4 MB** | **67** | **14.89 s** | **~14.1 MB/s** | ✅ sha256 match |

\* baseline elapsed not machine-timed (first run, pre-`time`); shown as estimate.

**Findings:**
- Larger chunks ≈ faster: 4 MB chunks nearly double throughput (14.1 vs 7.4 MB/s) — fewer POST round-trips, same chunk machinery.
- No ceiling hit at 200 MB — scales linearly with disk/bandwidth.
- Cover verified on every run (source overwritten + removed, hard-link witness).

**Reproduce:**
```bash
cd GHOST-HUNT-C2-KIT
python test/local_harness.py --size-mb 200 --chunk-mb 4   # 200 MB ceiling test
```

---

## 3. MEASURED THROUGHPUT — DNS KIT

Localhost direct-to-listener mode (UDP, no real resolver). Elapsed via `time`; queries/s = chunks / wall time.

| Test | Payload | Chunk chars | Chunks | Elapsed | Queries/s | Result |
|---|---|---|---|---|---|---|
| Baseline | 2 KB | 40 | 82 | ~6 s* | ~14 q/s | ✅ sha256 match |
| **Stress** | **20 KB** | **60** | **547** | **33.78 s** | **~16.2 q/s** | ✅ sha256 match, 547/547 ACK |
| **Ceiling** | **64 KB** | **60** | **1,748** | **100.40 s** | **~17.4 q/s** | ✅ sha256 match, 1,748/1,748 ACK |

\* baseline elapsed not machine-timed (first run, pre-`time`); shown as estimate.

**Findings:**
- Zero loss at scale: 1,748/1,748 queries ACKed — fileid + seq scheme holds.
- Rate is set by `--jitter`, not the client: at 0.01 s jitter ~17 q/s sustained; raising jitter to 1–5 s (production cover) drops rate to ~0.2–1 q/s.
- Practical channel: **~0.65 KB/s** at 0.01 s jitter for 64 KB / 100 s. Reserve for small high-value files or DNS-only-egress targets.

**Reproduce:**
```bash
cd GHOST-HUNT-C2-KIT-DNS
python test/local_dns_harness.py --size-kb 64 --chunk 60   # 64 KB ceiling test
```

---

## 4. CHANNEL CAPACITY DECISION TABLE (measured)

| Need | Channel | Measured capacity | Notes |
|---|---|---|---|
| Bulk exfil | HTTPS | **~14 MB/s** (4 MB chunks) | 200 MB in ~15 s |
| Small high-value files | DNS | **~0.65 KB/s** (0.01 s jitter) | 64 KB in ~100 s; tune `--jitter` up for cover |
| Stealth / DNS-only egress | DNS Method B | same as above | lowest detection profile |
| Full interactive tunnel | DNS Method A/C | n/a (tunnel, not exfil) | dnscat2 / iodine |

---

## 5. ENVIRONMENT FOOTPRINT (measured on this box)

| Asset | Detail |
|---|---|
| OS / shell | Windows (MINGW64 / Git Bash) |
| Python | 3.14 (`cryptography` 47.0.0 present) |
| Tooling | ruff 0.16.2, pyright 1.1.411, GNU make 4.4.1 (winget: `ezwinports.make`) |
| Ports used by harness | HTTPS auto-falls back from 8080; DNS from 5353 (mDNS) — never posts to unrelated services |

---

> `[OP-ID: VALIDATION-C2]` | `[PHASE]: III — WEAPONIZATION VALIDATION` | `[STATUS]: VERIFIED`

> **[CONCLUSION]:** Both kits pass all quality gates and are characterized at scale — HTTPS 200 MB @ ~14 MB/s, DNS 64 KB across 1,748 queries with zero loss. Measured numbers recorded here for deployment planning. 🚬

*END VALIDATION REPORT*
