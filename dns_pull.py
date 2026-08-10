#!/usr/bin/env python3
"""Reassemble + decrypt DNS-exfiltrated chunks (GHOST-HUNT playbook 12.2).

Consumes the capture format written by dns_handler.py (local listener): files
named chunk_<fileid>_<seq>.txt, each containing one base32-encoded, unpadded
chunk. One output file per <fileid> is written (<fileid>.bin). Legacy
single-file captures named chunk_<seq>.txt (no fileid) are still supported
and decode to recovered.bin.

Detects gaps and warns — missing chunks mean corrupt data.

In production (dnscat2), reconstruct from the server's session log or a
tcpdump capture by extracting the QNAME chunk + fileid labels per query into
chunk_<fileid>_<seq>.txt files, then run this.

Usage:
    python3 dns_pull.py --dir <capture-dir> --password <secret> [--out recovered]
    python3 dns_pull.py --dir <capture-dir> --password <secret> --strict
    DNS_PASSWORD=<secret> python3 dns_pull.py --dir dns_incoming

Exit codes: 0 = clean (or non-strict with data warnings — partial data kept
for triage); 1 = operational error (no capture, malformed input); 2 = --strict
and either the seq-gap or integrity warning fired.
"""

import argparse
import base64
import binascii
import glob
import hashlib
import os
import sys


def xor_decrypt(data: bytes, key: bytes) -> bytes:
    """XOR decrypt data with a repeating key."""
    return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])


def main() -> int:
    ap = argparse.ArgumentParser(description="Reassemble & decrypt DNS exfil chunks")
    ap.add_argument("--dir", required=True, help="directory containing chunk_<seq>.txt files")
    ap.add_argument(
        "--password",
        default=os.environ.get("DNS_PASSWORD"),
        help="shared secret (default: $DNS_PASSWORD)",
    )
    ap.add_argument("--out", default="recovered", help="output directory (default: recovered)")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit 2 if any chunk-gap or integrity warning was raised "
        "(for automated pipelines; default still exits 0 so partial "
        "data is available for triage)",
    )
    args = ap.parse_args()

    if not args.password:
        ap.error("set --password or the DNS_PASSWORD environment variable")
    if not os.path.isdir(args.dir):
        ap.error(f"capture directory not found: {args.dir}")

    key = hashlib.sha256(args.password.encode()).digest()

    # Group capture files by file id (filename: chunk_<id>_<seq>.txt),
    # preserving sequence order. Legacy chunk_<seq>.txt files (no id) are
    # grouped under the fixed id 'recovered'.
    by_id = {}
    for f in glob.glob(os.path.join(args.dir, "chunk_*.txt")):
        base = os.path.basename(f)
        rest = base[len("chunk_") : -len(".txt")]  # '<id>_<seq>' or '<seq>'
        stem, _, seqpart = rest.rpartition("_")
        try:
            seq = int(seqpart)
        except ValueError:
            print(f"[!] skipping malformed capture file: {base}")
            continue
        # Normalize to lowercase: the fileid label is lowercase hex, but a
        # production reconstruction tool may uppercase DNS labels (DNS is
        # case-insensitive). Lowercasing keeps grouping correct AND keeps the
        # integrity check (below) from silently disabling itself on a capture
        # whose labels were uppercased.
        cid = (stem or "recovered").lower()  # legacy single-file capture
        by_id.setdefault(cid, {})[seq] = f

    if not by_id:
        print(f"[!] no chunk_*.txt files found in {args.dir}")
        return 1

    os.makedirs(args.out, exist_ok=True)
    total = 0
    data_warning = False  # raised by --strict for automated pipelines
    for cid in sorted(by_id):
        chunks = by_id[cid]
        seqs = sorted(chunks)
        # The scan is O(max_seq) — guard against a stray chunk with an
        # implausibly large seq (label cap keeps them tiny in practice) from
        # allocating a giant list; the content-hash integrity check still
        # validates the recovered bytes either way.
        if seqs[-1] < 1_000_000:
            missing = [s for s in range(0, seqs[-1] + 1) if s not in chunks]
        else:
            missing = []
            print(f"[!] {cid}: max chunk seq {seqs[-1]} implausible for "
                  f"{len(seqs)} chunk(s) — gap scan skipped (the content-hash "
                  "integrity check still validates the recovered bytes)")
        # range starts at 0 — a lost first chunk (seq 0) would otherwise decode
        # to silently corrupt bytes with no warning
        if missing:
            data_warning = True
            print(f"[!] {cid}: WARNING missing chunks {missing} — recovered data will be corrupt")

        b32_parts: list[str] = []
        for s in seqs:
            with open(chunks[s]) as cf:
                b32_parts.append(cf.read().strip())
        b32 = "".join(b32_parts)
        padding = "=" * (-len(b32) % 8)
        try:
            encrypted = base64.b32decode((b32 + padding).encode("ascii"))
        except (binascii.Error, ValueError) as exc:
            print(f"[!] {cid}: capture data is not valid base32 — corrupted capture? ({exc})")
            continue
        plain = xor_decrypt(encrypted, key)

        # Integrity check. The capture filename's <fileid> is the first 16 hex
        # chars of sha256(source) (written by dns_exfil.py). A lost chunk —
        # including the FINAL one, which the seq-gap scan above cannot see — or
        # a wrong password changes the recovered bytes, so the prefix stops
        # matching. Warn loudly instead of handing back silent garbage.
        if (len(cid) == 16 and all(c in "0123456789abcdef" for c in cid)
                and hashlib.sha256(plain).hexdigest()[:16] != cid):
            data_warning = True
            print(f"[!] {cid}: INTEGRITY FAILED — recovered bytes do not match "
                  f"the fileid content hash (chunk loss or wrong password)")

        out = os.path.join(args.out, f"{cid}.bin")
        with open(out, "wb") as f:
            f.write(plain)
        print(f"[+] {cid}: {len(plain)} bytes from {len(chunks)} chunks -> {out}")
        total += len(plain)

    print(f"[+] Reassembled {len(by_id)} file(s), {total} bytes total")
    # Exit 0 by default so partial data stays available for triage; --strict
    # gives automation a non-zero signal that the data is corrupt.
    if args.strict and data_warning:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
