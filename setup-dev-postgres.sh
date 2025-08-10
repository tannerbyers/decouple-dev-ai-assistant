#!/bin/bash

echo "🚀 Setting up consistent PostgreSQL development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Create .env.dev for development if it doesn't exist
if [ ! -f .env.dev ]; then
    echo "📝 Creating .env.dev for consistent development environment..."
    cat > .env.dev << EOF
# Development Database Configuration
DATABASE_URL=postgresql://opsbrain_user:dev_password_123@localhost:5432/opsbrain_dev

# Your existing environment variables (copy from .env)
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_SIGNING_SECRET=your_slack_signing_secret
NOTION_API_KEY=your_notion_api_key
NOTION_DB_ID=your_notion_db_id
OPENAI_API_KEY=your_openai_api_key

# Optional database IDs
NOTION_GOALS_DB_ID=
NOTION_CLIENTS_DB_ID=
NOTION_PROJECTS_DB_ID=
NOTION_METRICS_DB_ID=

# Development settings
TEST_MODE=false
EOF
    echo "✅ Created .env.dev - please update it with your actual API keys"
else
    echo "📋 .env.dev already exists"
fi

# Start PostgreSQL development database
echo "🐘 Starting PostgreSQL development database..."
docker-compose --profile dev up -d postgres-dev

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker-compose exec postgres-dev pg_isready -U opsbrain_user -d opsbrain_dev > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    echo "❌ PostgreSQL failed to start within 60 seconds"
    exit 1
fi

# Run database migration to set up schema
echo "🔧 Setting up database schema..."
if [ -f migrate_to_production.py ]; then
    DATABASE_URL=postgresql://opsbrain_user:dev_password_123@localhost:5432/opsbrain_dev python migrate_to_production.py
    echo "✅ Database schema created"
else
    echo "⚠️  migrate_to_production.py not found - you may need to run schema setup manually"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env.dev with your actual API keys"
echo "2. Run: export DATABASE_URL=postgresql://opsbrain_user:dev_password_123@localhost:5432/opsbrain_dev"
echo "3. Or use: source .env.dev (if you have a script to load env files)"
echo "4. Start your application normally: python src/main.py"
echo ""
echo "🛠️  Optional tools:"
echo "• pgAdmin: docker-compose --profile tools up -d pgadmin"
echo "• Access pgAdmin at http://localhost:5050 (admin@opsbrain.dev / admin123)"
echo ""
echo "🧹 To clean up: docker-compose --profile dev down -v"
