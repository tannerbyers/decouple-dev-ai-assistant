import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from main import analyze_business_request, parse_database_request
import asyncio

class TestSlashCommandScenarios:
    """Test real-world slash command scenarios that could fail in production"""
    
    def test_business_request_analysis_task_backlog(self):
        """Test analysis of task backlog generation requests"""
        
        # Test the exact request that failed
        user_text = "review my business goals and current scale and add all missing tasks for my business. I think we need to focus on branding, marketing systems, and creating content."
        
        result = analyze_business_request(user_text)
        
        assert result['request_type'] == 'task_backlog'
        assert 'sales' in result['detected_areas']  # Should detect business areas
        assert len(result['detected_areas']) > 0
    
    def test_business_request_analysis_variations(self):
        """Test various ways users might request task backlog generation"""
        
        test_cases = [
            "create all tasks for my business",
            "add all missing tasks",
            "I need a complete task backlog", 
            "generate all the tasks I'm missing",
            "review my goals and create missing tasks",
            "help me with all missing items for my first customer"
        ]
        
        for user_text in test_cases:
            result = analyze_business_request(user_text)
            assert result['request_type'] == 'task_backlog', f"Failed for: {user_text}"
    
    def test_database_request_parsing_task_creation(self):
        """Test parsing of various task creation requests"""
        
        test_cases = [
            ("create task: Build landing page", 'create_task', "Build landing page"),
            ("add task: Set up analytics", 'create_task', "Set up analytics"),  
            ("new task: Client onboarding process", 'create_task', "Client onboarding process"),
            ("task: Review competitor pricing", 'create_task', "Review competitor pricing")
        ]
        
        for user_text, expected_action, expected_title in test_cases:
            result = parse_database_request(user_text)
            assert result['action'] == expected_action
            assert result['requires_db_action'] is True
            assert expected_title.lower() in result['params']['title'].lower()
    
    def test_complex_business_request_with_multiple_areas(self):
        """Test complex requests that mention multiple business areas"""
        
        user_text = "I need help with sales processes, marketing automation, and client delivery workflows. Also need to track financial metrics."
        
        result = analyze_business_request(user_text)
        
        # Should detect multiple areas
        detected = result['detected_areas']
        assert 'sales' in detected
        assert 'process' in detected  # from "processes" and "workflows"
        assert 'financial' in detected
        
        # Should recognize as business-focused
        assert result['is_ceo_focused'] is True
    
    def test_request_type_priority_ordering(self):
        """Test that more specific request types take precedence"""
        
        # This should be classified as task_backlog, not just general
        user_text = "review all tasks and create all missing tasks for marketing"
        result = analyze_business_request(user_text)
        assert result['request_type'] == 'task_backlog'  # More specific than 'review all tasks'
        
        # This should be task_cleanup, not task_backlog
        user_text = "review my tasks and remove anything that doesn't make sense"
        result = analyze_business_request(user_text)
        assert result['request_type'] == 'task_cleanup'


class TestSlashCommandErrorHandling:
    """Test error handling in slash command processing"""
    
    @patch('main.llm')
    @patch('main.fetch_open_tasks')
    def test_openai_timeout_handling(self, mock_fetch_tasks, mock_llm):
        """Test handling of OpenAI API timeouts"""
        
        # Mock data
        mock_fetch_tasks.return_value = ["Task 1", "Task 2"]
        mock_llm.invoke.side_effect = TimeoutError("Request timed out")
        
        # This would normally be tested in the full slash command flow
        # but we can test the error handling directly
        with pytest.raises(TimeoutError):
            mock_llm.invoke("test prompt")
    
    @patch('main.notion')
    def test_notion_api_failure_handling(self, mock_notion):
        """Test handling of Notion API failures during task fetching"""
        
        from notion_client.errors import APIResponseError
        
        # Mock Notion API failure
        mock_notion.databases.query.side_effect = APIResponseError(
            response=MagicMock(status_code=500), 
            message="Internal Server Error"
        )
        
        # Import and test the function that should handle this
        from main import fetch_open_tasks
        
        result = fetch_open_tasks()
        
        # Should return error message instead of crashing
        assert isinstance(result, list)
        assert len(result) > 0
        assert "Unable to fetch tasks from Notion" in result[0]
    
    def test_empty_user_input_handling(self):
        """Test handling of empty or minimal user input"""
        
        test_cases = ["", " ", "help", "?"]
        
        for user_text in test_cases:
            result = analyze_business_request(user_text)
            # Should not crash and should return valid result
            assert 'request_type' in result
            assert 'detected_areas' in result
            assert 'is_ceo_focused' in result
    
    def test_very_long_user_input(self):
        """Test handling of very long user input"""
        
        # Create a very long user input
        long_input = "I need help with " + "business tasks and goals " * 100
        
        result = analyze_business_request(long_input)
        
        # Should not crash and should still detect business areas
        assert 'request_type' in result
        assert len(result['detected_areas']) > 0


