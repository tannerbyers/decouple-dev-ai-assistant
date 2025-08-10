# Development Setup Guide

## Consistent Database Environment

To ensure consistency between development and production environments, we recommend using PostgreSQL for both. This eliminates potential differences between SQLite (dev) and PostgreSQL (prod).

### Option 1: Quick PostgreSQL Setup (Recommended)

```bash
# Run the automated setup script
./setup-dev-postgres.sh
```

This will:
- Start a PostgreSQL container for development
- Create the database schema
- Generate `.env.dev` with the correct DATABASE_URL
- Provide next steps

### Option 2: Manual PostgreSQL Setup

1. **Start PostgreSQL container:**
```bash
docker-compose --profile dev up -d postgres-dev
```

2. **Set environment variable:**
```bash
export DATABASE_URL=postgresql://opsbrain_user:dev_password_123@localhost:5432/opsbrain_dev
```

3. **Initialize database schema:**
```bash
python migrate_to_production.py
```

### Option 3: Keep SQLite for Development

If you prefer SQLite for development simplicity:
```bash
# Don't set DATABASE_URL - app will use SQLite by default
unset DATABASE_URL
python src/main.py
```

**Note:** This approach may lead to subtle differences between environments.

## Database Management Tools

### pgAdmin (Web UI)
```bash
# Start pgAdmin
docker-compose --profile tools up -d pgadmin

# Access at http://localhost:5050
# Email: admin@opsbrain.dev
# Password: admin123
```

### Direct PostgreSQL Access
```bash
# Connect to the database directly
docker-compose exec postgres-dev psql -U opsbrain_user -d opsbrain_dev
```

## Environment Variables

### Development (.env.dev)
```bash
# Database - PostgreSQL for consistency
DATABASE_URL=postgresql://opsbrain_user:dev_password_123@localhost:5432/opsbrain_dev

# Your API keys
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
NOTION_API_KEY=secret_your-key
NOTION_DB_ID=your-db-id
OPENAI_API_KEY=sk-your-key
```

### Production (Render.com)
```bash
# Automatically managed by Render
DATABASE_URL=postgresql://user:pass@host:5432/db_name
```

## Benefits of Consistent Database Setup

✅ **No environment-specific bugs**  
✅ **Identical SQL behavior**  
✅ **Same data types and constraints**  
✅ **Consistent testing**  
✅ **Production-like development experience**

## Migration Path

If you're currently using SQLite in development:

1. **Backup your current data:**
```bash
# SQLite databases are in the project root
cp *.db backup/
```

2. **Run the setup script:**
```bash
./setup-dev-postgres.sh
```

3. **Migrate data (optional):**
```bash
# The migration script can transfer SQLite data to PostgreSQL
DATABASE_URL=postgresql://opsbrain_user:dev_password_123@localhost:5432/opsbrain_dev python migrate_to_production.py
```

## Cleanup

To remove the development PostgreSQL setup:
```bash
# Stop and remove containers and volumes
docker-compose --profile dev down -v
docker-compose --profile tools down -v
```

## Troubleshooting

**PostgreSQL won't start:**
```bash
# Check Docker is running
docker info

# Check logs
docker-compose logs postgres-dev
```

**Connection errors:**
```bash
# Verify PostgreSQL is ready
docker-compose exec postgres-dev pg_isready -U opsbrain_user -d opsbrain_dev

# Check the DATABASE_URL format
echo $DATABASE_URL
```

**Schema issues:**
```bash
# Recreate the database
docker-compose exec postgres-dev psql -U opsbrain_user -c "DROP DATABASE IF EXISTS opsbrain_dev; CREATE DATABASE opsbrain_dev;"
python migrate_to_production.py
```
