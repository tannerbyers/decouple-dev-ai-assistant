.PHONY: test test-unit test-integration test-all help

# Default target
help:
	@echo "Available commands:"
	@echo "  test           - Run unit tests only (fast)"
	@echo "  test-unit      - Same as test, run unit tests only"
	@echo "  test-integration - Run integration tests only (slower)"
	@echo "  test-all       - Run all tests (unit + integration)"
	@echo "  clean          - Clean up test artifacts"

# Run unit tests only (excludes integration tests)
test:
	@echo "Running unit tests..."
	TEST_MODE=true python -m pytest tests/ -v --ignore=tests/integration/

test-unit: test

# Run integration tests only  
test-integration:
	@echo "Running integration tests..."
	TEST_MODE=true python -m pytest tests/integration/ -v

# Run all tests
test-all:
	@echo "Running all tests..."
	TEST_MODE=true python -m pytest tests/ -v

# Clean up test artifacts
clean:
	@echo "Cleaning up test artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
