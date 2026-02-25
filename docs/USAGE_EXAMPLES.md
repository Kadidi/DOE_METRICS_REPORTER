# Usage Examples

Practical examples of queries and reports using DOE_METRICS_REPORTER.

## Starting the Reporter

```bash
cd DOE_METRICS_REPORTER
./start_reporter.sh
```

You should see:
```
DOE_METRICS_REPORTER - Interactive Mode
Type 'help' for commands

DOE_METRICS>
```

## Help Command

Get available commands:

```bash
DOE_METRICS> help
```

## Cache Commands

### View Cache Status

Check what's currently cached:

```bash
DOE_METRICS> cache status
{
  "status": {
    "google_docs": 2,
    "slack": 5
  },
  "entries": [
    {
      "id": "slack:abc12345",
      "source": "slack",
      "cached_at": "2025-01-26T14:30:00",
      "ttl_hours": 2,
      "expires_in_hours": 1.5
    }
  ]
}
```

### List Cache Entries

View all cached items:

```bash
DOE_METRICS> cache list
  google_docs_search_perlmutter: google_docs (expires in 5h45m)
  slack_query_incidents_jan20: slack (expires in 1h30m)
  slack_query_outage: slack (expires in 2h)
```

### Clear Cache

Clear entire cache:

```bash
DOE_METRICS> cache clear
Cache cleared
```

Clear cache for specific source:

```bash
DOE_METRICS> cache clear slack
Slack cache cleared
```

Export cache for backup:

```bash
DOE_METRICS> cache export json
[
  {
    "id": "slack:q12345",
    "source": "slack",
    "cached_at": "2025-01-26T14:30:00",
    "ttl_hours": 2,
    "expires_in_hours": 1.5
  }
]
```

## Server Commands

### List Active Servers

See which MCP servers are loaded:

```bash
DOE_METRICS> servers list
Loaded servers (2):
  ✓ google_docs
  ✓ slack
```

### Reload Servers

After editing `servers.config`, reload:

```bash
DOE_METRICS> servers reload
Reloading server registry...
✓ Connected to google_docs
✓ Connected to slack
Ready with 2 servers
```

## Query Commands

### Query Slack Channels

Search for incident messages:

```bash
DOE_METRICS> search slack #incidents perlmutter outage
```

**Response:**
```json
{
  "channel": "incidents",
  "keywords": ["perlmutter", "outage"],
  "messages": [
    {
      "ts": "1737898200.000100",
      "user": "incident-bot",
      "text": "🚨 INCIDENT: Perlmutter nodes down",
      "timestamp": "2025-01-26T14:30:00Z",
      "reply_count": 12
    }
  ],
  "total": 1,
  "cache_hit": false
}
```

### Query Google Docs

Search for maintenance notes:

```bash
DOE_METRICS> search google_docs maintenance notes
```

### Natural Language Queries

Execute open-ended queries:

```bash
DOE_METRICS> query perlmutter gpu issues from jan 20 to 25
```

## Report Generation

### Generate Incidents Report

Create a multi-source incident report:

```bash
DOE_METRICS> report incidents --from 2025-01-01 --to 2025-01-26
```

**Output:**
```markdown
# NERSC Incidents Report

**Period:** 2025-01-01 to 2025-01-26

## Executive Summary
Summary of significant incidents discovered in this period.

## Incidents Discovered
- Perlmutter GPU failures (Jan 20)
- Archive node maintenance (Jan 22-23)

## Slack Discussion Snippets
Relevant discussion from #incidents and related channels.

## Timeline
1. Jan 20, 14:30 UTC: Perlmutter GPU issues reported
2. Jan 20, 15:00 UTC: Investigation underway
3. Jan 20, 18:00 UTC: Root cause identified (firmware)
4. Jan 21, 10:00 UTC: Fix deployed and verified

## Recommendations
1. Implement automated GPU health checks
2. Update firmware validation procedures
3. Improve incident notification speed

*Report generated: 2025-01-26T14:45:00Z*
```

### Generate Metrics Report

System utilization summary:

```bash
DOE_METRICS> report metrics --from 2025-01-20 --to 2025-01-26
```

### Generate Jobs Report

Job analysis and statistics:

```bash
DOE_METRICS> report jobs --from 2025-01-01
```

### Generate General Report

Overall system health summary:

```bash
DOE_METRICS> report general
```

## Batch Query Scenarios

### Scenario 1: Incident Investigation

Find all information about a recent incident:

```bash
# Step 1: Check cache status
DOE_METRICS> cache status

# Step 2: Search for incident mentions
DOE_METRICS> search slack #incidents perlmutter gpu

# Step 3: Get thread details
DOE_METRICS> search slack #incidents "Jan 20" "gpu failure"

# Step 4: Check documentation
DOE_METRICS> search google_docs "perlmutter" "gpu"

# Step 5: Generate report
DOE_METRICS> report incidents --from 2025-01-20 --to 2025-01-21

# Step 6: Export for stakeholders
DOE_METRICS> export report.md
```

### Scenario 2: Monthly Status Report

Compile monthly system status:

```bash
# Clear old cache to ensure fresh data
DOE_METRICS> cache clear

# Gather metrics from all sources
DOE_METRICS> report incidents --from 2025-01-01 --to 2025-01-31
DOE_METRICS> report metrics --from 2025-01-01 --to 2025-01-31
DOE_METRICS> report jobs --from 2025-01-01 --to 2025-01-31

# Export compiled report
DOE_METRICS> cache export json > january_metrics.json
```

### Scenario 3: Troubleshooting Job Failures

Investigate job failure patterns:

