"""
Meta Graph API Authentication & Token Management
=================================================

Handles Meta Graph API authentication, token validation, refresh,
and credential management for the AI Video Generator V2 pipeline.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Project-level import path setup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from utils.config import (
    get_meta_app_id,
    get_meta_app_secret,
    get_meta_access_token,
    get_facebook_page_id,
    get_instagram_account_id,
)
from utils.logger import get_logger
from utils.paths import ENV_FILE

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_GRAPH_BASE_URL: str = "https://graph.facebook.com"
_DEFAULT_GRAPH_API_VERSION: str = "v25.0"

# Tokens expiring within this window (seconds) are considered "near expiry".
_EXPIRY_BUFFER_SECONDS: int = 7 * 24 * 60 * 60  # 7 days


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _graph_url(version: str, base_url: str) -> str:
    """Return the versioned Graph API root, e.g. ``https://graph.facebook.com/v25.0``."""
    return f"{base_url.rstrip('/')}/{version}"


def _mask(value: str | None, visible: int = 4) -> str:
    """Mask a secret string, showing only the last *visible* characters."""
    if not value:
        return "<not set>"
    if len(value) <= visible:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]


def _save_token_to_env(new_token: str) -> None:
    """Persist a refreshed access token to .env and os.environ.

    Reads the current .env file, replaces the META_ACCESS_TOKEN line,
    and writes it back.  Also updates os.environ so subsequent calls
    within the same process use the new token without re-reading .env.
    """
    os.environ["META_ACCESS_TOKEN"] = new_token

    try:
        env_path = ENV_FILE
        if not env_path.exists():
            logger.warning(".env file not found at %s — token not persisted to disk.", env_path)
            return

        lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("META_ACCESS_TOKEN="):
                lines[i] = f"META_ACCESS_TOKEN={new_token}\n"
                updated = True
                break

        if not updated:
            lines.append(f"META_ACCESS_TOKEN={new_token}\n")

        env_path.write_text("".join(lines), encoding="utf-8")
        logger.info("Refreshed token persisted to %s", env_path)
    except Exception as exc:
        logger.warning("Could not persist refreshed token to .env: %s", exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_credentials() -> dict[str, str | None]:
    """Load all Meta-related credentials and settings into a dictionary.

    Keys returned:
        app_id, app_secret, access_token, page_id, instagram_id,
        graph_base_url, graph_api_version
    """
    credentials: dict[str, str | None] = {
        "app_id": get_meta_app_id(),
        "app_secret": get_meta_app_secret(),
        "access_token": get_meta_access_token(),
        "page_id": get_facebook_page_id(),
        "instagram_id": get_instagram_account_id(),
        "graph_base_url": os.getenv("META_GRAPH_BASE_URL", _DEFAULT_GRAPH_BASE_URL),
        "graph_api_version": os.getenv("META_GRAPH_API_VERSION", _DEFAULT_GRAPH_API_VERSION),
    }
    logger.info("Meta credentials loaded successfully.")
    return credentials


def validate_access_token(token: str) -> dict:
    """Validate an access token via the Graph API ``debug_token`` endpoint.

    Parameters
    ----------
    token:
        The access token to inspect.

    Returns
    -------
    dict
        The full parsed JSON response from the ``debug_token`` call.
    """
    creds = load_credentials()
    app_id: str = creds["app_id"] or ""
    app_secret: str = creds["app_secret"] or ""
    base_url: str = creds["graph_base_url"] or _DEFAULT_GRAPH_BASE_URL
    version: str = creds["graph_api_version"] or _DEFAULT_GRAPH_API_VERSION

    url = f"{_graph_url(version, base_url)}/debug_token"
    params: dict[str, str] = {
        "input_token": token,
        "access_token": f"{app_id}|{app_secret}",
    }

    logger.info("Validating access token via debug_token endpoint …")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data: dict = response.json()
    except requests.RequestException as exc:
        logger.error("Token validation request failed: %s", exc)
        raise

    # Log useful details from the response
    token_data: dict = data.get("data", {})
    token_type: str = token_data.get("type", "unknown")
    scopes: list[str] = token_data.get("scopes", [])
    expires_at: int = token_data.get("expires_at", 0)

    if expires_at:
        expiry_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        logger.info(
            "Token info — type: %s | scopes: %s | expires: %s",
            token_type,
            ", ".join(scopes) if scopes else "none",
            expiry_dt.isoformat(),
        )
    else:
        logger.info(
            "Token info — type: %s | scopes: %s | expires: never",
            token_type,
            ", ".join(scopes) if scopes else "none",
        )

    is_valid: bool = token_data.get("is_valid", False)
    if is_valid:
        logger.info("Access token is valid.")
    else:
        error_info = token_data.get("error", {})
        logger.warning(
            "Access token is INVALID. Error: %s — %s",
            error_info.get("code", "n/a"),
            error_info.get("message", "no message"),
        )

    return data


def refresh_access_token(token: str) -> str:
    """Exchange a short-lived token for a long-lived one.

    Parameters
    ----------
    token:
        The short-lived (or existing) access token to exchange.

    Returns
    -------
    str
        The new long-lived access token.

    Raises
    ------
    RuntimeError
        If the token exchange fails.
    """
    creds = load_credentials()
    app_id: str = creds["app_id"] or ""
    app_secret: str = creds["app_secret"] or ""
    base_url: str = creds["graph_base_url"] or _DEFAULT_GRAPH_BASE_URL
    version: str = creds["graph_api_version"] or _DEFAULT_GRAPH_API_VERSION

    url = f"{_graph_url(version, base_url)}/oauth/access_token"
    params: dict[str, str] = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": token,
    }

    logger.info("Attempting to exchange token for a long-lived token …")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data: dict = response.json()
    except requests.RequestException as exc:
        logger.error("Token refresh request failed: %s", exc)
        raise RuntimeError(f"Failed to refresh access token: {exc}") from exc

    new_token: str | None = data.get("access_token")
    if not new_token:
        error_msg = data.get("error", {}).get("message", "Unknown error")
        logger.error("Token refresh returned no access_token: %s", error_msg)
        raise RuntimeError(f"Token refresh failed: {error_msg}")

    expires_in: int = data.get("expires_in", 0)
    if expires_in:
        expiry_dt = datetime.fromtimestamp(time.time() + expires_in, tz=timezone.utc)
        logger.info(
            "Token refreshed successfully. New token expires: %s (~%d days)",
            expiry_dt.isoformat(),
            expires_in // 86400,
        )
    else:
        logger.info("Token refreshed successfully (no expiry info returned).")

    return new_token


