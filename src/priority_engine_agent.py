"""
Priority Engine Agent - Deterministic task scoring and ranking system
Uses mathematical formulas to score tasks based on business criteria
"""
import os
import json
import yaml
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class PriorityFactor(Enum):
    """Factors that influence task priority"""
    REVENUE_IMPACT = "revenue_impact"
    TIME_TO_IMPACT = "time_to_impact"
    EFFORT_REQUIRED = "effort_required"
    STRATEGIC_VALUE = "strategic_value"
    URGENCY = "urgency"
    DEPENDENCIES = "dependencies"
    BUSINESS_ALIGNMENT = "business_alignment"


@dataclass
class TaskScore:
    """Comprehensive task scoring breakdown"""
    task_id: str
    task_title: str
    total_score: float
    revenue_impact_score: float
    time_to_impact_score: float
    effort_efficiency_score: float
    strategic_value_score: float
    urgency_score: float
    alignment_score: float
    final_rank: Optional[int] = None
    reasoning: str = ""
    confidence: float = 0.0


@dataclass
class PriorityContext:
    """Context information for priority calculation"""
    current_business_goals: List[Dict[str, Any]]
    available_time_hours: int
    current_revenue: float
    target_revenue: float
    business_stage: str
    constraints: Dict[str, Any]


