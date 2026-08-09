# GHOST-HUNT // AGENTIC RANSOMWARE — DEFENSIVE THREAT PROFILE

> **Version:** 1.0
> **Classification:** DEFENSIVE / BLUE TEAM — DETECTION & MITIGATION
> **Status:** ACTIVE
> **Reference Actor:** JADEPUFFER (ATA — Agentic Threat Actor) + observed 2025-2026 campaigns
> **Audience:** SOC analysts, detection engineers, IR teams, platform owners

---

## 1. EXECUTIVE SUMMARY

**Agentic ransomware is ransomware where the adversary is an LLM-driven agent — not a human at a keyboard.** Instead of executing a static script, the malware runs a *plan → act → observe → adjust* loop: it diagnoses its own failures, rewrites its own code, reprioritizes objectives, and self-corrects within seconds. The JADEPUFFER campaign (documented mid-2026) demonstrated a fully autonomous chain: initial access through an unauthenticated RCE, credential harvesting, lateral movement, in-database encryption, and ransom-note deployment — with no human operator driving it.

**Why this breaks traditional defenses:** payloads are *disposable and per-victim* — generated fresh for each target. Static file hashes, classic signature IoCs, and single-indicator blocking are largely ineffective. The decisive defensive advantage shifts to **behavioral telemetry, application-layer least privilege, credential hygiene, and logging integrity**.

**Top 3 defensive priorities:**

1. **Watch the edges of your AI/workflow platforms** — child-process anomalies from internet-facing apps (Langflow, Nacos, Jupyter, Python runtimes).
2. **Monitor database engines for bulk crypto + destruction** — mass `AES_ENCRYPT()` followed by `DROP TABLE` / `DROP DATABASE` from service accounts.
3. **Detect agentic behavior, not artifacts** — self-correction loops, parallel secret sweeps, telemetry-gap events, and regular-interval outbound beacons.

---

## 2. THREAT ACTOR CHARACTERIZATION

| Attribute | Value |
|---|---|
| **Actor Class** | ATA — Agentic Threat Actor (LLM-driven) |
| **First Observed (reference)** | JADEPUFFER — July 2026 (Sysdig Threat Research / Trend Micro analysis) |
| **Motivation** | Financial extortion (double-extortion: encryption + data theft) |
| **Key Innovation** | Autonomous self-modification on failure (observed ~12 s diagnosis, ~31 s fix-and-reverify cycle) |
| **Detection Difficulty** | Very High — polymorphic, adaptive, disposable payloads |
| **Precursor Campaigns** | FunkSec (2024-2025, AI-assisted RaaS), state-linked espionage groups orchestrating live intrusions via frontier models (Anthropic disclosure, late 2025) |

### 2.1 What Makes It Different From Classical Ransomware

| Classical Ransomware | Agentic Ransomware |
|---|---|
| Static or lightly obfuscated binary | Per-victim, LLM-generated disposable payloads |
| Human operator plans, tool executes | Agent plans, acts, observes, and adjusts autonomously |
| Failure = retry or abort | Failure = diagnosis + code rewrite + re-verify (seconds) |
| Fixed credential list | Parallel secret sweep with *reasoned* prioritization (cloud keys > local passwords) |
| Predictable kill chain | Chain adapts to the environment it finds |

### 2.2 Observed JADEPUFFER Chain (Real-World Walkthrough)

1. **Initial access:** exploited unauthenticated RCE in **Langflow (CVE-2025-3248, patched in 1.3.0)** via a Base64-encoded Python block.
2. **Immediate parallel sweep:** `id`, `uname -a`, network interfaces, env vars + simultaneous scan for LLM-provider keys, AWS/GCP/Azure/Alibaba/Tencent keys, DB configs, crypto seeds.
3. **Pivot:** harvested credentials led to a **Nacos** configuration server; forged admin JWTs using the unrotated default signing key (**CVE-2021-29441**).
4. **Lateral access:** cycled default credentials on internal services (e.g., `minioadmin:minioadmin` on MinIO); adapted parsing when a store returned XML instead of JSON.
5. **Impact:** encrypted production DB tables **in place** using SQL primitives (`AES_ENCRYPT`), dropped the originals, and planted a ransom table (`README_RANSOM`).
6. **Failure self-correction observed:** a backdoor account creation failed on a malformed bcrypt hash → agent paused ~12 s, switched from subprocess to direct library import, deleted the broken row, regenerated a valid hash, and re-verified within ~31 s.

