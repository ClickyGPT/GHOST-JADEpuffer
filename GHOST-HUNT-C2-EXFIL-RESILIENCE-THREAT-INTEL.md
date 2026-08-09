# Common C2 Exfiltration Resilience Techniques and Their Detection Side

> **Document type:** Stand-alone research note — threat intelligence and detection-engineering perspective.
> **Audience:** detection engineers, SOC analysts, threat-intel consumers, blue-team leads, and lab researchers who study offensive tooling for defensive purposes.
> **Posture:** Defender-side analysis. **No patches** are provided for any offensive tooling in this repository (or anywhere else). Each technique is described at a conceptual level, mapped to MITRE ATT&CK, and paired with detection-engineering guidance.
> **Companion file:** `DEFENSIVE-OSINT-EXPOSURE-AUDIT.md` covering exposure of a high-net-worth individual. This file covers the operator-side of an exfiltration campaign.
> **Out of scope:** offensive guidance, code that any operator could plug into an existing tool, evasion tricks not specific to exfiltration loops, post-exploit lateral-movement techniques that aren't directly tied to data egress.

---

## 0. Reading guide

The document is organised in two halves:

- **Sections 1–3** — **Catalogue of resilience techniques.** Each entry describes an attacker-side technique (what it is, why it works against defenders, ATT&CK T-code, sub-technique, and data sources), then pairs it with a defender-side detection side (network indicators, host indicators, telemetry surfaces, and example detection logic).
- **Sections 4–7** — **Detection engineering.** Cross-cutting guidance on the telemetry required, the architecture for setting it up, the trade-offs, and a list of high-yield detection rules expressed in Suricata / Zeek / Sigma / KQL-flavoured pseudocode that a SOC can adapt.

A quick mnemonic: every resilience technique is paired with at least one indicator and at least one detection rule. Where a technique is paired with no clean detection, the entry is marked **[low-yield detection]** so the SOC knows where to invest elsewhere first.

---

## 1. The reference exfil loop

The shape of the loop we are analysing — described abstractly, not as code — is:

1. **Identify** the file(s) to be exfiltrated on the host.
2. **Encrypt** the payload with a symmetric key (Fernet / AES-GCM / ChaCha20-Poly1305).
3. **Chunk** the ciphertext into fixed-size slices.
4. **POST** each slice to a CDN-fronted endpoint, attaching custom headers (chunk ID, chunk sequence) and a fixed `User-Agent` masquerade.
5. **Cover** the host by overwriting the source file and removing it on success.
6. **Receive** the slices server-side, stitching them by ID and sequence.

A naive implementation of this loop fails in three ways that the resilience techniques below address:

- **Beaconing cadence is regular** → defenders see a fixed rhythm.
- **One chunk per request** → defenders see many sequential POSTs.
- **Plain HTTP/1.1 with no reuse** → defenders see the full TLS handshake per chunk and a one-shot socket pattern.

The resilience techniques in §3 each address one or more of these patterns. The detection-engineering work in §4–5 builds telemetry that surfaces any of them.

---

## 2. ATT&CK T-code legend

The MITRE ATT&CK mapping concentrates in three top-level tactics:

- **Command and Control (TA0011)** — `T1071`, `T1090`, `T1095`, `T1572`, `T1573`, `T1008`, `T1568`.
- **Exfiltration (TA0010)** — `T1041`, `T1567`.
- **Defense Evasion (TA0005)** — `T1036`, `T1027`, `T1132`.

The most heavily used primary codes in this catalogue are:

- `T1071.001` — Application Layer Protocol: Web Protocols
- `T1573.001/002` — Encrypted Channel (Symmetric / Asymmetric Cryptography)
- `T1041` — Exfiltration Over C2 Channel
- `T1567` — Exfiltration Over Web Service (and `.001` / `.002` sub-techniques)
- `T1132.001/002` — Data Encoding (Standard / Non-Standard)
- `T1090.002/003` — Proxy: External Proxy, Multi-hop Proxy
- `T1568` — Dynamic Resolution
- `T1008` — Fallback Channels

Each technique below cites one or more of these. Sub-techniques are referenced where they materially change the indicator set.

---

## 3. Catalogue of resilience techniques

Each entry has the same shape:

- **What it is** — one-paragraph description of the attacker action.
- **Why it works against defenders** — defender gap being exploited.
- **ATT&CK mapping** — T-codes and tactics.
- **Detection side** — network indicators, host indicators, and the telemetry surfaces that observe them, plus a per-entry detection note.
- **False-positive profile** — what benign traffic / behaviour looks similar.

### 3.1 Jittered / decorrelated back-off

**What it is.** On retry, instead of a fixed or linear back-off (e.g. `2*(attempt+1)` seconds per attempt), an operator-driven resilience technique is to apply AWS-style **decorrelated jitter**: `sleep = random_between(base, prev_sleep * 3)`, capped. The sleep interval is randomised per-attempt and per-chunk so the same retry sequence is non-reproducible across runs.

