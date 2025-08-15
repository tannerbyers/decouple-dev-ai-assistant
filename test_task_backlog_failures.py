import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from main import generate_task_backlog, create_fallback_tasks, handle_task_backlog_request, NotionDBInfo
import logging

# Set up test logging
logging.basicConfig(level=logging.INFO)

class TestTaskBacklogGenerationFailures:
    """Test various failure scenarios in task backlog generation"""
    
    @pytest.fixture
    def mock_business_goals(self):
        """Mock business goals for testing"""
        return {
            'goal1': MagicMock(title='Increase Revenue', description='Grow to $30k MRR'),
            'goal2': MagicMock(title='Improve Delivery', description='Standardize processes')
        }
    
    @pytest.fixture 
    def mock_db_info(self):
        """Mock Notion database info"""
        return NotionDBInfo(properties={
            'Task': 'title',
            'Status': 'select', 
            'Priority': 'select',
            'Project': 'rich_text',
            'Notes': 'rich_text'
        })
    
    @pytest.mark.asyncio
    async def test_empty_openai_response(self, mock_business_goals, mock_db_info):
        """Test handling of empty OpenAI response"""
        with patch('main.llm') as mock_llm:
            # Mock empty response
            mock_message = MagicMock()
            mock_message.content = ""
            mock_llm.ainvoke = AsyncMock(return_value=mock_message)
            
            result = await generate_task_backlog(
                "review my business goals and add all missing tasks", 
                mock_business_goals, 
                mock_db_info
            )
            
            # Should return fallback tasks
            assert len(result) > 0
            assert isinstance(result, list)
            assert all('title' in task for task in result)
            # Verify fallback tasks were created
            assert any('brand positioning' in task['title'].lower() for task in result)
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self, mock_business_goals, mock_db_info):
        """Test handling of invalid JSON from OpenAI"""
        with patch('main.llm') as mock_llm:
            # Mock invalid JSON response
            mock_message = MagicMock()
            mock_message.content = "This is not valid JSON at all!"
            mock_llm.ainvoke = AsyncMock(return_value=mock_message)
            
            result = await generate_task_backlog(
                "I need marketing and sales tasks", 
                mock_business_goals, 
                mock_db_info
            )
            
            # Should return fallback tasks
            assert len(result) > 0
            assert isinstance(result, list)
            # Verify fallback tasks structure
            for task in result:
                assert 'title' in task
                assert 'status' in task
                assert 'priority' in task
                assert 'project' in task
                assert 'notes' in task
    
    @pytest.mark.asyncio 
    async def test_malformed_json_array(self, mock_business_goals, mock_db_info):
        """Test handling of malformed JSON array"""
        with patch('main.llm') as mock_llm:
            # Mock malformed JSON (not an array)
            mock_message = MagicMock()
            mock_message.content = '{"title": "Single task", "status": "To Do"}'  # Object instead of array
            mock_llm.ainvoke = AsyncMock(return_value=mock_message)
            
            result = await generate_task_backlog(
                "create tasks for branding", 
                mock_business_goals, 
                mock_db_info
            )
            
            # Should return fallback tasks
            assert len(result) > 0
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_json_with_markdown_blocks(self, mock_business_goals, mock_db_info):
        """Test handling of JSON wrapped in markdown code blocks"""
        with patch('main.llm') as mock_llm:
            # Mock response with markdown code blocks 
            mock_message = MagicMock()
            mock_message.content = '''```json
[{"title": "Test Task", "status": "To Do", "priority": "High", "project": "Test", "notes": "Test notes"}]
```'''
            mock_llm.ainvoke = AsyncMock(return_value=mock_message)
            
            result = await generate_task_backlog(
                "create test tasks", 
                mock_business_goals, 
                mock_db_info
            )
            
            # Should successfully parse and return the task
            assert len(result) == 1
            assert result[0]['title'] == "Test Task"
            assert result[0]['status'] == "To Do"
    
    @pytest.mark.asyncio
    async def test_incomplete_task_objects(self, mock_business_goals, mock_db_info):
        """Test handling of task objects missing required fields"""
        with patch('main.llm') as mock_llm:
            # Mock response with incomplete task objects
            mock_message = MagicMock()
            mock_message.content = '''[
                {"title": "Complete Task"},
                {"status": "To Do", "priority": "High"},
                {"title": "Another Task", "project": "Marketing"}
            ]'''
            mock_llm.ainvoke = AsyncMock(return_value=mock_message)
            
            result = await generate_task_backlog(
                "create marketing tasks", 
                mock_business_goals, 
                mock_db_info
            )
            
            # Should only include valid tasks with defaults filled in
            valid_tasks = [t for t in result if 'title' in t and t['title'] != 'Untitled Task']
            assert len(valid_tasks) == 2  # Only tasks with titles
            
            # Check defaults are applied
            complete_task = next(t for t in result if t['title'] == "Complete Task")
            assert complete_task['status'] == "To Do"  # Default
            assert complete_task['priority'] == "Medium"  # Default
    
    @pytest.mark.asyncio
    async def test_openai_api_exception(self, mock_business_goals, mock_db_info):
        """Test handling of OpenAI API exceptions"""
        with patch('main.llm') as mock_llm:
            # Mock API exception
            mock_llm.ainvoke.side_effect = Exception("OpenAI API error")
            
            result = await generate_task_backlog(
                "create all business tasks", 
                mock_business_goals, 
                mock_db_info
            )
            
            # Should return fallback tasks
            assert len(result) > 0
            assert isinstance(result, list)
    
    def test_fallback_tasks_creation(self):
        """Test fallback task creation with different user inputs"""
        
        # Test with branding focus
        result = create_fallback_tasks("I need branding and marketing tasks")
        assert len(result) > 0
        branding_tasks = [t for t in result if 'brand' in t['title'].lower()]
        assert len(branding_tasks) > 0
        
        # Test with sales focus  
        result = create_fallback_tasks("help me with sales and revenue")
        assert len(result) > 0
        sales_tasks = [t for t in result if 'sales' in t['project'].lower()]
        assert len(sales_tasks) > 0
        
        # Test with generic input
        result = create_fallback_tasks("help me grow my business")
        assert len(result) > 0
        # Should have default tasks
        assert all(isinstance(task, dict) for task in result)
        assert all('title' in task for task in result)
    
    def test_fallback_task_structure(self):
        """Test that fallback tasks have proper structure"""
        result = create_fallback_tasks("test input")
        
        for task in result:
            # Verify required fields exist
            assert 'title' in task
            assert 'status' in task 
            assert 'priority' in task
            assert 'project' in task
            assert 'notes' in task
            
            # Verify field types and values
            assert isinstance(task['title'], str)
            assert task['status'] in ['To Do', 'In Progress', 'Done']
            assert task['priority'] in ['Low', 'Medium', 'High']
            assert isinstance(task['project'], str)
            assert isinstance(task['notes'], str)


