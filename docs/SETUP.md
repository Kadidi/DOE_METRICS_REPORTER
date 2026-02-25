# DOE_METRICS_REPORTER Setup Guide

Complete installation and configuration instructions for DOE_METRICS_REPORTER.

## Prerequisites

- **Python 3.11 or higher**
- **pip** or **uv** package manager
- **API credentials** for services you want to use (Google Docs, Slack, etc.)

## Installation Steps

### 1. Clone/Download the Project

```bash
cd DOE_METRICS_REPORTER
```

### 2. Make Scripts Executable

```bash
chmod +x setup_user.sh start_reporter.sh
```

### 3. Install Python Dependencies

Using pip:
```bash
pip install -e .
```

Using uv (faster):
```bash
uv pip install -e .
```

### 4. Run Setup Wizard

```bash
./setup_user.sh
```

This interactive script will:
- Create a `.env` file with secure permissions (mode 600)
- Prompt you to enter API credentials
- Configure cache directory and logging level
- Validate configuration

### 5. Start the Reporter

```bash
./start_reporter.sh
```

You should see:
```
==========================================
DOE_METRICS_REPORTER
==========================================

Configuration loaded from: /path/to/.env
Server registry: servers.config
Cache directory: ./cache

Starting MCP servers from registry...
✓ Found server: google_docs (servers/google_docs_server.py)
✓ Found server: slack (servers/slack_server.py)

Starting DOE_METRICS_REPORTER CLI...
Type 'help' for commands, 'exit' to quit

DOE_METRICS>
```

## Configuration

### Environment Variables (.env)

The `.env` file stores sensitive configuration. **Never commit this to git.**

Create from template:
```bash
cp .env.template .env
```

Edit with your API credentials:
```bash
nano .env
```

#### Google Docs Configuration

Required for Google Docs support:
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_CREDENTIALS_JSON=/path/to/credentials.json
```

#### Slack Configuration

Required for Slack support:
```
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your-signing-secret
```

#### Cache Configuration

Optional (has sensible defaults):
```
CACHE_DIR=./cache                    # Where to store cache.db
CACHE_DB=./cache/cache.db
LOG_LEVEL=INFO                       # DEBUG, INFO, WARNING, ERROR
```

### Server Registry (servers.config)

Control which MCP servers load by editing `servers.config`:

```
# Active servers (loaded on startup)
google_docs:servers/google_docs_server.py
slack:servers/slack_server.py

# Commented out servers (enable when ready)
# elasticsearch:servers/elasticsearch_server.py
# slurm:servers/slurm_server.py
```

Format: `name:relative/path/to/server.py`

To enable/disable a server:
- **Enable**: Remove the `#` comment
- **Disable**: Add `#` comment
- Restart the client with `./start_reporter.sh`

## Troubleshooting

### "Configuration file not found"

```
❌ Error: .env file not found
```

**Solution**: Run setup first
```bash
./setup_user.sh
```

### "servers.config not found"

```
❌ Error: servers.config not found
```

**Solution**: Ensure you're in the DOE_METRICS_REPORTER directory

### "Server not found: google_docs"

```
⚠️  Server not found: google_docs (servers/google_docs_server.py)
```

**Solution**: Check that the server file exists
```bash
ls -la servers/google_docs_server.py
```

### Python version too old

```
ERROR: Python 3.11+ is required
```

**Solution**: Install newer Python
```bash
# Check current version
python3 --version

# Use specific Python version
python3.11 -m pip install -e .
python3.11 doe_metrics_client.py
```

### Permission denied on scripts

```
-bash: ./start_reporter.sh: Permission denied
```

**Solution**: Make scripts executable
```bash
chmod +x setup_user.sh start_reporter.sh
```

### Import errors when running client

```
ModuleNotFoundError: No module named 'cache'
```

**Solution**: Ensure you installed the package and are in the project root
```bash
pip install -e .
cd DOE_METRICS_REPORTER
./start_reporter.sh
```

### Cache directory errors

```
FileNotFoundError: [Errno 2] No such file or directory: './cache/cache.db'
```

**Solution**: Cache directory will be created automatically, but ensure write permissions
```bash
mkdir -p ./cache
chmod 700 ./cache
```

## Next Steps

1. **Configure API Credentials** - See [API_CONFIGURATION.md](API_CONFIGURATION.md)
2. **Try Examples** - See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
3. **Add New Servers** - See [ADDING_SERVERS.md](ADDING_SERVERS.md) when ready for Phase 2

## Uninstallation

To remove DOE_METRICS_REPORTER:

```bash
# Remove Python package
pip uninstall doe-metrics-reporter

# Remove project files
rm -rf DOE_METRICS_REPORTER/

# Optional: Remove Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

## Getting Help

- Type `help` in the CLI for available commands
- Check logs for errors: `tail -f .env | grep LOG_LEVEL`
- Review documentation in `docs/` directory
- Contact NERSC support for API credential issues

---

**Last Updated:** 2025-01-26
