# GHOST-HUNT // TECHNICAL RECON — CAPE BOUVARD INVESTMENTS

> **Version:** 1.0
> **Classification:** RED TEAM INTEL — TECHNICAL RECONNAISSANCE
> **Framework:** GHOST-HUNT // x0rTr0n
> **Author:** Red Team
> **Status:** DRAFT
> **Date:** 2026-08-09
> **Parent Op:** `TGT-SARICH-OSINT` — Ralph Sarich Family Office
> **Recon Target:** `capebouvard.com.au` — CBI Corporate Infrastructure

---

## 1. EXECUTIVE SUMMARY

> *"Billion-dollar property empire. PHP 5.3.29 from 2012. No CSP. No HSTS. DMARC at quarantine. But the email is locked behind Microsoft 365 with DKIM and SPF hard-fail. The web server is the soft spot."*

| Category | Finding | Severity |
|---|---|---|
| **Web Server** | PHP/5.3.29 — EOL August 2014 | 🔴 **CRITICAL** |
| **Security Headers** | No CSP, HSTS, X-Frame, X-Content-Type-Options | 🟡 **HIGH** |
| **M365 Tenant** | Confirmed — `da16cd00-751d-4386-b3e8-3c783184ad02` | 🟡 **HIGH** |
| **M365 Users** | 5 confirmed Azure AD users (Ralph, Patricia, Karl, Lee, Grahame) | 🟡 **HIGH** |
| **Email Security** | DMARC `p=quarantine` (not reject) | 🟠 **MEDIUM** |
| **DKIM** | Dual selectors (1024-bit + 2048-bit RSA) | 🟢 **LOW** — well configured |
| **SPF** | Hard fail `-all` | 🟢 **LOW** — well configured |
| **SSL/TLS** | TLS 1.3, ChaCha20, Let's Encrypt | 🟢 **LOW** — modern |

---

## 2. DNS RECONNAISSANCE

### 2.1 Core Records

| Record | Value |
|---|---|
| **A Record** | `103.27.34.114` |
| **Nameservers** | `ns1.nameserver.net.au`, `ns2.nameserver.net.au`, `ns3.nameserver.net.au` |
| **SOA Serial** | `2024091802` (last updated Sep 18, 2024) |
| **TTL** | 3600 (1 hour) |

### 2.2 Subdomain Enumeration

| Subdomain | Resolves? | Notes |
|---|---|---|
| `www` | ✅ | Same IP — production site |
| `mail` | ✅ | Wildcard DNS in effect |
| `autodiscover` | ✅ | M365 autodiscover likely handled by Microsoft |
| `remote` | ✅ | Wildcard |
| `vpn` | ✅ | Wildcard |
| `portal` | ✅ | Wildcard |
| `login` | ✅ | Wildcard |
| `admin` | ✅ | Wildcard |
| `webmail` | ✅ | Wildcard |
| `owa` | ✅ | Wildcard |

> *Note: Appears to be a wildcard DNS record — all subdomains resolve. Not individually configured services.*

---

## 3. EMAIL SECURITY ASSESSMENT

### 3.1 MX Records

```
capebouvard.com.au  MX preference = 0  →  capebouvard-com-au.mail.eo.outlook.com
```

| Attribute | Value |
|---|---|
| **Mail Provider** | **Microsoft 365 (Exchange Online)** |
| **MX Priority** | 0 (single MX — no backup) |

### 3.2 SPF Record

```
v=spf1 ip4:116.212.206.18 a:mail.capebouvard.com.au include:spf.protection.outlook.com -all
```

| Mechanism | Value | Assessment |
|---|---|---|
| `ip4:116.212.206.18` | Explicit authorized sender IP | 🟡 Unknown host — separate from web server (103.27.34.114) |
| `a:mail.capebouvard.com.au` | CBI mail server A record | 🟢 Standard |
| `include:spf.protection.outlook.com` | M365 outbound | 🟢 Standard for Exchange Online |
| **Policy** | `-all` (HARD FAIL) | 🟢 **Well configured** — spoofed mail rejected |

### 3.3 DMARC Record

```
v=DMARC1; p=quarantine; rua=mailto:webmaster@capebouvard.com.au
```

| Attribute | Value | Assessment |
|---|---|---|
| **Policy** | `p=quarantine` | 🟠 **NOT REJECT** — spoofed mail lands in spam, not blocked |
| **Reports** | `webmaster@capebouvard.com.au` | 🟡 Reports sent to webmaster — active monitoring |
| **Subdomain Policy** | `sp=` NOT SET | 🟠 Subdomains inherit `quarantine` — spoofable subdomains go to spam |
| **Forensic Reports** | `ruf=` NOT SET | 🟡 No forensic reporting configured |