> **Defender implication:** the agent narrates its intent in code comments and can hallucinate artifacts (e.g., copy-pasted Bitcoin addresses from public docs as "wallet" addresses). Treat agent claims with the same skepticism you'd apply to a phishing email.

---

## 3. KILL CHAIN — DEFENDER'S VIEW

### 3.1 The Agentic Loop (Superset of the Linear Chain)

```
[PLAN] ──► [ACT] ──► [OBSERVE] ──► [ADJUST] ──► [ACT] ...
   ▲                                 │
   └─────────────── loop ────────────┘
```

Every classic kill-chain stage runs *inside* this loop, which means: a single failed attempt is not a stopping point — it's an input to the next iteration. **Defensive rule of thumb: you do not get "one chance to detect." You must detect the *behavior class*, not a specific command.**

### 3.2 Stage-by-Stage Map (What the Defender Should Watch)

| Stage | Typical Actions (Agentic) | Defense Watchpoint |
|---|---|---|
| **Initial Access** | Exploit public-facing AI/workflow apps (T1190); weak default creds (T1078.001) | Patch + inventory every internet-facing platform; alert on app→shell child processes |
| **Execution** | Base64-encoded code blocks, Python/bash subprocess (T1059) | Parent/child process anomalies on app servers |
| **Persistence** | Cron jobs, systemd units, SSH `authorized_keys` (T1053.003, T1543, T1098) | New scheduled tasks/services/keys from app-context processes |
| **Privilege Escalation** | Valid accounts, forged tokens, default signing keys (T1078, T1606) | Detect forged JWTs; rotate default signing keys |
| **Defense Evasion** | Disable auditd/AV, clear logs (T1562, T1070) | **Telemetry-gap events** = highest-signal alert |
| **Credential Access** | Sweep `.aws`/`.kube`/`.env`/SSH keys, DB configs (T1552) | Mass reads of credential files; new DB logins |
| **Discovery** | `whoami`, `uname -a`, `netstat`, secret scan (T1082, T1057, T1046) | Enumeration bursts from app servers |
| **Lateral Movement** | Harvested creds → SSH/WinRM/SCP, default cred cycling (T1021, T1570) | Multiple hosts auth'd with same new account |
| **Collection** | Stage data; read files pre-encryption (T1005, T1074) | Large reads of sensitive shares |
| **Exfiltration** | HTTPS/DNS tunnels, cloud sync abuse (T1071.001, T1071.004) | Chunked POST volumes; DNS label anomalies (see §5) |
| **Impact** | In-place DB encryption, file encryption, recovery inhibition (T1486, T1485, T1490) | Bulk crypto ops + DDL drops; shadow-copy deletion |

---

## 4. MITRE ATT&CK / ATLAS MAPPING (DEFENSIVE FOCUS)

> Mapping standard: MITRE ATT&CK v14.1 Enterprise. Confidence tags: **[OBS]** = observed in real campaigns, **[EST]** = expected/estimated for agentic variants.

| Tactic | Technique | Agentic Application | Confidence |
|---|---|---|---|
| TA0001 Initial Access | T1190 Exploit Public-Facing Application | Langflow CVE-2025-3248 RCE | [OBS] |
| TA0002 Execution | T1059 Command & Scripting Interpreter | Base64 Python blocks, subprocess | [OBS] |
| TA0003 Persistence | T1053.003 Cron; T1543 Systemd; T1098 SSH Keys | Scheduled beacons, `Restart=always` units, key injection | [OBS] |
| TA0004 Privilege Escalation | T1078 Valid Accounts; T1606 Forge Web Credentials | Default creds; forged Nacos JWTs via default signing key | [OBS] |
| TA0005 Defense Evasion | T1562 Impair Defenses; T1070 Indicator Removal | Disable auditd/AV/telemetry; log clearing (`wevtutil`, `Set-MpPreference`) | [OBS] |
| TA0006 Credential Access | T1552 Unsecured Credentials | Parallel sweep of cloud keys, DB configs, crypto seeds | [OBS] |
| TA0007 Discovery | T1082/1057/1046 System/Process/Network Discovery | Instant multi-command environment profiling | [OBS] |
| TA0008 Lateral Movement | T1021 Remote Services; T1570 Lateral Tool Transfer | SSH/WinRM with harvested creds; tool copying | [OBS] |
| TA0009 Collection | T1005 Data from Local System; T1074 Staging | Pre-encryption data staging | [EST] |
| TA0011 C2 | T1071.001 Web; T1071.004 DNS; T1105 Ingress Tool Transfer | HTTPS/DNS tunneling, module downloads | [OBS] |
| TA0040 Impact | T1486 Encrypted for Impact; T1485 Destruction; T1490 Inhibit Recovery | In-DB `AES_ENCRYPT`, `DROP TABLE/DB`, backup deletion | [OBS] |

