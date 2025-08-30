"""
Mock Discovery Agent - Simple implementation for testing
This provides basic discovery functionality without full dependencies
"""
import logging
import uuid
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)


class DiscoveryAgent:
    """Mock discovery agent for finding information and resources"""
    
    def __init__(self):
        logger.info("Mock DiscoveryAgent initialized")
        self.mock_data = {
            "users": [
                {"id": "user-1", "name": "John Doe", "email": "john@example.com", "role": "Sales Manager"},
                {"id": "user-2", "name": "Jane Smith", "email": "jane@example.com", "role": "Marketing Director"},
                {"id": "user-3", "name": "Bob Wilson", "email": "bob@example.com", "role": "Operations Lead"}
            ],
            "projects": [
                {"id": "proj-1", "name": "Q1 Sales Campaign", "status": "active", "lead": "John Doe"},
                {"id": "proj-2", "name": "Product Launch", "status": "planning", "lead": "Jane Smith"},
                {"id": "proj-3", "name": "Infrastructure Upgrade", "status": "active", "lead": "Bob Wilson"}
            ],
            "resources": [
                {"id": "res-1", "type": "document", "title": "Sales Playbook", "url": "https://company.com/sales-playbook"},
                {"id": "res-2", "type": "tool", "title": "CRM System", "url": "https://company.com/crm"},
                {"id": "res-3", "type": "document", "title": "Marketing Guidelines", "url": "https://company.com/marketing-guide"}
            ]
        }
    
    def search_users(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for users based on query and filters"""
        try:
            logger.info(f"Mock: Searching users with query '{query}'")
            
            # Simple search in user names and roles
            results = []
            query_lower = query.lower()
            
            for user in self.mock_data["users"]:
                if (query_lower in user["name"].lower() or 
                    query_lower in user["role"].lower() or
                    query_lower in user["email"].lower()):
                    results.append(user)
            
            # Apply role filter if provided
            if filters and filters.get("role"):
                role_filter = filters["role"].lower()
                results = [u for u in results if role_filter in u["role"].lower()]
            
            return {
                "success": True,
                "users": results,
                "total_count": len(results),
                "query": query,
                "filters": filters or {}
            }
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return {
                "success": False,
                "error": str(e),
                "users": []
            }
    
    def search_projects(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for projects based on query and filters"""
        try:
            logger.info(f"Mock: Searching projects with query '{query}'")
            
            results = []
            query_lower = query.lower()
            
            for project in self.mock_data["projects"]:
                if (query_lower in project["name"].lower() or 
                    query_lower in project["status"].lower() or
                    query_lower in project["lead"].lower()):
                    results.append(project)
            
            # Apply status filter if provided
            if filters and filters.get("status"):
                status_filter = filters["status"].lower()
                results = [p for p in results if p["status"].lower() == status_filter]
            
            return {
                "success": True,
                "projects": results,
                "total_count": len(results),
                "query": query,
                "filters": filters or {}
            }
            
        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            return {
                "success": False,
                "error": str(e),
                "projects": []
            }
    
    def search_resources(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for resources based on query and filters"""
        try:
            logger.info(f"Mock: Searching resources with query '{query}'")
            
            results = []
            query_lower = query.lower()
            
            for resource in self.mock_data["resources"]:
                if (query_lower in resource["title"].lower() or 
                    query_lower in resource["type"].lower()):
                    results.append(resource)
            
            # Apply type filter if provided
            if filters and filters.get("type"):
                type_filter = filters["type"].lower()
                results = [r for r in results if r["type"].lower() == type_filter]
            
            return {
                "success": True,
                "resources": results,
                "total_count": len(results),
                "query": query,
                "filters": filters or {}
            }
            
        except Exception as e:
            logger.error(f"Error searching resources: {e}")
            return {
                "success": False,
                "error": str(e),
                "resources": []
            }
    
    def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific user"""
        try:
            logger.info(f"Mock: Getting details for user {user_id}")
            
            user = next((u for u in self.mock_data["users"] if u["id"] == user_id), None)
            
            if user:
                # Add some additional mock details
                detailed_user = user.copy()
                detailed_user.update({
                    "department": "Sales" if "Sales" in user["role"] else "Marketing" if "Marketing" in user["role"] else "Operations",
                    "manager": "CEO",
                    "start_date": "2023-01-01",
                    "skills": ["Communication", "Leadership", "Strategy"]
                })
                
                return {
                    "success": True,
                    "user": detailed_user
                }
            else:
                return {
                    "success": False,
                    "error": f"User with ID {user_id} not found"
                }
                
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_project_details(self, project_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific project"""
        try:
            logger.info(f"Mock: Getting details for project {project_id}")
            
            project = next((p for p in self.mock_data["projects"] if p["id"] == project_id), None)
            
            if project:
                # Add some additional mock details
                detailed_project = project.copy()
                detailed_project.update({
                    "start_date": "2024-01-01",
                    "end_date": "2024-03-31",
                    "budget": "$50,000",
                    "team_size": 5,
                    "description": f"This is the {project['name']} project focusing on achieving business objectives."
                })
                
                return {
                    "success": True,
                    "project": detailed_project
                }
            else:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found"
                }
                
        except Exception as e:
            logger.error(f"Error getting project details: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def discover_related_items(self, item_type: str, item_id: str) -> Dict[str, Any]:
        """Discover items related to a specific item"""
        try:
            logger.info(f"Mock: Discovering items related to {item_type} {item_id}")
            
            # Mock relationship discovery
            related_items = []
            
            if item_type == "user":
                # Find projects led by this user
                user = next((u for u in self.mock_data["users"] if u["id"] == item_id), None)
                if user:
                    related_projects = [p for p in self.mock_data["projects"] if p["lead"] == user["name"]]
                    related_items.extend([{"type": "project", "item": p} for p in related_projects])
                    
            elif item_type == "project":
                # Find users associated with this project
                project = next((p for p in self.mock_data["projects"] if p["id"] == item_id), None)
                if project:
                    lead_user = next((u for u in self.mock_data["users"] if u["name"] == project["lead"]), None)
                    if lead_user:
                        related_items.append({"type": "user", "item": lead_user})
            
            return {
                "success": True,
                "related_items": related_items,
                "total_count": len(related_items),
                "source_type": item_type,
                "source_id": item_id
            }
            
        except Exception as e:
            logger.error(f"Error discovering related items: {e}")
            return {
                "success": False,
                "error": str(e),
                "related_items": []
            }
    
    def analyze_business_gaps(self, current_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze gaps in current business task coverage"""
        try:
            logger.info(f"Mock: Analyzing business gaps for {len(current_tasks)} current tasks")
            
            # Define business areas and expected tasks
            business_areas = {
                "sales": [
                    "Customer outreach", "Lead qualification", "Sales calls", "Proposal preparation",
                    "CRM maintenance", "Sales reporting"
                ],
                "marketing": [
                    "Content creation", "Social media management", "Email campaigns", "SEO optimization",
                    "Market research", "Brand management"
                ],
                "operations": [
                    "Process documentation", "Quality assurance", "System maintenance", "Data backup",
                    "Team meetings", "Performance monitoring"
                ],
                "finance": [
                    "Invoice processing", "Budget planning", "Financial reporting", "Tax preparation",
                    "Cash flow analysis", "Expense tracking"
                ]
            }
            
            # Analyze coverage for each business area
            gaps_by_area = {}
            coverage_scores = {}
            
            for area, expected_tasks in business_areas.items():
                # Check how many expected tasks are covered by current tasks
                covered_tasks = []
                uncovered_tasks = []
                
                for expected_task in expected_tasks:
                    # Simple keyword matching to see if task is covered
                    is_covered = any(
                        any(keyword in task.get("title", "").lower() or 
                            keyword in task.get("description", "").lower()
                            for keyword in expected_task.lower().split())
                        for task in current_tasks
                    )
                    
                    if is_covered:
                        covered_tasks.append(expected_task)
                    else:
                        uncovered_tasks.append(expected_task)
                
                gaps_by_area[area] = uncovered_tasks
                coverage_scores[area] = len(covered_tasks) / len(expected_tasks) if expected_tasks else 1.0
            
            # Calculate overall coverage
            total_expected = sum(len(tasks) for tasks in business_areas.values())
            total_gaps = sum(len(gaps) for gaps in gaps_by_area.values())
            overall_coverage = (total_expected - total_gaps) / total_expected if total_expected > 0 else 1.0
            
            return {
                "success": True,
                "gaps_by_area": gaps_by_area,
                "coverage_scores": coverage_scores,
                "overall_coverage": overall_coverage,
                "total_gaps": total_gaps,
                "recommendations": self._generate_gap_recommendations(gaps_by_area)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing business gaps: {e}")
            return {
                "success": False,
                "error": str(e),
                "gaps_by_area": {}
            }
    
    def discover_missing_foundations(self) -> Dict[str, Any]:
        """Discover foundational tasks that should be in place"""
        try:
            logger.info("Mock: Discovering missing foundational tasks")
            
            foundational_tasks = [
                {
                    "title": "Set up daily review routine",
                    "description": "Establish a daily habit of reviewing tasks and priorities",
                    "category": "productivity",
                    "priority": "High",
                    "estimated_effort": "15 minutes daily"
                },
                {
                    "title": "Create customer contact database",
                    "description": "Organize all customer and prospect information in a central system",
                    "category": "sales",
                    "priority": "High",
                    "estimated_effort": "2 hours"
                },
                {
                    "title": "Implement backup system",
                    "description": "Set up automated backups for important business data",
                    "category": "operations",
                    "priority": "Medium",
                    "estimated_effort": "3 hours"
                },
                {
                    "title": "Document key business processes",
                    "description": "Create documentation for critical business workflows",
                    "category": "operations",
                    "priority": "Medium",
                    "estimated_effort": "4 hours"
                },
                {
                    "title": "Set up financial tracking system",
                    "description": "Implement system for tracking income, expenses, and cash flow",
                    "category": "finance",
                    "priority": "High",
                    "estimated_effort": "3 hours"
                }
            ]
            
            return {
                "success": True,
                "foundational_tasks": foundational_tasks,
                "total_count": len(foundational_tasks),
                "categories": list(set(task["category"] for task in foundational_tasks))
            }
            
        except Exception as e:
            logger.error(f"Error discovering foundational tasks: {e}")
            return {
                "success": False,
                "error": str(e),
                "foundational_tasks": []
            }
    
    def generate_weekly_task_candidates(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate task candidates for weekly planning"""
        try:
            logger.info("Mock: Generating weekly task candidates")
            
            # Mock weekly task candidates based on different business areas
            weekly_candidates = [
                {
                    "title": "Reach out to 5 potential customers",
                    "description": "Contact prospects from recent inquiries and warm leads",
                    "area": "sales",
                    "priority": "High",
                    "estimated_effort": "3 hours",
                    "due_date_suggestion": "End of week",
                    "business_impact": "Revenue generation"
                },
                {
                    "title": "Create content for next week's social media",
                    "description": "Develop and schedule social media posts for the upcoming week",
                    "area": "marketing",
                    "priority": "Medium",
                    "estimated_effort": "2 hours",
                    "due_date_suggestion": "Friday",
                    "business_impact": "Brand awareness"
                },
                {
                    "title": "Review and update project timelines",
                    "description": "Assess current project progress and adjust deadlines as needed",
                    "area": "operations",
                    "priority": "Medium",
                    "estimated_effort": "1.5 hours",
                    "due_date_suggestion": "Mid-week",
                    "business_impact": "Operational efficiency"
                },
                {
                    "title": "Prepare weekly financial summary",
                    "description": "Compile revenue, expenses, and cash flow data for the week",
                    "area": "finance",
                    "priority": "Medium",
                    "estimated_effort": "1 hour",
                    "due_date_suggestion": "Friday",
                    "business_impact": "Financial visibility"
                },
                {
                    "title": "Plan and schedule team check-ins",
                    "description": "Coordinate with team members and schedule necessary meetings",
                    "area": "operations",
                    "priority": "Low",
                    "estimated_effort": "45 minutes",
                    "due_date_suggestion": "Monday",
                    "business_impact": "Team coordination"
                }
            ]
            
            # Calculate total time and priority distribution
            total_time = sum(float(task["estimated_effort"].split()[0]) for task in weekly_candidates)
            priority_distribution = {
                "High": len([t for t in weekly_candidates if t["priority"] == "High"]),
                "Medium": len([t for t in weekly_candidates if t["priority"] == "Medium"]),
                "Low": len([t for t in weekly_candidates if t["priority"] == "Low"])
            }
            
            return {
                "success": True,
                "weekly_candidates": weekly_candidates,
                "total_candidates": len(weekly_candidates),
                "total_estimated_time": total_time,
                "time_available": context.get("available_hours", 40) if context else 40,
                "priority_distribution": priority_distribution,
                "areas_covered": list(set(task["area"] for task in weekly_candidates))
            }
            
        except Exception as e:
            logger.error(f"Error generating weekly task candidates: {e}")
            return {
                "success": False,
                "error": str(e),
                "weekly_candidates": []
            }
    
    def _generate_gap_recommendations(self, gaps_by_area: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on identified gaps"""
        recommendations = []
        
        for area, gaps in gaps_by_area.items():
            if gaps:
                # Create a high-level recommendation for each area with gaps
                priority = "High" if len(gaps) > 3 else "Medium" if len(gaps) > 1 else "Low"
                
                recommendations.append({
                    "area": area,
                    "priority": priority,
                    "gap_count": len(gaps),
                    "recommendation": f"Focus on {area} tasks - {len(gaps)} key activities are missing",
                    "top_missing_tasks": gaps[:3]  # Show top 3 missing tasks
                })
        
        return sorted(recommendations, key=lambda x: len(x["top_missing_tasks"]), reverse=True)
