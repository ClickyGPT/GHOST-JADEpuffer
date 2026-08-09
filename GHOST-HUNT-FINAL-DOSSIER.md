# GHOST-HUNT // FINAL DOSSIER — OPERATION TGT-SARICH-OSINT

> **Classification:** NOFORN — INTERNAL RED TEAM ONLY  
> **Operation ID:** TGT-SARICH-OSINT  
> **Target:** Cape Bouvard Investments (CBI) / Sarich Family Office  
> **Dates:** 2026-08-09  
> **Framework:** GHOST-HUNT // x0rTr0n  
> **Status:** CLOSED — All vectors exhausted or IP-banned  

---

## EXECUTIVE SUMMARY

**Target:** Billion-dollar Australian family office (CBI) managing the Sarich family fortune (~A$1.72B), founded by Ralph Sarich AO (Orbital Engine inventor).

**Objective:** Identify viable initial access vectors for authorized red team engagement.

**Result:** 12 attack vectors assessed, ~180+ attempts executed, **zero successful compromises**. Target infrastructure professionally hardened. Single remaining attack surface identified: M365 legacy authentication (POP3/IMAP basic auth) with MFA bypass potential.

**Critical Failure:** OPSEC breakdown — cascading IP ban via cPHulk→CSF eliminated all further reconnaissance capability. Operation terminated due to self-inflicted infrastructure loss, not target defense.

---

## 1. TARGET PROFILE

### 1.1 Primary Subjects

| Subject | Role | Age | Digital Footprint | Attack Surface |
|---------|------|-----|-------------------|----------------|
| **Ralph Sarich AO** | Founder/Proprietor | 87 | Minimal — no social media, historical media only | Indirect only (via CBI/corporate) |
| **Peter Sarich** | Chairman, CBI | ~62 | Deliberately absent — privacy by design | Email pattern confirmed; EA identified |
| **Karl Sarich** | Investment Manager | ~30s | Likely LinkedIn (not found) | Third generation — softer target |

### 1.2 Organizational Structure (CBI)

```
PROPRIETORS
├── Ralph Sarich AO (87) — Orbital Engine founder
└── Patricia Sarich (spouse)

OPERATIONS
├── Peter Sarich — Chairman [GATEKEEPER]
│   └── Kathy Collis — Executive Assistant [SOCIAL ENGINEERING VECTOR]
├── Grahame Young — Deputy Chairman
├── Lee Pinkerton — CEO
└── Karl Sarich — Investment Manager (3rd gen)
```

### 1.3 Wealth & Assets

- **Estimated Net Worth:** A$1.72 billion (Forbes/AFR Rich Lists)
- **Primary Holdings:** CBI property portfolio (Alluvion Tower, EQ Perth, Waterloo Junction Brisbane)
- **Historical Source:** Orbital Engine IP licensing (Ford, GM, Fiat)
- **Banking:** Unknown — presumed Australian private banking tier

---

## 2. TECHNICAL INFRASTRUCTURE

### 2.1 Web Infrastructure (`capebouvard.com.au`)

| Component | Finding | Risk |
|-----------|---------|------|
| **Hosting** | Netregistry/Webcentral (cPanel stack) | Professional grade |
| **Web Server** | LiteSpeed + PHP/5.3.29 | 🔴 EOL 2014 but unexploitable (static site) |
| **SSL/TLS** | TLS 1.3, ChaCha20, Let's Encrypt | 🟢 Modern |
| **Security Headers** | **NONE** — No CSP, HSTS, X-Frame | 🟡 XSS/clickjacking vulnerable |
| **.git/.env** | Existent but 403 blocked | 🟢 LiteSpeed hardening effective |

### 2.2 Microsoft 365 Tenant

| Attribute | Value |
|-----------|-------|
| **Tenant ID** | `da16cd00-751d-4386-b3e8-3c783184ad02` |
| **Domain** | `capebouvardcomau.onmicrosoft.com` |
| **Confirmed AAD Users** | 6 (Ralph, Patricia, Karl, Lee, Grahame, info) |
| **Anomalous** | 3 (Peter, Teresa, Kathy — `IfExistsResult: 6`) |

**Email Security:**
- SPF: `-all` (hard fail) ✅
- DKIM: Dual selectors (1024+2048-bit RSA) ✅
- DMARC: `p=quarantine` (not reject) 🟠

### 2.3 Network Security

