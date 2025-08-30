"""
Mock Priority Engine - Simple implementation for testing
This provides basic priority scoring and ranking functionality
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PriorityEngine:
    """Mock priority engine for scoring and ranking tasks/requests"""
    
    def __init__(self):
        logger.info("Mock PriorityEngine initialized")
        
        # Define scoring weights for different factors
        self.weights = {
            "urgency": 0.4,
            "impact": 0.3,
            "effort": 0.2,
            "alignment": 0.1
        }
        
        # Priority level mappings
        self.priority_levels = {
            "Critical": 100,
            "High": 75,
            "Medium": 50,
            "Low": 25,
            "Deferred": 10
        }
    
    def calculate_priority_score(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate priority score for a task based on multiple factors"""
        try:
            logger.info(f"Mock: Calculating priority score for task: {task_data.get('title', 'Unknown')}")
            
            # Extract factors from task data or use defaults
            urgency = self._extract_urgency_score(task_data)
            impact = self._extract_impact_score(task_data)
            effort = self._extract_effort_score(task_data)
            alignment = self._extract_alignment_score(task_data)
            
            # Calculate weighted score
            weighted_score = (
                urgency * self.weights["urgency"] +
                impact * self.weights["impact"] +
                effort * self.weights["effort"] +
                alignment * self.weights["alignment"]
            )
            
            # Determine priority level
            priority_level = self._score_to_priority_level(weighted_score)
            
            return {
                "success": True,
                "task_id": task_data.get("id", "unknown"),
                "priority_score": round(weighted_score, 2),
                "priority_level": priority_level,
                "factors": {
                    "urgency": urgency,
                    "impact": impact,
                    "effort": effort,
                    "alignment": alignment
                },
                "weights": self.weights
            }
            
        except Exception as e:
            logger.error(f"Error calculating priority score: {e}")
            return {
                "success": False,
                "error": str(e),
                "priority_score": 0
            }
    
    def rank_tasks(self, tasks: List[Dict[str, Any]], limit: int = None) -> Dict[str, Any]:
        """Rank a list of tasks by priority"""
        try:
            logger.info(f"Mock: Ranking {len(tasks)} tasks by priority")
            
            scored_tasks = []
            
            for task in tasks:
                priority_result = self.calculate_priority_score(task)
                if priority_result["success"]:
                    task_with_score = task.copy()
                    task_with_score.update({
                        "priority_score": priority_result["priority_score"],
                        "priority_level": priority_result["priority_level"],
                        "priority_factors": priority_result["factors"]
                    })
                    scored_tasks.append(task_with_score)
            
            # Sort by priority score (descending)
            ranked_tasks = sorted(scored_tasks, key=lambda x: x["priority_score"], reverse=True)
            
            # Apply limit if provided
            if limit:
                ranked_tasks = ranked_tasks[:limit]
            
            return {
                "success": True,
                "ranked_tasks": ranked_tasks,
                "total_tasks": len(ranked_tasks),
                "ranking_criteria": "priority_score_descending"
            }
            
        except Exception as e:
            logger.error(f"Error ranking tasks: {e}")
            return {
                "success": False,
                "error": str(e),
                "ranked_tasks": []
            }
    
    def get_high_priority_tasks(self, tasks: List[Dict[str, Any]], threshold: float = 70.0) -> Dict[str, Any]:
        """Filter tasks that meet high priority threshold"""
        try:
            logger.info(f"Mock: Filtering high priority tasks (threshold: {threshold})")
            
            ranking_result = self.rank_tasks(tasks)
            if not ranking_result["success"]:
                return ranking_result
            
            high_priority_tasks = [
                task for task in ranking_result["ranked_tasks"]
                if task.get("priority_score", 0) >= threshold
            ]
            
            return {
                "success": True,
                "high_priority_tasks": high_priority_tasks,
                "total_count": len(high_priority_tasks),
                "threshold": threshold
            }
            
        except Exception as e:
            logger.error(f"Error filtering high priority tasks: {e}")
            return {
                "success": False,
                "error": str(e),
                "high_priority_tasks": []
            }
    
    def _extract_urgency_score(self, task_data: Dict[str, Any]) -> float:
        """Extract urgency score from task data"""
        # Check for due date
        due_date = task_data.get("due_date")
        if due_date:
            try:
                due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                now = datetime.now()
                days_until_due = (due - now).days
                
                if days_until_due < 1:
                    return 100.0  # Overdue or due today
                elif days_until_due <= 3:
                    return 80.0   # Due in 3 days
                elif days_until_due <= 7:
                    return 60.0   # Due in a week
                else:
                    return 40.0   # Not urgent
            except:
                pass
        
        # Check priority field
        priority = task_data.get("priority", "Medium").lower()
        if priority in ["critical", "urgent", "high"]:
            return 85.0
        elif priority == "medium":
            return 60.0
        else:
            return 30.0
    
    def _extract_impact_score(self, task_data: Dict[str, Any]) -> float:
        """Extract impact score from task data"""
        # Look for impact-related keywords
        title = task_data.get("title", "").lower()
        description = task_data.get("description", "").lower()
        project = task_data.get("project", "").lower()
        
        text = f"{title} {description} {project}"
        
        # High impact keywords
        high_impact_keywords = ["revenue", "sales", "customer", "critical", "launch", "release"]
        medium_impact_keywords = ["improve", "optimize", "enhance", "update"]
        
        if any(keyword in text for keyword in high_impact_keywords):
            return 80.0
        elif any(keyword in text for keyword in medium_impact_keywords):
            return 60.0
        else:
            return 40.0
    
    def _extract_effort_score(self, task_data: Dict[str, Any]) -> float:
        """Extract effort score from task data (lower effort = higher score)"""
        # Look for effort indicators
        title = task_data.get("title", "").lower()
        description = task_data.get("description", "").lower()
        
        text = f"{title} {description}"
        
        # Low effort (quick wins) get higher scores
        low_effort_keywords = ["quick", "simple", "easy", "fix", "update"]
        high_effort_keywords = ["complex", "develop", "build", "design", "architecture"]
        
        if any(keyword in text for keyword in low_effort_keywords):
            return 80.0  # Low effort, high score
        elif any(keyword in text for keyword in high_effort_keywords):
            return 30.0  # High effort, low score
        else:
            return 50.0  # Medium effort
    
    def _extract_alignment_score(self, task_data: Dict[str, Any]) -> float:
        """Extract strategic alignment score from task data"""
        project = task_data.get("project", "").lower()
        
        # Strategic projects get higher alignment scores
        strategic_projects = ["sales", "marketing", "revenue", "growth", "customer"]
        
        if any(keyword in project for keyword in strategic_projects):
            return 75.0
        else:
            return 50.0
    
    def _score_to_priority_level(self, score: float) -> str:
        """Convert numerical score to priority level"""
        if score >= 85:
            return "Critical"
        elif score >= 70:
            return "High"
        elif score >= 50:
            return "Medium"
        elif score >= 30:
            return "Low"
        else:
            return "Deferred"
    
    def get_priority_recommendations(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get priority-based recommendations for task management"""
        try:
            logger.info(f"Mock: Generating priority recommendations for {len(tasks)} tasks")
            
            ranking_result = self.rank_tasks(tasks)
            if not ranking_result["success"]:
                return ranking_result
            
            ranked_tasks = ranking_result["ranked_tasks"]
            
            recommendations = {
                "immediate_action": [t for t in ranked_tasks if t.get("priority_score", 0) >= 85],
                "this_week": [t for t in ranked_tasks if 70 <= t.get("priority_score", 0) < 85],
                "this_month": [t for t in ranked_tasks if 50 <= t.get("priority_score", 0) < 70],
                "backlog": [t for t in ranked_tasks if t.get("priority_score", 0) < 50]
            }
            
            return {
                "success": True,
                "recommendations": recommendations,
                "summary": {
                    "immediate_action": len(recommendations["immediate_action"]),
                    "this_week": len(recommendations["this_week"]),
                    "this_month": len(recommendations["this_month"]),
                    "backlog": len(recommendations["backlog"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating priority recommendations: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": {}
            }
    
    def get_daily_priority(self, tasks: List[Dict[str, Any]], priority_context = None) -> Dict[str, Any]:
        """Get the highest priority task for today"""
        try:
            logger.info(f"Mock: Getting daily priority from {len(tasks)} tasks")
            
            if not tasks:
                return {
                    "success": False,
                    "error": "No tasks available for priority selection",
                    "daily_priority": None
                }
            
            # Rank all tasks and select the top one
            ranking_result = self.rank_tasks(tasks, limit=1)
            if not ranking_result["success"] or not ranking_result["ranked_tasks"]:
                return {
                    "success": False,
                    "error": "Failed to rank tasks for daily priority",
                    "daily_priority": None
                }
            
            top_task = ranking_result["ranked_tasks"][0]
            
            # Format for daily priority response
            daily_priority = {
                "task_id": top_task.get("id"),
                "task_title": top_task.get("title"),
                "total_score": top_task.get("priority_score"),
                "priority_level": top_task.get("priority_level"),
                "factors": top_task.get("priority_factors", {}),
                "estimated_effort": top_task.get("estimated_effort", "Unknown")
            }
            
            # Generate reasoning
            reasoning = f"This task scored highest ({daily_priority['total_score']:.1f}) "
            reasoning += f"based on {daily_priority['priority_level'].lower()} priority factors. "
            
            factors = daily_priority.get("factors", {})
            if factors.get("urgency", 0) > 70:
                reasoning += "It has high urgency. "
            if factors.get("impact", 0) > 70:
                reasoning += "It has high business impact. "
            if factors.get("effort", 0) > 70:
                reasoning += "It's a quick win with low effort required."
            
            return {
                "success": True,
                "daily_priority": daily_priority,
                "reasoning": reasoning,
                "context": priority_context
            }
            
        except Exception as e:
            logger.error(f"Error getting daily priority: {e}")
            return {
                "success": False,
                "error": str(e),
                "daily_priority": None
            }
    
    def score_tasks(self, tasks: List[Dict[str, Any]], priority_context = None) -> Dict[str, Any]:
        """Score and rank tasks based on priority factors"""
        try:
            logger.info(f"Mock: Scoring {len(tasks)} tasks with context")
            
            scored_tasks = []
            
            for task in tasks:
                # Calculate priority score
                score_result = self.calculate_priority_score(task)
                if score_result["success"]:
                    scored_task = task.copy()
                    scored_task.update({
                        "priority_score": score_result["priority_score"],
                        "priority_level": score_result["priority_level"],
                        "scoring_factors": score_result["factors"],
                        "context_adjustments": self._apply_context_adjustments(
                            score_result["priority_score"], task, priority_context
                        )
                    })
                    scored_tasks.append(scored_task)
            
            # Sort by adjusted score (descending)
            scored_tasks = sorted(
                scored_tasks, 
                key=lambda x: x.get("context_adjustments", {}).get("adjusted_score", x.get("priority_score", 0)), 
                reverse=True
            )
            
            return {
                "success": True,
                "scored_tasks": scored_tasks,
                "total_tasks": len(scored_tasks),
                "scoring_criteria": {
                    "base_factors": list(self.weights.keys()),
                    "context_applied": priority_context is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error scoring tasks: {e}")
            return {
                "success": False,
                "error": str(e),
                "scored_tasks": []
            }
    
    def _apply_context_adjustments(self, base_score: float, task: Dict[str, Any], context) -> Dict[str, Any]:
        """Apply context-based adjustments to the base priority score"""
        adjustments = {
            "base_score": base_score,
            "adjustments": [],
            "adjusted_score": base_score
        }
        
        if not context:
            return adjustments
        
        try:
            adjusted_score = base_score
            
            # Time-based adjustments
            if hasattr(context, 'available_time_hours'):
                effort_str = task.get("estimated_effort", "1 hour")
                try:
                    effort_hours = float(effort_str.split()[0]) if effort_str else 1.0
                    if effort_hours > context.available_time_hours:
                        adjusted_score -= 10  # Reduce score for tasks that don't fit
                        adjustments["adjustments"].append("Reduced for time constraint")
                except:
                    pass
            
            # Revenue-based adjustments
            if hasattr(context, 'current_revenue') and hasattr(context, 'target_revenue'):
                revenue_gap = context.target_revenue - context.current_revenue
                if revenue_gap > 0:
                    # Boost revenue-related tasks
                    task_text = f"{task.get('title', '')} {task.get('description', '')}".lower()
                    if any(keyword in task_text for keyword in ['revenue', 'sales', 'customer', 'money']):
                        adjusted_score += 15
                        adjustments["adjustments"].append("Boosted for revenue focus")
            
            # Business stage adjustments
            if hasattr(context, 'business_stage'):
                if context.business_stage == "early_stage":
                    # Prioritize foundational tasks
                    task_text = f"{task.get('title', '')} {task.get('description', '')}".lower()
                    if any(keyword in task_text for keyword in ['setup', 'foundation', 'system', 'process']):
                        adjusted_score += 10
                        adjustments["adjustments"].append("Boosted for early stage focus")
            
            adjustments["adjusted_score"] = max(0, adjusted_score)
            return adjustments
            
        except Exception as e:
            logger.warning(f"Error applying context adjustments: {e}")
            return adjustments
