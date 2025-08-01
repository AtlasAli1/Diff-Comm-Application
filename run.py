#!/usr/bin/env python3
"""
Commission Calculator Pro - Launch Script
Run this script to start the application
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point"""
    print("🚀 Starting Commission Calculator Pro...")
    
    # Change to app directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    
    # Check if requirements are installed
    try:
        import streamlit
        import pandas
        import plotly
        import pydantic
        import loguru
        import bcrypt
        print("✅ All dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Launch Streamlit app
    print("🌐 Launching web application...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--theme.base", "light",
            "--theme.primaryColor", "#2C5F75",
            "--theme.backgroundColor", "#FFFFFF",
            "--theme.secondaryBackgroundColor", "#F0F2F6"
        ])
    except KeyboardInterrupt:
        print("\n👋 Commission Calculator Pro stopped")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

if __name__ == "__main__":
    main()