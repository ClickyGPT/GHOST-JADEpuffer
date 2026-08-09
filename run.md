# Run doc — JADEPUFFER GHOST-HUNT explainer preview

Serves `.freebuff/explain-jadepuffer-ghost-hunt.html` plus its sidecar
`kit-bundle.json` (in-page document viewer content) from a tiny static server,
so the viewer's fetch path is exercised live instead of the embedded fallback.

## Reproduce the artifacts

1. The explainer page is `explain-jadepuffer-ghost-hunt.html` (self-contained:
   inline CSS/JS, embedded bundle fallback in `<script id="kit-bundle-data">`).
2. The sidecar `kit-bundle.json` and the embedded fallback are BOTH generated
   from the repo documents by the idempotent build script:
   ```bash
   python .freebuff/build-kit-bundle.py
   ```
   Re-run it after editing any mapped document — it refreshes the sidecar and
   re-injects the embedded copy, and is safe to run repeatedly. A CI drift
   check exists too:
   ```bash
   python .freebuff/build-kit-bundle.py --check   # exit 1 if artifacts are stale
   ```
   (`--check` rebuilds in memory and diffs against the committed artifacts,
   ignoring the `generated` date; it never writes.) The viewer
   auto-refreshes: while the drawer is open it re-fetches kit-bundle.json on
   tab focus/visibility and a 30s poll, re-rendering an open doc when its
   content changes — no page reload needed (run the build first).
3. No env files, credentials, or dependency installs are needed (stdlib only).

## Run the server

Serve the `.freebuff` directory (the page and `kit-bundle.json` must share a
root so the relative `fetch('kit-bundle.json')` resolves):

```bash
cd .freebuff
python -m http.server 61998 --bind 127.0.0.1   # detached: nohup ... > preview-*.log 2>&1 &
```

- Default port: **61998** (loopback only). If busy, pick any free port and
  re-register the preview with the new URL.
- Verify: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:61998/kit-bundle.json` → `200`.
- Logs: `.freebuff/preview-ef9e0e29-6ddc-42bf-ae8d-df9fd3b2695b.log`.
- Stop: kill the PID shown by `netstat -ano | grep :61998`.
