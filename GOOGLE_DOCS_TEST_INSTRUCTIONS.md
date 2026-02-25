# Google Docs API Testing Instructions

## Current Status

✓ Dependencies installed
✓ Credentials file found: `client_secret_2_939664024804-3bqjcb161r3khle7bk30rsgm1pl3jgtb.apps.googleusercontent.com.json`
✗ Not yet authenticated (no token.json)

## How to Test the Connection

### Option 1: Interactive Authentication (Recommended)

Run the test script interactively:

```bash
module load python/3.11
python test_google_docs.py
```

When prompted:
1. Copy the URL that appears
2. Open it in your web browser (on any machine where you're logged into Google)
3. Authorize the application
4. Copy the full redirect URL from your browser
5. Paste it back into the terminal

The script will then:
- List your recent Google Docs
- Fetch the content of the first document
- Allow you to search for keywords

### Option 2: Test with a Specific Document ID

If you already have a Google Doc ID you want to test, create a simple test:

```python
from test_google_docs import get_credentials, test_get_document, test_search_in_document

# Authenticate once
creds = get_credentials()

# Test specific document
doc_id = "YOUR_DOCUMENT_ID_HERE"
test_get_document(creds, doc_id)

# Search in document
test_search_in_document(creds, doc_id, "keyword1,keyword2")
```

### Option 3: Check if Credentials are Valid

Simple validation test:

```bash
module load python/3.11
python -c "
from pathlib import Path
import json

creds_file = 'client_secret_2_939664024804-3bqjcb161r3khle7bk30rsgm1pl3jgtb.apps.googleusercontent.com.json'
with open(creds_file) as f:
    data = json.load(f)
    print('✓ Credentials file is valid JSON')
    print(f'Client ID: {data.get(\"installed\", {}).get(\"client_id\", \"N/A\")}')
    print(f'Project ID: {data.get(\"installed\", {}).get(\"project_id\", \"N/A\")}')
"
```

## Finding a Google Doc ID

Google Doc URLs look like:
```
https://docs.google.com/document/d/1ABC123xyz789/edit
```

The document ID is the part between `/d/` and `/edit`:
```
1ABC123xyz789
```

## What Gets Tested

The test script validates:

1. ✓ **Authentication** - Can connect to Google APIs
2. ✓ **List Documents** - Can query Google Drive for documents
3. ✓ **Fetch Content** - Can retrieve full document content
4. ✓ **Search** - Can search for keywords in documents

## Troubleshooting

### "Could not locate runnable browser"
This is expected on NERSC. The script will fall back to manual URL authentication.

### "Invalid grant"
Your credentials may have expired. Delete `token.json` and re-authenticate.

### "Access not configured"
Make sure the Google Docs API and Google Drive API are enabled in your Google Cloud Console.

## After Successful Authentication

Once you have `token.json`, you can:

1. Use the test functions directly in Python:
   ```python
   from test_google_docs import *
   creds = get_credentials()  # Uses saved token
   docs = test_list_documents(creds)
   ```

2. Integrate with the main DOE_METRICS_REPORTER client

3. Query documents programmatically without re-authenticating

## Next Steps

1. Run `python test_google_docs.py` interactively
2. Complete the OAuth flow
3. Test with your actual Google Docs
4. Once working, integrate with the main application
