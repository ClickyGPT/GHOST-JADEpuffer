# GHOST-HUNT // INCIDENT RESPONSE PLAYBOOK

> **Version:** 1.0  
> **Classification:** OPERATIONAL  
> **Framework:** GHOST-HUNT // x0rTr0n  
> **Author:** IR Team  
> **Status:** ACTIVE  
> **Purpose:** Structured incident response playbook framework for rapid, consistent breach response.

---

## 1. FRAMEWORK IDENTITY

> *"In an incident, the first casualty is clarity. This playbook replaces panic with procedure."*

| Principle | Meaning | Result |
|---|---|---|
| **Modular** | Each playbook stands alone | No cross-referencing mid-crisis |
| **Tactical** | Action-first, not explanation-first | Zero decision-paralysis |
| **Structured** | Tables > paragraphs | Skanmmable under stress |
| **Traceable** | Every action logged | Full post-mortem audit trail |

---

## 2. INCIDENT CLASSIFICATION MATRIX

### 2.1 Severity Levels

| Severity | Code | Definition | Escalation SLA | Example |
|---|---|---|---|---|
| **Critical** | `SEV-0` | Active breach; data exfil; system-wide outage | **Immediate** (0 min) | Ransomware, production DB dump |
| **High** | `SEV-1` | Targeted attack; lateral movement; PII exposure | **15 min** | Phishing with credential theft, web shell |
| **Medium** | `SEV-2` | Suspicious activity; policy violation; malware (isolated) | **1 hour** | Single endpoint alert, failed brute-force |
| **Low** | `SEV-3` | Reconnaissance; informational; false-positive triage | **24 hours** | Port scan, spam, low-fidelity alert |

### 2.2 Severity Decision Tree

| Condition | Threshold | Severity |
|---|---|---|
| Active data exfiltration detected | Any volume | `SEV-0` |
| Ransomware encryption observed | Any systems | `SEV-0` |
| Production systems unavailable | > 50% of user base affected | `SEV-0` |
| PII / PHI / PCI data exposed | > 500 records | `SEV-0` |
| Supply chain compromise confirmed | Vendor advisory + org impact | `SEV-0` |
| Credential theft (privileged account) | Domain admin / root / global admin | `SEV-1` |
| Production systems degraded | 10–50% of user base affected | `SEV-1` |
| PII / PHI / PCI data exposed | 1–500 records | `SEV-1` |
| Targeted attack detected (pre-breach) | Reconnaissance confirmed | `SEV-1` |
| Single-endpoint malware (isolated) | No lateral movement | `SEV-2` |
| Suspicious activity, no confirmed breach | Anomalous but unverified | `SEV-2` |
| Port scan / low-fidelity alert | Informational only | `SEV-3` |
| BEC with confirmed financial transfer | Any amount | `SEV-0` |
| Cryptojacking across multiple hosts | 3+ instances | `SEV-1` |

*Note: When in doubt, escalate up. Downgrading severity requires IC + CISO approval.*

### 2.3 Incident Types

| Type | Code | Phase I Trigger | Default Severity |
|---|---|---|---|
| **Malware / Ransomware** | `IR-MAL` | AV alert, file encryption, C2 beaconing | `SEV-0` |
| **Phishing / Credential Theft** | `IR-PHISH` | User report, suspicious login, forwarded email | `SEV-1` |
| **Business Email Compromise** | `IR-BEC` | Wire-fraud attempt, executive impersonation, vendor payment change | `SEV-0` |
| **Data Breach / Exfiltration** | `IR-EXFIL` | DLP alert, unusual egress, DB dump | `SEV-0` |
| **Denial of Service** | `IR-DOS` | Availability drop, traffic spike, load balancer fail | `SEV-1` |
| **Insider Threat** | `IR-INSIDER` | Anomalous access, off-hours activity, USB insert | `SEV-1` |
| **Cryptojacking** | `IR-CRYPTO` | CPU spike, cloud billing anomaly, CSPM alert | `SEV-2` |
| **Web Application Attack** | `IR-WEB` | WAF alert, SQLi/XSS payload, shell upload | `SEV-1` |
| **Cloud / Infrastructure Misconfig** | `IR-CLOUD` | Public bucket, open security group, exposed secret | `SEV-1` |
| **Supply Chain Compromise** | `IR-SUPPLY` | Third-party advisory, poisoned update, vendor alert | `SEV-0` |

*Note: Default severity is a starting point. Escalate if scope exceeds initial assessment. Use the decision tree (2.2) to override defaults.*

---

## 3. TEAM ROLES & ESCALATION MATRIX

### 3.1 IR Team Structure

