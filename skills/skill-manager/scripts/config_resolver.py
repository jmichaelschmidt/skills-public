#!/usr/bin/env python3
"""Helpers for resolving skill-manager runtime configuration."""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_CONFIG_PATH = REPO_ROOT / 'config.json'
TEMPLATE_CONFIG_PATH = REPO_ROOT / 'config.template.json'
DEFAULT_USER_CONFIG_PATH = Path(
    os.environ.get('SKILL_MANAGER_CONFIG', '~/.config/skill-manager/config.json')
).expanduser()


def get_runtime_config_path() -> Path:
    """Return the preferred per-user runtime config path."""
    return DEFAULT_USER_CONFIG_PATH


def find_config_path() -> Path | None:
    """Resolve config path preferring user-local config over bundled defaults."""
    for path in (DEFAULT_USER_CONFIG_PATH, REPO_CONFIG_PATH):
        if path.exists():
            return path
    return None


def load_config_optional(default=None):
    """Load config if present, otherwise return default."""
    path = find_config_path()
    if path is None:
        return default
    with open(path) as f:
        return json.load(f)


def load_config_required() -> dict:
    """Load config or exit with a helpful message."""
    config = load_config_optional()
    if config is not None:
        return config

    print(f"ERROR: Config file not found. Checked: {DEFAULT_USER_CONFIG_PATH} and {REPO_CONFIG_PATH}")
    print("Run 'scripts/init.py' to create a user-local skill-manager configuration.")
    sys.exit(1)


def save_user_config(config: dict) -> Path:
    """Persist config to the user-local runtime path."""
    path = get_runtime_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)
    return path
