# DEFENSIVE OSINT EXPOSURE AUDIT — HIGH-NET-WORTH INDIVIDUAL

> **Worked example:** Ralph Tony Sarich AO / Cape Bouvard Investments (CBI)
> **Purpose:** Defensive only. Reduce public-data exposure, harden the people and systems the remaining public data enables attacks against, and detect/respond to abuse fast.
> **Audience:** The principal and their authorized representatives (family-office security, legal counsel, or a vetted digital-risk protection provider).

---

## 0. Scope and posture

**This audit is defensive.** It inventories data that is *already public* about the principal and their family office, ranks how that data could be *abused against them*, and lays out a removal, monitoring, and hardening plan. It contains no reconnaissance, targeting, or exploitation guidance.

**What this audit is not:** a way to find more information about the principal, or a threat assessment of third parties. It assumes the data below is already out there (it is, and has been for decades) and asks only: *what harm can this do, and how do we reduce it?*

---

## 1. Data inventory — what is already public

| Category | Public data | Primary source types | Removable? |
|---|---|---|---|
| **Identity** | Full name + honorific (AO), DOB (1938), birthplace (Baskerville, WA), nationality, heritage | News, biographies, registries | No — but suppressible from aggregators |
| **Family** | Wife (married 1962), son Peter (family-office manager), daughter (deceased) | News archives | No — but suppressible from aggregators |
| **Wealth** | ~A$1.72B net worth; source (Orbital IP licensing); holdings structure | Forbes / AFR Rich Lists | No |
| **Career & corporate** | Career timeline; founder of Orbital Corp (ASX: OEC); Executive Chairman, CBI; property developments | ASIC, corporate filings, news | Registrations are public record — no; aggregator copies — partial |
| **Location** | Resides Perth WA; CBI offices Perth; WA property portfolio via CBI | News, property registries | Property titles public record — no |
| **Philanthropy** | $20M+ donations to medical research | News | No |
| **Media history** | Extensive coverage 1972–2008; inventor-of-the-year history | News archives | No |

**Bottom line:** the exploitable information is not hidden — identity, wealth, family structure, and corporate roles have been public for decades. That means the defense cannot be *removal alone*; it must be removal of the exploitable aggregation layer, hardening of humans and systems, and fast detection.

---

## 2. Abuse-risk ranking

For each exposure, the question is: *if misused, what is the harm, and what is the remedy?* Severity reflects both impact and how directly the data enables the abuse.

