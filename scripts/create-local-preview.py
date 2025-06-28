#!/usr/bin/env python3
"""
Create Local HTML Preview for Agentical Status Dashboard

This script generates a static HTML file that you can open directly in your browser
to preview the status dashboard locally without running a server.

Usage:
    python scripts/create-local-preview.py
    python scripts/create-local-preview.py --output preview.html
    python scripts/create-local-preview.py --open
"""

import json
import sys
import argparse
import subprocess
import webbrowser
from pathlib import Path

def generate_status_data(project_root):
    """Generate fresh status data."""
    generator_script = project_root / "generate_agentical_status.py"

    if not generator_script.exists():
        raise FileNotFoundError("Status generator script not found")

    # Run the status generator
    result = subprocess.run([
        sys.executable, str(generator_script), "--print"
    ], capture_output=True, text=True, cwd=project_root)

    if result.returncode != 0:
        raise RuntimeError(f"Status generation failed: {result.stderr}")

    # Parse JSON from output
    output_lines = result.stdout.strip().split('\n')
    json_start = -1

    for i, line in enumerate(output_lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    if json_start == -1:
        raise RuntimeError("Could not find JSON in status generator output")

    json_content = '\n'.join(output_lines[json_start:])
    return json.loads(json_content)

def create_html_preview(status_data):
    """Create HTML preview with embedded status data."""

    # Embed the JSON data directly in the HTML
    json_data = json.dumps(status_data, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Agentical Status JSON (Static Preview)</title>
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
        .preview-notice {{
            background: rgba(255, 255, 0, 0.1);
            border: 1px solid #00ff00;
            padding: 10px;
            margin: 15px 0;
            text-align: center;
            font-size: 0.9em;
        }}
        .preview-notice strong {{
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Agentical Status JSON</h1>
            <p>Raw JSON data for AI Agent Framework & Orchestration Platform</p>
            <div class="preview-notice">
                <strong>📋 Static Preview Mode</strong><br>
                Generated from your local codebase - regenerate file to update
            </div>
            <button class="refresh-btn" onclick="refreshData()">🔄 REFRESH JSON</button>
        </div>

        <div class="json-container">
            <div id="json-content" class="json-content">
                <!-- JSON content will be populated by JavaScript -->
            </div>
        </div>
    </div>

    <script>
        // Embedded status data
        const statusData = {json_data};

        function refreshData() {{
            // For static preview, just re-render the same data
            renderStatus(statusData);
        }}

        function renderStatus(data) {{
            const container = document.getElementById('json-content');
            // Format JSON with proper indentation
            const formattedJson = JSON.stringify(data, null, 2);
            container.innerHTML = formattedJson;
        }}

        // Initialize the page
        renderStatus(statusData);
    </script>
</body>
</html>"""

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Create static HTML preview of Agentical status dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/create-local-preview.py
  python scripts/create-local-preview.py --output preview.html
  python scripts/create-local-preview.py --open
        """
    )

    parser.add_argument(
        '--output', '-o',
        default='agentical-status-preview.html',
        help='Output HTML file name (default: agentical-status-preview.html)'
    )

    parser.add_argument(
        '--open',
        action='store_true',
        help='Automatically open the HTML file in browser'
    )

    args = parser.parse_args()

    try:
        project_root = Path(__file__).parent.parent

        print("🔍 Generating Agentical status data...")
        status_data = generate_status_data(project_root)

        print("🎨 Creating HTML preview...")
        html_content = create_html_preview(status_data)

        output_file = project_root / args.output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML preview created: {output_file}")
        print(f"📊 Data includes:")
        print(f"   • {status_data.get('agents', {}).get('total_agents', 0)} production agents")
        print(f"   • {status_data.get('tools', {}).get('mcp_servers', {}).get('total_available', 0)} MCP servers")
        print(f"   • {status_data.get('playbooks', {}).get('total_playbooks', 0)} available playbooks")

        if args.open:
            print("🌐 Opening in browser...")
            webbrowser.open(f"file://{output_file.absolute()}")
        else:
            print(f"💡 Open in browser: file://{output_file.absolute()}")

        return 0

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error creating preview: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
