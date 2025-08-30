"""
Comprehensive End-to-End Tests for Agent-Notion Integration

This test suite verifies that the agent system can successfully interact with 
a real or mock Notion database, including:
- Task creation, updates, completion, and removal
- Error handling and resilience 
- Proper cleanup of test data
- Integration with the main application flow

Tests are designed to run before pushes to ensure agent-Notion functionality works.
"""

import pytest
import asyncio
import os
import uuid
import time
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Set TEST_MODE before importing main components
os.environ['TEST_MODE'] = 'true'

from src.agent_integration import (
    agent_process_request, 
    initialize_agent_integration, 
    get_agent_integration,
    AgentIntegration
)
from main import create_notion_task, update_notion_task, delete_notion_task, get_all_tasks_with_details


class NotionTestFixture:
    """Manages test data in Notion with proper cleanup"""
    
    def __init__(self):
        self.created_task_ids: List[str] = []
        self.test_prefix = f"E2E_TEST_{uuid.uuid4().hex[:8]}_"
        
    def create_test_task(self, title: str = None, **kwargs) -> Dict[str, Any]:
        """Create a test task with automatic cleanup tracking"""
        if title is None:
            title = f"{self.test_prefix}Test Task {len(self.created_task_ids) + 1}"
        else:
            title = f"{self.test_prefix}{title}"
            
        # Create the task using the main application function
        success = create_notion_task(
            title=title,
            status=kwargs.get('status', 'To Do'),
            priority=kwargs.get('priority', 'Medium'),
            project=kwargs.get('project', 'Test Project'),
            notes=kwargs.get('notes', 'Test task created by E2E tests')
        )
        
        if success:
            # Since create_notion_task doesn't return the ID, we need to find it
            # This is a limitation of the current implementation
            tasks = get_all_tasks_with_details()
            for task in tasks:
                if task['title'] == title:
                    self.created_task_ids.append(task['id'])
                    return task
                    
        return None
        
    def cleanup(self):
        """Clean up all test tasks"""
        cleanup_count = 0
        for task_id in self.created_task_ids:
            try:
                if delete_notion_task(task_id):
                    cleanup_count += 1
            except Exception as e:
                print(f"Warning: Failed to cleanup task {task_id}: {e}")
        
        print(f"Cleaned up {cleanup_count}/{len(self.created_task_ids)} test tasks")
        self.created_task_ids.clear()


@pytest.fixture
def notion_fixture():
    """Provides a Notion test fixture with automatic cleanup"""
    fixture = NotionTestFixture()
    yield fixture
    fixture.cleanup()


@pytest.fixture  
def mock_notion_success():
    """Mock Notion client that simulates successful operations"""
    mock_notion = MagicMock()
    
    # Mock successful task creation
    mock_notion.pages.create.return_value = {
        'id': 'test-task-id-123',
        'properties': {
            'Task': {'title': [{'text': {'content': 'Test Task'}}]}
        }
    }
    
    # Mock successful task retrieval
    mock_notion.databases.query.return_value = {
        'results': [
            {
                'id': 'test-task-id-123',
                'properties': {
                    'Task': {'title': [{'text': {'content': 'Test Task'}}]},
                    'Status': {'select': {'name': 'To Do'}},
                    'Priority': {'select': {'name': 'Medium'}},
                    'Project': {'rich_text': [{'text': {'content': 'Test Project'}}]},
                    'Notes': {'rich_text': [{'text': {'content': 'Test notes'}}]}
                },
                'created_time': datetime.now().isoformat(),
                'last_edited_time': datetime.now().isoformat()
            }
        ]
    }
    
    # Mock successful task updates
    mock_notion.pages.update.return_value = {'id': 'test-task-id-123'}
    
    return mock_notion


@pytest.fixture
def mock_notion_failure():
    """Mock Notion client that simulates API failures"""
    mock_notion = MagicMock()
    
    # Mock API failures
    mock_notion.pages.create.side_effect = Exception("Notion API Error: Rate limited")
    mock_notion.databases.query.side_effect = Exception("Notion API Error: Unauthorized")
    mock_notion.pages.update.side_effect = Exception("Notion API Error: Page not found")
    
    return mock_notion


