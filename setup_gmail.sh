#!/bin/bash
# Setup Gmail integration

echo "================================================"
echo "Gmail Integration Setup"
echo "================================================"
echo ""
echo "Adding Gmail access to your Google authentication..."
echo ""
echo "This will update your token.json to include Gmail permissions."
echo ""
echo "Steps:"
echo "  1. Running authentication..."
echo "  2. A URL will appear - open it in your browser"
echo "  3. Sign in and authorize Gmail access"
echo "  4. Copy the redirect URL and paste it back"
echo ""
echo "Press Enter to continue..."
read

# Load Python
module load python/3.11

# Run authentication
python test_google_docs.py

if [ -f token.json ]; then
    echo ""
    echo "================================================"
    echo "✓ Gmail Setup Complete!"
    echo "================================================"
    echo ""
    echo "Test it:"
    echo "  python query_gmail.py"
    echo ""
    echo "Or search emails:"
    echo "  python query_gmail.py 'subject:incident'"
    echo ""
else
    echo ""
    echo "================================================"
    echo "Setup Incomplete"
    echo "================================================"
    echo ""
    echo "token.json was not created."
    echo "Please try running: python test_google_docs.py"
    echo ""
fi
