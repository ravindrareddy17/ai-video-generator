"""
upload_facebook.py — Upload Reels and videos to Facebook Pages via the Meta Graph API.

Part of the AI Video Generator V2 pipeline. Handles the three-phase Reels upload
(start → binary upload → finish), status polling, post deletion, and database updates.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Project path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from utils.logger import get_logger
from utils.paths import FINAL_VIDEO_FILE, THUMBNAIL_FILE, METADATA_FILE
from utils.helpers import load_json
from utils.database import get_connection
from utils.config import get_facebook_page_id, get_setting
import meta_auth

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GRAPH_API_BASE: str = "https://graph.facebook.com"
RUPLOAD_BASE: str = "https://rupload.facebook.com/video-upload"
DEFAULT_API_VERSION: str = "v25.0"
REQUEST_TIMEOUT: int = 60  # seconds
MAX_FILE_SIZE_BYTES: int = 1_073_741_824  # 1 GB warning threshold
RATE_LIMIT_WAIT: int = 60  # seconds to wait on HTTP 429


def _api_version() -> str:
    """Return the Graph API version from env/settings or the default."""
    return os.environ.get(
        "FACEBOOK_API_VERSION",
        get_setting("meta", "graph_api_version", DEFAULT_API_VERSION),
    )


def _base_url() -> str:
    """Build the versioned Graph API base URL."""
    return f"{GRAPH_API_BASE}/{_api_version()}"


def _get_page_token() -> str | None:
    """Obtain a valid Page Access Token, refreshing the user token first."""
    try:
        creds = meta_auth.load_credentials()
        user_token = meta_auth.get_valid_token(creds)
        if not user_token:
            logger.error("User access token is expired or invalid — cannot proceed.")
            return None

        page_id = get_facebook_page_id()
        page_token = meta_auth.get_page_access_token(user_token, page_id)
        if not page_token:
            logger.error(
                "Failed to retrieve Page Access Token for page %s.", page_id
            )
            return None

        return page_token
    except Exception:
        logger.exception("Error obtaining Page Access Token.")
        return None


def _handle_api_error(response: requests.Response, phase: str) -> None:
    """Log a structured error from a Graph API response."""
    try:
        error_body = response.json()
    except ValueError:
        error_body = {"raw": response.text}

    error_info = error_body.get("error", error_body)
    code = error_info.get("code", "unknown")
    message = error_info.get("message", str(error_info))
    error_type = error_info.get("type", "unknown")

    # Detect specific permission errors
    if code in (10, 200, 190):
        sub_code = error_info.get("error_subcode", "")
        logger.error(
            "[%s] Permission / auth error (code=%s, subcode=%s): %s — "
            "check that the token has pages_manage_posts, pages_read_engagement, "
            "and pages_show_list permissions.",
            phase,
            code,
            sub_code,
            message,
        )
    else:
        logger.error(
            "[%s] Graph API error (type=%s, code=%s): %s",
            phase,
            error_type,
            code,
            message,
        )


def _request_with_retry(
    method: str,
    url: str,
    *,
    retries: int = 1,
    **kwargs,
) -> requests.Response | None:
    """Execute an HTTP request with rate-limit handling and retries."""
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)

    for attempt in range(1 + retries):
        try:
            resp = requests.request(method, url, **kwargs)

            if resp.status_code == 429:
                retry_after = int(
                    resp.headers.get("Retry-After", RATE_LIMIT_WAIT)
                )
                logger.warning(
                    "Rate limited (429). Waiting %d s before retry…", retry_after
                )
                time.sleep(retry_after)
                continue

            return resp

        except requests.exceptions.Timeout:
            logger.warning(
                "Request timed out (attempt %d/%d): %s %s",
                attempt + 1,
                1 + retries,
                method,
                url,
            )
        except requests.exceptions.ConnectionError:
            logger.warning(
                "Connection error (attempt %d/%d): %s %s",
                attempt + 1,
                1 + retries,
                method,
                url,
            )

    logger.error("All request attempts exhausted for %s %s", method, url)
    return None


# =========================================================================
# Public API
# =========================================================================


def upload_facebook_reel(
    video_path: Path,
    title: str,
    description: str,
) -> str | None:
    """Upload a video as a Facebook Reel using the three-phase Reels API.

    Phases:
        1. **Start** — initialise the upload session and obtain a ``video_id``.
        2. **Upload** — stream the binary file to the resumable-upload endpoint.
        3. **Finish** — finalise the upload with metadata (title, description).

    Args:
        video_path: Absolute path to the video file.
        title: Reel title.
        description: Reel description / caption.

    Returns:
        The public Facebook post URL on success, or ``None`` on failure.
    """
    video_path = Path(video_path)

    # ------------------------------------------------------------------
    # Pre-flight checks
    # ------------------------------------------------------------------
    if not video_path.exists():
        logger.error("Video file does not exist: %s", video_path)
        return None

    file_size = video_path.stat().st_size
    if file_size == 0:
        logger.error("Video file is empty: %s", video_path)
        return None
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning(
            "Video file is large (%.2f GB). Upload may be slow or rejected.",
            file_size / (1024**3),
        )

    page_token = _get_page_token()
    if not page_token:
        return None

    page_id = get_facebook_page_id()
    base = _base_url()

    # ------------------------------------------------------------------
    # Phase 1 — Start
    # ------------------------------------------------------------------
    logger.info("Phase 1/3: Initializing Reel upload for page %s…", page_id)
    try:
        resp = _request_with_retry(
            "POST",
            f"{base}/{page_id}/video_reels",
            params={
                "upload_phase": "start",
                "access_token": page_token,
            },
        )
        if resp is None:
            return None

        if resp.status_code != 200:
            _handle_api_error(resp, "reel-start")
            return None

        start_data = resp.json()
        video_id: str = start_data.get("video_id", "")
        if not video_id:
            logger.error("No video_id returned from start phase: %s", start_data)
            return None

        logger.info("Start phase succeeded — video_id=%s", video_id)
    except Exception:
        logger.exception("Unexpected error during Reel start phase.")
        return None

    # ------------------------------------------------------------------
    # Phase 2 — Binary upload
    # ------------------------------------------------------------------
    logger.info("Phase 2/3: Uploading binary (%d bytes)…", file_size)
    try:
        with open(video_path, "rb") as fh:
            upload_resp = _request_with_retry(
                "POST",
                f"{RUPLOAD_BASE}/{video_id}",
                headers={
                    "Authorization": f"OAuth {page_token}",
                    "offset": "0",
                    "file_size": str(file_size),
                },
                data=fh,
                timeout=max(REQUEST_TIMEOUT, 300),  # generous for large files
            )

        if upload_resp is None:
            return None

        if upload_resp.status_code != 200:
            _handle_api_error(upload_resp, "reel-upload")
            return None

        logger.info("Binary upload succeeded.")
    except Exception:
        logger.exception("Unexpected error during binary upload phase.")
        return None

    # ------------------------------------------------------------------
    # Phase 3 — Finish
    # ------------------------------------------------------------------
    logger.info("Phase 3/3: Finishing Reel upload…")
    try:
        finish_resp = _request_with_retry(
            "POST",
            f"{base}/{page_id}/video_reels",
            params={
                "upload_phase": "finish",
                "video_id": video_id,
                "title": title,
                "description": description,
                "access_token": page_token,
            },
        )
        if finish_resp is None:
            return None

        if finish_resp.status_code != 200:
            _handle_api_error(finish_resp, "reel-finish")
            return None

        finish_data = finish_resp.json()
        post_id: str = finish_data.get("id") or finish_data.get("post_id", "")
        success: bool = finish_data.get("success", False)

        if not (post_id or success):
            logger.error("Finish phase did not confirm success: %s", finish_data)
            return None

        # Use video_id as fallback for URL if post_id is missing
        url_id = post_id or video_id
        facebook_url = f"https://www.facebook.com/{url_id}#video_id={video_id}"
        logger.info("Reel published successfully: %s", facebook_url)
        return facebook_url

    except Exception:
        logger.exception("Unexpected error during Reel finish phase.")
        return None


def get_upload_status(video_id: str) -> dict:
    """Query the processing / publish status of an uploaded video.

    Args:
        video_id: The Facebook video ID returned during upload.

    Returns:
        A dict with ``status`` and ``published`` fields, or an error dict.
    """
    page_token = _get_page_token()
    if not page_token:
        return {"error": "Could not obtain page access token."}

    resp = _request_with_retry(
        "GET",
        f"{_base_url()}/{video_id}",
        params={
            "fields": "status,published",
            "access_token": page_token,
        },
    )
    if resp is None:
        return {"error": "Request failed after retries."}

    try:
        data = resp.json()
    except ValueError:
        data = {"raw": resp.text}

    if resp.status_code != 200:
        _handle_api_error(resp, "get-status")

    return data


def delete_post(post_id: str) -> bool:
    """Delete a published Facebook post or video by its ID.

    Args:
        post_id: The Facebook post/video ID to delete.

    Returns:
        ``True`` if deletion succeeded, ``False`` otherwise.
    """
    page_token = _get_page_token()
    if not page_token:
        return False

    resp = _request_with_retry(
        "DELETE",
        f"{_base_url()}/{post_id}",
        params={"access_token": page_token},
    )
    if resp is None:
        return False

    if resp.status_code != 200:
        _handle_api_error(resp, "delete-post")
        return False

    data = resp.json()
    success = data.get("success", False)
    if success:
        logger.info("Post %s deleted successfully.", post_id)
    else:
        logger.warning("Deletion request returned success=false: %s", data)
    return bool(success)


# =========================================================================
# Pipeline entry point
# =========================================================================


def run() -> str | None:
    """Pipeline entry point — upload the final video as a Facebook Reel.

    Steps:
        1. Load metadata (title, description) from ``METADATA_FILE``.
        2. Upload the video at ``FINAL_VIDEO_FILE`` as a Reel.
        3. Update the database with the Facebook post ID and URL.

    Returns:
        The public Facebook URL on success, or ``None`` on failure.
    """
    logger.info("=== Facebook Upload — start ===")

    # Load metadata
    metadata = load_json(METADATA_FILE)
    if not metadata:
        logger.error("Failed to load metadata from %s", METADATA_FILE)
        return None

    title: str = metadata.get("title", "")
    description: str = metadata.get("description", "")

    if not title:
        logger.warning("Metadata has no title — using a default.")
        title = "New Video"

    # Upload
    facebook_url = upload_facebook_reel(FINAL_VIDEO_FILE, title, description)
    if not facebook_url:
        logger.error("Facebook Reel upload failed.")
        return None

    # Extract post/video ID from URL for database storage
    if "#video_id=" in facebook_url:
        facebook_id = facebook_url.split("#video_id=")[-1]
        facebook_url = facebook_url.split("#")[0]
    else:
        facebook_id = facebook_url.rstrip("/").rsplit("/", 1)[-1]

    # Update database
    try:
        # 1. Update central shortest_orbit_v3.db
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE videos
                   SET facebook_id  = ?,
                       facebook_url = ?,
                       status = 'uploaded',
                       uploaded_at = CURRENT_TIMESTAMP
                 WHERE id = (SELECT id FROM videos WHERE status = 'generating' ORDER BY id DESC LIMIT 1)
                """,
                (facebook_id, facebook_url),
            )
            conn.commit()
        finally:
            if conn:
                conn.close()
        logger.info(
            "Central database updated — facebook_id=%s, facebook_url=%s",
            facebook_id,
            facebook_url,
        )

        # 2. Update platform-specific facebook.db
        from automation.database.connection import get_facebook_conn
        fb_conn = None
        try:
            fb_conn = get_facebook_conn()
            fb_cursor = fb_conn.cursor()
            fb_cursor.execute(
                """
                UPDATE videos
                   SET facebook_id  = ?,
                       facebook_url = ?,
                       status = 'uploaded',
                       uploaded_at = CURRENT_TIMESTAMP
                 WHERE id = (SELECT id FROM videos WHERE status = 'generating' ORDER BY id DESC LIMIT 1)
                """,
                (facebook_id, facebook_url),
            )
            fb_conn.commit()
        finally:
            if fb_conn:
                fb_conn.close()
        logger.info(
            "Platform facebook.db updated — facebook_id=%s, facebook_url=%s",
            facebook_id,
            facebook_url,
        )

    except Exception:
        logger.exception("Failed to update database with Facebook info.")
        # Non-fatal — the upload itself succeeded.

    logger.info("=== Facebook Upload — done ===")
    return facebook_url