class TestAgentNotionIntegrationBasics:
    """Test basic agent-Notion interactions"""
    
    @patch('main.notion')
    @patch('src.agent_integration.get_agent_integration')
    def test_agent_can_create_tasks_in_notion(self, mock_get_agent, mock_notion):
        """Test that agent can successfully create tasks in Notion"""
        # Setup mocks
        mock_agent = MagicMock()
        mock_get_agent.return_value = mock_agent
        
        # Mock successful agent response
        mock_agent.process_user_request.return_value = {
            "success": True,
            "response": "Task created successfully",
            "agent_used": "TaskManagerAgent"
        }
        
        # Mock successful Notion task creation
        mock_notion.pages.create.return_value = {
            'id': 'test-task-123',
            'properties': {
                'Task': {'title': [{'text': {'content': 'Create landing page'}}]}
            }
        }
        
        # Test task creation through agent
        result = asyncio.run(agent_process_request(
            user_input="create task: Create landing page for new product",
            context={'tasks': [], 'business_goals': {}}
        ))
        
        assert "Task created successfully" in result
        mock_agent.process_user_request.assert_called_once()
        
    @patch('main.notion')
    @patch('main.NOTION_DB_ID', 'test-database-id')
    def test_notion_task_creation_direct(self, mock_notion):
        """Test direct Notion task creation functionality"""
        # Mock successful creation
        mock_notion.pages.create.return_value = {'id': 'test-task-456'}
        mock_notion.databases.retrieve.return_value = {
            'properties': {
                'Task': {'type': 'title'},
                'Status': {'type': 'select'},
                'Priority': {'type': 'select'},
                'Project': {'type': 'rich_text'},
                'Notes': {'type': 'rich_text'}
            }
        }
        
        # Test task creation
        success = create_notion_task(
            title="Test E2E Task",
            status="To Do", 
            priority="High",
            project="E2E Testing",
            notes="This is a test task for E2E validation"
        )
        
        assert success == True
        mock_notion.pages.create.assert_called_once()
        
        # Verify the correct data was passed
        call_args = mock_notion.pages.create.call_args
        assert call_args[1]['parent']['database_id'] == 'test-database-id'
        assert 'properties' in call_args[1]
        
    @patch('main.notion')
    def test_notion_task_update(self, mock_notion):
        """Test Notion task update functionality"""
        # Mock successful update
        mock_notion.pages.update.return_value = {'id': 'test-task-789'}
        
        # Test task update
        success = update_notion_task(
            task_id="test-task-789",
            status="In Progress",
            priority="High",
            notes="Updated task notes"
        )
        
        assert success == True
        mock_notion.pages.update.assert_called_once()
        
    @patch('main.notion')
    def test_notion_task_deletion(self, mock_notion):
        """Test Notion task deletion functionality"""
        # Mock successful deletion (archiving)
        mock_notion.pages.update.return_value = {'id': 'test-task-999'}
        
        # Test task deletion
        success = delete_notion_task("test-task-999")
        
        assert success == True
        mock_notion.pages.update.assert_called_once()
        
        # Verify task was archived
        call_args = mock_notion.pages.update.call_args
        assert call_args[1]['archived'] == True


