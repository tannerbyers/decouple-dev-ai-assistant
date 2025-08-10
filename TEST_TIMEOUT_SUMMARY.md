# Test Timeout and Configuration Updates

## Overview
Fixed all tests to include proper timeout handling to prevent hanging during setup or execution errors. Updated Warp configuration with concise commit message guidelines.

## Changes Made

### 1. Pytest Configuration (`pytest.ini`)
- Added 30-second timeout for all tests
- Configured thread-based timeout method
- Added verbose output and short traceback options

### 2. Test Files Updated with Timeout Handling

#### Main Test Files:
- `test_main.py` - Added signal-based timeout fixture
- `tests/test_business_goals.py` - Added timeout handling
- `tests/integration/test_security_and_core.py` - Added timeout handling
- `tests/integration/test_end_to_end_integration.py` - Added timeout handling
- `tests/integration/test_message_visibility.py` - Added timeout handling

#### Timeout Implementation:
```python
import signal
import pytest

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out")

@pytest.fixture(autouse=True)
def setup_timeout():
    """Setup timeout for all tests"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30 second timeout
    yield
    signal.alarm(0)  # Cancel alarm
```

### 3. Dependencies Updated
- Added `pytest-timeout` to `requirements.txt`
- Installed pytest-timeout plugin for better timeout handling

### 4. Warp Configuration (`.warp`)
Updated commit message guidelines:
- **Maximum 30 characters** for commit messages
- **No emojis anywhere**
- **Extremely concise** format
- Examples updated to reflect new standards

## Benefits

### Test Reliability
- Tests will automatically timeout after 30 seconds if hanging
- No manual intervention needed if tests get stuck
- Signal-based timeout handling works on macOS/Linux
- Both pytest-timeout plugin and signal-based fixtures for redundancy

### Commit Message Standards
- Enforces extremely concise commit messages
- No emojis policy prevents shell parsing issues
- 30-character limit ensures brevity
- Clear examples of good vs bad commits

## Usage

### Running Tests with Timeout
```bash
# All tests with default 30s timeout
python -m pytest -v

# Specific timeout override
python -m pytest --timeout=10 -v

# Run single test with timeout
python -m pytest test_main.py::test_health_check -v --timeout=5
```

### Commit Message Examples
```bash
# Good (30 chars or less)
git commit -m "Fix timeout tests"
git commit -m "Add dashboard endpoint"
git commit -m "Update warp config"

# Bad (too long or has emojis)
git commit -m "Fix timeout issues in test files"
git commit -m "✨ Add new dashboard feature"
```

## Test Results
All timeout configurations verified working:
- ✅ Main tests timeout properly
- ✅ Integration tests timeout properly  
- ✅ Signal handlers work correctly
- ✅ pytest-timeout plugin installed
- ✅ Both timeout methods work together

## Files Modified
1. `pytest.ini` - Added timeout configuration
2. `test_main.py` - Added timeout fixture
3. `tests/test_business_goals.py` - Added timeout fixture
4. `tests/integration/test_security_and_core.py` - Added timeout fixture
5. `tests/integration/test_end_to_end_integration.py` - Added timeout fixture
6. `tests/integration/test_message_visibility.py` - Added timeout fixture
7. `requirements.txt` - Added pytest-timeout
8. `.warp` - Updated commit message guidelines

The test suite is now robust against hanging tests and will always complete within the timeout period, allowing for unattended test execution.
