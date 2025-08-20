#!/bin/bash

# Simple server launch script for Papervisor
# Usage: (optional) activate your Python 3.12+ environment, then run:
#   ./launch_server_simple.sh

set -e

# Move to the directory where this script is located
cd "$(dirname "$0")"

# Check Python version (require 3.12+)
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ $(echo "$PYTHON_VERSION < 3.12" | bc) -eq 1 ]]; then
    echo "❌ Python 3.12 or higher is required. Current: $PYTHON_VERSION"
    exit 1
fi

echo "🚀 Launching Papervisor Web Server..."
echo "🐍 Python: $(python --version)"
echo "🌐 Starting server..."
echo "🔗 Local URL: http://127.0.0.1:5000"
echo "🔗 Network URL: http://0.0.0.0:5000"
echo "⚠️  Press Ctrl+C to stop the server"
echo "=================================================="

python -m papervisor.web_server || {
    echo "❌ Failed to launch Papervisor. Is it installed? Try: pip install .[dev]"
    exit 1
}