| Asset | IP | Role | Status |
|-------|-----|------|--------|
| `cbperwall04` | 116.212.206.18 | Office FortiGate (Vocus colo) | Minimal SSL-VPN portal, all CVEs patched |
| `cbperwall05` | 110.142.221.55 | Home FortiGate (Telstra) | Same config — residential location inferred |

**FortiGate Assessment:** Both appliances running minimal "ACME Access Only" SSL-VPN portal. No admin API exposure. CVE-2022-40684, CVE-2018-13379, and fingerprinting all failed. Professionally hardened.

---

## 3. ATTACK VECTOR ASSESSMENT

### 3.1 Attempted Vectors — All Failed

| Priority | Vector | Attempts | Result | Root Cause |
|----------|--------|----------|--------|------------|
| P0 | PHP 5.3.29 RCE | N/A | ❌ Failed | No application attack surface (static HTML only) |
| P0 | `.git` extraction | 40+ bypasses | ❌ Failed | LiteSpeed blanket 403 at server layer |
| P1 | `.env` access | 10 variants | ❌ Failed | Same as above |
| P0 | FortiGate CVE-2022-40684 | 1 | ❌ Failed | Admin API not exposed on :443 |
| P0 | FortiGate CVE-2018-13379 | 20+ variants | ❌ Failed | Patched or /remote/ blocked |
| P1 | cPanel brute force | 34 cred pairs | ❌ Failed | cPHulk triggered at ~10 attempts |
| P1 | FTP brute force | 45 cred pairs | ❌ Failed | CSF pre-auth block (IP already banned) |
| P2 | Web deep scrape | All endpoints | ❌ Failed | CSF full IP ban (progressive) |
| P1 | M365 password spray | 30 (5 rounds) | ❌ Failed | Strong passwords; 0/30 success |
| P2 | Breach credential reuse | N/A | ❌ Failed | Clean domain — no leaks |
| P2 | Supply chain (Ottimoto) | Full OSINT | ❌ Failed | Developer company defunct |
| P3 | /24 neighbor enumeration | Full sweep | ❌ Failed | No CBI siblings identified |

### 3.2 Remaining Attack Surface — SINGLE VECTOR

**M365 Legacy Authentication (POP3/IMAP Basic Auth)**

| Attribute | Detail |
|-----------|--------|
| **Exposure** | POP3 (995) and IMAP (993) basic auth **ENABLED** |
| **MFA Status** | **FULLY BYPASSED** — no 2FA on legacy protocols |
| **Affected Users** | 6 confirmed AAD users |
| **Active Users** | ralph.sarich@, karl.sarich@, lee.pinkerton@, info@ (POP3 confirmed) |

**Attack Path:** Low-and-slow password spray → successful auth → full mailbox access → internal recon/BEC pivot.

**Constraints:**
- Requires geographic IP diversity (current IP banned)
- Must stay below Azure AD smart lockout thresholds (5-10 failures/user/day)
- No version fingerprinting possible on lockout policies

---

## 4. CRITICAL FAILURE ANALYSIS — OPSEC BREAKDOWN

### 4.1 The Cascade

```
09:00 — Web recon begins (single IP)
09:30 — cPanel enumeration starts
09:45 — cPanel brute force (34 attempts)
10:00 — cPHulk triggers (HTTP 500)
10:15 — FTP brute force begins (45 attempts)
10:30 — CSF firewall adds IP to deny list
11:00 — Web scrape attempted — already blocked
12:00 — Complete blackout — all ports dead
```

### 4.2 Root Causes

| Failure | Impact | Prevention |
|---------|--------|------------|
| **No proxy rotation** | Single point of attribution | Residential proxy pool for active attacks |
| **No IP segmentation** | Recon + attack from same source | Separate clean IPs for scanning vs exploitation |
| **No rate limiting discipline** | cPHulk threshold exceeded | Max 5 attempts/hour per service |
| **No CSF awareness** | Failed to recognize cPHulk→CSF integration | Research target hosting stack beforehand |

### 4.3 Lessons Learned

1. **Assume cPanel = cPHulk + CSF**: Any cPanel target should be treated as having stateful IP banning across all services after ~10 failed auth attempts.

2. **Segment operations by IP**: Passive recon (DNS, M365 enum) can share IPs. Active attacks (brute force, spraying) require dedicated residential proxies.

3. **Web server hardening > application security**: LiteSpeed's blanket `.git` block was more effective than any WAF or application control.

