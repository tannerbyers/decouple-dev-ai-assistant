#!/bin/bash

# OpsBrain Deployment Script
# This script helps deploy the OpsBrain application

set -e  # Exit on any error

echo "🚀 Starting OpsBrain deployment..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found."
    exit 1
fi

# Run tests first
echo "🧪 Running tests..."
python3 -m pytest -v
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Deployment aborted."
    exit 1
fi

echo "✅ All tests passed!"

# Check for required environment variables
echo "🔍 Checking environment variables..."
required_vars=("SLACK_BOT_TOKEN" "SLACK_SIGNING_SECRET" "NOTION_API_KEY" "NOTION_DB_ID" "OPENAI_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '   - %s\n' "${missing_vars[@]}"
    echo "Please set these variables before deploying."
    exit 1
fi

echo "✅ All required environment variables are set!"

# Check if we're in production mode
if [ "${TEST_MODE}" = "true" ]; then
    echo "⚠️  Warning: TEST_MODE is enabled. Make sure to disable for production."
fi

# Health check
echo "🏥 Running health check..."
python3 -c "
import requests
import time
import subprocess
import signal
import os

# Start the server in background
proc = subprocess.Popen(['uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Give it time to start
time.sleep(3)

try:
    response = requests.get('http://localhost:8000/', timeout=5)
    if response.status_code == 200 and response.json()['status'] == 'healthy':
        print('✅ Health check passed!')
    else:
        print('❌ Health check failed:', response.text)
        exit(1)
except Exception as e:
    print('❌ Health check failed:', str(e))
    exit(1)
finally:
    # Clean up
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=5)
"

if [ $? -ne 0 ]; then
    echo "❌ Health check failed. Deployment aborted."
    exit 1
fi

echo "🎉 OpsBrain is ready for deployment!"
echo ""
echo "📋 Deployment Summary:"
echo "   - All tests passed ✅"
echo "   - Environment variables configured ✅"
echo "   - Health check passed ✅"
echo "   - Task backlog generation feature ready ✅"
echo ""
echo "To deploy to production:"
echo "   1. Set TEST_MODE=false"
echo "   2. Use: uvicorn main:app --host 0.0.0.0 --port 8000"
echo "   3. Or with gunicorn: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
echo ""
echo "🎯 OpsBrain features available:"
echo "   - Slack integration (slash commands & events)"
echo "   - Notion task management"
echo "   - Business goal tracking"
echo "   - CEO dashboard & insights"
echo "   - Intelligent task backlog generation 🆕"
echo "   - Client & metrics management"
