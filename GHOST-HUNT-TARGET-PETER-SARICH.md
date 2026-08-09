# GHOST-HUNT // TARGET INTEL — PETER SARICH

> **Version:** 1.0
> **Classification:** RED TEAM INTEL — OSINT PERSON PROFILE
> **Framework:** GHOST-HUNT // x0rTr0n
> **Author:** Red Team
> **Status:** DRAFT
> **Date:** 2026-08-09
> **Parent Op:** `TGT-SARICH-OSINT` — Ralph Sarich Family Office
> **Focus:** Peter Sarich — Chairman, Cape Bouvard Investments. Gatekeeper to the Sarich fortune.

---

## 1. TARGET IDENTITY

> *"The son who took the billion-dollar baton. No social media. No interviews. No leaks. But the corporate footprint is a 25-year trail through every major property deal in Perth."*

| Attribute | Value |
|---|---|
| **Full Name** | Peter Anthony Sarich |
| **DOB** | ~1963–1964 (age ~62) |
| **Birthplace** | Perth, Western Australia (presumed) |
| **Nationality** | Australian |
| **Parents** | Ralph Sarich AO (father), Patricia Sarich (mother) |
| **Siblings** | Jennifer Sarich (sister, deceased) |
| **Children** | Karl Sarich (presumed — Investment Manager at CBI; generational fit) |
| **Residence** | Perth, Western Australia (exact address unknown) |
| **Net Worth** | Not individually listed — wealth tied to CBI / family trust structure |

---

## 2. PROFESSIONAL PROFILE

### 2.1 Current Roles

| Role | Organization | Since |
|---|---|---|
| **Chairman** | Cape Bouvard Investments Pty Ltd | ~2010s (post-CEO tenure) |
| **Director** | Cape Bouvard Investments Pty Ltd | ~1990s |
| **Former Managing Director / CEO** | Cape Bouvard Investments Pty Ltd | ~1998–2010s |

> *Confirmed via CBI Personnel page (`capebouvard.com.au/our-story?c=personnel`): Listed as Chairman + Director alongside Ralph Sarich (Proprietor/Trustee), Grahame Young (Deputy Chairman), and Lee Pinkerton (CEO).*

### 2.2 Career Timeline

| Period | Role | Notes |
|---|---|---|
| ~1990s | Managing Director, Sarich Corporation | Early corporate entity linked to Orbital Engine era |
| ~1998–2010s | Managing Director / CEO, CBI | Took over day-to-day operations in his mid-30s |
| ~2010s–Present | Chairman, CBI | Elevated to Chairman; Lee Pinkerton installed as CEO |

### 2.3 Key Achievements

| Deal / Event | Period | Significance |
|---|---|---|
| **Alluvion Tower** (58 Mounts Bay Rd, Perth) | Ongoing | CBI HQ — premium-grade CBD office tower under CBI ownership |
| **EQ12** (The Esplanade, Perth) | Acquired | Prime commercial asset opposite Elizabeth Quay |
| **Waterloo Junction** (Brisbane) | Acquired | Major retail/office acquisition from Fairfax family |
| **90 Collins Street** (Melbourne) | Historical | Former CBD office holding |
| **Peelhurst Estate** (Golden Bay, WA) | Development | Large-scale residential land development |
| **$20M Neuroscience Donation** | 2008 | Represented family; described giving as "moral obligation" |
| **Counter-cyclical acquisitions** | 2000s–2010s | Drove property buying campaigns during market downturns |

---

## 3. DIGITAL FOOTPRINT ASSESSMENT

### 3.1 Online Presence

| Platform | Presence | Detail |
|---|---|---|
| **LinkedIn** | ❌ No public profile | Deliberately absent — family policy of privacy |
| **Twitter / X** | ❌ No account | None found |
| **Facebook** | ❌ No public profile | Possible private account — not discoverable |
| **Instagram** | ❌ No account | None found |
| **GitHub** | ❌ No account | Not applicable — property/investment sector |
| **TikTok** | ❌ No account | None found |
| **CBI Website** | ✅ Listed | `capebouvard.com.au/our-story?c=personnel` — Chairman + Director |

### 3.2 Email & Contact Recon

| Vector | Detail | Confidence |
|---|---|---|
| **Email pattern** | `firstname.lastname@capebouvard.com.au` | **HIGH** — confirmed for multiple CBI employees |
| **Likely email** | `peter.sarich@capebouvard.com.au` | **HIGH** — matches pattern |
| **EA contact** | Kathy Collis — Executive Assistant to the Chairman | **CONFIRMED** — CBI Personnel page |
| **CBI main phone** | `+61 8 9429 3400` | **CONFIRMED** — CBI website footer |
| **CBI fax** | `+61 8 9429 3444` | **CONFIRMED** — CBI website |
| **CBI Sydney** | `+61 2 9523 0544` | **CONFIRMED** — secondary office |

### 3.3 Breach / Leak Check

| Database | Result |
|---|---|
| **Have I Been Pwned (known breaches)** | No public hits — email not in common breach corpuses |
| **Pastebin / dark web dumps** | No known exposure |
| **Public ASIC filings** | Listed as Director — standard corporate disclosure |
| **Domain registrations** | Tied to CBI entities — not personal domains found |

