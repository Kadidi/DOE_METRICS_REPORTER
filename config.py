#!/usr/bin/env python3
"""Central configuration for DOE Metrics Reporter."""
import os
from pathlib import Path

# Installation directory (set during deployment)
INSTALL_DIR = os.getenv(
    "DOE_METRICS_INSTALL_DIR",
    "/global/common/software/nersc/google-docs-qa"
)

# =============================================================================
# Slack Configuration
# =============================================================================

def get_slack_token():
    """Get Slack bot token from central config or environment."""
    # First, check environment variable (for testing/override)
    token = os.getenv("SLACK_BOT_TOKEN")
    if token:
        return token

    # Next, check central config file
    config_file = Path(INSTALL_DIR) / ".slack_token"
    if config_file.exists():
        try:
            with open(config_file) as f:
                token = f.read().strip()
                if token:
                    return token
        except Exception:
            pass

    # Finally, check local directory (for development)
    local_config = Path(__file__).parent / ".slack_token"
    if local_config.exists():
        try:
            with open(local_config) as f:
                token = f.read().strip()
                if token:
                    return token
        except Exception:
            pass

    return None


# =============================================================================
# Google API Configuration
# =============================================================================

def get_google_token_path():
    """Get path to user's Google token."""
    # Users store their own Google tokens in their home directory
    return os.path.expanduser("~/token.json")


# =============================================================================
# SF API Configuration
# =============================================================================

def get_sfapi_client_id():
    """Get SF API client ID from environment."""
    return os.getenv("SFAPI_CLIENT_ID")


def get_sfapi_key_path():
    """Get path to SF API private key."""
    # Check environment variable first
    key_path = os.getenv("SFAPI_KEY_PATH")
    if key_path:
        return os.path.expanduser(key_path)
    
    # Default location
    default_path = os.path.expanduser("/global/homes/k/kadidia/priv_key.pem")
    if os.path.exists(default_path):
        return default_path
    
    # Alternative location
    alt_path = os.path.expanduser("~/.secrets/sfapi_client.pem")
    if os.path.exists(alt_path):
        return alt_path
    
    return None


def is_sfapi_configured():
    """Check if SF API is properly configured."""
    client_id = get_sfapi_client_id()
    key_path = get_sfapi_key_path()
    
    if not client_id:
        return False
    
    if not key_path or not os.path.exists(key_path):
        return False
    
    return True


# =============================================================================
# Documents Configuration
# =============================================================================

def get_config_path():
    """Get path to documents configuration."""
    # Check if user has custom config
    user_config = Path.home() / ".doe_metrics_config.yaml"
    if user_config.exists():
        return str(user_config)

    # Use central config
    central_config = Path(INSTALL_DIR) / "documents_config.yaml"
    if central_config.exists():
        return str(central_config)

    # Fall back to local
    local_config = Path(__file__).parent / "documents_config.yaml"
    return str(local_config)


# =============================================================================
# AI API Configuration
# =============================================================================

def get_ai_api_key():
    """Get AI API key from supported environment variables."""
    return os.getenv("ANTHROPIC_API_KEY") or os.getenv("CBORG_API_KEY")


def get_ai_base_url():
    """Get AI API base URL (for CBORG or other compatible endpoints)."""
    # Check for CBORG
    if os.getenv("CBORG_API_KEY"):
        return os.getenv("CBORG_BASE_URL", "https://api.cborg.lbl.gov/v1")
    
    # Check for custom Anthropic base URL
    return os.getenv("ANTHROPIC_BASE_URL")


# =============================================================================
# Status/Debug Functions
# =============================================================================

def print_config_status():
    """Print the current configuration status."""
    print("=" * 60)
    print("DOE Metrics Reporter - Configuration Status")
    print("=" * 60)
    
    # Slack
    slack_token = get_slack_token()
    print(f"\nSlack:")
    if slack_token:
        print(f"   ✅ Token configured ({slack_token[:15]}...)")
    else:
        print(f"   ❌ Token not configured")
    
    # Google
    google_token = get_google_token_path()
    print(f"\nGoogle Docs:")
    if os.path.exists(google_token):
        print(f"   ✅ Token exists ({google_token})")
    else:
        print(f"   ❌ Token not found ({google_token})")
    
    # SF API
    print(f"\nSF API:")
    sfapi_id = get_sfapi_client_id()
    sfapi_key = get_sfapi_key_path()
    if sfapi_id:
        print(f"   ✅ Client ID configured ({sfapi_id[:10]}...)")
    else:
        print(f"   ❌ Client ID not set (SFAPI_CLIENT_ID)")
    if sfapi_key and os.path.exists(sfapi_key):
        print(f"   ✅ Key file exists ({sfapi_key})")
    else:
        print(f"   ❌ Key file not found")
    
    # AI
    print(f"\nAI API:")
    ai_key = get_ai_api_key()
    ai_url = get_ai_base_url()
    if ai_key:
        print(f"   ✅ API key configured")
        if ai_url:
            print(f"      Using custom endpoint: {ai_url}")
    else:
        print(f"   ❌ API key not set (ANTHROPIC_API_KEY or CBORG_API_KEY)")
    
    # Config file
    print(f"\nConfig file:")
    config_path = get_config_path()
    if os.path.exists(config_path):
        print(f"   ✅ {config_path}")
    else:
        print(f"   ❌ Not found: {config_path}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_config_status()