| Role | `ROLE_ID` | Responsibilities | On-Call |
|---|---|---|---|
| **Incident Commander** | `IC` | Coordinates response; declares severity; communications lead | **Always** |
| **Technical Lead** | `TL` | Forensics; containment; evidence handling | **Always** |
| **Communications Officer** | `CO` | Internal/external comms; stakeholder updates; PR liaison | Business hours |
| **Legal Counsel** | `LC` | Breach notification assessment; regulatory compliance | On-call |
| **SME (on-demand)** | `SME` | Domain-specific expertise (cloud, DB, app, network) | Escalation |

### 3.2 RACI (Per-Incident)

| Task | `IC` | `TL` | `CO` | `LC` | `SME` |
|---|---|---|---|---|---|
| Declare incident | **A** | **R** | C | I | I |
| Contain threat | **A** | **R** | I | I | C |
| Preserve evidence | I | **A/R** | I | C | C |
| Forensic analysis | I | **A/R** | I | I | C |
| Stakeholder notification | **A** | I | **R** | C | I |
| Regulatory reporting | C | I | **R** | **A** | I |
| Evidence handoff to legal | I | **R** | I | **A** | I |
| Root-cause analysis | I | **A/R** | I | I | C |
| Post-mortem | **A** | **R** | C | C | C |

*Key: **R**=Responsible (does the work), **A**=Accountable (approves/signs off — exactly one per task), **C**=Consulted, **I**=Informed*

### 3.3 Escalation Triggers

| Trigger | Escalate To | SLA |
|---|---|---|
| `SEV-0` declared | **CISO** | 5 min |
| `SEV-0` + data exfiltration confirmed | **CISO + CEO** | 15 min |
| `SEV-0` unresolved after 4 hours | **CEO + Board** | 4h |
| `SEV-1` unresolved after 24 hours | **CISO** | 24h |
| Regulatory notification required | **Legal Counsel** | 1h |
| Law enforcement engagement needed | **Legal Counsel + CISO** | 2h |
| Press / media inquiry received | **Communications Officer + CISO** | 30 min |
| Third-party vendor involvement | **CISO + Procurement** | 4h |

---

## 4. THE RESPONSE LIFECYCLE

```
[PREP] → [DETECT] → [CONTAIN] → [ERADICATE] → [RECOVER] → [POST-MORTEM]
```

| Phase | Objective | Key Output | Max Duration |
|---|---|---|---|
| **0 — Preparation** | Tools, contacts, runbooks in place | Pre-staged IR kit | N/A (continuous) |
| **I — Detection & Triage** | Confirm incident; assign severity | `[IR-<ID>]` opened | 30 min |
| **II — Containment** | Stop the bleeding; preserve evidence | Isolation complete | `SEV-0`: 1h / `SEV-1`: 4h |
| **III — Eradication** | Remove threat; harden surface | Root cause removed | `SEV-0`: 4h / `SEV-1`: 24h |
| **IV — Recovery** | Restore services; verify integrity | Service restored | `SEV-0`: 8h / `SEV-1`: 48h |
| **V — Post-Mortem** | Document; improve; prevent recurrence | Post-mortem report | 7 days post-recovery |

*Note: Phase V is not optional. Every `SEV-0` and `SEV-1` incident gets a post-mortem.*

---

## 5. INCIDENT PLAYBOOKS

### 5.1 `IR-MAL` — Malware / Ransomware

### [OP-ID: IR-MAL-RESPONSE]

**Objective:** Contain malware execution, prevent lateral spread, preserve forensic artifacts, and restore from clean backups.

| Asset | Status | Action |
|---|---|---|
| Affected host(s) | `COMPROMISED` | **Isolate immediately** — disable NIC, do NOT power off |
| Network segment | `AT-RISK` | Quarantine VLAN; block outbound C2 ports |
| Backups | `TO-VALIDATE` | Verify integrity of last-known-good snapshot |
| IOCs (hashes, IPs) | `COLLECT` | Submit to threat-intel; block at perimeter |

1. **Phase I — Detection & Triage**
   - Validate alert: cross-reference hash with `VirusTotal` and internal threat-intel
   - Trace initial execution vector to identify patient-zero
   - Capture volatile data: `process list`, `network connections`, `scheduled tasks`
   - Declare severity per decision tree (Section 2.2)

2. **Phase II — Containment**
   - Disable affected host NIC (`ip link set eth0 down` or equivalent)
   - Quarantine VLAN segment at switch level
   - Block IOCs at firewall / EDR / DNS filter
   - Force password reset for accounts active on affected host
   - Snapshot affected disk (forensic image before remediation)

3. **Phase III — Eradication**
   - Identify root cause (phishing link, drive-by download, RDP brute-force, USB)
   - Wipe and reimage affected host(s) from trusted baseline
   - Apply missing patches / close vector
   - Reset all credentials exposed to affected segment
   - Verify no persistence mechanisms survive (registry, cron, WMI, startup)

