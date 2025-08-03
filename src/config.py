"""Configuration management for the AI assistant."""
import os
from typing import Optional

class Config:
    """Application configuration from environment variables."""
    
    def __init__(self):
        self.slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.notion_api_key = os.getenv("NOTION_API_KEY")
        self.notion_db_id = os.getenv("NOTION_DB_ID")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.port = int(os.getenv("PORT", "8000"))
        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    def validate_required_vars(self) -> Optional[str]:
        """Check if all required environment variables are set."""
        required_vars = [
            ("SLACK_BOT_TOKEN", self.slack_bot_token),
            ("SLACK_SIGNING_SECRET", self.slack_signing_secret),
            ("NOTION_API_KEY", self.notion_api_key),
            ("NOTION_DB_ID", self.notion_db_id),
            ("OPENAI_API_KEY", self.openai_api_key)
        ]
        
        missing = [name for name, value in required_vars if not value]
        
        if missing:
            return f"Missing required environment variables: {', '.join(missing)}"
        return None
    
    @property
    def is_configured(self) -> bool:
        """Check if all required configuration is present."""
        return self.validate_required_vars() is None

# Global config instance
config = Config()
