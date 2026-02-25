# DOE_METRICS_REPORTER - Quick Start

Get up and running with DOE_METRICS_REPORTER in 5 minutes.

## Installation (One-Time)

```bash
cd DOE_METRICS_REPORTER
chmod +x setup_user.sh start_reporter.sh
pip install -e .
./setup_user.sh
```

Follow the prompts to enter your API credentials for Google Docs and Slack.

## Start the Reporter

```bash
./start_reporter.sh
```

You should see:
```
DOE_METRICS_REPORTER - Interactive Mode
Type 'help' for commands

DOE_METRICS>
```

## Essential Commands

### Check Cache
```bash
DOE_METRICS> cache status
DOE_METRICS> cache list
```

### Search Slack
```bash
DOE_METRICS> search slack #incidents perlmutter
DOE_METRICS> search slack #incidents gpu,timeout,error
```

### Generate Reports
```bash
DOE_METRICS> report incidents --from 2025-01-01 --to 2025-01-26
DOE_METRICS> report metrics --from 2025-01-20 --to 2025-01-26
DOE_METRICS> report jobs --from 2025-01-15
```

### Manage Cache
```bash
DOE_METRICS> cache clear slack       # Clear Slack cache
DOE_METRICS> cache clear             # Clear all cache
```

### Get Help
```bash
DOE_METRICS> help
DOE_METRICS> servers list
```

## Common Workflows

### Investigate an Incident

```bash
# 1. Search for incident mentions
DOE_METRICS> search slack #incidents perlmutter gpu failure

# 2. Check cache status
DOE_METRICS> cache status

# 3. Generate incident report
DOE_METRICS> report incidents --from 2025-01-20 --to 2025-01-21

# 4. Exit
DOE_METRICS> exit
```

### Generate Monthly Report

```bash
# 1. Clear cache for fresh data
DOE_METRICS> cache clear

# 2. Generate reports for each theme
DOE_METRICS> report incidents --from 2025-01-01 --to 2025-01-31
DOE_METRICS> report metrics --from 2025-01-01 --to 2025-01-31
DOE_METRICS> report jobs --from 2025-01-01 --to 2025-01-31

# 3. Export cache for archiving
DOE_METRICS> cache export json > january.json
```

## Troubleshooting

**"Cannot find .env"**
```bash
./setup_user.sh
```

**"Server not loaded"**
```bash
DOE_METRICS> servers list
# Check servers.config if missing
```

**"API rate limited"**
```bash
# Wait 5-10 minutes or use cache hits
DOE_METRICS> cache clear slack
# Then search again
```

## Documentation

- **Setup Details** → [SETUP.md](docs/SETUP.md)
- **API Credentials** → [API_CONFIGURATION.md](docs/API_CONFIGURATION.md)
- **Usage Examples** → [USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md)
- **Add New Servers** → [ADDING_SERVERS.md](docs/ADDING_SERVERS.md)
- **Full README** → [README.md](README.md)

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API credentials (keep secret!) |
| `servers.config` | Which MCP servers to load |
| `pyproject.toml` | Python dependencies |

## Key Features

- ✅ Query Google Docs and Slack
- ✅ Generate batch reports
- ✅ Smart local caching (6h, 2h, 1h)
- ✅ Type-safe data models
- ✅ Extensible with new servers

## Next Steps

1. Run `./start_reporter.sh`
2. Try `search slack #incidents test`
3. Try `report incidents --from 2025-01-20`
4. Read [USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) for more examples

---

**Version:** 0.1.0 | **Status:** Ready for MVP testing