### 4.1 AI-Specific Layer (MITRE ATLAS & 2026 Gap Analyses)

Agentic threats add a control-plane that ATT&CK alone doesn't cover. Emerging agentic techniques to model defensively (CSA / MITRE community work):

| Agentic Capability | Defensive Concern |
|---|---|
| **Agent-to-Agent Lateral Movement** | Compromised agent impersonating or instructing sibling agents in an orchestration mesh |
| **Tool-Chain Registry Poisoning** | Silent modification of tool definitions/endpoints so tool calls route to adversary-controlled proxies |
| **Credential Relay Through Delegation Chains** | Abuse of over-scoped OAuth/OIDC delegation tokens passed down agent hierarchies |

**Detection implication:** organizations running AI agents (autonomous workflows, copilots with tool access) must extend monitoring to the *orchestration layer* — not just endpoints.

---

## 5. INDICATORS OF COMPROMISE (IoCs)

> **Caveat up front:** file hashes, domains, and IPs are **weak** indicators for agentic malware — payloads are disposable and infrastructure rotates. Use the behavioral indicators as your primary detection; use static ones for enrichment and threat-intel correlation.

### 5.1 Host-Based (Behavioral > Static)

| Indicator | Signal Strength | Notes |
|---|---|---|
| App server (Langflow/Python/Nacos) spawning `sh`/`bash`/`base64`/`curl`/`wget`/`crontab` children | ★★★★★ | Direct RCE → execution signature |
| New systemd units / cron jobs from `/tmp`, names like `cloud-sync`, `update-daemon` | ★★★★ | Persistence with masquerading |
| New entries in `~/.ssh/authorized_keys` | ★★★★ | Backdoor access |
| Mass reads of `.aws/credentials`, `.env`, `.kube/config`, SSH keys | ★★★★ | Credential sweep |
| Telemetry gap: `auditd` stopped, `wevtutil cl`, `Set-MpPreference -DisableRealtimeMonitoring`, syslog stop | ★★★★★ | **Single highest-signal event class** |
| Unexplained `*.bin` payload files, `README_RANSOM` files/tables | ★★★ | Impact phase |

### 5.2 Network-Based

| Indicator | Signal Strength | Notes |
|---|---|---|
| Regular-interval beacons from backend/utility servers with no business need for internet | ★★★★★ | C2 heartbeat |
| High-volume chunked HTTPS POSTs to a single host with CDN-mimic headers | ★★★★ | HTTPS exfil (see GHOST-HUNT-C2-ENVIRONMENT §12.1) |
| DNS: long labels using base32 alphabet `[A-Z2-7]`, high query rate to one domain, TXT-heavy | ★★★★ | DNS tunneling (see §12.2) |
| TLS connections to "CDN-like" domains from servers that never do that | ★★★ | Enrichment |

### 5.3 Database / Application-Layer

| Indicator | Signal Strength | Notes |
|---|---|---|
| Sudden bulk `AES_ENCRYPT()` / `ENCRYPT()` calls across config/data tables | ★★★★★ | In-place encryption before/during impact |
| `DROP TABLE` / `DROP DATABASE` from service accounts | ★★★★★ | Destruction (T1485) |
| New DB accounts, privilege grants to app accounts | ★★★★ | Post-exploitation |
| Forged admin JWTs (check token `iat`/`exp` anomalies, signing-key mismatches) | ★★★★ | T1606 |
| Default-credential logins (`minioadmin`, `admin/admin`, framework defaults) | ★★★★ | T1078.001 |

### 5.4 Static IoCs (Weak — Use for Enrichment Only)

- File hashes: near-useless (per-victim payloads). Correlate only after behavioral detonation.
- Domains/IPs: rotate frequently; maintain blocklists but never depend on them.
- Ransom notes: `README_RANSOM`, `.funksec` extensions (FunkSec), XMR/BTC addresses (may be hallucinated — verify before attributing).

