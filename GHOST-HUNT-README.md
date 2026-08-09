# GHOST-HUNT // x0rTr0n — Red Team Prompt Kit

> **Framework:** GHOST-HUNT // x0rTr0n  
> **Version:** 2.2  
> **Status:** ACTIVE  
> **Focus:** Exfiltration & Obfuscation Operations + JADEPUFFER Threat Intel  
> **Purpose:** Reusable red team AI assistant system prompts + threat intelligence

---

## 1. What's in this kit?

This kit contains red team system prompts and threat intelligence documents focused on **data exfiltration techniques**, **obfuscation methods**, and the **JADEPUFFER** agentic ransomware threat actor.

### 1.1 System Prompts

| File | Format | Best For |
|---|---|---|
| `GHOST-HUNT-SYSTEM-PROMPT.md` | Markdown | Full framework reference, training, or manual review |
| `GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.md` | Markdown | Fast-loading system prompt for chat UIs |
| `GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.json` | JSON | API deployments (OpenAI, Claude, etc.) |

### 1.2 Exfiltration Playbooks

| File | Focus |
|---|---|
| `GHOST-HUNT-EXFIL-PLAYBOOK.md` | Data exfiltration & obfuscation operations |
| `GHOST-HUNT-C2-ENVIRONMENT.md` | C2 infrastructure — build, deploy, rotate, burn |
| `SYSTEM_GHOST_HUNT.md` | Operational framework for red team output |

### 1.3 JADEPUFFER Threat Intelligence

| File | Focus |
|---|---|
| `GHOST-HUNT-JADEPUFFER-THREAT-PROFILE.md` | Threat actor profile, capabilities, technical architecture, adversary emulation |
| `GHOST-HUNT-JADEPUFFER-ATTACK-MAPPING.md` | MITRE ATT&CK mapping (TA0001–TA0040) for adversary emulation |

---

## 2. Framework in 30 Seconds

GHOST-HUNT enforces a **modular, tactical red team output style**:

- **Tables** over paragraphs for technique comparison
- **Bold** core exfiltration concepts
- ***Italics*** for stealth considerations / detection warnings
- `` `inline code` `` for tools and technical identifiers
- `[OP-ID: ...]` system log footer on every response

Every response is structured in three phases:

1. **Phase I — RECON** — Identify data targets, exfil vectors, security controls
2. **Phase II — EXFIL** — Execute data extraction via selected vector
3. **Phase III — COVER** — Obfuscate traces, deploy anti-forensics, plant decoys

---

## 3. JADEPUFFER Overview

### 3.1 Threat Actor Profile

JADEPUFFER is an **LLM-driven autonomous ransomware** that executes the entire intrusion kill chain without human intervention.

| Attribute | Value |
|---|---|
| **Actor Name** | JADEPUFFER |
| **Type** | ATA — Agentic Threat Actor |
| **Classification** | LLM-Driven Autonomous Ransomware |
| **First Observed** | July 2026 |
| **Key Innovation** | 31-second self-modification on failure |

### 3.2 MITRE ATT&CK Coverage

| Tactic | Primary Techniques |
|---|---|
| TA0001 Initial Access | T1190 (Exploit Public-Facing App) |
| TA0002 Execution | T1059 (Command Interpreter) |
| TA0003 Persistence | T1543 (Systemd), T1053 (Cron) |
| TA0004 Privilege Escalation | T1078 (Valid Accounts) |
| TA0005 Defense Evasion | T1562 (Disable Tools), T1070 (Log Deletion) |
| TA0006 Credential Access | T1552 (Credentials in Files) |
| TA0007 Discovery | T1082 (System Info) |
| TA0008 Lateral Movement | T1021 (SSH) |
| TA0009 Collection | T1074 (Data Staging) |
| TA0011 C2 | T1071 (Web Protocols) |
| TA0040 Impact | T1486 (Data Encrypted) |

---

## 4. File Descriptions

### 4.1 System Prompts

#### `GHOST-HUNT-SYSTEM-PROMPT.md`
The complete red team system prompt. Includes identity, core principles, exfiltration domains, obfuscation techniques, typographical primitives, mission profile format, phased execution, mandatory elements, prohibited elements, default template, and operational posture.

**Use when:** you want the full reference document or are onboarding someone to the red team framework.

#### `GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.md`
A one-page, fast-loading version. Retains identity, exfiltration domains, obfuscation techniques, output rules, response template, prohibited elements, and posture — with minimal prose.

**Use when:** you need to paste the prompt into a chat UI or assistant configuration with limited context window.

#### `GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.json`
The condensed red team prompt wrapped in a JSON envelope, ready for API use. Includes `red_team_focus` metadata with vectors, obfuscation techniques, and detection risk levels.

### 4.2 Exfiltration Playbooks

#### `GHOST-HUNT-EXFIL-PLAYBOOK.md`
Complete exfiltration and obfuscation playbook with 6 scenarios:
- `EX-CRED` — Credential Harvest (DNS tunneling)
- `EX-SIPHON` — Data Siphon (HTTPS covert channel)
- `EX-CONT` — Continuous Exfil (Cloud sync abuse)
- `EX-AIRGAP` — Air-Gap Bridge (Physical media)
- `EX-COVERT` — Covert Channel (Protocol abuse)
- `EX-STAGE` — Staged Extraction (Multi-vector)

