"""Slack API interactions for message handling."""
import requests
import logging
from .config import config

logger = logging.getLogger(__name__)

class SlackService:
    """Service for interacting with Slack API."""
    
    def __init__(self):
        self.base_url = "https://slack.com/api/"
        self.headers = {
            "Authorization": f"Bearer {config.slack_bot_token}",
            "Content-type": "application/json"
        }
    
    def post_message(self, channel: str, text: str) - bool:
        """Post a message to a Slack channel."""
        try:
            response = requests.post(
                f"{self.base_url}chat.postMessage",
                headers=self.headers,
                json={"channel": channel, "text": text},
                timeout=10
            )
            if not response.ok:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send message to Slack: {e}")
            return False

# Singleton instance
slack_service = SlackService()

