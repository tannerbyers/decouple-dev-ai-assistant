#!/usr/bin/env python3

"""
CEO Operator System Tests

Tests for Business Brain, Task Matrix, Priority Engine, TaskCandidate scoring,
Weekly Runbook functions, and integrated CEO-level strategic operations.
"""

import os
import sys
import tempfile
import json
import yaml
import datetime
from unittest.mock import patch, mock_open, MagicMock
from dataclasses import asdict

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the components we're testing
from main import (
    load_business_brain, load_task_matrix, TaskCandidate, 
    generate_weekly_candidates, perform_gap_check, generate_ceo_weekly_plan,
    generate_midweek_nudge, generate_friday_retro, create_trello_card_json,
    get_discovery_call_script, business_brain, task_matrix
)

class TestBusinessBrainLoading:
    """Test Business Brain YAML loading and configuration."""
    
    def test_load_business_brain_success(self):
        """Test successful loading of business brain YAML."""
        mock_yaml_content = {
            'company': {
                'name': 'Decouple Dev',
                'positioning': 'Async dev agency'
            },
            'goals': {
                'north_star': 'Hit $30k/mo revenue'
            },
            'policy': {
                'priority_order': ['RevenueNow', 'Retention', 'Systems', 'Brand']
            }
        }
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(mock_yaml_content))):
            result = load_business_brain()
            
            assert result['company']['name'] == 'Decouple Dev'
            assert result['goals']['north_star'] == 'Hit $30k/mo revenue'
            assert 'RevenueNow' in result['policy']['priority_order']
    
    def test_load_business_brain_file_not_found(self):
        """Test business brain loading when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            result = load_business_brain()
            
            # Should return default configuration
            assert result['company']['name'] == 'Decouple Dev'
            assert result['goals']['north_star'] == 'Hit $30k/mo revenue'
            assert result['policy']['priority_order'] == ['RevenueNow', 'Retention', 'Systems', 'Brand']
    
    def test_load_business_brain_yaml_error(self):
        """Test business brain loading with invalid YAML."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="invalid: yaml: content: [")), \
             patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML")):
            result = load_business_brain()
            
            # Should return empty dict on error
            assert result == {}


class TestTaskMatrixLoading:
    """Test Task Matrix YAML loading and configuration."""
    
    def test_load_task_matrix_success(self):
        """Test successful loading of task matrix YAML."""
        mock_yaml_content = {
            'marketing': ['Define ICP/pain bullets', 'Content creation'],
            'sales': ['Outbound outreach', 'Discovery calls'],
            'delivery': ['Process documentation', 'Quality assurance'],
            'ops': ['Weekly reviews', 'System maintenance']
        }
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(mock_yaml_content))):
            result = load_task_matrix()
            
            assert len(result) == 4
            assert result['marketing'][0] == 'Define ICP/pain bullets'
            assert result['sales'][1] == 'Discovery calls'
            assert result['delivery'][0] == 'Process documentation'
            assert result['ops'][1] == 'System maintenance'
    
    def test_load_task_matrix_file_not_found(self):
        """Test task matrix loading when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            result = load_task_matrix()
            
            # Should return default task matrix
            assert 'marketing' in result
            assert 'sales' in result
            assert 'delivery' in result
            assert 'ops' in result
    
    def test_load_task_matrix_yaml_error(self):
        """Test task matrix loading with invalid YAML."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="invalid: yaml")), \
             patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML")):
            result = load_task_matrix()
            
            # Should return empty dict on error
            assert result == {}


