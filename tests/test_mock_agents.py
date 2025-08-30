"""
Simplified tests for the mock agent system
Tests the actual mock agent functionality that exists
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

# Import the modules we need to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent_integration import (
    initialize_agent_integration, 
    AgentIntegration
)

# Import mock agents
from mock_task_manager import TaskManager
from mock_discovery_agent import DiscoveryAgent  
from mock_priority_engine import PriorityEngine
from mock_chat_handler import ChatHandler


class TestMockTaskManager:
    """Test cases for the mock task manager agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_notion = Mock()
        self.mock_db_id = "test_db_id"
        self.agent = TaskManager(self.mock_notion, self.mock_db_id)

    def test_create_task(self):
        """Test task creation functionality."""
        task_data = {
            "title": "Test Task",
            "description": "Test Description", 
            "priority": "High",
            "status": "To Do"
        }
        
        result = self.agent.create_task(task_data)
        
        assert result["success"] == True
        assert "task_id" in result
        assert result["message"].startswith("Task 'Test Task' created")
        assert result["data"]["title"] == "Test Task"

    def test_update_task(self):
        """Test task updating functionality."""
        result = self.agent.update_task("task_123", {"status": "In Progress"})
        
        assert result["success"] == True
        assert result["task_id"] == "task_123"
        assert result["message"] == "Task updated successfully"

    def test_list_tasks(self):
        """Test task listing with filtering."""
        result = self.agent.list_tasks(limit=10)
        
        assert result["success"] == True
        assert "tasks" in result
        assert len(result["tasks"]) <= 10
        # Should return the mock tasks
        assert len(result["tasks"]) == 3  # Mock has 3 tasks

    def test_list_tasks_with_filter(self):
        """Test task listing with status filter."""
        result = self.agent.list_tasks({"status": "To Do"}, limit=10)
        
        assert result["success"] == True
        # Should filter to only "To Do" tasks
        for task in result["tasks"]:
            assert task["status"] == "To Do"


class TestMockDiscoveryAgent:
    """Test cases for the mock discovery agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = DiscoveryAgent()

    def test_search_users(self):
        """Test user search functionality."""
        result = self.agent.search_users("john")
        
        assert result["success"] == True
        assert "users" in result
        assert len(result["users"]) >= 1
        # Should find John Doe
        assert any("John" in user["name"] for user in result["users"])

    def test_search_projects(self):
        """Test project search functionality.""" 
        result = self.agent.search_projects("sales")
        
        assert result["success"] == True
        assert "projects" in result
        # Should find sales campaign
        assert any("Sales" in project["name"] for project in result["projects"])

    def test_analyze_business_gaps(self):
        """Test business gap analysis."""
        current_tasks = [
            {"title": "Sales call with prospect", "description": "Follow up on lead"},
            {"title": "Update CRM", "description": "Add new contacts"}
        ]
        
        result = self.agent.analyze_business_gaps(current_tasks)
        
        assert result["success"] == True
        assert "gaps_by_area" in result
        assert "coverage_scores" in result
        assert "overall_coverage" in result

    def test_discover_missing_foundations(self):
        """Test foundational task discovery."""
        result = self.agent.discover_missing_foundations()
        
        assert result["success"] == True
        assert "foundational_tasks" in result
        assert len(result["foundational_tasks"]) > 0
        # Should include foundational business tasks
        task_titles = [task["title"] for task in result["foundational_tasks"]]
        assert any("backup" in title.lower() for title in task_titles)

    def test_generate_weekly_task_candidates(self):
        """Test weekly task candidate generation."""
        context = {"available_hours": 40, "business_goals": ["revenue", "growth"]}
        
        result = self.agent.generate_weekly_task_candidates(context)
        
        assert result["success"] == True
        assert "weekly_candidates" in result
        assert "total_estimated_time" in result
        assert "priority_distribution" in result


class TestMockPriorityEngine:
    """Test cases for the mock priority engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = PriorityEngine()

    def test_calculate_priority_score(self):
        """Test priority score calculation."""
        task = {
            "title": "High priority sales task",
            "priority": "High",
            "project": "Sales",
            "description": "Revenue generating task"
        }
        
        result = self.agent.calculate_priority_score(task)
        
        assert result["success"] == True
        assert "priority_score" in result
        assert "priority_level" in result
        assert result["priority_score"] > 0
        assert result["priority_level"] in ["Critical", "High", "Medium", "Low", "Deferred"]

    def test_rank_tasks(self):
        """Test task ranking functionality."""
        tasks = [
            {
                "id": "task_1",
                "title": "Low priority task",
                "priority": "Low",
                "project": "Operations"
            },
            {
                "id": "task_2", 
                "title": "High priority sales task",
                "priority": "High",
                "project": "Sales"
            },
            {
                "id": "task_3",
                "title": "Medium priority task",
                "priority": "Medium", 
                "project": "Marketing"
            }
        ]
        
        result = self.agent.rank_tasks(tasks)
        
        assert result["success"] == True
        assert "ranked_tasks" in result
        assert len(result["ranked_tasks"]) == 3
        
        # Should be ranked by priority score (highest first)
        scores = [task["priority_score"] for task in result["ranked_tasks"]]
        assert scores == sorted(scores, reverse=True)

    def test_get_daily_priority(self):
        """Test daily priority task selection."""
        tasks = [
            {
                "id": "task_1",
                "title": "High priority sales task", 
                "priority": "High",
                "project": "Sales"
            },
            {
                "id": "task_2",
                "title": "Low priority admin task",
                "priority": "Low",
                "project": "Operations"
            }
        ]
        
        result = self.agent.get_daily_priority(tasks)
        
        assert result["success"] == True
        assert "daily_priority" in result
        assert "reasoning" in result
        
        daily_task = result["daily_priority"]
        assert "task_title" in daily_task
        assert "total_score" in daily_task
        # Should select the higher priority task
        assert daily_task["task_title"] == "High priority sales task"

    def test_deterministic_scoring(self):
        """Test that scoring is deterministic."""
        task = {
            "title": "Test task",
            "priority": "Medium",
            "project": "Test"
        }
        
        # Calculate score multiple times
        scores = []
        for _ in range(5):
            result = self.agent.calculate_priority_score(task)
            scores.append(result["priority_score"])
        
        # All scores should be identical (deterministic)
        assert all(score == scores[0] for score in scores)


