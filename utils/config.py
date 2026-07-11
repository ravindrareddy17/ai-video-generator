"""
Configuration loader for AI Video Generator V2.

Loads API keys from .env and project settings from config/settings.json.
Uses @lru_cache to avoid re-reading settings.json on every call.

NOTE: Does NOT import utils.logger to avoid circular dependencies.
      Uses standard logging directly where needed.
"""

import json
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap – make project root importable
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import SETTINGS_FILE, ENV_FILE, PROJECT_ROOT  # noqa: E402

# ---------------------------------------------------------------------------
# Module-level logger (stdlib only – no utils.logger import)
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load .env into os.environ (idempotent, won't overwrite existing vars)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=str(ENV_FILE), override=False)
    log.debug("Loaded .env from %s", ENV_FILE)
except ImportError:
    log.warning(
        "python-dotenv is not installed. "
        "Environment variables must be set externally."
    )


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_settings() -> dict[str, Any]:
    """Load and return *config/settings.json* as a dictionary.

    The result is cached after the first call.  To force a reload, call
    ``load_settings.cache_clear()`` first.

    Returns:
        dict: Parsed settings dictionary.

    Raises:
        FileNotFoundError: If settings.json does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    settings_path = Path(SETTINGS_FILE)
    if not settings_path.exists():
        raise FileNotFoundError(
            f"Settings file not found: {settings_path}"
        )

    with settings_path.open("r", encoding="utf-8") as fh:
        settings: dict[str, Any] = json.load(fh)

    log.debug("Loaded settings from %s (%d top-level keys)",
              settings_path, len(settings))
    return settings


def get_setting(section: str, key: str, default: Any = None) -> Any:
    """Retrieve a nested value from settings.json.

    Example::

        model = get_setting("llm", "model")          # "llama-3.3-70b-versatile"
        fps   = get_setting("video", "fps", 30)

    Args:
        section: Top-level key (e.g. ``"llm"``, ``"video"``).
        key: Second-level key within *section*.
        default: Fallback value if *section* or *key* is missing.

    Returns:
        The requested setting value, or *default*.
    """
    settings = load_settings()
    try:
        return settings[section][key]
    except (KeyError, TypeError):
        return default


# ---------------------------------------------------------------------------
# API-key accessors
# ---------------------------------------------------------------------------

def _require_env(var_name: str) -> str:
    """Return the value of an environment variable or raise ``ValueError``.

    Args:
        var_name: Name of the environment variable.

    Returns:
        The non-empty string value.

    Raises:
        ValueError: If the variable is unset or empty.
    """
    value = os.getenv(var_name, "").strip()
    if not value:
        raise ValueError(
            f"Environment variable '{var_name}' is not set. "
            f"Add it to your .env file at {ENV_FILE}"
        )
    return value


def get_groq_key() -> str:
    """Return the ``GROQ_API_KEY`` from the environment.

    Raises:
        ValueError: If the key is not set.
    """
    return _require_env("GROQ_API_KEY")


def get_pexels_key() -> str:
    """Return the ``PEXELS_API_KEY`` from the environment.

    Raises:
        ValueError: If the key is not set.
    """
    return _require_env("PEXELS_API_KEY")


def get_pixabay_key() -> str:
    """Return the ``PIXABAY_API_KEY`` from the environment.

    Raises:
        ValueError: If the key is not set.
    """
    return _require_env("PIXABAY_API_KEY")


def get_gemini_key() -> str:
    """Return the ``GEMINI_API_KEY`` from the environment.

    Raises:
        ValueError: If the key is not set.
    """
    return _require_env("GEMINI_API_KEY")


# ---------------------------------------------------------------------------
# Meta / Facebook / Instagram accessors
# ---------------------------------------------------------------------------

def get_meta_app_id() -> str:
    """Return the ``META_APP_ID`` from the environment."""
    return _require_env("META_APP_ID")


def get_meta_app_secret() -> str:
    """Return the ``META_APP_SECRET`` from the environment."""
    return _require_env("META_APP_SECRET")


def get_meta_access_token() -> str:
    """Return the ``META_ACCESS_TOKEN`` from the environment."""
    return _require_env("META_ACCESS_TOKEN")


def get_facebook_page_id() -> str:
    """Return the ``FACEBOOK_PAGE_ID`` from the environment."""
    return _require_env("FACEBOOK_PAGE_ID")


def get_instagram_account_id() -> str:
    """Return the ``INSTAGRAM_BUSINESS_ACCOUNT_ID`` from the environment."""
    return _require_env("INSTAGRAM_BUSINESS_ACCOUNT_ID")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  AI Video Generator V2 – config.py self-test")
    print("=" * 60)

    # --- Settings ---------------------------------------------------------
    print(f"\n[settings.json]  path = {SETTINGS_FILE}")
    try:
        settings = load_settings()
        print(f"  Loaded OK – {len(settings)} top-level sections:")
        for section, values in settings.items():
            if isinstance(values, dict):
                print(f"    {section}: {list(values.keys())}")
            else:
                print(f"    {section}: {values}")
    except Exception as exc:
        print(f"  FAILED to load settings: {exc}")

    # --- Nested setting ---------------------------------------------------
    model = get_setting("llm", "model")
    print(f"\n  get_setting('llm', 'model')   = {model}")
    fps = get_setting("video", "fps", 30)
    print(f"  get_setting('video', 'fps')   = {fps}")
    missing = get_setting("nonexistent", "key", "DEFAULT")
    print(f"  get_setting('nonexistent', 'key', 'DEFAULT') = {missing}")

    # --- API keys ---------------------------------------------------------
    print(f"\n[.env]  path = {ENV_FILE}")

    key_funcs = {
        "GROQ_API_KEY": get_groq_key,
        "PEXELS_API_KEY": get_pexels_key,
        "PIXABAY_API_KEY": get_pixabay_key,
        "GEMINI_API_KEY": get_gemini_key,
    }

    for name, func in key_funcs.items():
        try:
            val = func()
            # Show only first/last 4 chars for safety
            masked = val[:4] + "***" + val[-4:] if len(val) > 8 else "***"
            print(f"  {name}: {masked}")
        except ValueError as exc:
            print(f"  {name}: MISSING – {exc}")

    print("\n" + "=" * 60)
    print("  Self-test complete.")
    print("=" * 60)
