#!/bin/bash

# Setup script for OpsBrain Slack Bot git hooks
# Installs pre-push hook for automatic test validation

echo "🔧 Setting up git hooks for OpsBrain Slack Bot..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if we're in a git repository
if [[ ! -d ".git" ]]; then
    echo "❌ Error: Not in a git repository"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Check if hooks directory exists
if [[ ! -d ".git/hooks" ]]; then
    echo "📁 Creating .git/hooks directory..."
    mkdir -p .git/hooks
fi

# Install pre-push hook
HOOK_FILE=".git/hooks/pre-push"

if [[ -f "$HOOK_FILE" ]]; then
    echo "⚠️  Pre-push hook already exists"
    echo "   Creating backup: $HOOK_FILE.backup"
    cp "$HOOK_FILE" "$HOOK_FILE.backup"
fi

cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash

# Pre-push hook for OpsBrain Slack Bot
# Ensures all tests pass before allowing push to remote repository

echo "🧪 Running pre-push test validation..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Set TEST_MODE to ensure proper test environment
export TEST_MODE=true

# Check if we're in a virtual environment or can activate one
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
elif [[ -d "venv" ]]; then
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
    if [[ $? -ne 0 ]]; then
        echo "❌ Failed to activate virtual environment"
        exit 1
    fi
else
    echo "⚠️  No virtual environment found - proceeding with system Python"
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing test dependencies..."
    pip install pytest pytest-timeout httpx
    if [[ $? -ne 0 ]]; then
        echo "❌ Failed to install test dependencies"
        exit 1
    fi
fi

# Run the full test suite
echo "🚀 Running full test suite (49 tests)..."
echo ""

# Run pytest with verbose output and proper test discovery
python -m pytest -v --tb=short

# Capture the exit code
TEST_EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    echo "✅ ALL TESTS PASSED! Push allowed."
    echo "🚀 Proceeding with push to remote repository..."
    exit 0
else
    echo "❌ TESTS FAILED! Push blocked."
    echo ""
    echo "📋 Next steps:"
    echo "  1. Fix the failing tests"
    echo "  2. Run tests locally: python -m pytest -v"
    echo "  3. Commit your fixes"
    echo "  4. Try pushing again"
    echo ""
    echo "🛡️  This hook prevents broken code from being pushed."
    exit 1
fi
EOF

# Make the hook executable
chmod +x "$HOOK_FILE"

echo "✅ Pre-push hook installed successfully!"
echo ""
echo "📋 What this does:"
echo "   • Automatically runs all 49 tests before every git push"
echo "   • Blocks pushes if any tests fail"
echo "   • Ensures only working code reaches the repository"
echo ""
echo "🧪 Test the hook:"
echo "   make pre-push    # Run the same validation manually"
echo "   git push         # Will automatically run tests"
echo ""
echo "🚀 Ready! Your pushes are now protected by automatic test validation."