4. **Phase IV — Recovery**
   - Restore data from verified clean backup
   - Re-deploy host to production with enhanced monitoring
   - Monitor for 72 hours post-restoration
   - Validate AV/EDR signatures updated

5. **Phase V — Post-Mortem**
   - Timeline reconstruction
   - Control gap analysis
   - Update detection rules / playbook

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: EXECUTION_VECTOR` | `[PHASE]: I`

---

### 5.2 `IR-PHISH` — Phishing / Credential Theft

### [OP-ID: IR-PHISH-RESPONSE]

**Objective:** Identify compromised accounts, revoke sessions, assess data exposure, and block phishing infrastructure.

| Asset | Status | Action |
|---|---|---|
| Reported email | `EVIDENCE` | Preserve headers + body; do NOT forward |
| Targeted user(s) | `AT-RISK` | Force password reset; revoke all sessions |
| Phishing infrastructure | `IDENTIFIED` | Submit to takedown; block at DNS/email gateway |
| Login audit logs | `COLLECT` | Pull all logins for affected users (72h window) |

1. **Phase I — Detection & Triage**
   - Retrieve original email (`.eml` with full headers)
   - Extract: `From`, `Reply-To`, `Return-Path`, `X-Originating-IP`, embedded URLs
   - Check: did user click link or submit credentials?
   - Pull `Azure AD` / `Okta` / IdP sign-in logs for affected user

2. **Phase II — Containment**
   - Force password reset for targeted user
   - Revoke all active sessions (`Revoke-AzureADUserAllRefreshToken` / equivalent)
   - Block sender domain / IP at email gateway
   - Block embedded URLs at web proxy / DNS filter
   - Search mailbox for other recipients of same campaign

3. **Phase III — Eradication**
   - Remove phishing email from all recipient inboxes (admin `Search-Mailbox` + `DeleteContent`)
   - Submit phishing URL to safe-browsing blocklists
   - If credentials entered: audit what data that account can access
   - Rotate any API keys or service accounts accessible by compromised user

4. **Phase IV — Recovery**
   - Re-enable MFA if disabled
   - Brief affected user(s) on identifying phishing
   - Monitor account for 30 days for anomalous activity

5. **Phase V — Post-Mortem**
   - Calculate: `time-to-click` → `time-to-report` → `time-to-contain`
   - Assess email-filter bypass reason
   - Update phishing simulation training

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: SOCIAL_ENGINEERING` | `[PHASE]: I`

---

### 5.3 `IR-EXFIL` — Data Breach / Exfiltration

### [OP-ID: IR-EXFIL-RESPONSE]

**Objective:** Identify exfiltrated data, stop egress, determine regulatory exposure, and notify stakeholders.

| Asset | Status | Action |
|---|---|---|
| Egress point | `IDENTIFIED` | Block outbound connection; capture flow logs |
| Exfiltrated data | `TO-SCOPE` | Audit access logs; determine record count + type |
| Regulatory exposure | `PENDING` | Map data types to GDPR/HIPAA/PCI-DSS obligations |
| Legal | `NOTIFIED` | Engage counsel for breach-notification timeline |

1. **Phase I — Detection & Triage**
   - Identify egress method (`HTTP POST`, `DNS tunneling`, `S3 sync`, `rsync`, `cloud storage`)
   - Determine data source: which DB / bucket / file share?
   - Pull netflow logs for volume + destination IP
   - Declare `SEV-0`

2. **Phase II — Containment**
   - Block egress IP / port / protocol at perimeter
   - Revoke compromised credentials / access keys
   - Freeze affected database exports and/or bucket public access
   - Preserve all access logs (SIEM, CloudTrail, DB audit logs)

3. **Phase III — Eradication**
   - Close initial access vector (exploit, misconfiguration, credential leak)
   - Rotate all secrets exposed to affected environment
   - Apply additional access controls (network segmentation, MFA enforcement)
   - Validate no secondary egress paths exist

4. **Phase IV — Recovery**
   - Restore least-privilege access model
   - Enable enhanced logging / DLP rules
   - Legal: determine notification obligations (GDPR 72h clock, state breach laws)
   - Communications: draft stakeholder notification per legal guidance

