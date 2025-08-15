# Test Automation Setup ✅

## Overview

Your OpsBrain Slack Bot now has **complete test automation** that ensures all 49 tests pass before any code is pushed to the repository. This prevents broken code from reaching production.

## What Was Set Up

### 1. Pre-Push Git Hook ✅
- **File**: `.git/hooks/pre-push`
- **Purpose**: Automatically runs all tests before every `git push`
- **Behavior**: Blocks push if any tests fail
- **Coverage**: All 49 tests across 4 test files

### 2. Updated Makefile ✅
- **Enhanced commands** for different test scenarios
- **Aligned with git hook** for consistency
- **Easy-to-use targets** for development workflow

### 3. Setup Script ✅
- **File**: `setup-git-hooks.sh`
- **Purpose**: Install git hooks on new environments
- **Usage**: `./setup-git-hooks.sh`

### 4. Updated Warp Configuration ✅
- **Documented automation** in `.warp` file
- **Clear workflow instructions**
- **Troubleshooting guidance**

## Available Commands

### Quick Test Validation
```bash
# Run all tests (same as pre-push hook)
make test

# Fast core test subset
make test-fast

# Pre-push validation check
make pre-push

# All tests with coverage report
make test-all
```

### Manual Test Execution
```bash
# All tests with verbose output
python -m pytest -v

# Specific test file
python -m pytest test_task_extraction.py -v

# Specific test function
python -m pytest test_core.py::TestHealthAndBasics::test_health_endpoint -v
```

## How It Works

### Normal Development Workflow
1. **Make changes** to your code
2. **Run tests** locally: `make test` or `python -m pytest -v`
3. **Fix any failures** before committing
4. **Commit changes**: `git commit -m "Short description"`
5. **Push changes**: `git push`

### What Happens During Push
1. **Git pre-push hook triggers** automatically
2. **Environment validation** - checks for virtual environment
3. **Dependency check** - ensures pytest is available
4. **Test execution** - runs all 49 tests with verbose output
5. **Pass/Fail decision**:
   - ✅ **All tests pass**: Push proceeds to remote repository
   - ❌ **Any test fails**: Push is blocked with clear error message

### Example Success Output
```bash
🧪 Running pre-push test validation...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Virtual environment detected: /path/to/venv
🚀 Running full test suite (49 tests)...

=============================================== test session starts ===============================================
test_core.py::TestHealthAndBasics::test_health_endpoint PASSED                    [  2%]
test_core.py::TestHealthAndBasics::test_app_starts PASSED                         [  4%]
...
test_task_extraction.py::TestTaskExtractionRegexPatterns::test_all_regex_patterns_work PASSED [100%]

=============================================== 49 passed in 0.53s ===============================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL TESTS PASSED! Push allowed.
🚀 Proceeding with push to remote repository...
```

### Example Failure Output
```bash
🧪 Running pre-push test validation...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ TESTS FAILED! Push blocked.

📋 Next steps:
  1. Fix the failing tests
  2. Run tests locally: python -m pytest -v
  3. Commit your fixes
  4. Try pushing again

🛡️  This hook prevents broken code from being pushed.
```

## Current Test Status

### Test Files (4 total)
- ✅ `test_core.py` - 11 tests (Basic functionality)
- ✅ `test_slash_command_integration.py` - 14 tests (Integration scenarios)
- ✅ `test_task_backlog_failures.py` - 10 tests (Error handling)
- ✅ `test_task_extraction.py` - 14 tests (Lettered list support)

### Test Coverage
- **Total**: 49 tests
- **Passing**: 49 tests (100% success rate)
- **Key Features Covered**:
  - Health endpoints
  - Slack webhook handling
  - Task extraction (including new lettered list feature)
  - Business request analysis
  - OpenAI API error handling
  - Notion API integration
  - Async operations

## Setup for New Environments

If you clone this repository on a new machine:

1. **Install the git hook**:
   ```bash
   ./setup-git-hooks.sh
   ```

2. **Verify setup**:
   ```bash
   make pre-push
   ```

3. **Test a push** (optional):
   ```bash
   git push --dry-run  # Test without actually pushing
   ```

## Benefits

### 🛡️ **Quality Assurance**
- **No broken code** reaches the repository
- **Automatic validation** on every push
- **Early error detection** before deployment

### 🚀 **Developer Experience**
- **Clear feedback** when tests fail
- **Easy commands** for manual testing
- **Consistent workflow** across environments

### 📈 **Continuous Integration**
- **Local validation** before remote push
- **Complements GitHub Actions** with pre-push validation
- **Faster feedback loop** than waiting for CI

## Troubleshooting

### Common Issues

#### "pytest not found"
```bash
# Install test dependencies
pip install pytest pytest-timeout httpx
```

#### "Virtual environment not activated"
```bash
# Activate virtual environment
source venv/bin/activate
```

#### "Tests fail on push but pass locally"
```bash
# Ensure TEST_MODE is set
export TEST_MODE=true
python -m pytest -v
```

### Disabling the Hook (Not Recommended)

If you need to bypass the hook temporarily:
```bash
git push --no-verify
```

**⚠️ Warning**: This bypasses test validation and can push broken code.

### Re-enabling After Disabling

The hook runs automatically on every push. No action needed to re-enable.

## Maintenance

### Updating the Hook

If you need to modify the pre-push hook:
1. Edit `.git/hooks/pre-push`
2. Ensure it remains executable: `chmod +x .git/hooks/pre-push`
3. Test with: `make pre-push`

### Adding New Tests

1. **Create test file** following existing patterns
2. **Run locally**: `python -m pytest new_test_file.py -v`
3. **Update documentation** if needed
4. **Commit and push** - hook will validate automatically

## Summary

✅ **Complete test automation is now active**
- 49 tests run automatically before every push
- Broken code cannot reach the repository
- Clear feedback and easy troubleshooting
- Convenient commands for development workflow

Your development process is now protected by comprehensive test validation!
