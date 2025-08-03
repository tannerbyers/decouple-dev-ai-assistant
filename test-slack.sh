#!/bin/bash

# Simple wrapper script for Slack integration testing
# Usage: ./test-slack.sh [URL] [SIGNING_SECRET]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default URL
DEFAULT_URL="https://decouple-ai.onrender.com"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Check if requests module is available
if ! python3 -c "import requests" 2>/dev/null; then
    print_warning "requests module not installed. Installing..."
    pip3 install requests
fi

# Get URL from argument or use default
URL=${1:-$DEFAULT_URL}
SIGNING_SECRET=$2

print_status "Testing Slack Integration for: $URL"

# Run the Python test suite
if [ -n "$SIGNING_SECRET" ]; then
    print_status "Using provided signing secret for signature testing"
    python3 test_slack_integration.py "$URL" --signing-secret "$SIGNING_SECRET"
else
    print_warning "No signing secret provided. Signature validation tests will be skipped."
    print_status "To test with signature validation, run:"
    print_status "  $0 $URL your_slack_signing_secret"
    echo
    python3 test_slack_integration.py "$URL"
fi

# Check exit code and provide guidance
if [ $? -eq 0 ]; then
    print_success "All tests passed! Your Slack integration should work."
    echo
    print_status "Next steps:"
    echo "1. Go to https://api.slack.com/apps"
    echo "2. Select your Slack app"
    echo "3. Go to 'Event Subscriptions'"
    echo "4. Enable Events and set Request URL to: $URL/slack"
    echo "5. Subscribe to 'message.channels' bot event"
    echo "6. Save changes and test by messaging your bot"
else
    print_error "Some tests failed. Please fix the issues above."
    echo
    print_status "Common fixes:"
    echo "• Check environment variables on your hosting platform"
    echo "• Ensure SLACK_SIGNING_SECRET matches your Slack app"
    echo "• Verify your app is deployed and running"
    echo "• Check the PRODUCTION_CHECKLIST.md for more details"
fi