def create_headers(token: str) -> dict[str, str]:
    """Return authorization headers for Graph API requests.

    Parameters
    ----------
    token:
        A valid access token.

    Returns
    -------
    dict[str, str]
        Headers dictionary with ``Authorization: Bearer <token>``.
    """
    return {"Authorization": f"Bearer {token}"}


def get_valid_token(creds: dict[str, str | None] | None = None) -> str:
    """Obtain a valid Meta access token, refreshing if necessary.

    This is the **main entry point** for other modules that need a
    ready-to-use access token.

    Returns
    -------
    str
        A valid access token string.

    Raises
    ------
    ValueError
        If no valid token can be obtained.
    """
    if creds is None:
        creds = load_credentials()
    token: str | None = creds.get("access_token")

    if not token:
        raise ValueError(
            "No Meta access token found. Please set META_ACCESS_TOKEN in your "
            f"environment or in {ENV_FILE}."
        )

    # --- Validate -----------------------------------------------------------
    try:
        validation = validate_access_token(token)
    except Exception as exc:
        logger.error("Could not validate token: %s", exc)
        raise ValueError(
            "Failed to validate the Meta access token. Check your credentials "
            "and network connectivity."
        ) from exc

    token_data: dict = validation.get("data", {})
    is_valid: bool = token_data.get("is_valid", False)
    expires_at: int = token_data.get("expires_at", 0)

    needs_refresh: bool = False
    if not is_valid:
        logger.warning("Current token is invalid — attempting refresh.")
        needs_refresh = True
    elif expires_at:
        remaining = expires_at - time.time()
        if remaining < _EXPIRY_BUFFER_SECONDS:
            logger.warning(
                "Token expires in %.1f days — attempting refresh.",
                remaining / 86400,
            )
            needs_refresh = True

    # --- Refresh if needed --------------------------------------------------
    if needs_refresh:
        try:
            token = refresh_access_token(token)
            logger.info("Token refreshed successfully.")
            # Persist the new long-lived token to .env and os.environ
            _save_token_to_env(token)
        except Exception as exc:
            logger.error("Token refresh failed: %s", exc)
            if not is_valid:
                raise ValueError(
                    "Meta access token is invalid and could not be refreshed. "
                    "Please generate a new token in the Meta Developer portal."
                ) from exc
            # Token was still valid but near-expiry — use it as-is.
            logger.warning(
                "Continuing with near-expiry token; manual refresh recommended."
            )

    return token


