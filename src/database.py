"""Database manager for OpsBrain AI Assistant configuration and data storage."""
import sqlite3
import json
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    db_path: str = "opsbrain.db"
    schema_path: str = "database_schema.sql"
    backup_enabled: bool = True
    backup_retention_days: int = 7

class DatabaseManager:
    """Manages SQLite database operations for OpsBrain configuration and data."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.db_path = self.config.db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist."""
        if not os.path.exists(self.db_path):
            logger.info(f"Creating new database at {self.db_path}")
            self._create_database()
        else:
            logger.info(f"Using existing database at {self.db_path}")
    
    def _create_database(self) -> None:
        """Create database schema from SQL file."""
        if os.path.exists(self.config.schema_path):
            with open(self.config.schema_path, 'r') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                logger.info("Database schema created successfully")
        else:
            logger.warning(f"Schema file {self.config.schema_path} not found, creating minimal schema")
            self._create_minimal_schema()
    
    def _create_minimal_schema(self) -> None:
        """Create minimal database schema if schema file is missing."""
        minimal_schema = """
        CREATE TABLE IF NOT EXISTS configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            description TEXT,
            is_sensitive BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS thread_contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_key TEXT UNIQUE NOT NULL,
            channel_id TEXT NOT NULL,
            thread_ts TEXT,
            messages TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
        """
        
        with self.get_connection() as conn:
            conn.executescript(minimal_schema)
            logger.info("Minimal database schema created")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling and cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
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
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM configurations WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            return row['value'] if row else default
    
    def set_config(self, key: str, value: str, category: str = 'general', 
                   description: str = '', is_sensitive: bool = False) -> None:
        """Set configuration value."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO configurations 
                (key, value, category, description, is_sensitive, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value, category, description, is_sensitive))
            conn.commit()
            logger.info(f"Configuration updated: {key} = {value if not is_sensitive else '[REDACTED]'}")
    
    def get_configs_by_category(self, category: str) -> Dict[str, str]:
        """Get all configurations for a specific category."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT key, value FROM configurations WHERE category = ?", (category,)
            )
            return {row['key']: row['value'] for row in cursor.fetchall()}
    
    def delete_config(self, key: str) -> bool:
        """Delete configuration by key. Returns True if deleted, False if not found."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM configurations WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Thread Context Management
    def save_thread_context(self, thread_key: str, channel_id: str, 
                          thread_ts: Optional[str], messages: List[str]) -> None:
        """Save thread context to database."""
        messages_json = json.dumps(messages)
        expires_at = datetime.now() + timedelta(hours=24)  # Default 24-hour expiry
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO thread_contexts 
                (thread_key, channel_id, thread_ts, messages, expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (thread_key, channel_id, thread_ts, messages_json, expires_at))
            conn.commit()
    
    def get_thread_context(self, thread_key: str) -> Optional[Dict]:
        """Get thread context by key."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT thread_key, channel_id, thread_ts, messages, created_at, updated_at
                FROM thread_contexts 
                WHERE thread_key = ? AND expires_at > CURRENT_TIMESTAMP
            """, (thread_key,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'thread_key': row['thread_key'],
                    'channel_id': row['channel_id'],
                    'thread_ts': row['thread_ts'],
                    'messages': json.loads(row['messages']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
    
    def cleanup_expired_threads(self) -> int:
        """Remove expired thread contexts. Returns number of cleaned up contexts."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM thread_contexts 
                WHERE expires_at <= CURRENT_TIMESTAMP
            """)
            conn.commit()
            cleaned_count = cursor.rowcount
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired thread contexts")
            return cleaned_count
    
    # Business Goals Management
    def save_business_goal(self, goal_data: Dict) -> None:
        """Save business goal to database."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO business_goals
                (id, title, description, area, status, priority, target_date, 
                 progress, weekly_actions, daily_actions, success_metrics, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
    
    def get_business_goals(self, area: Optional[str] = None, 
                          status: Optional[str] = None) -> List[Dict]:
        """Get business goals with optional filtering."""
        query = "SELECT * FROM business_goals WHERE 1=1"
        params = []
        
        if area:
            query += " AND area = ?"
            params.append(area)
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY priority DESC, created_at DESC"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            goals = []
            for row in cursor.fetchall():
                goal = dict(row)
                goal['weekly_actions'] = json.loads(goal['weekly_actions'])
                goal['daily_actions'] = json.loads(goal['daily_actions'])
                goal['success_metrics'] = json.loads(goal['success_metrics'])
                goals.append(goal)
            return goals
    
    def delete_business_goal(self, goal_id: str) -> bool:
        """Delete business goal by ID. Returns True if deleted, False if not found."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM business_goals WHERE id = ?", (goal_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Application Settings
    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """Get application setting with type conversion."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT setting_value, setting_type FROM app_settings WHERE setting_key = ?", 
                (key,)
            )
            row = cursor.fetchone()
            if not row:
                return default
            
            value = row['setting_value']
            setting_type = row['setting_type']
            
            # Convert value based on type
            if setting_type == 'boolean':
                return value.lower() in ('true', '1', 'yes', 'on')
            elif setting_type == 'integer':
                return int(value)
            elif setting_type == 'json':
                return json.loads(value)
            else:
                return value
    
    def set_app_setting(self, key: str, value: Any, setting_type: str = 'string',
                       description: str = '') -> None:
        """Set application setting with automatic type detection."""
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
            conn.execute("""
                INSERT OR REPLACE INTO app_settings
                (setting_key, setting_value, setting_type, description, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value, setting_type, description))
            conn.commit()
    
    # Performance Metrics
    def log_performance_metric(self, metric_name: str, metric_value: float,
                             metric_unit: str = '', additional_data: Optional[Dict] = None) -> None:
        """Log performance metric."""
        additional_json = json.dumps(additional_data) if additional_data else None
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO performance_metrics 
                (metric_name, metric_value, metric_unit, additional_data)
                VALUES (?, ?, ?, ?)
            """, (metric_name, metric_value, metric_unit, additional_json))
            conn.commit()
    
    def get_performance_metrics(self, metric_name: Optional[str] = None,
                              hours: int = 24) -> List[Dict]:
        """Get performance metrics from last N hours."""
        since = datetime.now() - timedelta(hours=hours)
        
        query = "SELECT * FROM performance_metrics WHERE timestamp >= ?"
        params = [since]
        
        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)
        
        query += " ORDER BY timestamp DESC"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # Migration and Maintenance
    def migrate_from_json(self, json_file_path: str) -> int:
        """Migrate business goals from JSON file to database."""
        if not os.path.exists(json_file_path):
            logger.warning(f"JSON file {json_file_path} not found for migration")
            return 0
        
        with open(json_file_path, 'r') as f:
            goals_data = json.load(f)
        
        migrated_count = 0
        for goal_id, goal_data in goals_data.items():
            try:
                # Normalize the goal data structure
                normalized_goal = {
                    'id': goal_id,
                    'title': goal_data.get('title', ''),
                    'description': goal_data.get('description', ''),
                    'area': goal_data.get('area') or goal_data.get('category', 'sales'),
                    'status': goal_data.get('status', 'not_started'),
                    'priority': goal_data.get('priority', 2),
                    'target_date': goal_data.get('target_date'),
                    'progress': goal_data.get('progress_percentage', 0),
                    'weekly_actions': goal_data.get('weekly_actions', []),
                    'daily_actions': goal_data.get('daily_actions', []),
                    'success_metrics': goal_data.get('success_metrics', {}),
                    'notes': goal_data.get('notes', ''),
                }
                
                self.save_business_goal(normalized_goal)
                migrated_count += 1
            except Exception as e:
                logger.error(f"Failed to migrate goal {goal_id}: {e}")
        
        logger.info(f"Migrated {migrated_count} business goals from {json_file_path}")
        return migrated_count
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create database backup. Returns backup file path."""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
        
        # Simple file copy for SQLite
        import shutil
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")
        return backup_path
    
    def get_database_info(self) -> Dict:
        """Get database information and statistics."""
        with self.get_connection() as conn:
            # Get table counts
            tables_info = {}
            cursor = conn.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            for row in cursor.fetchall():
                table_name = row['name']
                count_cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = count_cursor.fetchone()['count']
                tables_info[table_name] = count
            
            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'database_path': self.db_path,
                'database_size_bytes': db_size,
                'tables': tables_info,
                'total_records': sum(tables_info.values())
            }

# Global database manager instance
db_manager = DatabaseManager()
