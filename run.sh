#!/usr/bin/env bash
# ──── GHOST-HUNT // C2 KIT-DNS — make-equivalent runner ────
# Mirrors the Makefile targets so they run without GNU make
# (Git Bash / MSYS2 / any POSIX shell, incl. Windows).
# Usage:  ./run.sh [target]      (default: help)
#   e.g.  ./run.sh test          # round-trip smoke test
#         ./run.sh lint
#         ./run.sh typecheck
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PY="${PYTHON:-python}"

GREEN='\033[0;32m'
NC='\033[0m'

help() {
    echo ""
    echo "DNS C2 Kit Targets"
    echo "=================="
    echo "  help             Show this help"
    echo "  test             Round-trip smoke test (2 KB file, ~82 chunks)"
    echo "  test-roundtrip   Same as test"
    echo "  test-keep        Round-trip with --keep (retain artifacts)"
    echo "  test-cover       Cover verification self-test"
    echo "  test-chunk-loss  Chunk-loss simulation (5 scenarios: none/middle/first/last/many)"
    echo "  lint             Lint Python files (ruff)"
    echo "  typecheck        Type-check Python files (pyright)"
    echo "  clean            Remove __pycache__ / .pyc caches"
    echo ""
}

test_roundtrip() {
    "$PY" test/local_dns_harness.py
}

test_keep() {
    "$PY" test/local_dns_harness.py --keep
}

test_cover() {
    "$PY" test/local_dns_harness.py --self-test-cover
}

test_chunk_loss() {
    "$PY" test/test_chunk_loss.py
}

test_all() {
    test_roundtrip
    test_chunk_loss
    echo -e "${GREEN}[PASS] DNS C2 kit tests passed${NC}"
}

lint() {
    "$PY" -m ruff check *.py test/ --config ../pyproject.toml
}

typecheck() {
    "$PY" -m pyright *.py --pythonversion 3.6
}

clean() {
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
}

TARGET="${1:-help}"
case "$TARGET" in
    help)            help ;;
    test)            test_all ;;
    test-roundtrip)  test_roundtrip ;;
    test-keep)       test_keep ;;
    test-cover)      test_cover ;;
    test-chunk-loss) test_chunk_loss ;;
    lint)            lint ;;
    typecheck)       typecheck ;;
    clean)           clean ;;
    *)
        echo "[!] Unknown target: $TARGET (run ./run.sh help for targets)" >&2
        exit 1
        ;;
esac
