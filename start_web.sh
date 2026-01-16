#!/bin/bash
# Startup script for the web interface

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================="
echo "  Relay/LED Controller Web UI"
echo "=================================="
echo ""

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found"
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Warning: Flask is not installed"
    echo "Installing dependencies..."
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
fi

# Get local IP address for convenience
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "Starting web server..."
echo ""
echo "Access the web interface at:"
echo "  Local:   http://localhost:5000"
echo "  Network: http://${LOCAL_IP}:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the web server
cd "$SCRIPT_DIR/controller"
python3 web_server.py "$@"
