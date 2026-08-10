# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  GHOST-HUNT // DNS C2 KIT — Makefile                                       ║
# ║  Run from: GHOST-HUNT-C2-KIT-DNS/                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

.PHONY: help test test-roundtrip test-keep test-cover test-chunk-loss lint typecheck clean

PYTHON ?= python
PY     ?= $(PYTHON)

GREEN := \033[0;32m
NC    := \033[0m

help: ## Show this help
	@echo ""
	@echo "DNS C2 Kit Targets"
	@echo "=================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'
	@echo ""

test: test-roundtrip test-chunk-loss ## Run all tests
	@echo "$(GREEN)[PASS] DNS C2 kit tests passed$(NC)"

test-roundtrip: ## Round-trip smoke test (2 KB file, ~82 chunks)
	$(PY) test/local_dns_harness.py

test-keep: ## Round-trip with --keep (retain artifacts)
	$(PY) test/local_dns_harness.py --keep

test-cover: ## Cover verification self-test
	$(PY) test/local_dns_harness.py --self-test-cover

test-chunk-loss: ## Chunk-loss simulation (5 scenarios: none/middle/first/last/many)
	$(PY) test/test_chunk_loss.py

lint: ## Lint Python files
	$(PY) -m ruff check *.py test/ --config ../pyproject.toml

typecheck: ## Type-check Python files
	$(PY) -m pyright *.py --pythonversion 3.6

clean: ## Remove caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