class TestTaskBacklogIntegration:
    """Test the full task backlog request handling"""
    
    @pytest.mark.asyncio
    async def test_handle_task_backlog_request_with_failures(self):
        """Test the full task backlog request handling when OpenAI fails"""
        
        mock_business_goals = {
            'goal1': MagicMock(title='Revenue Goal', description='Increase revenue')
        }
        
        with patch('main.get_notion_db_info') as mock_get_db_info, \
             patch('main.generate_task_backlog') as mock_generate_backlog, \
             patch('main.bulk_create_notion_tasks') as mock_bulk_create:
            
            # Setup mocks
            mock_get_db_info.return_value = NotionDBInfo(properties={'Task': 'title'})
            mock_generate_backlog.return_value = []  # Simulate no tasks generated
            
            # Should not call bulk_create_notion_tasks if no tasks generated
            await handle_task_backlog_request(
                "review my goals and add missing tasks", 
                mock_business_goals, 
                "test_channel"
            )
            
            mock_bulk_create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_task_backlog_request_db_info_failure(self):
        """Test handling when Notion DB info retrieval fails"""
        
        mock_business_goals = {'goal1': MagicMock()}
        
        with patch('main.get_notion_db_info') as mock_get_db_info:
            # Mock DB info retrieval failure
            mock_get_db_info.return_value = NotionDBInfo(properties={})
            
            # Should return early if no DB properties
            await handle_task_backlog_request(
                "create tasks", 
                mock_business_goals, 
                "test_channel"
            )
            
            # Verify it attempted to get DB info
            mock_get_db_info.assert_called_once()


if __name__ == "__main__":
    # Run specific tests
    pytest.main([__file__, "-v"])