**Why it works against defenders.** Fixed or linear back-off is trivially detected by cadence analysis: a process that retries with a `2s, 4s, 6s` sequence is observable on the wire and in the EDR timer queue. Decorrelated jitter shifts the per-attempt inter-arrival time into a wider distribution and breaks the simple regression-style detector while still being bounded (i.e. not catastrophically slow).

**ATT&CK mapping.**

- `T1071.001` — Application Layer Protocol: Web Protocols (the retry surface).
- `T1027` — Obfuscated Files or Information (the randomness hides the cadence pattern).

**Detection side.**

- *Network:* inter-arrival time distribution for a single flow (src_ip, dst_ip, dst_port, sni_tuple) becomes heavy-tailed rather than narrow around a fixed value. To detect: collect flow records (NetFlow, Zeek `conn.log`), bucketise per (host, destination) pair each minute, and compare the variance of inter-arrival times. Defender-side systems such as the RITA framework or its successors do exactly this.
- *Host:* the process making the requests is observed by EDR reading `nanosleep`/`select` syscall durations; decorrelated jitter produces a distinctive log-normal pattern.
- *Telemetry surfaces:* Zeek `conn.log` + custom timing analysis, Suricata `flow` records, Wireshark-pcap post-hoc, EDR syscall telemetry.

**False-positive profile.** Genuinely flaky mobile / IoT clients with poor connection management produce jittered patterns. Exclude known low-trust device classes via asset context (mobile, BYOD, kiosk) before raising alerts.

---

### 3.2 Connection / TLS reuse

**What it is.** A naïve chunk loop opens a fresh TLS connection per chunk; an operator-driven resilience technique is to keep a single TCP/TLS session alive across chunks and stream multiple chunks within it. This implies **HTTP keep-alive**, **TLS session resumption (RFC 5246 ticket or 8446 PSK)**, and **HTTP/2 multiplex** (multiple chunks on one connection, different streams).

**Why it works against defenders.** A one-shot-socket-per-chunk pattern is itself a strong indicator: legitimate web clients almost never issue one POST and disconnect. Connection reuse moves the traffic into the same shape as a legitimate web session, including TLS resumption that most clients do legitimately.

**ATT&CK mapping.**

- `T1071.001` — Application Layer Protocol: Web Protocols.
- `T1573.001` / `T1573.002` — Encrypted Channel.

**Detection side.**

- *Network:* ratio of *connections* to *requests* per (src_ip, destination) over a sliding window. Legitimate clients tend to make many requests per connection; naïve C2 loops tend to make exactly one. Track ratio outliers.
- *Network (deeper):* TLS session-ticket reuse across what should be unrelated connections. Clients that resumption-stick to one server are mostly normal; clients that resumption-stick to a destination no other host in the org talks to is anomalous.
- *Host:* EDR observation of socket reuse — the process opens `socket()` once, then calls `send()` many times via `SSL_write`. Naïve C2 closes the SSL context between chunks.

**False-positive profile.** Browsers and legitimate API clients exhibit exactly this pattern. Detection must be context-bound (the destination in question is not a corporate-sanctioned web service, OR the ratio is anomalous across the whole org for this destination, OR the process doing the reuse is unknown to your inventory).

---

### 3.3 HTTP/2 stream-multiplexed exfil

**What it is.** Single HTTP/2 connection, multiple concurrent streams. The operator-driven technique is to launch multiple chunks as parallel `HTTP/2` streams on one TLS session, eliminating sequential waiting while keeping a single TCP/TLS fingerprint.

**Why it works against defenders.** Stream multiplexing hides chunk count from naïve detectors that count `HTTP/1.1` POST methods on a connection basis. HTTP/2 also obscures the request order — frames can interleave across streams.

**ATT&CK mapping.**

- `T1071.001` — Application Layer Protocol: Web Protocols.
- `T1090.002` — Proxy: External Proxy (the fronted CDN is often itself a proxy hop).

**Detection side.**

- *Network:* HTTP/2 connection count vs stream count. Track per (src_ip, dst_ip, dst_port) the metric *concurrent_streams / connections*. Values much larger than typical for that destination are an indicator.
- *Network:* HTTP/2 SETTINGS frames and `WINDOW_UPDATE` patterns. Browsers issue these in a well-known shape; an unknown client with custom settings is inspectable.
- *TLS:* JA3S / JA4 server fingerprint is constant for the CDN; the unusual indicator is on the *client* side (JA3 / JA4 fingerprint).
- *Telemetry surfaces:* `nghttp2`-aware Zeek or Suricata logs, Envoy/Istio metrics if the org proxies egress, `alpn="h2"` connection inventory.

**False-positive profile.** Most egress flows in modern organisations are HTTP/2. The differentiating signal is *client-side* — JA3/JA4 / HTTP/2 SETTINGS fingerprint — combined with the destination not being a known corporate endpoint.

---

### 3.4 Chunk-resume / checkpointed uploads

**What it is.** The server returns a checkpoint token after each successful chunk (`X-Last-Seq` or similar). The client resumes from the next sequence on retry instead of restarting from `seq=0`. A naïve loop on failure restarts at zero.

