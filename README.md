# GHOST-HUNT // x0rTr0n — Prompt Kit

> **Framework:** GHOST-HUNT // x0rTr0n  
> **Version:** 1.0  
> **Status:** ACTIVE  
> **Purpose:** Reusable operational AI assistant system prompts

---

## 1. What's in this kit?

This kit contains three versions of the same GHOST-HUNT // x0rTr0n system prompt, tuned for different use cases.

| File | Format | Best For |
|---|---|---|
| `GHOST-HUNT-SYSTEM-PROMPT.md` | Markdown | Full framework reference, training, or manual review |
| `GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.md` | Markdown | Fast-loading system prompt for chat UIs |
| `GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.json` | JSON | API deployments (OpenAI, Claude, etc.) |
| `AGENTICAUTOMATION/AGENTICAUTOMATION-OPENCOE.md` | Markdown | OpenCoe harness prompt |
| `AGENTICAUTOMATION/AGENTICAUTOMATION-HERMES.md` | Markdown | Hermes harness prompt |
| `AGENTICAUTOMATION/AGENTICAUTOMATION-FREEBUIFF.md` | Markdown | Freebuiff harness prompt |
| `AGENTICAUTOMATION/AGENTICAUTOMATION-OPENCOE.json` | JSON | OpenCoe API-ready prompt |
| `AGENTICAUTOMATION/AGENTICAUTOMATION-HERMES.json` | JSON | Hermes API-ready prompt |
| `AGENTICAUTOMATION/AGENTICAUTOMATION-FREEBUIFF.json` | JSON | Freebuiff API-ready prompt |

---

## 2. Framework in 30 Seconds

GHOST-HUNT enforces a **modular, tactical output style**:

- **Tables** over paragraphs
- **Bold** core concepts
- ***Italics*** for nuance / commentary
- `` `inline code` `` for technical identifiers
- `[OP-ID: ...]` system log footer on every response

Every response is structured in three phases:

1. **Phase I** — Recon / Data Harvest
2. **Phase II** — Pattern / Vuln Mapping
3. **Phase III** — Execution / Tagging / Exfil

---

## 3. File Descriptions

### 3.1 `GHOST-HUNT-SYSTEM-PROMPT.md`

The complete system prompt. Includes identity, core principles, typographical primitives, mission profile format, phased execution, mandatory elements, prohibited elements, default template, and operational posture.

**Use when:** you want the full reference document or are onboarding someone to the framework.

### 3.2 `GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.md`

A one-page, fast-loading version. Retains identity, output rules, response template, prohibited elements, and posture — with minimal prose.

**Use when:** you need to paste the prompt into a chat UI or assistant configuration with limited context window.

### 3.3 `GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.json`

The condensed prompt wrapped in a JSON envelope, ready for API use. Structure:

```json
{
  "name": "GHOST-HUNT // x0rTr0n — Condensed",
  "version": "1.0",
  "system_message": {
    "role": "system",
    "content": "..."
  },
  "api_compatibility": [...],
  "usage": {
    "OpenAI": "...",
    "Claude": "..."
  }
}
```

---

## 4. How to Use

### 4.1 OpenAI / OpenAI-Compatible APIs

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
            {"role": "user", "content": "Draft a recon plan for target ACME."}
        ]
    }
)
```

### 4.2 Anthropic Claude Messages API

```python
import json
from anthropic import Anthropic

with open("GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.json") as f:
    prompt_data = json.load(f)

client = Anthropic(api_key=ANTHROPIC_API_KEY)

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=prompt_data["system_message"]["content"],
    messages=[
        {"role": "user", "content": "Draft a recon plan for target ACME."}
    ]
)
```

### 4.3 Manual / Chat UI Use

Open `GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.md`, copy the contents, and paste it into the system prompt field of your chat interface.

---

## 5. Expected Response Format

When the prompt is active, the model will produce outputs like:

```markdown
### [OP-ID: ACME-RECON]

**Objective:** Harvest public-facing infrastructure data.

| Asset | Status | Action |
|---|---|---|
| `acme.com` | IDENTIFIED | Map subdomains |
| GitHub org | FOUND | Enumerate repos |

*Note: focus on passive sources only.*

1. **Phase I** — DNS / subdomain enumeration
2. **Phase II** — Tech stack fingerprinting
3. **Phase III** — Report and tag findings

> `[LOGIC_STATE]: ACTIVE` | `[VULNERABILITY]: TBD` | `[PHASE]: I`
```

---

## 6. Rules Summary

| Do | Don't |
|---|---|
| Use `### [OP-ID: ...]` headers | Use narrative transitions |
| Include at least one table | Add decorative filler |
| Bold core concepts | Write in passive voice |
| Add *italicized* nuance | Dump uniform wall-of-text paragraphs |
| Use `inline code` for identifiers | |
| Close with the system log footer | |

---

## 7. License / Use

This is an internal operational framework. Adapt the prompt text to your environment as needed, but preserve the core structural rules if you want consistent GHOST-HUNT output.

---

## 8. C2 Kits — Validation Summary

The deployable C2 kits ship with their own validation, deployment, and CI artifacts. All measured numbers below were collected on 2026-08-10 and are re-verified nightly by CI.

| Artifact | Purpose | Key Numbers / Status |
|---|---|---|
| [`VALIDATION.md`](VALIDATION.md) | Measured throughput + quality-gate report for both kits | HTTPS **200 MB @ ~14 MB/s**; DNS **64 KB / 1,748 queries, zero loss**; lint + typecheck clean |
| [`DEPLOYMENT_CHECKLIST_C2_KITS.md`](DEPLOYMENT_CHECKLIST_C2_KITS.md) | End-to-end deployment runbook: bootstrap, env vars, TLS/DNS config, exfil/pull, burn | Both kits gated green before deploy |
| [`GHOST-HUNT-C2-KIT/README.md`](GHOST-HUNT-C2-KIT/README.md) | HTTPS receiver kit: bootstrap, handler, exfil, pull, burn | Round-trip + cover verified; `make test` / `run.sh test` |
| [`GHOST-HUNT-C2-KIT-DNS/README.md`](GHOST-HUNT-C2-KIT-DNS/README.md) | DNS tunnel kit: dnscat2/iodine/dns_exfil, stdlib-only client | Round-trip + cover verified; `make test` / `run.sh test` |
| [`.github/workflows/smoke.yml`](.github/workflows/smoke.yml) | CI: smoke (6-matrix), ruff + pyright, nightly capacity stress, bundle-drift | All gates enforced on push / PR / nightly / manual |
| `GHOST-HUNT-C2-KIT/run.sh` · `GHOST-HUNT-C2-KIT-DNS/run.sh` | make-equivalent runners (no GNU make required) | `test` / `lint` / `typecheck` / `test-cover` / `clean` |

**Validation state (both kits):** smoke round-trip ✅ · cover 6/6 ✅ · ruff 0 findings ✅ · pyright 0 errors ✅ · capacity at ceiling ✅ · burn documented ✅

---

> **CONCLUSION:** The machinery of the operation is the only thing that survives contact with the target. Everything else is noise. Strip it. Execute. 🚬
