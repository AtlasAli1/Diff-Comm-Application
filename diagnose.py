#!/usr/bin/env python3
"""
Diagnostic script to identify server issues
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python():
    """Check Python installation"""
    print("🐍 Python Check")
    print("-" * 20)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path[:3]}...")
    print()

def check_dependencies():
    """Check required dependencies"""
    print("📦 Dependencies Check")
    print("-" * 25)
    
    dependencies = [
        'pandas',
        'streamlit', 
        'plotly',
        'openpyxl',
        'datetime'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - MISSING")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing)}")
        print("Install with: pip3 install streamlit pandas plotly openpyxl")
    else:
        print("\n✅ All dependencies available")
    
    print()
    return len(missing) == 0

def check_files():
    """Check required files"""
    print("📁 Files Check")
    print("-" * 15)
    
    required_files = [
        'working_main_app.py',
        'sample_revenue_data.csv',
        'sample_timesheet_data.csv'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ Missing files: {', '.join(missing_files)}")
    else:
        print("\n✅ All required files present")
    
    print()
    return len(missing_files) == 0

def check_syntax():
    """Check Python syntax"""
    print("🔍 Syntax Check")
    print("-" * 15)
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', 'working_main_app.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ No syntax errors found")
            return True
        else:
            print("❌ Syntax errors found:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error checking syntax: {e}")
        return False

def check_ports():
    """Check if ports are available"""
    print("🌐 Port Check")
    print("-" * 13)
    
    import socket
    
    ports_to_check = [8503, 8504, 8501]
    
    for port in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                print(f"❌ Port {port} is already in use")
            else:
                print(f"✅ Port {port} is available")
        except Exception as e:
            print(f"⚠️ Port {port} check failed: {e}")
        finally:
            sock.close()
    
    print()

def suggest_fixes():
    """Suggest fixes for common issues"""
    print("🔧 Suggested Fixes")
    print("-" * 18)
    print("1. Install missing dependencies:")
    print("   pip3 install streamlit pandas plotly openpyxl")
    print()
    print("2. Start the app:")
    print("   ./start_app.sh")
    print("   OR")
    print("   python3 -m streamlit run working_main_app.py --server.port 8503")
    print()
    print("3. If port 8503 is busy, try:")
    print("   python3 -m streamlit run working_main_app.py --server.port 8505")
    print()
    print("4. For debugging, check:")
    print("   python3 test_core_logic.py")
    print()

def main():
    """Run all diagnostic checks"""
    print("🏥 Commission Calculator Pro - Diagnostic Tool")
    print("=" * 55)
    print()
    
    # Run checks
    python_ok = True
    deps_ok = check_dependencies()
    files_ok = check_files()
    syntax_ok = check_syntax()
    
    print()
    check_ports()
    
    # Summary
    print("📊 Summary")
    print("-" * 10)
    
    all_good = deps_ok and files_ok and syntax_ok
    
    if all_good:
        print("🎉 All checks passed! The app should work.")
        print("🚀 Run: ./start_app.sh")
    else:
        print("⚠️ Issues found. See suggestions below.")
        suggest_fixes()
    
    print()
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)