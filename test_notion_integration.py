#!/usr/bin/env python3
"""
Comprehensive Notion Integration Test Suite
Tests database schema detection, task creation, bulk operations, and error handling.
"""

import os
import sys
import json
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional
import pytest
from dataclasses import dataclass

# Import the main application functions
try:
    from main import (
        create_notion_task,
        bulk_create_notion_tasks,
        get_notion_db_info,
        generate_task_backlog,
        create_fallback_tasks,
        NotionDBInfo,
        NOTION_DB_ID,
        notion,
        llm,
        logger
    )
    print("✅ Successfully imported main application functions")
except ImportError as e:
    print(f"❌ Failed to import main functions: {e}")
    sys.exit(1)

class NotionIntegrationTester:
    """Comprehensive Notion integration testing suite"""
    
    def __init__(self):
        self.results = {'passed': 0, 'failed': 0, 'total': 0}
        self.test_results = []
        
        # Mock database schemas for testing
        self.mock_db_schema_standard = {
            'properties': {
                'Task': {'type': 'title'},
                'Status': {'type': 'select'},
                'Priority': {'type': 'select'},
                'Project': {'type': 'rich_text'},
                'Notes': {'type': 'rich_text'},
                'Due Date': {'type': 'date'}
            }
        }
        
        self.mock_db_schema_alternative = {
            'properties': {
                'Name': {'type': 'title'},
                'Status': {'type': 'select'},
                'Priority': {'type': 'select'},
                'Category': {'type': 'select'},
                'Description': {'type': 'rich_text'},
                'Due': {'type': 'date'}
            }
        }
        
        self.mock_db_schema_minimal = {
            'properties': {
                'Title': {'type': 'title'},
                'Status': {'type': 'select'}
            }
        }

    def print_header(self):
        """Print test suite header"""
        print("=" * 80)
        print("📋 NOTION INTEGRATION TEST SUITE")
        print("=" * 80)
        print("Testing database schema detection, task creation, and bulk operations")
        print("=" * 80)
        print()

    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results"""
        print(f"🧪 Testing: {test_name}")
        
        try:
            success = test_func()
            
            if success:
                print(f"  ✅ PASSED")
                self.results['passed'] += 1
            else:
                print(f"  ❌ FAILED")
                self.results['failed'] += 1
            
            self.results['total'] += 1
            self.test_results.append({
                'name': test_name,
                'success': success
            })
            
            return success
            
        except Exception as e:
            print(f"  💥 ERROR: {str(e)}")
            self.results['failed'] += 1
            self.results['total'] += 1
            self.test_results.append({
                'name': test_name,
                'success': False,
                'error': str(e)
            })
            return False

    def test_database_schema_detection_standard(self) -> bool:
        """Test database schema detection with standard property names"""
        try:
            with patch.object(notion.databases, 'retrieve') as mock_retrieve:
                mock_retrieve.return_value = self.mock_db_schema_standard
                
                # Test the create_notion_task function's schema detection
                with patch.object(notion.pages, 'create') as mock_create:
                    mock_create.return_value = {'id': 'test_page_id'}
                    
                    result = create_notion_task(
                        title="Test Task",
                        status="To Do",
                        priority="High",
                        project="Testing",
                        notes="Test notes"
                    )
                    
                    # Verify the function succeeded
                    if not result:
                        print(f"    ❌ Task creation returned False")
                        return False
                    
                    # Verify the correct properties were sent to Notion
                    call_args = mock_create.call_args
                    properties = call_args[1]['properties']
                    
                    expected_properties = [
                        'Task',    # Title field
                        'Status',  # Select field
                        'Priority', # Select field  
                        'Project', # Rich text field
                        'Notes'    # Rich text field
                    ]
                    
                    for prop in expected_properties:
                        if prop not in properties:
                            print(f"    ❌ Missing expected property: {prop}")
                            return False
                    
                    print(f"    ✅ All expected properties mapped correctly")
                    print(f"    ✅ Properties: {list(properties.keys())}")
                    
                    return True
                    
        except Exception as e:
            print(f"    ❌ Schema detection failed: {e}")
            return False

    def test_database_schema_detection_alternative(self) -> bool:
        """Test database schema detection with alternative property names"""
        try:
            with patch.object(notion.databases, 'retrieve') as mock_retrieve:
                mock_retrieve.return_value = self.mock_db_schema_alternative
                
                with patch.object(notion.pages, 'create') as mock_create:
                    mock_create.return_value = {'id': 'test_page_id'}
                    
                    result = create_notion_task(
                        title="Test Task Alt",
                        status="In Progress",
                        priority="Medium",
                        project="Alternative Testing",
                        notes="Alternative test notes"
                    )
                    
                    if not result:
                        print(f"    ❌ Task creation returned False")
                        return False
                    
                    # Verify correct property mapping for alternative schema
                    call_args = mock_create.call_args
                    properties = call_args[1]['properties']
                    
                    # Should map to 'Name' instead of 'Task'
                    if 'Name' not in properties:
                        print(f"    ❌ Failed to map to 'Name' property")
                        return False
                    
                    # Should map to 'Category' instead of 'Project'  
                    if 'Category' not in properties:
                        print(f"    ❌ Failed to map to 'Category' property")
                        return False
                        
                    # Should map to 'Description' instead of 'Notes'
                    if 'Description' not in properties:
                        print(f"    ❌ Failed to map to 'Description' property")
                        return False
                    
                    print(f"    ✅ Alternative schema mapped correctly")
                    print(f"    ✅ Properties: {list(properties.keys())}")
                    
                    return True
                    
        except Exception as e:
            print(f"    ❌ Alternative schema test failed: {e}")
            return False

    def test_database_schema_detection_minimal(self) -> bool:
        """Test database schema detection with minimal properties"""
        try:
            with patch.object(notion.databases, 'retrieve') as mock_retrieve:
                mock_retrieve.return_value = self.mock_db_schema_minimal
                
                with patch.object(notion.pages, 'create') as mock_create:
                    mock_create.return_value = {'id': 'test_page_id'}
                    
                    result = create_notion_task(
                        title="Minimal Test Task",
                        status="To Do",
                        priority="Low",  # Should be ignored - no Priority property
                        project="Should Be Ignored",  # Should be ignored - no Project property
                        notes="Should be ignored"  # Should be ignored - no Notes property
                    )
                    
                    if not result:
                        print(f"    ❌ Task creation returned False")
                        return False
                    
                    call_args = mock_create.call_args
                    properties = call_args[1]['properties']
                    
                    # Should only have Title and Status
                    if len(properties) != 2:
                        print(f"    ❌ Expected 2 properties, got {len(properties)}: {list(properties.keys())}")
                        return False
                    
                    if 'Title' not in properties or 'Status' not in properties:
                        print(f"    ❌ Missing required properties. Got: {list(properties.keys())}")
                        return False
                    
                    print(f"    ✅ Minimal schema handled correctly")
                    print(f"    ✅ Only mapped available properties: {list(properties.keys())}")
                    
                    return True
                    
        except Exception as e:
            print(f"    ❌ Minimal schema test failed: {e}")
            return False

    def test_notion_api_error_handling(self) -> bool:
        """Test error handling when Notion API fails"""
        try:
            # Test database retrieval failure
            with patch.object(notion.databases, 'retrieve') as mock_retrieve:
                from notion_client.errors import APIResponseError
                mock_retrieve.side_effect = APIResponseError(
                    response=Mock(status_code=404),
                    message="Database not found",
                    code="object_not_found"
                )
                
                result = create_notion_task(title="Should Fail")
                
                if result:
                    print(f"    ❌ Expected False when API fails, got True")
                    return False
                
                print(f"    ✅ Correctly handled database retrieval failure")
                
            # Test page creation failure
            with patch.object(notion.databases, 'retrieve') as mock_retrieve:
                mock_retrieve.return_value = self.mock_db_schema_standard
                
                with patch.object(notion.pages, 'create') as mock_create:
                    mock_create.side_effect = APIResponseError(
                        response=Mock(status_code=400),
                        message="Invalid properties",
                        code="validation_error"
                    )
                    
                    result = create_notion_task(title="Should Also Fail")
                    
                    if result:
                        print(f"    ❌ Expected False when page creation fails, got True")
                        return False
                    
                    print(f"    ✅ Correctly handled page creation failure")
                    
            return True
            
        except Exception as e:
            print(f"    ❌ Error handling test failed: {e}")
            return False

    def test_task_property_validation(self) -> bool:
        """Test validation of task properties before creation"""
        try:
            with patch.object(notion.databases, 'retrieve') as mock_retrieve:
                mock_retrieve.return_value = self.mock_db_schema_standard
                
                with patch.object(notion.pages, 'create') as mock_create:
                    mock_create.return_value = {'id': 'test_page_id'}
                    
                    # Test with empty title (should still work)
                    result = create_notion_task(title="")
                    if not result:
                        print(f"    ❌ Empty title test failed")
                        return False
                    
                    # Test with None values (should be handled gracefully)
                    result = create_notion_task(
                        title="Valid Title",
                        status=None,
                        priority=None,
                        project=None,
                        notes=None
                    )
                    if not result:
                        print(f"    ❌ None values test failed")
                        return False
                    
                    # Test with very long title (should be truncated or handled)
                    long_title = "x" * 2000  # Very long title
                    result = create_notion_task(title=long_title)
                    if not result:
                        print(f"    ❌ Long title test failed")
                        return False
                    
                    print(f"    ✅ Property validation handled correctly")
                    return True
                    
        except Exception as e:
            print(f"    ❌ Property validation test failed: {e}")
            return False

    def test_fallback_task_generation(self) -> bool:
        """Test fallback task generation when AI fails"""
        try:
            # Test with different user inputs
            test_inputs = [
                "help me with marketing",
                "I need sales tasks",
                "create processes and operations",
                "generic business help",
                ""  # Empty input
            ]
            
            for user_input in test_inputs:
                fallback_tasks = create_fallback_tasks(user_input)
                
                if not fallback_tasks:
                    print(f"    ❌ No fallback tasks generated for: '{user_input}'")
                    return False
                
                if not isinstance(fallback_tasks, list):
                    print(f"    ❌ Fallback tasks not a list for: '{user_input}'")
                    return False
                
                # Validate task structure
                for task in fallback_tasks:
                    required_fields = ['title', 'status', 'priority', 'project', 'notes']
                    for field in required_fields:
                        if field not in task:
                            print(f"    ❌ Missing field '{field}' in fallback task")
                            return False
                
                print(f"    ✅ Generated {len(fallback_tasks)} fallback tasks for: '{user_input[:30]}...'")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Fallback task generation test failed: {e}")
            return False

    def test_task_backlog_generation_with_mock_ai(self) -> bool:
        """Test task backlog generation with mocked AI response"""
        try:
            # Mock database info
            db_info = NotionDBInfo(properties={
                'Task': 'title',
                'Status': 'select',
                'Priority': 'select',
                'Project': 'rich_text',
                'Notes': 'rich_text'
            })
            
            # Mock AI response with valid JSON
            mock_ai_response = [
                {
                    "title": "AI Generated Task 1",
                    "status": "To Do",
                    "priority": "High",
                    "project": "Testing",
                    "notes": "STEPS: 1. Do something 2. Complete it DELIVERABLE: Completed task"
                },
                {
                    "title": "AI Generated Task 2", 
                    "status": "To Do",
                    "priority": "Medium",
                    "project": "Development",
                    "notes": "STEPS: 1. Start work 2. Finish work DELIVERABLE: Working feature"
                }
            ]
            
            # Mock the LLM response
            mock_message = Mock()
            mock_message.content = json.dumps(mock_ai_response)
            
            with patch.object(llm, 'ainvoke', return_value=mock_message):
                # Run the async function
                async def run_test():
                    tasks = await generate_task_backlog(
                        user_text="Create test tasks",
                        business_goals={},
                        db_info=db_info
                    )
                    return tasks
                
                # Use asyncio to run the test
                tasks = asyncio.run(run_test())
                
                if not tasks:
                    print(f"    ❌ No tasks generated from AI")
                    return False
                
                if len(tasks) != 2:
                    print(f"    ❌ Expected 2 tasks, got {len(tasks)}")
                    return False
                
                # Validate task structure
                for task in tasks:
                    required_fields = ['title', 'status', 'priority', 'project', 'notes']
                    for field in required_fields:
                        if field not in task:
                            print(f"    ❌ Missing field '{field}' in generated task")
                            return False
                
                print(f"    ✅ Successfully generated {len(tasks)} tasks from AI")
                print(f"    ✅ Task titles: {[t['title'] for t in tasks]}")
                
                return True
                
        except Exception as e:
            print(f"    ❌ Task backlog generation test failed: {e}")
            return False

    def test_malformed_ai_response_handling(self) -> bool:
        """Test handling of malformed AI responses"""
        try:
            db_info = NotionDBInfo(properties={'Task': 'title', 'Status': 'select'})
            
            # Test various malformed responses
            malformed_responses = [
                "",  # Empty response
                "not json at all",  # Invalid JSON
                "```json\n[{\"title\": \"test\"}]\n```",  # JSON in code blocks
                "[{\"missing_title\": \"value\"}]",  # Missing required fields
                "{\"not_array\": \"value\"}",  # Not an array
                "[\"string_instead_of_object\"]"  # String instead of object
            ]
            
            for i, malformed_response in enumerate(malformed_responses):
                mock_message = Mock()
                mock_message.content = malformed_response
                
                with patch.object(llm, 'ainvoke', return_value=mock_message):
                    async def run_test():
                        return await generate_task_backlog(
                            user_text="test",
                            business_goals={},
                            db_info=db_info
                        )
                    
                    tasks = asyncio.run(run_test())
                    
                    # Should fall back to default tasks
                    if not tasks:
                        print(f"    ❌ No fallback tasks for malformed response {i+1}")
                        return False
                    
                    # Should be fallback tasks (not empty)
                    if len(tasks) == 0:
                        print(f"    ❌ Empty fallback tasks for malformed response {i+1}")
                        return False
                    
                    print(f"    ✅ Handled malformed response {i+1}: '{malformed_response[:30]}...'")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Malformed response handling test failed: {e}")
            return False

    async def test_bulk_task_creation_with_mocks(self) -> bool:
        """Test bulk task creation with mocked dependencies"""
        try:
            # Mock Slack API call
            with patch('requests.post') as mock_post:
                mock_post.return_value.ok = True
                
                # Mock Notion database and page creation
                with patch.object(notion.databases, 'retrieve') as mock_db_retrieve:
                    mock_db_retrieve.return_value = self.mock_db_schema_standard
                    
                    with patch.object(notion.pages, 'create') as mock_page_create:
                        mock_page_create.return_value = {'id': 'test_page_id'}
                        
                        # Test tasks
                        test_tasks = [
                            {
                                'title': 'Bulk Test Task 1',
                                'status': 'To Do',
                                'priority': 'High',
                                'project': 'Testing',
                                'notes': 'Test notes 1'
                            },
                            {
                                'title': 'Bulk Test Task 2',
                                'status': 'In Progress', 
                                'priority': 'Medium',
                                'project': 'Development',
                                'notes': 'Test notes 2'
                            }
                        ]
                        
                        # Run bulk creation
                        await bulk_create_notion_tasks(test_tasks, "test_channel")
                        
                        # Verify Slack messages were sent (initial + final)
                        if mock_post.call_count < 2:
                            print(f"    ❌ Expected at least 2 Slack messages, got {mock_post.call_count}")
                            return False
                        
                        # Verify Notion page creation was called for each task
                        if mock_page_create.call_count != len(test_tasks):
                            print(f"    ❌ Expected {len(test_tasks)} page creations, got {mock_page_create.call_count}")
                            return False
                        
                        print(f"    ✅ Successfully created {len(test_tasks)} tasks in bulk")
                        print(f"    ✅ Sent {mock_post.call_count} Slack notifications")
                        
                        return True
                        
        except Exception as e:
            print(f"    ❌ Bulk task creation test failed: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all Notion integration tests"""
        self.print_header()
        
        # Define test suite
        tests = [
            ("Database Schema - Standard", self.test_database_schema_detection_standard),
            ("Database Schema - Alternative", self.test_database_schema_detection_alternative),
            ("Database Schema - Minimal", self.test_database_schema_detection_minimal),
            ("Notion API Error Handling", self.test_notion_api_error_handling),
            ("Task Property Validation", self.test_task_property_validation),
            ("Fallback Task Generation", self.test_fallback_task_generation),
            ("AI Task Backlog Generation", self.test_task_backlog_generation_with_mock_ai),
            ("Malformed AI Response", self.test_malformed_ai_response_handling)
        ]
        
        # Add async test
        async_tests = [
            ("Bulk Task Creation", self.test_bulk_task_creation_with_mocks)
        ]
        
        print("🚀 Starting Notion integration tests...\n")
        
        # Run synchronous tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            print()
        
        # Run async tests
        for test_name, test_func in async_tests:
            print(f"🧪 Testing: {test_name}")
            try:
                success = asyncio.run(test_func())
                if success:
                    print(f"  ✅ PASSED")
                    self.results['passed'] += 1
                else:
                    print(f"  ❌ FAILED")
                    self.results['failed'] += 1
                self.results['total'] += 1
                self.test_results.append({
                    'name': test_name,
                    'success': success
                })
            except Exception as e:
                print(f"  💥 ERROR: {str(e)}")
                self.results['failed'] += 1
                self.results['total'] += 1
                self.test_results.append({
                    'name': test_name,
                    'success': False,
                    'error': str(e)
                })
            print()
        
        # Print final summary
        self.print_summary()
        
        return self.results['failed'] == 0

    def print_summary(self):
        """Print test results summary"""
        print("=" * 80)
        print("📊 NOTION INTEGRATION TEST RESULTS")
        print("=" * 80)
        
        total = self.results['total']
        passed = self.results['passed']
        failed = self.results['failed']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"🎯 Total Tests: {total}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Your Notion integration is working correctly.")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Issues identified:")
            
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['name']}")
                    if 'error' in result:
                        print(f"      Error: {result['error']}")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['name']}")
        
        print("=" * 80)


def main():
    """Run the Notion integration test suite"""
    try:
        tester = NotionIntegrationTester()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
