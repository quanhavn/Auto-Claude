#!/usr/bin/env python3
"""
Test script to verify custom model ID resolution.
Tests the 3-tier priority system:
1. Global config file (~/.auto-claude/config.json)
2. Environment variables (CUSTOM_*_MODEL)
3. Hardcoded defaults
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config import get_config_file_path, load_global_config, save_global_config
from phase_config import resolve_model_id

# Enable logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def test_default_models():
    """Test default model resolution without any custom config"""
    print("\n" + "="*60)
    print("TEST 1: Default Models (no custom config)")
    print("="*60)

    for model in ["haiku", "sonnet", "opus"]:
        resolved = resolve_model_id(model)
        print(f"  {model:10} → {resolved}")


def test_config_file():
    """Test custom models from config file"""
    print("\n" + "="*60)
    print("TEST 2: Custom Models from Config File")
    print("="*60)

    config_path = get_config_file_path()
    print(f"Config file: {config_path}")

    # Create test config
    test_config = {
        "customHaikuModelId": "custom-haiku-test-123",
        "customSonnetModelId": "custom-sonnet-test-456",
        "customOpusModelId": "custom-opus-test-789"
    }

    print(f"Writing test config: {test_config}")
    save_global_config(test_config)

    # Reload and test
    loaded_config = load_global_config()
    print(f"Loaded config: {loaded_config}")

    for model in ["haiku", "sonnet", "opus"]:
        resolved = resolve_model_id(model)
        print(f"  {model:10} → {resolved}")


def test_env_vars():
    """Test custom models from environment variables"""
    print("\n" + "="*60)
    print("TEST 3: Custom Models from Environment Variables")
    print("="*60)

    # Delete config file to test env vars
    config_path = get_config_file_path()
    if config_path.exists():
        config_path.unlink()
        print(f"Deleted config file: {config_path}")

    # Set env vars
    os.environ["CUSTOM_HAIKU_MODEL"] = "env-haiku-999"
    os.environ["CUSTOM_SONNET_MODEL"] = "env-sonnet-888"
    os.environ["CUSTOM_OPUS_MODEL"] = "env-opus-777"

    print("Set environment variables:")
    print(f"  CUSTOM_HAIKU_MODEL = {os.environ['CUSTOM_HAIKU_MODEL']}")
    print(f"  CUSTOM_SONNET_MODEL = {os.environ['CUSTOM_SONNET_MODEL']}")
    print(f"  CUSTOM_OPUS_MODEL = {os.environ['CUSTOM_OPUS_MODEL']}")

    for model in ["haiku", "sonnet", "opus"]:
        resolved = resolve_model_id(model)
        print(f"  {model:10} → {resolved}")

    # Clean up env vars
    del os.environ["CUSTOM_HAIKU_MODEL"]
    del os.environ["CUSTOM_SONNET_MODEL"]
    del os.environ["CUSTOM_OPUS_MODEL"]


def test_priority():
    """Test priority: config file > env vars > defaults"""
    print("\n" + "="*60)
    print("TEST 4: Priority System (Config > Env > Defaults)")
    print("="*60)

    # Set both config and env
    save_global_config({"customOpusModelId": "config-opus-priority"})
    os.environ["CUSTOM_OPUS_MODEL"] = "env-opus-should-be-ignored"

    print("Config has: customOpusModelId = config-opus-priority")
    print("Env has: CUSTOM_OPUS_MODEL = env-opus-should-be-ignored")
    print("Expected: config-opus-priority (config wins)")

    resolved = resolve_model_id("opus")
    print(f"Actual: {resolved}")

    assert resolved == "config-opus-priority", "Config file should have priority over env vars!"
    print("✓ Priority system works correctly!")

    # Clean up
    if "CUSTOM_OPUS_MODEL" in os.environ:
        del os.environ["CUSTOM_OPUS_MODEL"]


def cleanup():
    """Clean up test config file"""
    config_path = get_config_file_path()
    if config_path.exists():
        config_path.unlink()
        print(f"\nCleaned up test config: {config_path}")


if __name__ == "__main__":
    try:
        test_default_models()
        test_config_file()
        test_env_vars()
        test_priority()

        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cleanup()