class PriorityEngineAgent:
    """Agent that provides deterministic task prioritization"""
    
    def __init__(self, config_path: str = "config/priority_engine.yaml"):
        self.config_path = config_path
        self.scoring_weights = {}
        self.business_multipliers = {}
        self.load_configuration()
        
        logger.info("Priority Engine Agent initialized with deterministic scoring")
    
    def load_configuration(self):
        """Load priority scoring configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.scoring_weights = config.get("scoring_weights", {})
                    self.business_multipliers = config.get("business_multipliers", {})
            else:
                logger.warning("Priority config not found, using defaults")
                self.setup_default_config()
        except Exception as e:
            logger.error(f"Error loading priority configuration: {e}")
            self.setup_default_config()
    
    def setup_default_config(self):
        """Set up default scoring configuration"""
        self.scoring_weights = {
            "revenue_impact": 3.0,      # Highest weight - direct revenue impact
            "time_to_impact": 2.0,      # Speed of results
            "effort_efficiency": 1.5,   # Effort vs impact ratio
            "strategic_value": 1.0,     # Long-term strategic importance
            "urgency": 1.0,             # Time sensitivity
            "business_alignment": 0.5   # Alignment with current goals
        }
        
        self.business_multipliers = {
            "early_stage": {
                "revenue_impact": 1.5,
                "strategic_value": 0.8
            },
            "growth_stage": {
                "revenue_impact": 1.3,
                "strategic_value": 1.2
            },
            "mature_stage": {
                "revenue_impact": 1.0,
                "strategic_value": 1.5
            }
        }
    
    def score_tasks(self, tasks: List[Dict[str, Any]], context: PriorityContext) -> Dict[str, Any]:
        """Score and rank a list of tasks deterministically"""
        try:
            scored_tasks = []
            
            for task in tasks:
                score = self._calculate_comprehensive_score(task, context)
                scored_tasks.append(score)
            
            # Sort by total score (highest first)
            scored_tasks.sort(key=lambda x: x.total_score, reverse=True)
            
            # Assign ranks
            for i, task_score in enumerate(scored_tasks, 1):
                task_score.final_rank = i
            
            # Calculate distribution statistics
            scores = [task.total_score for task in scored_tasks]
            stats = {
                "total_tasks": len(scored_tasks),
                "highest_score": max(scores) if scores else 0,
                "lowest_score": min(scores) if scores else 0,
                "average_score": sum(scores) / len(scores) if scores else 0,
                "score_range": max(scores) - min(scores) if scores else 0
            }
            
            logger.info(f"Scored {len(scored_tasks)} tasks, score range: {stats['lowest_score']:.2f} - {stats['highest_score']:.2f}")
            
            return {
                "success": True,
                "scored_tasks": [asdict(task) for task in scored_tasks],
                "statistics": stats,
                "context_used": asdict(context)
            }
            
        except Exception as e:
            logger.error(f"Error scoring tasks: {e}")
            return {
                "success": False,
                "error": str(e),
                "scored_tasks": []
            }
    
    def get_daily_priority(self, tasks: List[Dict[str, Any]], context: PriorityContext) -> Dict[str, Any]:
        """Get the single highest priority task for today - deterministic selection"""
        try:
            if not tasks:
                return {
                    "success": False,
                    "error": "No tasks provided",
                    "daily_priority": None
                }
            
            # Score all tasks
            scoring_result = self.score_tasks(tasks, context)
            if not scoring_result["success"]:
                return scoring_result
            
            scored_tasks = scoring_result["scored_tasks"]
            
            # Apply daily priority logic
            daily_candidates = self._filter_for_daily_work(scored_tasks, context)
            
            if not daily_candidates:
                return {
                    "success": False,
                    "error": "No suitable tasks for daily work",
                    "daily_priority": None
                }
            
            # Select the highest scoring daily candidate
            top_task = daily_candidates[0]
            
            # Generate deterministic selection reasoning
            selection_reasoning = self._generate_daily_selection_reasoning(
                top_task, daily_candidates, context
            )
            
            logger.info(f"Selected daily priority: {top_task['task_title']} (score: {top_task['total_score']:.2f})")
            
            return {
                "success": True,
                "daily_priority": top_task,
                "reasoning": selection_reasoning,
                "alternatives_considered": len(daily_candidates),
                "selection_criteria": "highest_score_with_daily_constraints"
            }
            
        except Exception as e:
            logger.error(f"Error selecting daily priority: {e}")
            return {
                "success": False,
                "error": str(e),
                "daily_priority": None
            }
    
    def rank_tasks_by_criteria(self, tasks: List[Dict[str, Any]], 
                              criteria: List[str], context: PriorityContext) -> Dict[str, Any]:
        """Rank tasks by specific criteria"""
        try:
            valid_criteria = [c for c in criteria if c in self.scoring_weights]
            if not valid_criteria:
                return {
                    "success": False,
                    "error": f"No valid criteria provided. Valid options: {list(self.scoring_weights.keys())}"
                }
            
            ranked_tasks = []
            
            for task in tasks:
                criteria_scores = {}
                total_weighted_score = 0
                
                for criterion in valid_criteria:
                    score = self._calculate_criterion_score(task, criterion, context)
                    weight = self.scoring_weights[criterion]
                    criteria_scores[criterion] = score
                    total_weighted_score += score * weight
                
                task_ranking = {
                    "task_id": task.get("id", ""),
                    "task_title": task.get("title", ""),
                    "criteria_scores": criteria_scores,
                    "total_weighted_score": total_weighted_score
                }
                ranked_tasks.append(task_ranking)
            
            # Sort by total weighted score
            ranked_tasks.sort(key=lambda x: x["total_weighted_score"], reverse=True)
            
            # Add ranks
            for i, task in enumerate(ranked_tasks, 1):
                task["rank"] = i
            
            logger.info(f"Ranked {len(ranked_tasks)} tasks by criteria: {valid_criteria}")
            
            return {
                "success": True,
                "ranked_tasks": ranked_tasks,
                "criteria_used": valid_criteria,
                "ranking_method": "weighted_sum"
            }
            
        except Exception as e:
            logger.error(f"Error ranking tasks by criteria: {e}")
            return {
                "success": False,
                "error": str(e),
                "ranked_tasks": []
            }
    
    def _calculate_comprehensive_score(self, task: Dict[str, Any], context: PriorityContext) -> TaskScore:
        """Calculate comprehensive score for a single task"""
        try:
            task_id = task.get("id", "")
            task_title = task.get("title", "Unknown Task")
            
            # Calculate individual dimension scores (0-5 scale)
            revenue_score = self._calculate_revenue_impact_score(task, context)
            time_to_impact_score = self._calculate_time_to_impact_score(task, context)
            effort_score = self._calculate_effort_efficiency_score(task, context)
            strategic_score = self._calculate_strategic_value_score(task, context)
            urgency_score = self._calculate_urgency_score(task, context)
            alignment_score = self._calculate_business_alignment_score(task, context)
            
            # Apply business stage multipliers
            business_stage = context.business_stage
            multipliers = self.business_multipliers.get(business_stage, {})
            
            revenue_score *= multipliers.get("revenue_impact", 1.0)
            strategic_score *= multipliers.get("strategic_value", 1.0)
            
            # Calculate weighted total score
            total_score = (
                revenue_score * self.scoring_weights["revenue_impact"] +
                time_to_impact_score * self.scoring_weights["time_to_impact"] +
                effort_score * self.scoring_weights["effort_efficiency"] +
                strategic_score * self.scoring_weights["strategic_value"] +
                urgency_score * self.scoring_weights["urgency"] +
                alignment_score * self.scoring_weights["business_alignment"]
            )
            
            # Generate reasoning
            reasoning = self._generate_scoring_reasoning(
                revenue_score, time_to_impact_score, effort_score, 
                strategic_score, urgency_score, alignment_score
            )
            
            # Calculate confidence based on data quality
            confidence = self._calculate_confidence_score(task)
            
            return TaskScore(
                task_id=task_id,
                task_title=task_title,
                total_score=round(total_score, 2),
                revenue_impact_score=round(revenue_score, 2),
                time_to_impact_score=round(time_to_impact_score, 2),
                effort_efficiency_score=round(effort_score, 2),
                strategic_value_score=round(strategic_score, 2),
                urgency_score=round(urgency_score, 2),
                alignment_score=round(alignment_score, 2),
                reasoning=reasoning,
                confidence=round(confidence, 2)
            )
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive score for task: {e}")
            return TaskScore(
                task_id=task.get("id", ""),
                task_title=task.get("title", "Error Task"),
                total_score=0.0,
                revenue_impact_score=0.0,
                time_to_impact_score=0.0,
                effort_efficiency_score=0.0,
                strategic_value_score=0.0,
                urgency_score=0.0,
                alignment_score=0.0,
                reasoning="Error in scoring calculation",
                confidence=0.0
            )
    
    def _calculate_revenue_impact_score(self, task: Dict[str, Any], context: PriorityContext) -> float:
        """Calculate revenue impact score (0-5 scale)"""
        # Analyze task for revenue indicators
        task_title = task.get("title", "").lower()
        task_description = task.get("description", "").lower()
        task_area = task.get("project", "").lower()
        
        # Direct revenue indicators
        direct_revenue_keywords = [
            "sales", "client", "prospect", "lead", "proposal", "close", "revenue", 
            "discovery call", "outreach", "pipeline", "deal", "customer"
        ]
        
        # Count direct revenue indicators
        direct_indicators = sum(
            1 for keyword in direct_revenue_keywords 
            if keyword in task_title or keyword in task_description
        )
        
        # Area-based scoring
        area_scores = {
            "sales": 5.0,
            "marketing": 3.5,
            "delivery": 2.0,
            "operations": 1.0,
            "finance": 1.5,
            "product": 2.5,
            "team": 0.5
        }
        
        area_score = area_scores.get(task_area, 2.0)  # Default medium impact
        
        # Combine indicators and area score
        indicator_boost = min(2.0, direct_indicators * 0.5)  # Cap boost at 2.0
        base_score = min(5.0, area_score + indicator_boost)
        
        return base_score
    
    def _calculate_time_to_impact_score(self, task: Dict[str, Any], context: PriorityContext) -> float:
        """Calculate time to impact score - faster = higher score (0-5 scale)"""
        # Parse estimated effort/duration
        effort_str = task.get("estimated_effort", "")
        description = task.get("description", "").lower()
        
        # Extract time estimates
        estimated_hours = self._parse_hours_from_string(effort_str + " " + description)
        
        # Score based on time to complete and see results
        if estimated_hours <= 2:
            return 5.0  # Immediate impact
        elif estimated_hours <= 4:
            return 4.0  # Same day impact
        elif estimated_hours <= 8:
            return 3.0  # Next day impact
        elif estimated_hours <= 16:
            return 2.0  # Weekly impact
        elif estimated_hours <= 40:
            return 1.0  # Monthly impact
        else:
            return 0.5  # Long-term impact
    
    def _calculate_effort_efficiency_score(self, task: Dict[str, Any], context: PriorityContext) -> float:
        """Calculate effort efficiency - lower effort for high impact = higher score"""
        estimated_hours = self._parse_hours_from_string(
            task.get("estimated_effort", "") + " " + task.get("description", "")
        )
        
        # Get expected impact level
        expected_impact = self._estimate_task_impact_level(task)
        
        # Calculate efficiency ratio
        if estimated_hours == 0:
            estimated_hours = 3.0  # Default assumption
        
        # Efficiency = Impact / Effort (normalized to 0-5 scale)
        impact_values = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        impact_score = impact_values.get(expected_impact, 2)
        
        # Inverse relationship with effort, normalized to 0-5
        efficiency = (impact_score * 10) / estimated_hours
        
        return min(5.0, efficiency)
    
    def _calculate_strategic_value_score(self, task: Dict[str, Any], context: PriorityContext) -> float:
        """Calculate strategic value score (0-5 scale)"""
        task_title = task.get("title", "").lower()
        task_description = task.get("description", "").lower()
        
        # Strategic keywords
        strategic_keywords = [
            "foundation", "system", "process", "automat", "scale", "framework",
            "strategy", "long-term", "competitive", "growth", "expansion"
        ]
        
        # Foundational tasks score higher
        strategic_indicators = sum(
            1 for keyword in strategic_keywords 
            if keyword in task_title or keyword in task_description
        )
        
        # Base score from strategic indicators
        base_score = min(3.0, strategic_indicators * 0.8)
        
        # Boost for foundational business areas
        if any(word in task_title for word in ["foundation", "framework", "system"]):
            base_score += 1.5
        
        # Goal alignment boost
        goal_alignment = self._check_goal_alignment(task, context)
        base_score += goal_alignment
        
        return min(5.0, base_score)
    
    def _calculate_urgency_score(self, task: Dict[str, Any], context: PriorityContext) -> float:
        """Calculate urgency score based on due dates and external factors"""
        due_date_str = task.get("due_date", "")
        
        if not due_date_str:
            return 2.0  # No deadline = medium urgency
        
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_until_due = (due_date - today).days
            
            if days_until_due < 0:
                return 5.0  # Overdue
            elif days_until_due == 0:
                return 4.5  # Due today
            elif days_until_due <= 1:
                return 4.0  # Due tomorrow
            elif days_until_due <= 3:
                return 3.0  # Due this week
            elif days_until_due <= 7:
                return 2.0  # Due next week
            else:
                return 1.0  # Future deadline
                
        except ValueError:
            return 2.0  # Invalid date format
    
    def _calculate_business_alignment_score(self, task: Dict[str, Any], context: PriorityContext) -> float:
        """Calculate alignment with current business goals"""
        return self._check_goal_alignment(task, context)
    
    def _calculate_criterion_score(self, task: Dict[str, Any], criterion: str, context: PriorityContext) -> float:
        """Calculate score for a specific criterion"""
        if criterion == "revenue_impact":
            return self._calculate_revenue_impact_score(task, context)
        elif criterion == "time_to_impact":
            return self._calculate_time_to_impact_score(task, context)
        elif criterion == "effort_efficiency":
            return self._calculate_effort_efficiency_score(task, context)
        elif criterion == "strategic_value":
            return self._calculate_strategic_value_score(task, context)
        elif criterion == "urgency":
            return self._calculate_urgency_score(task, context)
        elif criterion == "business_alignment":
            return self._calculate_business_alignment_score(task, context)
        else:
            return 2.0  # Default medium score
    
    def _parse_hours_from_string(self, text: str) -> float:
        """Extract hour estimates from text"""
        import re
        
        # Look for patterns like "2-3 hours", "4 hours", "1-2h", etc.
        hour_patterns = [
            r'(\d+)-(\d+)\s*hours?',
            r'(\d+)\s*hours?',
            r'(\d+)-(\d+)h',
            r'(\d+)h'
        ]
        
        for pattern in hour_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                if isinstance(matches[0], tuple):
                    # Range like "2-3 hours"
                    return (float(matches[0][0]) + float(matches[0][1])) / 2
                else:
                    # Single value like "4 hours"
                    return float(matches[0])
        
        return 3.0  # Default estimate
    
    def _estimate_task_impact_level(self, task: Dict[str, Any]) -> str:
        """Estimate the impact level of a task"""
        task_text = (task.get("title", "") + " " + task.get("description", "")).lower()
        
        # High impact indicators
        high_impact_keywords = [
            "revenue", "client", "sales", "critical", "launch", "release"
        ]
        
        # Low impact indicators  
        low_impact_keywords = [
            "documentation", "cleanup", "minor", "update", "maintenance"
        ]
        
        high_score = sum(1 for keyword in high_impact_keywords if keyword in task_text)
        low_score = sum(1 for keyword in low_impact_keywords if keyword in task_text)
        
        if high_score > low_score and high_score >= 2:
            return "high"
        elif low_score > high_score and low_score >= 2:
            return "low"
        else:
            return "medium"
    
    def _check_goal_alignment(self, task: Dict[str, Any], context: PriorityContext) -> float:
        """Check how well task aligns with current business goals"""
        if not context.current_business_goals:
            return 1.0  # No goals to align with
        
        task_text = (task.get("title", "") + " " + task.get("description", "")).lower()
        alignment_score = 0.0
        
        for goal in context.current_business_goals:
            goal_text = (goal.get("title", "") + " " + goal.get("description", "")).lower()
            goal_area = goal.get("area", "").lower()
            task_area = task.get("project", "").lower()
            
            # Area alignment
            if goal_area == task_area:
                alignment_score += 1.0
            
            # Keyword overlap
            goal_keywords = set(goal_text.split())
            task_keywords = set(task_text.split())
            overlap = len(goal_keywords & task_keywords)
            
            if overlap >= 2:
                alignment_score += 0.5
        
        return min(3.0, alignment_score)  # Cap at 3.0
    
    def _filter_for_daily_work(self, scored_tasks: List[Dict[str, Any]], context: PriorityContext) -> List[Dict[str, Any]]:
        """Filter tasks suitable for daily work"""
        daily_candidates = []
        max_daily_hours = 8  # Maximum daily work hours
        
        for task_data in scored_tasks:
            # Estimate task duration
            estimated_hours = self._parse_hours_from_string(
                task_data.get("task_title", "") + " estimated effort description"
            )
            
            # Include tasks that can be completed in a day or are high priority
            if estimated_hours <= max_daily_hours or task_data["total_score"] >= 12.0:
                daily_candidates.append(task_data)
        
        return daily_candidates
    
    def _generate_scoring_reasoning(self, revenue: float, time_to_impact: float, 
                                   effort: float, strategic: float, urgency: float, 
                                   alignment: float) -> str:
        """Generate human-readable reasoning for the scoring"""
        components = []
        
        if revenue >= 4.0:
            components.append("high revenue potential")
        elif revenue >= 3.0:
            components.append("moderate revenue impact")
        
        if time_to_impact >= 4.0:
            components.append("quick results expected")
        elif time_to_impact <= 2.0:
            components.append("longer-term payoff")
        
        if effort >= 4.0:
            components.append("highly efficient effort-to-impact ratio")
        elif effort <= 2.0:
            components.append("high effort requirement")
        
        if strategic >= 3.5:
            components.append("strong strategic value")
        
        if urgency >= 4.0:
            components.append("time-sensitive")
        
        if alignment >= 2.0:
            components.append("well-aligned with business goals")
        
        if components:
            return "Prioritized due to: " + ", ".join(components)
        else:
            return "Standard priority task"
    
    def _generate_daily_selection_reasoning(self, selected_task: Dict[str, Any], 
                                           alternatives: List[Dict[str, Any]], 
                                           context: PriorityContext) -> str:
        """Generate reasoning for daily priority selection"""
        score = selected_task["total_score"]
        title = selected_task["task_title"]
        
        reasoning = f"Selected '{title}' (score: {score:.1f}) as today's priority because:\n"
        
        # Score-based reasoning
        if score >= 15.0:
            reasoning += "• Exceptional priority score indicates high business impact\n"
        elif score >= 12.0:
            reasoning += "• High priority score suggests strong ROI potential\n"
        
        # Specific factor highlights
        if selected_task["revenue_impact_score"] >= 4.0:
            reasoning += "• Strong revenue generation potential\n"
        
        if selected_task["time_to_impact_score"] >= 4.0:
            reasoning += "• Quick results expected\n"
        
        if selected_task["effort_efficiency_score"] >= 4.0:
            reasoning += "• Excellent effort-to-impact efficiency\n"
        
        if selected_task["urgency_score"] >= 4.0:
            reasoning += "• Time-sensitive with approaching deadline\n"
        
        # Context factors
        if context.available_time_hours <= 4:
            reasoning += f"• Fits within available time budget of {context.available_time_hours} hours\n"
        
        return reasoning.strip()
    
    def _calculate_confidence_score(self, task: Dict[str, Any]) -> float:
        """Calculate confidence in the scoring based on available data"""
        data_quality_factors = []
        
        # Check data completeness
        if task.get("title"):
            data_quality_factors.append(0.2)
        if task.get("description"):
            data_quality_factors.append(0.2)
        if task.get("estimated_effort"):
            data_quality_factors.append(0.2)
        if task.get("due_date"):
            data_quality_factors.append(0.2)
        if task.get("project"):
            data_quality_factors.append(0.2)
        
        return sum(data_quality_factors)
