"""
Task Discovery Agent - Identifies new tasks based on business context
Analyzes gaps, business goals, and strategic priorities to suggest actionable tasks
"""
import os
import json
import yaml
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class BusinessArea(Enum):
    """Business areas for task categorization"""
    MARKETING = "marketing"
    SALES = "sales"
    DELIVERY = "delivery"
    OPERATIONS = "operations"
    FINANCE = "finance"
    PRODUCT = "product"
    TEAM = "team"


@dataclass
class TaskSuggestion:
    """Structure for task suggestions"""
    title: str
    description: str
    area: BusinessArea
    priority: str
    estimated_effort: str
    reasoning: str
    acceptance_criteria: str
    due_date_suggestion: Optional[str]
    dependencies: List[str]
    business_impact: str


class TaskDiscoveryAgent:
    """Agent specialized in discovering missing tasks and gaps"""
    
    def __init__(self, business_brain_path: str = "business_brain.yaml", task_matrix_path: str = "task_matrix.yaml"):
        self.business_brain_path = business_brain_path
        self.task_matrix_path = task_matrix_path
        self.business_brain = {}
        self.task_matrix = {}
        
        self.load_business_context()
        logger.info("Task Discovery Agent initialized")
    
    def load_business_context(self):
        """Load business brain and task matrix configurations"""
        try:
            # Load business brain
            if os.path.exists(self.business_brain_path):
                with open(self.business_brain_path, 'r') as f:
                    self.business_brain = yaml.safe_load(f)
                    logger.info(f"Loaded business brain: {self.business_brain.get('company', {}).get('name', 'Unknown')}")
            else:
                logger.warning("Business brain file not found, using defaults")
                self.business_brain = self._get_default_business_brain()
            
            # Load task matrix
            if os.path.exists(self.task_matrix_path):
                with open(self.task_matrix_path, 'r') as f:
                    self.task_matrix = yaml.safe_load(f)
                    logger.info(f"Loaded task matrix with {len(self.task_matrix)} areas")
            else:
                logger.warning("Task matrix file not found, using defaults")
                self.task_matrix = self._get_default_task_matrix()
                
        except Exception as e:
            logger.error(f"Error loading business context: {e}")
            self.business_brain = self._get_default_business_brain()
            self.task_matrix = self._get_default_task_matrix()
    
    def _get_default_business_brain(self) -> Dict[str, Any]:
        """Default business brain configuration"""
        return {
            "company": {
                "name": "Decouple Dev",
                "positioning": "Async development agency",
                "stage": "early_growth"
            },
            "goals": {
                "north_star": "Hit $30k/mo revenue",
                "quarterly_targets": ["$15k MRR", "5 active clients", "Streamlined delivery"]
            },
            "constraints": {
                "time_per_week": 40,
                "budget_monthly": 5000,
                "team_size": 1
            },
            "priorities": {
                "order": ["revenue", "retention", "systems", "brand"]
            }
        }
    
    def _get_default_task_matrix(self) -> Dict[str, List[str]]:
        """Default task matrix configuration"""
        return {
            "marketing": [
                "Content creation and distribution",
                "SEO optimization",
                "Social media presence",
                "Lead magnets and case studies"
            ],
            "sales": [
                "Outbound prospecting",
                "Discovery call framework",
                "Proposal templates",
                "Pipeline management"
            ],
            "delivery": [
                "Process documentation", 
                "Quality assurance checklists",
                "Client communication templates",
                "Project management system"
            ],
            "operations": [
                "Weekly business reviews",
                "Metrics tracking setup",
                "Automation workflows",
                "Financial management"
            ],
            "product": [
                "Service offerings refinement",
                "Pricing strategy",
                "Technology stack optimization",
                "Tools and systems integration"
            ],
            "team": [
                "Hiring processes",
                "Onboarding documentation",
                "Skills development",
                "Contractor management"
            ]
        }
    
    def analyze_business_gaps(self, current_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze gaps between current tasks and required business activities"""
        try:
            # Extract current task titles and areas
            current_task_titles = [task.get("title", "").lower() for task in current_tasks]
            current_areas = [task.get("project", "").lower() for task in current_tasks]
            
            gaps = {}
            coverage_analysis = {}
            
            # Analyze each business area
            for area, required_tasks in self.task_matrix.items():
                area_gaps = []
                area_coverage = 0
                
                for required_task in required_tasks:
                    # Check if this required task has coverage in current tasks
                    task_keywords = required_task.lower().split()[:3]  # First 3 words for matching
                    
                    # Check for keyword overlap
                    has_coverage = any(
                        any(keyword in current_title for keyword in task_keywords)
                        for current_title in current_task_titles
                    )
                    
                    if has_coverage:
                        area_coverage += 1
                    else:
                        area_gaps.append(required_task)
                
                gaps[area] = area_gaps
                coverage_analysis[area] = {
                    "required_tasks": len(required_tasks),
                    "covered_tasks": area_coverage,
                    "coverage_percentage": round((area_coverage / len(required_tasks)) * 100, 1),
                    "missing_tasks": len(area_gaps)
                }
            
            # Calculate overall business health
            total_required = sum(len(tasks) for tasks in self.task_matrix.values())
            total_covered = sum(analysis["covered_tasks"] for analysis in coverage_analysis.values())
            overall_coverage = round((total_covered / total_required) * 100, 1)
            
            # Identify priority gap areas based on business priorities
            priority_gaps = self._identify_priority_gaps(gaps, coverage_analysis)
            
            logger.info(f"Gap analysis completed: {overall_coverage}% business coverage")
            
            return {
                "success": True,
                "overall_coverage": overall_coverage,
                "area_analysis": coverage_analysis,
                "gaps_by_area": gaps,
                "priority_gaps": priority_gaps,
                "recommendations": self._generate_gap_recommendations(gaps, coverage_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in gap analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "overall_coverage": 0
            }
    
    def suggest_tasks_for_goals(self, business_goals: List[Dict[str, Any]], limit: int = 10) -> Dict[str, Any]:
        """Suggest specific tasks to achieve business goals"""
        try:
            suggestions = []
            
            for goal in business_goals:
                goal_title = goal.get("title", "")
                goal_area = goal.get("area", "sales")
                goal_description = goal.get("description", "")
                target_date = goal.get("target_date", "")
                
                # Generate task suggestions for this goal
                goal_tasks = self._generate_goal_specific_tasks(
                    goal_title, goal_area, goal_description, target_date
                )
                suggestions.extend(goal_tasks)
            
            # Sort by business impact and priority
            suggestions.sort(key=lambda x: self._calculate_task_priority_score(x), reverse=True)
            
            # Limit results
            suggestions = suggestions[:limit]
            
            logger.info(f"Generated {len(suggestions)} task suggestions for {len(business_goals)} goals")
            
            return {
                "success": True,
                "task_suggestions": [asdict(task) for task in suggestions],
                "count": len(suggestions),
                "based_on_goals": len(business_goals)
            }
            
        except Exception as e:
            logger.error(f"Error generating task suggestions: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_suggestions": []
            }
    
    def discover_missing_foundations(self) -> Dict[str, Any]:
        """Discover missing foundational business tasks"""
        try:
            foundational_areas = {
                "brand_identity": {
                    "area": BusinessArea.MARKETING,
                    "tasks": [
                        "Define brand voice and messaging",
                        "Create brand style guide",
                        "Develop elevator pitch variations",
                        "Document unique value proposition"
                    ]
                },
                "sales_system": {
                    "area": BusinessArea.SALES,
                    "tasks": [
                        "Create discovery call script",
                        "Build proposal template",
                        "Set up CRM system",
                        "Define sales process stages"
                    ]
                },
                "delivery_excellence": {
                    "area": BusinessArea.DELIVERY,
                    "tasks": [
                        "Create project kickoff checklist",
                        "Build quality assurance process",
                        "Document handoff procedures",
                        "Establish client feedback loops"
                    ]
                },
                "business_operations": {
                    "area": BusinessArea.OPERATIONS,
                    "tasks": [
                        "Set up financial tracking",
                        "Create weekly review process",
                        "Build metrics dashboard",
                        "Document standard procedures"
                    ]
                }
            }
            
            suggestions = []
            
            for foundation, config in foundational_areas.items():
                for task_title in config["tasks"]:
                    suggestion = TaskSuggestion(
                        title=f"[Foundation] {task_title}",
                        description=f"Foundational task for {foundation.replace('_', ' ')}",
                        area=config["area"],
                        priority="High",
                        estimated_effort="2-4 hours",
                        reasoning=f"Essential foundation for {config['area'].value} excellence",
                        acceptance_criteria=f"Complete and document {task_title.lower()}",
                        due_date_suggestion=self._calculate_due_date(7),  # 1 week
                        dependencies=[],
                        business_impact="Foundational - enables future growth"
                    )
                    suggestions.append(suggestion)
            
            logger.info(f"Discovered {len(suggestions)} foundational tasks")
            
            return {
                "success": True,
                "foundational_tasks": [asdict(task) for task in suggestions],
                "count": len(suggestions),
                "focus_areas": list(foundational_areas.keys())
            }
            
        except Exception as e:
            logger.error(f"Error discovering foundational tasks: {e}")
            return {
                "success": False,
                "error": str(e),
                "foundational_tasks": []
            }
    
    def generate_weekly_task_candidates(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate task candidates for the upcoming week"""
        try:
            context = context or {}
            time_available = context.get("time_available", 40)  # hours per week
            current_priorities = context.get("priorities", self.business_brain.get("priorities", {}).get("order", []))
            
            candidates = []
            
            # Generate tasks for each priority area
            for priority in current_priorities:
                area_tasks = self._generate_priority_area_tasks(priority, time_available // len(current_priorities))
                candidates.extend(area_tasks)
            
            # Add time-sensitive opportunities
            opportunity_tasks = self._identify_time_sensitive_opportunities()
            candidates.extend(opportunity_tasks)
            
            # Score and rank candidates
            for candidate in candidates:
                candidate.priority_score = self._calculate_task_priority_score(candidate)
            
            candidates.sort(key=lambda x: x.priority_score, reverse=True)
            
            # Select top candidates that fit time constraint
            selected_candidates = self._select_optimal_task_mix(candidates, time_available)
            
            logger.info(f"Generated {len(selected_candidates)} weekly task candidates")
            
            return {
                "success": True,
                "weekly_candidates": [asdict(task) for task in selected_candidates],
                "total_estimated_time": self._calculate_total_time(selected_candidates),
                "time_available": time_available,
                "priority_distribution": self._analyze_priority_distribution(selected_candidates)
            }
            
        except Exception as e:
            logger.error(f"Error generating weekly candidates: {e}")
            return {
                "success": False,
                "error": str(e),
                "weekly_candidates": []
            }
    
    def _identify_priority_gaps(self, gaps: Dict[str, List[str]], coverage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify the most critical gaps based on business priorities"""
        priority_order = self.business_brain.get("priorities", {}).get("order", ["revenue", "retention", "systems", "brand"])
        
        # Map business priorities to business areas
        priority_mapping = {
            "revenue": ["sales", "marketing"],
            "retention": ["delivery", "operations"],
            "systems": ["operations", "product"],
            "brand": ["marketing", "product"]
        }
        
        priority_gaps = []
        
        for priority in priority_order:
            mapped_areas = priority_mapping.get(priority, [])
            for area in mapped_areas:
                if area in gaps and gaps[area]:
                    priority_gaps.append({
                        "priority": priority,
                        "area": area,
                        "missing_tasks": gaps[area][:3],  # Top 3 missing tasks
                        "coverage": coverage_analysis.get(area, {}).get("coverage_percentage", 0)
                    })
        
        return priority_gaps
    
    def _generate_gap_recommendations(self, gaps: Dict[str, List[str]], coverage_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on gap analysis"""
        recommendations = []
        
        # Find areas with lowest coverage
        low_coverage_areas = [
            area for area, analysis in coverage_analysis.items()
            if analysis["coverage_percentage"] < 50
        ]
        
        if low_coverage_areas:
            recommendations.append(f"Focus on {', '.join(low_coverage_areas)} - these areas have <50% task coverage")
        
        # Find completely missing areas
        zero_coverage_areas = [
            area for area, analysis in coverage_analysis.items()
            if analysis["coverage_percentage"] == 0
        ]
        
        if zero_coverage_areas:
            recommendations.append(f"Critical: {', '.join(zero_coverage_areas)} have no task coverage")
        
        # Revenue-focused recommendation
        revenue_areas = ["sales", "marketing"]
        revenue_gaps = sum(len(gaps.get(area, [])) for area in revenue_areas)
        if revenue_gaps > 3:
            recommendations.append("Revenue risk: Missing critical sales and marketing tasks")
        
        return recommendations
    
    def _generate_goal_specific_tasks(self, goal_title: str, goal_area: str, description: str, target_date: str) -> List[TaskSuggestion]:
        """Generate specific tasks to achieve a business goal"""
        tasks = []
        
        # Task templates based on goal area
        goal_task_templates = {
            "sales": [
                ("Identify target prospects for {goal}", "Research and list potential clients", "Medium", "2-3 hours"),
                ("Create outreach sequence for {goal}", "Develop email/call scripts", "High", "3-4 hours"),
                ("Set up tracking for {goal}", "Implement metrics and monitoring", "Medium", "1-2 hours")
            ],
            "marketing": [
                ("Develop content strategy for {goal}", "Plan content calendar and topics", "High", "2-3 hours"),
                ("Create lead magnet for {goal}", "Design downloadable resource", "Medium", "4-6 hours"),
                ("Set up measurement for {goal}", "Track engagement and conversions", "Medium", "1-2 hours")
            ],
            "delivery": [
                ("Optimize process for {goal}", "Streamline workflow and reduce bottlenecks", "High", "3-4 hours"),
                ("Create quality checklist for {goal}", "Document standards and requirements", "Medium", "2-3 hours"),
                ("Build client feedback system for {goal}", "Implement feedback collection", "Medium", "1-2 hours")
            ],
            "operations": [
                ("Set up automation for {goal}", "Identify and implement automated processes", "High", "4-6 hours"),
                ("Create reporting for {goal}", "Build dashboard and tracking", "Medium", "2-3 hours"),
                ("Document procedures for {goal}", "Create SOPs and guidelines", "Medium", "3-4 hours")
            ]
        }
        
        templates = goal_task_templates.get(goal_area.lower(), goal_task_templates["sales"])
        
        for template_title, template_desc, priority, effort in templates:
            task = TaskSuggestion(
                title=template_title.format(goal=goal_title[:30] + "..."),
                description=f"{template_desc} - Supporting goal: {goal_title}",
                area=BusinessArea(goal_area.lower() if goal_area.lower() in [e.value for e in BusinessArea] else "sales"),
                priority=priority,
                estimated_effort=effort,
                reasoning=f"Directly supports achieving: {goal_title}",
                acceptance_criteria=f"Complete {template_desc.lower()} with measurable outcomes",
                due_date_suggestion=target_date,
                dependencies=[],
                business_impact=f"Directly contributes to goal: {goal_title}"
            )
            tasks.append(task)
        
        return tasks
    
    def _generate_priority_area_tasks(self, priority: str, time_budget: int) -> List[TaskSuggestion]:
        """Generate tasks for a specific priority area"""
        # This would contain more sophisticated task generation logic
        # For now, return sample tasks
        
        task_templates = {
            "revenue": [
                TaskSuggestion(
                    title="Conduct 3 discovery calls this week",
                    description="Schedule and execute discovery calls with qualified prospects",
                    area=BusinessArea.SALES,
                    priority="High",
                    estimated_effort="6 hours",
                    reasoning="Direct revenue generation opportunity",
                    acceptance_criteria="Complete 3 discovery calls, document outcomes",
                    due_date_suggestion=self._calculate_due_date(5),
                    dependencies=[],
                    business_impact="Potential $15k+ pipeline addition"
                )
            ],
            "retention": [
                TaskSuggestion(
                    title="Create client check-in process",
                    description="Implement regular client satisfaction monitoring",
                    area=BusinessArea.DELIVERY,
                    priority="Medium",
                    estimated_effort="3 hours",
                    reasoning="Improves client retention and satisfaction",
                    acceptance_criteria="Document process and schedule first check-ins",
                    due_date_suggestion=self._calculate_due_date(7),
                    dependencies=[],
                    business_impact="Reduces churn, increases LTV"
                )
            ]
        }
        
        return task_templates.get(priority, [])
    
    def _identify_time_sensitive_opportunities(self) -> List[TaskSuggestion]:
        """Identify opportunities that are time-sensitive"""
        # This would integrate with external data sources in a real implementation
        return [
            TaskSuggestion(
                title="Prepare for Q4 planning cycle",
                description="Review Q3 performance and plan Q4 objectives",
                area=BusinessArea.OPERATIONS,
                priority="High",
                estimated_effort="4 hours",
                reasoning="End of quarter strategic planning opportunity",
                acceptance_criteria="Complete Q3 review and Q4 plan document",
                due_date_suggestion=self._calculate_due_date(14),
                dependencies=[],
                business_impact="Sets direction for next quarter growth"
            )
        ]
    
    def _calculate_task_priority_score(self, task: TaskSuggestion) -> float:
        """Calculate priority score for task ranking"""
        # Base score from priority level
        priority_scores = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
        base_score = priority_scores.get(task.priority, 2)
        
        # Business impact multiplier
        impact_multipliers = {
            BusinessArea.SALES: 1.5,
            BusinessArea.MARKETING: 1.3,
            BusinessArea.DELIVERY: 1.2,
            BusinessArea.OPERATIONS: 1.1,
            BusinessArea.FINANCE: 1.0,
            BusinessArea.PRODUCT: 1.0,
            BusinessArea.TEAM: 0.8
        }
        
        impact_multiplier = impact_multipliers.get(task.area, 1.0)
        
        # Effort efficiency (lower effort = higher score)
        effort_hours = self._parse_effort_hours(task.estimated_effort)
        effort_efficiency = max(1, 5 - effort_hours / 2)  # Favor smaller tasks
        
        final_score = base_score * impact_multiplier * effort_efficiency
        return round(final_score, 2)
    
    def _parse_effort_hours(self, effort_str: str) -> float:
        """Parse effort string to hours"""
        if not effort_str:
            return 3.0  # default
        
        # Extract numbers from strings like "2-3 hours", "4 hours", etc.
        import re
        numbers = re.findall(r'\d+', effort_str)
        if numbers:
            return float(numbers[0])  # Use first number
        return 3.0  # default
    
    def _select_optimal_task_mix(self, candidates: List[TaskSuggestion], time_budget: int) -> List[TaskSuggestion]:
        """Select optimal mix of tasks within time constraint"""
        selected = []
        used_time = 0
        
        for candidate in candidates:
            task_hours = self._parse_effort_hours(candidate.estimated_effort)
            if used_time + task_hours <= time_budget:
                selected.append(candidate)
                used_time += task_hours
        
        return selected
    
    def _calculate_total_time(self, tasks: List[TaskSuggestion]) -> int:
        """Calculate total estimated time for tasks"""
        return sum(self._parse_effort_hours(task.estimated_effort) for task in tasks)
    
    def _analyze_priority_distribution(self, tasks: List[TaskSuggestion]) -> Dict[str, int]:
        """Analyze distribution of tasks by priority and area"""
        distribution = {}
        for task in tasks:
            area = task.area.value
            distribution[area] = distribution.get(area, 0) + 1
        return distribution
    
    def _calculate_due_date(self, days_from_now: int) -> str:
        """Calculate due date string"""
        target_date = datetime.now() + timedelta(days=days_from_now)
        return target_date.strftime('%Y-%m-%d')
