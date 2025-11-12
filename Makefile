# Makefile for Unity MCP Server
# Provides convenient commands for development tasks

.PHONY: help install install-dev test test-cov lint format type-check clean run download reset docs

help:  ## Show this help message
	@echo "Unity MCP Server - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync

install-dev:  ## Install with dev dependencies
	uv sync --extra dev

test:  ## Run tests
	uv run pytest -v

test-cov:  ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=html --cov-report=term

test-watch:  ## Run tests in watch mode (requires pytest-watch)
	uv run ptw -- -v

lint:  ## Run ruff linter
	uv run ruff check src tests

format:  ## Format code with black
	uv run black src tests main.py

format-check:  ## Check formatting without changing files
	uv run black --check src tests main.py

type-check:  ## Run mypy type checking
	uv run mypy src

quality:  ## Run all quality checks (format, lint, type-check)
	@echo "Running black..."
	@uv run black src tests main.py
	@echo "\nRunning ruff..."
	@uv run ruff check src tests
	@echo "\nRunning mypy..."
	@uv run mypy src
	@echo "\n✅ All quality checks passed!"

clean:  ## Clean temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage build/ dist/

run:  ## Run the MCP server
	uv run python main.py

download:  ## Download and index Unity documentation
	uv run python main.py --download

download-test:  ## Download and index limited docs for testing (100 pages)
	uv run python main.py --download --max-pages 100

reset:  ## Reset everything and re-download documentation
	uv run python main.py --reset

server-debug:  ## Run server with debug logging
	LOG_LEVEL=DEBUG uv run python main.py

docs:  ## Generate documentation (if using sphinx or similar)
	@echo "Documentation is in README.md and related .md files"
	@echo "See: README.md, QUICK_REFERENCE.md, PRODUCTIVITY_TOOLS.md"

build:  ## Build package distribution
	uv build

publish-test:  ## Publish to Test PyPI
	uv publish --repository testpypi

publish:  ## Publish to PyPI
	uv publish

version:  ## Show current version
	@grep version pyproject.toml | head -1 | cut -d'"' -f2

deps-update:  ## Update dependencies
	uv lock --upgrade

deps-show:  ## Show dependency tree
	uv pip list

.DEFAULT_GOAL := help