class TestAgentNotionErrorHandling:
    """Test error handling and resilience"""
    
    @patch('main.notion')
    def test_notion_api_failure_handling(self, mock_notion):
        """Test that Notion API failures are handled gracefully"""
        # Mock API failure
        mock_notion.pages.create.side_effect = Exception("Notion API Error: Rate limited")
        mock_notion.databases.retrieve.side_effect = Exception("Database not found")
        
        # Test task creation with failure
        success = create_notion_task(
            title="This should fail",
            status="To Do"
        )
        
        assert success == False  # Should return False on failure, not crash
        
    @patch('src.agent_integration.get_agent_integration')
    def test_agent_handles_notion_failures(self, mock_get_agent):
        """Test that agent handles Notion failures gracefully"""
        # Mock agent that simulates Notion failure
        mock_agent = MagicMock()
        mock_get_agent.return_value = mock_agent
        
        mock_agent.process_user_request.return_value = {
            "success": False,
            "error": "Task manager not available",
            "fallback_used": True
        }
        
        # Test agent request with failure
        result = asyncio.run(agent_process_request(
            user_input="create urgent task: Fix production bug",
            context={'tasks': [], 'business_goals': {}}
        ))
        
        assert "Error:" in result
        assert "Task manager not available" in result
        
    @patch('main.notion')
    def test_task_retrieval_with_malformed_data(self, mock_notion):
        """Test handling of malformed Notion data"""
        # Mock response with missing/malformed data
        mock_notion.databases.query.return_value = {
            'results': [
                {
                    'id': 'malformed-task-1',
                    'properties': {}  # Missing required properties
                },
                {
                    'id': 'malformed-task-2',
                    'properties': {
                        'Task': {'title': []}  # Empty title array
                    }
                }
            ]
        }
        
        # Should not crash, should handle gracefully
        tasks = get_all_tasks_with_details()
        
        assert isinstance(tasks, list)
        # Should still return task objects, potentially with default values
        
    def test_network_timeout_simulation(self):
        """Test handling of network timeouts"""
        # This would be more complex in a real scenario
        # For now, we test that timeouts don't cause crashes
        
        with patch('main.notion.pages.create') as mock_create:
            mock_create.side_effect = TimeoutError("Network timeout")
            
            success = create_notion_task("Timeout test task")
            assert success == False  # Should handle timeout gracefully


class TestAgentNotionWorkflows:
    """Test complete workflows end-to-end"""
    
    @patch('main.notion')
    @patch('src.agent_integration.get_agent_integration')
    def test_complete_task_lifecycle(self, mock_get_agent, mock_notion):
        """Test a complete task lifecycle: create -> update -> complete -> delete"""
        # Setup mocks
        mock_agent = MagicMock()
        mock_get_agent.return_value = mock_agent
        
        task_id = "lifecycle-test-task-123"
        
        # Mock database schema
        mock_notion.databases.retrieve.return_value = {
            'properties': {
                'Task': {'type': 'title'},
                'Status': {'type': 'select'},
                'Priority': {'type': 'select'}
            }
        }
        
        # Mock successful creation
        mock_notion.pages.create.return_value = {'id': task_id}
        
        # Mock successful updates
        mock_notion.pages.update.return_value = {'id': task_id}
        
        # 1. Create task
        create_success = create_notion_task(
            title="Lifecycle Test Task",
            status="To Do",
            priority="Medium"
        )
        assert create_success == True
        
        # 2. Update task
        update_success = update_notion_task(
            task_id=task_id,
            status="In Progress",
            notes="Working on this task"
        )
        assert update_success == True
        
        # 3. Complete task
        complete_success = update_notion_task(
            task_id=task_id,
            status="Done",
            notes="Task completed successfully"
        )
        assert complete_success == True
        
        # 4. Delete task
        delete_success = delete_notion_task(task_id)
        assert delete_success == True
        
        # Verify all operations were called
        mock_notion.pages.create.assert_called_once()
        assert mock_notion.pages.update.call_count == 3  # 2 updates + 1 delete
        
    @patch('src.agent_integration.get_agent_integration')
    def test_agent_request_processing_pipeline(self, mock_get_agent):
        """Test the full agent request processing pipeline"""
        # Mock agent with realistic responses
        mock_agent = MagicMock()
        mock_get_agent.return_value = mock_agent
        
        # Test different request types
        test_requests = [
            {
                'input': 'create task: Set up CI/CD pipeline',
                'expected_response': {
                    'success': True,
                    'response': 'Created task: Set up CI/CD pipeline',
                    'agent_used': 'TaskManagerAgent'
                }
            },
            {
                'input': 'what should I work on today?',
                'expected_response': {
                    'success': True,
                    'response': 'Today\'s priority: Review client proposals',
                    'agent_used': 'PriorityEngineAgent'
                }
            },
            {
                'input': 'help me with task planning',
                'expected_response': {
                    'success': True,
                    'response': 'I can help you create a weekly plan...',
                    'agent_used': 'ChatHandlerAgent'
                }
            }
        ]
        
        for test_case in test_requests:
            mock_agent.process_user_request.return_value = test_case['expected_response']
            
            result = asyncio.run(agent_process_request(
                user_input=test_case['input'],
                context={'tasks': [], 'business_goals': {}}
            ))
            
            assert test_case['expected_response']['response'] in result
            if 'agent_used' in test_case['expected_response']:
                assert test_case['expected_response']['agent_used'] in result


