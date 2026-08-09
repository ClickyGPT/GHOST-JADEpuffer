# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  GHOST-HUNT // x0rTr0n — C2 Kit Makefile                                  ║
# ║  Common targets: test, lint, typecheck, install, clean                     ║
# ║  Usage:  make help  (lists all targets)                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

.PHONY: help test test-https test-dns lint typecheck install install-dev clean fmt check

# ── Default Python ────────────────────────────────────────────────────────────
PYTHON ?= python
PY     ?= $(PYTHON)

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m

# ============================================================================
# HELP
# ============================================================================

help: ## Show this help
	@echo ""
	@echo "GHOST-HUNT // C2 Kit Makefile"
	@echo "============================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make test              # Run all smoke tests"
	@echo "  make test-https        # Run HTTPS kit smoke test only"
	@echo "  make lint              # Lint all Python files"
	@echo "  make typecheck         # Type-check C2 kit code"
	@echo "  make check             # Run lint + typecheck + test"
	@echo ""

# ============================================================================
# INSTALL
# ============================================================================

install: ## Install runtime dependencies
	@echo "$(GREEN)[*] Installing runtime dependencies...$(NC)"
	$(PY) -m pip install -q cryptography

install-dev: install ## Install dev dependencies (ruff, pyright, pytest)
	@echo "$(GREEN)[*] Installing dev dependencies...$(NC)"
	$(PY) -m pip install -q ruff pyright pytest

# ============================================================================
# TEST
# ============================================================================

test: test-https test-dns ## Run all C2 kit smoke tests
	@echo "$(GREEN)[PASS] All smoke tests passed$(NC)"

test-https: ## Run HTTPS C2 kit round-trip smoke test
	@echo "$(GREEN)[*] Running HTTPS C2 kit smoke test...$(NC)"
	$(PY) GHOST-HUNT-C2-KIT/test/local_harness.py

test-dns: ## Run DNS C2 kit round-trip smoke test
	@echo "$(GREEN)[*] Running DNS C2 kit smoke test...$(NC)"
	$(PY) GHOST-HUNT-C2-KIT-DNS/test/local_dns_harness.py

test-cover: ## Run cover verification self-tests (both kits)
	@echo "$(GREEN)[*] Running HTTPS cover self-test...$(NC)"
	$(PY) GHOST-HUNT-C2-KIT/test/local_harness.py --self-test-cover
	@echo "$(GREEN)[*] Running DNS cover self-test...$(NC)"
	$(PY) GHOST-HUNT-C2-KIT-DNS/test/local_dns_harness.py --self-test-cover
	@echo "$(GREEN)[PASS] Cover self-tests passed$(NC)"

# ============================================================================
# LINT
# ============================================================================

lint: ## Lint all Python files with ruff
	@echo "$(GREEN)[*] Linting with ruff...$(NC)"
	$(PY) -m ruff check GHOST-HUNT-C2-KIT/ GHOST-HUNT-C2-KIT-DNS/ --config pyproject.toml

lint-fix: ## Auto-fix lint issues
	@echo "$(GREEN)[*] Auto-fixing lint issues...$(NC)"
	$(PY) -m ruff check --fix GHOST-HUNT-C2-KIT/ GHOST-HUNT-C2-KIT-DNS/ --config pyproject.toml

fmt: ## Format all Python files with ruff
	@echo "$(GREEN)[*] Formatting with ruff...$(NC)"
	$(PY) -m ruff format GHOST-HUNT-C2-KIT/ GHOST-HUNT-C2-KIT-DNS/ --config pyproject.toml

# ============================================================================
# TYPECHECK
# ============================================================================

typecheck: ## Type-check C2 kit code with pyright
	@echo "$(GREEN)[*] Type-checking with pyright...$(NC)"
	$(PY) -m pyright --project pyproject.toml

# ============================================================================
# CHECK (CI pipeline)
# ============================================================================

check: lint typecheck test ## Run full CI pipeline: lint + typecheck + test
	@echo ""
	@echo "$(GREEN)╔══════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║  ALL CHECKS PASSED                  ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════╝$(NC)"

# ============================================================================
# CLEAN
# ============================================================================

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)[*] Cleaning...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)[+] Clean$(NC)"