# =========================================================================
# Self-test (connectivity validation only)
# =========================================================================

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("  Facebook Upload -- Connectivity Self-Test")
    print("=" * 60)

    # 1. Load and validate credentials
    print("\n[1] Loading credentials...")
    try:
        creds = meta_auth.load_credentials()
        print("    [OK] Credentials loaded.")
    except Exception as exc:
        print(f"    [FAIL] Failed to load credentials: {exc}")
        sys.exit(1)

    # 2. Validate user token
    print("[2] Validating user access token...")
    user_token = meta_auth.get_valid_token()
    if user_token:
        print("    [OK] User token is valid.")
    else:
        print("    [FAIL] User token is invalid or expired.")
        sys.exit(1)

    # 3. Retrieve Page info
    page_id = get_facebook_page_id()
    print(f"[3] Configured Page ID: {page_id}")

    print("[4] Fetching Page name...")
    try:
        resp = requests.get(
            f"{_base_url()}/{page_id}",
            params={
                "fields": "name,id",
                "access_token": user_token,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            page_data = resp.json()
            print(f"    [OK] Page Name : {page_data.get('name', '(unknown)')}")
            print(f"    [OK] Page ID   : {page_data.get('id', page_id)}")
        else:
            print(f"    [FAIL] API returned {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:
        print(f"    [FAIL] Request failed: {exc}")

    # 4. Validate Page token
    print("[5] Obtaining Page Access Token...")
    page_token = meta_auth.get_page_access_token(user_token, page_id)
    if page_token:
        print("    [OK] Page Access Token obtained.")
    else:
        print("    [FAIL] Could not obtain Page Access Token.")

    print("\n" + "=" * 60)
    print("  Self-test complete -- NO uploads were performed.")
    print("=" * 60)
