"""Utilities for loading and validating API key configuration.

This module centralizes how the application discovers API keys across
environment variables, optional ``.env`` files, and the persisted
``config.json``. It also provides lightweight validation helpers so UI
controllers can give immediate feedback when a key looks malformed.
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, Tuple


GOOGLE_KEY_PATTERN = re.compile(r"^AIza[0-9A-Za-z\-_]{30,}")

# Mapping of environment variable names to the internal config keys we expect.
ENV_KEY_MAPPING = {
    "GOOGLE_API_KEY": "writer_key",
    "GOOGLE_VISION_API_KEY": "vision_key",
    "GOOGLE_IMAGEN_API_KEY": "image_key",
}


def sanitize_key(raw_key: str | None) -> str:
    """Remove leading/trailing whitespace from an API key string.

    Parameters
    ----------
    raw_key:
        The user-supplied key value; may be ``None`` or empty.

    Returns
    -------
    str
        A trimmed key string (or an empty string when no key was provided).
    """

    if not raw_key:
        return ""
    return raw_key.strip()


def _load_json_config(config_path: str) -> Dict[str, str]:
    if not os.path.exists(config_path):
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            data = json.load(config_file)
            return {k: sanitize_key(v) for k, v in data.items() if isinstance(v, str)}
    except (OSError, json.JSONDecodeError):
        return {}


def _load_env_file(env_path: str) -> Dict[str, str]:
    if not os.path.exists(env_path):
        return {}

    values: Dict[str, str] = {}
    with open(env_path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            text = line.strip()
            if not text or text.startswith("#") or "=" not in text:
                continue
            key, value = text.split("=", 1)
            values[key.strip()] = sanitize_key(value)
    return values


def load_api_keys(config_path: str = "config.json", env_path: str = ".env") -> Dict[str, str]:
    """Load API keys from JSON config, ``.env`` file, and environment variables.

    Precedence (lowest to highest):
    1) ``config.json`` values
    2) values in the ``.env`` file
    3) active process environment variables

    Parameters
    ----------
    config_path:
        Path to the JSON configuration file.
    env_path:
        Path to a dotenv-style file with ``KEY=VALUE`` entries.

    Returns
    -------
    Dict[str, str]
        A dictionary with keys ``vision_key``, ``writer_key`` and ``image_key``.
    """

    keys: Dict[str, str] = {
        "vision_key": "",
        "writer_key": "",
        "image_key": "",
    }

    config_values = _load_json_config(config_path)
    keys.update({k: v for k, v in config_values.items() if k in keys or k == "gemini_key"})

    env_file_values = _load_env_file(env_path)
    for env_name, internal_name in ENV_KEY_MAPPING.items():
        if env_name in env_file_values:
            keys[internal_name] = env_file_values[env_name]
    # Legacy naming support
    if "GEMINI_KEY" in env_file_values:
        keys["writer_key"] = env_file_values["GEMINI_KEY"]

    for env_name, internal_name in ENV_KEY_MAPPING.items():
        env_value = os.getenv(env_name)
        if env_value:
            keys[internal_name] = sanitize_key(env_value)

    return keys


def validate_google_api_key(key: str) -> Tuple[bool, str]:
    """Validate that a Google API key has the expected shape.

    Parameters
    ----------
    key:
        The key string to validate.

    Returns
    -------
    Tuple[bool, str]
        ``(True, "")`` when the key looks valid, otherwise ``(False, reason)``.
    """

    cleaned = sanitize_key(key)
    if not cleaned:
        return False, "API-Schlüssel fehlt."
    if not GOOGLE_KEY_PATTERN.match(cleaned):
        return False, "Google API Keys sollten mit 'AIza' beginnen und >= 30 Zeichen lang sein."
    return True, ""
