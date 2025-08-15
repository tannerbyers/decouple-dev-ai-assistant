# Manual Tests

This directory contains tests that require special setup or dependencies and are not suitable for automated CI/CD pipelines.

## UI End-to-End Tests

### test_e2e_ui.py

Tests the Streamlit dashboard UI functionality using Selenium WebDriver.

**Requirements:**
- `selenium` package
- `webdriver-manager` package  
- Chrome browser installed
- ChromeDriver (automatically managed by webdriver-manager)

**To run:**
```bash
# Install dependencies
pip install selenium webdriver-manager

# Run the UI tests
python manual_tests/test_e2e_ui.py

# Run with custom port
python manual_tests/test_e2e_ui.py --port 8502 --timeout 60
```

**What it tests:**
- Dashboard page loading
- Sidebar navigation
- Metrics display
- Interactive elements (buttons, inputs, etc.)
- Data visualization (charts)
- Responsive design across different screen sizes

**Note:** These tests start a real Streamlit server and use a real browser (headless Chrome) to interact with the UI, so they take longer than unit tests and require more system resources.
