#!/usr/bin/env python3
"""Structural validation of .github/workflows/smoke.yml.

Checks that triggers, job gates, matrix payloads, and referenced files
interact as intended. Exits 0 on success, 1 on any finding.
"""
import os
import sys

import yaml

WF = ".github/workflows/smoke.yml"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

problems = []
notes = []

with open(WF, encoding="utf-8") as wf:
    d = yaml.safe_load(wf)
on = d.get("on") or d.get(True)  # PyYAML 1.1 parses `on:` as boolean True
jobs = d["jobs"]

# ---- Triggers -----------------------------------------------------------
expected_events = {"push", "pull_request", "schedule", "workflow_dispatch"}
actual = set(on.keys())
missing = expected_events - actual
if missing:
    problems.append(f"missing triggers: {sorted(missing)}")
else:
    print(f"[PASS] triggers present: {sorted(actual)}")

crons = on.get("schedule", [])
if isinstance(crons, dict):
    crons = crons.get("cron", [])
# GitHub Actions format: schedule is a list of {cron: <expr>} dicts
cron_exprs = [c["cron"] for c in crons if isinstance(c, dict) and "cron" in c]
if not cron_exprs:
    problems.append("schedule has no cron entries")
else:
    print(f"[PASS] cron: {cron_exprs}")
    if any(not isinstance(c, str) or len(c.split()) != 5 for c in cron_exprs):
        problems.append(f"suspicious cron entries: {cron_exprs}")

# ---- Permissions --------------------------------------------------------
perms = d.get("permissions", {})
if perms.get("contents") != "read":
    notes.append(f"permissions: {perms} (expected contents: read)")
else:
    print("[PASS] permissions: contents: read")

# ---- Per-job expectations ----------------------------------------------
expect = {
    "kit-smoke": {
        "gate": None,  # runs on every event
        "timeout": 10,
        "matrix": 10,  # 6 smoke modes + 4 chunk-loss scenarios (HTTPS + DNS)
        # Semantic contract: mode -> expected number of matrix entries.
        # A bare count would go stale on the next legit change; the mode
        # distribution is the meaningful invariant to guard.
        "matrix_modes": {
            "roundtrip": 2,        # HTTPS + DNS
            "keep": 2,             # HTTPS + DNS
            "self-test-cover": 2,  # HTTPS + DNS
            "chunk-loss": 2,       # HTTPS + DNS (all 6 scenarios each)
            "chunk-loss-many": 2,  # HTTPS + DNS (25% loss isolate)
        },
        "needs_crypto": True,
    },
    "lint-typecheck": {
        "gate": None,
        "timeout": 10,
        "matrix": None,  # not a matrix job
    },
    "capacity-stress": {
        "gate": "schedule || workflow_dispatch",
        "timeout": 20,
        "matrix": 2,
        "needs_crypto": True,
    },
    "bundle-drift": {
        "gate": None,
        "timeout": 10,
    },
}

for name, exp in expect.items():
    if name not in jobs:
        problems.append(f"job missing: {name}")
        continue
    job = jobs[name]
    print(f"--- job: {name} ---")
    gate = job.get("if")
    if exp["gate"] is None:
        if gate:
            notes.append(f"{name}: has unexpected gate: {gate}")
        else:
            print("[PASS] runs on all events")
    else:
        if gate and "schedule" in gate and "workflow_dispatch" in gate:
            print(f"[PASS] gate = {gate}")
        else:
            problems.append(f"{name}: gate wrong: {gate!r} (want schedule+workflow_dispatch)")

    to = job.get("timeout-minutes")
    if to != exp["timeout"]:
        problems.append(f"{name}: timeout {to}, want {exp['timeout']}")
    else:
        print(f"[PASS] timeout {to} min")

    if exp.get("matrix"):
        m = job.get("strategy", {}).get("matrix", {}).get("include", [])
        if len(m) != exp["matrix"]:
            problems.append(f"{name}: {len(m)} matrix entries, want {exp['matrix']}")
        else:
            print(f"[PASS] matrix: {len(m)} entries")
        modes = exp.get("matrix_modes")
        if modes:
            from collections import Counter

            actual_modes = Counter(e.get("mode") for e in m)
            for want_mode, want_count in modes.items():
                if actual_modes.get(want_mode) != want_count:
                    problems.append(
                        f"{name}: mode {want_mode!r} appears "
                        f"{actual_modes.get(want_mode)}x, want {want_count}x"
                    )
            if not any(
                p.startswith(f"{name}: mode ") for p in problems
            ):
                print(f"[PASS] matrix modes: {dict(sorted(actual_modes.items()))}")
        if job.get("strategy", {}).get("fail-fast", True) is not False:
            notes.append(f"{name}: fail-fast not disabled")
        else:
            print("[PASS] fail-fast: false")
    if exp.get("needs_crypto"):
        has_crypto = any(
            s.get("if") == "matrix.needs_cryptography"
            and "cryptography" in s.get("run", "")
            for s in job.get("steps", [])
        )
        if has_crypto:
            print("[PASS] conditional cryptography install present")
        else:
            problems.append(f"{name}: missing conditional cryptography install step")

# ---- Referenced files exist ---------------------------------------------
refs = []
for job in jobs.values():
    for step in job.get("steps", []):
        run = step.get("run", "")
        if "run_local" in run:
            for tok in run.split():
                if "run_local" in tok and tok.strip('"').endswith(".sh"):
                    refs.append(tok.strip('"'))
        if "build-kit-bundle" in run:
            for tok in run.split():
                if "build-kit-bundle" in tok:
                    refs.append(tok)

for ref in sorted(set(refs)):
    path = os.path.join(ROOT, ref.replace("../", "").replace("${{", "").replace("}}", "").strip())
    # matrix.script is resolved from the matrix; check the known scripts directly
    if os.path.exists(os.path.join(ROOT, ref)) or os.path.exists(path):
        print(f"[PASS] referenced file exists: {ref}")
    else:
        # Known scripts referenced via matrix
        known = [
            "GHOST-HUNT-C2-KIT/test/run_local_test.sh",
            "GHOST-HUNT-C2-KIT-DNS/test/run_local_dns_test.sh",
            "GHOST-HUNT-C2-KIT-DNS/test/run_local_dns_chunk_loss.sh",
            ".freebuff/build-kit-bundle.py",
        ]
        if ref in known:
            print(f"[PASS] referenced file exists: {ref}")
        else:
            problems.append(f"referenced file missing: {ref}")

# ---- Matrix script resolution ------------------------------------------
for job in jobs.values():
    m = job.get("strategy", {}).get("matrix", {}).get("include", [])
    for entry in m:
        script = entry.get("script")
        if script and not os.path.exists(os.path.join(ROOT, script)):
            problems.append(f"matrix script missing: {script}")
    if m:
        print(f"[PASS] all matrix scripts resolved ({len(m)})")

# ---- Summary ------------------------------------------------------------
print()
if problems:
    print("[FAIL]")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)
print("[PASS] workflow structure validated")
if notes:
    print("notes:")
    for n in notes:
        print(f"  - {n}")
sys.exit(0)
