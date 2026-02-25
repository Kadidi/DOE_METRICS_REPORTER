#!/bin/bash

# setup_user.sh - Interactive setup wizard for DOE_METRICS_REPORTER
# This script guides users through API credential configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
ENV_TEMPLATE="$SCRIPT_DIR/.env.template"

echo "=========================================="
echo "DOE_METRICS_REPORTER Setup Wizard"
echo "=========================================="
echo ""

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo "⚠️  .env file already exists at: $ENV_FILE"
    read -p "Do you want to reconfigure? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Existing .env preserved."
        exit 0
    fi
fi

# Create .env from template
cp "$ENV_TEMPLATE" "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo "✓ Created .env file (mode 600 - read-only)"
echo ""

# Function to prompt for configuration
prompt_config() {
    local key=$1
    local prompt_text=$2
    local current_value=$3

    echo "Enter $prompt_text"
    if [ ! -z "$current_value" ] && [ "$current_value" != "your_*" ]; then
        echo "Current: $current_value"
    fi
    read -p "> " value

    if [ ! -z "$value" ]; then
        # Escape special characters for sed
        escaped_value=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g')
        sed -i "s|^${key}=.*|${key}=${escaped_value}|" "$ENV_FILE"
    fi
}

# Interactive configuration
echo "Configure API Credentials"
echo "Leave blank to skip (can be configured later)"
echo ""

# Google Docs
echo "--- Google Docs API ---"
read -p "Do you want to configure Google Docs? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    prompt_config "GOOGLE_CLIENT_ID" "Google Client ID (from Google Cloud Console)"
    prompt_config "GOOGLE_CLIENT_SECRET" "Google Client Secret"
    prompt_config "GOOGLE_CREDENTIALS_JSON" "Path to Google credentials.json"
    echo "✓ Google Docs configured"
    echo ""
fi

# Slack
echo "--- Slack API ---"
read -p "Do you want to configure Slack? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    prompt_config "SLACK_BOT_TOKEN" "Slack Bot Token (starts with xoxb-)"
    prompt_config "SLACK_SIGNING_SECRET" "Slack Signing Secret"
    prompt_config "SLACK_APP_TOKEN" "Slack App-Level Token for Socket Mode (starts with xapp-)"
    echo "✓ Slack configured"
    echo ""
fi

# Cache settings
echo "--- Cache Configuration ---"
read -p "Cache directory [./cache]: " cache_dir
cache_dir="${cache_dir:-.cache}"
sed -i "s|^CACHE_DIR=.*|CACHE_DIR=${cache_dir}|" "$ENV_FILE"

read -p "Log level [INFO]: " log_level
log_level="${log_level:-INFO}"
sed -i "s|^LOG_LEVEL=.*|LOG_LEVEL=${log_level}|" "$ENV_FILE"

echo ""
echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "Configuration saved to: $ENV_FILE"
echo ""
echo "Next steps:"
echo "1. Review/edit .env file if needed: nano $ENV_FILE"
echo "2. Install Python dependencies: pip install -e ."
echo "3. Start the reporter: ./start_reporter.sh"
echo ""
