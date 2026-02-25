#!/bin/bash
# Quick wrapper for asking questions about the NERSC downtimes document

DOC_ID="1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8"

# Load Python module
module load python/3.11 2>/dev/null

if [ $# -eq 0 ]; then
    echo "Usage: ./quick_ask.sh \"Your question here\""
    echo ""
    echo "Examples:"
    echo "  ./quick_ask.sh \"What were the unplanned outages?\""
    echo "  ./quick_ask.sh \"How many maintenance windows in December?\""
    echo "  ./quick_ask.sh \"What happened with login nodes?\""
    echo ""
    echo "Or run interactively:"
    echo "  ./quick_ask.sh interactive"
    exit 1
fi

if [ "$1" = "interactive" ]; then
    python ask_document.py "$DOC_ID"
else
    python ask_document.py "$DOC_ID" "$*"
fi
