#!/usr/bin/env python3
"""
Agent System Test Runner

This script runs comprehensive tests for the orchestrator agent system,
including routing logic, agent interactions, and deterministic behavior.

Usage:
    python run_agent_tests.py              # Run all tests
    python run_agent_tests.py --fast       # Run only fast unit tests
    python run_agent_tests.py --integration # Run only integration tests  
    python run_agent_tests.py --coverage   # Run with coverage report
    python run_agent_tests.py --verbose    # Run with detailed output
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def setup_test_environment():
    """Set up the test environment and dependencies."""
    print("🔧 Setting up test environment...")
    
    # Add src directory to Python path
    src_dir = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_dir))
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"])
        import pytest
        print("✅ pytest installed successfully")
    
    return True


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run the specified tests."""
    test_file = "tests/test_agent_system.py"
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
    
    # Add async support
    cmd.append("-p")
    cmd.append("no:warnings")
    
    # Select test categories
    if test_type == "fast":
        # Run unit tests only (exclude integration tests)
        cmd.extend(["-k", "not integration"])
    elif test_type == "integration":
        # Run integration tests only
        cmd.extend(["-k", "integration"])
    
    cmd.append(test_file)
    
    print(f"🚀 Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ Test file not found. Make sure tests/test_agent_system.py exists.")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def check_agent_files():
    """Check that all required agent files exist."""
    print("🔍 Checking agent system files...")
    
    required_files = [
        "src/agent_integration.py",
        "src/agent_orchestrator.py", 
        "src/task_manager_agent.py",
        "src/task_discovery_agent.py",
        "src/priority_engine_agent.py",
        "src/chat_handler_agent.py",
        "tests/test_agent_system.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n⚠️  Warning: {len(missing_files)} files are missing.")
        print("The tests may fail due to import errors.")
        return False
    
    print("✅ All required files found!")
    return True


def run_mock_tests():
    """Run a simplified mock test to verify the test framework works."""
    print("🧪 Running mock tests to verify framework...")
    
    mock_test_code = '''
import pytest

def test_basic_functionality():
    """Basic test to verify pytest works."""
    assert 1 + 1 == 2
    assert "hello".upper() == "HELLO"

def test_mock_agent_routing():
    """Mock test for agent routing logic."""
    # Simulate request type detection
    request_types = {
        "create task": "TASK_MANAGEMENT",
        "what should I do": "PRIORITY_SELECTION", 
        "missing tasks": "TASK_DISCOVERY",
        "call client": "CHAT_TASK_ADDITION"
    }
    
    for request, expected_type in request_types.items():
        # Mock the routing logic
        if "create" in request or "task" in request:
            detected_type = "TASK_MANAGEMENT"
        elif "should I do" in request or "priority" in request:
            detected_type = "PRIORITY_SELECTION"
        elif "missing" in request:
            detected_type = "TASK_DISCOVERY"
        elif "call" in request or "client" in request:
            detected_type = "CHAT_TASK_ADDITION"
        else:
            detected_type = "UNKNOWN"
        
        if detected_type == expected_type:
            print(f"✅ Routing test passed: '{request}' -> {expected_type}")
        else:
            print(f"❌ Routing test failed: '{request}' -> {detected_type} (expected {expected_type})")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
    
    # Write mock test to temporary file
    mock_test_file = Path("temp_mock_test.py")
    try:
        with open(mock_test_file, "w") as f:
            f.write(mock_test_code)
        
        # Run mock test
        result = subprocess.run([
            sys.executable, "-m", "pytest", str(mock_test_file), "-v"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Mock tests passed! Test framework is working.")
            print("📊 Test output:")
            print(result.stdout)
            return True
        else:
            print("❌ Mock tests failed!")
            print("Error output:")
            print(result.stderr)
            return False
    
    finally:
        # Clean up mock test file
        if mock_test_file.exists():
            mock_test_file.unlink()


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run agent system tests")
    parser.add_argument("--fast", action="store_true", help="Run only fast unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--verbose", action="store_true", help="Run with detailed output")
    parser.add_argument("--mock", action="store_true", help="Run mock tests to verify framework")
    parser.add_argument("--check", action="store_true", help="Check if required files exist")
    
    args = parser.parse_args()
    
    print("🤖 Agent System Test Runner")
    print("=" * 50)
    
    # Check files if requested
    if args.check:
        check_agent_files()
        return
    
    # Run mock tests if requested
    if args.mock:
        run_mock_tests()
        return
    
    # Set up environment
    if not setup_test_environment():
        print("❌ Failed to set up test environment")
        sys.exit(1)
    
    # Check required files
    if not check_agent_files():
        print("\n⚠️  Some files are missing. Tests may fail.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Determine test type
    test_type = "all"
    if args.fast:
        test_type = "fast"
    elif args.integration:
        test_type = "integration"
    
    # Run tests
    exit_code = run_tests(test_type, args.verbose, args.coverage)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        print("🎉 Agent system is working correctly!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
        print("🔧 Check the output above for details.")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