class TestTaskCandidate:
    """Test TaskCandidate dataclass and priority scoring."""
    
    def test_task_candidate_creation(self):
        """Test creating a TaskCandidate instance."""
        candidate = TaskCandidate(
            title="[Sales] Close 3 new deals",
            description="Focus on warm leads and follow up with proposals",
            area="Sales",
            role="CSO",
            revenue_impact=5,
            time_to_impact=4,
            effort=2,
            strategic_compounding=1,
            fit_to_constraints=2,
            due_date="2025-01-15",
            owner="Me",
            estimate="M",
            acceptance_criteria="Complete 3 signed contracts"
        )
        
        assert candidate.title == "[Sales] Close 3 new deals"
        assert candidate.area == "Sales"
        assert candidate.role == "CSO"
        assert candidate.revenue_impact == 5
    
    def test_priority_score_calculation(self):
        """Test priority score calculation using the Priority Engine formula."""
        candidate = TaskCandidate(
            title="High Priority Task",
            description="Test task",
            area="Sales",
            role="CSO",
            revenue_impact=5,  # 2 * 5 = 10
            time_to_impact=4,  # 1.5 * 4 = 6
            effort=2,          # 1 * (5-2) = 3
            strategic_compounding=3,  # 1 * 3 = 3
            fit_to_constraints=2,     # 1 * 2 = 2
            due_date="2025-01-15",
            owner="Me",
            estimate="L",
            acceptance_criteria="Complete task"
        )
        
        # Expected: (2*5) + (1.5*4) + (1*3) + (1*3) + (1*2) = 10 + 6 + 3 + 3 + 2 = 24
        expected_score = 24.0
        assert candidate.priority_score == expected_score
    
    def test_priority_score_edge_cases(self):
        """Test priority score calculation with edge cases."""
        # Test with effort = 0 (should use 5 as effort_inverse)
        candidate_zero_effort = TaskCandidate(
            title="Zero Effort Task",
            description="Test task",
            area="Marketing",
            role="CMO",
            revenue_impact=3,
            time_to_impact=2,
            effort=0,  # Should result in effort_inverse = 5
            strategic_compounding=1,
            fit_to_constraints=1,
            due_date="2025-01-15",
            owner="Me",
            estimate="S",
            acceptance_criteria="Complete task"
        )
        
        # Expected: (2*3) + (1.5*2) + (1*5) + (1*1) + (1*1) = 6 + 3 + 5 + 1 + 1 = 16
        expected_score = 16.0
        assert candidate_zero_effort.priority_score == expected_score
        
        # Test with maximum values
        max_candidate = TaskCandidate(
            title="Max Priority Task",
            description="Test task",
            area="Sales",
            role="CSO",
            revenue_impact=5,
            time_to_impact=5,
            effort=0,  # Lowest effort = highest score
            strategic_compounding=3,
            fit_to_constraints=2,
            due_date="2025-01-15",
            owner="Me",
            estimate="L",
            acceptance_criteria="Complete task"
        )
        
        # Expected: (2*5) + (1.5*5) + (1*5) + (1*3) + (1*2) = 10 + 7.5 + 5 + 3 + 2 = 27.5
        expected_max_score = 27.5
        assert max_candidate.priority_score == expected_max_score


class TestGapCheck:
    """Test gap analysis functionality."""
    
    def test_perform_gap_check_with_gaps(self):
        """Test gap check identifying missing tasks."""
        # Mock task matrix directly in the function call
        mock_task_matrix = {
            'marketing': ['Define ICP/pain bullets', 'Content creation'],
            'sales': ['Outbound outreach', 'Discovery calls']
        }
        
        # Mock current tasks that don't match the required tasks
        mock_current_tasks = ['Some unrelated task', 'Another random task']
        
        with patch('main.fetch_open_tasks', return_value=mock_current_tasks), \
             patch('main.task_matrix', mock_task_matrix):
            gaps = perform_gap_check()
            
            # Should identify all tasks as missing
            assert len(gaps) == 4
            assert '[Marketing] Define ICP/pain bullets' in gaps
            assert '[Marketing] Content creation' in gaps
            assert '[Sales] Outbound outreach' in gaps
            assert '[Sales] Discovery calls' in gaps
    
    def test_perform_gap_check_no_gaps(self):
        """Test gap check with no missing tasks."""
        # Mock task matrix directly
        mock_task_matrix = {
            'marketing': ['Define ICP'],
            'sales': ['Discovery calls']
        }
        
        # Mock current tasks that match the required tasks
        mock_current_tasks = ['define icp strategy document', 'schedule discovery calls for leads']
        
        with patch('main.fetch_open_tasks', return_value=mock_current_tasks), \
             patch('main.task_matrix', mock_task_matrix):
            gaps = perform_gap_check()
            
            # Should find no gaps since keywords match
            assert len(gaps) == 0
    
    def test_perform_gap_check_partial_matches(self):
        """Test gap check with partial keyword matches."""
        # Mock task matrix directly
        mock_task_matrix = {
            'marketing': ['Content creation strategy', 'Social media posts'],
            'sales': ['Outbound email campaign']
        }
        
        # Mock current tasks with partial matches
        mock_current_tasks = ['content creation for blog', 'some other task']
        
        with patch('main.fetch_open_tasks', return_value=mock_current_tasks), \
             patch('main.task_matrix', mock_task_matrix):
            gaps = perform_gap_check()
            
            # Should identify missing tasks (Content creation and social media and outbound campaign)
            # "Content creation" matches "content creation for blog" but "social media" and "outbound" don't
            assert len(gaps) >= 2  # At least social media and outbound
            assert '[Marketing] Social media posts' in gaps
            assert '[Sales] Outbound email campaign' in gaps