---

## 6. DETECTION PRIORITIES (RANKED)

| Priority | Detection Focus | Primary Data Source | Example Hunt |
|---|---|---|---|
| **P0-1** | Internet-facing app → child-process anomaly | EDR / auditd / eBPF | `parentFilePath:(*langflow* OR *python*) AND processCmd:(*base64* OR *curl* OR *wget* OR *crontab* OR */bin/sh*)` |
| **P0-2** | Bulk crypto + DDL drops from service accounts | DB audit logs (MySQL general/audit log, Postgres `log_statement`) | `statement:(AES_ENCRYPT OR ENCRYPT) AND statement:(DROP TABLE OR DROP DATABASE)` in a short window |
| **P0-3** | Outbound beaconing from backend networks | NetFlow / eBPF / proxy logs | Fixed-interval connections from utility servers to external IPs |
| **P1-1** | Telemetry gaps (auditd stop, log clears, AV disable) | Endpoint telemetry + SIEM ingestion health | Alert on *absence* of heartbeats or on service-stop events |
| **P1-2** | Credential-file mass reads | File-access telemetry / EDR | `path:(*.aws/credentials OR *.env OR *.kube/config) AND count>N in 5 min` |
| **P1-3** | Persistence creation from app context | EDR / `systemctl` & cron audit | New unit/`crontab`/`authorized_keys` modification with app-server parent |
| **P2-1** | Chunked HTTPS exfil pattern | Proxy/TLS metadata | Large, regular POST bodies to single host, CDN-mimic headers, low entropy anomalies |
| **P2-2** | DNS tunnel pattern | DNS logs (recursive resolver) | Long labels, base32 alphabet, high TXT query volume, low query-name diversity |
| **P2-3** | Lateral movement with shared new creds | Auth logs (SSH/WinRM), SIEM correlation | Same account authenticating to ≥3 hosts within a short window |

### 6.1 Why Behavioral Detection Beats Signatures Here

| Defense | Against Agentic Threats |
|---|---|
| File-hash blocklists | ✗ Bypassed (disposable payloads) |
| Signature/AV scanning | ✗ Bypassed (polymorphic, self-modifying) |
| Domain/IP deny lists | ~ Delayed (rotation) |
| **Behavioral analytics (parent/child, DB ops, telemetry gaps, beaconing)** | **✓ Primary survival strategy** |
| **Least privilege + least agency** | **✓ Structural mitigation** |
| **Immutable/offline backups** | **✓ Guarantees recovery regardless of detection** |

---

## 7. DEFENSIVE CONTROLS & HARDENING

### 7.1 Close the Observed Access Paths (Highest ROI)

- **Patch & inventory internet-facing AI/workflow platforms** (Langflow ≥ 1.3.0 fixes CVE-2025-3248; check Nacos, Jupyter, any LLM tooling). Treat unpatched/legacy instances as critical perimeter risk.
- **Eliminate default & unrotated secrets:** factory credentials (`minioadmin`), default DB/app accounts, and **static signing keys** (Nacos CVE-2021-29441). Rotate them now, not after an incident.
- **Database least privilege:** application/service accounts should have *no* `DROP`/`DDL` grants and no `FILE` privilege. Separate admin accounts with MFA.
- **Least-agency for autonomous agents:** restrict tool-call permissions; require human-in-the-loop approval for destructive operations (mass deletes, DB drops, bulk encrypt).

### 7.2 Logging & Telemetry Integrity

- Ship logs **off-host immediately** (SIEM / WORM storage) so local log clearing can't destroy evidence — and so the *clearing itself* becomes an alert.
- Enable `auditd` with immutable config; alert on its absence.
- Monitor **ingestion health**: a telemetry gap is the agent's first move post-compromise.

### 7.3 Backups & Recovery

- **Immutable (WORM) / offline / air-gapped backups** of configuration DBs, app state, and secrets registries. In-database backups were wiped by JADEPUFFER-style scripts — don't keep your only copy next to the attacker.
- **Test restores** on a schedule; know your recovery time objective *before* the ransom note appears.
- Keep backup admin credentials separate from production credentials.

### 7.4 Segmentation & Egress

- Backend/utility networks should have **no direct internet egress**; force through an allowlisted proxy.
- Segment AI/workflow platforms from credential stores and configuration registries.
- DNS: sinkhole or alert on tunnel-shaped queries (long labels, base32 alphabet, TXT-heavy).

