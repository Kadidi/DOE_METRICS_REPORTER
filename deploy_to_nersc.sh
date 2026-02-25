#!/bin/bash
# Deployment script for NERSC Google Docs Q&A tool

set -e  # Exit on error

echo "================================================"
echo "NERSC Google Docs Q&A - Deployment Script"
echo "================================================"
echo ""

# Configuration
DEFAULT_INSTALL_DIR="/global/common/software/nersc/google-docs-qa"
INSTALL_DIR="${1:-$DEFAULT_INSTALL_DIR}"

echo "Installation directory: $INSTALL_DIR"
echo ""

# Check if running with appropriate permissions
if [ ! -w "$(dirname $INSTALL_DIR)" ]; then
    echo "WARNING: You may not have write permission to $INSTALL_DIR"
    echo "You may need to:"
    echo "  1. Contact NERSC support to create the directory"
    echo "  2. Use 'sudo' or run as appropriate user"
    echo "  3. Choose a different installation directory"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create installation directory
echo "Step 1: Creating installation directory..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/docs"
mkdir -p "$INSTALL_DIR/examples"

# Copy main scripts
echo "Step 2: Copying scripts..."
cp test_google_docs.py "$INSTALL_DIR/"
cp ask_document.py "$INSTALL_DIR/"
cp query_doc.py "$INSTALL_DIR/"
cp list_docs.py "$INSTALL_DIR/"
cp query_slack.py "$INSTALL_DIR/"
cp smart_ask.py "$INSTALL_DIR/"
cp multi_ask.py "$INSTALL_DIR/"
cp config.py "$INSTALL_DIR/"

# Copy configuration
echo "Step 3: Copying configuration files..."
cp documents_config.yaml "$INSTALL_DIR/"

# Copy documentation
echo "Step 4: Copying documentation..."
cp NL_QA_GUIDE.md "$INSTALL_DIR/docs/"
cp NATURAL_LANGUAGE_QA_SUMMARY.md "$INSTALL_DIR/docs/"
cp NERSC_DEPLOYMENT_GUIDE.md "$INSTALL_DIR/docs/"

# Configure Slack token (optional)
echo "Step 5: Configuring Slack integration..."
if [ -f .slack_token ]; then
    echo "  Found existing Slack token, copying to installation..."
    cp .slack_token "$INSTALL_DIR/.slack_token"
    chmod 600 "$INSTALL_DIR/.slack_token"
    echo "  ✓ Slack token configured"
else
    echo "  ⚠ No .slack_token file found"
    echo "  To enable Slack integration, create $INSTALL_DIR/.slack_token with your bot token"
    echo "  Example: echo 'xoxb-your-token' > $INSTALL_DIR/.slack_token"
    echo "  Then: chmod 600 $INSTALL_DIR/.slack_token"
fi

# Create README for users
echo "Step 6: Creating user README..."
cat > "$INSTALL_DIR/README.md" <<'EOF'
# Multi-Source Natural Language Q&A

Query Google Docs AND Slack using natural language questions!
The system automatically finds the right sources for your question.

## Quick Start

### 1. First-Time Setup (5 minutes)

Authenticate with Google (one-time):

```bash
module load python/3.11
cd ~  # Create token in your home directory
python /global/common/software/nersc/google-docs-qa/test_google_docs.py
```

Follow the prompts to authorize access to your Google account.

### 2. Install Dependencies

```bash
module load python/3.11
pip install --user google-auth-oauthlib google-api-python-client anthropic
```

### 3. Ask a Question!

**Just ask - no need to specify which documents or Slack channels!**

```bash
module load python/3.11
python /global/common/software/nersc/google-docs-qa/multi_ask.py "Your question"
```

Or use the wrapper:

```bash
/global/common/software/nersc/google-docs-qa/nersc-ask "Your question"
```

## Examples

```bash
# The system automatically searches both Google Docs and Slack:

# Ask about incidents
python /global/common/software/nersc/google-docs-qa/multi_ask.py "What outages happened in December?"

# Ask about events
python /global/common/software/nersc/google-docs-qa/multi_ask.py "What events are happening?"

# Ask about Perlmutter
python /global/common/software/nersc/google-docs-qa/multi_ask.py "What is the status of Perlmutter?"

# Interactive mode
python /global/common/software/nersc/google-docs-qa/multi_ask.py

# List your documents
python /global/common/software/nersc/google-docs-qa/list_docs.py
```

## Documentation

- **User Guide**: docs/NL_QA_GUIDE.md
- **Full Documentation**: docs/NATURAL_LANGUAGE_QA_SUMMARY.md
- **Deployment Info**: docs/NERSC_DEPLOYMENT_GUIDE.md