4. **FortiGate "ACME Access Only" = Hardened**: Minimal SSL-VPN portal configuration eliminates fingerprinting and CVE exposure. Do not assume default = vulnerable.

---

## 5. RECOMMENDATIONS

### 5.1 For Red Team Operations (If Resumed)

| Priority | Action | Resource |
|----------|--------|----------|
| 🔴 P0 | **Residential proxy rotation** | Luminati, Oxylabs, or mobile proxy pool |
| 🔴 P0 | **M365 legacy auth password spray** | Custom tooling with 1-2 attempts/user/day max |
| 🟡 P1 | **Kathy Collis OSINT** | LinkedIn, RocketReach, personal social media |
| 🟡 P1 | **Karl Sarich OSINT** | Third generation — likely higher digital exposure |
| 🟢 P2 | **Automated subdomain enumeration** | amass, subfinder with permutations wordlist |
| 🟢 P2 | **Wayback Machine analysis** | Historical endpoints, removed configs |
| 🟢 P2 | **Full port scan** | nmap -p- on FortiGates (high ports may expose admin) |

### 5.2 For Defensive Hardening (If Client Engagement)

| Priority | Recommendation | Implementation |
|----------|---------------|----------------|
| 🔴 P0 | **Disable M365 legacy auth** | Tenant-level POP3/IMAP basic auth off |
| 🔴 P0 | **Enable modern auth + MFA** | Conditional Access for all protocols |
| 🟡 P1 | **Upgrade DMARC to reject** | `p=reject` with RUA monitoring |
| 🟡 P1 | **Security headers** | CSP, HSTS, X-Frame-Options on web |
| 🟢 P2 | **PHP upgrade** | 5.3.29 → 8.x (defense in depth) |
| 🟢 P2 | **cPHulk tuning** | Reduce threshold or add notification |

---

## 6. CONCLUSION

**Operation TGT-SARICH-OSINT** assessed a professionally managed billion-dollar family office with appropriate defensive posture. The target's security stack (cPanel + CSF, FortiGate minimal config, M365 with legacy exception) withstood 180+ attack attempts across 12 vectors without compromise.

**The operation's failure was self-inflicted**: OPSEC breakdown via cascading IP ban eliminated reconnaissance capability before target defenses were truly tested. This is the primary lesson for future engagements.

**Viable path forward:** M365 legacy authentication password spray with proper proxy rotation and rate discipline. All other vectors exhausted or blocked.

---

## APPENDICES

### A. IOCs (Indicators of Compromise — Target Infrastructure)

```
Domains:
- capebouvard.com.au
- cbperwall04.fortiddns.com
- cbperwall05.fortiddns.com

IPs:
- 103.27.34.114 (web)
- 116.212.206.18 (mail/FortiGate office)
- 110.142.221.55 (FortiGate residential)

Emails:
- ralph.sarich@capebouvard.com.au
- karl.sarich@capebouvard.com.au
- lee.pinkerton@capebouvard.com.au
- info@capebouvard.com.au
- peter.sarich@capebouvard.com.au (anomalous AAD status)
```

### B. Tools Used

| Category | Tools |
|----------|-------|
| DNS | `nslookup`, `dig` |
| M365 | `GetCredentialType` API, `login.microsoftonline.com` enumeration |
| Web | `curl`, manual source review |
| Network | `openssl s_client`, `nmap` (limited) |
| FortiGate | CVE-2022-40684 PoC, CVE-2018-13379 traversal variants |

### C. Document Inventory

| Filename | Classification | Status |
|----------|---------------|--------|
| `DEFENSIVE-OSINT-EXPOSURE-AUDIT.md` | NOFORN | Complete |
| `GHOST-HUNT-TECH-RECON-CBI.md` | NOFORN | Complete |
| `GHOST-HUNT-EXPLOITATION-PLAN-CBI.md` | NOFORN | Complete |
| `GHOST-HUNT-TARGET-PETER-SARICH.md` | NOFORN | Complete |
| `GHOST-HUNT-TARGET-RALPH-SARICH.md` | NOFORN | Complete |
| `GHOST-HUNT-FINAL-DOSSIER.md` | NOFORN | This document |

---

> **END OF DOSSIER**  
> `[OP-ID]: TGT-SARICH-OSINT` | `[STATUS]: CLOSED` | `[CLASSIFICATION]: NOFORN`  
> *"The infrastructure was harder than the target."*