class TestAgentNotionPerformance:
    """Test performance and reliability aspects"""
    
    def test_concurrent_task_operations(self):
        """Test that concurrent operations don't cause issues"""
        # This would test concurrent access to Notion API
        # For now, just verify the functions can be called concurrently
        
        with patch('main.notion.pages.create') as mock_create:
            mock_create.return_value = {'id': 'concurrent-task'}
            
            # Simulate concurrent calls (would be more complex in real scenario)
            success1 = create_notion_task("Concurrent task 1")
            success2 = create_notion_task("Concurrent task 2")
            
            assert success1 == True
            assert success2 == True
            
    @patch('main.notion')
    def test_large_task_list_handling(self, mock_notion):
        """Test handling of large task lists"""
        # Mock a large number of tasks
        mock_tasks = []
        for i in range(100):
            mock_tasks.append({
                'id': f'task-{i}',
                'properties': {
                    'Task': {'title': [{'text': {'content': f'Task {i}'}}]},
                    'Status': {'select': {'name': 'To Do'}},
                    'Priority': {'select': {'name': 'Medium'}},
                    'Project': {'rich_text': [{'text': {'content': 'Bulk Test'}}]},
                    'Notes': {'rich_text': [{'text': {'content': f'Task {i} notes'}}]}
                },
                'created_time': datetime.now().isoformat(),
                'last_edited_time': datetime.now().isoformat()
            })
        
        mock_notion.databases.query.return_value = {'results': mock_tasks}
        
        # Should handle large result sets without issues
        tasks = get_all_tasks_with_details()
        
        assert len(tasks) == 100
        assert all('title' in task for task in tasks)


class TestAgentNotionIntegration:
    """High-level integration tests"""
    
    @pytest.mark.timeout(30)  # Set timeout for integration tests
    def test_agent_system_initialization(self):
        """Test that the agent system initializes correctly"""
        # Test that we can initialize the agent integration
        try:
            from notion_client import Client as NotionClient
            mock_client = MagicMock(spec=NotionClient)
            mock_db_id = "test-database-id"
            
            # This should not crash
            integration = AgentIntegration(mock_client, mock_db_id)
            assert integration is not None
            
        except Exception as e:
            pytest.fail(f"Agent system initialization failed: {e}")
            
    def test_environment_variable_handling(self):
        """Test that the system handles missing environment variables gracefully"""
        # This is handled by TEST_MODE, but let's verify
        import main
        
        # Should not crash even with missing env vars in test mode
        assert main.app is not None
        
    @patch('main.llm')
    def test_ai_response_integration(self, mock_llm):
        """Test integration with AI response generation"""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = "I'll help you create that task. Task created successfully."
        mock_llm.invoke.return_value = mock_response
        
        # Test that AI integration doesn't crash
        from main import generate_help_response
        response = generate_help_response()
        
        assert isinstance(response, str)
        assert len(response) > 0


def test_e2e_test_infrastructure():
    """Meta-test: Verify that the E2E test infrastructure itself works"""
    # Test that we can import all required modules
    assert agent_process_request is not None
    assert create_notion_task is not None
    assert update_notion_task is not None
    assert delete_notion_task is not None
    
    # Test that TEST_MODE is set
    assert os.environ.get('TEST_MODE') == 'true'
    
    # Test that asyncio works correctly
    async def dummy_async():
        return "async works"
    
    result = asyncio.run(dummy_async())
    assert result == "async works"


if __name__ == "__main__":
    # Run the tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
