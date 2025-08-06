#!/bin/bash

# Comprehensive test runner script
# Run this manually to test everything before pushing to production

echo "🧪 OpsBrain Test Suite Runner"
echo "============================="
echo ""

# Set test environment variables
export TEST_MODE=true
export SLACK_BOT_TOKEN=fake_slack_token
export NOTION_API_KEY=fake_notion_key
export NOTION_DB_ID=fake_db_id
export OPENAI_API_KEY=fake_openai_key

# Track overall success
OVERALL_SUCCESS=true

# Function to run a test and track success
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo "🔍 Running $test_name..."
    echo "----------------------------------------"
    
    eval $test_command
    if [ $? -eq 0 ]; then
        echo "✅ $test_name PASSED"
    else
        echo "❌ $test_name FAILED"
        OVERALL_SUCCESS=false
    fi
    echo ""
}

# Run performance tests
run_test "Performance Tests" "python test_performance.py"

# Run timeout protection tests
run_test "Timeout Protection Tests" "python test_timeout_protection.py"

# Run full test suite with coverage
run_test "Full Test Suite" "pytest -v --tb=short"

# Check if business goals load correctly
run_test "Business Goals Loading" "TEST_MODE=true python -c \"from main import business_goals; print(f'✅ Loaded {len(business_goals)} business goals successfully')\""

# Summary
echo "🏁 TEST SUMMARY"
echo "==============="
if [ "$OVERALL_SUCCESS" = true ]; then
    echo "🎉 ALL TESTS PASSED! Ready for deployment."
    echo ""
    echo "Next steps:"
    echo "1. git add ."
    echo "2. git commit -m 'Your commit message'"
    echo "3. git push"
    exit 0
else
    echo "💥 SOME TESTS FAILED! Fix issues before deploying."
    echo ""
    echo "Review the failed tests above and fix the issues."
    exit 1
fi
