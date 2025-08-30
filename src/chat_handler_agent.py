"""
Chat Handler Agent - Processes natural language requests to add tasks
Parses conversational input and extracts structured task information
"""
import os
import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class TaskIntent(Enum):
    """Different types of task-related intents"""
    CREATE_TASK = "create_task"
    SCHEDULE_TASK = "schedule_task"
    SET_REMINDER = "set_reminder"
    FOLLOW_UP = "follow_up"
    PROJECT_WORK = "project_work"
    RESEARCH_TASK = "research_task"
    COMMUNICATION_TASK = "communication_task"
    UNCLEAR_INTENT = "unclear_intent"


@dataclass
class ParsedTaskRequest:
    """Structured representation of a chat task request"""
    intent: TaskIntent
    title: str
    description: str
    priority: Optional[str]
    project: Optional[str]
    due_date: Optional[str]
    estimated_effort: Optional[str]
    tags: List[str]
    confidence_score: float
    extracted_entities: Dict[str, Any]
    raw_input: str


class ChatHandlerAgent:
    """Agent specialized in parsing natural language task requests"""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.entity_extractors = self._load_entity_extractors()
        self.priority_keywords = self._load_priority_keywords()
        self.effort_patterns = self._load_effort_patterns()
        
        logger.info("Chat Handler Agent initialized with NLP capabilities")
    
    def parse_task_request(self, user_input: str, context: Dict[str, Any] = None) -> ParsedTaskRequest:
        """Parse natural language input into structured task request"""
        try:
            context = context or {}
            
            # Clean and normalize input
            cleaned_input = self._clean_input(user_input)
            
            # Extract intent
            intent = self._extract_intent(cleaned_input)
            
            # Extract entities
            entities = self._extract_entities(cleaned_input)
            
            # Generate task title and description
            title, description = self._generate_title_and_description(cleaned_input, intent, entities)
            
            # Extract priority
            priority = self._extract_priority(cleaned_input)
            
            # Extract project/category
            project = self._extract_project(cleaned_input, context)
            
            # Extract due date
            due_date = self._extract_due_date(cleaned_input)
            
            # Extract effort estimate
            effort = self._extract_effort_estimate(cleaned_input)
            
            # Extract tags
            tags = self._extract_tags(cleaned_input)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(cleaned_input, entities)
            
            parsed_request = ParsedTaskRequest(
                intent=intent,
                title=title,
                description=description,
                priority=priority,
                project=project,
                due_date=due_date,
                estimated_effort=effort,
                tags=tags,
                confidence_score=confidence,
                extracted_entities=entities,
                raw_input=user_input
            )
            
            logger.info(f"Parsed task request: '{title}' (confidence: {confidence:.2f})")
            
            return parsed_request
            
        except Exception as e:
            logger.error(f"Error parsing task request: {e}")
            return ParsedTaskRequest(
                intent=TaskIntent.UNCLEAR_INTENT,
                title=user_input[:50] + "..." if len(user_input) > 50 else user_input,
                description=f"Raw input: {user_input}",
                priority="Medium",
                project=None,
                due_date=None,
                estimated_effort=None,
                tags=["chat-parsed"],
                confidence_score=0.3,
                extracted_entities={},
                raw_input=user_input
            )
    
    def create_task_from_chat(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a task from natural language chat input"""
        try:
            # Parse the request
            parsed_request = self.parse_task_request(user_input, context)
            
            # Convert to task creation format
            task_data = {
                "title": parsed_request.title,
                "description": parsed_request.description,
                "priority": parsed_request.priority or "Medium",
                "project": parsed_request.project,
                "due_date": parsed_request.due_date,
                "estimated_effort": parsed_request.estimated_effort or "2-3 hours",
                "tags": parsed_request.tags,
                "notes": f"Created from chat: {parsed_request.raw_input}"
            }
            
            # Add metadata
            metadata = {
                "source": "chat",
                "intent": parsed_request.intent.value,
                "confidence": parsed_request.confidence_score,
                "extracted_entities": parsed_request.extracted_entities,
                "parsing_timestamp": datetime.now().isoformat()
            }
            
            result = {
                "success": True,
                "task_data": task_data,
                "metadata": metadata,
                "parsed_request": asdict(parsed_request)
            }
            
            # Add warnings for low confidence
            if parsed_request.confidence_score < 0.6:
                result["warnings"] = [
                    f"Low confidence parsing (Score: {parsed_request.confidence_score:.2f})",
                    "Please review the generated task details"
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating task from chat: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_data": None
            }
    
    def suggest_task_improvements(self, parsed_request: ParsedTaskRequest) -> Dict[str, Any]:
        """Suggest improvements to a parsed task request"""
        try:
            suggestions = []
            
            # Title improvements
            if len(parsed_request.title) < 10:
                suggestions.append({
                    "type": "title",
                    "issue": "Title may be too short",
                    "suggestion": "Consider adding more descriptive details to the title"
                })
            
            if len(parsed_request.title) > 80:
                suggestions.append({
                    "type": "title", 
                    "issue": "Title may be too long",
                    "suggestion": "Consider shortening the title and moving details to description"
                })
            
            # Description improvements
            if not parsed_request.description or len(parsed_request.description) < 20:
                suggestions.append({
                    "type": "description",
                    "issue": "Description lacks detail",
                    "suggestion": "Add more context about what needs to be done and why"
                })
            
            # Priority improvements
            if not parsed_request.priority:
                suggestions.append({
                    "type": "priority",
                    "issue": "No priority set",
                    "suggestion": "Consider setting priority based on urgency and importance"
                })
            
            # Due date improvements
            if not parsed_request.due_date:
                suggestions.append({
                    "type": "due_date",
                    "issue": "No due date specified",
                    "suggestion": "Adding a target completion date helps with planning"
                })
            
            # Effort estimate improvements
            if not parsed_request.estimated_effort:
                suggestions.append({
                    "type": "effort",
                    "issue": "No effort estimate",
                    "suggestion": "Estimate how long this task will take (e.g., '2-3 hours')"
                })
            
            # Project/categorization improvements
            if not parsed_request.project:
                suggestions.append({
                    "type": "project",
                    "issue": "No project/category assigned",
                    "suggestion": "Consider categorizing this task (e.g., Marketing, Sales, Operations)"
                })
            
            return {
                "success": True,
                "suggestions": suggestions,
                "suggestion_count": len(suggestions),
                "overall_quality": "good" if len(suggestions) <= 2 else "needs_improvement"
            }
            
        except Exception as e:
            logger.error(f"Error generating task suggestions: {e}")
            return {
                "success": False,
                "error": str(e),
                "suggestions": []
            }
    
    def _clean_input(self, text: str) -> str:
        """Clean and normalize input text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common chat abbreviations
        replacements = {
            r'\bu\b': 'you',
            r'\br\b': 'are',
            r'\bur\b': 'your',
            r'\btmrw\b': 'tomorrow',
            r'\basap\b': 'as soon as possible',
            r'\betc\b': 'and so on'
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _extract_intent(self, text: str) -> TaskIntent:
        """Extract the primary intent from the text"""
        text_lower = text.lower()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return TaskIntent(intent)
        
        # Default intent based on common phrases
        if any(phrase in text_lower for phrase in ["need to", "should", "have to", "want to"]):
            return TaskIntent.CREATE_TASK
        elif any(phrase in text_lower for phrase in ["remind me", "don't forget", "remember to"]):
            return TaskIntent.SET_REMINDER
        elif any(phrase in text_lower for phrase in ["follow up", "check on", "get back to"]):
            return TaskIntent.FOLLOW_UP
        elif any(phrase in text_lower for phrase in ["research", "look into", "investigate"]):
            return TaskIntent.RESEARCH_TASK
        else:
            return TaskIntent.CREATE_TASK  # Default fallback
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract named entities and key phrases from text"""
        entities = {
            "people": [],
            "companies": [],
            "dates": [],
            "times": [],
            "amounts": [],
            "locations": [],
            "tools": [],
            "actions": []
        }
        
        # Extract people/names (capitalized words)
        people_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        entities["people"] = list(set(re.findall(people_pattern, text)))
        
        # Extract companies/organizations (common suffixes)
        company_pattern = r'\b[A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Ltd|Company|Co)\b'
        entities["companies"] = list(set(re.findall(company_pattern, text)))
        
        # Extract dates
        date_patterns = [
            r'\b(?:today|tomorrow|yesterday)\b',
            r'\b(?:next|this)\s+(?:week|month|quarter|year)\b',
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b'
        ]
        
        for pattern in date_patterns:
            entities["dates"].extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Extract times
        time_pattern = r'\b\d{1,2}:\d{2}(?:\s*(?:am|pm))?\b'
        entities["times"] = list(set(re.findall(time_pattern, text, re.IGNORECASE)))
        
        # Extract amounts/numbers
        amount_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:hours?|minutes?|days?|weeks?|months?)\b'
        entities["amounts"] = list(set(re.findall(amount_pattern, text, re.IGNORECASE)))
        
        # Extract action verbs
        action_pattern = r'\b(?:create|build|design|write|send|call|email|schedule|plan|review|analyze|research|update|fix|implement|deploy|test)\b'
        entities["actions"] = list(set(re.findall(action_pattern, text, re.IGNORECASE)))
        
        # Clean up empty lists
        entities = {k: v for k, v in entities.items() if v}
        
        return entities
    
    def _generate_title_and_description(self, text: str, intent: TaskIntent, entities: Dict[str, Any]) -> Tuple[str, str]:
        """Generate appropriate title and description from the input"""
        
        # Clean text for title generation
        text_clean = text.strip()
        
        # Generate title based on intent
        if intent == TaskIntent.CREATE_TASK:
            if text_clean.lower().startswith(("i need to", "i should", "i have to", "i want to")):
                title = text_clean[text_clean.lower().find(" to ") + 3:].strip()
                title = title.capitalize()
            else:
                title = text_clean
        elif intent == TaskIntent.SET_REMINDER:
            if "remind me to" in text_clean.lower():
                title = text_clean[text_clean.lower().find("remind me to") + 12:].strip()
                title = f"Reminder: {title.capitalize()}"
            else:
                title = f"Reminder: {text_clean}"
        elif intent == TaskIntent.FOLLOW_UP:
            if any(phrase in text_clean.lower() for phrase in ["follow up", "check on", "get back to"]):
                title = f"Follow up: {text_clean}"
            else:
                title = text_clean
        else:
            title = text_clean
        
        # Clean up title
        title = re.sub(r'^(task:?|todo:?|reminder:?)\s*', '', title, flags=re.IGNORECASE).strip()
        
        # Limit title length
        if len(title) > 80:
            title = title[:77] + "..."
        
        # Generate description
        description = f"Task created from chat input: {text}\n\n"
        
        if entities:
            description += "Extracted information:\n"
            for entity_type, values in entities.items():
                if values:
                    description += f"- {entity_type.title()}: {', '.join(str(v) for v in values)}\n"
        
        # Add intent-specific description details
        if intent == TaskIntent.RESEARCH_TASK:
            description += "\nThis appears to be a research task. Consider breaking it down into specific research questions and deliverables."
        elif intent == TaskIntent.COMMUNICATION_TASK:
            description += "\nThis involves communication with others. Make sure to include context and expected outcomes."
        elif intent == TaskIntent.PROJECT_WORK:
            description += "\nThis seems to be project-related work. Consider linking it to relevant project goals and milestones."
        
        return title, description.strip()
    
    def _extract_priority(self, text: str) -> Optional[str]:
        """Extract priority level from text"""
        text_lower = text.lower()
        
        # High priority indicators
        if any(word in text_lower for word in self.priority_keywords["high"]):
            return "High"
        
        # Critical priority indicators
        if any(word in text_lower for word in self.priority_keywords["critical"]):
            return "Critical"
        
        # Low priority indicators
        if any(word in text_lower for word in self.priority_keywords["low"]):
            return "Low"
        
        # Medium priority indicators (or default)
        if any(word in text_lower for word in self.priority_keywords["medium"]):
            return "Medium"
        
        return None  # Let system decide
    
    def _extract_project(self, text: str, context: Dict[str, Any]) -> Optional[str]:
        """Extract project/category from text"""
        text_lower = text.lower()
        
        # Check for explicit project mentions
        project_patterns = [
            r'for\s+(?:the\s+)?([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s+project',
            r'in\s+(?:the\s+)?([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s+(?:project|area)',
            r'project:\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',
            r'category:\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)?)'
        ]
        
        for pattern in project_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1).title()
        
        # Infer project from keywords
        project_keywords = {
            "Marketing": ["marketing", "content", "social media", "seo", "blog", "campaign", "brand"],
            "Sales": ["sales", "client", "prospect", "lead", "proposal", "discovery call", "pipeline"],
            "Development": ["code", "programming", "development", "build", "deploy", "technical", "api"],
            "Operations": ["operations", "process", "automation", "workflow", "system", "admin"],
            "Finance": ["finance", "budget", "invoice", "payment", "revenue", "expenses", "accounting"],
            "HR": ["team", "hire", "interview", "onboard", "employee", "staff", "recruitment"]
        }
        
        for project, keywords in project_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return project
        
        # Check context for current project
        if context and context.get("current_project"):
            return context["current_project"]
        
        return None
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text"""
        text_lower = text.lower()
        
        # Today/tomorrow
        if "today" in text_lower:
            return datetime.now().strftime('%Y-%m-%d')
        elif "tomorrow" in text_lower:
            return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # This/next week
        if "this week" in text_lower:
            days_until_friday = (4 - datetime.now().weekday()) % 7
            if days_until_friday == 0:
                days_until_friday = 7  # Next Friday if today is Friday
            return (datetime.now() + timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
        elif "next week" in text_lower:
            days_until_next_friday = (4 - datetime.now().weekday()) + 7
            return (datetime.now() + timedelta(days=days_until_next_friday)).strftime('%Y-%m-%d')
        
        # Specific dates
        date_patterns = [
            (r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b', lambda m: self._parse_date_match(m)),
            (r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})\b', lambda m: self._parse_month_day(m))
        ]
        
        for pattern, parser in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return parser(match)
        
        # Days of week
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        for day_name, day_num in weekdays.items():
            if day_name in text_lower:
                today = datetime.now()
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        return None
    
    def _extract_effort_estimate(self, text: str) -> Optional[str]:
        """Extract effort estimate from text"""
        text_lower = text.lower()
        
        # Check for explicit time estimates
        for pattern, estimate in self.effort_patterns.items():
            if re.search(pattern, text_lower):
                return estimate
        
        # Infer from complexity indicators
        if any(word in text_lower for word in ["quick", "simple", "easy", "small"]):
            return "1-2 hours"
        elif any(word in text_lower for word in ["complex", "difficult", "major", "big", "large"]):
            return "1-2 days"
        elif any(word in text_lower for word in ["research", "analyze", "investigate"]):
            return "2-4 hours"
        elif any(word in text_lower for word in ["create", "build", "develop", "design"]):
            return "4-8 hours"
        
        return None
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        tags = ["chat-created"]
        text_lower = text.lower()
        
        # Add intent-based tags
        if any(word in text_lower for word in ["urgent", "asap", "immediately"]):
            tags.append("urgent")
        
        if any(word in text_lower for word in ["research", "analyze", "investigate"]):
            tags.append("research")
        
        if any(word in text_lower for word in ["client", "customer", "prospect"]):
            tags.append("client-related")
        
        if any(word in text_lower for word in ["meeting", "call", "email", "communicate"]):
            tags.append("communication")
        
        if any(word in text_lower for word in ["follow up", "followup", "check on"]):
            tags.append("follow-up")
        
        return tags
    
    def _calculate_confidence(self, text: str, entities: Dict[str, Any]) -> float:
        """Calculate confidence score for parsing accuracy"""
        confidence_factors = []
        
        # Length factor (not too short, not too long)
        length = len(text.strip())
        if 10 <= length <= 200:
            confidence_factors.append(0.3)
        elif 5 <= length <= 300:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)
        
        # Grammar and structure factor
        if text.strip().endswith('.'):
            confidence_factors.append(0.1)
        
        # Entity extraction factor
        entity_count = sum(len(values) for values in entities.values())
        if entity_count >= 3:
            confidence_factors.append(0.3)
        elif entity_count >= 1:
            confidence_factors.append(0.2)
        
        # Clear action verb factor
        action_verbs = ["create", "build", "send", "call", "write", "schedule", "plan", "review"]
        if any(verb in text.lower() for verb in action_verbs):
            confidence_factors.append(0.2)
        
        # Specific details factor
        if any(indicator in text.lower() for indicator in ["by", "for", "with", "about", "regarding"]):
            confidence_factors.append(0.2)
        
        return min(1.0, sum(confidence_factors))
    
    def _parse_date_match(self, match) -> str:
        """Parse a date regex match into YYYY-MM-DD format"""
        try:
            if len(match.groups()) == 3:
                month, day, year = match.groups()
                if len(year) == 2:
                    year = "20" + year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
        return None
    
    def _parse_month_day(self, match) -> str:
        """Parse month name and day into YYYY-MM-DD format"""
        try:
            month_names = {
                "january": 1, "february": 2, "march": 3, "april": 4,
                "may": 5, "june": 6, "july": 7, "august": 8,
                "september": 9, "october": 10, "november": 11, "december": 12
            }
            
            month_name, day = match.groups()
            month_num = month_names.get(month_name.lower())
            
            if month_num:
                current_year = datetime.now().year
                return f"{current_year}-{month_num:02d}-{int(day):02d}"
        except:
            pass
        return None
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent recognition patterns"""
        return {
            "create_task": [
                r'\b(?:create|add|make|build|develop|design)\b',
                r'\b(?:i need to|i should|i have to|i want to)\b',
                r'\b(?:task|todo|work on)\b'
            ],
            "schedule_task": [
                r'\b(?:schedule|plan|set up|arrange)\b',
                r'\b(?:meeting|appointment|call|session)\b'
            ],
            "set_reminder": [
                r'\b(?:remind me|don\'t forget|remember to)\b',
                r'\b(?:reminder|alert|notification)\b'
            ],
            "follow_up": [
                r'\b(?:follow up|followup|check on|get back to)\b',
                r'\b(?:touch base|reconnect|circle back)\b'
            ],
            "research_task": [
                r'\b(?:research|investigate|analyze|look into|explore)\b',
                r'\b(?:find out|learn about|study)\b'
            ],
            "communication_task": [
                r'\b(?:email|call|message|contact|reach out)\b',
                r'\b(?:communicate|discuss|talk to|speak with)\b'
            ]
        }
    
    def _load_entity_extractors(self) -> Dict[str, str]:
        """Load entity extraction patterns"""
        return {
            "person": r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            "company": r'\b[A-Z][a-zA-Z\s]+(?:Inc|Corp|LLC|Ltd|Company|Co)\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "url": r'https?://[^\s]+',
            "currency": r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
        }
    
    def _load_priority_keywords(self) -> Dict[str, List[str]]:
        """Load priority level keywords"""
        return {
            "critical": ["critical", "emergency", "urgent", "asap", "immediately", "now"],
            "high": ["high", "important", "priority", "soon", "quickly"],
            "medium": ["medium", "normal", "regular", "standard"],
            "low": ["low", "later", "eventually", "when possible", "nice to have"]
        }
    
    def _load_effort_patterns(self) -> Dict[str, str]:
        """Load effort estimation patterns"""
        return {
            r'\b(\d+)\s*(?:minute|min)s?\b': lambda m: f"{m.group(1)} minutes",
            r'\b(\d+)\s*(?:hour|hr)s?\b': lambda m: f"{m.group(1)} hours",
            r'\b(\d+)\s*(?:day|d)s?\b': lambda m: f"{m.group(1)} days",
            r'\b(\d+)\s*(?:week|wk)s?\b': lambda m: f"{m.group(1)} weeks",
            r'\bquick\b': "30 minutes",
            r'\bshort\b': "1 hour",
            r'\blong\b': "4-6 hours",
            r'\bmajor\b': "1-2 days"
        }
