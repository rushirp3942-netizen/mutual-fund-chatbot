"""
Simple HTTP server to serve the React frontend.
Since Node.js/npm is not available, we serve the static files directly.
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

# Change to the directory containing this script
os.chdir(Path(__file__).parent)

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Serving frontend at http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()
