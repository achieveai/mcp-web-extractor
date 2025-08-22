# Trafilatura MCP Server - Development Makefile
# Use 'make help' to see available commands

.PHONY: help install install-dev test lint format type-check clean example run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install package for production"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting (ruff)"
	@echo "  format       - Format code (black, isort)"
	@echo "  type-check   - Run type checking (mypy)"
	@echo "  example      - Run example usage script"
	@echo "  run          - Run the MCP server"
	@echo "  clean        - Clean build artifacts"
	@echo "  all          - Run format, lint, type-check, and test"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/ -v

# Code quality
lint:
	ruff check src/ example_usage.py

format:
	black src/ example_usage.py
	isort src/ example_usage.py

type-check:
	mypy src/

# Run example
example:
	python example_usage.py

# Run server
run:
	python -m trafilatura_mcp.server

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run all quality checks
all: format lint type-check test
	@echo "✅ All checks passed!"

# Development setup
setup: install-dev
	@echo "✅ Development environment ready!"
	@echo "Run 'make example' to test the implementation"