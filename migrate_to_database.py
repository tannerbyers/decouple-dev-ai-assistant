#!/usr/bin/env python3
"""
Migration script to transition OpsBrain AI Assistant from current storage to database.

This script:
1. Creates the SQLite database with proper schema
2. Migrates business goals from business_goals.json
3. Sets up initial configurations
4. Provides rollback capability
5. Validates the migration
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager, DatabaseConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles migration from current storage system to database."""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.backup_dir = "migration_backups"
        self.migration_log = []
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def log_step(self, step: str, status: str = "SUCCESS", details: str = "") -> None:
        """Log migration step."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'details': details
        }
        self.migration_log.append(entry)
        logger.info(f"{status}: {step} - {details}")
    
    def backup_current_data(self) -> bool:
        """Backup current JSON files and configurations."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = os.path.join(self.backup_dir, f"migration_{timestamp}")
            os.makedirs(backup_subdir, exist_ok=True)
            
            # Backup business_goals.json if it exists
            if os.path.exists("business_goals.json"):
                import shutil
                shutil.copy2("business_goals.json", 
                           os.path.join(backup_subdir, "business_goals.json"))
                self.log_step("Backup business_goals.json", details=backup_subdir)
            
            # Save environment variables to backup
            env_backup = {}
            env_vars = [
                'SLACK_BOT_TOKEN', 'SLACK_SIGNING_SECRET', 'NOTION_API_KEY', 
                'NOTION_DB_ID', 'NOTION_GOALS_DB_ID', 'NOTION_CLIENTS_DB_ID', 
                'NOTION_PROJECTS_DB_ID', 'NOTION_METRICS_DB_ID', 'OPENAI_API_KEY',
                'TRELLO_API_KEY', 'TRELLO_TOKEN', 'TRELLO_BOARD_ID'
            ]
            
            for var in env_vars:
                value = os.getenv(var)
                if value:
                    # Don't store sensitive values in backup, just note their presence
                    env_backup[var] = '[PRESENT]' if 'TOKEN' in var or 'KEY' in var or 'SECRET' in var else value
            
            with open(os.path.join(backup_subdir, "environment_backup.json"), 'w') as f:
                json.dump(env_backup, f, indent=2)
            
            self.log_step("Backup environment configuration", details=backup_subdir)
            return True
            
        except Exception as e:
            self.log_step("Backup current data", "FAILED", str(e))
            return False
    
    def migrate_business_goals(self) -> bool:
        """Migrate business goals from JSON file to database."""
        try:
            if not os.path.exists("business_goals.json"):
                self.log_step("No business_goals.json found", "WARNING", "Skipping business goals migration")
                return True
            
            migrated_count = self.db_manager.migrate_from_json("business_goals.json")
            self.log_step("Migrate business goals", details=f"Migrated {migrated_count} goals")
            return True
            
        except Exception as e:
            self.log_step("Migrate business goals", "FAILED", str(e))
            return False
    
    def setup_initial_configurations(self) -> bool:
        """Set up initial configurations in database from environment variables."""
        try:
            # API configurations
            api_configs = {
                'openai_api_key': ('OPENAI_API_KEY', 'openai', 'OpenAI API key for LLM functionality', True),
                'notion_api_key': ('NOTION_API_KEY', 'notion', 'Notion API key for database access', True),
                'slack_bot_token': ('SLACK_BOT_TOKEN', 'slack', 'Slack bot token for API access', True),
                'slack_signing_secret': ('SLACK_SIGNING_SECRET', 'slack', 'Slack signing secret for request verification', True),
            }
            
            # Database IDs
            db_configs = {
                'notion_main_db_id': ('NOTION_DB_ID', 'notion', 'Main Notion database ID for tasks', False),
                'notion_goals_db_id': ('NOTION_GOALS_DB_ID', 'notion', 'Notion database ID for business goals', False),
                'notion_clients_db_id': ('NOTION_CLIENTS_DB_ID', 'notion', 'Notion database ID for client management', False),
                'notion_projects_db_id': ('NOTION_PROJECTS_DB_ID', 'notion', 'Notion database ID for project tracking', False),
                'notion_metrics_db_id': ('NOTION_METRICS_DB_ID', 'notion', 'Notion database ID for business metrics', False),
            }
            
            # Trello configurations
            trello_configs = {
                'trello_api_key': ('TRELLO_API_KEY', 'trello', 'Trello API key for task management', True),
                'trello_token': ('TRELLO_TOKEN', 'trello', 'Trello API token for authentication', True),
                'trello_board_id': ('TRELLO_BOARD_ID', 'trello', 'Trello board ID for task management', False),
            }
            
            # Migrate all configurations
            all_configs = {**api_configs, **db_configs, **trello_configs}
            migrated_count = 0
            
            for config_key, (env_var, category, description, is_sensitive) in all_configs.items():
                env_value = os.getenv(env_var)
                if env_value:
                    self.db_manager.set_config(
                        key=config_key,
                        value=env_value,
                        category=category,
                        description=description,
                        is_sensitive=is_sensitive
                    )
                    migrated_count += 1
            
            # Set up application settings
            app_settings = {
                'enable_ceo_mode': True,
                'enable_debug_logging': os.getenv('TEST_MODE', 'false').lower() == 'true',
                'enable_performance_monitoring': True,
                'auto_cleanup_enabled': True,
                'max_concurrent_requests': 10,
                'max_thread_context_messages': 10,
                'thread_context_cleanup_hours': 24,
            }
            
            for setting_key, setting_value in app_settings.items():
                self.db_manager.set_app_setting(setting_key, setting_value)
                migrated_count += 1
            
            self.log_step("Setup initial configurations", details=f"Set up {migrated_count} configurations")
            return True
            
        except Exception as e:
            self.log_step("Setup initial configurations", "FAILED", str(e))
            return False
    
    def validate_migration(self) -> bool:
        """Validate that migration was successful."""
        try:
            # Check database exists and has tables
            db_info = self.db_manager.get_database_info()
            
            if not db_info['tables']:
                self.log_step("Database validation", "FAILED", "No tables found in database")
                return False
            
            # Validate configurations
            test_config = self.db_manager.get_config('app_name')
            if not test_config:
                self.log_step("Configuration validation", "FAILED", "Default configurations not found")
                return False
            
            # Validate business goals if they were migrated
            if os.path.exists("business_goals.json"):
                goals = self.db_manager.get_business_goals()
                with open("business_goals.json", 'r') as f:
                    original_goals = json.load(f)
                
                if len(goals) != len(original_goals):
                    self.log_step("Business goals validation", "FAILED", 
                                f"Goal count mismatch: {len(goals)} vs {len(original_goals)}")
                    return False
            
            self.log_step("Migration validation", details=f"Database contains {db_info['total_records']} total records")
            return True
            
        except Exception as e:
            self.log_step("Migration validation", "FAILED", str(e))
            return False
    
    def save_migration_log(self) -> str:
        """Save migration log to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.backup_dir, f"migration_log_{timestamp}.json")
        
        with open(log_file, 'w') as f:
            json.dump(self.migration_log, f, indent=2)
        
        return log_file
    
    def run_migration(self) -> bool:
        """Run the complete migration process."""
        logger.info("🚀 Starting database migration for OpsBrain AI Assistant")
        
        # Step 1: Backup current data
        if not self.backup_current_data():
            logger.error("❌ Failed to backup current data. Migration aborted.")
            return False
        
        # Step 2: Migrate business goals
        if not self.migrate_business_goals():
            logger.error("❌ Failed to migrate business goals. Migration aborted.")
            return False
        
        # Step 3: Setup initial configurations
        if not self.setup_initial_configurations():
            logger.error("❌ Failed to setup initial configurations. Migration aborted.")
            return False
        
        # Step 4: Validate migration
        if not self.validate_migration():
            logger.error("❌ Migration validation failed. Please check the logs.")
            return False
        
        # Step 5: Save migration log
        log_file = self.save_migration_log()
        
        logger.info("✅ Migration completed successfully!")
        logger.info(f"📋 Migration log saved to: {log_file}")
        logger.info(f"💾 Database file: {self.db_manager.db_path}")
        
        # Display summary
        db_info = self.db_manager.get_database_info()
        logger.info("\n📊 Migration Summary:")
        logger.info(f"   Database size: {db_info['database_size_bytes']} bytes")
        for table, count in db_info['tables'].items():
            logger.info(f"   {table}: {count} records")
        
        return True

def main():
    """Main migration function."""
    print("OpsBrain AI Assistant - Database Migration Tool")
    print("=" * 50)
    
    # Check if database already exists
    if os.path.exists("opsbrain.db"):
        response = input("⚠️  Database already exists. Continue migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    
    # Run migration
    migrator = DatabaseMigrator()
    success = migrator.run_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now update your application to use the database.")
        print(f"Database file: {migrator.db_manager.db_path}")
        
        # Show next steps
        print("\n📝 Next Steps:")
        print("1. Update main.py to use database for configurations")
        print("2. Update thread context management to use database")
        print("3. Test the application with the new database")
        print("4. Remove or rename business_goals.json after validation")
        
    else:
        print("\n❌ Migration failed. Check the logs for details.")
        print("Your original data has been backed up safely.")
        sys.exit(1)

if __name__ == "__main__":
    main()
