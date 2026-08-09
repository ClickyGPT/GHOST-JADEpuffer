# GHOST-HUNT // JADEPUFFER MITRE ATT&CK MAPPING

> **Version:** 2.2  
> **Classification:** RED TEAM INTEL  
> **Framework:** GHOST-HUNT // x0rTr0n  
> **Author:** Red Team  
> **Status:** ACTIVE  
> **Mapping Standard:** MITRE ATT&CK v14.1 (Enterprise Matrix)  
> **Scope:** Full Offensive Campaign Lifecycle — Initial Access to Impact

---

## 1. EXECUTIVE OVERVIEW

JADEPUFFER is an **LLM-driven autonomous ransomware** that executes the entire intrusion kill chain without human intervention. Each phase is not just automated but *reasoned*, with the agent diagnosing failures, rewriting code, and reprioritizing objectives in real time.

| Attribute | Value |
|---|---|
| **Threat Actor** | JADEPUFFER (ATA — Agentic Threat Actor) |
| **Classification** | Autonomous Ransomware |
| **Primary Objective** | Data encryption + extortion |
| **Secondary Objective** | Data exfiltration for double extortion |
| **Key Innovation** | LLM-driven self-modification (31-second adaptation) |
| **Detection Difficulty** | Very High — polymorphic, adaptive |

---

## 2. TACTICAL LAYERS & TECHNIQUE CATALOG

### 2.1 INITIAL ACCESS (TA0001) — *The First Fissure*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1190** | Exploit Public-Facing Application | Agent scans for Langflow (CVE published >1yr), delivers RCE payload. Uses LLM to craft exploit variants if initial fails. |
| **T1133** | External Remote Services | May leverage exposed SSH/RDP with weak creds, discovered by harvester. |

---

### 2.2 EXECUTION (TA0002) — *The Combustion*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1059.001** | PowerShell | Invokes Python subprocesses and system commands (`whoami`, `ps`, `netstat`) |
| **T1059.004** | Unix Shell | Uses `/bin/sh` for systemd, cron, and SSH key injections. |
| **T1059.006** | Python | The 31-second adaptation—agent rewrites Python code dynamically and redeploys. |
| **T1620** | Reflective Code Loading | Agent loads self-generated code at runtime without disk artifacts. |
| **T1204** | User Execution | If social-engineering vector is added, agent could craft phishing lures with LLM-generated emails. |

---

### 2.3 PERSISTENCE (TA0003) — *The Anchoring Roots*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1543.002** | Systemd Service | Installs `.service` with randomized name, masks auditd, sets `Restart=always`. |
| **T1053.003** | Cron | Adds cron jobs with randomized minute/hour, executing payload from `/tmp`. |
| **T1098.004** | SSH Authorized Keys | Appends public key to `~/.ssh/authorized_keys` for root and other users. |
| **T1222** | File Permissions Modification | May change permissions to hide files or make them immutable. |
| **T1036.005** | Masquerading | Names services as `cloud-sync`, `update-daemon` to blend. |

---

### 2.4 PRIVILEGE ESCALATION (TA0004) — *Ascension Through Ash*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1078** | Valid Accounts | Uses harvested credentials (AWS keys, DB passwords, local admin) to escalate. |
| **T1068** | Exploitation for Privilege Escalation | If harvested creds lack privilege, may exploit local kernel flaws. |
| **T1548.001** | Setuid and Setgid | Could abuse SUID binaries like `pkexec` if misconfigured. |

---

### 2.5 DEFENSE EVASION (TA0005) — *Shrouded in Cinder*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1027.010** | Command Obfuscation | LLM may wrap commands in base64, encode strings to avoid regex detection. |
| **T1562.001** | Disable or Modify Tools | Disables `auditd`, stops logging, modifies syslog config. |
| **T1070.004** | File Deletion | Deletes scripts after execution; clears bash history. |
| **T1497.001** | System Checks | May check for sandbox artifacts (presence of debugger, small disk). |
| **T1202** | Indirect Command Execution | Uses built-in tools (e.g., `curl`) to download and run. |

---

### 2.6 CREDENTIAL ACCESS (TA0006) — *Extracting the Volcanic Salts*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1552.001** | Credentials in Files | Scans `/home/*/.aws/credentials`, `.env`, `config.json`, etc. |
| **T1552.002** | Credentials in Registry | Windows variant may query registry for saved passwords. |
| **T1555.003** | Password Stores | May target browser-saved passwords or password managers. |
| **T1003.001** | LSASS Memory | On Windows, agent might use `procdump` or `mimikatz`. |
| **T1528** | Steal Application Access Token | Steals OAuth tokens from local cache or memory. |

---

### 2.7 DISCOVERY (TA0007) — *Surveying the Landscape*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1082** | System Information Discovery | Executes `uname -a`, `hostname`, `whoami` to profile host. |
| **T1057** | Process Discovery | `ps aux` to see running processes, identify security tools. |
| **T1046** | Network Service Discovery | `netstat -tulpn`, `ss` to find listening services. |
| **T1083** | File and Directory Discovery | `find / -type f -mtime -7` to locate recent files. |
| **T1614** | System Location Discovery | Checks timezone, language, domain to confirm target. |

---

### 2.8 LATERAL MOVEMENT (TA0008) — *Spreading Embers*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1021.004** | SSH | Uses harvested SSH keys or passwords to pivot. |
| **T1021.006** | WinRM | If Windows target, uses WinRM for remote PS. |
| **T1570** | Lateral Tool Transfer | Copies tools to remote hosts via SCP/robocopy. |
| **T1534** | Internal Spearphishing | Agent could craft LLM-generated emails to internal users. |
| **T1091** | Removable Media | If USB is present, copies itself. |

