# C2 Exfil Response Runbook (SOC Player)

> **Companion to `GHOST-HUNT-C2-EXFIL-RESILIENCE-THREAT-INTEL.md` §3 (catalogue) and §5 (rules). One-page-format runbook for SOC analysts handling a high-confidence alert from rules 5.A — 5.K.**
>
> **(One)** What to do in the first ten minutes. **(Two)** What evidence to grab before the host reboots. **(Three)** When and how to hand off to IR.
>
> **Posture:** analyst-side ONLY. Don't act unilaterally on host state. Containment decisions go through IR. Block-at-egress is the only unilateral exception.

---

## 0. Quick-route triage — rule → first action

| Rule (TI §5) | Indicator of | First action (analyst) | Time budget |
|---|---|---|---|
| **5.A cadence anomaly** | decorrelated jitter | correlate on same (host, dest) — expect 5.B / 5.K corroboration | ≤ 5 min |
| **5.B ratio outlier** | one-shot-socket-per-chunk | EDR/PID lookup → binary path → hash | ≤ 5 min |
| **5.C SNI/Host mismatch** | domain fronting | capture both fields; pick `dest` from SNI; verify against fronting-blocklist | ≤ 5 min |
| **5.D resume-from-N+1** | checkpointed upload | confirm `dest` not in SaaS-multipart allowlist; pull flow | ≤ 5 min |
| **5.E body-entropy / MIME** | padding / CT evasion | PCAP 1 KB; magic-byte test | ≤ 5 min |
| **5.F JA3 mismatch** | custom TLS stack | EDR PID → on-disk hash → threat-intel hash lookup | ≤ 5 min |
| **5.G DNS tunnel label length** | DNS-tunnel fallback | resolver query pull; tally unique subdomains; isolate workstation | ≤ 10 min |
| **5.H in-memory key** | process-isolated secret | process tree dump + image-load list; ASSUME SEV-2 even with single hit | ≤ 10 min |
| **5.I decoy cardinality** | cover traffic | capture flow bytes; entropy per chunk; pair with 5.A / 5.B | ≤ 10 min |
| **5.J multi-hop SaaS** | SaaS upload from non-SaaS proc | CASB / EDR PID correlation; identify process, plan block | ≤ 5 min |
| **5.K inventory drift** | unknown binary recently seen | asset / crown-jewel correlation; scope of pkgs/CI deploy | ≤ 10 min |

> **Universal first step regardless of rule:** open the SOC ticket, freeze the host's clock-skew artefacts (do not reboot), paged-claim the alert to avoid double-handling.

---

## 1. Severity tiers

| Tier | Conditions |
|---|---|
| **SEV-1** | ≥ 2 rules corroborating on the same (host, dest) within 24 h **or** 5.J with non-sanctioned SaaS **or** 5.C with confirmed fronting target **or** rule fires on a crown-jewel / executive host |
| **SEV-2** | Single high-confidence rule on a production / exec host, no corroboration yet — but process is unknown to inventory |
| **SEV-3** | Single rule on a workstation only; no crown-jewel data on disk per asset inventory |
| **SEV-4** | Disputed / FP candidate after first triage; needs rule tuning |

---

## 2. Decision tree

```
                       HIGH-CONFIDENCE ALERT (5.A–5.K)
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
       ANY rule fires on      ≥ 2 rules correlate    Known-sanctioned
       crown-jewel / exec?    on same (host, dest)?  proc + allowlisted
              │                      │                   destination?
              ▼                      ▼                      ▼
            SEV-1                  SEV-1                 (close as FP;
              │                      │                   tune rule)
              │                      │
              ▼                      ▼
       ──── IMMEDIATE ESCALATION (§4) ────
                          │
                  ┌───────┴───────┐
              SEV-2 / SEV-3   Single rule only
              EDR hash lookup      │
              or unknown process   ▼
                  │            §3 triage checklist
                  │            ──────► SEV-2 minimum
                  ▼
              capture volatile evidence
              (§3, in order)
                  │
            ┌─────┴─────┐
       confirmed       disputed
       malicious         │
            │            ▼
            ▼         SEV-4: tune
       SEV-1 — escalation
```

