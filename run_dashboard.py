#!/usr/bin/env python3
"""
CEO Operator Dashboard Runner
Simple script to start the dashboard with proper setup.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def check_requirements():
    """Check if dashboard requirements are installed"""
    try:
        import streamlit
        import plotly
        import pandas
        print("✅ Dashboard dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n📦 Install dashboard requirements with:")
        print("pip install -r dashboard_requirements.txt")
        return False

def check_environment():
    """Check if environment variables are set"""
    required_vars = ['NOTION_TOKEN', 'NOTION_DATABASE_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Dashboard will run but some features may be limited")
    else:
        print("✅ Environment variables configured")
    
    return len(missing_vars) == 0

def main():
    """Main entry point"""
    print("🎯 CEO Operator Dashboard Startup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("dashboard.py").exists():
        print("❌ dashboard.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    env_ok = check_environment()
    
    print("\n🚀 Starting CEO Operator Dashboard...")
    print("📊 Dashboard will open in your browser")
    print("💡 Use Ctrl+C to stop the dashboard")
    print("=" * 40)
    
    try:
        # Start the Streamlit dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard.py",
            "--server.address", "localhost",
            "--server.port", "8501",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
