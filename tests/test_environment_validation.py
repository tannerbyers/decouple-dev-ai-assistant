import os
import pytest
import sys
from unittest.mock import patch
import importlib

class TestEnvironmentVariableValidation:
    """Test that required environment variables are properly validated."""
    
    def test_missing_all_env_vars_raises_error(self):
        """Test that missing all environment variables raises ValueError."""
        # Clear all required env vars and disable TEST_MODE
        env_vars = {
            'TEST_MODE': 'false'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Remove main from modules if it exists
            if 'main' in sys.modules:
                del sys.modules['main']
            
            with pytest.raises(ValueError) as exc_info:
                import main
            
            error_msg = str(exc_info.value)
            assert "Missing required environment variables" in error_msg
            assert "SLACK_BOT_TOKEN" in error_msg
            assert "NOTION_API_KEY" in error_msg
    
    def test_missing_some_env_vars_raises_error(self):
        """Test that missing some environment variables raises ValueError."""
        env_vars = {
            'SLACK_BOT_TOKEN': 'fake_token',
            'NOTION_API_KEY': 'fake_key',
            'OPENAI_API_KEY': 'fake_key',
            'TEST_MODE': 'false'
            # SLACK_SIGNING_SECRET and NOTION_DB_ID are missing
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            if 'main' in sys.modules:
                del sys.modules['main']
            
            with pytest.raises(ValueError) as exc_info:
                import main
            
            error_msg = str(exc_info.value)
            assert "Missing required environment variables" in error_msg
            assert "SLACK_SIGNING_SECRET" in error_msg
            assert "NOTION_DB_ID" in error_msg
    
    def test_all_env_vars_present_no_error(self):
        """Test that having all environment variables does not raise error."""
        env_vars = {
            'SLACK_BOT_TOKEN': 'fake_token',
            'SLACK_SIGNING_SECRET': 'fake_secret',
            'NOTION_API_KEY': 'fake_key',
            'NOTION_DB_ID': 'fake_db_id',
            'OPENAI_API_KEY': 'fake_openai_key',
            'TEST_MODE': 'false'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            if 'main' in sys.modules:
                del sys.modules['main']
            
            # Should not raise any exception
            try:
                import main
            except ValueError:
                pytest.fail("Should not raise ValueError when all env vars are present")
    
    def test_test_mode_bypasses_validation(self):
        """Test that TEST_MODE=true bypasses environment variable validation."""
        env_vars = {
            'TEST_MODE': 'true'
            # All other env vars are missing
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            if 'main' in sys.modules:
                del sys.modules['main']
            
            # Should not raise any exception due to TEST_MODE
            try:
                import main
                # Test passed if we get here without exception
            except ValueError:
                pytest.fail("Should not raise ValueError when TEST_MODE=true")
    
    def test_empty_string_env_vars_treated_as_missing(self):
        """Test that empty string environment variables are treated as missing."""
        env_vars = {
            'SLACK_BOT_TOKEN': '',  # Empty string should be treated as missing
            'SLACK_SIGNING_SECRET': 'fake_secret',
            'NOTION_API_KEY': '',  # Empty string should be treated as missing
            'NOTION_DB_ID': 'fake_db_id',
            'OPENAI_API_KEY': 'fake_openai_key',
            'TEST_MODE': 'false'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            if 'main' in sys.modules:
                del sys.modules['main']
            
            with pytest.raises(ValueError) as exc_info:
                import main
            
            error_msg = str(exc_info.value)
            assert "SLACK_BOT_TOKEN" in error_msg
            assert "NOTION_API_KEY" in error_msg
    
    def teardown_method(self):
        """Clean up after each test."""
        # Remove main from modules so next test starts fresh
        if 'main' in sys.modules:
            del sys.modules['main']