5. **Phase V — Post-Mortem**
   - Data inventory audit
   - DLP rule gap analysis
   - Access review policy update

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: EGRESS_CONTROL` | `[PHASE]: I`

---

### 5.4 `IR-INSIDER` — Insider Threat

### [OP-ID: IR-INSIDER-RESPONSE]

**Objective:** Investigate anomalous user activity, determine intent (malicious / accidental), contain damage, and engage HR/Legal.

| Asset | Status | Action |
|---|---|---|
| User account | `QUARANTINED` | Disable access; preserve session data |
| Accessed resources | `AUDIT` | Pull full access log timeline (90 days) |
| HR file | `NOTIFIED` | Engage HR before direct confrontation |
| Legal | `ON-STANDBY` | Prepare for employment action / law enforcement |

1. **Phase I — Detection & Triage**
   - Identify alert source: DLP, manager report, off-hours access, USB detection, anomalous data transfer
   - Pull: login history, file access logs, email export, print logs, USB mount history
   - Compare behavior against user's role baseline
   - **Do NOT confront the user.** Coordinate with HR first.

2. **Phase II — Containment**
   - Disable all account access (SSO, VPN, email, SaaS, physical badge)
   - Revoke all active sessions
   - Preserve workstation: forensic image; do NOT allow user to touch device
   - Freeze any data that may have been exfiltrated or modified

3. **Phase III — Eradication**
   - HR-led interview with user (IT provides evidence package)
   - Determine: malicious vs. negligent vs. false-positive
   - If malicious: preserve evidence chain for potential prosecution
   - Close access pathways exploited by user

4. **Phase IV — Recovery**
   - Restore / rollback any modified or deleted data
   - Re-evaluate access control model: least-privilege audit
   - If termination: execute offboarding checklist within 1 hour

5. **Phase V — Post-Mortem**
   - Behavioral indicator analysis for early detection
   - Access review policy changes
   - HR offboarding process review

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: TRUST_BOUNDARY` | `[PHASE]: I`

---

### 5.5 `IR-BEC` — Business Email Compromise

### [OP-ID: IR-BEC-RESPONSE]

**Objective:** Identify fraudulent communication, halt financial transfer, notify bank, and preserve evidence for law enforcement.

| Asset | Status | Action |
|---|---|---|
| Fraudulent email | `EVIDENCE` | Preserve full `.eml` with headers; do NOT delete |
| Financial transaction | `AT-RISK` | Contact bank immediately; attempt wire recall |
| Affected executive identity | `SPOOFED` | Block impersonation at email gateway |
| FBI / law enforcement | `NOTIFIED` | File IC3 complaint within 24h |

1. **Phase I — Detection & Triage**
   - Classify BEC type: executive impersonation / vendor payment change / payroll redirect
   - Extract email headers: `Return-Path`, `Reply-To`, `Received` chain
   - Determine financial transfer status: executed or blocked?
   - Pull: mail-flow rules, forwarding rules, inbox rules for affected identities

2. **Phase II — Containment**
   - Contact **bank / payment processor** immediately; initiate wire recall
   - Block sender domain / lookalike domain at email gateway
   - Disable any auto-forwarding rules on affected accounts
   - Force password reset + MFA re-enrollment for impersonated identity

3. **Phase III — Eradication**
   - Remove phishing/social-engineering emails from all recipient inboxes
   - Submit lookalike domain to registrar abuse contact
   - File **IC3 complaint** (ic3.gov) within 24 hours
   - Engage cyber-insurance provider if financial loss threshold met

4. **Phase IV — Recovery**
   - Implement DMARC reject policy (`p=reject`) if not already enforced
   - Add executive display-name spoofing rules to email gateway
   - Brief finance team on payment-change verification procedures

5. **Phase V — Post-Mortem**
   - Calculate: financial exposure and recovered amount
   - Audit: payment-change authorization process
   - Implement: out-of-band payment verification (phone callback required)

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: SOCIAL_ENGINEERING_FINANCIAL` | `[PHASE]: I`

---

### 5.6 `IR-CRYPTO` — Cryptojacking

### [OP-ID: IR-CRYPTO-RESPONSE]

**Objective:** Identify cryptomining activity, terminate processes, remove persistence, and audit cloud billing impact.

| Asset | Status | Action |
|---|---|---|
| Affected host / instance | `COMPROMISED` | Isolate; capture process list + network connections |
| Cloud billing | `AUDIT` | Calculate unauthorized compute cost |
| Mining pool / wallet | `IDENTIFIED` | Block at firewall + DNS; submit to threat-intel |
| Adjacent hosts | `TO-SCAN` | Check for lateral spread via same vector |

1. **Phase I — Detection & Triage**
   - Identify alert source: CPU spike, cloud billing anomaly, CSPM alert, EDR detection
   - Capture: `process list`, `network connections`, `cron/at/systemd timers`
   - Extract: mining binary path, pool address, wallet address
   - Determine initial access vector (exposed API, unpatched vuln, SSH brute-force)

2. **Phase II — Containment**
   - Kill mining process; block mining pool IP + domain at perimeter
   - Isolate host from network (disable NIC; do NOT power off)
   - If cloud instance: snapshot for forensics, then stop instance
   - Scan adjacent hosts / sibling instances for same IOCs

3. **Phase III — Eradication**
   - Wipe and reimage affected host from trusted baseline
   - Close initial access vector (patch, rotate keys, restrict network access)
   - Remove all persistence: `crontab`, `systemd timers`, `~/.ssh/authorized_keys`, `startup scripts`
   - Validate cloud IAM roles: no excessive permissions enabling self-deployment

4. **Phase IV — Recovery**
   - Re-deploy host with enhanced monitoring (CPU threshold alerts)
   - Enable cloud billing anomaly alerts if not already active
   - Monitor for 72 hours for reinfection

5. **Phase V — Post-Mortem**
   - Calculate: unauthorized compute cost
   - Audit: CSPM / cloud-security posture gaps
   - Implement: infrastructure-as-code scanning for exposed services

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: COMPUTE_RESOURCE` | `[PHASE]: I`

