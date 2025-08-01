#!/usr/bin/env python3
"""
Alternative server startup script with better error handling
"""

import subprocess
import sys
import socket
import time
from pathlib import Path

def check_port(host, port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0  # Port is available if connection fails
    except:
        return False

def find_available_port(start_port=8501):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + 20):
        if check_port('127.0.0.1', port):
            return port
    return None

def start_streamlit_app(app_file, port):
    """Start a Streamlit app on the specified port"""
    try:
        print(f"🚀 Starting {app_file} on port {port}...")
        
        cmd = [
            sys.executable, '-m', 'streamlit', 'run', app_file,
            '--server.port', str(port),
            '--server.address', '127.0.0.1',
            '--server.headless', 'true',
            '--server.enableCORS', 'false',
            '--server.enableXsrfProtection', 'false',
            '--server.runOnSave', 'false'
        ]
        
        process = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Give it a moment to start
        time.sleep(3)
        
        if process.poll() is None:  # Process is still running
            print(f"✅ Server started successfully!")
            print(f"🌐 Access at: http://127.0.0.1:{port}")
            print(f"🌐 Or try: http://localhost:{port}")
            return process, port
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start server:")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None, None

def main():
    """Main function"""
    print("🔧 Commission Calculator Pro - Server Startup")
    print("=" * 50)
    
    # Change to app directory
    app_dir = Path(__file__).parent
    print(f"📁 Working directory: {app_dir}")
    
    # Apps to start
    apps = [
        ('test_app.py', '🧪 Test App'),
        ('debug_main_app.py', '🐛 Debug App'),
        ('app.py', '💰 Main App')
    ]
    
    running_servers = []
    
    for app_file, app_name in apps:
        if not Path(app_file).exists():
            print(f"⚠️ {app_file} not found, skipping...")
            continue
            
        port = find_available_port(8501 + len(running_servers))
        if port is None:
            print(f"❌ No available ports found for {app_name}")
            continue
            
        process, actual_port = start_streamlit_app(app_file, port)
        if process and actual_port:
            running_servers.append({
                'name': app_name,
                'file': app_file,
                'port': actual_port,
                'process': process,
                'url': f'http://127.0.0.1:{actual_port}'
            })
    
    if running_servers:
        print("\n🎉 Servers Started Successfully!")
        print("=" * 50)
        for server in running_servers:
            print(f"{server['name']}: {server['url']}")
        
        print(f"\n🔑 Login credentials (for main app):")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        
        print(f"\n💡 Troubleshooting tips:")
        print(f"   • Try both 127.0.0.1 and localhost URLs")
        print(f"   • Check firewall settings")
        print(f"   • Try different browsers")
        print(f"   • Disable antivirus temporarily")
        
        print(f"\n⏰ Servers will run until you stop this script...")
        
        try:
            # Keep running
            while True:
                time.sleep(1)
                # Check if any process has died
                for server in running_servers[:]:  # Copy list to avoid modification during iteration
                    if server['process'].poll() is not None:  # Process has terminated
                        print(f"⚠️ {server['name']} has stopped")
                        running_servers.remove(server)
                
                if not running_servers:
                    print("❌ All servers have stopped")
                    break
                    
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping servers...")
            for server in running_servers:
                server['process'].terminate()
            print("👋 All servers stopped")
    
    else:
        print("❌ No servers could be started")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())