#!/usr/bin/env python3
"""
Production Deployment Diagnosis Script
Helps identify why the dashboard doesn't work in production while health endpoint does
"""

import os
import sys
import requests
import json
import time
from typing import Dict, Any, Optional

def check_production_url(base_url: str) -> Dict[str, Any]:
    """Check various endpoints on the production URL."""
    results = {}
    
    endpoints = {
        'health': '/',
        'health_alt': '/health', 
        'dashboard': '/dashboard',
        'dashboard_health': '/dashboard/health',
        'dashboard_api_metrics': '/dashboard/api/metrics'
    }
    
    for name, path in endpoints.items():
        url = f"{base_url.rstrip('/')}{path}"
        try:
            print(f"Testing {name}: {url}")
            
            response = requests.get(url, timeout=10)
            results[name] = {
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'content_type': response.headers.get('content-type', ''),
                'content_length': len(response.content),
                'response_time': response.elapsed.total_seconds()
            }
            
            # Store partial content for analysis
            if response.status_code == 200:
                content = response.text[:500] if len(response.text) > 500 else response.text
                results[name]['content_preview'] = content
            else:
                results[name]['error'] = response.text[:200]
                
            print(f"  ✅ Status: {response.status_code}, Time: {response.elapsed.total_seconds():.2f}s")
            
        except requests.exceptions.Timeout:
            results[name] = {'error': 'Request timeout', 'success': False}
            print(f"  ❌ Timeout")
            
        except requests.exceptions.ConnectionError as e:
            results[name] = {'error': f'Connection error: {str(e)}', 'success': False}
            print(f"  ❌ Connection error: {e}")
            
        except Exception as e:
            results[name] = {'error': f'Unexpected error: {str(e)}', 'success': False}
            print(f"  ❌ Error: {e}")
    
    return results

def analyze_deployment_config() -> Dict[str, Any]:
    """Analyze deployment configuration for potential issues."""
    config_analysis = {}
    
    # Check if key files exist
    key_files = [
        'main.py',
        'src/web_dashboard.py', 
        'src/config_manager.py',
        'src/database.py',
        'render.yaml',
        'Dockerfile',
        'requirements.txt'
    ]
    
    config_analysis['files'] = {}
    for file_path in key_files:
        config_analysis['files'][file_path] = os.path.exists(file_path)
    
    # Check render.yaml configuration
    if os.path.exists('render.yaml'):
        try:
            with open('render.yaml', 'r') as f:
                render_config = f.read()
                config_analysis['render_yaml'] = {
                    'exists': True,
                    'has_dashboard_routes': 'dashboard' in render_config.lower(),
                    'start_command': 'startCommand' in render_config,
                    'build_command': 'buildCommand' in render_config
                }
        except Exception as e:
            config_analysis['render_yaml'] = {'error': str(e)}
    
    # Check requirements.txt for necessary dependencies
    if os.path.exists('requirements.txt'):
        try:
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
                config_analysis['requirements'] = {
                    'has_fastapi': 'fastapi' in requirements.lower(),
                    'has_streamlit': 'streamlit' in requirements.lower(),
                    'has_jinja2': 'jinja2' in requirements.lower(),
                    'has_tailwind_note': 'tailwind' in requirements.lower()
                }
        except Exception as e:
            config_analysis['requirements'] = {'error': str(e)}
    
    return config_analysis

def check_dashboard_integration() -> Dict[str, Any]:
    """Check if dashboard is properly integrated in main.py."""
    integration_status = {}
    
    if os.path.exists('main.py'):
        try:
            with open('main.py', 'r') as f:
                main_content = f.read()
                
            integration_status['main_py'] = {
                'imports_web_dashboard': 'from src.web_dashboard import' in main_content,
                'imports_config_manager': 'from src.config_manager import' in main_content,
                'calls_integration': 'integrate_dashboard_with_main_app' in main_content,
                'has_dashboard_routes': '/dashboard' in main_content,
                'fastapi_app_exists': 'app = FastAPI()' in main_content
            }
        except Exception as e:
            integration_status['main_py'] = {'error': str(e)}
    
    # Check if dashboard files exist and are importable
    dashboard_files = [
        'src/web_dashboard.py',
        'src/config_manager.py', 
        'src/database.py'
    ]
    
    integration_status['dashboard_files'] = {}
    for file_path in dashboard_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    integration_status['dashboard_files'][file_path] = {
                        'exists': True,
                        'has_routes': '@dashboard_router' in content or '@app.' in content,
                        'has_integration_func': 'integrate_dashboard_with_main_app' in content,
                        'size_kb': len(content) // 1024
                    }
            except Exception as e:
                integration_status['dashboard_files'][file_path] = {'error': str(e)}
        else:
            integration_status['dashboard_files'][file_path] = {'exists': False}
    
    return integration_status