> *⚠️ DMARC at quarantine means: spoofed emails from `@capebouvard.com.au` will land in the recipient's spam/junk folder — not outright rejected. For targeted phishing against external parties who may have relaxed spam filters, this is exploitable.*

### 3.4 DKIM Configuration

| Selector | Key Size | Status |
|---|---|---|
| **selector1** | 1024-bit RSA | ✅ Active |
| **selector2** | 2048-bit RSA | ✅ Active |
| `google` | — | ❌ Not configured |
| `default` | — | ❌ Not configured |

```
selector1._domainkey → CNAME → selector1-capebouvard-com-au._domainkey.capebouvardcomau.onmicrosoft.com
selector2._domainkey → CNAME → selector2-capebouvard-com-au._domainkey.capebouvardcomau.onmicrosoft.com
```

> *DKIM is delegated to Microsoft 365 via CNAME — standard for Exchange Online. Dual selectors provide key rotation capability. Well configured.*

### 3.5 Email Security Scorecard

| Control | Status | Grade |
|---|---|---|
| SPF | `-all` hard fail | 🟢 A |
| DKIM | Dual 1024/2048-bit | 🟢 A |
| DMARC | `p=quarantine` | 🟠 B |
| MX | Single Microsoft 365 | 🟡 B |

---

## 4. MICROSOFT 365 TENANT ENUMERATION

### 4.1 Tenant Confirmation

| Attribute | Value |
|---|---|
| **Tenant ID** | `da16cd00-751d-4386-b3e8-3c783184ad02` |
| **Tenant Domain (onmicrosoft)** | `capebouvardcomau.onmicrosoft.com` |
| **Region** | `OC` (Oceania / Australia) |
| **Cloud Instance** | `microsoftonline.com` (Global — not GCC/USGov) |

### 4.2 User Enumeration (GetCredentialType)

| Email | IfExistsResult | Status | Throttle |
|---|---|---|---|
| `ralph.sarich@capebouvard.com.au` | **0** | ✅ **CONFIRMED — Azure AD User** | 0 |
| `patricia.sarich@capebouvard.com.au` | **0** | ✅ **CONFIRMED — Azure AD User** | 0 |
| `karl.sarich@capebouvard.com.au` | **0** | ✅ **CONFIRMED — Azure AD User** | 0 |
| `lee.pinkerton@capebouvard.com.au` | **0** | ✅ **CONFIRMED — Azure AD User** | 0 |
| `grahame.young@capebouvard.com.au` | **0** | ✅ **CONFIRMED — Azure AD User** | 0 |
| `info@capebouvard.com.au` | **0** | ✅ **CONFIRMED — Azure AD User** (shared mailbox) | 0 |
| `peter.sarich@capebouvard.com.au` | **6** | ⚠️ **EXISTS — Different account type** | 0 |
| `teresa.wong@capebouvard.com.au` | **6** | ⚠️ **EXISTS — Different account type** | 0 |
| `kathy.collis@capebouvard.com.au` | **6** | ⚠️ **EXISTS — Different account type** | 0 |

> *IfExistsResult codes: `0` = Azure AD user in this tenant | `1` = Does not exist | `5` = Exists in different tenant | `6` = Exists as Microsoft Account / external identity*

> *⚠️ **Key anomaly:** Peter Sarich (Chairman), Teresa Wong (GM), and Kathy Collis (EA) return result `6` — they exist but not as standard Azure AD users. Possible explanations: (a) they use personal Microsoft Accounts linked to the domain, (b) guest/B2B accounts in a different tenant, or (c) the domain isn't fully federated for those users. Ralph Sarich (87 years old!) is a confirmed AAD user — interesting.*

### 4.3 M365 Tenant Summary

| Metric | Value |
|---|---|
| Tenant confirmed | ✅ Yes — `da16cd00-751d-4386-b3e8-3c783184ad02` |
| Users enumerated | 9 attempted, 9 responded |
| Confirmed AAD users | **6** (Ralph, Patricia, Karl, Lee, Grahame, info) |
| Anomalous responses | **3** (Peter, Teresa, Kathy — result 6) |
| Rate limiting | None — ThrottleStatus 0 on all queries |
| Legacy auth | Not tested |

---

## 5. WEB SERVER ASSESSMENT

### 5.1 Server Profile

| Attribute | Value |
|---|---|
| **Server Software** | **LiteSpeed** |
| **HTTP Version** | HTTP/1.1 |
| **HTTPS** | ✅ Enabled (port 443) |
| **HTTP/3 (QUIC)** | ✅ Advertised via `alt-svc: h3=":443"` |

