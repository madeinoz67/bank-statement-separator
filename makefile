# Makefile for Bank Statement Separator - Testing Focus

.PHONY: help install test test-unit test-integration test-edge test-performance test-coverage clean generate-test-data format lint check

help: ## Show this help message
	@echo "Bank Statement Separator - Available Commands:"
	@echo "=============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

test: ## Run all tests
	uv run python scripts/run_tests.py --type all --verbose

test-unit: ## Run unit tests only
	uv run python scripts/run_tests.py --type unit --verbose

test-integration: ## Run integration tests only
	uv run python scripts/run_tests.py --type integration --verbose

test-edge: ## Run edge case tests only
	uv run python scripts/run_tests.py --type edge_cases --verbose

test-performance: ## Run performance tests
	uv run pytest tests/integration/test_performance.py -v -m slow

test-fast: ## Run fast tests only (skip slow tests)
	uv run python scripts/run_tests.py --type fast --verbose

test-coverage: ## Run tests with coverage report
	uv run python scripts/run_tests.py --type all --coverage --verbose

test-api: ## Run tests that require OpenAI API key
	uv run python scripts/run_tests.py --type requires_api --verbose

generate-test-data: ## Generate test PDF statements
	uv run python scripts/generate_test_statements.py

test-with-data: ## Generate test data and run tests
	uv run python scripts/run_tests.py --generate --type all --verbose

format: ## Format code with ruff
	uv run ruff format .

lint: ## Lint code with ruff
	uv run ruff check . --fix

check: format lint ## Format and lint code

clean: ## Clean up test artifacts and generated files
	rm -rf test/input/generated/*.pdf
	rm -rf test/input/generated/*.json
	rm -rf test/output/*
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

demo: ## Run a demo with the Westpac test file
	uv run python -m src.workflow_bank_statement_separator.main "test/input/2015-05-21 Westpac BusinessChoice Rewards VISA Card Statement.pdf" --yes -o test/output --verbose

demo-dry: ## Run a dry-run demo
	uv run python -m src.workflow_bank_statement_separator.main "test/input/2015-05-21 Westpac BusinessChoice Rewards VISA Card Statement.pdf" --dry-run --yes --verbose

# Development targets
dev-install: ## Install with development dependencies
	uv sync --group dev

pre-commit: check test-fast ## Run pre-commit checks (format, lint, fast tests)

ci: install test-coverage ## Run CI pipeline (install, test with coverage)

# Test specific scenarios
test-validation: ## Test validation system specifically
	uv run pytest tests/unit/test_validation_system.py -v

test-edge-billing: ## Test billing account edge case
	uv run pytest tests/integration/test_edge_cases.py::TestSpecificEdgeCases::test_billing_account_detection -v

test-with-fallback: ## Test fallback processing (no API key)
	OPENAI_API_KEY="" uv run pytest tests/integration/test_edge_cases.py::TestEdgeCaseScenarios::test_fallback_processing_without_api_key -v

# Documentation and reporting
coverage-html: ## Generate HTML coverage report
	uv run pytest --cov=src/workflow_bank_statement_separator --cov-report=html tests/

coverage-xml: ## Generate XML coverage report
	uv run pytest --cov=src/workflow_bank_statement_separator --cov-report=xml tests/

# Debugging targets
debug-single: ## Debug single statement test
	uv run pytest tests/integration/test_edge_cases.py::TestEdgeCaseScenarios::test_single_statement_processing -v -s

debug-validation: ## Debug validation system
	uv run pytest tests/unit/test_validation_system.py::TestValidationSystem::test_validate_output_integrity_success -v -s

# Environment setup
setup-env: ## Setup environment file
	cp .env.example .env
	@echo "Please edit .env with your OPENAI_API_KEY"

# Clean and reset
reset: clean install ## Clean everything and reinstall

# Statistics
test-stats: ## Show test statistics
	@echo "Test Statistics:"
	@echo "==============="
	@echo "Unit tests:        $$(find tests/unit -name 'test_*.py' | wc -l | tr -d ' ')"
	@echo "Integration tests: $$(find tests/integration -name 'test_*.py' | wc -l | tr -d ' ')"
	@echo "Manual tests:      $$(find tests/manual -name 'test_*.py' | wc -l | tr -d ' ')"
	@echo "Total test files:  $$(find tests -name 'test_*.py' -not -path 'tests/manual/*' | wc -l | tr -d ' ')"
	@echo "Generated PDFs:    $$(find test/input/generated -name '*.pdf' 2>/dev/null | wc -l | tr -d ' ' || echo 0)"

# Documentation commands
.PHONY: docs-serve docs-build docs-deploy docs-clean

docs-serve: ## Serve documentation locally
	@echo "Starting documentation server..."
	uv run mkdocs serve

docs-build: ## Build documentation site
	@echo "Building documentation..."
	uv run mkdocs build --clean

docs-deploy: ## Deploy documentation to GitHub Pages
	@echo "Deploying documentation to GitHub Pages..."
	uv run mkdocs gh-deploy

docs-clean: ## Clean documentation build
	@echo "Cleaning documentation build..."
	rm -rf site/

.DEFAULT_GOAL := help