def identify_potential_issues(results: Dict[str, Any], config: Dict[str, Any], integration: Dict[str, Any]) -> list:
    """Identify potential issues based on test results."""
    issues = []
    
    # Check if health endpoints work but dashboard doesn't
    health_works = results.get('health', {}).get('success', False)
    dashboard_works = results.get('dashboard', {}).get('success', False)
    
    if health_works and not dashboard_works:
        dashboard_status = results.get('dashboard', {}).get('status_code')
        if dashboard_status == 404:
            issues.append("🔍 Dashboard returns 404 - routes may not be properly registered")
        elif dashboard_status == 500:
            issues.append("🔍 Dashboard returns 500 - likely import or initialization error")
        elif dashboard_status is None:
            issues.append("🔍 Dashboard not responding - server may be rejecting the route")
    
    # Check for missing dependencies
    reqs = config.get('requirements', {})
    if not reqs.get('has_jinja2', False):
        issues.append("🔍 Missing jinja2 dependency - required for HTML template rendering")
    
    # Check integration issues
    main_integration = integration.get('main_py', {})
    if not main_integration.get('imports_web_dashboard', False):
        issues.append("🔍 main.py doesn't import web_dashboard module")
    
    if not main_integration.get('calls_integration', False):
        issues.append("🔍 main.py doesn't call integrate_dashboard_with_main_app()")
    
    # Check file existence
    if not config.get('files', {}).get('src/web_dashboard.py', False):
        issues.append("🔍 src/web_dashboard.py file is missing")
    
    # Check dashboard route registration
    dashboard_health = results.get('dashboard_health', {})
    if dashboard_health.get('status_code') == 404:
        issues.append("🔍 Dashboard health endpoint not found - routes not registered")
    
    return issues

def suggest_fixes(issues: list) -> list:
    """Suggest fixes for identified issues."""
    fixes = []
    
    issue_text = " ".join(issues)
    
    if "routes may not be properly registered" in issue_text:
        fixes.append("✅ Ensure integrate_dashboard_with_main_app(app) is called in main.py")
        fixes.append("✅ Check that dashboard_router is properly defined in web_dashboard.py")
    
    if "import" in issue_text:
        fixes.append("✅ Verify all src/ modules are properly structured with __init__.py")
        fixes.append("✅ Check import paths are correct (relative vs absolute imports)")
    
    if "jinja2" in issue_text:
        fixes.append("✅ Add 'jinja2' to requirements.txt")
        fixes.append("✅ Redeploy after updating requirements")
    
    if "500" in issue_text:
        fixes.append("✅ Check application logs for specific error details")
        fixes.append("✅ Test imports locally: python -c 'from src.web_dashboard import dashboard_router'")
    
    if len(issues) == 0:
        fixes.append("✅ All basic checks passed - issue may be environment-specific")
        fixes.append("✅ Check Render.com deployment logs for detailed error messages")
    
    return fixes

def main():
    """Main diagnosis function."""
    print("🔍 OpsBrain Production Deployment Diagnosis")
    print("=" * 50)
    
    # Get production URL from environment variable or use default
    production_url = os.getenv('PRODUCTION_URL', 'https://decouple-ai.onrender.com')
    
    print(f"Using production URL: {production_url}")
    
    print(f"\n📊 Testing endpoints on: {production_url}")
    print("-" * 50)
    
    # Test production endpoints
    results = check_production_url(production_url)
    
    print(f"\n📁 Analyzing local deployment configuration...")
    print("-" * 50)
    
    # Analyze local configuration
    config = analyze_deployment_config()
    integration = check_dashboard_integration()
    
    # Print results
    print(f"\n📋 Results Summary:")
    print("-" * 50)
    
    working_endpoints = [name for name, result in results.items() if result.get('success')]
    broken_endpoints = [name for name, result in results.items() if not result.get('success')]
    
    print(f"✅ Working endpoints: {', '.join(working_endpoints) if working_endpoints else 'None'}")
    print(f"❌ Broken endpoints: {', '.join(broken_endpoints) if broken_endpoints else 'None'}")
    
    # Identify issues
    issues = identify_potential_issues(results, config, integration)
    
    print(f"\n🔍 Identified Issues:")
    print("-" * 50)
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print("  ✅ No obvious issues detected")
    
    # Suggest fixes
    fixes = suggest_fixes(issues)
    
    print(f"\n💡 Suggested Fixes:")
    print("-" * 50)
    for fix in fixes:
        print(f"  {fix}")
    
    # Output detailed JSON for further analysis
    detailed_results = {
        'timestamp': time.time(),
        'production_url': production_url,
        'endpoint_tests': results,
        'config_analysis': config,
        'integration_analysis': integration,
        'identified_issues': issues,
        'suggested_fixes': fixes
    }
    
    # Save detailed results
    with open('production_diagnosis.json', 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: production_diagnosis.json")
    print(f"\n🎯 Quick Fix Commands:")
    print("-" * 50)
    print("1. Add missing dependencies:")
    print("   echo 'jinja2>=3.0.0' >> requirements.txt")
    print("\n2. Test dashboard integration locally:")
    print("   python -c 'from src.web_dashboard import integrate_dashboard_with_main_app; print(\"✅ Import successful\")'")
    print("\n3. Test local dashboard:")
    print("   uvicorn main:app --host 0.0.0.0 --port 8000")
    print("   # Then visit: http://localhost:8000/dashboard")

if __name__ == "__main__":
    main()