```bash
# Search for error messages
DOE_METRICS> search slack #ops-alerts "timeout" "error"

# Search documentation for known issues
DOE_METRICS> search google_docs "job timeout" "troubleshooting"

# Generate report focused on jobs
DOE_METRICS> report jobs --from 2025-01-20 --to 2025-01-26

# Check system metrics for correlation
DOE_METRICS> report metrics --from 2025-01-20 --to 2025-01-26
```

### Scenario 4: Finding Discussion Context

When you see an error, find related discussions:

```bash
# First, search slack for the error
DOE_METRICS> search slack #incidents "GPU memory error"

# Get thread details for full context
DOE_METRICS> search slack #incidents-followup "GPU memory"

# Check Google Docs for troubleshooting guides
DOE_METRICS> search google_docs "GPU troubleshooting"

# Generate comprehensive report
DOE_METRICS> report general
```

## Advanced Usage

### Export Reports to File

Save reports to markdown file for sharing:

```bash
DOE_METRICS> report incidents --from 2025-01-01 --to 2025-01-26 > report.md
```

### Filter by Date Range

All report commands support date filters:

```bash
# Last 7 days
DOE_METRICS> report incidents --from 2025-01-19 --to 2025-01-26

# Specific month
DOE_METRICS> report metrics --from 2025-01-01 --to 2025-01-31

# Just today
DOE_METRICS> report jobs --from 2025-01-26
```

### Multi-Keyword Searches

Search for multiple terms at once:

```bash
DOE_METRICS> search slack #incidents perlmutter,gpu,timeout,error
```

This finds messages containing any of those keywords.

### Time-Series Analysis

Generate reports for different time periods to spot trends:

```bash
# Week 1
DOE_METRICS> report metrics --from 2025-01-01 --to 2025-01-07

# Week 2
DOE_METRICS> report metrics --from 2025-01-08 --to 2025-01-14

# Week 3
DOE_METRICS> report metrics --from 2025-01-15 --to 2025-01-21

# Week 4
DOE_METRICS> report metrics --from 2025-01-22 --to 2025-01-28
```

Compare reports to identify patterns.

## Cache Optimization

### Strategy 1: Frequent Queries

For queries you run frequently, let cache work:

```bash
# First run (fresh from API)
DOE_METRICS> search slack #incidents perlmutter

# Second run (from cache, instant)
DOE_METRICS> search slack #incidents perlmutter

# Cache valid for 2 hours, then refreshes
```

### Strategy 2: Daily Reports

Generate daily reports efficiently:

```bash
# Morning: Fresh data
DOE_METRICS> report incidents --from 2025-01-26

# Afternoon: Cached + fresh updates
DOE_METRICS> report metrics --from 2025-01-26

# End of day: Archive to file
DOE_METRICS> cache export json > 2025-01-26.json
DOE_METRICS> cache clear
```

### Strategy 3: Weekly Rollups

Combine multiple days efficiently:

```bash
# Queries hit cache for recent data, fresh for older data
DOE_METRICS> report incidents --from 2025-01-19 --to 2025-01-26

# Cache keeps searches under 2 hours, older data fetched fresh
```

## Exiting the CLI

```bash
DOE_METRICS> exit
Goodbye!

# Or use Ctrl+C
```

## Tips & Tricks

### 1. Use Tab Completion

Most shells support tab completion for commands:

```bash
DOE_METRICS> cach[TAB]    # Completes to "cache"
DOE_METRICS> repor[TAB]   # Completes to "report"
```

### 2. History Navigation

Access previous commands with up/down arrow:

```bash
DOE_METRICS> [UP]    # Previous command
DOE_METRICS> [DOWN]  # Next command
```

### 3. Screen Clear

Clear the terminal for readability:

```bash
DOE_METRICS> clear
```

### 4. Chain Commands

Execute multiple queries in sequence:

```bash
DOE_METRICS> cache status
(review results)
DOE_METRICS> cache clear slack
(clear slack cache)
DOE_METRICS> search slack #incidents perlmutter
(search with fresh data)
```

### 5. Batch Processing

For scripts, pipe commands to the CLI:

```bash
cat << 'EOF' | python3 doe_metrics_client.py
cache status
search slack #incidents perlmutter
report incidents --from 2025-01-20
exit
EOF
```

## Troubleshooting Common Issues

### "Unknown command"

```
DOE_METRICS> qeury slack ...
Unknown command: qeury
```

**Solution**: Check spelling. Common misspellings:
- `qeury` → `query`
- `sarch` → `search`
- `chache` → `cache`

### "Server not found"

```
ERROR: Unknown tool: slack_query
```

**Solution**: Verify server is loaded
```bash
DOE_METRICS> servers list
```

If not listed, check `servers.config` and restart.

### "Rate limit exceeded"

```
ERROR: Slack API rate limited
```

**Solution**: Wait for cache to handle subsequent queries, or manually clear and wait:
```bash
DOE_METRICS> cache clear slack
(wait 5-10 minutes)
DOE_METRICS> search slack #incidents perlmutter
```

### Empty results

```
DOE_METRICS> search slack #incidents "ghost incident"
(returns no results)
```

**Solution**: Try broader search terms
```bash
DOE_METRICS> search slack #incidents "incident"
```

---

## Next Steps

- Try the examples above to get familiar with the CLI
- Review [ADDING_SERVERS.md](ADDING_SERVERS.md) to add new data sources
- Check [API_CONFIGURATION.md](API_CONFIGURATION.md) for credential setup
- Read [SETUP.md](SETUP.md) for troubleshooting

---

**Last Updated:** 2025-01-26