**Why it works against defenders.** Restart-from-zero means the partial upload is repeated on every retry — visible as monotonically increasing re-transmits. Checkpointed resume keeps retries small and indistinguishable from continuation.

**ATT&CK mapping.**

- `T1071.001` — Application Layer Protocol: Web Protocols.
- `T1008` — Fallback Channels (the resume token can act as a fallback signal).

**Detection side.**

- *Network:* repeated `POST /` requests with non-zero chunk sequences after a connection drop. The pattern is "server returned 4xx/5xx at chunk N, next request is chunk N+1, not chunk 0". On the wire, parse the chunk sequence header and detect restart-from-zero vs resume-from-N+1 patterns.
- *Host:* EDR can observe the persistent state file (a small SQLite or JSON file keeping `last_seq` per chunk ID) — and the subsequent read pattern in the file.
- *Telemetry surfaces:* Suricata `http` events with parsed custom-header logic, EDR file-creation/write syscalls with small dotfiles in `$TMPDIR`.

**False-positive profile.** Some legitimate file-upload services (`tus.io`, AWS S3 multipart, YouTube resumable uploads) use the same protocol. Detection must fingerprint the destination — these are well-known SaaS endpoints; C2 destinations are not.

---

### 3.5 Inter-chunk jitter + active-hours operation

**What it is.** Sleeps between successful chunks, not just on retries. Operator-driven techniques range from random sleeps in [N, 3·N] seconds between chunks, to "only emit chunks when the user's UI is active" (mouse / keyboard events polled), to "only emit chunks during business hours in the user's timezone".

**Why it works against defenders.** Bursts of activity at low-rate-but-extended-time windows are easily mistaken for background file-sync or backup. Active-hours gating makes the activity invisible during SOC off-hours and invisible during periods the user is "doing nothing".

**ATT&CK mapping.**

- `T1071.001` — Application Layer Protocol: Web Protocols.
- `T1027` — Obfuscated Files or Information (jitter and gating make the rhythm non-detectable).

**Detection side.**

- *Network:* long-window inter-arrival distribution; long tails on outgoing POSTs during user-sleep windows are anomalous. Burst-detection over a 24-hour window per host works better than 1-hour burst-detection.
- *Host:* process CPU/IO footprint at moments when the host is in low-input state (no mouse / keyboard activity) is a strong signal. EDR reads `GetLastInputInfo` on Windows, `loginctl idleHint` on systemd, or just the absence of recent login session activity.
- *UEBA:* user-entity behaviour analytics detects "this user has no recent activity and yet this process is sending data".

**False-positive profile.** Backup clients, antivirus updaters, software-telemetry agents, and minor business apps that run nightly. Asset inventory and approval state of the running process is the disambiguator.

---

### 3.6 Cover traffic / decoy requests

**What it is.** Alongside real chunk POSTs, the operator-driven technique is to issue *decoy* requests to the same endpoint (or a sibling CDN edge) that look like the real payload but carry dummy content. The decoys match cadence, shape, and header style so the traffic *and* its absence (when chunking stops) are both plausible to a defender.

**Why it works against defenders.** Even volume-cadence analyses are defeated: the operator can pause real exfil and continue decoys, or vice versa, with the same per-flow volume profile. Tripwire-style decoys at known endpoints can also probe detection before sending real data.

**ATT&CK mapping.**

- `T1071.001` — Application Layer Protocol: Web Protocols.
- `T1090.002` — Proxy: External Proxy (the CDN is the cover).

**Detection side.**

- *Network:* payload content entropy. Real ciphertext (Fernet, AES-GCM) has high-MSE entropy (≈ 7.999 bits/byte). Decoy payloads that are not random — fixed strings, repeated blobs — have lower entropy. Track per-chunk Shannon entropy on outgoing POST bodies.
- *Network:* replication of identical bytes across chunks of the same flow — a high signal of padding / templated decoys vs. encrypted content.
- *Host:* EDR observation of plaintext generation vs ciphertext fingerprinting — only the chunk-upload step should be high-entropy on the wire.
- *Telemetry surfaces:* Network IDS / DPI that records body entropy per flow; Zeek `files.log` analysis.

**False-positive profile.** Real encrypted backups, file-sync traffic (Dropbox, OneDrive). Disambiguation is by destination: sanctioned vs unsanctioned.

---

### 3.7 Domain fronting / CDN-fronted relay

