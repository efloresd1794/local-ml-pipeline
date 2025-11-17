#!/usr/bin/env python3
"""
Simple web server to serve the ML prediction GUI
Serves static files with CORS enabled
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path


class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler with CORS headers"""

    def end_headers(self):
        """Add CORS headers to all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def serve(port=8080):
    """Start the web server"""
    # Change to web directory
    web_dir = Path(__file__).parent
    os.chdir(web_dir)

    # Create server
    handler = CORSHTTPRequestHandler

    with socketserver.TCPServer(("", port), handler) as httpd:
        print("=" * 60)
        print("🌐 ML House Price Predictor - Web Interface")
        print("=" * 60)
        print(f"\n✅ Server running at: http://localhost:{port}")
        print(f"📁 Serving files from: {web_dir}")
        print("\n📖 Instructions:")
        print("   1. Open http://localhost:{port} in your browser")
        print("   2. Make sure LocalStack is running")
        print("   3. Enter your API Gateway URL")
        print("   4. Start making predictions!")
        print("\n🛑 Press Ctrl+C to stop the server")
        print("=" * 60 + "\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    # Get port from command line argument or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    serve(port)
