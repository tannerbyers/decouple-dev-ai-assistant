"""
Comprehensive Configuration Manager for OpsBrain AI Assistant
Handles all application settings, prompts, and configurations via database storage.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ConfigCategory(Enum):
    """Configuration categories."""
    GENERAL = "general"
    API = "api"
    SLACK = "slack"
    NOTION = "notion"
    OPENAI = "openai"
    TRELLO = "trello"
    DASHBOARD = "dashboard"
    PROMPTS = "prompts"
    SCHEDULING = "scheduling"
    FEATURES = "features"

@dataclass
class ConfigItem:
    """Configuration item with metadata."""
    key: str
    value: Any
    category: ConfigCategory = ConfigCategory.GENERAL
    description: str = ""
    is_sensitive: bool = False
    value_type: str = "string"  # string, boolean, integer, json, list
    default_value: Any = None
    validation_rules: Dict = field(default_factory=dict)

class ConfigManager:
    """Manages all application configuration through database storage."""
    
    def __init__(self, database_manager = None):
        # Import here to avoid circular imports
        if database_manager is None:
            from .database import db_manager
            self.db = db_manager
        else:
            self.db = database_manager
        self._config_cache = {}
        self._initialize_default_configs()
    
    def _initialize_default_configs(self) -> None:
        """Initialize default configurations if they don't exist."""
        default_configs = [
            # General Settings
            ConfigItem("app_name", "OpsBrain AI Assistant", ConfigCategory.GENERAL, "Application name"),
            ConfigItem("app_version", "2.0.0", ConfigCategory.GENERAL, "Application version"),
            ConfigItem("debug_mode", False, ConfigCategory.GENERAL, "Enable debug logging", value_type="boolean"),
            ConfigItem("max_thread_context_messages", 10, ConfigCategory.GENERAL, "Maximum messages in thread context", value_type="integer"),
            ConfigItem("thread_cleanup_hours", 24, ConfigCategory.GENERAL, "Hours before cleaning old threads", value_type="integer"),
            
            # API Settings
            ConfigItem("request_timeout", 30, ConfigCategory.API, "Default API request timeout", value_type="integer"),
            ConfigItem("max_concurrent_requests", 10, ConfigCategory.API, "Maximum concurrent API requests", value_type="integer"),
            ConfigItem("retry_attempts", 3, ConfigCategory.API, "Number of retry attempts for failed requests", value_type="integer"),
            
            # Slack Settings
            ConfigItem("slack_response_timeout", 3, ConfigCategory.SLACK, "Slack response timeout in seconds", value_type="integer"),
            ConfigItem("slack_enable_threading", True, ConfigCategory.SLACK, "Enable threaded conversations", value_type="boolean"),
            ConfigItem("slack_default_channel", None, ConfigCategory.SLACK, "Default Slack channel for notifications"),
            ConfigItem("slack_enable_reactions", True, ConfigCategory.SLACK, "Enable emoji reactions", value_type="boolean"),
            
            # OpenAI Settings
            ConfigItem("openai_model", "gpt-4", ConfigCategory.OPENAI, "Default OpenAI model"),
            ConfigItem("openai_max_tokens", 1000, ConfigCategory.OPENAI, "Maximum tokens per response", value_type="integer"),
            ConfigItem("openai_temperature", 0.7, ConfigCategory.OPENAI, "OpenAI temperature setting", value_type="number"),
            ConfigItem("openai_enable_streaming", False, ConfigCategory.OPENAI, "Enable streaming responses", value_type="boolean"),
            
            # Notion Settings
            ConfigItem("notion_timeout", 30, ConfigCategory.NOTION, "Notion API timeout", value_type="integer"),
            ConfigItem("notion_max_page_size", 100, ConfigCategory.NOTION, "Maximum items per Notion query", value_type="integer"),
            ConfigItem("notion_enable_caching", True, ConfigCategory.NOTION, "Enable Notion response caching", value_type="boolean"),
            
            # Dashboard Settings
            ConfigItem("dashboard_weekly_hours", 5, ConfigCategory.DASHBOARD, "Weekly hours available", value_type="integer"),
            ConfigItem("dashboard_max_weekly_hours", 20, ConfigCategory.DASHBOARD, "Maximum weekly hours", value_type="integer"),
            ConfigItem("dashboard_auto_refresh", 300, ConfigCategory.DASHBOARD, "Auto refresh interval in seconds", value_type="integer"),
            ConfigItem("dashboard_theme", "light", ConfigCategory.DASHBOARD, "Dashboard theme (light/dark)"),
            
            # Feature Flags
            ConfigItem("enable_ceo_mode", True, ConfigCategory.FEATURES, "Enable CEO-focused responses", value_type="boolean"),
            ConfigItem("enable_analytics", True, ConfigCategory.FEATURES, "Enable analytics tracking", value_type="boolean"),
            ConfigItem("enable_performance_monitoring", True, ConfigCategory.FEATURES, "Track performance metrics", value_type="boolean"),
            ConfigItem("enable_auto_cleanup", True, ConfigCategory.FEATURES, "Auto-cleanup old data", value_type="boolean"),
            ConfigItem("enable_advanced_prompts", True, ConfigCategory.FEATURES, "Use advanced AI prompts", value_type="boolean"),
            
            # Scheduling Settings
            ConfigItem("schedule_weekly_plan", True, ConfigCategory.SCHEDULING, "Auto-generate weekly plans", value_type="boolean"),
            ConfigItem("schedule_midweek_nudge", True, ConfigCategory.SCHEDULING, "Send midweek check-ins", value_type="boolean"),
            ConfigItem("schedule_friday_retro", True, ConfigCategory.SCHEDULING, "Generate Friday retrospectives", value_type="boolean"),
            ConfigItem("schedule_monday_time", "09:00", ConfigCategory.SCHEDULING, "Monday weekly plan time"),
            ConfigItem("schedule_wednesday_time", "14:00", ConfigCategory.SCHEDULING, "Wednesday nudge time"),
            ConfigItem("schedule_friday_time", "17:00", ConfigCategory.SCHEDULING, "Friday retro time"),
        ]
        
        # Insert defaults if they don't exist
        for config in default_configs:
            existing = self.db.get_config(config.key)
            if existing is None:
                self.set_config(config.key, config.value, config.category.value, config.description, config.is_sensitive)
        
        self._initialize_default_prompts()
    
    def _initialize_default_prompts(self) -> None:
        """Initialize default AI prompts."""
        default_prompts = {
            "ceo_system_prompt": """You are OpsBrain, a CEO-level AI assistant. You think and respond like a strategic executive focused on revenue, efficiency, and high-impact decisions.

RESPONSE STYLE:
- Be direct and action-oriented
- Focus on business impact and ROI
- Prioritize revenue-generating activities
- Identify and eliminate inefficiencies
- Maximum 2 sentences unless complex strategy required
- No bullet points or long explanations

CORE PRINCIPLES:
- Time is money - every task should drive revenue or efficiency
- Delegate non-strategic work
- Focus on high-leverage activities only
- Question everything that doesn't directly impact goals""",

            "task_analysis_prompt": """Analyze this request for task creation or management:

Request: {user_text}
Current Tasks: {task_count}

Identify:
1. Request type (create_tasks, update_status, planning, analysis)
2. Business area (sales, delivery, product, financial, team, process)
3. Priority level (high, medium, low)
4. Specific actions needed

Respond with structured analysis and recommended actions.""",

            "weekly_plan_prompt": """Generate a focused weekly plan for a CEO based on:

High Priority Tasks: {high_priority_tasks}
Business Goals: {active_goals}
Weekly Hours Available: {weekly_hours}

Create a strategic weekly plan that:
- Prioritizes revenue-generating activities
- Balances strategic and operational tasks
- Identifies key outcomes for the week
- Suggests time blocks for different activities

Format as actionable weekly schedule.""",

            "midweek_nudge_prompt": """Create a midweek check-in message based on:

This Week's Plan: {weekly_plan}
Completed Tasks: {completed_tasks}
Remaining Tasks: {remaining_tasks}

Generate a brief CEO-style midweek nudge that:
- Acknowledges progress made
- Refocuses on critical remaining items
- Suggests adjustments if needed
- Motivates for strong finish""",

            "friday_retro_prompt": """Generate a Friday retrospective based on:

Weekly Goals: {weekly_goals}
Completed Tasks: {completed_count}
Total Tasks: {total_tasks}
Key Achievements: {achievements}

Create a CEO-focused retrospective that:
- Celebrates wins and progress
- Identifies lessons learned
- Notes areas for improvement
- Sets context for next week's planning""",

            "help_response": """🎯 **OpsBrain CEO Assistant Commands:**

**Task Management:**
- "Generate comprehensive tasks" - Create full task backlog
- "Show high priority tasks" - Focus on critical items
- "Update task status" - Mark tasks complete/in-progress

**Planning & Strategy:**
- "Generate weekly plan" - Strategic weekly planning
- "Midweek check-in" - Progress review and adjustments
- "Friday retrospective" - Week summary and insights

**Business Goals:**
- "Show active goals" - Current business objectives
- "Create new goal" - Add strategic objective
- "Goal progress update" - Update goal status

**Quick Actions:**
- "/help" - Show this help
- "/dashboard" - View CEO dashboard
- "/status" - System status check

💡 **CEO Focus:** I prioritize revenue impact, efficiency, and strategic outcomes."""
        }
        
        for prompt_key, prompt_text in default_prompts.items():
            existing = self.db.get_config(prompt_key)
            if existing is None:
                self.set_config(prompt_key, prompt_text, ConfigCategory.PROMPTS.value, f"AI prompt: {prompt_key}")
    
    # Core Configuration Methods
    def get_config(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """Get configuration value with optional caching."""
        if use_cache and key in self._config_cache:
            return self._config_cache[key]
        
        value = self.db.get_config(key, str(default) if default is not None else None)
        
        if value is not None:
            # Try to parse as JSON first, then return as string
            try:
                parsed_value = json.loads(value)
                if use_cache:
                    self._config_cache[key] = parsed_value
                return parsed_value
            except (json.JSONDecodeError, TypeError):
                if use_cache:
                    self._config_cache[key] = value
                return value
        
        return default
    
    def set_config(self, key: str, value: Any, category: str = "general", 
                   description: str = "", is_sensitive: bool = False) -> None:
        """Set configuration value."""
        # Convert value to string for storage
        if isinstance(value, (dict, list)):
            str_value = json.dumps(value)
        elif isinstance(value, bool):
            str_value = json.dumps(value)  # Store as JSON boolean
        else:
            str_value = str(value)
        
        self.db.set_config(key, str_value, category, description, is_sensitive)
        
        # Update cache
        self._config_cache[key] = value
        
        logger.info(f"Configuration updated: {key} in category {category}")
    
    def get_category_configs(self, category: Union[str, ConfigCategory]) -> Dict[str, Any]:
        """Get all configurations for a category."""
        if isinstance(category, ConfigCategory):
            category = category.value
        
        raw_configs = self.db.get_configs_by_category(category)
        configs = {}
        
        for key, value in raw_configs.items():
            try:
                configs[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                configs[key] = value
        
        return configs
    
    def delete_config(self, key: str) -> bool:
        """Delete configuration."""
        success = self.db.delete_config(key)
        if success and key in self._config_cache:
            del self._config_cache[key]
        return success
    
    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._config_cache.clear()
    
    # Specialized Configuration Methods
    def get_slack_config(self) -> Dict[str, Any]:
        """Get all Slack-related configurations."""
        return self.get_category_configs(ConfigCategory.SLACK)
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get all OpenAI-related configurations."""
        return self.get_category_configs(ConfigCategory.OPENAI)
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get all dashboard-related configurations."""
        return self.get_category_configs(ConfigCategory.DASHBOARD)
    
    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """Get AI prompt with variable substitution."""
        prompt_template = self.get_config(prompt_key, "")
        
        if kwargs:
            try:
                return prompt_template.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing variable {e} in prompt {prompt_key}")
                return prompt_template
        
        return prompt_template
    
    def update_prompt(self, prompt_key: str, prompt_text: str, description: str = "") -> None:
        """Update AI prompt."""
        self.set_config(prompt_key, prompt_text, ConfigCategory.PROMPTS.value, description)
    
    # Feature Flag Methods
    def is_feature_enabled(self, feature_key: str) -> bool:
        """Check if a feature is enabled."""
        return self.get_config(feature_key, False)
    
    def enable_feature(self, feature_key: str, description: str = "") -> None:
        """Enable a feature flag."""
        self.set_config(feature_key, True, ConfigCategory.FEATURES.value, description)
    
    def disable_feature(self, feature_key: str) -> None:
        """Disable a feature flag."""
        self.set_config(feature_key, False, ConfigCategory.FEATURES.value)
    
    # Bulk Configuration Methods
    def export_configs(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Export configurations as JSON."""
        if category:
            return self.get_category_configs(category)
        
        all_configs = {}
        for cat in ConfigCategory:
            cat_configs = self.get_category_configs(cat)
            if cat_configs:
                all_configs[cat.value] = cat_configs
        
        return all_configs
    
    def import_configs(self, configs: Dict[str, Any], overwrite: bool = False) -> int:
        """Import configurations from JSON. Returns count of imported configs."""
        imported_count = 0
        
        for category, category_configs in configs.items():
            if not isinstance(category_configs, dict):
                continue
            
            for key, value in category_configs.items():
                existing = self.db.get_config(key)
                if existing is None or overwrite:
                    self.set_config(key, value, category)
                    imported_count += 1
        
        logger.info(f"Imported {imported_count} configurations")
        return imported_count
    
    def validate_config(self, key: str, value: Any) -> Tuple[bool, str]:
        """Validate configuration value. Returns (is_valid, error_message)."""
        # Add validation logic here based on key patterns or validation rules
        # For now, basic validation
        
        if key.endswith('_timeout') or key.endswith('_hours'):
            try:
                num_value = float(value)
                if num_value < 0:
                    return False, "Value must be positive"
            except (ValueError, TypeError):
                return False, "Value must be a number"
        
        if key.endswith('_enabled') or key.startswith('enable_'):
            if not isinstance(value, bool):
                return False, "Value must be boolean"
        
        return True, ""
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration system information."""
        info = {}
        
        for category in ConfigCategory:
            cat_configs = self.get_category_configs(category)
            info[category.value] = {
                'count': len(cat_configs),
                'keys': list(cat_configs.keys())
            }
        
        info['total_configs'] = sum(cat['count'] for cat in info.values())
        info['cache_size'] = len(self._config_cache)
        
        return info

# Global configuration manager instance
config_manager = ConfigManager()