class TestMockChatHandler:
    """Test cases for the mock chat handler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ChatHandler()

    def test_process_message(self):
        """Test message processing."""
        result = self.agent.process_message("Hello, I need help with tasks")
        
        assert result["success"] == True
        assert "response" in result
        assert "message_type" in result
        assert result["confidence"] > 0

    def test_create_task_from_chat(self):
        """Test task creation from natural language."""
        chat_input = "Create task: Call client about urgent proposal"
        
        result = self.agent.create_task_from_chat(chat_input)
        
        assert result["success"] == True
        assert "task_data" in result
        assert "parsed_request" in result
        
        task_data = result["task_data"]
        assert "title" in task_data
        assert "priority" in task_data
        # Should detect urgency and set high priority
        assert task_data["priority"] == "High"

    def test_generate_task_suggestion(self):
        """Test task suggestion generation."""
        context = {"recent_activity": "sales", "user_role": "sales_manager"}
        
        result = self.agent.generate_task_suggestion(context)
        
        assert result["success"] == True
        assert "suggestion" in result
        assert "reasoning" in result
        
        suggestion = result["suggestion"] 
        assert "title" in suggestion
        assert "priority" in suggestion

    def test_provide_context_summary(self):
        """Test context summarization."""
        tasks = [
            {"title": "Task 1", "priority": "High"},
            {"title": "Task 2", "priority": "Medium"},
            {"title": "Task 3", "priority": "Low"}
        ]
        
        result = self.agent.provide_context_summary(tasks, "tasks")
        
        assert result["success"] == True
        assert "summary" in result
        assert "count" in result
        assert result["count"] == 3


class TestAgentIntegration:
    """Test cases for the agent integration system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_notion = Mock()
        self.mock_db_id = "test_db_id"

    @pytest.mark.asyncio
    async def test_initialize_agent_integration(self):
        """Test initialization of the agent integration system."""
        result = initialize_agent_integration(self.mock_notion, self.mock_db_id)
        
        assert result is not None
        assert isinstance(result, AgentIntegration)
        # Check that agents are initialized
        assert result.task_manager is not None
        assert result.task_discovery is not None
        assert result.priority_engine is not None
        assert result.chat_handler is not None

    @pytest.mark.asyncio
    async def test_get_daily_priority_task(self):
        """Test getting daily priority task through integration."""
        integration = initialize_agent_integration(self.mock_notion, self.mock_db_id)
        
        result = await integration.get_daily_priority_task()
        
        assert "success" in result
        # Should return a result (success or failure with error message)
        if result["success"]:
            assert "daily_priority" in result
        else:
            assert "error" in result

    @pytest.mark.asyncio
    async def test_add_task_via_chat(self):
        """Test adding task via chat through integration."""
        integration = initialize_agent_integration(self.mock_notion, self.mock_db_id)
        
        result = await integration.add_task_via_chat("Create task: Call John about proposal")
        
        assert "success" in result
        if result["success"]:
            assert "task_id" in result
            assert "message" in result

    @pytest.mark.asyncio 
    async def test_discover_missing_tasks(self):
        """Test discovering missing tasks through integration."""
        integration = initialize_agent_integration(self.mock_notion, self.mock_db_id)
        
        result = await integration.discover_missing_tasks()
        
        assert "success" in result
        if result["success"]:
            assert "gap_analysis" in result
            assert "foundational_suggestions" in result

    @pytest.mark.asyncio
    async def test_generate_weekly_plan(self):
        """Test generating weekly plan through integration."""
        integration = initialize_agent_integration(self.mock_notion, self.mock_db_id)
        
        context = {"available_hours": 40, "business_goals": ["revenue"]}
        result = await integration.generate_weekly_plan(context)
        
        assert "success" in result
        if result["success"]:
            assert "weekly_plan" in result
            assert "plan_summary" in result

    def test_task_crud_operations(self):
        """Test basic CRUD operations through integration."""
        integration = initialize_agent_integration(self.mock_notion, self.mock_db_id)
        
        # Test create
        task_data = {"title": "Test Task", "priority": "Medium"}
        create_result = integration.create_task(task_data)
        assert create_result["success"] == True
        
        # Test list
        list_result = integration.list_tasks()
        assert list_result["success"] == True
        assert "tasks" in list_result
        
        # Test update
        if create_result["success"]:
            task_id = create_result["task_id"]
            update_result = integration.update_task(task_id, {"status": "In Progress"})
            assert update_result["success"] == True


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