| Rank | Data combination | Primary abuse scenarios | Severity | Remedy |
|---|---|---|---|---|
| 1 | Identity + wealth + family + corporate roles | **Impersonation & fraud:** fake family-office entities, investment scams run in the principal's name, deepfake audio/video of a well-known figure, romance/scam use of identity | **HIGH** | Monitoring + response; never remove — so harden the humans and systems that see the principal's name |
| 2 | Son's name + gatekeeper role | **The realistic human target:** credential phishing, business-email compromise (BEC), vendor fraud aimed at the family office through its manager | **HIGH** | Harden the gatekeeper: phishing-resistant MFA, out-of-band verification, targeted education |
| 3 | Corporate registrations + office address + entity names | **Convincing BEC:** fake invoices, impersonated vendors, "new supplier onboarding" using real entity details; physical social engineering at the office | **MEDIUM-HIGH** | Email authentication (SPF/DKIM/DMARC), out-of-band vendor verification, physical access controls |
| 4 | Residence city + property holdings | Physical intrusion, burglary, harassment; "your home address is exposed" scare scams | **MEDIUM** | Property-record suppression where state law allows; physical security review; never use home address as public mailing address |
| 5 | DOB + birthplace + family details | Identity-theft building blocks; knowledge-based account-recovery attacks; genealogy-based pretexts | **MEDIUM** (high combined with #1) | Remove from data brokers; stop new disclosures; fraud alerts on financial accounts |
| 6 | Philanthropy + media history | Pretext material for charity/investment scams; deepfake training material | **LOW-MEDIUM** | Awareness; monitoring; fast takedown of fraudulent appeals |
| 7 | Net-worth estimates | The reason the principal is a target at all | **LOW (driver)** | Cannot change; the remedy is the controls above |

**Key insight:** the highest-risk exposures are not the individual data points — they are the *combinations*. Identity + wealth + family structure + corporate role is everything an impersonator or fraudster needs without harvesting anything. That combination is permanent public record, so the defense is monitoring, response, and hardening rather than removal.

---

## 3. Takedown / removal plan

### 3.1 Three tiers of removability

| Tier | What's in it | Action | Cadence |
|---|---|---|---|
| **1 — Removable** | Data-broker and people-search listings: home addresses, phone numbers, relatives, property details republished by aggregators | Inventory → opt out per site (most require identity verification) → verify removal → recheck | Recheck quarterly; brokers re-add data |
| **2 — Partially removable** | Social media (privatize accounts, remove tagged/family content), professional profiles, directory listings, digital-legacy sites | Manual cleanup by the principal/household with support | One-time + on new disclosures |
| **3 — Permanent public record** | News archives, Rich Lists, ASIC registrations, property titles, broadcast history | Accept permanence; pursue correction/removal *only* where content is inaccurate, unlawful, or harmful; focus energy on monitoring + response | Ongoing monitoring, not removal |

### 3.2 Removal workflow

1. **Inventory.** Search the principal's and family members' names on major data brokers and people-search sites; record URL, data shown, and opt-out status in a tracking log.
2. **Prioritize.** Tier 1 listings showing home address, phone, or relatives first — they enable the most direct abuse.
3. **Opt out.** Work through each site's opt-out process (typically ID verification via the data subject). Log each request and its deadline.
4. **Verify.** Confirm removal on each site; screenshot or save confirmation; mark the log.
5. **Recheck quarterly.** Brokers republish from court, property, and voter records; treat removal as recurring maintenance, not a one-time fix.

### 3.3 Legal levers (jurisdiction-dependent)

| Lever | Applies to | Caveat |
|---|---|---|
| Australian Privacy Act 1988 (APP) | Organizations mishandling personal information | Does not remove lawful news or public-record data |
| GDPR / UK GDPR right to erasure | Controllers with an EU/UK nexus — many international data brokers qualify | Must be asserted per-controller; brokers vary in compliance |
| eSafety Commissioner | Serious online abuse; removal of harmful content | Content-based, not general privacy removal |
| Defamation / correction routes | False or reputationally harmful content | Requires inaccuracy; news is usually accurate |
| ASIC / AFP reporting | Corporate impersonation and fraud | Law-enforcement route, not takedown |

**Expectation setting:** none of these remove decades of legitimate coverage. The removal program targets the *aggregation layer* (Tier 1/2) where data becomes searchable and saleable; Tier 3 is managed with monitoring and response instead.

### 3.4 Commercial support

A vetted digital-risk-protection (DRP) / takedown provider can run the inventory, opt-outs, and rechecks at scale, plus dark-web and breach monitoring. Selection criteria: defined scope, documented opt-out methodology, reporting cadence, and data-handling guarantees. Breach monitoring should also cover the family office's business email addresses.

---

## 4. Monitoring plan

| Monitor | What | Tooling / method | Cadence |
|---|---|---|---|
| **Name & entity** | Name variants (Ralph Sarich / Ralph Saric / R.T. Sarich), Orbital, Cape Bouvard, son's name | Automated alerts (search alerts), media monitoring | Continuous (automated) |
| **Impersonation** | Lookalike domains of corporate sites, fake social accounts, entities falsely claiming to be CBI | Domain watch, social search, periodic manual sweeps | Weekly automated + monthly human review |
| **Breach exposure** | Family-office business email addresses appearing in breach data | Breach monitoring service | Continuous |
| **Deepfake / media** | Synthetic audio/video of the principal | Sample checks; DRP vendor capability | Monthly |
| **Fraudulent appeals** | Charity/investment schemes using the principal's name or philanthropy history | Name monitoring + report channel | Continuous |

**Review cadence:** weekly automated sweep → monthly human review of hits → quarterly full re-audit (inventory + opt-out verification + monitoring tuning) → post-incident review. Every finding, action, and outcome goes in the tracking log.

---

## 5. Hardening the humans and systems (defense-in-depth)

Removal can't do the whole job. The data that cannot be removed is exactly what an attacker would use, so the people and systems that encounter it must be hardened.

| Layer | Action |
|---|---|
| **Gatekeeper & staff** | Phishing-resistant MFA (FIDO2 security keys) on all accounts; separate business/personal identities; education that the family is a target and how to verify unexpected contact **out-of-band** |
| **Family-office email** | SPF/DKIM/DMARC on all corporate domains; registry lock against takeover and lookalike domains |
| **Vendor & payments** | Bank/payment details never changed on email alone — verify out-of-band; dual approval above thresholds; supplier onboarding with independent verification |
| **Principal** | Stop the bleed: privatize accounts, suppress new disclosures, property-record suppression where state law allows, use a mailing address that is not the home address |
| **Household** | Same hygiene for spouse, children, and anyone with account or home access |

---

## 6. Escalation / incident response

**Standing triggers** that escalate automatically (define owners in advance):

- An impersonation account or lookalike domain with live content
- A breach alert on a family-office business email
- A fraudulent charity/investment appeal using the principal's name
- Any direct contact to family or staff claiming to represent the principal or CBI

**Response posture:**

| Situation | Route |
|---|---|
| Cybercrime | ReportCyber (ACSC) / local police; preserve evidence, don't engage |
| Threats or harassment | Police (WA / local jurisdiction) |
| Serious online abuse | eSafety Commissioner |
| Corporate impersonation / fraud | ASIC, and AFP for major fraud |
| Takedown disputes | Legal counsel with privacy/defamation expertise |

**Standing plan:** who decides, who is legal counsel, who is the DRP vendor, and a communication hold. Decide all of this before an incident, not during one.

---

## 7. Realistic expectations and success measures

A 50+ year public career cannot be erased. The objective is:

1. **Remove the exploitable aggregation layer** — broker and people-search listings gone or minimized (Tier 1/2).
2. **Harden what remains** — the gatekeeper, family-office email, vendors, and payments.
3. **Detect and respond fast** — impersonation and fraud attempts found in days, taken down quickly, and reported.

**Success measures:** broker listings declining quarter over quarter; no successful BEC or fraud; impersonations detected within days and removed; every incident logged and reviewed.

---

## 8. Per-exposure rotation & obscuration playbook

> Companion to §3 (removal), §4 (monitoring), and §5 (hardening). Each row names the data class already in §1, the **system that holds it**, and the **concrete rotation/obscuration step** the data subject (or an authorized family-office representative) executes. Rows marked **PERMANENT** are public-record items that cannot be removed; the listed action is therefore monitoring + response rather than suppression.
>
> **Posture:** every action below benefits the **data subject**. None of it relies on techniques whose primary utility is anti-detection against an investigating party. Where the wording is "obscuration", the intent is data-subject privacy minimisation (role mailboxes, no PII in public-facing surfaces), not camouflage.

### 8.1 Identity & family data

| Exposure (§1 row) | System holding it | Concrete rotation / obscuration step |
|---|---|---|
| Full name + AO + DOB + birthplace | News archives (1972–2008), Wikipedia/aggregators, genealogy sites | **AGGREGATOR:** submit Tier-1 opt-outs to people-search sites (Spokeo, Pipl, Whitepages Australia, BeenVerified) per §3.2 workflow. **WIKIPEDIA:** raise citation/source-update requests where DOB/birthplace is unsourced or outdated. **GENEALOGY:** submit removals to Ancestry, MyHeritage, FamilySearch for any profiles attached to living family members, citing the platform's living-person policy. |
| Spouse name (Patricia) + marriage date | News archives, family-tree sites, wedding-record aggregators | Same as above for the spouse's name. Family-office should instruct immediate family to privatise Facebook, lock down tagged photos, and remove maiden/married-name linkage from genealogy uploads. |
| Children's names (Peter, Jennifer) | News archives, public biographies | **PETER / LIVING CHILDREN:** opt out of people-search aggregators under the child's name explicitly; request removal of tagged photos from social platforms; request genealogy-site removal under "living person" rules. **JENNIFER / DECEASED:** handle with defamation/privacy counsel; do not amplify obituary reprints containing other family members' details. |

### 8.2 Corporate roles & entity names

| Exposure | System holding it | Concrete step |
|---|---|---|
| Director / Chairman listings | **ASIC** (ConnectOnline); permanent public record | **PERMANENT.** ASIC director records are statutory disclosure. The mitigation is **layered entity hygiene**: any new family-office activity that does not need Ralph/Peter named personally should sit in a separate holding entity (e.g. `Cape Bouvard (WA) Holdings Pty Ltd`), so future sensitive activity does not append directly to the principals' director histories. |
| Personnel bios on corporate site | **`capebouvard.com.au/our-story?c=personnel`** | **ROTATE:** replace named personnel (incl. EA Kathy Collis, GM Teresa Wong) with role titles only ("Executive Assistant to the Chairman", "General Manager"); drop photos; drop direct dial/email where it appears. Update the page quarterly and after any staff change. |
| CEO's public LinkedIn (`Lee Pinkerton`) | LinkedIn | Encourage the CEO to (a) restrict profile visibility to 1st-degree connections, (b) remove CBI from the headline, (c) rotate any visible work-email references to a role mailbox. Same for any other CBI employees enumerated via LinkedIn search. |
| Orbital Corp (`orbitalcorp.com.au`) corporate page | Corporate website | Confirm no historical photos or named-quote content references Ralph personally on the corporate site beyond the founder bio. If present, ensure founder bio uses role framing ("Founder, Orbital Engine Company") on a dedicated `/history` page rather than prominent banner content. |

### 8.3 Contact vectors (email, phone, EA)

| Exposure | System holding it | Concrete step |
|---|---|---|
| Email pattern `firstname.lastname@capebouvard.com.au` (incl. `peter.sarich@<…>`) | CBI corporate site (footer + Personnel), email-pattern databases (RocketReach, Hunter.io caches) | **ROTATE to role mailboxes.** Replace `peter.sarich@` with `chairman@`; `kathy.collis@` with `ea.chairman@`; any other named alias with a role alias. Implement catch-all forwarding from the old alias during a 90-day transition window, then disable. **PATTERN-DB OPT-OUT:** submit removal requests to RocketReach / Apollo / Hunter for any cached entries showing the old pattern. **M365 TENANT HARDENING:** enforce `p=reject` DMARC and `smtp.tls.required` outbound so spoofed internal addresses get blocked at the recipient. |
| CBI main phone `+61 8 9429 3400` & fax `+61 8 9429 3444` | CBI website footer | **ROTATE to a switchboard / role DID.** Replace direct number with a switchboard IVR; expose role DIDs only ("Investor Relations", "Press", "Suppliers") via the website. Remove fax number entirely if unused. |
| Executive Assistant: Kathy Collis (named, photo, direct contact) | CBI Personnel page | **OBSCURE via role title** (see §8.2). **ACCOUNT HARDENING:** enroll the EA mailbox under phishing-resistant MFA (FIDO2 hardware key), conditional-access policy requiring compliant device + geo fence, mail-flow audit rule flagging any auto-forward created externally, and require out-of-band (phone) callback for any payment-detail or address-book change (matches §5 vendor/payments controls). |
| Sydney office `+61 2 9523 0544` | CBI website footer | Same switchboard / role-DID treatment as Perth main. |
| Inbound media contact route | Press release templates, journalist-relationship docs | If any template publicly exposes a personal or EA mobile for "after-hours press", replace with the switchboard and a callout routing policy. |

### 8.4 Property / addresses

| Exposure | System holding it | Concrete step |
|---|---|---|
| WA property titles associated with Ralph/Peter individually | **WA Landgate** — permanent public record | **PERMANENT.** WA does not generally permit suppression. Mitigation is **title reorganisation**: future acquisitions or refinances held in holding entities (see §8.2) avoid appending additional records to the named individuals. For existing titles, retain the existing public record and compensate via residential security review and a non-residential mailing address (see below). |
| Mailing address = home address | Family-office mail, supplier invoices | **ROTATE:** establish a CMRA / commercial mail-receiving agency address or a PO Box at a Perth post office as the publicly-listed correspondence address on ASIC, CBI website footer, and supplier onboarding forms. The principal's physical address is never the public mailing address. |
| Office address "Level 19, Alluvion, 58 Mounts Bay Road, Perth" | CBI website | **OBSCURE:** list "Alluvion Tower, Perth CBD" (building + city only) on the public site; reserve the full street address for investor-relations and legal mailings behind a contact form. |
| Vehicle / vessel / aircraft registrations | WA DoT, AMSA, CASA registries | **PERMANENT** when registered to an individual. **MITIGATION:** register any future high-value assets to the holding entities from §8.2 rather than to the principals personally. |

### 8.5 Wealth signals

| Exposure | System holding it | Concrete step |
|---|---|---|
| A$1.72B net-worth figure | AFR Rich List, Forbes Australia — annual, not removable | **PERMANENT** as a published historical estimate. **MITIGATION:** the control set is hardening humans and systems per §5 — the rich-list number is the *reason* the principal is targeted, not a separately-fixable exposure. Track republishing on Tier-1/2 aggregators (people-search sites republishing the figure) and opt out per §3.2. |
| Banking relationships (CBA / Westpac / NAB / ANZ presumed) | Not publicly disclosed | **HARDEN:** request a `flagged-account` note or fraud-victim advisory on retail banking profiles for the principal and immediate family; enroll under each bank's "high-net-worth" fraud team if available; require in-branch verification for any address/contact change. |

### 8.6 Philanthropy & media history

| Exposure | System holding it | Concrete step |
|---|---|---|
| $20M+ philanthropic donations (incl. 2008 medical-research donations, paternal quote about "moral obligation") | News archives, charity sites, YouTube broadcast archives | **PERMANENT** in news. **CHARITY SITES:** request that recipient charities replace first-person quotes with family-office attribution; remove named photographs of the principal from current fundraising pages. **INDIRECT BENEFIT:** raising the cost of impersonation appeals by reducing the contextual fidelity an impersonator can assemble from the charity's own site. |
| Broadcast appearances (`The Inventors`, 1972) | ABC archive, YouTube reposts, news clipping aggregators | **PERMANENT** in ABC archive. **AGGREGATOR OPT-OUT** for reposts on YouTube/Trove/news-clip sites per §3.2; submit copyright/DMCA only where a repost uses owned footage without permission. |

### 8.7 DNS, domain, certificate hygiene (defensive)

| Vector | Who controls it | Concrete step |
|---|---|---|
| **`capebouvard.com.au`** — primary corporate domain | CBI / registrar (e.g. Melbourne IT, Crazy Domains, Netregistry) | **REGISTRY LOCK:** enable registrar lock + clientHold-equivalent (where the registry supports it — `.au` via auDA; ask registrar for the highest lock tier available) to prevent unauthorised transfer or DNS hijack. **WHOIS:** enable `auDA WHOIS Privacy` (role-based contact, no individual name on the public record) if eligible. |
| Email authentication on `capebouvard.com.au` | CBI's DNS zone (or their MSP) | **DMARC `p=reject`** with at least `pct=100; rua=mailto:dmarc@capebouvard.com.au; ruf=mailto:dmarc@capebouvard.com.au`. **SPF:** `-all` (hard fail) referencing only approved senders. **DKIM:** signing on every outbound system (M365, any bulk-sender). **MONITOR:** a weekly review of DMARC aggregate reports for new senders or spikes. |
| Likely typosquat / lookalike domains (e.g. `capebouvard.com`, `cape-bouvard.com`, `capebouvardinvestments.com.au`, `capebouvard-inv.com.au`, `cbeenbouvard.com.au`) | Not held — currently available | **DEFENSIVE REGISTRATION:** register the top 20–30 likely variants across `.com`, `.com.au`, `.net.au` as a one-off project; park them on a registrar sinkhole that 301-redirects to the real corporate site for legitimate variants, and serves a generic notice for malicious-feeling variants. **CT-LOG MONITORING:** subscribe to certificate-transparency logs (e.g. Censys, crt.sh) for `capebouvard` so any new TLS cert issuance is detected within hours. |
| Internal subdomains leaking via MTA / cert | M365, any web property | **MTA-STS + TLS-RPT** on `capebouvard.com.au` to force encryption inbound and report downgrade attempts. **CERT SAN HYGIENE:** when issuing TLS certs (Let's Encrypt or commercial), keep the SAN list minimal and exclude any internal hostname from public CT logs by using a wildcard cert only where necessary (and then rotate frequently). |
| Nameservers / SOA admin email | DNS zone | Replace the SOA RNAME with `hostmaster.capebouvard.com.au` (role) rather than any individual CBI staff email; rotate the address it forwards to annually. |

### 8.8 Web / social surface — HTTP response headers & social metadata

| Surface | Where it is | Concrete step |
|---|---|---|
| Corporate site `capebouvard.com.au` — HTTP response headers | nginx / CDN config | Add (in order of priority): `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`; `Referrer-Policy: no-referrer` so outbound links don't leak path/query/identity; `Content-Security-Policy` with an explicit allowlist to cut XSS-driven redirect pages; `Permissions-Policy` denying unused features; `X-Frame-Options: DENY` and `X-Content-Type-Options: nosniff`. These cut impersonation-site cloning fidelity and reduce identity-correlatable referrer leaks. |
| Social / Open-Graph metadata (`og:title`, `og:description`, `og:image`, Twitter card) | `<head>` of corporate site + any CBI-published press pages | Audit and strip named-individual content from `og:` and Twitter card metadata on any public-facing page that is not specifically an executive bio. Replace "Peter Sarich, Chairman" → "Office of the Chairman, Cape Bouvard Investments" in shared-link previews. |
| Schema.org / JSON-LD structured data | Corporate site, press releases | Audit JSON-LD `Person` blocks; replace them with `Organization` blocks for corporate pages. Remove the `Person` schema entirely from the personnel page once role-only titles have been adopted (§8.2). |
| LinkedIn company page (`/company/cape-bouvard-investments`) | LinkedIn | Restrict employee visibility to current staff only; remove named personnel from the "People" tab where LinkedIn exposes it; rotate the company-page admin account and enforce SSO + hardware-key MFA on it. |
| Family members' personal social | Facebook / Instagram / X | Privatise accounts; remove historical tags from public posts; revoke third-party app authorisations on a quarterly review; set "Use Facebook as [page]" off; turn off activity-log public visibility. |
| Search-engine indexing of personal content | Google, Bing | Submit removal requests for any cached page exposing unredacted PII (home address, phone, DOB); use `noindex,nofollow` on press pages that incidentally name family members; use a `robots.txt` `Disallow: /personnel/` once the personnel page moves to authenticated access. |
| Email auto-replies / signatures | Outlook/Gmail signature templates | Strip named-signature mobile numbers, direct extensions, and home addresses from auto-reply templates; sign with role title + switchboard only. |

### 8.9 Per-target execution checklist (template)

The principal's authorised representative (family-office security lead or DRP vendor) can run the following on a fixed cadence. Each row carries a target system, a target system identifier (where applicable), the change to make, and the verification step.

| # | Cadence | Target system | Specific change | Verify |
|---|---|---|---|---|
| 1 | One-off + on each staff change | `capebouvard.com.au/our-story?c=personnel` | Replace named individuals with role titles; drop photos; remove direct dial/email | Curl the page; confirm no individual names in HTML text |
| 2 | One-off | CBI M365 tenant | Enable security defaults + FIDO2-only MFA + conditional access; create role aliases (`chairman@`, `ea.chairman@`, `investor.relations@`); retain old aliases for 90 days then disable | Sign in as the chairman; confirm role alias in use; check forwarding rules |
| 3 | One-off | DNS zone `capebouvard.com.au` | Enable registry lock; replace SOA RNAME role; publish DMARC `p=reject`; publish MTA-STS | `dig TXT _dmarc.capebouvard.com.au`; `dig TXT _mta-sts.capebouvard.com.au`; check WHOIS privacy enabled |
| 4 | One-off | Defensive domain procurement | Register the 20–30 most-likely typo/lookalike domains across TLDs | `crt.sh` and `Censys` searches return only the defensive-registered hits |
| 5 | Quarterly | Data brokers (Tier 1) | Run §3.2 inventory + opt-out cycle on the principal, spouse, son, and grandchild | Compare the Tier-1 listing count quarter-on-quarter; success measure per §7 |
| 6 | Quarterly | Personnel page audit | Re-curl the personnel page; grep HTML for any individual name, email, phone, or EA reference | Zero matches from grep |
| 7 | Quarterly | FIDO2 key & account review | Reissue any hardware key older than 24 months; rotate role mailbox passwords; confirm inbox auto-forward rules absent | M365 admin centre: zero external auto-forwards; hardware-key attestation fresh |
| 8 | Quarterly | Property-record diff | Landgate + RP Data: search both principals individually and via holding entities | New property acquisitions sit in holding entities, not personal names |
| 9 | Quarterly | Social-account hygiene review | Walk through principal / spouse / son / grandchild socials; tighten privacy settings; remove tags | Each account shows minimum public visibility for the demographic |
| 10 | Continuous | DMARC RUA report | Weekly review of aggregate report; investigate new senders; spike in failures | Failure count trending toward zero; no senders outside the allowlist |

---

> **Prepared as a defensive assessment for the principal and authorized representatives. No targeting or offensive content is included.**
