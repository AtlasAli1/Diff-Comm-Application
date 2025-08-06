#!/usr/bin/env python3
"""
Startup script for Commission Calculator Pro API
"""

import uvicorn
import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description='Start Commission Calculator Pro API')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes')
    parser.add_argument('--log-level', default='info', choices=['debug', 'info', 'warning', 'error'])
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ['API_HOST'] = args.host
    os.environ['API_PORT'] = str(args.port)
    
    print(f"🚀 Starting Commission Calculator Pro API...")
    print(f"📍 Server will be available at: http://{args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔄 Auto-reload: {'Enabled' if args.reload else 'Disabled'}")
    
    try:
        uvicorn.run(
            "api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1,
            log_level=args.log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n📴 API server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()