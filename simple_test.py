#!/usr/bin/env python3
"""
Simple test server to verify network connectivity
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html_content = """
        <html>
        <head><title>Commission Calculator Pro - Test</title></head>
        <body>
            <h1>Network Test Successful!</h1>
            <p>If you can see this page, the network is working.</p>
            <p>The Commission Calculator Pro should work on this same IP address.</p>
            <hr>
            <p>Next step: Try the full application</p>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))

if __name__ == '__main__':
    port = 8080
    server = HTTPServer(('0.0.0.0', port), MyHandler)
    print(f"Test server running on:")
    print(f"  - http://localhost:{port}")
    print(f"  - http://127.0.0.1:{port}")
    print(f"  - http://0.0.0.0:{port}")
    print("\nPress Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()