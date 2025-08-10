-- Configuration and Data Storage Schema for OpsBrain AI Assistant
-- SQLite Database Schema

-- Application configurations
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general', -- api, slack, notion, openai, trello, etc.
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE, -- for API keys, tokens
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Thread contexts for conversation continuity
CREATE TABLE thread_contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_key TEXT UNIQUE NOT NULL, -- "channel:thread_ts" or just "channel"
    channel_id TEXT NOT NULL,
    thread_ts TEXT, -- NULL for non-threaded conversations
    messages TEXT NOT NULL, -- JSON array of messages
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP -- for cleanup
);

-- Business goals storage (replacing JSON file)
CREATE TABLE business_goals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    area TEXT NOT NULL, -- sales, delivery, product, financial, team, process
    status TEXT NOT NULL DEFAULT 'not_started',
    priority INTEGER NOT NULL DEFAULT 2,
    target_date DATE,
    progress INTEGER DEFAULT 0, -- percentage
    weekly_actions TEXT, -- JSON array
    daily_actions TEXT, -- JSON array
    success_metrics TEXT, -- JSON object
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application settings and feature flags
CREATE TABLE app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type TEXT DEFAULT 'string', -- string, boolean, integer, json
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User preferences and customizations
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL, -- Slack user ID
    preference_key TEXT NOT NULL,
    preference_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_key)
);

-- Audit log for configuration changes
CREATE TABLE config_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    action TEXT NOT NULL, -- INSERT, UPDATE, DELETE
    old_values TEXT, -- JSON
    new_values TEXT, -- JSON
    changed_by TEXT, -- user_id or 'system'
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics and monitoring
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT, -- seconds, milliseconds, count, percentage
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    additional_data TEXT -- JSON for extra context
);

-- Indexes for better performance
CREATE INDEX idx_configurations_category ON configurations(category);
CREATE INDEX idx_configurations_key ON configurations(key);
CREATE INDEX idx_thread_contexts_channel ON thread_contexts(channel_id);
CREATE INDEX idx_thread_contexts_expires ON thread_contexts(expires_at);
CREATE INDEX idx_business_goals_area ON business_goals(area);
CREATE INDEX idx_business_goals_status ON business_goals(status);
CREATE INDEX idx_user_preferences_user ON user_preferences(user_id);
CREATE INDEX idx_config_audit_table ON config_audit(table_name, record_id);
CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- Initial configuration data
INSERT INTO configurations (key, value, category, description, is_sensitive) VALUES
('app_name', 'OpsBrain AI Assistant', 'general', 'Application name', FALSE),
('app_version', '1.0.0', 'general', 'Application version', FALSE),
('max_thread_context_messages', '10', 'general', 'Maximum messages to keep in thread context', FALSE),
('thread_context_cleanup_hours', '24', 'general', 'Hours after which thread contexts are cleaned up', FALSE),
('slack_timeout_seconds', '3', 'slack', 'Maximum response time for Slack commands', FALSE),
('openai_model', 'gpt-4', 'openai', 'Default OpenAI model to use', FALSE),
('openai_max_tokens', '1000', 'openai', 'Maximum tokens for OpenAI responses', FALSE),
('notion_timeout_seconds', '30', 'notion', 'Timeout for Notion API calls', FALSE);

-- Initial app settings
INSERT INTO app_settings (setting_key, setting_value, setting_type, description) VALUES
('enable_ceo_mode', 'true', 'boolean', 'Enable CEO-focused responses and insights'),
('enable_debug_logging', 'false', 'boolean', 'Enable detailed debug logging'),
('enable_performance_monitoring', 'true', 'boolean', 'Track and store performance metrics'),
('auto_cleanup_enabled', 'true', 'boolean', 'Automatically cleanup old thread contexts'),
('max_concurrent_requests', '10', 'integer', 'Maximum concurrent API requests');