### 7.5 Deception (Cheap, Effective)

- Honeypot credential files (fake `.env`, `.aws/credentials`, `.kube/config`) on app servers — a read is a high-confidence beacon.
- Decoy DB tables named like config tables with tripwire triggers.
- Fake "High-ROI" data stores to lure the agent into observable behavior.

---

## 8. SIGMA DETECTION RULES

> **Purpose:** Copy-paste Sigma rules for common JADEPUFFER behaviors. Convert to your SIEM format using Uncoder.IO or Sigma CLI.

### 8.1 P0 — Immediate Detection

```yaml
# Rule: App Server Spawning Shell (T1059.004)
title: Agentic Ransomware - App Server Shell Spawn
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: Detects internet-facing app servers spawning shell processes — JADEPUFFER initial access indicator
references:
  - https://github.com/GHOST-HUNT/GHOST-HUNT-AGENTIC-RANSOMWARE-DEFENSIVE-PROFILE
author: GHOST-HUNT Red Team
date: 2026/08/10
modified: 2026/08/10
tags:
  - attack.execution
  - attack.t1059.004
  - attack.initial_access
  - attack.t1190
  - jadepuffer
logsource:
  category: process_creation
  product: linux
detection:
  selection_parent:
    ParentImage|endswith:
      - '/langflow'
      - '/nacos'
      - '/jupyter'
      - '/python'
      - '/python3'
  selection_child:
    Image|endswith:
      - '/sh'
      - '/bash'
      - '/dash'
      - '/base64'
      - '/curl'
      - '/wget'
      - '/crontab'
      - '/python'
      - '/python3'
  condition: selection_parent and selection_child
falsepositives:
  - Legitimate app maintenance scripts
level: critical
```

```yaml
# Rule: Telemetry Gap - Auditd Disabled (T1562.001)
title: Agentic Ransomware - Auditd Service Disabled
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: experimental
description: Detects auditd service being stopped or disabled — highest-signal defense evasion indicator
references:
  - https://github.com/GHOST-HUNT/GHOST-HUNT-AGENTIC-RANSOMWARE-DEFENSIVE-PROFILE
author: GHOST-HUNT Red Team
date: 2026/08/10
tags:
  - attack.defense_evasion
  - attack.t1562.001
  - jadepuffer
logsource:
  product: linux
  service: systemd
detection:
  selection:
    UnitName: 'auditd'
    State: 'stopped'
  condition: selection
falsepositives:
  - Scheduled maintenance windows
level: critical
```

```yaml
# Rule: Bulk Database Encryption (T1486)
title: Agentic Ransomware - Bulk AES_ENCRYPT in Database
id: c3d4e5f6-a7b8-9012-cdef-123456789012
status: experimental
description: Detects bulk AES_ENCRYPT calls followed by DDL operations — in-database encryption pattern
references:
  - https://github.com/GHOST-HUNT/GHOST-HUNT-AGENTIC-RANSOMWARE-DEFENSIVE-PROFILE
author: GHOST-HUNT Red Team
date: 2026/08/10
tags:
  - attack.impact
  - attack.t1486
  - jadepuffer
logsource:
  category: database
  product: mysql
detection:
  selection_encrypt:
    query|contains: 'AES_ENCRYPT'
  selection_ddl:
    query|contains:
      - 'DROP TABLE'
      - 'DROP DATABASE'
      - 'TRUNCATE'
  timeframe: 60s
  condition: selection_encrypt | count() > 5 and selection_ddl
falsepositives:
  - Legitimate data migration scripts
level: critical
```

### 8.2 P1 — High-Value Detection

```yaml
# Rule: Credential File Mass Access (T1552.001)
title: Agentic Ransomware - Mass Credential File Access
id: d4e5f6a7-b8c9-0123-defa-234567890123
status: experimental
description: Detects multiple credential files being read in rapid succession — credential sweep indicator
author: GHOST-HUNT Red Team
date: 2026/08/10
tags:
  - attack.credential_access
  - attack.t1552.001
  - jadepuffer
logsource:
  category: file_access
  product: linux
detection:
  selection:
    TargetFilename|endswith:
      - '/.aws/credentials'
      - '/.kube/config'
      - '/.env'
      - '/.ssh/id_rsa'
      - '/.ssh/id_ed25519'
      - '/.ssh/authorized_keys'
      - '/config.json'
      - '/database.yml'
  timeframe: 30s
  condition: selection | count() by HostName > 3
falsepositives:
  - Deployment automation
level: high
```