def get_page_access_token(user_token: str, page_id: str) -> str:
    """Fetch the Page access token required for publishing to a Facebook Page.

    Parameters
    ----------
    user_token:
        A valid User access token with ``pages_manage_posts`` permission.
    page_id:
        The Facebook Page ID to retrieve a token for.

    Returns
    -------
    str
        The Page-scoped access token.

    Raises
    ------
    RuntimeError
        If the request fails or no token is returned.
    """
    creds = load_credentials()
    base_url: str = creds["graph_base_url"] or _DEFAULT_GRAPH_BASE_URL
    version: str = creds["graph_api_version"] or _DEFAULT_GRAPH_API_VERSION

    url = f"{_graph_url(version, base_url)}/{page_id}"
    params: dict[str, str] = {
        "fields": "access_token",
        "access_token": user_token,
    }

    logger.info("Fetching Page access token for page %s …", page_id)

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data: dict = response.json()
    except requests.RequestException as exc:
        logger.error("Failed to fetch Page access token: %s", exc)
        raise RuntimeError(
            f"Could not retrieve Page access token for page {page_id}: {exc}"
        ) from exc

    page_token: str | None = data.get("access_token")
    if not page_token:
        error_msg = data.get("error", {}).get("message", "No access_token in response")
        logger.error("Page token retrieval failed: %s", error_msg)
        raise RuntimeError(f"Page access token not returned: {error_msg}")

    logger.info("Page access token retrieved successfully for page %s.", page_id)
    return page_token


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("  Meta Graph API — Authentication Self-Test")
    print("=" * 60)

    # 1. Load & display credentials (masked) --------------------------------
    print("\n[1] Loading credentials …")
    try:
        creds = load_credentials()
        print(f"  App ID          : {_mask(creds.get('app_id'))}")
        print(f"  App Secret      : {_mask(creds.get('app_secret'))}")
        print(f"  Access Token    : {_mask(creds.get('access_token'))}")
        print(f"  Page ID         : {creds.get('page_id', '<not set>')}")
        print(f"  Instagram ID    : {creds.get('instagram_id', '<not set>')}")
        print(f"  Graph Base URL  : {creds.get('graph_base_url')}")
        print(f"  Graph API Ver   : {creds.get('graph_api_version')}")
    except Exception as exc:
        print(f"  ERROR loading credentials: {exc}")
        sys.exit(1)

    # 2. Validate token ------------------------------------------------------
    access_token: str | None = creds.get("access_token")
    if access_token:
        print("\n[2] Validating access token …")
        try:
            result = validate_access_token(access_token)
            token_data = result.get("data", {})
            token_type = token_data.get("type", "unknown")
            scopes = token_data.get("scopes", [])
            expires_at = token_data.get("expires_at", 0)
            is_valid = token_data.get("is_valid", False)

            print(f"  Valid           : {is_valid}")
            print(f"  Type            : {token_type}")
            print(f"  Scopes          : {', '.join(scopes) if scopes else 'none'}")
            if expires_at:
                expiry_str = datetime.fromtimestamp(
                    expires_at, tz=timezone.utc
                ).isoformat()
                print(f"  Expires         : {expiry_str}")
            else:
                print("  Expires         : never / not set")
        except Exception as exc:
            print(f"  ERROR validating token: {exc}")
    else:
        print("\n[2] Skipping token validation — no access token configured.")

    # 3. Test Page access token ----------------------------------------------
    page_id: str | None = creds.get("page_id")
    if access_token and page_id:
        print(f"\n[3] Fetching Page access token for page {page_id} …")
        try:
            page_token = get_page_access_token(access_token, page_id)
            print(f"  Page Token      : {_mask(page_token)}")
        except Exception as exc:
            print(f"  ERROR fetching page token: {exc}")
    else:
        print("\n[3] Skipping page token test — access_token or page_id not set.")

    print("\n" + "=" * 60)
    print("  Self-test complete.")
    print("=" * 60)
