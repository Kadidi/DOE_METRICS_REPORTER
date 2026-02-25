#!/bin/bash

# start_reporter.sh - Start the DOE_METRICS_REPORTER client
# Dynamically loads MCP servers from servers.config

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVERS_CONFIG="$SCRIPT_DIR/servers.config"
ENV_FILE="$SCRIPT_DIR/.env"

echo "=========================================="
echo "DOE_METRICS_REPORTER"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found"
    echo "Please run setup first: ./setup_user.sh"
    exit 1
fi

# Check if servers.config exists
if [ ! -f "$SERVERS_CONFIG" ]; then
    echo "❌ Error: servers.config not found"
    echo "Please ensure servers.config exists: $SERVERS_CONFIG"
    exit 1
fi

# Load environment
export $(cat "$ENV_FILE" | grep -v '^#' | xargs)

# Create cache directory if it doesn't exist
mkdir -p "$CACHE_DIR"

echo "Configuration loaded from: $ENV_FILE"
echo "Server registry: $SERVERS_CONFIG"
echo "Cache directory: $CACHE_DIR"
echo ""
echo "Starting MCP servers from registry..."
echo ""

# Parse servers.config and start servers
while IFS='=' read -r name path; do
    # Skip comments and empty lines
    [[ "$name" =~ ^#.*$ ]] && continue
    [ -z "$name" ] && continue

    # Trim whitespace
    name=$(echo "$name" | xargs)
    path=$(echo "$path" | xargs)

    # Check if server file exists
    full_path="$SCRIPT_DIR/$path"
    if [ -f "$full_path" ]; then
        echo "✓ Found server: $name ($path)"
    else
        echo "⚠️  Server not found: $name ($path)"
    fi
done < "$SERVERS_CONFIG"

echo ""
echo "Starting DOE_METRICS_REPORTER CLI..."
echo "Type 'help' for commands, 'exit' to quit"
echo ""

# Start the Python client with servers.config available
cd "$SCRIPT_DIR"
python3 -u doe_metrics_client.py