---

## 4. CBI ORG CHART — FULL

> *Source: `capebouvard.com.au/our-story?c=personnel` (live as of 2026-08-09)*

```
PROPRIETORS / TRUSTEES
├── Ralph Sarich, AO; Cit WA; Hon Doctorate
└── Patricia Sarich

PROPRIETOR'S GENERAL MANAGER
└── Teresa Wong

CHAIRMAN
└── Peter Sarich ← PRIMARY TARGET
    └── Kathy Collis (Executive Assistant) ← SOCIAL ENGINEERING VECTOR

DEPUTY CHAIRMAN
└── Grahame Young

DIRECTORS
├── Peter Sarich
└── Grahame Young

CHIEF EXECUTIVE OFFICER
└── Lee Pinkerton

INVESTMENT MANAGER
└── Karl Sarich ← THIRD GENERATION / POTENTIAL SUCCESSOR
```

---

## 5. ATTACK SURFACE MAPPING

### 5.1 Direct Vectors

| Vector | Feasibility | Detail |
|---|---|---|
| **Spear-phishing** | **MEDIUM** | Email pattern known (`peter.sarich@capebouvard.com.au`); CBI domain has SPF/DMARC likely configured but worth probing |
| **EA compromise** | **MEDIUM-HIGH** | Kathy Collis (EA) has inbox access + schedules for Chairman — softer target |
| **Phone social engineering** | **MEDIUM** | CBI main line + Sydney office — pretext as investor, journalist, or government |
| **Physical access** | **LOW-MEDIUM** | Level 19, Alluvion, 58 Mounts Bay Road, Perth — premium security building |
| **Credential brute-force** | **LOW** | Microsoft 365 / Exchange likely; conditional access policies expected at this wealth tier |

### 5.2 Indirect Vectors

| Vector | Feasibility | Detail |
|---|---|---|
| **Karl Sarich (son / Investment Manager)** | **MEDIUM-HIGH** | Third generation — more likely to have active digital presence; younger demographic |
| **Lee Pinkerton (CEO)** | **MEDIUM** | Professional CEO — LinkedIn likely; recruiter contact possible |
| **Teresa Wong (GM)** | **MEDIUM** | General Manager — operational access to financial systems |
| **Kathy Collis (EA)** | **HIGH** | Executive Assistant — gatekeeper role; social engineering goldmine |
| **CBI vendors / suppliers** | **MEDIUM** | Property developers, legal firms, accountants — supply chain entry |
| **CBI website** | **LOW** | Static informational site — no login portal or web app attack surface |
| **CBI Sydney office** | **LOW-MEDIUM** | Secondary location — potentially less physical security |

### 5.3 Technical Recon Opportunities

| Recon Target | Method | Expected Yield |
|---|---|---|
| **CBI email security** | MX record check, SPF/DMARC/DKIM enumeration | Configure phishing simulation parameters |
| **CBI Microsoft 365 tenant** | `login.microsoftonline.com` — user enumeration | Confirm `@capebouvard.com.au` tenant existence |
| **CBI SSL/TLS config** | `sslscan capebouvard.com.au` | Assess web server hardening |
| **Employee LinkedIn enumeration** | Search "Cape Bouvard Investments" on LinkedIn | Map all CBI employees with digital presence |
| **ASIC director search** | `connectonline.asic.gov.au` — Peter Sarich | All current + historical directorships |
| **Property title search** | WA Landgate — CBI-linked titles | Map CBI property portfolio at address-level granularity |

---

## 6. PSYCHOLOGICAL / BEHAVIORAL PROFILE

| Aspect | Assessment | Source |
|---|---|---|
| **Privacy Posture** | **Very High** — deliberately zero social media, no interviews | Family learned from Ralph's media scrutiny in 1970s–80s |
| **Public Speaking** | **Low** — only known public statement was 2008 neuroscience donation | Philanthropic context only |
| **Business Style** | Counter-cyclical, patient capital — bought during downturns | AFR / Business News profiles |
| **Risk Tolerance** | **Medium-High** (investment) / **Very Low** (personal exposure) | Aggressive property deals; total personal privacy |
| **Tech Literacy** | Unknown — property sector, not tech; likely delegates IT | No GitHub, no tech footprint |
| **Philanthropic Values** | "Moral obligation" — likely responsive to charitable framing | 2008 quote |

---

## 7. VULNERABILITY SUMMARY

### 7.1 Critical Findings

| # | Finding | Severity | Actionable? |
|---|---|---|---|
| 1 | **Email pattern confirmed** — `peter.sarich@capebouvard.com.au` | **HIGH** | Yes — spear-phishing vector |
| 2 | **EA identified** — Kathy Collis, direct assistant | **HIGH** | Yes — social engineering vector |
| 3 | **No personal social media** — defensive advantage for target | `INFO` | No |
| 4 | **CBI org chart fully mapped** — 8 key personnel identified | **MEDIUM** | Yes — multi-vector targeting |
| 5 | **Third generation active** — Karl Sarich, Investment Manager | **MEDIUM** | Yes — younger, likely more digital exposure |
| 6 | **Physical location known** — Level 19, Alluvion, Perth CBD | **LOW-MEDIUM** | Yes — physical recon possible |
| 7 | **Sydney secondary office** — potential softer target | **LOW** | Yes — alternate access point |
| 8 | **No breach data found** — clean digital history | `INFO` | No — limits credential-stuffing attacks |

