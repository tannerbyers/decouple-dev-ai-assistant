# Testing Guide: Preventing Runtime Issues Like the Asyncio Import Bug

## The Problem

The asyncio import issue wasn't caught by tests because our testing strategy had several critical gaps:

1. **Over-mocking**: Tests mocked away the actual async execution paths
2. **Missing integration tests**: No tests exercised the real code paths where the bug occurred
3. **No async test infrastructure**: Couldn't properly test async functions and their error handling
4. **Limited coverage analysis**: Unknown which code paths were actually tested

## Root Cause Analysis

The bug was caused by local `import asyncio` statements inside functions that shadowed the global import:

```python
# PROBLEMATIC PATTERN (original buggy code)
import asyncio  # Global import

def some_function():
    try:
        import asyncio  # Local import shadows global
        loop = asyncio.new_event_loop()
    except RuntimeError:
        # If local import is in try block, asyncio becomes undefined here
        loop = asyncio.get_event_loop()  # UnboundLocalError!
```

## Testing Strategy to Catch Such Issues

### 1. Integration Tests for Async Code Paths

```python
# Example from test_bulk_operations_integration.py
@pytest.mark.asyncio
async def test_bulk_operation_async_execution():
    """Actually execute async code paths to catch import issues"""
    
    # Don't mock the async execution - let it run
    bulk_operation = BulkOperation(
        operation_type=BulkOperationType.PRIORITY_UPDATE,
        filters=TaskFilter(status='To Do'),
        new_values={'priority': 'High'}
    )
    
    # This would trigger the real async execution path
    # where the import issue occurred
```

### 2. Test Different Event Loop Scenarios

```python
def test_event_loop_creation_paths():
    """Test different asyncio.get_event_loop() scenarios"""
    scenarios = [
        Exception("There is no current event loop"),  # RuntimeError
        MagicMock(is_running=lambda: False),          # Existing, not running
        MagicMock(is_running=lambda: True)           # Existing, running
    ]
    
    # Test each scenario that could trigger different code paths
```

### 3. Variable Scoping Tests

```python
def test_variable_scoping_issue_simulation():
    """Test patterns that could cause variable scoping issues"""
    
    def buggy_pattern():
        try:
            import asyncio  # Local import
            return asyncio.new_event_loop()
        except Exception:
            return asyncio.get_event_loop()  # Would fail!
    
    def fixed_pattern():
        import asyncio  # Global import
        try:
            return asyncio.new_event_loop()
        except Exception:
            return asyncio.get_event_loop()  # Works
```

### 4. Direct Async Function Testing

```python
@pytest.mark.asyncio
async def test_async_functions_directly():
    """Test async functions directly, not just their callers"""
    
    # Test the actual async function, not mocked versions
    from main import handle_task_backlog_request
    
    await handle_task_backlog_request("test", {}, "channel")
```

## Required Test Infrastructure

### 1. Install Async Testing Dependencies

```bash
pip install pytest-asyncio pytest-cov pytest-mock
```

### 2. Configure Pytest for Async Testing

```ini
# pytest.ini
[tool:pytest]
asyncio_mode = auto
addopts = 
    --cov=main
    --cov=src
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=70
```

### 3. Test Categories

Mark tests by category to run different test suites:

```python
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.bulk_operations
def test_bulk_operation_integration():
    """Integration test for bulk operations"""
```

## Running Tests to Catch Issues

### 1. Run All Tests with Coverage

```bash
pytest --cov=main --cov=src --cov-report=html
```

### 2. Run Only Integration Tests

```bash
pytest -m integration
```

### 3. Run Async-Specific Tests

```bash
pytest -m asyncio
```

### 4. Check Coverage Report

```bash
# Open htmlcov/index.html to see coverage gaps
open htmlcov/index.html
```

## Code Patterns to Test

### 1. Async Function Calls with Event Loop Management

```python
# Test this pattern specifically
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(async_function())
    else:
        loop.run_until_complete(async_function())
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(async_function())
    finally:
        loop.close()
```

### 2. Import Statements in Functions

- Test functions with local imports
- Test functions with conditional imports
- Test functions with imports in try/except blocks

### 3. Background Thread Execution

- Test threading.Thread execution paths
- Test async code called from background threads
- Test event loop creation in different thread contexts

## Specific Tests for This Bug

The `test_asyncio_import_bug.py` file demonstrates exactly how to test for this type of issue:

1. **Simulate the problematic conditions**: Bulk operation parsing, async execution, event loop creation
2. **Test variable scoping patterns**: Local imports that shadow globals
3. **Exercise all async code paths**: Task cleanup, task backlog generation, bulk operations

## Prevention Strategy

### 1. Mandatory Integration Tests

- Every async function must have an integration test
- Every background execution path must be tested
- Every event loop management scenario must be covered

### 2. Code Coverage Requirements

- Minimum 70% code coverage
- 100% coverage for critical async paths
- Coverage reports in CI/CD

### 3. Static Analysis

Add linting rules to catch problematic patterns:

```python
# pylint: disable=import-outside-toplevel  # Flag local imports
# mypy: check for variable scoping issues
```

### 4. Regular Testing

```bash
# Run full test suite
make test

# Run integration tests
make test-integration

# Check coverage
make test-coverage
```

## CI/CD Integration

Ensure these tests run in CI:

```yaml
# .github/workflows/test.yml
- name: Run comprehensive tests
  run: |
    pytest --cov=main --cov=src --cov-report=xml
    pytest -m integration
    pytest -m asyncio
```

## Summary

The asyncio import bug should have been caught by:

1. **Integration tests** that exercise real async code paths
2. **Proper async test infrastructure** with pytest-asyncio
3. **Code coverage analysis** showing untested paths
4. **Variable scoping tests** for import patterns
5. **Direct async function testing** instead of just mocking

This comprehensive testing strategy will prevent similar runtime issues in the future.