class TestWeeklyCandidateGeneration:
    """Test weekly candidate task generation."""
    
    def test_generate_weekly_candidates(self):
        """Test generating weekly candidate tasks."""
        # Mock task matrix directly
        mock_task_matrix = {
            'marketing': ['Task 1', 'Task 2', 'Task 3', 'Task 4'],  # Will take first 3
            'sales': ['Sales Task 1', 'Sales Task 2', 'Sales Task 3'],
            'ops': ['Ops Task 1', 'Ops Task 2']
        }
        
        with patch('main.task_matrix', mock_task_matrix):
            candidates = generate_weekly_candidates()
            
            # Should generate candidates for marketing (3), sales (3), ops (2)
            assert len(candidates) == 8
            
            # Check marketing candidates
            marketing_candidates = [c for c in candidates if c.area == "Marketing"]
            assert len(marketing_candidates) == 3
            assert all(c.role == "CMO" for c in marketing_candidates)
            assert all(c.revenue_impact == 4 for c in marketing_candidates)
            
            # Check sales candidates
            sales_candidates = [c for c in candidates if c.area == "Sales"]
            assert len(sales_candidates) == 3
            assert all(c.role == "CSO" for c in sales_candidates)
            assert all(c.revenue_impact == 5 for c in sales_candidates)
            
            # Check ops candidates
            ops_candidates = [c for c in candidates if c.area == "Ops"]
            assert len(ops_candidates) == 2
            assert all(c.role == "COO" for c in ops_candidates)
            assert all(c.revenue_impact == 2 for c in ops_candidates)
    
    def test_generate_weekly_candidates_empty_matrix(self):
        """Test generating candidates with empty task matrix."""
        with patch('main.task_matrix', {}):
            candidates = generate_weekly_candidates()
            
            # Should return empty list when no tasks available
            assert len(candidates) == 0
    
    def test_generate_weekly_candidates_due_dates(self):
        """Test that generated candidates have appropriate due dates."""
        mock_task_matrix = {
            'marketing': ['Test task'],
            'sales': ['Test sales task'],
            'ops': ['Test ops task']
        }
        
        with patch('main.task_matrix', mock_task_matrix):
            candidates = generate_weekly_candidates()
            
            # Check that due dates are in the future
            today = datetime.datetime.now()
            for candidate in candidates:
                due_date = datetime.datetime.strptime(candidate.due_date, '%Y-%m-%d')
                assert due_date > today
            
            # Marketing tasks should be due in 7 days
            marketing_candidate = next(c for c in candidates if c.area == "Marketing")
            expected_due = (today + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            assert marketing_candidate.due_date == expected_due
            
            # Sales tasks should be due in 5 days
            sales_candidate = next(c for c in candidates if c.area == "Sales")
            expected_due = (today + datetime.timedelta(days=5)).strftime('%Y-%m-%d')
            assert sales_candidate.due_date == expected_due


class TestWeeklyRunbook:
    """Test Weekly Runbook functions."""
    
    def test_generate_ceo_weekly_plan(self):
        """Test CEO weekly plan generation."""
        # Mock configurations
        mock_business_brain = {
            'goals': {'north_star': 'Hit $30k/mo revenue'},
            'company': {'name': 'Test Company'}
        }
        mock_task_matrix = {
            'marketing': ['Marketing task'],
            'sales': ['Sales task']
        }
        
        mock_tasks = ['Task 1', 'Task 2']
        
        with patch('main.fetch_open_tasks', return_value=mock_tasks), \
             patch('main.perform_gap_check', return_value=['Gap 1', 'Gap 2']), \
             patch('main.business_brain', mock_business_brain), \
             patch('main.task_matrix', mock_task_matrix):
            
            plan = generate_ceo_weekly_plan("Generate weekly plan")
            
            assert "*Decouple Dev — Weekly Plan*" in plan
            assert "Working toward: Hit $30k/mo revenue" in plan
            assert "Top tasks (ranked by priority):" in plan
            assert "Identified gaps: 2 missing tasks from matrix" in plan
            assert "Approve Trello changes? (Y/N)" in plan
    
    def test_generate_ceo_weekly_plan_no_north_star(self):
        """Test CEO weekly plan generation without north star goal."""
        global business_brain, task_matrix
        
        # Mock configurations without north star
        business_brain = {'company': {'name': 'Test Company'}}
        task_matrix = {'marketing': ['Task']}
        
        with patch('main.fetch_open_tasks', return_value=[]), \
             patch('main.perform_gap_check', return_value=[]):
            
            plan = generate_ceo_weekly_plan()
            
            assert "Revenue pipeline + process foundations" in plan
    
    def test_generate_midweek_nudge(self):
        """Test Wednesday pipeline push message generation."""
        mock_tasks = ['client meeting task', 'sales proposal draft', 'random task']
        
        with patch('main.fetch_open_tasks', return_value=mock_tasks):
            nudge = generate_midweek_nudge()
            
            assert "*Pipeline Push*" in nudge
            assert "Current sales tasks: 2 active" in nudge
            assert "Record 1 proof asset today" in nudge
            assert "warm intros I should chase" in nudge
    
    def test_generate_friday_retro(self):
        """Test Friday retrospective message generation."""
        mock_tasks = ['Task 1', 'Task 2', 'Task 3']
        
        with patch('main.fetch_open_tasks', return_value=mock_tasks):
            retro = generate_friday_retro()
            
            assert "*Weekly Retro*" in retro
            assert "3 still pending" in retro
            assert "discovery calls 0, proposals 0" in retro
            assert "Proof assets captured:" in retro
            assert "Approve 'Next Up'" in retro


class TestTrelloIntegration:
    """Test Trello card creation and integration."""
    
    def test_create_trello_card_json(self):
        """Test creating Trello card JSON payload."""
        global business_brain
        
        # Mock business brain
        business_brain = {
            'policy': {
                'priority_order': ['RevenueNow', 'Systems']
            }
        }
        
        candidate = TaskCandidate(
            title="Test Task",
            description="Test description",
            area="Sales",
            role="CSO",
            revenue_impact=5,
            time_to_impact=4,
            effort=2,
            strategic_compounding=1,
            fit_to_constraints=2,
            due_date="2025-01-15",
            owner="Me",
            estimate="M",
            acceptance_criteria="Complete task successfully"
        )
        
        card_json = create_trello_card_json(candidate)
        
        assert card_json['name'] == "Test Task"
        assert "Goal: Test description" in card_json['desc']
        assert "Acceptance Criteria: Complete task successfully" in card_json['desc']
        assert "Owner: Me" in card_json['desc']
        assert "Estimate: M" in card_json['desc']
        # Check that priority score is included (may vary based on calculation)
        assert "Priority Score:" in card_json['desc']
        assert card_json['due'] == "2025-01-15"
        assert "RevenueNow" in card_json['labels']
        assert "Sales" in card_json['labels']
    
    def test_create_trello_card_json_no_business_brain(self):
        """Test creating Trello card JSON without business brain config."""
        global business_brain
        business_brain = {}
        
        candidate = TaskCandidate(
            title="Test Task",
            description="Test description",
            area="Marketing",
            role="CMO",
            revenue_impact=3,
            time_to_impact=3,
            effort=3,
            strategic_compounding=2,
            fit_to_constraints=1,
            due_date="2025-01-15",
            owner="Team",
            estimate="L",
            acceptance_criteria="Task completed"
        )
        
        card_json = create_trello_card_json(candidate)
        
        # Should handle missing business brain gracefully
        assert card_json['name'] == "Test Task"
        assert "Marketing" in card_json['labels']


class TestDiscoveryCallScript:
    """Test discovery call script functionality."""
    
    def test_get_discovery_call_script(self):
        """Test getting the discovery call script."""
        script = get_discovery_call_script()
        
        assert "**Discovery Call Script**" in script
        assert "Opener:" in script
        assert "CI/CD + a minimal test harness" in script
        assert "Questions:" in script
        assert "What breaks your deploys today?" in script
        assert "Close:" in script
        assert "fixed-price audit" in script
        assert "1–2 week sprint" in script


class TestIntegrationScenarios:
    """Test integrated CEO Operator scenarios."""
    
    def test_full_weekly_planning_cycle(self):
        """Test a complete weekly planning cycle."""
        # Set up realistic configurations
        mock_business_brain = {
            'company': {'name': 'Decouple Dev'},
            'goals': {'north_star': 'Hit $30k/mo revenue'},
            'policy': {'priority_order': ['RevenueNow', 'Retention', 'Systems']}
        }
        
        mock_task_matrix = {
            'marketing': ['Define ICP/pain bullets', 'TikTok content creation'],
            'sales': ['Outbound outreach', 'Discovery calls', 'Proposal templates'],
            'delivery': ['Audit playbooks', 'Sprint processes'],
            'ops': ['Weekly reviews', 'Contractor management']
        }
        
        current_tasks = ['Random existing task']
        
        with patch('main.fetch_open_tasks', return_value=current_tasks), \
             patch('main.business_brain', mock_business_brain), \
             patch('main.task_matrix', mock_task_matrix):
            # Generate weekly plan
            weekly_plan = generate_ceo_weekly_plan("Create comprehensive weekly plan")
            
            # Verify comprehensive plan elements
            assert "Decouple Dev — Weekly Plan" in weekly_plan
            assert "Hit $30k/mo revenue" in weekly_plan
            assert "Top tasks (ranked by priority)" in weekly_plan
            assert "Identified gaps:" in weekly_plan
            
            # Generate midweek nudge
            midweek_nudge = generate_midweek_nudge()
            assert "*Pipeline Push*" in midweek_nudge
            
            # Generate Friday retro
            friday_retro = generate_friday_retro()
            assert "*Weekly Retro*" in friday_retro
    
    def test_priority_engine_ranking(self):
        """Test that Priority Engine correctly ranks tasks."""
        mock_task_matrix = {
            'marketing': ['High impact marketing'],
            'sales': ['Direct revenue sales'],
            'ops': ['System maintenance']
        }
        
        with patch('main.task_matrix', mock_task_matrix):
            candidates = generate_weekly_candidates()
            
            # Sort by priority score (same as in generate_ceo_weekly_plan)
            candidates.sort(key=lambda x: x.priority_score, reverse=True)
            
            # Sales tasks should generally rank higher due to higher revenue_impact and time_to_impact
            assert len(candidates) > 0
            
            # Verify scores are in descending order
            for i in range(len(candidates) - 1):
                assert candidates[i].priority_score >= candidates[i + 1].priority_score
    
    def test_error_handling_in_ceo_functions(self):
        """Test error handling in CEO Operator functions."""
        global business_brain, task_matrix
        
        # Test with empty configurations
        business_brain = {}
        task_matrix = {}
        
        # Functions should handle empty configurations gracefully
        candidates = generate_weekly_candidates()
        assert len(candidates) == 0
        
        with patch('main.fetch_open_tasks', return_value=[]):
            gaps = perform_gap_check()
            assert len(gaps) == 0
            
            plan = generate_ceo_weekly_plan()
            assert "Weekly Plan" in plan


if __name__ == "__main__":
    import pytest
    
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
