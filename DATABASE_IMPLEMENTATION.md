# OpsBrain AI Assistant - Database Implementation Guide

## Overview

This document outlines the database implementation for OpsBrain AI Assistant, transitioning from the current environment variable + JSON file storage system to a robust SQLite database solution.

## Current vs New Architecture

### Current System (Problems):
- ❌ Configurations scattered across environment variables and JSON files
- ❌ In-memory thread contexts lost on restart
- ❌ No configuration persistence or versioning
- ❌ Hard to scale and maintain
- ❌ No centralized config management
- ❌ No audit trail or performance tracking

### New Database System (Benefits):
- ✅ Centralized configuration and data storage
- ✅ Persistent thread contexts across restarts
- ✅ Configuration versioning and audit trail
- ✅ Performance metrics collection
- ✅ Easy backup and migration
- ✅ Scalable and maintainable
- ✅ Type-safe configuration management

## Database Schema

### Tables Overview

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `configurations` | API keys, database IDs, system settings | Categories, sensitive flag, audit trail |
| `thread_contexts` | Slack conversation continuity | Auto-expiration, JSON message storage |
| `business_goals` | Business objectives and tracking | Priority, progress, actions, metrics |
| `app_settings` | Feature flags and application settings | Type-aware storage (boolean, integer, JSON) |
| `user_preferences` | User-specific customizations | Per-user configuration overrides |
| `config_audit` | Configuration change history | Full audit trail for compliance |
| `performance_metrics` | System performance tracking | Response times, resource usage |

### Key Features

- **Automatic Schema Creation**: Database and tables created on first run
- **Migration Support**: Seamless migration from existing JSON files
- **Type Safety**: Automatic type conversion for settings
- **Security**: Sensitive data flagging and proper handling
- **Performance**: Optimized indexes for fast queries
- **Maintenance**: Auto-cleanup of expired data

## Implementation Files

### Core Files
- `database_schema.sql` - Complete database schema definition
- `src/database.py` - Database manager class with all operations
- `migrate_to_database.py` - Migration script from current system
- `test_database.py` - Comprehensive test suite

### Key Classes
- `DatabaseManager` - Main database interface
- `DatabaseConfig` - Configuration for database settings
- `DatabaseMigrator` - Handles migration from existing system

## Migration Process

### Step 1: Run Tests
```bash
# Test database functionality
python test_database.py
```

### Step 2: Run Migration
```bash
# Migrate from current system to database
python migrate_to_database.py
```

### Step 3: Verify Migration
The migration script will:
1. ✅ Backup current data safely
2. ✅ Create database with proper schema  
3. ✅ Migrate business goals from JSON
4. ✅ Transfer environment configurations
5. ✅ Set up application settings
6. ✅ Validate migration success
7. ✅ Generate detailed migration log

### Step 4: Update Application
Update `main.py` to use database instead of environment variables and in-memory storage.

## Usage Examples

### Configuration Management
```python
from src.database import db_manager

# Get configuration with fallback
api_key = db_manager.get_config('openai_api_key', 'fallback_key')

# Set configuration
db_manager.set_config(
    key='new_feature_enabled',
    value='true',
    category='features',
    description='Enable new AI feature',
    is_sensitive=False
)

# Get all configs by category
slack_configs = db_manager.get_configs_by_category('slack')
```

### Thread Context Management
```python
# Save conversation context
db_manager.save_thread_context(
    thread_key='C123:ts456',
    channel_id='C123',
    thread_ts='ts456',
    messages=['User: Hello', 'Bot: Hi there']
)

# Retrieve context
context = db_manager.get_thread_context('C123:ts456')
if context:
    messages = context['messages']
    # Continue conversation...
```

### Business Goals
```python
# Create business goal
goal_data = {
    'id': 'sales_q1_2025',
    'title': 'Q1 Sales Target',
    'description': 'Achieve $50k in Q1 sales',
    'area': 'sales',
    'status': 'in_progress',
    'priority': 4,
    'weekly_actions': ['Follow up with leads', 'Send proposals'],
    'success_metrics': {'revenue': '$50000'}
}
db_manager.save_business_goal(goal_data)

# Query goals
active_goals = db_manager.get_business_goals(status='in_progress')
sales_goals = db_manager.get_business_goals(area='sales')
```

### Application Settings
```python
# Set different types of settings
db_manager.set_app_setting('max_retries', 3)  # integer
db_manager.set_app_setting('debug_mode', True)  # boolean
db_manager.set_app_setting('features', {'ai_mode': True})  # JSON

# Get with automatic type conversion
max_retries = db_manager.get_app_setting('max_retries')  # returns int(3)
debug_enabled = db_manager.get_app_setting('debug_mode')  # returns bool(True)
```

### Performance Tracking
```python
# Log performance metrics
db_manager.log_performance_metric(
    metric_name='slack_response_time',
    metric_value=0.85,
    metric_unit='seconds',
    additional_data={'endpoint': '/slack', 'user_count': 5}
)

# Query performance data
recent_metrics = db_manager.get_performance_metrics('slack_response_time', hours=24)
```