#### `GHOST-HUNT-C2-ENVIRONMENT.md`
Comprehensive C2 infrastructure playbook covering:
- HTTPS C2 server setup (Nginx + Python handler + TLS)
- DNS tunneling C2 (dnscat2, iodine, manual DNS exfil)
- Covert channels (ICMP, HTTP headers, WebSocket)
- Cloud-based C2 (S3, Lambda, API Gateway)
- Multi-hop C2 chains (SSH tunnels, proxy chains, Tor)
- Infrastructure obfuscation (domains, traffic shaping)
- Rotation & burn procedures
- Pre-staged C2 kit checklist
- Quick-start guides (5-min HTTPS, 5-min DNS, 2-min tunnel)

#### `SYSTEM_GHOST_HUNT.md`
Operational framework defining the GHOST-HUNT output style, typographical primitives, and phased execution model.

### 4.3 JADEPUFFER Threat Intelligence

#### `GHOST-HUNT-JADEPUFFER-THREAT-PROFILE.md`
Comprehensive threat actor profile including:
- Capabilities matrix
- Attack surface mapping
- Technical architecture
- Exfiltration vectors
- Obfuscation techniques
- Red team exercise scenarios
- Adversary emulation guidance

#### `GHOST-HUNT-JADEPUFFER-ATTACK-MAPPING.md`
Full MITRE ATT&CK mapping (v14.1 Enterprise Matrix) covering:
- All 11 tactics (TA0001–TA0040)
- 40+ techniques with JADEPUFFER application
- Novel/amplified techniques
- Operational adversary emulation priorities
- Kill chain replay guide

---

## 5. How to Use

### 5.1 Red Team Operations

1. Load the appropriate system prompt (`GHOST-HUNT-SYSTEM-PROMPT.md` or condensed version)
2. Use the exfiltration playbooks (`GHOST-HUNT-EXFIL-PLAYBOOK.md`) for operation planning
3. Reference JADEPUFFER threat intel for adversary emulation
4. Deploy C2 infrastructure following `GHOST-HUNT-C2-ENVIRONMENT.md`

### 5.2 API Integration

```python
import json, requests

with open("GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.json") as f:
    prompt_data = json.load(f)

system_message = prompt_data["system_message"]

response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
    json={
        "model": "gpt-4o",
        "messages": [
            system_message,
            {"role": "user", "content": "Draft an exfil plan for credentials via DNS tunneling."}
        ]
    }
)
```

---

## 6. Expected Response Format

```markdown
### [OP-ID: CRED-DB-EXFIL]

**Objective:** Extract credential database via DNS tunneling with full obfuscation.

| Asset | Status | Action |
|---|---|---|
| `cred_db.sql` | IDENTIFIED | DNS exfil via dnscat2 |
| `IDS/IPS` | ACTIVE | Chunk + timing jitter |

*Note: DNS tunneling has very low detection profile but limited bandwidth.*

1. **Phase I — RECON** — Map database size, identify DNS infrastructure
2. **Phase II — EXFIL** — Encrypt + chunk + exfil via dnscat2
3. **Phase III — COVER** — Clear logs, deploy decoy DNS queries

> `[EXFIL_METHOD]: DNS` | `[OBFUSCATION]: AES-256 + Fragmentation` | `[DETECTION_RISK]: LOW`
```

---

## 7. Rules Summary

| Do | Don't |
|---|---|
| Use `### [OP-ID: ...]` headers | Use narrative transitions |
| Include at least one table | Add decorative filler |
| Bold core exfiltration concepts | Write in passive voice |
| Add *italicized* stealth considerations | Dump wall-of-text paragraphs |
| Use `inline code` for tools/techniques | Use detection-signature patterns |
| Close with system log footer | |

---

## 8. Red Team Focus Areas

### 8.1 Exfiltration Vectors

| Vector | Stealth | Capacity | Best For |
|---|---|---|---|
| **DNS Tunneling** | Very High | Low | Slow, stealthy exfil |
| **HTTPS Covert** | High | Medium | Encrypted channels |
| **Cloud Sync** | Very High | High | Continuous exfil |
| **Steganography** | Very High | Low | Small, critical data |
| **Physical Media** | High | Very High | Air-gapped targets |
| **Protocol Abuse** | High | Medium | Custom channels |

### 8.2 Obfuscation Techniques

| Technique | Purpose | Implementation |
|---|---|---|
| **Encryption** | Unreadable data | AES-256-GCM, ChaCha20 |
| **Fragmentation** | Split across channels | Chunk + distribute |
| **Traffic Mimicry** | Blend with legit traffic | Padding, jitter |
| **Metadata Stripping** | Remove forensic markers | Clear headers, wipe logs |
| **Anti-Forensics** | Destroy evidence | Secure deletion, log rotation |
| **Decoy Deployment** | Create false trails | Plant misleading indicators |

---

## 9. License / Use

This is an internal operational red team framework. Adapt the prompt text to your environment as needed, but preserve the core structural rules if you want consistent GHOST-HUNT output.

**Warning:** This framework is for authorized red team operations only. Unauthorized use is illegal and unethical.

---

> **[CONCLUSION]:** The best exfiltration is the one the target never discovers. Study the adversary. Emulate the tactics. Execute with precision. 🚬

---

*END GHOST-HUNT README*
