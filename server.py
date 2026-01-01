#!/usr/bin/env python3
"""Simple HTTP server for the Stoicism presentation app."""

import http.server
import socketserver
import webbrowser
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"\n🎓 Stoicism Presentation Server")
        print(f"=" * 50)
        print(f"Server running at: {url}")
        print(f"\nPress Ctrl+C to stop the server")
        print(f"=" * 50)

        # Open browser automatically
        webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✓ Server stopped.")

if __name__ == "__main__":
    main()
