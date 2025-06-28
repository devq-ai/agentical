#!/usr/bin/env python3
"""
Agentical Local Status Server

This script serves the status dashboard locally for development and testing.
It generates fresh status data and serves it with auto-refresh capabilities.

Usage:
    python scripts/serve-status-local.py
    python scripts/serve-status-local.py --port 8080
    python scripts/serve-status-local.py --no-auto-refresh
"""

import http.server
import socketserver
import json
import os
import sys
import argparse
import subprocess
import webbrowser
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

class AgenticalStatusHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for serving Agentical status dashboard."""

    def __init__(self, *args, auto_refresh=True, **kwargs):
        self.auto_refresh = auto_refresh
        self.project_root = Path(__file__).parent.parent
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests with custom logic."""

        # Parse the request path
        parsed_path = urlparse(self.path)
        path = parsed_path.path.lstrip('/')

        # Handle root request
        if path == '' or path == 'index.html':
            self.serve_dashboard()
            return

        # Handle status.json request
        elif path == 'status.json':
            self.serve_status_json()
            return

        # Handle static files (if any)
        else:
            # Change to docs directory for serving
            os.chdir(self.project_root / 'docs')
            super().do_GET()
            return

    def serve_dashboard(self):
        """Serve the HTML dashboard."""

        html_content = self.generate_html_dashboard()

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def serve_status_json(self):
        """Generate and serve fresh status JSON."""

        try:
            # Generate fresh status data
            status_data = self.generate_fresh_status()

            json_content = json.dumps(status_data, indent=2, ensure_ascii=False)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(json_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(json_content.encode('utf-8'))

        except Exception as e:
            self.send_error(500, f"Error generating status: {str(e)}")

    def generate_fresh_status(self):
        """Generate fresh status data using the status generator."""

        generator_script = self.project_root / "generate_agentical_status.py"

        if not generator_script.exists():
            raise FileNotFoundError("Status generator script not found")

        # Run the status generator and capture output
        result = subprocess.run([
            sys.executable, str(generator_script), "--print"
        ], capture_output=True, text=True, cwd=self.project_root)

        if result.returncode != 0:
            raise RuntimeError(f"Status generation failed: {result.stderr}")

        # Parse the JSON from stdout (skip the log messages)
        output_lines = result.stdout.strip().split('\n')
        json_start = -1

        for i, line in enumerate(output_lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        if json_start == -1:
            raise RuntimeError("Could not find JSON output in status generator")

        json_content = '\n'.join(output_lines[json_start:])
        return json.loads(json_content)

    def generate_html_dashboard(self):
        """Generate the HTML dashboard."""

        refresh_script = ""
        if self.auto_refresh:
            refresh_script = """
                // Auto-refresh every 30 seconds in development
                setInterval(loadStatus, 30000);
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Agentical Status JSON (Local Development)</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: #000000;
            color: #00ff00;
            font-family: 'Courier New', Monaco, monospace;
            font-size: 14px;
            line-height: 1.4;
        }}
        .container {{
            max-width: none;
            margin: 0;
            padding: 0;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #333;
        }}
        .header h1 {{
            color: #00ff00;
            font-size: 2.5em;
            margin: 0;
            font-weight: normal;
        }}
        .header p {{
            color: #00ff00;
            font-size: 1.1em;
            margin: 10px 0 20px 0;
            opacity: 0.8;
        }}
        .dev-notice {{
            background: rgba(57, 255, 20, 0.1);
            border: 1px solid #00ff00;
            padding: 10px;
            margin: 15px 0;
            text-align: center;
            font-size: 0.9em;
        }}
        .dev-notice strong {{
            color: #00ff00;
        }}
        .refresh-btn {{
            background: #00ff00;
            color: #000000;
            border: 2px solid #00ff00;
            padding: 8px 16px;
            font-family: 'Courier New', Monaco, monospace;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            margin: 10px;
            text-transform: uppercase;
        }}
        .refresh-btn:hover {{
            background: #000000;
            color: #00ff00;
        }}
        .json-container {{
            background-color: #000000;
            border: 1px solid #333;
            padding: 20px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .json-content {{
            color: #00ff00;
            font-family: 'Courier New', Monaco, monospace;
            font-size: 13px;
            line-height: 1.3;
        }}
        .loading {{
            text-align: center;
            color: #00ff00;
            font-style: italic;
            padding: 50px;
        }}
        .error {{
            color: #ff0000;
            text-align: center;
            padding: 20px;
        }}
        .refresh-indicator {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #00ff00;
            color: #000000;
            padding: 5px 10px;
            font-size: 0.8em;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        .refresh-indicator.show {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <div class="refresh-indicator" id="refreshIndicator">🔄 Refreshing...</div>

    <div class="container">
        <div class="header">
            <h1>🤖 Agentical Status JSON</h1>
            <p>Raw JSON data for AI Agent Framework & Orchestration Platform</p>
            <div class="dev-notice">
                <strong>🚧 Local Development Mode</strong><br>
                Live data from your local codebase - auto-refreshes every 30 seconds
            </div>
            <button class="refresh-btn" onclick="loadStatus()">🔄 REFRESH JSON</button>
        </div>

        <div class="json-container">
            <div id="json-content" class="json-content loading">
                Loading status data...
            </div>
        </div>
    </div>

    <script>
        let lastUpdateTime = null;

        async function loadStatus() {{
            const indicator = document.getElementById('refreshIndicator');
            const container = document.getElementById('json-content');

            indicator.classList.add('show');
            container.innerHTML = 'Loading status data...';
            container.className = 'json-content loading';

            try {{
                const response = await fetch('status.json?' + Date.now()); // Cache bust
                const data = await response.json();

                // Format JSON with proper indentation
                const formattedJson = JSON.stringify(data, null, 2);

                container.innerHTML = formattedJson;
                container.className = 'json-content';
                lastUpdateTime = new Date();
            }} catch (error) {{
                container.innerHTML = 'Error loading status data: ' + error.message;
                container.className = 'json-content error';
            }} finally {{
                setTimeout(() => {{
                    indicator.classList.remove('show');
                }}, 1000);
            }}
        }}

        // Load status on page load
        loadStatus();

        {refresh_script}
    </script>
</body>
</html>"""

class CustomHTTPServer(socketserver.TCPServer):
    """Custom HTTP server that allows reuse of address."""
    allow_reuse_address = True

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Serve Agentical status dashboard locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/serve-status-local.py
  python scripts/serve-status-local.py --port 8080
  python scripts/serve-status-local.py --no-auto-refresh
        """
    )

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='Port to serve on (default: 8000)'
    )

    parser.add_argument(
        '--no-auto-refresh',
        action='store_true',
        help='Disable automatic refresh'
    )

    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Don\'t automatically open browser'
    )

    args = parser.parse_args()

    # Set up the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Create a handler with auto-refresh setting
    def handler_factory(*args, **kwargs):
        return AgenticalStatusHandler(*args, auto_refresh=not args.no_auto_refresh, **kwargs)

    # Create and start the server
    try:
        with CustomHTTPServer(("", args.port), handler_factory) as httpd:
            url = f"http://localhost:{args.port}"

            print("🚀 Agentical Status Dashboard - Local Development Server")
            print("=" * 55)
            print(f"📍 Server running at: {url}")
            print(f"📊 Status data: {url}/status.json")
            print(f"🔄 Auto-refresh: {'Enabled (30s)' if not args.no_auto_refresh else 'Disabled'}")
            print(f"📁 Serving from: {project_root}")
            print("=" * 55)
            print("Press Ctrl+C to stop the server")

            if not args.no_browser:
                # Open browser after a short delay
                def open_browser():
                    time.sleep(1)
                    webbrowser.open(url)

                threading.Thread(target=open_browser, daemon=True).start()

            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {args.port} is already in use")
            print(f"💡 Try a different port: python scripts/serve-status-local.py --port {args.port + 1}")
        else:
            print(f"❌ Server error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
