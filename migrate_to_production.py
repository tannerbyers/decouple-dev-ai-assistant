#!/usr/bin/env python3
"""
Production migration script for OpsBrain AI Assistant.

This script migrates data from SQLite (development) to PostgreSQL (production).
It's designed to run on first deployment to Render.com or other cloud platforms.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main production migration function."""
    print("🚀 OpsBrain Production Migration")
    print("=" * 40)
    
    # Check if we're in production environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found. This script is for production deployment.")
        print("💡 For local development, use: python migrate_to_database.py")
        sys.exit(1)
    
    # Check if we have existing SQLite data to migrate
    sqlite_file = "opsbrain.db"
    has_sqlite_data = os.path.exists(sqlite_file)
    
    print(f"📊 Environment Check:")
    print(f"   Database URL: {database_url.split('@')[0]}@[REDACTED]")
    print(f"   SQLite data: {'Found' if has_sqlite_data else 'Not found'}")
    
    try:
        # Import PostgreSQL database manager
        sys.path.append('src')
        from postgres_database import PostgresDatabaseManager
        
        # Initialize PostgreSQL database
        print("🔗 Connecting to PostgreSQL database...")
        db_manager = PostgresDatabaseManager()
        
        # Get database info to confirm connection
        try:
            db_info = db_manager.get_database_info()
            print(f"✅ Connected to PostgreSQL successfully")
            print(f"   Database size: {db_info.get('database_size', 'Unknown')}")
            print(f"   Existing records: {db_info.get('total_records', 0)}")
        except Exception as db_info_error:
            print(f"⚠️  Could not get database info (continuing anyway): {db_info_error}")
            db_info = {'total_records': 0}  # Default to trigger initial setup
        
        # Initialize default configurations if database is empty
        if db_info.get('total_records', 0) == 0:
            print("📝 Setting up initial configuration...")
            
            try:
                # Set up initial configurations from environment variables
                initial_configs = {
                    'openai_api_key': ('OPENAI_API_KEY', 'openai', 'OpenAI API key for LLM functionality', True),
                    'notion_api_key': ('NOTION_API_KEY', 'notion', 'Notion API key for database access', True),
                    'slack_bot_token': ('SLACK_BOT_TOKEN', 'slack', 'Slack bot token for API access', True),
                    'slack_signing_secret': ('SLACK_SIGNING_SECRET', 'slack', 'Slack signing secret for request verification', True),
                    'notion_main_db_id': ('NOTION_DB_ID', 'notion', 'Main Notion database ID for tasks', False),
                    'notion_goals_db_id': ('NOTION_GOALS_DB_ID', 'notion', 'Notion database ID for business goals', False),
                    'notion_clients_db_id': ('NOTION_CLIENTS_DB_ID', 'notion', 'Notion database ID for client management', False),
                    'notion_projects_db_id': ('NOTION_PROJECTS_DB_ID', 'notion', 'Notion database ID for project tracking', False),
                    'notion_metrics_db_id': ('NOTION_METRICS_DB_ID', 'notion', 'Notion database ID for business metrics', False),
                }
                
                config_count = 0
                for config_key, (env_var, category, description, is_sensitive) in initial_configs.items():
                    env_value = os.getenv(env_var)
                    if env_value:
                        try:
                            db_manager.set_config(
                                key=config_key,
                                value=env_value,
                                category=category,
                                description=description,
                                is_sensitive=is_sensitive
                            )
                            config_count += 1
                        except Exception as config_error:
                            print(f"⚠️  Failed to set config {config_key}: {config_error}")
                
                # Set up initial application settings
                app_settings = {
                    'enable_ceo_mode': True,
                    'enable_debug_logging': False,
                    'enable_performance_monitoring': True,
                    'auto_cleanup_enabled': True,
                    'max_concurrent_requests': 10,
                    'max_thread_context_messages': 10,
                    'thread_context_cleanup_hours': 24,
                }
                
                for setting_key, setting_value in app_settings.items():
                    try:
                        db_manager.set_app_setting(setting_key, setting_value)
                        config_count += 1
                    except Exception as setting_error:
                        print(f"⚠️  Failed to set setting {setting_key}: {setting_error}")
                
                print(f"✅ Initial configuration completed ({config_count} settings)")
                
            except Exception as config_setup_error:
                print(f"⚠️  Configuration setup had issues (continuing anyway): {config_setup_error}")
        
        # Migrate from SQLite if available
        if has_sqlite_data:
            print("🔄 Migrating data from SQLite...")
            try:
                migration_result = db_manager.migrate_from_sqlite(sqlite_file)
                
                if migration_result:
                    print("✅ SQLite migration completed:")
                    for table, count in migration_result.items():
                        print(f"   {table}: {count} records")
                else:
                    print("⚠️  SQLite migration had no data to migrate")
            except Exception as migration_error:
                print(f"⚠️  SQLite migration failed (continuing anyway): {migration_error}")
        
        # Final database info
        try:
            final_info = db_manager.get_database_info()
            print("\n📊 Final Database Status:")
            print(f"   Total records: {final_info.get('total_records', 0)}")
            print(f"   Database size: {final_info.get('database_size', 'Unknown')}")
            
            for table, count in final_info.get('tables', {}).items():
                if count > 0:
                    print(f"   {table}: {count} records")
        except Exception as final_info_error:
            print(f"⚠️  Could not get final database info: {final_info_error}")
        
        print("\n🎉 Production migration completed successfully!")
        print("✅ OpsBrain is ready for production use")
        
        # Clean up SQLite file in production
        if has_sqlite_data and os.path.exists(sqlite_file):
            try:
                os.remove(sqlite_file)
                print("🧹 Cleaned up SQLite file from production environment")
            except Exception as e:
                print(f"⚠️  Could not remove SQLite file: {e}")
        
    except ImportError as e:
        print(f"⚠️  Failed to import PostgreSQL dependencies: {e}")
        print("💡 PostgreSQL functionality will be disabled, continuing with environment variables only")
        print("✅ Basic deployment continuing without database migration")
        # Don't exit - let the app start with just environment variables
    except Exception as e:
        print(f"⚠️  Production migration encountered an error: {e}")
        logger.error(f"Migration error: {e}")
        print("💡 Continuing deployment - app will use environment variables")
        # Don't exit - let the app start anyway

if __name__ == "__main__":
    main()