---

### 5.7 `IR-DOS` — Denial of Service

### [OP-ID: IR-DOS-RESPONSE]

**Objective:** Maintain or restore service availability; identify attack vector; engage upstream provider if needed.

| Asset | Status | Action |
|---|---|---|
| Internet-facing services | `DEGRADED` | Enable CDN/WAF DoS protection; scale resources |
| Upstream provider | `NOTIFIED` | Request traffic scrubbing / blackhole if needed |
| Attack signature | `COLLECT` | Capture packet captures; analyze traffic pattern |
| Failover | `PREPARED` | Activate DR site if primary unrecoverable |

1. **Phase I — Detection & Triage**
   - Classify attack type: volumetric / application-layer / protocol
   - Capture `pcap` sample (5 min) for signature analysis
   - Check CDN/WAF posture: origin exposed or edge absorbing?
   - Declare severity based on customer impact

2. **Phase II — Containment**
   - Enable CDN/WAF "under attack" mode
   - Rate-limit at edge; deploy geo-blocking if attack is regional
   - Contact upstream ISP for traffic scrubbing
   - If application-layer: identify targeted endpoint; temporarily disable or cache heavily

3. **Phase III — Eradication**
   - Deploy WAF rules matching attack signature
   - Scale origin capacity if volumetric
   - Consider migrating critical services to alternative IP range
   - Monitor for shift in attack vector (multi-vector attacks)

4. **Phase IV — Recovery**
   - Gradually reduce rate-limiting as attack subsides
   - Restore geo-blocking to normal posture
   - Performance-test recovered services
   - Monitor traffic for 48 hours for follow-up attacks

5. **Phase V — Post-Mortem**
   - Calculate: `time-to-detect` → `time-to-mitigate` → total downtime
   - Architecture review: eliminate single points of failure
   - Update runbook with attack signatures observed

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: AVAILABILITY` | `[PHASE]: I`

---

### 5.8 `IR-WEB` — Web Application Attack

### [OP-ID: IR-WEB-RESPONSE]

**Objective:** Halt active exploitation, patch injection point, scan for web shells, and rotate application secrets.

| Asset | Status | Action |
|---|---|---|
| Affected application | `COMPROMISED` | Take offline or enable WAF block mode |
| WAF / access logs | `COLLECT` | Pull payloads, source IPs, timestamps |
| Application secrets | `EXPOSED` | Rotate all keys, tokens, DB credentials |
| Deployment artifacts | `TO-SCAN` | Search for web shells, backdoors, modified files |

1. **Phase I — Detection & Triage**
   - Identify attack type: `SQLi`, `XSS`, `RCE`, `LFI/RFI`, `CSRF`, `SSRF`, deserialization
   - Extract payloads from WAF logs; correlate with access logs
   - Determine: did the attack succeed (response codes, data returned)?
   - Declare severity per decision tree (Section 2.2)

2. **Phase II — Containment**
   - Enable WAF blocking mode for targeted endpoint(s)
   - Take application offline if active exploitation confirmed
   - Block attacker IPs at perimeter
   - Revoke application's DB credentials; issue temporary restricted credentials

3. **Phase III — Eradication**
   - Patch vulnerability (code fix, library update, config change)
   - Scan full codebase + upload directories for web shells (`find` with timestamps, checksum audit)
   - Rotate all application secrets and API keys
   - Validate fix with same payloads — confirm 40x response

4. **Phase IV — Recovery**
   - Re-deploy patched application
   - Enable enhanced WAF logging for targeted endpoints
   - Monitor application error rates and DB query patterns for 72 hours

5. **Phase V — Post-Mortem**
   - Code review: how did the vulnerability survive to production?
   - Pipeline audit: SAST/DAST coverage gap
   - Update secure coding guidelines

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: APPLICATION_LAYER` | `[PHASE]: I`

