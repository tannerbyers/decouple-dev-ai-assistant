#!/bin/bash

# Run E2E Tests for Agent-Notion Integration
# This script runs the comprehensive E2E test suite to verify agent system works correctly

set -e  # Exit on any error

echo "🧪 Running Agent-Notion E2E Test Suite"
echo "========================================"

# Set environment variables for testing
export TEST_MODE=true

# Check if pytest is available
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python 3"
    exit 1
fi

if ! python3 -m pytest --version &> /dev/null; then
    echo "❌ pytest not found. Please install pytest:"
    echo "   pip3 install pytest"
    exit 1
fi

# Run the E2E tests with verbose output
echo "🚀 Running E2E tests..."
python3 -m pytest tests/e2e/test_agent_notion_integration.py \
    -v \
    --tb=short

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All E2E tests passed!"
    echo "✅ Agent-Notion integration is working correctly"
    echo ""
    echo "Test Coverage:"
    echo "  • Agent task creation, updates, completion, deletion"
    echo "  • Error handling and resilience"  
    echo "  • Complete task lifecycle workflows"
    echo "  • Performance and reliability"
    echo "  • System integration"
    echo ""
else
    echo ""
    echo "❌ E2E tests failed!"
    echo "❌ Agent-Notion integration has issues that need to be fixed"
    echo ""
    echo "Next steps:"
    echo "  1. Review the test failures above"
    echo "  2. Fix any issues in the agent or Notion integration code"
    echo "  3. Run the tests again: ./scripts/run-e2e-tests.sh"
    echo ""
    exit 1
fi