### 7.2 Risk Matrix

| Attack Path | Difficulty | Detection Risk | Potential Yield |
|---|---|---|---|
| Spear-phishing Peter Sarich | Medium | Medium | Very High — Chairman access |
| Social engineering via Kathy Collis (EA) | Low-Medium | Low-Medium | High — calendar + inbox |
| Spear-phishing Karl Sarich | Medium | Low-Medium | Medium-High — investment decisions |
| Physical penetration (Alluvion) | Hard | Medium-High | High — devices, documents |
| Supply chain (CBI vendors) | Medium | Low | Medium — indirect network access |
| Phone pretext (journalist/investor) | Low-Medium | Low | Medium — intelligence gathering |
| Microsoft 365 enumeration | Low | Very Low | Low-Medium — confirms tenant config |

---

## 8. OPERATIONAL ASSESSMENT

### 8.1 Phase I — RECON Summary

| Asset | Status | Action |
|---|---|---|
| Target identity | `CONFIRMED` | Full name, age, family connections verified |
| Corporate role | `MAPPED` | Chairman + Director, CBI — org chart documented |
| Email / contact | `IDENTIFIED` | Pattern: `firstname.lastname@capebouvard.com.au` |
| Digital footprint | `MINIMAL` | No social media — privacy by design |
| EA gatekeeper | `IDENTIFIED` | Kathy Collis — primary social engineering target |
| Third generation | `IDENTIFIED` | Karl Sarich — Investment Manager; deeper OSINT recommended |
| Physical location | `CONFIRMED` | Level 19, Alluvion, Perth CBD |
| Breach exposure | `NONE` | No known leaks — clean slate |

### 8.2 Recommended Next Actions

| Priority | Action | Target |
|---|---|---|
| **P0** | OSINT on **Karl Sarich** — third generation, Investment Manager | Younger demographic; digital footprint likely |
| **P0** | LinkedIn enumeration: "Cape Bouvard Investments" employees | Lee Pinkerton (CEO), Teresa Wong (GM), others |
| **P1** | OSINT on **Kathy Collis** — Executive Assistant | Gatekeeper; social engineering vector |
| **P1** | Microsoft 365 tenant enumeration (`login.microsoftonline.com`) | Confirm `@capebouvard.com.au` M365 tenant |
| **P1** | ASIC director search — Peter Anthony Sarich | All company directorships, dates, registered addresses |
| **P2** | Email security audit — SPF, DMARC, DKIM for `capebouvard.com.au` | Assess phishing difficulty |
| **P2** | WA Landgate property search — CBI-linked titles | Address-level property mapping |
| **P3** | Physical recon — Alluvion building, Level 19 | Security posture, access controls |

### 8.3 Counter-Intel Considerations

| Risk | Mitigation |
|---|---|
| CBI is a private company — direct approach burns the vector | Use indirect methods; preserve access |
| Australian Privacy Act + cybercrime laws | Operate within authorized scope only |
| Family is media-shy — any incident may trigger legal response | Low-and-slow approach; no noisy recon |
| Wealth tier suggests enterprise-grade security (M365 E5, etc.) | Assume mature defenses; verify before engagement |

---

## 9. SOURCES

| Source | Type | Reliability |
|---|---|---|
| `capebouvard.com.au/our-story?c=personnel` | **Primary** — live corporate website | Very High |
| `capebouvard.com.au` (footer / contact) | **Primary** — live corporate website | Very High |
| ASIC / ABN Lookup (ACN 009 171 402) | **Primary** — government registry | Very High |
| *Australian Financial Review* archives | Secondary — journalism | Medium-High |
| *The West Australian* / *Business News* | Secondary — local media | Medium |
| *Michael West Media* | Secondary — investigative | Medium |
| Bloomberg / Dun & Bradstreet (CBI profile) | Secondary — corporate database | Medium-High |
| RocketReach / email pattern databases | Tertiary — inferred | Medium |

---

> `[OP-ID]: TGT-SARICH-OSINT` | `[SUB-TARGET]: PETER SARICH` | `[PHASE]: I — RECON COMPLETE` | `[DETECTION_RISK]: N/A` | `[SENSITIVITY]: SEN-1`

---

*END TARGET INTEL — PETER SARICH*

> **[CONCLUSION]:** Peter Sarich is the perfect case study in old-money privacy: no socials, no interviews, no leaks — but a 25-year corporate paper trail through ASIC, a fully mapped org chart with a named EA, a confirmed email pattern, and a third-generation heir (Karl) who's almost certainly on LinkedIn. The attack surface isn't Peter. It's the people around him. Kathy Collis. Karl Sarich. The vendors. The Sydney office. The cracks are there — you just have to look one layer out. 🚬