## Support

- NERSC Support: support@nersc.gov
- Documentation: https://docs.nersc.gov/

## Optional: AI-Powered Answers

For intelligent summaries and analysis:

1. Get API key from: https://console.anthropic.com/
2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY='your-key-here'
   ```
3. Ask complex questions:
   ```bash
   python ask_document.py <DOC_ID> "Summarize all the incidents"
   ```
EOF

# Create wrapper script
echo "Step 7: Creating wrapper script..."
cat > "$INSTALL_DIR/nersc-ask" <<'EOF'
#!/bin/bash
# NERSC Multi-Source Q&A Wrapper Script
# Searches Google Docs AND Slack automatically

INSTALL_DIR="/global/common/software/nersc/google-docs-qa"

# Check if Python module is loaded
if ! command -v python &> /dev/null; then
    module load python/3.11 2>/dev/null || {
        echo "Error: Could not load Python module"
        echo "Run: module load python/3.11"
        exit 1
    }
fi

# Check if user has authenticated with Google
if [ ! -f ~/token.json ] && [ ! -f ./token.json ]; then
    echo "================================================"
    echo "First Time Setup Required"
    echo "================================================"
    echo ""
    echo "You need to authenticate with Google first."
    echo "Run this command once:"
    echo ""
    echo "  python $INSTALL_DIR/test_google_docs.py"
    echo ""
    echo "Then try your query again."
    exit 1
fi

# Run the multi-source tool
python "$INSTALL_DIR/multi_ask.py" "$@"
EOF

chmod +x "$INSTALL_DIR/nersc-ask"

# Create requirements.txt
echo "Step 8: Creating requirements file..."
cat > "$INSTALL_DIR/requirements.txt" <<EOF
google-auth-oauthlib>=1.2.0
google-api-python-client>=2.188.0
anthropic>=0.77.0
slack-sdk>=3.27.0
pyyaml>=6.0
EOF

# Create example usage script
echo "Step 9: Creating example script..."
cat > "$INSTALL_DIR/examples/example_usage.sh" <<'EOF'
#!/bin/bash
# Example usage of Google Docs Q&A

# Load Python
module load python/3.11

# Example document ID (replace with your own)
DOC_ID="1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8"

# Basic query
echo "Example 1: Basic query"
python /global/common/software/nersc/google-docs-qa/ask_document.py \
  "$DOC_ID" "What were the main issues?"

# Interactive mode
echo ""
echo "Example 2: Interactive mode (type 'quit' to exit)"
python /global/common/software/nersc/google-docs-qa/ask_document.py "$DOC_ID"
EOF

chmod +x "$INSTALL_DIR/examples/example_usage.sh"

# Set permissions
echo "Step 10: Setting permissions..."
chmod -R 755 "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR/README.md"
chmod 644 "$INSTALL_DIR/requirements.txt"
chmod 755 "$INSTALL_DIR"/*.py

# Create user setup script
echo "Step 11: Creating user setup script..."
cat > "$INSTALL_DIR/setup_user.sh" <<'EOF'
#!/bin/bash
# User setup script - each user runs this once

echo "================================================"
echo "Google Docs Q&A - User Setup"
echo "================================================"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
module load python/3.11
pip install --user google-auth-oauthlib google-api-python-client anthropic

echo ""
echo "Dependencies installed!"
echo ""

# Authenticate
echo "Now you need to authenticate with Google..."
echo "This will open a browser for you to sign in."
echo ""
read -p "Press Enter to continue..."

python /global/common/software/nersc/google-docs-qa/test_google_docs.py

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Try it out:"
echo "  module load python/3.11"
echo "  python /global/common/software/nersc/google-docs-qa/ask_document.py <DOC_ID> \"Your question\""
echo ""
echo "Or use the wrapper:"
echo "  /global/common/software/nersc/google-docs-qa/nersc-ask-doc <DOC_ID> \"Your question\""
echo ""
EOF

chmod 755 "$INSTALL_DIR/setup_user.sh"

# Summary
echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the installation:"
echo "   $INSTALL_DIR/nersc-ask-doc --help"
echo ""
echo "2. (Optional) Create a module file at:"
echo "   /global/common/software/modulefiles/google-docs-qa/1.0.lua"
echo ""
echo "3. (Optional) Add to shared PATH by creating /etc/profile.d/google-docs-qa.sh:"
echo "   export PATH=\"$INSTALL_DIR:\$PATH\""
echo ""
echo "4. Tell users to run the setup script:"
echo "   $INSTALL_DIR/setup_user.sh"
echo ""
echo "Documentation: $INSTALL_DIR/README.md"
echo ""
