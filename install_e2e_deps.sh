#!/bin/bash

# Install E2E Testing Dependencies
# This script installs all required dependencies for UI and Slack E2E testing

set -e

echo "🔧 Installing E2E Testing Dependencies"
echo "====================================="

# Check if Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is required but not installed."
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "🐍 Using Python: $PYTHON_CMD"

# Install core dependencies
echo "📦 Installing core Python packages..."
$PYTHON_CMD -m pip install --upgrade pip

# Install web UI testing dependencies
echo "🌐 Installing UI testing dependencies..."
$PYTHON_CMD -m pip install streamlit selenium webdriver-manager

# Install API testing dependencies
echo "🔌 Installing API testing dependencies..."
$PYTHON_CMD -m pip install requests pytest pytest-asyncio

# Install FastAPI server dependencies (if not already installed)
echo "⚡ Installing server dependencies..."
$PYTHON_CMD -m pip install fastapi uvicorn

# Check if Chrome is available (needed for UI tests)
echo "🔍 Checking for Chrome browser..."
if command -v google-chrome &> /dev/null; then
    echo "✅ Google Chrome found"
elif command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium browser found"
elif command -v chromium &> /dev/null; then
    echo "✅ Chromium found"
else
    echo "⚠️  Chrome/Chromium not found. UI tests may fail."
    echo "   Install Chrome: https://www.google.com/chrome/"
    echo "   Or install Chromium: sudo apt install chromium-browser (Linux)"
fi

# Make test scripts executable
echo "🔐 Making test scripts executable..."
chmod +x test_e2e_ui.py 2>/dev/null || true
chmod +x test_slack_integration.py 2>/dev/null || true
chmod +x run_e2e_tests.py 2>/dev/null || true

# Verify installation
echo ""
echo "✅ Verifying installation..."

# Test imports
$PYTHON_CMD -c "import streamlit; print('✅ Streamlit installed')" 2>/dev/null || echo "❌ Streamlit installation failed"
$PYTHON_CMD -c "import selenium; print('✅ Selenium installed')" 2>/dev/null || echo "❌ Selenium installation failed"
$PYTHON_CMD -c "import requests; print('✅ Requests installed')" 2>/dev/null || echo "❌ Requests installation failed"
$PYTHON_CMD -c "from webdriver_manager.chrome import ChromeDriverManager; print('✅ WebDriver Manager installed')" 2>/dev/null || echo "❌ WebDriver Manager installation failed"

echo ""
echo "🚀 E2E Testing Dependencies Installation Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Run comprehensive E2E tests:"
echo "   python run_e2e_tests.py"
echo ""
echo "2. Run individual test suites:"
echo "   python test_e2e_ui.py"
echo "   python test_slack_integration.py https://your-app-url.com"
echo ""
echo "3. For production testing with real Slack credentials:"
echo "   python test_slack_integration.py https://your-app.com --signing-secret YOUR_SECRET"
echo ""