### 5.2 PHP Version — 🔴 CRITICAL

```
X-Powered-By: PHP/5.3.29
```

| Attribute | Value |
|---|---|
| **PHP Version** | **5.3.29** |
| **Release Date** | August 14, 2014 |
| **End of Life** | **August 14, 2014** (12 years out of date!) |
| **Known CVEs** | **100+ unpatched** (CVE-2014-5459, CVE-2015-0235, CVE-2016-5093, etc.) |

> *🔴 **PHP 5.3.29 is critically vulnerable.** EOL for over a decade. This is the single most significant finding in this recon. Even if the site is "just a static brochure," the PHP runtime is exposed and exploitable. The site was "Last-Modified: Aug 2, 2026" — so it's actively maintained but running on ancient infrastructure.*

### 5.3 Security Headers — 🟡 FAILING

| Header | Present? | Risk |
|---|---|---|
| **Content-Security-Policy** | ❌ Missing | **HIGH** — XSS vulnerable |
| **Strict-Transport-Security (HSTS)** | ❌ Missing | **HIGH** — SSL stripping possible |
| **X-Frame-Options** | ❌ Missing | **MEDIUM** — Clickjacking possible |
| **X-Content-Type-Options** | ❌ Missing | **MEDIUM** — MIME sniffing |
| **X-XSS-Protection** | ❌ Missing | **LOW** — Legacy, but still useful |
| **Referrer-Policy** | ❌ Missing | **LOW** — Referrer leakage |
| **Permissions-Policy** | ❌ Missing | **LOW** |

> *Zero security headers. On a site serving HTTP/3 with modern TLS. The infrastructure is a contradiction: cutting-edge transport with zero application-layer security.*

### 5.4 SSL/TLS

| Attribute | Value |
|---|---|
| **TLS Version** | TLS 1.3 |
| **Cipher** | `TLS_CHACHA20_POLY1305_SHA256` |
| **Certificate Authority** | Let's Encrypt (YR2) |
| **Subject CN** | `capebouvard.com.au` |
| **SANs** | `capebouvard.com.au`, `www.capebouvard.com.au` |
| **Valid** | Jul 24, 2026 → Oct 22, 2026 |
| **Wildcard** | ❌ No |

> *Modern TLS config — the one thing they got right. But the cert only covers two names (apex + www); any subdomain services would fail TLS validation.*

### 5.5 Technology Stack

| Technology | Detected | Notes |
|---|---|---|
| **jQuery** | ✅ | Frontend JS library |
| **Google Analytics / Maps** | ✅ | `google` references in source |
| **PHP** | 5.3.29 | Server-side (X-Powered-By header) |
| **LiteSpeed** | ✅ | Web server (Server header) |
| **CMS** | ❌ Not WordPress/Drupal/Joomla | Likely custom static site or simple CMS |

---

## 6. VULNERABILITY MATRIX

### 6.1 Critical Findings

| # | Finding | CVSS Equivalent | Exploitability | Impact |
|---|---|---|---|---|
| 1 | **PHP 5.3.29 — 12 years EOL** | 9.8 Critical | Medium-High | Remote code execution |
| 2 | **No security headers** | 6.5 Medium | Low-Medium | XSS, clickjacking, MITM |
| 3 | **DMARC at quarantine** | 5.3 Medium | Medium | Email spoofing possible |
| 4 | **Wildcard DNS** | 4.0 Medium | Low | Subdomain enumeration noise; possible unintended service exposure |

### 6.2 Attack Paths — Prioritized

| Priority | Attack Path | Difficulty | Detection Risk | Yield |
|---|---|---|---|---|
| **P0** | PHP 5.3.29 RCE (CVE exploitation) | Medium | Low-Medium | **Very High** — full server compromise |
| **P1** | M365 phishing (6 confirmed AAD users) | Low-Medium | Low-Medium | **High** — credential theft → email access |
| **P1** | Email spoofing (DMARC quarantine bypass) | Low | Medium | **Medium** — impersonate CBI personnel |
| **P2** | Password spray (known AAD users) | Low-Medium | Medium-High | **Medium-High** — account takeover |
| **P2** | Clickjacking (no X-Frame-Options) | Low | Very Low | **Low** — limited to social engineering |
| **P3** | Subdomain brute-force (wildcard DNS) | Low | Low | **Low** — unlikely to find real services |

---

## 7. INFRASTRUCTURE MAP

