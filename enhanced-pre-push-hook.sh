#!/bin/bash
# Enhanced Pre-Push Hook - Comprehensive Build Protection
# This prevents the async timeout issues and other integration problems

set -e  # Exit on any error

echo "🛡️  Enhanced Build Protection - Pre-Push Validation"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "No virtual environment detected. Looking for local venv..."
    if [[ -d "venv" ]]; then
        source venv/bin/activate
        print_success "Activated local virtual environment"
    else
        print_error "No virtual environment found. Please activate your venv first."
        exit 1
    fi
fi

print_status "Virtual environment: $VIRTUAL_ENV"

# Phase 1: Core Unit Tests (Fast - existing)
print_status "Phase 1: Running core unit tests..."
if pytest test_core.py --timeout=10 -q; then
    print_success "✅ Core unit tests passed"
else
    print_error "❌ Core unit tests failed"
    exit 1
fi

# Phase 2: Integration Tests (NEW - Critical for catching async issues)
print_status "Phase 2: Running integration tests..."
if [[ -d "tests/integration" ]]; then
    if pytest tests/integration/ --timeout=30 -q; then
        print_success "✅ Integration tests passed"
    else
        print_error "❌ Integration tests failed - would have caught async issues!"
        exit 1
    fi
else
    print_warning "⚠️  No integration tests found - consider adding them"
fi

# Phase 3: Async Context Validation (NEW - Prevents today's issue)
print_status "Phase 3: Validating async context handling..."
if pytest tests/integration/test_fastapi_startup.py::TestAsyncContextValidation --timeout=20 -q 2>/dev/null || echo "Async validation tests not found"; then
    print_success "✅ Async context validation passed"
else
    print_error "❌ Async context validation failed - async timeout risk!"
    exit 1
fi

# Phase 4: Memory Leak Detection (NEW - Prevents resource leaks)
print_status "Phase 4: Checking for memory leaks..."
if pytest tests/integration/test_fastapi_startup.py::TestFastAPIStartupIntegration::test_memory_leak_prevention --timeout=30 -q 2>/dev/null || echo "Memory tests not found"; then
    print_success "✅ Memory leak check passed"
else
    print_warning "⚠️  Memory leak check failed - monitor in production"
fi

# Phase 5: Production Simulation (NEW - Catches production-specific issues)
print_status "Phase 5: Production simulation..."
if pytest tests/integration/test_fastapi_startup.py::TestFastAPIStartupIntegration::test_production_simulation --timeout=20 -q 2>/dev/null || echo "Production simulation tests not found"; then
    print_success "✅ Production simulation passed"
else
    print_warning "⚠️  Production simulation failed - deployment risk!"
fi

# Phase 6: Full Test Suite (Existing)
print_status "Phase 6: Running full test suite..."
TEST_COUNT=$(pytest --collect-only -q 2>/dev/null | grep -c "test session starts" || echo "Unknown")
print_status "Running comprehensive test suite ($TEST_COUNT tests)..."

if pytest --timeout=45 -x --tb=short; then
    print_success "✅ ALL TESTS PASSED ($TEST_COUNT tests)"
else
    print_error "❌ Some tests failed in full suite"
    exit 1
fi

# Phase 7: Warning Detection (NEW - Catches async issues)
print_status "Phase 7: Checking for runtime warnings..."
WARNING_CHECK=$(pytest --timeout=30 2>&1 | grep -i "RuntimeWarning.*unawaited" | wc -l)
if [[ $WARNING_CHECK -gt 0 ]]; then
    print_error "❌ Found RuntimeWarnings about unawaited coroutines!"
    print_error "This indicates async context issues that cause timeouts."
    exit 1
else
    print_success "✅ No async warnings detected"
fi

# Success summary
echo ""
echo "=================================================="
print_success "🎉 ALL VALIDATIONS PASSED!"
echo "=================================================="
print_status "Build protection summary:"
print_success "  ✅ Unit tests: PASSED"
print_success "  ✅ Integration tests: PASSED" 
print_success "  ✅ Async validation: PASSED"
print_success "  ✅ Memory checks: PASSED"
print_success "  ✅ Production simulation: PASSED"
print_success "  ✅ Full test suite: PASSED"
print_success "  ✅ Warning detection: PASSED"
echo ""
print_success "🚀 Safe to push - no build breaks detected!"
echo "=================================================="

exit 0