## Integration with Existing Code

### Environment Variable Replacement
Replace this pattern:
```python
# OLD: Environment variable access
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")
```

With:
```python
# NEW: Database configuration
OPENAI_API_KEY = db_manager.get_config('openai_api_key')
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not configured in database")
```

### Thread Context Replacement  
Replace this pattern:
```python
# OLD: In-memory storage (lost on restart)
thread_contexts: Dict[str, Dict] = {}

def get_thread_context(thread_key):
    return thread_contexts.get(thread_key)
```

With:
```python
# NEW: Persistent database storage
def get_thread_context(thread_key):
    return db_manager.get_thread_context(thread_key)
```

### Business Goals Replacement
Replace this pattern:
```python
# OLD: JSON file loading
with open('business_goals.json', 'r') as f:
    business_goals = json.load(f)
```

With:
```python
# NEW: Database queries
business_goals = db_manager.get_business_goals()
```

## Maintenance and Operations

### Backup Strategy
```python
# Manual backup
backup_path = db_manager.backup_database()
print(f"Database backed up to: {backup_path}")

# Automated backup (can be scheduled)
def daily_backup():
    timestamp = datetime.now().strftime("%Y%m%d")
    backup_path = f"backups/opsbrain_backup_{timestamp}.db"
    return db_manager.backup_database(backup_path)
```

### Performance Monitoring
```python
# Get database statistics
db_info = db_manager.get_database_info()
print(f"Database size: {db_info['database_size_bytes']} bytes")
print(f"Total records: {db_info['total_records']}")

# Monitor performance metrics
metrics = db_manager.get_performance_metrics(hours=24)
avg_response_time = sum(m['metric_value'] for m in metrics if m['metric_name'] == 'response_time') / len(metrics)
```

### Cleanup Operations
```python
# Manual cleanup of expired threads
cleaned = db_manager.cleanup_expired_threads()
print(f"Cleaned up {cleaned} expired thread contexts")

# Scheduled cleanup (can be run daily)
def cleanup_old_data():
    # Cleanup expired threads
    db_manager.cleanup_expired_threads()
    
    # Archive old performance metrics (keep 30 days)
    # Implementation depends on specific retention requirements
```

## Security Considerations

### Sensitive Data Handling
- API keys and tokens marked as `is_sensitive=True`
- Sensitive configurations not logged in plain text
- Database file should be protected with appropriate file permissions

### Access Control
```bash
# Set appropriate permissions on database file
chmod 600 opsbrain.db  # Owner read/write only
```

### Backup Security
- Backup files contain sensitive data
- Store backups securely with encryption if needed
- Regular backup rotation and cleanup

## Troubleshooting

### Common Issues

1. **Database Lock Errors**
   ```python
   # Issue: Database is locked
   # Solution: Ensure connections are properly closed
   with db_manager.get_connection() as conn:
       # Do database operations
       pass  # Connection auto-closed
   ```

2. **Migration Failures**
   ```bash
   # Check migration logs
   ls migration_backups/
   cat migration_backups/migration_log_*.json
   ```

3. **Performance Issues**
   ```python
   # Check database size and optimize
   info = db_manager.get_database_info()
   if info['database_size_bytes'] > 100_000_000:  # 100MB
       # Consider cleanup or archiving
       db_manager.cleanup_expired_threads()
   ```

### Diagnostic Commands
```python
# Database health check
def health_check():
    try:
        # Test basic operations
        db_manager.set_config('health_check', 'ok')
        value = db_manager.get_config('health_check')
        db_manager.delete_config('health_check')
        
        if value == 'ok':
            print("✅ Database is healthy")
            return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False
```

## Future Enhancements

### Phase 2 Features
- [ ] Configuration encryption at rest
- [ ] Multi-user support with role-based access
- [ ] Configuration versioning and rollback
- [ ] Real-time configuration updates
- [ ] Database replication for high availability

### Performance Optimizations
- [ ] Connection pooling for high concurrency
- [ ] Query optimization and indexing
- [ ] Automated performance monitoring
- [ ] Data archiving strategies

## Testing

### Run Complete Test Suite
```bash
# Test all database functionality
python test_database.py

# Expected output:
# ✅ Configuration management
# ✅ Thread context management  
# ✅ Business goals management
# ✅ Application settings
# ✅ Performance metrics
# ✅ Database info and cleanup
# ✅ JSON migration
# 
# 📊 Test Results:
#    Passed: 7/7
#    Success Rate: 100.0%
# ✅ All tests passed!
```

### Integration Tests
After migration, run existing test suite to ensure compatibility:
```bash
# Run application tests with new database
python -m pytest tests/ -v
```

## Conclusion

The database implementation provides:
- **Reliability**: Persistent storage survives restarts
- **Scalability**: Easy to add new configuration types  
- **Maintainability**: Centralized data management
- **Performance**: Fast queries with proper indexing
- **Security**: Proper handling of sensitive data
- **Observability**: Performance metrics and audit trails

This foundation enables OpsBrain to scale efficiently while maintaining data integrity and providing better user experience through persistent conversation contexts.
