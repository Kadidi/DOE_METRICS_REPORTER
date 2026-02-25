# API Configuration Guide

Step-by-step instructions for obtaining and configuring API credentials for DOE_METRICS_REPORTER.

## Google Docs API

### Prerequisites
- Google Cloud Account
- Google Drive with shared documents

### Setup Steps

#### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create a new project"
3. Enter project name: `doe-metrics-reporter`
4. Click "Create"

#### 2. Enable Required APIs

1. In the Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable:
   - **Google Docs API**
   - **Google Drive API**
   - **Google Sheets API** (optional, for advanced features)

#### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Desktop application" as the application type
4. Click "Create"
5. Download the JSON file → save as `credentials.json`
6. Copy the contents or note:
   - Client ID
   - Client Secret

#### 4. Update .env File

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_CREDENTIALS_JSON=./credentials.json
```

#### 5. Grant Permissions (First Run)

On first use, you'll be prompted to authorize the app to access your Google account.

### Troubleshooting Google Docs

**"Invalid OAuth credentials"**
- Re-download credentials.json from Cloud Console
- Ensure Client ID and Secret are correct
- Check that Google Docs API is enabled

**"Access denied to document"**
- Ensure the document is shared with your Google account
- Check folder permissions
- Verify document ID is correct

**"Rate limited"**
- Google Docs API has quotas
- Space API calls with cache hits (default 6h TTL)
- Check quota usage in Cloud Console

---

## Slack API

### Prerequisites
- Slack workspace (admin access recommended)
- Slack app (or ability to create one)

### Setup Steps

#### 1. Create Slack App

1. Go to [api.slack.com](https://api.slack.com/)
2. Click "Create an App"
3. Choose "From scratch"
4. Name: `DOE-Metrics-Reporter`
5. Choose your workspace
6. Click "Create App"

#### 2. Configure Permissions

1. On the left sidebar, go to "OAuth & Permissions"
2. Under "Scopes," add these **Bot Token Scopes**:
   - `channels:read` - List channels
   - `channels:history` - Read channel messages
   - `users:read` - List users
   - `team:read` - Read workspace info
   - `chat:write` - Send messages (optional, for future features)

#### 3. Install App to Workspace

1. Scroll up to "OAuth Tokens for Your Workspace"
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

#### 4. Get Signing Secret

1. Go to "Basic Information"
2. Under "App Credentials," copy the **Signing Secret**

#### 5. Update .env File

```bash
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

#### 6. Add Bot to Channels (Optional)

To query specific channels, add the bot:

```bash
DOE_METRICS> /invite @doe-metrics-reporter
```

Or invite manually:
1. Open channel in Slack
2. Go to "Details" → "Members"
3. Click "Add members"
4. Search for and select your bot

### Troubleshooting Slack

**"Invalid token"**
- Check the token starts with `xoxb-`
- Regenerate token from "OAuth & Permissions"
- Ensure bot is still installed to workspace

**"Bot not responding"**
- Check bot is added to the channel
- Verify bot token permissions in OAuth scopes
- Check Slack workspace hasn't revoked the app

**"Rate limited"**
- Slack has API rate limits (120 requests/minute)
- Use cache strategically (default 2h TTL for Slack)
- Batch queries to avoid excessive requests

---

## Elasticsearch (Phase 2)

### Prerequisites
- Elasticsearch cluster (7.0+)
- Network access to cluster
- Authentication credentials

### Configuration

When you're ready for Phase 2, configure:

```bash
ELASTICSEARCH_HOST=your-cluster-hostname
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your-password
ELASTICSEARCH_VERIFY_CERTS=true
```

### Index Requirements

DOE_METRICS_REPORTER expects these Elasticsearch indices:
- `metrics-*` - System metrics (CPU, GPU, memory, network)
- `logs-*` - System logs

Contact your Elasticsearch administrator for access to these indices.

---

## SLURM Configuration (Phase 2)

### Prerequisites
- Access to SLURM-based HPC system
- Local sacct command available

### Configuration

When you're ready for Phase 2:

```bash
SLURM_SACCT_COMMAND=/usr/bin/sacct
SLURM_CLUSTER=perlmutter
```

The SLURM server uses local `sacct` command, so no additional setup needed beyond system access.

---

## ServiceNow Configuration (Phase 3)

### Prerequisites
- ServiceNow instance
- Admin access or API integration role
- Service account credentials

### Configuration

When you're ready for Phase 3:

```bash
SERVICENOW_INSTANCE=your-instance.service-now.com
SERVICENOW_USERNAME=integration_user
SERVICENOW_PASSWORD=your-password
```

---

## Testing Credentials

After configuration, test your credentials:

```bash
# Start the reporter
./start_reporter.sh

# Test commands
DOE_METRICS> servers list
DOE_METRICS> query test
DOE_METRICS> cache status
```

If servers load successfully, credentials are working.

### Detailed Testing

**Test Google Docs:**
```bash
DOE_METRICS> search google_docs documents "your search term"
```

**Test Slack:**
```bash
DOE_METRICS> search slack #incidents "keyword"
```

---

## Security Best Practices

1. **Never commit .env to git**
   - It's in `.gitignore`
   - Double-check with `git status`

2. **Rotate credentials regularly**
   - Google: Regenerate OAuth credentials monthly
   - Slack: Rotate bot token when team access changes

3. **Use minimal permissions**
   - Only enable required API scopes
   - Don't give admin access unless necessary
   - Use service accounts when possible

4. **Monitor API usage**
   - Google Cloud Console: APIs & Services → Credentials
   - Slack: App Dashboard → "Activity"
   - Check for suspicious or unexpected usage

5. **Handle credentials securely**
   - Don't share .env files
   - Use secrets management for production
   - Audit access to credential files

---

## Credential Storage for Production

For production deployments:

1. **Use environment variables** instead of .env files
2. **Use secrets management** (HashiCorp Vault, AWS Secrets Manager)
3. **Implement access control** - only authorized systems can read credentials
4. **Enable audit logging** - track who accesses what
5. **Rotate regularly** - implement credential rotation policies

Example with environment variables:
```bash
export GOOGLE_CLIENT_ID="..."
export SLACK_BOT_TOKEN="..."
./start_reporter.sh
```

---

## Troubleshooting Common Issues

### All APIs report "permission denied"

1. Check .env file exists: `ls -la .env`
2. Check file is readable: `cat .env | head -5`
3. Ensure credentials aren't expired
4. Re-run setup: `./setup_user.sh`

### "Certificate verification failed" (SSL errors)

This usually means the system can't verify API certificates.

**Solution:**
1. Check your internet connection
2. Update SSL certificates:
   ```bash
   pip install --upgrade certifi
   ```
3. Contact your network administrator if behind a proxy

### Rate Limiting Errors

Each API has rate limits. DOE_METRICS_REPORTER uses caching to minimize API calls:

- Google Docs: 6-hour cache
- Slack: 2-hour cache
- Metrics: 1-hour cache
- Jobs: 4-hour cache

To reduce rate limiting:
1. Increase cache TTL in doe_metrics_client.py
2. Batch queries together
3. Space out report generation
4. Request higher limits from API providers

---

## Support

For issues with specific APIs:
- **Google**: [Google Cloud Support](https://cloud.google.com/support)
- **Slack**: [Slack Community](https://slack.com/help)
- **Elasticsearch**: [Elastic Support](https://www.elastic.co/support)

For DOE_METRICS_REPORTER setup issues, contact NERSC support.

---

**Last Updated:** 2025-01-26
