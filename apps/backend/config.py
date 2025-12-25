"""
Global Configuration Module
============================

Reads global Auto Claude configuration from ~/.auto-claude/config.json
This file is shared between frontend (Electron) and backend (Python).

Frontend writes to this file when user changes settings.
Backend reads from this file to get global preferences like custom model IDs.
"""

import json
import os
from pathlib import Path
from typing import TypedDict


class GlobalConfig(TypedDict, total=False):
    """Structure of global config file"""

    customHaikuModelId: str
    customSonnetModelId: str
    customOpusModelId: str
    globalAnthropicBaseUrl: str
    globalAnthropicApiKey: str


def get_config_file_path() -> Path:
    """
    Get the path to the global config file.

    Returns:
        Path to ~/.auto-claude/config.json
    """
    home = Path.home()
    config_dir = home / ".auto-claude"
    config_file = config_dir / "config.json"
    return config_file


def load_global_config() -> GlobalConfig:
    """
    Load global configuration from ~/.auto-claude/config.json

    Returns:
        Parsed configuration dict, or empty dict if file doesn't exist
    """
    config_file = get_config_file_path()

    if not config_file.exists():
        return {}

    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def get_custom_model_id(model_shorthand: str) -> str | None:
    """
    Get custom model ID from global config.

    Args:
        model_shorthand: "haiku", "sonnet", or "opus"

    Returns:
        Custom model ID if set, None otherwise
    """
    config = load_global_config()

    field_map = {
        "haiku": "customHaikuModelId",
        "sonnet": "customSonnetModelId",
        "opus": "customOpusModelId",
    }

    field_name = field_map.get(model_shorthand)
    if not field_name:
        return None

    return config.get(field_name)


def save_global_config(config: GlobalConfig) -> None:
    """
    Save global configuration to ~/.auto-claude/config.json

    Note: This is typically called from the frontend (Electron).
    Backend should only read, not write.

    Args:
        config: Configuration dict to save
    """
    config_file = get_config_file_path()

    # Create directory if it doesn't exist
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