---

### 5.9 `IR-CLOUD` — Cloud / Infrastructure Misconfig

### [OP-ID: IR-CLOUD-RESPONSE]

**Objective:** Revoke public access, audit exposure window, rotate exposed secrets, and harden infrastructure-as-code.

| Asset | Status | Action |
|---|---|---|
| Exposed resource | `PUBLIC` | Revoke public access immediately |
| Access logs | `COLLECT` | Determine if unauthorized access occurred |
| Exposed secrets / data | `TO-ROTATE` | Rotate all keys; assess data exposure |
| IaC templates | `TO-AUDIT` | Fix misconfiguration at source (Terraform, CFN, Pulumi) |

1. **Phase I — Detection & Triage**
   - Identify misconfig type: public S3 bucket, open security group, exposed IAM key, unsecured DB, public ECR/ACR repo
   - Pull access logs for the exposure window
   - Determine: was the resource accessed by unauthorized parties?
   - Declare severity based on data classification and access evidence

2. **Phase II — Containment**
   - Revoke public access / apply restrictive policy
   - Rotate all exposed credentials, API keys, and access keys
   - Revoke any active sessions associated with exposed credentials
   - If data accessed: treat as `IR-EXFIL` (Section 5.3) for egress scoping

3. **Phase III — Eradication**
   - Fix root cause in IaC (Terraform, CloudFormation, Pulumi, ARM)
   - Apply organization-wide SCP / policy guardrails to prevent recurrence
   - Scan all sibling resources for same misconfiguration pattern
   - Enable automated CSPM scanning with alerting

4. **Phase IV — Recovery**
   - Re-deploy resources via patched IaC pipeline
   - Validate: no hardcoded secrets in code, config, or environment variables
   - Monitor cloud audit logs (CloudTrail / equivalent) for 72 hours

5. **Phase V — Post-Mortem**
   - IaC review: why did the misconfig pass review / CI checks?
   - CSPM tooling gap analysis
   - Implement blocking SCPs / Azure Policy / org constraints

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: CONFIGURATION` | `[PHASE]: I`

---

### 5.10 `IR-SUPPLY` — Supply Chain Compromise

### [OP-ID: IR-SUPPLY-RESPONSE]

**Objective:** Identify compromised vendor artifact, isolate affected systems, assess blast radius, and coordinate with vendor.

| Asset | Status | Action |
|---|---|---|
| Vendor advisory | `RECEIVED` | Assess CVE/CVSS; determine org exposure |
| Affected software / library | `IDENTIFIED` | Determine deployed instances and version |
| Deployment inventory | `TO-SCAN` | Full SBOM audit for compromised artifact |
| Vendor liaison | `ENGAGED` | Request IOCs, patch ETA, workaround guidance |

1. **Phase I — Detection & Triage**
   - Source: vendor security advisory, CISA KEV, threat-intel feed, GitHub security advisory
   - Assess: CVE score, exploitability, whether exploitation is active in the wild
   - Run SBOM scan across all environments for affected artifact + version
   - Declare `SEV-0` per classification matrix

2. **Phase II — Containment**
   - Isolate systems running compromised software from production traffic
   - Block IOCs provided by vendor at perimeter / EDR
   - If CI/CD pipeline poisoned: freeze all deployments; revoke pipeline credentials
   - Audit recent deployments for signs of post-compromise activity

3. **Phase III — Eradication**
   - Apply vendor patch or update to remediated version
   - If no patch available: apply vendor workaround or remove software temporarily
   - Rotate all secrets and credentials accessible to affected systems
   - Validate: no persistence or secondary payload deployed via compromised artifact

4. **Phase IV — Recovery**
   - Re-deploy with patched version from trusted source
   - Monitor affected systems for 30 days for delayed activation
   - Implement SBOM generation + vulnerability scanning in CI/CD pipeline

5. **Phase V — Post-Mortem**
   - SBOM maturity audit: can we answer "where is library X?" in under 1 hour?
   - Vendor risk assessment: update procurement security questionnaire
   - Pipeline hardening: artifact signing, provenance verification

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: THIRD_PARTY` | `[PHASE]: I`

---

## 6. COMMUNICATION TEMPLATES

### 6.1 Incident Declaration (Internal)

```
[OP-ID: <IR-ID>] // INCIDENT DECLARED

Severity: <SEV-0|SEV-1|SEV-2|SEV-3>
Type: <IR-MAL|IR-PHISH|IR-BEC|IR-EXFIL|IR-DOS|IR-INSIDER|IR-CRYPTO|IR-WEB|IR-CLOUD|IR-SUPPLY>
Triage Owner: <IC name>
War Room: <Bridge/Channel URL>
Time Declared: <YYYY-MM-DD HH:MM UTC>

Initial Scope: <One-line summary of what is known.>
Containment Status: <ACTIVE|PENDING>
Next Update: <time or condition>
```