```
capebouvard.com.au (103.27.34.114)
│
├── Web: LiteSpeed + PHP/5.3.29 🔴
│   └── TLS: Let's Encrypt YR2 (TLS 1.3 / ChaCha20)
│   └── Security Headers: NONE
│
├── Email: Microsoft 365 Exchange Online
│   ├── Tenant: da16cd00-751d-4386-b3e8-3c783184ad02
│   ├── Fallback: capebouvardcomau.onmicrosoft.com
│   ├── MX: capebouvard-com-au.mail.eo.outlook.com
│   ├── SPF: -all (hard fail) — Authorized: 116.212.206.18
│   ├── DKIM: selector1 (1024-bit) + selector2 (2048-bit) ✅
│   └── DMARC: p=quarantine (reports to webmaster@) 🟠
│
├── DNS: ns1/ns2/ns3.nameserver.net.au
│   └── Wildcard: All subdomains resolve to A record IP
│
├── Known Users (Azure AD):
│   ├── ralph.sarich@       ← Proprietor, age 87
│   ├── patricia.sarich@    ← Proprietor
│   ├── karl.sarich@        ← Investment Manager (3rd gen)
│   ├── lee.pinkerton@      ← CEO
│   ├── grahame.young@      ← Deputy Chairman / Director
│   └── info@               ← Shared mailbox
│
└── Anomalous Users (IfExistsResult: 6):
    ├── peter.sarich@       ← CHAIRMAN — not standard AAD
    ├── teresa.wong@        ← GM — not standard AAD
    └── kathy.collis@       ← EA — not standard AAD
```

---

## 8. OPERATIONAL ASSESSMENT

### 8.1 Phase I — Technical RECON Complete

| Asset | Status | Detail |
|---|---|---|
| DNS topology | `MAPPED` | A, MX, NS, SOA, wildcard confirmed |
| Email security posture | `ASSESSED` | SPF A, DKIM A, DMARC B — spoofable (quarantine) |
| M365 tenant | `CONFIRMED` | Tenant ID, 6 confirmed AAD users, 3 anomalous |
| Web server | `PROFILED` | LiteSpeed + PHP 5.3.29 — critically vulnerable |
| SSL/TLS | `ASSESSED` | Modern (TLS 1.3) — only strong point |
| Subdomain inventory | `SCANNED` | 19 common names — wildcard; no real services found |

### 8.2 Recommended Next Actions

| Priority | Action | Rationale |
|---|---|---|
| **P0** | **PHP 5.3.29 CVE research** — identify exploitable RCE vectors | Critical vulnerability — likely the fastest path to compromise |
| **P1** | **MFA enumeration** — check MFA status on confirmed AAD users | Determines phishing vs. password spray viability |
| **P1** | **Legacy auth check** — test for basic auth / POP3 / IMAP on M365 tenant | Legacy protocols often bypass MFA |
| **P2** | **SPF IP (116.212.206.18) investigation** — is this the web server origin? | May reveal additional infrastructure |
| **P2** | **Kathy Collis recon** — EA to Chairman, anomalous AAD status | Social engineering vector |
| **P3** | **LiteSpeed version fingerprinting** — check for known LiteSpeed CVEs | Additional web attack surface |
| **P3** | **Web CMS identification** — Wappalyzer or manual source review | Plugin/CMS vulnerabilities |

---

## 9. SOURCES

| Source | Method | Reliability |
|---|---|---|
| `nslookup -type=MX/TXT/A/NS/SOA capebouvard.com.au` | DNS query (live) | Very High |
| `login.microsoftonline.com/common/GetCredentialType` | M365 API (live) | Very High |
| `login.microsoftonline.com/<tenant>/.well-known/openid-configuration` | M365 OIDC (live) | Very High |
| `openssl s_client -connect capebouvard.com.au:443` | TLS handshake (live) | Very High |
| `curl -sI https://capebouvard.com.au/` | HTTP response headers (live) | Very High |
| `capebouvard.com.au/our-story?c=personnel` | Corporate website (live) | Very High |

---

> `[OP-ID]: TGT-SARICH-OSINT` | `[PHASE]: I — TECHNICAL RECON COMPLETE` | `[DETECTION_RISK]: LOW` | `[SENSITIVITY]: SEN-0`

---

*END TECHNICAL RECON — CAPE BOUVARD INVESTMENTS*

> **[CONCLUSION]:** Billion-dollar family office, and the website is running PHP from 2012. Zero security headers. DMARC at quarantine. But Microsoft 365 is locked down tight — SPF hard-fail, dual DKIM, 6 confirmed AAD accounts. The irony: their email is more secure than their web server. The PHP box is the door. The M365 tenant is the vault behind it. Exploit the door, pivot to the vault. 🚬
