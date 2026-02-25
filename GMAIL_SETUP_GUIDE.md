# Gmail Integration Setup Guide

## 🎯 What This Enables

Query your Gmail emails using natural language and filters, integrated with Google Docs and Slack searches!

## 📋 Prerequisites

You need to re-authenticate to add Gmail permissions to your existing Google token.

## 🚀 Setup Steps

### Step 1: Re-Authenticate with Gmail Scope

The current `token.json` only has Google Docs permissions. We need to add Gmail.

```bash
module load python/3.11

# Remove old token (it will be recreated with Gmail access)
rm token.json

# Re-authenticate with Gmail scope
python test_google_docs.py
```

**What happens:**
1. Opens authentication URL
2. Sign in to Google
3. **Important:** You'll see a new permission request for Gmail (read-only)
4. Authorize it
5. Copy redirect URL and paste back
6. New `token.json` created with Gmail access

### Step 2: Test Gmail Access

```bash
python query_gmail.py
```

Should show:
```
✓ Gmail authentication successful!
```

And list your recent emails.

### Step 3: Try Some Queries

```bash
# Search by subject
python query_gmail.py "subject:incident"

# Search by sender
python query_gmail.py "from:alerts@nersc.gov"

# Search by date
python query_gmail.py "after:2024/02/01"

# Combined filters
python query_gmail.py "from:system subject:outage"
```

## 📧 Gmail Query Syntax

The system supports full Gmail search syntax:

### By Sender
```bash
from:user@example.com
from:alerts@nersc.gov
```

### By Subject
```bash
subject:incident
subject:"system down"
```

### By Date
```bash
after:2024/01/01
before:2024/02/01
after:2024/01/15 before:2024/01/20
```

### By Status
```bash
is:unread          # Only unread emails
is:read            # Only read emails
has:attachment     # Has attachments
```

### By Label
```bash
label:important
label:urgent
```

### Combined Queries
```bash
from:alerts@nersc.gov subject:perlmutter after:2024/01/01
```

## 🔧 Integration with Multi-Source Q&A

Once Gmail is set up, you can add email filters to `documents_config.yaml`:

```yaml
gmail_filters:
  - name: "System Alerts"
    query: "from:alerts@nersc.gov"
    category: "incidents"
    keywords:
      - alert
      - system
      - critical
    description: "System alert emails"

  - name: "Incident Reports"
    query: "subject:incident OR subject:outage"
    category: "incidents"
    keywords:
      - incident
      - outage
      - downtime
    description: "Incident and outage reports"

  - name: "Meeting Announcements"
    query: "subject:meeting OR subject:seminar"
    category: "events"
    keywords:
      - meeting
      - seminar
      - event
    description: "Meeting and event announcements"
```

Then queries will automatically search Gmail too!

```bash
# This will search Google Docs + Slack + Gmail
multi_ask.py "What incidents happened?"
```

## 📊 Example Filters for NERSC

### System Incidents
```yaml
- name: "System Incidents"
  query: "from:alerts@nersc.gov (subject:incident OR subject:outage OR subject:down)"
  keywords:
    - incident
    - outage
    - downtime
```

### Maintenance Notifications
```yaml
- name: "Maintenance Notices"
  query: "from:notices@nersc.gov subject:maintenance"
  keywords:
    - maintenance
    - scheduled
    - planned
```

### Job Failures
```yaml
- name: "Job Notifications"
  query: "subject:job (subject:failed OR subject:completed)"
  keywords:
    - job
    - batch
    - slurm
```

### User Support Tickets
```yaml
- name: "Support Tickets"
  query: "from:support@nersc.gov"
  keywords:
    - support
    - ticket
    - help
```

## 🔒 Security & Privacy

- **Read-only access**: The integration can only read emails, not send or modify
- **OAuth authentication**: Secure Google OAuth flow
- **Scopes requested**:
  - `gmail.readonly` - Read emails only
  - `documents.readonly` - Read Google Docs only
  - `drive.readonly` - List Drive files only

## 🧪 Testing

### Test 1: Authentication
```bash
python query_gmail.py
# Should list recent emails
```

### Test 2: Search by Subject
```bash
python query_gmail.py "subject:incident"
# Should find emails with "incident" in subject
```

### Test 3: Search by Sender
```bash
python query_gmail.py "from:alerts@nersc.gov"
# Should find emails from that sender
```

### Test 4: Date Range
```bash
python query_gmail.py "after:2024/01/01 before:2024/01/31"
# Should find January emails
```

## 📝 Advanced Usage

### Python API

```python
from query_gmail import GmailQuerier

# Initialize
querier = GmailQuerier()

# Search with filters
emails = querier.search_by_filter(
    sender="alerts@nersc.gov",
    subject="incident",
    after_date="2024/01/01",
    max_results=10
)

# Print results
for email in emails:
    print(f"From: {email['from']}")
    print(f"Subject: {email['subject']}")
    print(f"Date: {email['date']}")
    print(f"Snippet: {email['snippet']}")
    print()
```

### Custom Queries

```python
# Complex query
emails = querier.search_emails(
    "from:system@nersc.gov (subject:perlmutter OR subject:cori) after:2024/01/01"
)

# Recent unread
emails = querier.search_emails("is:unread after:2024/02/01")

# With attachments
emails = querier.search_emails("has:attachment subject:report")
```

## 🆘 Troubleshooting

### "Gmail credentials not found"
```bash
# Re-run authentication
python test_google_docs.py
```

### "Insufficient Permission"
```bash
# Delete old token and re-authenticate
rm token.json
python test_google_docs.py
```

### "Gmail API has not been used"
Enable Gmail API:
1. Go to: https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=YOUR_PROJECT
2. Click "Enable"
3. Wait 2-3 minutes
4. Try again

### "No emails found"
- Check your query syntax
- Try broader query: `python query_gmail.py "after:2024/01/01"`
- Verify you have emails matching the filter

## ✅ Next Steps

1. **Re-authenticate** to add Gmail scope
2. **Test** with `python query_gmail.py`
3. **Configure filters** in `documents_config.yaml`
4. **Use multi-source** queries that include Gmail

---

**Ready to set up?** Run:
```bash
bash setup_gmail.sh
```