> **Decision rule of thumb:** if any rule pair fires on the same `(host, egress_destination)` tuple, the destination is "operator infrastructure" for that host. Treat accordingly.

---

## 3. Triage checklist — volatile evidence first

> **Critical:** preserve order. Reboot, sleep, or shutdown destroys volatile state. The operator may be watching — don't communicate with the suspect process (no pings, no DNS lookups, no recompile, no `kill -0`).

1. **Process tree dump** — EDR live response *or* `ps -ef` / `tasklist /v` / `Get-Process`. Hash every node; capture parent chain.
2. **Open sockets & handles for suspect PID** — `lsof -p <pid>`, `netstat -anob` / Sysmon Event 3. Note egress destinations and listening sockets.
3. **Loaded modules** — image-load list. Flag crypto libs (`bcrypt`, `Fernet`, `libcrypto.so*`, `libsodium*`, `CryptoAPI`).
4. **Egress flow snapshot** — last 60 minutes. Zeek `conn.log` window keyed on `(host, sus_dest_ip, sus_dest_port)`. Capture total bytes, duration, JA3/SNI, X-* headers.
5. **PCAP slice** — egress sensor port; same window. **1 KB max** for magic-byte check; never replay traffic.
6. **DNS cache** — `ipconfig /displaydns` / `scutil --dns` / `resolvectl statistics`. Dump before any host reboot.
7. **Execution-history artefacts** — Prefetch, Amcache, Shimcache, recent file history. Establishes timeline.
8. **On-disk remnants** — file hashes for source-file candidates, MFT entries for recently-modified user files. Done **only** if SEV-1 confirmed.
9. **Process memory dump** — only on SEV-1; only with IR approval.
10. **Full disk image** — last; only on IR ownership handover.

> **Time budget:** volatile items 1–6 in 10 minutes. Items 7–10 only with IR sign-off.

---

## 4. Escalation triggers — auto-call IR

Escalate immediately if **any** of:

- ≥ 2 rules from TI §5 fire on the same `(host, dest)` within 24 h.
- 5.J with a non-sanctioned SaaS destination.
- 5.C with a confirmed fronting target.
- 5.F where the on-disk hash returns a known catalogued malware hash.
- 5.G with confirmed DNS-tunnel authoritative server.
- Any alert on a host tagged `crown-jewel` or `executive`.
- Customer or regulatory notification clauses triggered (data class on host, breach clock, jurisdictional threshold).
- The analyst cannot rule out malicious intent within 15 minutes.

When escalating, complete §6 first. Escalation ownership transfers to IR; analyst remains on the call until IR confirms.

---

## 5. Containment posture (analyst-side only)

### ✅ Do

- Preserve evidence (per §3).
- Block egress to confirmed-bad destination at the egress proxy on SEV-1. (This is the only unilateral analyst action.)
- Tag the suspect binary hash in the EDR as `quarantine-blocked` to prevent further execution while you decide.
- Page the SOC manager and IR duty officer for SEV-1.
- Open a clean communication channel (out-of-band) for IR handoff — assume operational channel is monitored.

### ❌ Don't

- Don't reboot / shut down / sleep the host.
- Don't kill the suspect process until memory capture is complete (SEV-1) or until IR takes ownership.
- Don't `ping`, `dig`, `curl`, or otherwise probe the suspect destination — the operator's response can confirm and tip them off.
- Don't change passwords or rotate keys on the suspect host until IR has decided on scoping.
- Don't run "AV scans" or "clean-up" tools that may overwrite volatile artefacts.
- Don't communicate findings to the user-base or to peers outside the SOC / IR channel before IR has set the external-comms posture.

