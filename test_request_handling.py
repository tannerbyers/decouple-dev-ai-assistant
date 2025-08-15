#!/usr/bin/env python3
"""
Request Handling Logic Test Suite
Tests business request analysis, parsing, and command routing.
"""

import os
import sys
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import the main application functions
try:
    from main import (
        analyze_business_request,
        generate_ceo_insights,
        parse_database_request,
        handle_task_backlog_request,
        fetch_open_tasks,
        business_goals,
        logger
    )
    print("✅ Successfully imported request handling functions")
except ImportError as e:
    print(f"❌ Failed to import request handling functions: {e}")
    sys.exit(1)

class RequestHandlingTester:
    """Comprehensive request handling testing suite"""
    
    def __init__(self):
        self.results = {'passed': 0, 'failed': 0, 'total': 0}
        self.test_results = []

    def print_header(self):
        """Print test suite header"""
        print("=" * 80)
        print("🎯 REQUEST HANDLING LOGIC TEST SUITE")
        print("=" * 80)
        print("Testing business request analysis, parsing, and command routing")
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

    def test_help_request_detection(self) -> bool:
        """Test detection of help requests"""
        try:
            help_queries = [
                "help",
                "Help me",
                "I need help",
                "can you help?",
                "help please"
            ]
            
            non_help_queries = [
                "help me create all tasks",  # Should be task_backlog, not help
                "help me with missing tasks",  # Should be task_backlog
                "show me tasks that help",  # Contains help but not a help request
                "create tasks to help sales",  # Contains help but not a help request
                "what should I work on today?"  # No help
            ]
            
            # Test help queries
            for query in help_queries:
                analysis = analyze_business_request(query)
                if analysis['request_type'] != 'help':
                    print(f"    ❌ Failed to detect help in: '{query}' (got: {analysis['request_type']})")
                    return False
                print(f"    ✅ Correctly detected help: '{query}'")
            
            # Test non-help queries
            for query in non_help_queries:
                analysis = analyze_business_request(query)
                if analysis['request_type'] == 'help':
                    print(f"    ❌ Incorrectly detected help in: '{query}'")
                    return False
                print(f"    ✅ Correctly ignored help in: '{query}' (detected: {analysis['request_type']})")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Help detection test failed: {e}")
            return False

    def test_task_backlog_request_detection(self) -> bool:
        """Test detection of task backlog generation requests"""
        try:
            backlog_queries = [
                "create all tasks",
                "generate tasks for my first customer",
                "I need all the missing tasks",
                "create missing tasks",
                "add all missing tasks",
                "task backlog",
                "generate task backlog"
            ]
            
            non_backlog_queries = [
                "show me my tasks",  # Should be general
                "create task: specific task",  # Should be create_task
                "help with tasks",  # Should be help
                "review my tasks"  # Should be task_review
            ]
            
            # Test backlog queries
            for query in backlog_queries:
                analysis = analyze_business_request(query)
                if analysis['request_type'] != 'task_backlog':
                    print(f"    ❌ Failed to detect task_backlog in: '{query}' (got: {analysis['request_type']})")
                    return False
                print(f"    ✅ Correctly detected task_backlog: '{query}'")
            
            # Test non-backlog queries
            for query in non_backlog_queries:
                analysis = analyze_business_request(query)
                if analysis['request_type'] == 'task_backlog':
                    print(f"    ❌ Incorrectly detected task_backlog in: '{query}'")
                    return False
                print(f"    ✅ Correctly identified as {analysis['request_type']}: '{query}'")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Task backlog detection test failed: {e}")
            return False

    def test_business_area_detection(self) -> bool:
        """Test detection of business areas in requests"""
        try:
            area_test_cases = [
                ("I need help with sales strategy", ['sales']),
                ("Create marketing content for our campaigns", ['process']),  # marketing maps to process
                ("Improve client delivery processes", ['delivery']),
                ("Track financial metrics and budget", ['financial']),
                ("Hire new team members", ['team']),
                ("Automate our workflow processes", ['process']),
                ("Sales and marketing alignment", ['sales', 'process']),  # Should detect both
                ("Revenue pipeline management", ['sales']),  # revenue -> sales
                ("Client work efficiency", ['delivery'])  # client work -> delivery
            ]
            
            for query, expected_areas in area_test_cases:
                analysis = analyze_business_request(query)
                detected_areas = analysis['detected_areas']
                
                # Check if all expected areas are detected
                for expected_area in expected_areas:
                    if expected_area not in detected_areas:
                        print(f"    ❌ Failed to detect area '{expected_area}' in: '{query}' (got: {detected_areas})")
                        return False
                
                print(f"    ✅ Correctly detected areas {detected_areas}: '{query[:40]}...'")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Business area detection test failed: {e}")
            return False

    def test_request_type_priority_ordering(self) -> bool:
        """Test that request types are detected in correct priority order"""
        try:
            # Test that more specific patterns take priority over general ones
            priority_test_cases = [
                ("create all tasks for sales", 'task_backlog'),  # Should be task_backlog, not general
                ("review all my tasks", 'task_review'),  # Should be task_review, not general
                ("remove tasks that don't make sense", 'task_cleanup'),  # Should be cleanup, not general
                ("create goal: increase revenue", 'goal_creation'),  # Should be goal_creation
                ("show me dashboard", 'dashboard'),  # Should be dashboard
                ("help me plan this week", 'planning'),  # Should be planning
                ("research our competitors", 'research')  # Should be research
            ]
            
            for query, expected_type in priority_test_cases:
                analysis = analyze_business_request(query)
                detected_type = analysis['request_type']
                
                if detected_type != expected_type:
                    print(f"    ❌ Wrong priority for: '{query}' (expected: {expected_type}, got: {detected_type})")
                    return False
                
                print(f"    ✅ Correct priority {detected_type}: '{query[:40]}...'")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Request type priority test failed: {e}")
            return False

    def test_ceo_focus_detection(self) -> bool:
        """Test detection of CEO-focused requests"""
        try:
            ceo_queries = [
                "I need CEO insights on revenue",
                "Business strategy for growth",
                "Revenue optimization plan",
                "Strategic business decisions"
            ]
            
            non_ceo_queries = [
                "Create a simple task",
                "Show me my todo list",
                "Help with formatting",
                "Technical implementation details"
            ]
            
            # Test CEO queries
            for query in ceo_queries:
                analysis = analyze_business_request(query)
                if not analysis['is_ceo_focused']:
                    print(f"    ❌ Failed to detect CEO focus in: '{query}'")
                    return False
                print(f"    ✅ Correctly detected CEO focus: '{query[:40]}...'")
            
            # Test non-CEO queries
            for query in non_ceo_queries:
                analysis = analyze_business_request(query)
                if analysis['is_ceo_focused']:
                    print(f"    ❌ Incorrectly detected CEO focus in: '{query}'")
                    return False
                print(f"    ✅ Correctly identified as non-CEO: '{query[:40]}...'")
            
            return True
            
        except Exception as e:
            print(f"    ❌ CEO focus detection test failed: {e}")
            return False

    def test_database_request_parsing(self) -> bool:
        """Test parsing of database action requests"""
        try:
            db_test_cases = [
                ("create task: Review quarterly reports", 'create_task'),
                ("add client: Acme Corporation", 'create_client'),
                ("log metric: $50k revenue this month", 'log_metric'),
                ("mark task as done", 'trello_done'),
                ("check status of project", 'trello_status'),
                ("add missing business tasks", 'add_business_tasks'),
                ("find client information", 'search'),
                ("create goal: Increase sales by 30%", 'create_goal')
            ]
            
            for query, expected_action in db_test_cases:
                parsed = parse_database_request(query)
                detected_action = parsed.get('action_type') if parsed else None
                
                if detected_action != expected_action:
                    print(f"    ❌ Wrong action for: '{query}' (expected: {expected_action}, got: {detected_action})")
                    return False
                
                print(f"    ✅ Correct action {detected_action}: '{query[:40]}...'")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Database request parsing test failed: {e}")
            return False

    def test_parameter_extraction(self) -> bool:
        """Test extraction of parameters from requests"""
        try:
            # Test task creation parameter extraction
            parsed = parse_database_request("create task: Complete project documentation")
            if 'title' not in parsed or parsed['title'] != "Complete project documentation":
                print(f"    ❌ Failed to extract task title: {parsed}")
                return False
            print(f"    ✅ Correctly extracted task title: '{parsed['title']}'")
            
            # Test client creation parameter extraction  
            parsed = parse_database_request("add client: Global Tech Solutions")
            if 'name' not in parsed or parsed['name'] != "Global Tech Solutions":
                print(f"    ❌ Failed to extract client name: {parsed}")
                return False
            print(f"    ✅ Correctly extracted client name: '{parsed['name']}'")
            
            # Test goal creation parameter extraction
            parsed = parse_database_request("create goal: Reach $100k monthly revenue")
            if 'title' not in parsed or parsed['title'] != "Reach $100k monthly revenue":
                print(f"    ❌ Failed to extract goal title: {parsed}")
                return False
            print(f"    ✅ Correctly extracted goal title: '{parsed['title']}'")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Parameter extraction test failed: {e}")
            return False

    def test_edge_case_handling(self) -> bool:
        """Test handling of edge cases and malformed requests"""
        try:
            edge_cases = [
                "",  # Empty string
                "   ",  # Whitespace only
                "a",  # Single character
                "help" * 100,  # Very long help request
                "create task:",  # Missing task title
                "add client:",  # Missing client name
                "log metric:",  # Missing metric details
                "xyz random text 123",  # Nonsensical input
                "!@#$%^&*()",  # Special characters only
            ]
            
            for query in edge_cases:
                try:
                    analysis = analyze_business_request(query)
                    
                    # Should always return a valid structure
                    required_fields = ['detected_areas', 'request_type', 'is_ceo_focused']
                    for field in required_fields:
                        if field not in analysis:
                            print(f"    ❌ Missing field '{field}' for edge case: '{query}'")
                            return False
                    
                    # Should always have valid types
                    if not isinstance(analysis['detected_areas'], list):
                        print(f"    ❌ Invalid detected_areas type for: '{query}'")
                        return False
                    
                    if not isinstance(analysis['request_type'], str):
                        print(f"    ❌ Invalid request_type type for: '{query}'")
                        return False
                    
                    if not isinstance(analysis['is_ceo_focused'], bool):
                        print(f"    ❌ Invalid is_ceo_focused type for: '{query}'")
                        return False
                    
                    print(f"    ✅ Handled edge case: '{query[:20]}...' -> {analysis['request_type']}")
                    
                except Exception as e:
                    print(f"    ❌ Exception on edge case '{query}': {e}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"    ❌ Edge case handling test failed: {e}")
            return False

    def test_request_context_consistency(self) -> bool:
        """Test that related requests maintain consistent context"""
        try:
            # Test that business area detection is consistent
            sales_queries = [
                "help with sales",
                "create sales tasks", 
                "sales strategy planning",
                "revenue pipeline management"
            ]
            
            for query in sales_queries:
                analysis = analyze_business_request(query)
                if 'sales' not in analysis['detected_areas']:
                    print(f"    ❌ Inconsistent sales detection for: '{query}' (areas: {analysis['detected_areas']})")
                    return False
                print(f"    ✅ Consistent sales context: '{query}'")
            
            # Test that task-related queries are handled consistently
            task_queries = [
                "create all tasks",
                "review my tasks", 
                "show me tasks",
                "clean up tasks"
            ]
            
            task_types = ['task_backlog', 'task_review', 'general', 'task_cleanup']
            
            for i, query in enumerate(task_queries):
                analysis = analyze_business_request(query)
                expected_type = task_types[i]
                if analysis['request_type'] != expected_type:
                    print(f"    ❌ Inconsistent task type for: '{query}' (expected: {expected_type}, got: {analysis['request_type']})")
                    return False
                print(f"    ✅ Consistent task context: '{query}' -> {analysis['request_type']}")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Request context consistency test failed: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all request handling tests"""
        self.print_header()
        
        # Define test suite
        tests = [
            ("Help Request Detection", self.test_help_request_detection),
            ("Task Backlog Detection", self.test_task_backlog_request_detection),
            ("Business Area Detection", self.test_business_area_detection),
            ("Request Type Priority", self.test_request_type_priority_ordering),
            ("CEO Focus Detection", self.test_ceo_focus_detection),
            ("Database Request Parsing", self.test_database_request_parsing),
            ("Parameter Extraction", self.test_parameter_extraction),
            ("Edge Case Handling", self.test_edge_case_handling),
            ("Context Consistency", self.test_request_context_consistency)
        ]
        
        print("🚀 Starting request handling tests...\n")
        
        # Run each test
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            print()
        
        # Print final summary
        self.print_summary()
        
        return self.results['failed'] == 0

    def print_summary(self):
        """Print test results summary"""
        print("=" * 80)
        print("📊 REQUEST HANDLING TEST RESULTS")
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
            print("\n🎉 ALL TESTS PASSED! Your request handling logic is working correctly.")
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
    """Run the request handling test suite"""
    try:
        tester = RequestHandlingTester()
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
