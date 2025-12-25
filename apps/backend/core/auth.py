"""
Authentication helpers for Auto Claude.

Provides centralized authentication token resolution with fallback support
for multiple environment variables, and SDK environment variable passthrough
for custom API endpoints.
"""

import json
import os
import platform
import subprocess

# Priority order for auth token resolution
# OAuth is preferred, but API keys are supported for advanced use cases
AUTH_TOKEN_ENV_VARS = [
    "CLAUDE_CODE_OAUTH_TOKEN",  # OAuth token from Claude Code CLI (priority 1)
    "ANTHROPIC_AUTH_TOKEN",  # CCR/proxy token (for enterprise setups) (priority 2)
    "ANTHROPIC_API_KEY",  # API key for direct billing (priority 3)
]

# Environment variables to pass through to SDK subprocess
SDK_ENV_VARS = [
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "NO_PROXY",
    "DISABLE_TELEMETRY",
    "DISABLE_COST_WARNINGS",
    "API_TIMEOUT_MS",
]


def get_token_from_keychain() -> str | None:
    """
    Get authentication token from macOS Keychain.

    Reads Claude Code credentials from macOS Keychain and extracts the OAuth token.
    Only works on macOS (Darwin platform).

    Returns:
        Token string if found in Keychain, None otherwise
    """
    # Only attempt on macOS
    if platform.system() != "Darwin":
        return None

    try:
        # Query macOS Keychain for Claude Code credentials
        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-s",
                "Claude Code-credentials",
                "-w",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        # Parse JSON response
        credentials_json = result.stdout.strip()
        if not credentials_json:
            return None

        data = json.loads(credentials_json)

        # Extract OAuth token from nested structure
        token = data.get("claudeAiOauth", {}).get("accessToken")

        if not token:
            return None

        # Validate token format (Claude OAuth tokens start with sk-ant-oat01-)
        if not token.startswith("sk-ant-oat01-"):
            return None

        return token

    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, Exception):
        # Silently fail - this is a fallback mechanism
        return None


def get_auth_token() -> str | None:
    """
    Get authentication token from environment variables or macOS Keychain.

    Checks multiple sources in priority order:
    1. CLAUDE_CODE_OAUTH_TOKEN (env var)
    2. ANTHROPIC_AUTH_TOKEN (CCR/proxy env var for enterprise setups)
    3. macOS Keychain (if on Darwin platform)

    NOTE: ANTHROPIC_API_KEY is intentionally NOT supported to prevent
    silent billing to user's API credits when OAuth is misconfigured.

    Returns:
        Token string if found, None otherwise
    """
    # First check environment variables
    for var in AUTH_TOKEN_ENV_VARS:
        token = os.environ.get(var)
        if token:
            return token

    # Fallback to macOS Keychain
    return get_token_from_keychain()


def get_auth_token_source() -> str | None:
    """Get the name of the source that provided the auth token."""
    # Check environment variables first
    for var in AUTH_TOKEN_ENV_VARS:
        if os.environ.get(var):
            return var

    # Check if token came from macOS Keychain
    if get_token_from_keychain():
        return "macOS Keychain"

    return None


def get_auth_type() -> str:
    """
    Get the authentication type being used.

    Returns:
        'oauth' for OAuth tokens (sk-ant-oat01-)
        'apikey' for API keys (sk-ant-api)
        'enterprise' for enterprise/CCR tokens
        'none' if no token is found
    """
    token = get_auth_token()
    if not token:
        return "none"

    if token.startswith("sk-ant-oat01-"):
        return "oauth"
    elif token.startswith("sk-ant-api"):
        return "apikey"
    else:
        return "enterprise"


def require_auth_token() -> str:
    """
    Get authentication token or raise ValueError.

    Raises:
        ValueError: If no auth token is found in any supported source
    """
    token = get_auth_token()
    if not token:
        error_msg = (
            "No authentication token found.\n\n"
            "Auto Claude supports OAuth (recommended) or API key authentication.\n\n"
        )
        # Provide platform-specific guidance
        if platform.system() == "Darwin":
            error_msg += (
                "To authenticate:\n"
                "Option 1 (OAuth - Recommended):\n"
                "  1. Run: claude setup-token\n"
                "  2. The token will be saved to macOS Keychain automatically\n\n"
                "Option 2 (API Key):\n"
                "  1. Get your API key from https://console.anthropic.com/\n"
                "  2. Set ANTHROPIC_API_KEY in your .env file\n"
                "  Note: API key usage will be billed to your Anthropic account."
            )
        else:
            error_msg += (
                "To authenticate:\n"
                "Option 1 (OAuth - Recommended):\n"
                "  1. Run: claude setup-token\n"
                "  2. Set CLAUDE_CODE_OAUTH_TOKEN in your .env file\n\n"
                "Option 2 (API Key):\n"
                "  1. Get your API key from https://console.anthropic.com/\n"
                "  2. Set ANTHROPIC_API_KEY in your .env file\n"
                "  Note: API key usage will be billed to your Anthropic account."
            )
        raise ValueError(error_msg)
    return token


def get_sdk_env_vars() -> dict[str, str]:
    """
    Get environment variables to pass to SDK.

    Collects relevant env vars (ANTHROPIC_BASE_URL, etc.) that should
    be passed through to the claude-agent-sdk subprocess.

    Priority order for ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY:
    1. Environment variables (for backwards compatibility)
    2. Global config file (~/.auto-claude/config.json)

    Returns:
        Dict of env var name -> value for non-empty vars
    """
    env = {}

    # First, collect all SDK env vars from environment
    for var in SDK_ENV_VARS:
        value = os.environ.get(var)
        if value:
            env[var] = value

    # Then, overlay with global config values if not already set
    # This allows global config to provide defaults while env vars can override
    try:
        from config import load_global_config

        global_config = load_global_config()

        # Set base URL from global config if not already set by env var
        if "ANTHROPIC_BASE_URL" not in env and global_config.get("globalAnthropicBaseUrl"):
            env["ANTHROPIC_BASE_URL"] = global_config["globalAnthropicBaseUrl"]

        # Set API key from global config if not already set by env var
        if "ANTHROPIC_API_KEY" not in env and global_config.get("globalAnthropicApiKey"):
            env["ANTHROPIC_API_KEY"] = global_config["globalAnthropicApiKey"]
    except (ImportError, Exception):
        # Config module not available or error reading - env vars only
        pass

    return env


def ensure_claude_code_oauth_token() -> None:
    """
    Ensure CLAUDE_CODE_OAUTH_TOKEN is set (for SDK compatibility).

    If not set but other auth tokens are available, copies the value
    to CLAUDE_CODE_OAUTH_TOKEN so the underlying SDK can use it.
    """
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return

    token = get_auth_token()
    if token:
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = token