---

## 6. IR handoff template (YAML — paste into the ticket)

```yaml
ticket_id: <SIEM-INC-…>
handoff_at_utc: 2026-…
analyst: <name, @username, extension>
on_call_ir: <name, @username, extension>
alert_source: <5.A | 5.B | 5.C | 5.D | 5.E | 5.F | 5.G | 5.H | 5.I | 5.J | 5.K; cite TI §5 verbatim>
correlated_rules_present: <list of other rules from §5 firing on same (host,dest) in 24h>
severity: <SEV-1 | SEV-2 | SEV-3>
crown_jewel: <yes | no; if yes, list dataset class names e.g. PCI, PII, IP, M&A, M&A]
host:
  hostname: 
  ip: 
  asset_class: <workstation | server | exec | dev | k8s-node | …>
  os_user: <user account on host, NOT the principal under investigation>
  last_reboot: <from uptime field>
process:
  pid: 
  path: 
  sha256: 
  parent_process:
    name: 
    sha256: 
  command_line: 
  loaded_modules: <flag crypto libs>
network:
  destination_ip: 
  destination_domain: 
  sni: 
  ja3_client: 
  ja3s_server: 
  x_chunk_id: <if present>
  x_chunk_seq: <if present>
  user_agent: 
  bytes_sent: 
  bytes_received: 
  first_seen_utc: 
  last_seen_utc: 
  flow_uids: <Zeek conn.uid list>
  pcap_path: <file share path for the captured slice>
evidence_collected:
  volatile:
    - process_tree: <path>
    - sockets_handles: <path>
    - image_loads: <path>
    - dns_cache: <path>
  network:
    - zeek_window_extract: <path>
    - pcap_slice: <path>
    - casb_corroboration: <path or "n/a">
  on_disk:
    - file_hashes: <list sha256 of source candidates>
    - prefetch_amcache: <path>
    - mft_or_shimcache: <path>
containment_actions_taken:
  - <egress block to dest at proxy at time_utc, by analyst>
  - <EDR quarantine hash>
false_positive_candidates:
  - <list with reason each>
analyst_hypothesis: <one paragraph>
next_actions_requested_from_ir:
  - <item>
  - <item>
comms_posture:
  customer_notify: <yes | no | pending>
  dpo_paged: <yes | no | pending>
  threat_intel_share: <yes | no | pending>
```

---

## 7. "Done" looks like

- IR owns the ticket and is driving response.
- Host isolated at network level by IR (block-by-IP + block-by-domain + block-by-JA3-JA4).
- Source process binary hash shared into threat-intel pipeline (TI ingestion accepted).
- Egress to destination blocked *before* the operator's next alert app showed up.
- Crown-jewel data on host triaged: was any exfiltrated, and if so, what — by class.
- Customer / DPO notification path activated if data exfil is confirmed.
- Post-incident review scheduled; detection rule tuned; runbook updated with any new tactic observed.
- Pipeline-verify ✓ — the runbook is in the analyst's hands at the start of the shift, not scrambling after the page.

---

## 8. Posture reminders (single-line, tape this to the wall)

- **Volatile first. Disk last.**
- **Don't tip off the operator.**
- **One analyst owns the box end-to-end until IR confirms.**
- **Don't probe the destination. The reply tells them you're watching.**
- **Two rules on the same (host, dest) is SEV-1, not "let me keep digging."**
- **Don't reboot the host.**
- **Egress-block is the only unilateral move you get.**
- **Handoff complete = ticket closed at SOC; reopen only on IR request.**

---

> **Prepared as a defensive analyst-side runbook. No offensive tooling, no rule patches, no operator tradecraft is included. Patch the rules in `GHOST-HUNT-C2-EXFIL-RESILIENCE-THREAT-INTEL.md` §5 over time based on incident learnings, and revise severity triggers in §1 / §4 here to match your environment's actual crown-jewel inventory.**