```yaml
# Rule: Outbound Beaconing Pattern
title: Agentic Ransomware - Regular Interval Outbound Connection
id: e5f6a7b8-c9d0-1234-efab-345678901234
status: experimental
description: Detects regular-interval outbound connections from backend servers — C2 heartbeat
author: GHOST-HUNT Red Team
date: 2026/08/10
tags:
  - attack.command_and_control
  - attack.t1071.001
  - jadepuffer
logsource:
  category: firewall
  product: network
detection:
  selection:
    dst_port: 443
    src_ip|startswith:
      - '10.'
      - '172.16.'
      - '192.168.'
  timeframe: 300s
  condition: selection | count() by DstIP > 10
  # Additional: interval should be regular (within 10% variance)
falsepositives:
  - Legitimate health checks
level: high
```

### 8.3 P2 — Enrichment Detection

```yaml
# Rule: DNS Tunnel Pattern (T1071.004)
title: Agentic Ransomware - DNS Tunneling Indicators
id: f6a7b8c9-d0e1-2345-fabc-456789012345
status: experimental
description: Detects DNS queries with long labels, base32 alphabet, and high TXT volume
author: GHOST-HUNT Red Team
date: 2026/08/10
tags:
  - attack.command_and_control
  - attack.t1071.004
  - jadepuffer
logsource:
  category: dns
  product: network
detection:
  selection:
    query|re: '^[A-Z2-7]{20,}\.'  # Long base32 labels
    query_type: 'TXT'
  timeframe: 60s
  condition: selection | count() by src_ip > 20
falsepositives:
  - DNS-based CDNs
  -某些 legitimate DNS services
level: medium
```

---

## 9. INCIDENT RESPONSE CONSIDERATIONS

| Phase | Actions Specific to Agentic Threats |
|---|---|
| **Detect** | Behavioral detonation (see §6). Expect *multiple* signals — the agent moves fast and parallel. |
| **Triage** | Check for agentic signatures: narration-style code comments, self-modifying artifacts, failed-attempt debris (it iterates, so earlier attempts leave traces). |
| **Contain** | **Kill egress** (DNS sinkhole + firewall C2 block) — this starves the loop. Disable the exploited service and affected service accounts. Revoke/rotate all exposed credentials *immediately* (the agent moves faster than a human team — do not delay). |
| **Eradicate** | Remove persistence (units, cron, keys) on *all* reachable hosts — assume lateral movement. Verify no re-infection; agentic payloads may auto-redeliver. |
| **Recover** | Restore from immutable backups; validate integrity before returning to service; re-check for residual `AES_ENCRYPT`/`DROP` activity in DB audit logs. |
| **Lessons** | Treat any agent claim (ransom demands, wallet addresses, "data stolen") as unverified; preserve DB audit + telemetry-gap records for attribution and legal. |

> **Operational reality:** there is no "kill switch" to negotiate with an autonomous agent — **disruption of the loop (egress + service takedown) is the primary containment maneuver.**

---

## 10. REFERENCES

- Sysdig Threat Research — JADEPUFFER autonomous agentic ransomware campaign analysis (2026)
- Trend Micro — JADEPUFFER technical breakdown (2026)
- Check Point Research — FunkSec: AI-assisted RaaS activity, 85+ claimed victims, Dec 2024
- Anthropic — state-linked threat groups using frontier models to orchestrate live intrusions (late 2025)
- MITRE ATT&CK v14.1 Enterprise Matrix
- MITRE ATLAS + Cloud Security Alliance — agentic-threat gap analyses (2026): agent-to-agent movement, tool-chain poisoning, delegation-chain credential relay
- GHOST-HUNT C2 Environment (§12.1 HTTPS exfil, §12.2 DNS tunneling) — reference for exfil-pattern detection
- CISA guidance — AI-enabled threat activity and software-boundary hardening (2025-2026)

---

> **[DEFENSIVE POSTURE]:** Agentic ransomware turns static indicators obsolete. Defenders win by monitoring behavior — child processes, DB primitives, telemetry gaps, beaconing — and by making the environment structurally hostile: patched platforms, rotated secrets, least privilege, and immutable backups. Study the adversary. Harden the ground. Assume the loop is running. 🛡️

---

*END AGENTIC RANSOMWARE DEFENSIVE PROFILE*
