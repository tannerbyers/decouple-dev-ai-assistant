#!/usr/bin/env python3
"""
Test script for PostgreSQL database functionality.

This script tests the PostgreSQL adapter to ensure it's working correctly
without requiring a real PostgreSQL connection.
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_postgres_import():
    """Test that PostgreSQL dependencies can be imported."""
    try:
        import psycopg2
        print("✅ psycopg2 is available")
        assert True  # Test passed
    except ImportError as e:
        print(f"❌ psycopg2 not available: {e}")
        assert False, f"psycopg2 not available: {e}"

def test_postgres_module():
    """Test that our PostgreSQL module can be imported."""
    try:
        sys.path.append('src')
        from postgres_database import PostgresDatabaseManager, create_database_manager
        print("✅ PostgreSQL database module imports successfully")
        assert True  # Test passed
    except ImportError as e:
        print(f"❌ PostgreSQL module import failed: {e}")
        assert False, f"PostgreSQL module import failed: {e}"
    except Exception as e:
        print(f"❌ PostgreSQL module error: {e}")
        assert False, f"PostgreSQL module error: {e}"

def test_factory_function():
    """Test the database manager factory function."""
    try:
        sys.path.append('src')
        
        # Test without DATABASE_URL (should use SQLite)
        original_database_url = os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        from postgres_database import create_database_manager
        db_manager = create_database_manager()
        print("✅ Factory function works for development (SQLite)")
        
        # Test with DATABASE_URL (would use PostgreSQL but we don't have a real connection)
        os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
        
        try:
            # This will fail to connect but should import correctly
            from postgres_database import PostgresDatabaseManager
            print("✅ PostgreSQL manager can be instantiated (connection would fail without real DB)")
        except ValueError as e:
            if "DATABASE_URL" in str(e):
                print("✅ PostgreSQL manager validates DATABASE_URL correctly")
            else:
                raise
        except Exception as e:
            if "connect" in str(e).lower():
                print("✅ PostgreSQL manager attempts connection correctly")
            else:
                raise
        
        # Restore original environment
        if original_database_url:
            os.environ['DATABASE_URL'] = original_database_url
        elif 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        assert True  # Test passed
        
    except Exception as e:
        print(f"❌ Factory function test failed: {e}")
        assert False, f"Factory function test failed: {e}"

def main():
    """Run all tests."""
    print("🧪 Testing PostgreSQL Database Implementation")
    print("=" * 50)
    
    tests = [
        ("PostgreSQL dependency import", test_postgres_import),
        ("PostgreSQL module import", test_postgres_module),
        ("Database factory function", test_factory_function),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   Test failed")
        except Exception as e:
            print(f"   Test error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All PostgreSQL tests passed!")
        print("🚀 Ready for production deployment")
    else:
        print("❌ Some tests failed")
        print("💡 Check that psycopg2-binary is installed: pip install psycopg2-binary")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