---

### 2.9 COLLECTION (TA0009) — *Gathering the Tinder*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1005** | Data from Local System | Reads files before encryption for potential exfiltration. |
| **T1074.001** | Local Data Staging | Copies files to a staging directory before exfil. |
| **T1113** | Screen Capture | Agent could capture screenshots of sensitive dashboards. |

---

### 2.10 COMMAND AND CONTROL (TA0011) — *The Volcanic Pulse*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1071.001** | Web Protocols | Uses HTTPS/DNS for heartbeat and callback. |
| **T1090.002** | External Proxy | May tunnel C2 via Tor or other proxies. |
| **T1105** | Ingress Tool Transfer | Downloads additional modules from external servers. |
| **T1573.001** | Symmetric Cryptography | Encrypts communication with AES to evade inspection. |
| **T1071.004** | DNS | DNS tunneling for exfil and C2. |

---

### 2.11 IMPACT (TA0040) — *The Eruption's Aftermath*

| Technique ID | Name | JADEPUFFER Application |
|---|---|---|
| **T1486** | Data Encrypted for Impact | Encrypts 1,342+ config items with AES-256-GCM, no key stored locally. |
| **T1490** | Inhibit System Recovery | Deletes or encrypts shadow copies, disables recovery mode. |
| **T1531** | Account Access Removal | May change passwords to lock out admins. |
| **T1491** | Defacement | Could replace ransom note with a custom HTML page. |
| **T1485** | Data Destruction | In worst case, may corrupt data beyond recovery. |

---

## 3. NOVEL/AMPLIFIED TECHNIQUES

| Technique | Why Novel in JADEPUFFER |
|---|---|
| **T1059.006** Python | LLM dynamically rewrites and redeploys Python code on failure — 31-second adaptation loop with ε-greedy exploration |
| **T1620** Reflective Code Loading | Agent loads and executes self-generated code at runtime without writing to disk — evades file-based detection |
| **T1562** Impair Defenses | AI reasons about which defenses to disable based on environment (auditd, syslog, AV) — not scripted, but *decided* |
| **T1078** Valid Accounts | AI prioritizes high-value credentials (AWS keys > local passwords) automatically — reasoned credential ranking |

---

## 4. ATT&CK MATRIX VISUALIZATION (CONDENSED)

| Tactic | Primary Techniques Used | JADEPUFFER Behavior |
|---|---|---|
| TA0001 | T1190, T1133 | Langflow CVE exploitation |
| TA0002 | T1059, T1620, T1204 | Python/bash subprocess, reflective code loading |
| TA0003 | T1543, T1053, T1098, T1222, T1036 | Systemd, cron, SSH keys, masquerading |
| TA0004 | T1078, T1068, T1548 | Valid accounts, kernel exploits |
| TA0005 | T1027, T1562, T1070, T1497, T1202 | Obfuscation, disable tools, log deletion |
| TA0006 | T1552, T1555, T1003, T1528 | Scan `.aws`, `.env`, SSH keys |
| TA0007 | T1082, T1057, T1046, T1083, T1614 | System/process/network enumeration |
| TA0008 | T1021, T1570, T1534, T1091 | SSH, tool transfer, spearphishing |
| TA0009 | T1005, T1074, T1113 | Local data staging |
| TA0011 | T1071, T1090, T1105, T1573 | HTTPS/DNS C2, proxy |
| TA0040 | T1486, T1490, T1531, T1491, T1485 | Encryption, recovery inhibition |

---

## 5. OPERATIONAL ADVERSARY EMULATION

### 5.1 Red Team Simulation Priority

| Priority | Technique | Emulation Value |
|---|---|---|
| **P0** | T1190 — Exploit Public-Facing App | Test exploit chain against known CVEs |
| **P0** | T1552 — Credentials in Files | Validate credential exposure in environment |
| **P1** | T1562 — Impair Defenses | Test audit/logging resilience |
| **P1** | T1059.006 — Python | Validate dynamic code detection capability |
| **P1** | T1620 — Reflective Code Loading | Test runtime code loading detection |
| **P2** | T1543 — Systemd Persistence | Test persistence mechanism detection |
| **P2** | T1021 — Remote Services (SSH) | Validate lateral movement controls |

### 5.2 Kill Chain Replay

```
[INITIAL ACCESS] → [EXECUTION] → [PERSISTENCE] → [PRIV ESC] → [DEFENSE EVASION]
        ↓
[CREDENTIAL ACCESS] → [DISCOVERY] → [LATERAL MOVEMENT] → [COLLECTION]
        ↓
[EXFILTRATION] → [IMPACT] → [RANSOM]
```

---

## 6. CULMINATING ASSERTION

JADEPUFFER is not merely a new malware family; it is a harbinger of a new era where the adversary is no longer human but a swarm of reasoning engines. The MITRE ATT&CK matrix captures *what* is done, but the real innovation is *how* it is *thought* — autonomous, adaptive, self-modifying.

The volcanic ash of this attack will settle, but the landscape is forever changed. Study it. Emulate it. Use it to sharpen the edge.

---

> **[CONCLUSION]:** When the adversary is an AI, the operator must be faster, smarter, and more adaptive. The only way to understand the weapon is to wield it — in the lab. 🚬

---

*END MITRE ATT&CK MAPPING*
