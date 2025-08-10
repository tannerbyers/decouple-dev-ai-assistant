#!/usr/bin/env python3
"""
Test script for OpsBrain database functionality.

This script tests all major database operations to ensure everything works correctly.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager, DatabaseConfig

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_operations():
    """Test all database operations."""
    print("🧪 Testing OpsBrain Database Operations")
    print("=" * 40)
    
    # Use test database
    test_config = DatabaseConfig(db_path="test_opsbrain.db")
    db = DatabaseManager(test_config)
    
    tests_passed = 0
    tests_total = 0
    
    def run_test(test_name, test_func):
        nonlocal tests_passed, tests_total
        tests_total += 1
        try:
            test_func()
            print(f"✅ {test_name}")
            tests_passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
    
    # Test 1: Configuration management
    def test_configurations():
        # Set configuration
        db.set_config('test_key', 'test_value', 'test', 'Test configuration')
        
        # Get configuration
        value = db.get_config('test_key')
        assert value == 'test_value', f"Expected 'test_value', got '{value}'"
        
        # Get configs by category
        configs = db.get_configs_by_category('test')
        assert 'test_key' in configs, "Configuration not found in category"
        
        # Delete configuration
        deleted = db.delete_config('test_key')
        assert deleted, "Configuration not deleted"
        
        # Verify deletion
        value = db.get_config('test_key')
        assert value is None, "Configuration should be None after deletion"
    
    run_test("Configuration management", test_configurations)
    
    # Test 2: Thread context management
    def test_thread_contexts():
        # Save thread context
        messages = ["User: Hello", "Bot: Hi there"]
        db.save_thread_context('test_thread', 'C123', 'ts123', messages)
        
        # Get thread context
        context = db.get_thread_context('test_thread')
        assert context is not None, "Thread context not found"
        assert context['messages'] == messages, "Messages don't match"
        assert context['channel_id'] == 'C123', "Channel ID doesn't match"
        
        # Update with new messages
        new_messages = ["User: Hello", "Bot: Hi there", "User: How are you?"]
        db.save_thread_context('test_thread', 'C123', 'ts123', new_messages)
        
        # Verify update
        context = db.get_thread_context('test_thread')
        assert len(context['messages']) == 3, f"Expected 3 messages, got {len(context['messages'])}"
    
    run_test("Thread context management", test_thread_contexts)
    
    # Test 3: Business goals management
    def test_business_goals():
        # Create test goal
        test_goal = {
            'id': 'test_goal_1',
            'title': 'Test Goal',
            'description': 'A test business goal',
            'area': 'sales',
            'status': 'in_progress',
            'priority': 3,
            'target_date': '2025-12-31',
            'progress': 50,
            'weekly_actions': ['Action 1', 'Action 2'],
            'daily_actions': ['Daily task'],
            'success_metrics': {'metric1': 'value1'},
            'notes': 'Test notes'
        }
        
        # Save goal
        db.save_business_goal(test_goal)
        
        # Get all goals
        goals = db.get_business_goals()
        assert len(goals) >= 1, "No goals found"
        
        # Find our test goal
        test_goal_found = None
        for goal in goals:
            if goal['id'] == 'test_goal_1':
                test_goal_found = goal
                break
        
        assert test_goal_found is not None, "Test goal not found"
        assert test_goal_found['title'] == 'Test Goal', "Goal title doesn't match"
        assert len(test_goal_found['weekly_actions']) == 2, "Weekly actions count doesn't match"
        
        # Test filtering
        sales_goals = db.get_business_goals(area='sales')
        assert len(sales_goals) >= 1, "No sales goals found"
        
        # Delete goal
        deleted = db.delete_business_goal('test_goal_1')
        assert deleted, "Goal not deleted"
    
    run_test("Business goals management", test_business_goals)
    
    # Test 4: Application settings
    def test_app_settings():
        # Set different types of settings
        db.set_app_setting('test_string', 'hello')
        db.set_app_setting('test_boolean', True)
        db.set_app_setting('test_integer', 42)
        db.set_app_setting('test_json', {'key': 'value'})
        
        # Get settings with type conversion
        assert db.get_app_setting('test_string') == 'hello'
        assert db.get_app_setting('test_boolean') is True
        assert db.get_app_setting('test_integer') == 42
        assert db.get_app_setting('test_json') == {'key': 'value'}
        
        # Test default values
        assert db.get_app_setting('nonexistent', 'default') == 'default'
    
    run_test("Application settings", test_app_settings)
    
    # Test 5: Performance metrics
    def test_performance_metrics():
        # Log some metrics
        db.log_performance_metric('response_time', 0.5, 'seconds', {'endpoint': '/slack'})
        db.log_performance_metric('response_time', 0.3, 'seconds', {'endpoint': '/health'})
        db.log_performance_metric('memory_usage', 150.0, 'MB')
        
        # Get all metrics
        metrics = db.get_performance_metrics()
        assert len(metrics) >= 3, f"Expected at least 3 metrics, got {len(metrics)}"
        
        # Get specific metric
        response_metrics = db.get_performance_metrics('response_time')
        assert len(response_metrics) >= 2, f"Expected at least 2 response_time metrics"
    
    run_test("Performance metrics", test_performance_metrics)
    
    # Test 6: Database info and cleanup
    def test_database_info():
        # Get database info
        info = db.get_database_info()
        assert 'database_path' in info, "Database path not in info"
        assert 'tables' in info, "Tables info not found"
        assert 'total_records' in info, "Total records not found"
        assert info['total_records'] > 0, "No records found in database"
        
        # Test cleanup
        cleaned = db.cleanup_expired_threads()
        # Should be 0 since we just created the threads
        assert cleaned >= 0, "Cleanup should return non-negative number"
    
    run_test("Database info and cleanup", test_database_info)
    
    # Test 7: JSON migration (if business_goals.json exists)
    def test_json_migration():
        if os.path.exists("business_goals.json"):
            # Create a backup first
            original_count = len(db.get_business_goals())
            
            # Run migration
            migrated = db.migrate_from_json("business_goals.json")
            assert migrated > 0, "No goals migrated from JSON"
            
            # Check that goals were added
            new_count = len(db.get_business_goals())
            assert new_count >= original_count + migrated, "Goals not properly migrated"
        else:
            logger.info("No business_goals.json found, skipping migration test")
    
    run_test("JSON migration", test_json_migration)
    
    # Print results
    print("\n📊 Test Results:")
    print(f"   Passed: {tests_passed}/{tests_total}")
    print(f"   Success Rate: {(tests_passed/tests_total)*100:.1f}%")
    
    if tests_passed == tests_total:
        print("✅ All tests passed! Database is working correctly.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    # Cleanup test database
    try:
        if os.path.exists("test_opsbrain.db"):
            os.remove("test_opsbrain.db")
            print("🧹 Test database cleaned up")
    except Exception as e:
        print(f"⚠️  Could not clean up test database: {e}")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = test_database_operations()
    sys.exit(0 if success else 1)
