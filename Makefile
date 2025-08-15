.PHONY: test test-unit test-integration test-all test-fast pre-push help clean

# Default target
help:
	@echo "Available commands:"
	@echo "  test           - Run all tests (same as pre-push validation)"
	@echo "  test-fast      - Run core tests only (fastest)"
	@echo "  test-all       - Run all tests with coverage"
	@echo "  pre-push       - Validate before push (same as git hook)"
	@echo "  clean          - Clean up test artifacts"

# Main test command - runs all current tests (49 total)
test:
	@echo "🧪 Running all tests (49 tests)..."
	TEST_MODE=true python -m pytest -v --tb=short

# Fast test subset for quick validation
test-fast:
	@echo "⚡ Running fast core tests..."
	TEST_MODE=true python -m pytest test_core.py test_task_extraction.py -v

# All tests with coverage report
test-all:
	@echo "📊 Running all tests with coverage..."
	TEST_MODE=true python -m pytest -v --tb=short --cov=main --cov-report=term-missing

# Pre-push validation (same as git hook)
pre-push:
	@echo "🚀 Pre-push validation (same as git hook)..."
	TEST_MODE=true python -m pytest -v --tb=short
	@echo "✅ Ready to push!"

# Legacy aliases for backward compatibility
test-unit: test-fast
test-integration: test

# Clean up test artifacts
clean:
	@echo "🧹 Cleaning up test artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"