### 6.2 Stakeholder Update (Hourly)

```markdown
### [OP-ID: <IR-ID>] — Hourly Update #<N>

**Status:** <CONTAINING|ERADICATING|RECOVERING|RESOLVED>

| Metric | Value |
|---|---|
| Time since declaration | `<N>h <M>m` |
| Services affected | `<list>` |
| Users/data affected | `<count/scope>` |
| Containment status | `<COMPLETE|IN-PROGRESS|BLOCKED>` |
| Estimated resolution | `<timeframe>` |

*Note: <Material change since last update, if any.>*

> `[LOGIC_STATE]: <STATE>` | `[PHASE]: <II|III|IV>` | `[NEXT_UPDATE]: <time>`
```

### 6.3 External / Customer Notification

> **⚠ UNCLASSIFIED — Do NOT send without Legal approval.**

```
Subject: [COMPANY] Service Incident — <date>

We are investigating a service disruption affecting <service_name>.
Impact: <scope: what customers are experiencing>.
Our operations team is working to restore service.
Next update: <time or timeframe>.

If you have questions, contact <support channel>.
```

---

## 7. EVIDENCE HANDLING PROTOCOL

### 7.1 Chain of Custody

| `EVIDENCE_ID` | Description | Collected By | Timestamp | Hash (SHA-256) | Custody Transfer |
|---|---|---|---|---|---|
| `EVID-001` | `pcap` from `app-server-03` | `TL` | `YYYY-MM-DD HH:MM` | `<hash>` | → `Forensics Team` |
| `EVID-002` | Disk image `workstation-17` | `TL` | `YYYY-MM-DD HH:MM` | `<hash>` | → `Forensics Team` |
| `EVID-003` | Phishing `.eml` | `CO` | `YYYY-MM-DD HH:MM` | `<hash>` | → `TL` |

### 7.2 Evidence Preservation Order

1. **Volatile data first:** memory dump → network state → process list → disk image
2. **Never power off** affected systems before capturing volatile data
3. **Hash everything** before and after transfer
4. **Store evidence** on write-once media or append-only log storage
5. **Document every transfer** in chain-of-custody log

*Note: Assume every incident may become a legal matter. Preserve evidence accordingly.*

---

## 8. POST-MORTEM TEMPLATE

```markdown
### [OP-ID: <IR-ID>-POSTMORTEM]

**Objective:** Root-cause analysis and control improvement for <IR-ID>.

| Field | Value |
|---|---|
| Incident ID | `<IR-ID>` |
| Severity | `<SEV-0|SEV-1|SEV-2|SEV-3>` |
| Type | `<IR-MAL|IR-PHISH|...>` |
| Date / Duration | `<start> → <end> (<N> hours)` |
| IC | `<name>` |
| Services affected | `<list>` |
| Data exposed | `<count/type>` |

### Timeline

| Time (UTC) | Event | Actor |
|---|---|---|
| `HH:MM` | Initial compromise / trigger | `<attacker/user/system>` |
| `HH:MM` | Detection (alert / user report) | `<source>` |
| `HH:MM` | Incident declared | `IC` |
| `HH:MM` | Contained | `TL` |
| `HH:MM` | Eradicated | `TL` |
| `HH:MM` | Recovered | `TL` |
| `HH:MM` | Resolved | `IC` |

### Root Cause

- **What happened:** <one-paragraph summary>
- **Why:** <underlying cause — technical, process, or human>
- **Missed control:** <which control should have caught this?>

### Remediation

| `[CONTROL]` | `[GAP]` | `[ACTION]` | `[OWNER]` | `[DUE]` |
|---|---|---|---|---|
| `<control name>` | `<description>` | `<action>` | `<name>` | `<date>` |

### Lessons Learned

- **What went well:** <at least one positive>
- **What went poorly:** <at least one gap>
- **Process changes:** <playbook updates needed>

*Note: Post-mortems are blameless. Focus on controls, not people.*

> `[LOGIC_STATE]: RESOLVED` | `[VULNERABILITY]: <ROOT_CAUSE>` | `[PHASE]: V — COMPLETE`
```

---

## 9. PRE-STAGED IR KIT

| Resource | Location | Access | Notes |
|---|---|---|---|
| IR Playbook (this doc) | `wiki/ir-playbook` | All team | Printed copies in NOC |
| Forensic USB drives | `safe — NOC cabinet` | `TL`, `IC` | Write-blockers included |
| Jump bag (network kit) | `safe — NOC cabinet` | `TL` | Cables, switch, console adapter |
| Offline password vault | `safe — NOC cabinet` | `IC` | Break-glass admin credentials |
| Emergency contacts | `wiki/ir-contacts` | All team | ISP, legal, PR, executive |
| SIEM / log retention | `<SIEM URL>` | `TL`, `SME` | Minimum 90-day retention |
| Clean OS images | `<image server path>` | `TL` | Verified SHA-256 hashes |

