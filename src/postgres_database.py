"""PostgreSQL database adapter for production deployment on Render.com."""
import os
import json
import logging
import psycopg2
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class PostgresConfig:
    """PostgreSQL database configuration."""
    database_url: str = ""
    max_connections: int = 20
    connection_timeout: int = 30

class PostgresDatabaseManager:
    """PostgreSQL database manager for production deployment."""
    
    def __init__(self, config: Optional[PostgresConfig] = None):
        self.config = config or PostgresConfig()
        self.database_url = self.config.database_url or os.getenv('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required for PostgreSQL")
        
        # Parse database URL
        self.db_params = self._parse_database_url(self.database_url)
        self._ensure_database_schema()
    
    def _parse_database_url(self, url: str) -> Dict[str, str]:
        """Parse DATABASE_URL into connection parameters."""
        parsed = urlparse(url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password,
            'sslmode': 'require'  # Required for most cloud PostgreSQL services
        }
    
    def _ensure_database_schema(self):
        """Create database tables if they don't exist."""
        schema_sql = """
        -- Create tables with PostgreSQL-specific syntax
        CREATE TABLE IF NOT EXISTS configurations (
            id SERIAL PRIMARY KEY,
            key VARCHAR(255) UNIQUE NOT NULL,
            value TEXT NOT NULL,
            category VARCHAR(100) NOT NULL DEFAULT 'general',
            description TEXT,
            is_sensitive BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS thread_contexts (
            id SERIAL PRIMARY KEY,
            thread_key VARCHAR(255) UNIQUE NOT NULL,
            channel_id VARCHAR(100) NOT NULL,
            thread_ts VARCHAR(50),
            messages JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS business_goals (
            id VARCHAR(100) PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            description TEXT NOT NULL,
            area VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'not_started',
            priority INTEGER NOT NULL DEFAULT 2,
            target_date DATE,
            progress INTEGER DEFAULT 0,
            weekly_actions JSONB,
            daily_actions JSONB,
            success_metrics JSONB,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS app_settings (
            id SERIAL PRIMARY KEY,
            setting_key VARCHAR(255) UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            setting_type VARCHAR(50) DEFAULT 'string',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS user_preferences (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            preference_key VARCHAR(255) NOT NULL,
            preference_value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, preference_key)
        );
        
        CREATE TABLE IF NOT EXISTS config_audit (
            id SERIAL PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            record_id VARCHAR(100) NOT NULL,
            action VARCHAR(50) NOT NULL,
            old_values JSONB,
            new_values JSONB,
            changed_by VARCHAR(100),
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id SERIAL PRIMARY KEY,
            metric_name VARCHAR(255) NOT NULL,
            metric_value DECIMAL(10,4) NOT NULL,
            metric_unit VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            additional_data JSONB
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_configurations_category ON configurations(category);
        CREATE INDEX IF NOT EXISTS idx_configurations_key ON configurations(key);
        CREATE INDEX IF NOT EXISTS idx_thread_contexts_channel ON thread_contexts(channel_id);
        CREATE INDEX IF NOT EXISTS idx_thread_contexts_expires ON thread_contexts(expires_at);
        CREATE INDEX IF NOT EXISTS idx_business_goals_area ON business_goals(area);
        CREATE INDEX IF NOT EXISTS idx_business_goals_status ON business_goals(status);
        CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);
        CREATE INDEX IF NOT EXISTS idx_config_audit_table ON config_audit(table_name, record_id);
        CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
        CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
                conn.commit()
                logger.info("PostgreSQL database schema created/verified successfully")
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get PostgreSQL connection with proper error handling."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_params)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    # Configuration Management
    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value by key."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT value FROM configurations WHERE key = %s", (key,))
                    row = cur.fetchone()
                    return row[0] if row else default
        except Exception as e:
            logger.error(f"Failed to get config {key}: {e}")
            return default
    
    def set_config(self, key: str, value: str, category: str = 'general', 
                   description: str = '', is_sensitive: bool = False) -> None:
        """Set configuration value."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO configurations (key, value, category, description, is_sensitive, updated_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (key) DO UPDATE SET
                            value = EXCLUDED.value,
                            category = EXCLUDED.category,
                            description = EXCLUDED.description,
                            is_sensitive = EXCLUDED.is_sensitive,
                            updated_at = CURRENT_TIMESTAMP
                    """, (key, value, category, description, is_sensitive))
                conn.commit()
                logger.info(f"Configuration updated: {key} = {value if not is_sensitive else '[REDACTED]'}")
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
            raise
    
    def get_configs_by_category(self, category: str) -> Dict[str, str]:
        """Get all configurations for a specific category."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT key, value FROM configurations WHERE category = %s", (category,))
                    return {row[0]: row[1] for row in cur.fetchall()}
        except Exception as e:
            logger.error(f"Failed to get configs for category {category}: {e}")
            return {}
    
    def delete_config(self, key: str) -> bool:
        """Delete configuration by key."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM configurations WHERE key = %s", (key,))
                    deleted = cur.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            logger.error(f"Failed to delete config {key}: {e}")
            return False
    
    # Thread Context Management
    def save_thread_context(self, thread_key: str, channel_id: str, 
                          thread_ts: Optional[str], messages: List[str]) -> None:
        """Save thread context to database."""
        try:
            messages_json = json.dumps(messages)
            expires_at = datetime.now() + timedelta(hours=24)
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO thread_contexts (thread_key, channel_id, thread_ts, messages, expires_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (thread_key) DO UPDATE SET
                            channel_id = EXCLUDED.channel_id,
                            thread_ts = EXCLUDED.thread_ts,
                            messages = EXCLUDED.messages,
                            expires_at = EXCLUDED.expires_at,
                            updated_at = CURRENT_TIMESTAMP
                    """, (thread_key, channel_id, thread_ts, messages_json, expires_at))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save thread context {thread_key}: {e}")
            raise
    
    def get_thread_context(self, thread_key: str) -> Optional[Dict]:
        """Get thread context by key."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT thread_key, channel_id, thread_ts, messages, created_at, updated_at
                        FROM thread_contexts 
                        WHERE thread_key = %s AND expires_at > CURRENT_TIMESTAMP
                    """, (thread_key,))
                    row = cur.fetchone()
                    
                    if row:
                        return {
                            'thread_key': row[0],
                            'channel_id': row[1],
                            'thread_ts': row[2],
                            'messages': json.loads(row[3]) if row[3] else [],
                            'created_at': row[4],
                            'updated_at': row[5]
                        }
            return None
        except Exception as e:
            logger.error(f"Failed to get thread context {thread_key}: {e}")
            return None
    
    def cleanup_expired_threads(self) -> int:
        """Remove expired thread contexts."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM thread_contexts WHERE expires_at <= CURRENT_TIMESTAMP")
                    cleaned_count = cur.rowcount
                conn.commit()
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} expired thread contexts")
                return cleaned_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired threads: {e}")
            return 0
    
    # Business Goals Management
    def save_business_goal(self, goal_data: Dict) -> None:
        """Save business goal to database."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO business_goals
                        (id, title, description, area, status, priority, target_date, 
                         progress, weekly_actions, daily_actions, success_metrics, notes, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            description = EXCLUDED.description,
                            area = EXCLUDED.area,
                            status = EXCLUDED.status,
                            priority = EXCLUDED.priority,
                            target_date = EXCLUDED.target_date,
                            progress = EXCLUDED.progress,
                            weekly_actions = EXCLUDED.weekly_actions,
                            daily_actions = EXCLUDED.daily_actions,
                            success_metrics = EXCLUDED.success_metrics,
                            notes = EXCLUDED.notes,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        goal_data['id'],
                        goal_data['title'],
                        goal_data['description'],
                        goal_data['area'],
                        goal_data['status'],
                        goal_data['priority'],
                        goal_data.get('target_date'),
                        goal_data.get('progress', 0),
                        json.dumps(goal_data.get('weekly_actions', [])),
                        json.dumps(goal_data.get('daily_actions', [])),
                        json.dumps(goal_data.get('success_metrics', {})),
                        goal_data.get('notes', ''),
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save business goal {goal_data.get('id')}: {e}")
            raise
    
    def get_business_goals(self, area: Optional[str] = None, 
                          status: Optional[str] = None) -> List[Dict]:
        """Get business goals with optional filtering."""
        try:
            query = "SELECT * FROM business_goals WHERE 1=1"
            params = []
            
            if area:
                query += " AND area = %s"
                params.append(area)
            if status:
                query += " AND status = %s"
                params.append(status)
            
            query += " ORDER BY priority DESC, created_at DESC"
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    goals = []
                    columns = [desc[0] for desc in cur.description]
                    
                    for row in cur.fetchall():
                        goal = dict(zip(columns, row))
                        goal['weekly_actions'] = json.loads(goal['weekly_actions']) if goal['weekly_actions'] else []
                        goal['daily_actions'] = json.loads(goal['daily_actions']) if goal['daily_actions'] else []
                        goal['success_metrics'] = json.loads(goal['success_metrics']) if goal['success_metrics'] else {}
                        goals.append(goal)
                    
                    return goals
        except Exception as e:
            logger.error(f"Failed to get business goals: {e}")
            return []
    
    def delete_business_goal(self, goal_id: str) -> bool:
        """Delete business goal by ID."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM business_goals WHERE id = %s", (goal_id,))
                    deleted = cur.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            logger.error(f"Failed to delete business goal {goal_id}: {e}")
            return False
    
    # Application Settings
    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """Get application setting with type conversion."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT setting_value, setting_type FROM app_settings WHERE setting_key = %s", 
                        (key,)
                    )
                    row = cur.fetchone()
                    if not row:
                        return default
                    
                    value, setting_type = row
                    
                    # Convert value based on type
                    if setting_type == 'boolean':
                        return value.lower() in ('true', '1', 'yes', 'on')
                    elif setting_type == 'integer':
                        return int(value)
                    elif setting_type == 'json':
                        return json.loads(value)
                    else:
                        return value
        except Exception as e:
            logger.error(f"Failed to get app setting {key}: {e}")
            return default
    
    def set_app_setting(self, key: str, value: Any, setting_type: str = 'string',
                       description: str = '') -> None:
        """Set application setting with automatic type detection."""
        try:
            if setting_type == 'string':
                # Auto-detect type
                if isinstance(value, bool):
                    setting_type = 'boolean'
                    value = str(value).lower()
                elif isinstance(value, int):
                    setting_type = 'integer'
                    value = str(value)
                elif isinstance(value, (dict, list)):
                    setting_type = 'json'
                    value = json.dumps(value)
                else:
                    value = str(value)
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO app_settings (setting_key, setting_value, setting_type, description, updated_at)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (setting_key) DO UPDATE SET
                            setting_value = EXCLUDED.setting_value,
                            setting_type = EXCLUDED.setting_type,
                            description = EXCLUDED.description,
                            updated_at = CURRENT_TIMESTAMP
                    """, (key, value, setting_type, description))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to set app setting {key}: {e}")
            raise
    
    # Performance Metrics
    def log_performance_metric(self, metric_name: str, metric_value: float,
                             metric_unit: str = '', additional_data: Optional[Dict] = None) -> None:
        """Log performance metric."""
        try:
            additional_json = json.dumps(additional_data) if additional_data else None
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, additional_data)
                        VALUES (%s, %s, %s, %s)
                    """, (metric_name, metric_value, metric_unit, additional_json))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log performance metric {metric_name}: {e}")
    
    def get_performance_metrics(self, metric_name: Optional[str] = None,
                              hours: int = 24) -> List[Dict]:
        """Get performance metrics from last N hours."""
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            query = "SELECT * FROM performance_metrics WHERE timestamp >= %s"
            params = [since]
            
            if metric_name:
                query += " AND metric_name = %s"
                params.append(metric_name)
            
            query += " ORDER BY timestamp DESC"
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return []
    
    # Migration from SQLite
    def migrate_from_sqlite(self, sqlite_db_path: str = "opsbrain.db") -> Dict[str, int]:
        """Migrate data from SQLite database to PostgreSQL."""
        if not os.path.exists(sqlite_db_path):
            logger.warning(f"SQLite database {sqlite_db_path} not found")
            return {}
        
        try:
            import sqlite3
            
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(sqlite_db_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            migration_counts = {}
            
            # Migrate configurations
            try:
                sqlite_cur = sqlite_conn.execute("SELECT * FROM configurations")
                configs = [dict(row) for row in sqlite_cur.fetchall()]
                
                for config in configs:
                    self.set_config(
                        config['key'], config['value'], config['category'],
                        config.get('description', ''), config.get('is_sensitive', False)
                    )
                
                migration_counts['configurations'] = len(configs)
                logger.info(f"Migrated {len(configs)} configurations")
            except Exception as e:
                logger.error(f"Failed to migrate configurations: {e}")
            
            # Migrate business goals
            try:
                sqlite_cur = sqlite_conn.execute("SELECT * FROM business_goals")
                goals = [dict(row) for row in sqlite_cur.fetchall()]
                
                for goal in goals:
                    # Parse JSON fields from SQLite
                    goal['weekly_actions'] = json.loads(goal['weekly_actions']) if goal['weekly_actions'] else []
                    goal['daily_actions'] = json.loads(goal['daily_actions']) if goal['daily_actions'] else []
                    goal['success_metrics'] = json.loads(goal['success_metrics']) if goal['success_metrics'] else {}
                    
                    self.save_business_goal(goal)
                
                migration_counts['business_goals'] = len(goals)
                logger.info(f"Migrated {len(goals)} business goals")
            except Exception as e:
                logger.error(f"Failed to migrate business goals: {e}")
            
            # Migrate app settings
            try:
                sqlite_cur = sqlite_conn.execute("SELECT * FROM app_settings")
                settings = [dict(row) for row in sqlite_cur.fetchall()]
                
                for setting in settings:
                    self.set_app_setting(
                        setting['setting_key'], setting['setting_value'],
                        setting['setting_type'], setting.get('description', '')
                    )
                
                migration_counts['app_settings'] = len(settings)
                logger.info(f"Migrated {len(settings)} app settings")
            except Exception as e:
                logger.error(f"Failed to migrate app settings: {e}")
            
            sqlite_conn.close()
            logger.info(f"SQLite to PostgreSQL migration completed: {migration_counts}")
            return migration_counts
            
        except Exception as e:
            logger.error(f"SQLite migration failed: {e}")
            return {}
    
    def get_database_info(self) -> Dict:
        """Get database information and statistics."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get table counts
                    tables_info = {}
                    table_names = ['configurations', 'thread_contexts', 'business_goals', 
                                 'app_settings', 'user_preferences', 'config_audit', 'performance_metrics']
                    
                    for table_name in table_names:
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cur.fetchone()[0]
                            tables_info[table_name] = count
                        except Exception as e:
                            logger.error(f"Failed to count {table_name}: {e}")
                            tables_info[table_name] = 0
                    
                    # Get database size (PostgreSQL specific)
                    try:
                        cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                        db_size = cur.fetchone()[0]
                    except Exception:
                        db_size = "Unknown"
                    
                    return {
                        'database_url': self.database_url.split('@')[0] + '@[REDACTED]',  # Hide credentials
                        'database_size': db_size,
                        'tables': tables_info,
                        'total_records': sum(tables_info.values())
                    }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {'error': str(e)}

# Factory function to choose database based on environment
def create_database_manager():
    """Create appropriate database manager based on environment."""
    if os.getenv('DATABASE_URL'):
        # Production: Use PostgreSQL
        logger.info("Using PostgreSQL database for production")
        return PostgresDatabaseManager()
    else:
        # Development: Use SQLite
        logger.info("Using SQLite database for development")
        try:
            from .database import DatabaseManager
        except ImportError:
            # Handle direct execution or testing
            from database import DatabaseManager
        return DatabaseManager()

# Global database manager instance
db_manager = create_database_manager()