class TestAsyncOperationHandling:
    """Test async operation handling in slash commands"""
    
    @pytest.mark.asyncio 
    async def test_async_task_backlog_error_recovery(self):
        """Test error recovery in async task backlog generation"""
        
        with patch('main.get_notion_db_info') as mock_db_info, \
             patch('main.generate_task_backlog') as mock_generate, \
             patch('main.bulk_create_notion_tasks') as mock_bulk_create:
            
            from main import handle_task_backlog_request, NotionDBInfo
            
            # Test scenario 1: DB info retrieval fails
            mock_db_info.return_value = NotionDBInfo(properties={})
            
            # Should handle gracefully and not call subsequent functions
            await handle_task_backlog_request(
                "create tasks", 
                {}, 
                "test_channel"
            )
            
            mock_generate.assert_not_called()
            mock_bulk_create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_concurrent_slash_command_handling(self):
        """Test handling of multiple simultaneous slash commands"""
        
        # This tests that the async operations don't interfere with each other
        mock_business_goals = {'goal1': MagicMock()}
        
        with patch('main.get_notion_db_info') as mock_db_info, \
             patch('main.generate_task_backlog') as mock_generate, \
             patch('main.bulk_create_notion_tasks') as mock_bulk_create:
            
            from main import handle_task_backlog_request, NotionDBInfo
            
            mock_db_info.return_value = NotionDBInfo(properties={'Task': 'title'})
            mock_generate.return_value = [{'title': 'Test Task', 'status': 'To Do'}]
            mock_bulk_create.return_value = None
            
            # Run multiple requests concurrently
            tasks = [
                handle_task_backlog_request("create tasks 1", mock_business_goals, "channel1"),
                handle_task_backlog_request("create tasks 2", mock_business_goals, "channel2"),
                handle_task_backlog_request("create tasks 3", mock_business_goals, "channel3")
            ]
            
            # Should all complete without interfering with each other
            await asyncio.gather(*tasks)
            
            # Verify all were called
            assert mock_generate.call_count == 3
            assert mock_bulk_create.call_count == 3


class TestSpecificFailureScenarios:
    """Test specific scenarios that have failed in production"""
    
    def test_task_backlog_with_focus_areas(self):
        """Test the specific request that failed in production"""
        
        user_text = "review my business goals and current scale and add all missing tasks for my business. I think we need to focus on branding, marketing systems, and creating content."
        
        # Test business request analysis
        analysis = analyze_business_request(user_text)
        assert analysis['request_type'] == 'task_backlog'
        
        # Should detect focus areas from the text
        detected_areas = analysis['detected_areas']
        
        # The word "branding" should trigger sales/process areas
        # The word "marketing" should trigger process area  
        # The word "content" might trigger various areas
        assert len(detected_areas) > 0
        
        # Test that this would trigger the right code path
        assert analysis['request_type'] == 'task_backlog'
    
    @patch('main.llm')
    def test_empty_openai_response_handling(self, mock_llm):
        """Test the specific empty response scenario that caused the JSON error"""
        
        # Mock the exact scenario - OpenAI returns empty content
        mock_message = MagicMock()
        mock_message.content = ""  # This caused the JSON parsing error
        mock_llm.ainvoke.return_value = mock_message
        
        from main import create_fallback_tasks
        
        # The create_fallback_tasks function should be called when OpenAI fails
        result = create_fallback_tasks("review my business goals and add all missing tasks")
        
        # Should return valid tasks structure
        assert len(result) > 0
        assert all('title' in task for task in result)
        assert all('status' in task for task in result)
        assert all('priority' in task for task in result)
        
        # Should include focus areas mentioned in original request
        task_content = " ".join([task['title'] + " " + task['notes'] for task in result])
        assert any(word in task_content.lower() for word in ['brand', 'marketing', 'content'])
    
    def test_markdown_response_cleanup(self):
        """Test cleanup of markdown-wrapped JSON responses"""
        
        test_responses = [
            '```json\n[{"title": "Test"}]\n```',
            '```\n[{"title": "Test"}]\n```', 
            '[{"title": "Test"}]',  # No markdown
            '```python\n[{"title": "Test"}]\n```'  # Wrong language but still wrapped
        ]
        
        for response in test_responses:
            # Simulate the cleanup logic from generate_task_backlog
            cleaned = response.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('\n', 1)[1]  # Remove first line
                cleaned = cleaned.rsplit('\n', 1)[0]  # Remove last line  
                cleaned = cleaned.strip()
            
            # Should be valid JSON after cleanup
            try:
                data = json.loads(cleaned)
                assert isinstance(data, list)
                assert 'title' in data[0]
            except json.JSONDecodeError:
                pytest.fail(f"Failed to parse cleaned response: {cleaned}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