---

## 10. TABLE-TOP EXERCISE GUIDANCE

> *"No playbook survives first contact with a real incident. Test it quarterly or it's dead paper."*

| Exercise | Frequency | Duration | Participants | Goal |
|---|---|---|---|---|
| **Walkthrough** | Quarterly | 2 hours | `IC`, `TL`, `CO` | Validate playbook flow; catch stale contacts |
| **Simulation** | Biannual | 4 hours | Full IR team + `SME` | Red-team injects; test detection → containment → recovery |
| **Cross-team drill** | Annual | 8 hours | IR + Legal + Exec + PR | Full breach scenario with regulatory notification practice |

**Scenario rotation:** Cycle through `IR-MAL` → `IR-EXFIL` → `IR-BEC` → `IR-INSIDER` across exercises.

**After each exercise:**

1. Capture **gaps** in the playbook (missing steps, broken contacts, stale tools)
2. Update playbook within **1 week** of exercise
3. Publish **after-action report** using the post-mortem template (Section 8)

---

## 11. LEGAL & COMPLIANCE TRIGGERS

| Regulation | Trigger Event | Deadline | Action |
|---|---|---|---|
| **GDPR** (EU) | Personal data breach (any volume) | **72 hours** | Notify supervisory authority; affected individuals if high risk |
| **CCPA / CPRA** (CA) | Unauthorized access to CA resident PII (500+ records) | **Without unreasonable delay** | Notify CA AG; affected individuals |
| **HIPAA** (US healthcare) | PHI breach (500+ individuals) | **60 days** | Notify HHS, affected individuals, and media |
| **NY SHIELD Act** | Breach of private information (any NY resident) | **Without unreasonable delay** | Notify NY AG, DHS, affected individuals |
| **PCI-DSS** | Cardholder data compromise | **Immediately** | Notify acquiring bank and payment brands |
| **SEC** (public companies) | Material cybersecurity incident | **4 business days** | File Form 8-K (Item 1.05) |
| **FedRAMP** | Security incident involving federal data | **1 hour** | Notify AO, agency, US-CERT |

*Note: This table is a starting reference, not legal advice. Always consult **Legal Counsel** for jurisdiction-specific obligations.*

---

## 12. APPENDIX: FIELD QUICK-REFERENCE CARD

> **Print and laminate. One per NOC station.**

**IR-ID format:** `IR-YYYYMMDD-NNN` (e.g., `IR-20260730-001`)

| Severity | Declare | Contain (max) | Eradicate (max) | Recover (max) |
|---|---|---|---|---|
| `SEV-0` | **Immediate** | 1h | 4h | 8h |
| `SEV-1` | 15 min | 4h | 24h | 48h |
| `SEV-2` | 1h | 24h | 72h | 5 days |
| `SEV-3` | 24h | N/A | 7 days | 14 days |

```
[OBSERVE] → [CONFIRM] → [DECLARE SEVERITY] → [CONTAIN] → [ERADICATE] → [RECOVER] → [POST-MORTEM]
 └── Phase I ──┘  └──────── Phase II ────────┘  └── Phase III ──┘  └─ Phase IV ─┘  └─ Phase V ─┘
```

**Playbook Quick-Pick:**

| Symptom | Playbook |
|---|---|
| Files encrypted / ransom note | `IR-MAL` (Section 5.1) |
| Suspicious email / fake login page | `IR-PHISH` (Section 5.2) |
| Executive impersonation / payment fraud | `IR-BEC` (Section 5.5) |
| Data uploaded to unknown destination | `IR-EXFIL` (Section 5.3) |
| Service unavailable / traffic flood | `IR-DOS` (Section 5.7) |
| Off-hours access / USB insertion | `IR-INSIDER` (Section 5.4) |
| CPU spike / cloud bill spike | `IR-CRYPTO` (Section 5.6) |
| WAF alert / SQLi / XSS payload | `IR-WEB` (Section 5.8) |
| Public S3 bucket / open security group | `IR-CLOUD` (Section 5.9) |
| Vendor advisory / poisoned update | `IR-SUPPLY` (Section 5.10) |

---

> **[CONCLUSION]:** When the alarm fires, the playbook replaces thinking. Every second spent deciding what to do is a second the attacker is still in your network. Strip hesitation. Execute procedure. 🚬

---

*END INCIDENT RESPONSE PLAYBOOK*