**What it is.** The `Host:` header the TLS server sees differs from the `SNI` presented in the TLS handshake. The client speaks TLS to a CDN (e.g. `cdn.example.com`) but the HTTP layer asks for a different origin (`api.your-target.com`). The CDN forwards to the second origin. Operator-driven resilience requires choosing a CDN that still supports this (most major ones have closed this off since 2022; smaller and tier-2 CDNs often haven't).

**Why it works against defenders.** Network defenders see a TLS SNI of a legitimate CDN, and proxy-layer logs see only CDN traffic. Only endpoint defenders (CDN-side) and TLS server-name-aware middleboxes have any view of the real origin.

**ATT&CK mapping.**

- `T1090.002` — Proxy: External Proxy.
- `T1090.003` — Proxy: Multi-hop Proxy (CDN → origin is two hops).
- `T1568` — Dynamic Resolution (CDN as a dynamic front).

**Detection side.**

- *Network:* TLS SNI vs HTTP `Host` mismatch. In environments where TLS is terminated at a middlebox (corporate egress proxy, cloud-NGFW with TLS-inspect), the SNI and `Host` are both visible. Mismatch is a high-signal indicator.
- *Network:* rare or never-seen origins behind common CDNs. Build allowlists per CDN and alert on deviation.
- *Endpoint:* server logs at the CDN's own visibility level detect this — but the defender in this situation is often the customer, not the CDN.
- *Telemetry surfaces:* TLS-inspecting egress, `http.log` with both `Host` and SNI fields, custom middlebox logs.

**False-positive profile.** Multi-tenant SaaS applications legitimately front and serve multiple origins. The disambiguator is the destination's reputation and any observed mismatches in the same flow's earlier connections.

---

### 3.8 User-Agent and header rotation / obfuscation

**What it is.** Beyond a single static `User-Agent`, the operator-driven technique is to rotate UAs across chunks (a small bank of plausible browser strings), randomise header case, and use multiple custom header names. Naïve loop uses one fixed UA.

**Why it works against defenders.** A static masquerade UA in a flow is a low-cost search needle; against basic blocklists, it works. Against behavioural analytics, it's still a giveaway: *all* traffic from a host to one destination sharing one UA, vs *all* traffic from a browser fleet to the same destination exhibiting UA diversity.

**ATT&CK mapping.**

- `T1036.005` — Masquerading: Match Legitimate Name or Location (UA match).
- `T1071.001` — Application Layer Protocol: Web Protocols.

**Detection side.**

- *Network:* per (host, destination) tuple, the *UA diversity* on egress should match what other hosts in the org send to that destination. Hosts whose UA distribution deviates are anomalous.
- *Network:* header case entropy vs matched browser fingerprint. Chrome produces a deterministic UA order and `Accept-*` order; a sequence that mismatches is suspicious.
- *Network:* EDR inventory of the running process — outbound HTTP via `WinHTTP` or `curl` is spoofable; outbound HTTP via a real browser engine loads JS and asset requests. A flow with no companion static-asset / favicon / analytics requests is highly suspicious even with a valid UA.
- *Telemetry surfaces:* Zeek `http.log` UA field; corporate proxy access logs.

**False-positive profile.** Headless browsers and OS-Update agents can look similar. Inventory disambiguation is sufficient in most networks.

---

### 3.9 MIME-type masquerading and payload padding

**What it is.** Beyond `application/octet-stream`, the operator-driven technique is to declare a `Content-Type` matching a benign MIME type (`application/json`, `image/jpeg`, `multipart/form-data`) and to pad the body so the size class matches the declared type. A naïve loop declared octet-stream and let the body size be whatever the chunk yielded.

**Why it works against defenders.** DLP rules keyed on `Content-Type: application/octet-stream` to egress points are easy: declare `image/jpeg` and the rule fails. Payload-size-class checks (DLP module that flags "lots of small bodies from one host in a short window") are also defeated by padding to a fixed size per chunk.

**ATT&CK mapping.**

- `T1132.001` — Data Encoding: Standard Encoding (content-type claiming).
- `T1027` — Obfuscated Files or Information (pad-to-class).

**Detection side.**

- *Network:* declared `Content-Type` vs body entropy and structure. `image/jpeg` should fail a JPEG magic-byte check at body[:3]. `application/json` should parse. Failed checks against declared types are high-signal.
- *Network:* ANOMALY histograms of body size per declared Content-Type. The legitimate `application/json` distribution from a browser or API client is well-known; an anomalous distribution is observable.
- *Telemetry surfaces:* Suricata / DPI post-decompression analysis, custom egress proxies that re-validate MIME types.

**False-positive profile.** DLP evasion is the dominant legitimate use (privacy-conscious users), but typically on outbound webmail / web forms, not background processes.

---

### 3.10 In-memory / process-isolated secret storage

**What it is.** Beyond reading the key from `os.environ`, the operator-driven technique is to receive the key over a network channel (DNS, an HTTP header, a query parameter) just before use, decrypt in memory, and never persist it. Naïve loops log or read keys from disk.

**Why it works against defenders.** Disk-resident keys are findable by EDR / DFIR filesystem enumeration, by `/proc/<pid>/cmdline` scraping of older arg-list patterns, by shell history (older `export C2_KEY=…`), and by `~/.bash_history` cleanup gaps.

**ATT&CK mapping.**

- `T1573.001` / `T1573.002` — Encrypted Channel (key delivery).
- `T1027` — Obfuscated Files or Information (no disk-resident fingerprint).

**Detection side.**

- *Host:* look for crypto library gaps without a corresponding key on disk. EDR observes the process loading `libcrypto.so` / `bcrypt.dll` / `Fernet` (Python) but no pre-existing key file. EDD also observes network reads of small unique payloads immediately preceding crypto use.
- *Host:* the absence of any `*.key` / `*.secret` / `*.pem` write on a process that is doing crypto is a positive indicator of in-memory key handling.
- *Network:* the *prior* network call delivering the key is itself a target: small POST/GET immediately before a large POST burst from the same destination.

**False-positive profile.** Any legitimate application with TPM-backed secrets, browser processes reading keys from `keychain`/`secret-tool`/Windows DPAPI, etc. Disambiguation: the in-memory key pattern is more alarming when combined with the rest of an exfil pattern.

---

### 3.11 DNS-tunnel fallback channel

**What it is.** When HTTPS egress fails (blocked, alerted on), the operator-driven technique is to fall back to DNS-tunnelled exfil — embedding chunk bytes into the labels of TXT or NULL-record queries to a DNS server the operator controls. Naïve C2 has no fallback and fails closed.

**Why it works against defenders.** DNS is rarely deep-inspected; even TLS-inspecting middleboxes don't terminate DNS. Long subdomain labels (e.g., `AVGHEXF……。example.com`) are the signal, but tunnel-detection is its own engineering problem.

**ATT&CK mapping.**

- `T1071.004` — Application Layer Protocol: DNS.
- `T1572` — Protocol Tunneling.
- `T1008` — Fallback Channels.
- `T1568` — Dynamic Resolution.
- `T1132.002` — Data Encoding: Non-Standard Encoding (the DNS label encoding).

**Detection side.**

- *DNS logs:* subdomain label length distribution. Authoritative DNS sees long random labels. Measure mean/95th-percentile length per (resolver, domain) pair.
- *DNS logs:* query rate asymmetry between internal recursors and external authoritative — high volume of unique subdomains to one domain is a strong signal.
- *Network:* payload entropy of label content. Tunnel queries carry ciphertext; benign label entropy is much lower.
- *Host:* EDR observation of `dnscat2`, `iodine`, or bespoke DNS-querying processes; outbound UDP/53 from a process that doesn't normally do DNS.
- *Telemetry surfaces:* passive DNS (RPZ feeds), Splunk/DNSDB-history, internal resolver query logs, Zeek `dns.log`.

**False-positive profile.** CDN hostname shorteners, anti-spam tracking domains, malware-research networks. Allowlist known low-risk high-entropy domains; alert on the rest.

---

### 3.12 TLS client hello masquerade (JA3 / JA4 conformance)

**What it is.** Make the TLS ClientHello indistinguishable from a real browser. The operator-driven technique is to use a TLS library that emits the same cipher list, extensions, ALPN, and EC point formats as Chrome or Firefox. Naïve clients use Go `crypto/tls` defaults or Python `ssl` defaults which produce distinctive (now-rare) JA3s.

**Why it works against defenders.** TLS-fingerprinting middleboxes and EDR NTA modules (Cloudflare-spectrum-style, JA3-based detectors) maintain a list of legitimate browser fingerprints; non-matching fingerprints from a process whose name doesn't match (curl, custom binary) is an immediate signal.

**ATT&CK mapping.**

- `T1573.001` / `T1573.002` — Encrypted Channel.
- `T1036.005` — Masquerading.

**Detection side.**

- *Network:* JA3 / JA4 fingerprint per egress flow vs the inventory of processes allowed to emit that fingerprint. Browsers are allowed; `python`, `golang-net`, `curl`, `wget` are unusual.
- *Network:* cipher/extension conformance. Real browsers don't negotiate `TLS_RSA_*` ciphers; any flow that does is detectable.
- *Telemetry surfaces:* Zeek `ssl.log`, Suricata `tls` records, commercial NTA modules that record JA3/JA4.

**False-positive profile.** A Python tool that legitimately needs to talk to an internal API server usually uses the default fingerprint. There it's *expected*, not C2. Treat the JA3 fingerprint as one signal among many.

---

### 3.13 Chained / multi-hop exfil

**What it is.** Beyond a single hop to a CDN-fronted receiver, an operator-driven resilience technique is **multi-hop**: target's exfil client → first front (compromise / CDN) → second front (mailbox / paste service / cloud-bucket) → operator's authoritative receiver. Naïve loops have a single hop.

**Why it works against defenders.** Each hop is anonymous from the perspective of an egress middlebox. The host sees traffic to "Google Drive / Dropbox / Telegram / OneDrive"; only inside those services does the malicious use become visible. SSRF sunburst patterns (vendor compromise) are a special case.

**ATT&CK mapping.**

- `T1567.001` — Exfiltration Over Web Service: Exfiltration to Cloud Storage.
- `T1567.002` — Exfiltration Over Web Service: Exfiltration to Code Repository.
- `T1090.003` — Proxy: Multi-hop Proxy.
- `T1568` — Dynamic Resolution.

**Detection side.**

- *Network:* SaaS app usage from processes / hosts that don't normally use that SaaS. Office productivity apps talk to OneDrive; an unrelated process doing so is a strong indicator.
- *CASB:* cloud-access security broker logs see the upload; correlate CASB destination info with the originating process.
- *Host:* EDR observation of API calls to SaaS endpoints from processes whose names aren't sanctioned for SaaS use (custom binaries, interpreter-launched scripts).
- *Telemetry surfaces:* CASB, egress logs, EDR net-conn events, browser-history export (where present).

**False-positive profile.** Heavy SaaS-use orgs have many legitimate uploads. Reduction: identify which processes have authorisation to write to which SaaS, alert on the others.

---

## 4. Detection-engineering cross-cutting

The detection rules in §5 use the following telemetry surfaces. This section explains what to instrument and how to combine signals.

### 4.1 Network-layer telemetry

| Surface | What you see | Where to put it |
|---|---|---|
| **NetFlow / IPFIX** | Per-flow byte and packet counts, duration, src/dst tuples | Edge routers, internal core |
| **Zeek `conn.log`** | Per-connection metadata, application protocol detection | SPAN port at egress |
| **Zeek `http.log`** | UA, headers (incl. custom `X-*`), declared MIME, response code | SPAN port |
| **Zeek `ssl.log`** | JA3, JA3S, certificate subject, SNI | SPAN port |
| **Zeek `dns.log`** | Query name, type, response | SPAN port |
| **Zeek `files.log`** | File seen over the wire (incl. entropy and entropy histogram) | SPAN port |
| **Suricata EVE** | All of the above plus alerts | SPAN port |
| **PCAP** | Full payload capture (high storage; sample at egress) | Forensic store, not realtime |

### 4.2 TLS fingerprinting

JA3 (MD5 over extensions/ciphers) and JA4 (more flexible, includes ALPN/extension order) are practical in any TLS-aware middlebox. Maintain a list of fingerprints expected per process-class in your org:

- Chrome (latest and recent)
- Firefox (latest and recent)
- Edge
- Office / Teams
- Known internal apps
- Sanctioned APIs (Python `requests`, Go, `curl`, etc.)

Anything outside the list, *especially* from a process whose declared name is one of the above, is a signal.

### 4.3 Host / EDR telemetry

| Signal | What it tells you |
|---|---|
| Process creation (Sysmon / EdrProcessCreate) | What binary is running |
| Image loads (`bcrypt.dll`, `Fernet`, `libcrypto`) | Whether encryption libs are loaded |
| File events (`*.key`, `*.secret`, `*.pem`) | Whether secrets are persisted |
| DNS events from non-DNS-processes | DNS-tunnel candidate |
| Net conns from non-browser processes | Bypass candidate |
| Syscall `nanosleep`/`select` cadence | Cadence pattern |

### 4.4 Proxy / DNS / firewall logs

| Surface | What you see |
|---|---|
| Egress proxy access log | All HTTP egress with full headers (incl. SNI if TLS-Inspect) |
| Internal recursive DNS log | All queries from workstations |
| Forward-proxy CONNECT log | TLS-only metadata (SNI, cert subject, byte count) |
| Firewall flow log | Per-flow metadata |

### 4.5 UEBA / behavioural analytics

User-Entity Behavioural Analytics on top of the above surfaces combines:

- Recent activity window per user
- Process inventory per user
- Network-egress baseline per host
- Time-of-day baseline per (user, host)

Surfacing "this user's previously-unknown process is sending egress to a never-before-seen domain on a Saturday night" is where the high-value findings live.

---

## 5. Example detection rules (pseudo)

Each rule below is written in a Sigma-style / Suricata-style pseudo-grammar so a SOC can adapt it to their stack. **Validity range / tuning notes** follow each rule so they don't fire noisy.

### Rule 5.A — Cadence (RITA-style) anomaly per host-to-destination pair

> **Suricata / custom analysis on Zeek `conn.log`:**
>
> ```
> FOR (src_ip, dst_ip, dst_port) WINDOW 1h:
>    count_distinct(inter_arrival_seconds) >= 30 unique values
>    AND count(reqs) >= 50
>    AND stdev(inter_arrival_seconds) > mean(inter_arrival_seconds) / 2
>    AND destination NOT IN sanctioned_endpoint_allowlist
> ```

- **Validity:** heavy-tailed inter-arrival distribution is decorrelated-jitter. Web browsers produce narrow distributions (focused burst) or wide-with-low-mean (idle+active). Confirm hash and process class before escalating.
- **False positives:** mobile / IoT clients with bad networks. Tag by `device_class`.

### Rule 5.B — Connection-to-request ratio outlier

> **Sigma (targeting Zeek + endpoint context):**
>
> ```yaml
> title: Suspicious 1:1 Request-to-Connection Ratio
> logsource: zeek
> detection:
>   selection_http:
>     proto: http
>     method: POST
>   filter_browsers:
>     ua|startswith: ["Mozilla/5.0", "AppleWebKit", "Edg/", "Chrome"]
>   filter_saas_uploads:
>     host|endswith: sanctioned_saas_upload_domains
>   condition: selection_http AND NOT (filter_browsers OR filter_saas_uploads)
>   timeframe: 1h
> ```

- **Validity:** legitimate browsers and SaaS uploads suffer the same one-request-per-connection pattern; they are explicitly excluded. Anything left is a candidate.
- **False positives:** Python services calling internal APIs. Add `process_name IN sanctioned_python_apps` whitelist.

### Rule 5.C — TLS SNI / HTTP Host mismatch (domain fronting)

> **Suricata rule:**
>
> ```
> alert http $HOME_NET any -> $EXTERNAL_NET any (
>   msg:"Possible domain fronting - SNI/Host mismatch";
>   tls.sni; content:"<cdn>"; http.host; content:"!"; sid:1000002; rev:1;
> )
> ```

- **To make it selective:** parametrise the CDN allowlist; fire only when `tls.sni` resolves to a CDN your org uses and `http.host` resolves to a domain known to be a target / not a customer of that CDN.
- **False positives:** multi-tenant SaaS products legitimately fronting multiple origins behind a CDN.

### Rule 5.D — Resume-from-N+1 header pattern

> **Suricata / custom:**
>
> ```
> IF on connection_drop THEN next_request.X-Chunk-Seq != 0
>   AND count_of_consecutive_zero_starts_in_flow == 0
> THEN tag as checkpointed-upload.
> ```
>
> In practice: track `X-Chunk-Seq` per `X-Chunk-ID` in flow state. If any retry resumes from a non-zero value, mark the flow.

- **Validity:** legitimate resumable uploads (S3 multipart, `tus.io`, YouTube resumable) all use the same pattern. Restrict by destination allowlist.
- **False positives:** none if the destination allowlist is correct.

### Rule 5.E — Body entropy higher than declared MIME type should hold

> **Custom (Zeek `files.log` analysis):**
>
> ```
> IF http.content_type matches /^image\/|^audio\/|^video\//
>   AND files.log.entropy > 7.9 (bits/byte)
> THEN flag for manual review.
> ```

- **Validity:** real JPEG/MP3 video files have entropy closer to 7.5–7.99 but with detectable magic bytes. Pure ciphertext hits 7.999. Magic-byte check is the strongest signal.
- **False positives:** some legitimate encrypted file formats (ZFS send, gpg-cmd output).

### Rule 5.F — JA3 fingerprint mismatch with process name

> **Sigma (targeting EDR + Zeek):**
>
> ```yaml
> title: TLS ClientHello fingerprint inconsistent with process
> logsource: edr + zeek
> detection:
>   selection_chrome_ja3:
>     zeek.ssl.ja3: chrome_known_ja3
>   selection_non_chrome_proc:
>     edr.process_name: ["python*", "curl", "wget", "go-*", "node*"]
>   condition: selection_chrome_ja3 AND selection_non_chrome_proc
> ```

- **Validity:** legitimate Python scripts using library PinnedCerts may still legitimately use a Chrome JA3 if they embed the same TLS stack — but typically they don't. Restrict to internal apps by hash.
- **False positives:** some legitimate tools proxy through curl with custom cipher lists.

### Rule 5.G — DNS-tunnel signal via label length

> **Suricata:**
>
> ```
> alert dns $HOME_NET any -> any 53 (
>   msg:"DNS query with unusually long subdomain label";
>   dns.query; pcre:"/^[A-Za-z0-9+\/=]{40,}\\./";
>   sid:1000010; rev:1;
> )
> ```

- **Validity:** legitimate DKIM, Base64-encoded nameserver records, ACME challenges get close but rarely cross 40 chars of pure alphanumeric in a single label.
- **False positives:** TXT-record ACME-`dns-01`-style challenges. Exclude `acme-validation` or similar.

### Rule 5.H — Process-isolated key indicator

> **Sigma (EDR-side):**
>
> ```yaml
> title: Crypto library loaded but no key file created / read
> detection:
>   select_crypto_load:
>     edr.event: image_load
>     module: ["cryptography", "bcrypt", "Fernet", "libcrypto.so*", "bcrypt.dll"]
>   filter_known_apps:
>     edr.process_name: known_crypto_apps_hash_list
>   select_no_key_file:
>     edr.event: file_event
>     NOT edr.process_name: known_crypto_apps_hash_list
>     AND EXISTS(process: loaded crypto lib)
>     AND NOT EXISTS(process: file_event action:read|create file:*.key|*.pem|*.secret)
>   condition: select_crypto_load AND select_no_key_file
> ```

- **Validity:** in-memory-only key holders are a single indicator. Pair with rule 5.K (process inventory drift) before escalating.
- **False positives:** browser / OS service code that legitimately uses DPAPI / Keychain without a key file on disk is enormous. Restrict to non-system processes.

### Rule 5.I — Cover-traffic / decoy inflated cardinality

> **Custom (Zeek `http.log` analysis):**
>
> ```
> GROUP BY (src_ip, dst_ip, dst_port, hour):
>   PER chunk: bytes_sent = chunk_size
>   total_bytes = N_chunks * chunk_size
>   unique_byte_content = count(distinct SHA1(first_64_bytes_of_body))
>   IF unique_byte_content > 0.3 * N_chunks AND total_bytes > 5MB
>     THEN flag.
> ```

- **Validity:** encrypted chunks should each have unique bytes; legitimate traffic has lower repetition. The 30%-distinct heuristic detects decoy padding (which by definition is repeated).
- **False positives:** legitimate byte streams with natural block-repetition. Restrict to flows tagged as exfil-candidate by another rule.

### Rule 5.J — Multi-hop egress to SaaS from non-SaaS-process

> **Sigma (EDR + Egress log):**
>
> ```yaml
> title: SaaS upload from non-SaaS-authorised process
> detection:
>   selection_saas_dest:
>     egress.dst_domain: ["*.dropbox.com", "*.drive.google.com",
>                          "*.onedrive.com", "api.telegram.org",
>                          "*.github.com", "*.pastebin.com"]
>   selection_non_saas_proc:
>     edr.process_name NOT IN sanctioned_saas_clients
>   condition: selection_saas_dest AND selection_non_saas_proc
> ```

- **Validity:** CASB-saw log cross-correlation. Restrict further by upload direction (`POST /upload`, `PUT /file`) rather than any TCP/443.
- **False positives:** CLI tools (`rclone`, `aws-cli`) legitimately write to SaaS. Allowed when the user is an admin/devops.

### Rule 5.K — Process inventory drift (known-baseline)

> **Sigma (EDR process-create):**
>
> ```yaml
> title: New process observed not in organisation baseline
> detection:
>   selection:
>     edr.event: process_create
>     edr.process_hash NOT IN known_process_hashes
>     edr.first_seen: <24h
>   condition: selection
> ```

- **Validity:** every organisation should baseline running processes. Drift is a general signal, not specific to exfil — but on its own constitutes a reason to look closer.
- **False positives:** new software deploys. Mute during known change windows.

---

## 6. Defensive priorities / quick wins

In a SOC with limited engineering effort, prioritise in this order:

1. **Egress proxy with TLS inspection.** Without TLS inspection you can't see SNI, certificate subject, JA3, or HTTP headers. This is the single highest-leverage investment.
2. **TLS-aware Zeek + JA3 inventory.** Spin up Zeek at egress; collect `conn.log`, `http.log`, `ssl.log`, `dns.log`. Build JA3 inventory per process class.
3. **Egress allowlist.** A strict deny-by-default egress policy with an explicit allowlist of destinations kills the majority of naive exfil. Treat every external destination as suspect by default.
4. **EDR with process-tree + image-load + file-event telemetry.** The host-side counterpart. Without it, you cannot make the host-side correlations in §4.
5. **CASB or SaaS-egress log.** Without this, multi-hop exfil is invisible from your network.
6. **DMARC `p=reject` + reporting**. Already covered in §8.7 of the OSINT audit — it's the email counterpart to egress allowlist.
7. **UEBA / behavioural analytics** layered on top of the above. Provides the "rule-of-n" outliers the static rules miss.

The first four items there are the 80%-solution. The rest buys margin.

---

## 7. Out of scope and remaining gaps

Items deliberately not covered:

- **Lateral movement** to source the data in the first place (separate technique domain).
- **Initial access / execution** — the loop presupposes data is already on disk.
- **Encryption of the data at rest** in the receiver — server-side is operator territory.
- **Operational tradecraft** (drop times, safe countries, OPSEC of the operator personally).
- **Specific tool names being newly-developed or improved** — this document describes techniques; not work to be done on any specific implementation.

Detection **gaps** explicitly acknowledged:

- **[low-yield detection]** A high-quality TLS fingerprint that exactly matches a real browser, sent from a real browser instance the attacker hijacked (e.g. via malicious extension), is hard to detect without endpoint-browser-isolation visibility.
- **[low-yield detection]** In-memory-only operations with no telemetry-evading syscall gaps — most EDRs have blind spots here.
- **[low-yield detection]** Operations that ride *only* over heavily-used legitimate destinations with perfect JA3 conformance from a process whose hash is on the allowlist — defenders must rely on *behavioural* signals alone.

These should be prioritised in research, not in production detection, until behavioural telemetry matures.

---

## 8. Sources & references

- MITRE ATT&CK Enterprise matrix, v15+ — `attack.mitre.org`.
- Zeek project documentation — `docs.zeek.org`.
- Suricata rule documentation — `suricata.readthedocs.io`.
- Sigma generic signature format — `github.com/SigmaHQ/sigma`.
- RITA (Real Intelligence Threat Analytics) — for inter-arrival-time analysis.
- JA3 / JA4 specification — `github.com/FoxIO-LLC/ja4` and original SalesForce JA3 work.
- AWS Architecture Blog — "Exponential Backoff And Jitter" (decorrelated jitter origin).
- Cloudflare/Salesforce research on domain fronting (incl. deprecation announcements 2022).

---

> **Prepared as a defensive research note. No offensive tooling is included, no patches to scripts in this repository are proposed, and no code that any operator could directly plug into an existing tool is provided.**
