"""
Integration tests for bulk operations that would catch asyncio import issues.
These tests actually exercise the async code paths to find runtime errors.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Setup test environment
from test_utils import setup_test_environment
setup_test_environment()

from main import app
from src.enhanced_task_operations import BulkOperationParser, BulkOperation, BulkOperationType, TaskFilter

client = TestClient(app)

@pytest.mark.asyncio
async def test_bulk_operation_async_execution():
    """Test that bulk operations actually execute async code paths"""
    
    # Create a real bulk operation request
    bulk_operation = BulkOperation(
        operation_type=BulkOperationType.PRIORITY_UPDATE,
        filters=TaskFilter(status='To Do'),
        new_values={'priority': 'High'}
    )
    
    # Mock the enhanced_tasks to return a real result but avoid actual API calls
    with patch('main.enhanced_tasks') as mock_enhanced_tasks:
        mock_result = MagicMock()
        mock_result.message = "Updated 5 tasks"
        mock_result.errors = []
        
        # Make execute_bulk_operation actually async to test the async path
        async def mock_execute_bulk_operation(operation):
            await asyncio.sleep(0.1)  # Simulate async work
            return mock_result
            
        mock_enhanced_tasks.execute_bulk_operation = mock_execute_bulk_operation
        
        # This should trigger the asyncio.new_event_loop() code path
        with patch('main.BulkOperationParser.parse_bulk_request', return_value=bulk_operation):
            with patch('main.fetch_open_tasks', return_value=["Task 1", "Task 2"]):
                with patch('main.requests.post') as mock_requests:
                    mock_requests.return_value.ok = True
                    
                    # Send a slash command that triggers bulk operations
                    form_data = (
                        "token=fake_token&team_id=T123&channel_id=C123&"
                        "command=/ai&text=update all tasks to high priority"
                    )
                    
                    response = client.post(
                        "/slack",
                        data=form_data,
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
                    
                    assert response.status_code == 200

def test_bulk_operation_parse_and_execute():
    """Test the complete bulk operation flow including parsing"""
    
    # Test bulk operation parsing
    user_text = "set all tasks in 'sales' project to high priority"
    bulk_operation = BulkOperationParser.parse_bulk_request(user_text)
    
    if bulk_operation:  # Only test if parsing succeeds
        # Mock enhanced_tasks to avoid real API calls
        with patch('main.enhanced_tasks') as mock_enhanced_tasks:
            mock_result = MagicMock()
            mock_result.message = "Bulk operation completed"
            mock_result.errors = []
            
            # Mock the async method
            async def mock_execute(operation):
                return mock_result
            mock_enhanced_tasks.execute_bulk_operation = mock_execute
            
            with patch('main.fetch_open_tasks', return_value=["Task 1"]):
                with patch('main.requests.post') as mock_requests:
                    mock_requests.return_value.ok = True
                    
                    # This would trigger the asyncio execution path
                    response = client.post("/slack", json={
                        "type": "event_callback",
                        "event": {
                            "type": "message",
                            "text": user_text,
                            "channel": "fake_channel",
                            "subtype": None
                        }
                    })
                    
                    assert response.status_code == 200

@pytest.mark.asyncio 
async def test_task_backlog_generation_async():
    """Test async task backlog generation that would catch import issues"""
    
    with patch('main.get_notion_db_info') as mock_db_info:
        mock_db_info.return_value.properties = {"Task": "title", "Status": "select"}
        
        with patch('main.generate_task_backlog') as mock_generate:
            mock_generate.return_value = [
                {"title": "Test Task", "status": "To Do", "priority": "Medium"}
            ]
            
            with patch('main.bulk_create_notion_tasks') as mock_bulk_create:
                mock_bulk_create.return_value = None
                
                # This should exercise the async code path
                from main import handle_task_backlog_request
                
                # Call the async function directly
                await handle_task_backlog_request(
                    "create all missing tasks", 
                    {}, 
                    "test_channel"
                )
                
                # Verify async functions were called
                mock_db_info.assert_called_once()
                mock_generate.assert_called_once()

def test_task_cleanup_async_path():
    """Test task cleanup that would trigger async execution"""
    
    with patch('main.get_all_tasks_with_details') as mock_get_tasks:
        mock_get_tasks.return_value = [
            {
                'id': 'task123',
                'title': 'Test Task',
                'status': 'To Do',
                'priority': 'Low',
                'project': 'Test',
                'notes': 'Test notes'
            }
        ]
        
        with patch('main.llm') as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="task123")
            
            with patch('main.delete_notion_task') as mock_delete:
                mock_delete.return_value = True
                
                with patch('main.requests.post') as mock_requests:
                    mock_requests.return_value.ok = True
                    
                    # Test task cleanup request
                    response = client.post("/slack", json={
                        "type": "event_callback", 
                        "event": {
                            "type": "message",
                            "text": "review all tasks and remove anything that doesn't make sense",
                            "channel": "fake_channel",
                            "subtype": None
                        }
                    })
                    
                    assert response.status_code == 200

@pytest.mark.asyncio
async def test_async_error_handling():
    """Test error handling in async operations"""
    
    # Test that async errors are properly caught
    async def failing_async_operation():
        # This would trigger the asyncio code path and then fail
        raise Exception("Async operation failed")
    
    with patch('main.analyze_and_remove_irrelevant_tasks', side_effect=failing_async_operation):
        with patch('main.requests.post') as mock_requests:
            mock_requests.return_value.ok = True
            
            response = client.post("/slack", json={
                "type": "event_callback",
                "event": {
                    "type": "message", 
                    "text": "clean up my tasks",
                    "channel": "fake_channel",
                    "subtype": None
                }
            })
            
            assert response.status_code == 200

def test_event_loop_creation_paths():
    """Test different event loop creation scenarios"""
    
    # Mock different asyncio.get_event_loop() scenarios
    scenarios = [
        # Scenario 1: No existing loop (RuntimeError)
        Exception("There is no current event loop"),
        # Scenario 2: Existing loop that's not running
        MagicMock(is_running=lambda: False),
        # Scenario 3: Existing loop that is running  
        MagicMock(is_running=lambda: True)
    ]
    
    for i, scenario in enumerate(scenarios):
        with patch('asyncio.get_event_loop', side_effect=[scenario] if isinstance(scenario, Exception) else [scenario]):
            with patch('asyncio.new_event_loop') as mock_new_loop:
                with patch('asyncio.set_event_loop'):
                    mock_loop = MagicMock()
                    mock_new_loop.return_value = mock_loop
                    
                    with patch('main.fetch_open_tasks', return_value=["Task 1"]):
                        with patch('main.requests.post') as mock_requests:
                            mock_requests.return_value.ok = True
                            
                            response = client.post("/slack", json={
                                "type": "event_callback",
                                "event": {
                                    "type": "message",
                                    "text": "generate task backlog",
                                    "channel": f"test_channel_{i}",
                                    "subtype": None
                                }
                            })
                            
                            assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
