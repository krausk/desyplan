#!/bin/bash
# Wrapper script for firmware deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "desyplan Firmware Build Script"
echo "==============================="
echo ""

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found"
    exit 1
fi

# Run the Python deployment script
python3 "$SCRIPT_DIR/deploy_firmware.py" "$@"
