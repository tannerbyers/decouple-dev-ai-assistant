# End-to-End Testing Guide for CEO Operator

This guide explains how to use the comprehensive E2E testing suite to verify that both your UI dashboard and Slack API integrations are working correctly.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install all required E2E testing dependencies
./install_e2e_deps.sh
```

### 2. Run All Tests

```bash
# Run comprehensive E2E test suite (UI + Slack + Integration)
python run_e2e_tests.py
```

### 3. For Production Testing

```bash
# Test your deployed Slack endpoint (uses .env automatically)
python run_e2e_tests.py

# Or test a different URL
python run_e2e_tests.py --slack-url https://your-other-app.com
```

## 📋 Test Suites

### 1. UI Dashboard Tests (`test_e2e_ui.py`)

Tests the Streamlit dashboard functionality:

- **Dashboard Page Load**: Verifies the dashboard loads successfully
- **Sidebar Navigation**: Checks interactive sidebar elements
- **Metrics Display**: Validates business metrics are shown
- **Interactive Elements**: Tests buttons, inputs, and controls
- **Data Visualization**: Verifies charts and graphs render
- **Responsive Design**: Tests different screen sizes

```bash
# Run only UI tests
python test_e2e_ui.py --port 8501 --timeout 60
```

### 2. Slack Integration Tests (`test_slack_integration.py`)

Tests your deployed Slack bot endpoint:

#### Basic Infrastructure Tests:
- **Connectivity**: Endpoint reachability
- **HTTPS/SSL**: Certificate validation
- **Endpoint Exists**: `/slack` route availability
- **URL Verification**: Slack challenge handling
- **Signature Verification**: Security validation
- **Error Handling**: Invalid input handling
- **Response Times**: Performance validation

#### Core Workflow Tests:
- **Slash Commands**: `/ai` command processing
- **Event Callbacks**: Message event handling
- **Help Commands**: Help system functionality
- **Thread Context**: Conversation continuity
- **Concurrent Requests**: Load handling

```bash
# Test production deployment (uses .env automatically)
python test_slack_integration.py

# Test local development server
python test_slack_integration.py http://localhost:8000

# Test different URL
python test_slack_integration.py https://your-other-app.com

# Override signing secret (otherwise uses .env)
python test_slack_integration.py --signing-secret YOUR_OTHER_SECRET
```

### 3. Integration Tests (Existing pytest suite)

Runs your existing integration tests for business logic validation.

```bash
# Run integration tests only
python -m pytest tests/integration/ -v
```

## 🔧 Understanding Test Results

### Test Output Format

```
✅ PASS | Test Name
     Success message
     Details: Additional information

❌ FAIL | Test Name
     Error message
     Details: Specific error details
```

### Common Test Scenarios

#### 1. All Tests Passing ✅
```
✅ PASS | UI Tests           |   6/  6 passed (100.0%)
✅ PASS | Slack Tests        |  13/ 13 passed (100.0%)
✅ PASS | Integration Tests  |   3/  3 passed (100.0%)
----------------------------------------
✅ PASS | OVERALL           |  22/ 22 passed (100.0%)
```

Your application is working perfectly!

#### 2. Signature Verification Issues ⚠️
```
❌ FAIL | Slash Command Workflow
     Slash command failed: 403
     Details: {"detail":"Invalid Slack signature"}
```

**Solution**: Provide your real Slack signing secret:
```bash
python test_slack_integration.py https://your-app.com --signing-secret YOUR_REAL_SECRET
```

#### 3. UI Loading Issues ❌
```
❌ FAIL | Dashboard Page Load
     Dashboard page load timed out
     Details: Page failed to load within 30 seconds
```

**Solutions**:
- Check if Streamlit is installed: `pip install streamlit`
- Verify Chrome/ChromeDriver is available
- Check for port conflicts on 8501

#### 4. Connectivity Issues 🌐
```
❌ FAIL | Basic Connectivity
     Cannot reach endpoint
     Details: Connection timeout
```

**Solutions**:
- Verify your app is deployed and running
- Check the URL is correct
- Ensure firewall/network settings allow connections

## 🛠️ Troubleshooting

### UI Test Issues

1. **Chrome/ChromeDriver Missing**:
   ```bash
   # Install Chrome (macOS)
   brew install google-chrome
   
   # Install ChromeDriver automatically
   pip install webdriver-manager
   ```

2. **Streamlit Import Errors**:
   ```bash
   pip install streamlit plotly pandas
   ```

3. **Port Conflicts**:
   ```bash
   # Use different port
   python test_e2e_ui.py --port 8502
   ```

### Slack Test Issues

1. **403 Signature Errors** (Expected in production):
   - Use real signing secret from Slack app settings
   - Or test in TEST_MODE with local server

2. **SSL Certificate Errors**:
   - Ensure your deployment uses HTTPS
   - Check certificate is valid and not expired

3. **Timeout Issues**:
   - Increase timeout: `--timeout 60`
   - Check if your server is overloaded

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        ./install_e2e_deps.sh
        
    - name: Run E2E tests
      run: |
        python run_e2e_tests.py --slack-url ${{ secrets.SLACK_ENDPOINT_URL }}
      env:
        SLACK_SIGNING_SECRET: ${{ secrets.SLACK_SIGNING_SECRET }}
```

## 📊 Test Coverage

### What These Tests Validate

✅ **UI Functionality**:
- Dashboard loads and renders correctly
- Interactive elements work
- Responsive design works across devices
- Charts and visualizations display

✅ **Slack Integration**:
- Webhook endpoint is accessible
- Security (HTTPS, signatures) is working
- All core commands process correctly
- Thread context is maintained
- Performance meets Slack requirements

✅ **Business Logic**:
- Task creation workflows
- Help system functionality
- Error handling and recovery
- Concurrent request processing

### What's NOT Covered

❌ **External API Calls**:
- Real Notion API interactions
- Real OpenAI API calls
- Real Trello API calls

❌ **Database Persistence**:
- Data consistency across restarts
- Database migration scenarios

❌ **Authentication**:
- User authentication flows
- Permission/authorization checks

## 🎯 Production Checklist

Before deploying to production, ensure:

1. **All E2E tests pass**: `python run_e2e_tests.py --slack-url YOUR_PROD_URL --signing-secret YOUR_SECRET`
2. **Performance tests pass**: Response times < 3 seconds
3. **Security tests pass**: Signature verification working
4. **SSL certificate is valid**: HTTPS properly configured
5. **Environment variables set**: All required vars in production
6. **Monitoring configured**: Health checks and alerting set up

## 📚 Additional Resources

- [Slack API Testing Guide](https://api.slack.com/authentication/verifying-requests-from-slack)
- [Streamlit Testing Documentation](https://docs.streamlit.io/library/advanced-features/testing)
- [Selenium Testing Best Practices](https://selenium-python.readthedocs.io/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)

---

## 🆘 Need Help?

If you encounter issues:

1. **Check the logs**: Test output includes detailed error information
2. **Run individual tests**: Isolate the problem by running specific test suites
3. **Verify dependencies**: Ensure all required packages are installed
4. **Check environment**: Verify environment variables and network connectivity
5. **Review this guide**: Many common issues have solutions documented here

The E2E test suite is designed to catch integration issues early and ensure your CEO Operator system works reliably in production! 🚀
