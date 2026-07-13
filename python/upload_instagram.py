"""
upload_instagram.py – Upload Reels to Instagram via the Meta Graph API.

Workflow
--------
1. Retrieve a valid Meta (Facebook / Instagram) access token.
2. Obtain a publicly-accessible video URL (YouTube or Facebook) from the
   most recent row in the `videos` database table.
3. Create a media container on Instagram (type = REELS).
4. Poll the container until processing finishes (or errors out).
5. Publish the container, making the Reel visible on the profile.
6. Record the resulting Instagram media ID and permalink back to the DB.

Instagram's Graph API does **not** accept direct file uploads for Reels –
the video must already be hosted at a public URL.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Project-level path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from utils.logger import get_logger
from utils.paths import FINAL_VIDEO_FILE, METADATA_FILE
from utils.helpers import load_json
from utils.database import get_connection
from utils.config import get_instagram_account_id, get_setting

import meta_auth
from meta_auth import get_valid_token, load_credentials

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GRAPH_API_BASE: str = "https://graph.facebook.com"
DEFAULT_API_VERSION: str = "v25.0"
DEFAULT_POLL_INTERVAL: int = 5        # seconds between status polls
DEFAULT_POLL_MAX_WAIT: int = 300      # max seconds to wait for processing
REQUEST_TIMEOUT: int = 60             # HTTP request timeout in seconds


def _api_version() -> str:
    """Return the Graph API version from env / settings, falling back to the default."""
    version: str = os.getenv(
        "META_API_VERSION",
        get_setting("meta", "graph_api_version", DEFAULT_API_VERSION),
    )
    return version


def _base_url() -> str:
    """Build the versioned Graph API base URL."""
    return f"{GRAPH_API_BASE}/{_api_version()}"


# ── 1. Create Media Container ────────────────────────────────────────────────

def create_media_container(
    ig_account_id: str,
    video_url: str,
    caption: str,
    access_token: str,
) -> str:
    """Create an Instagram Reels media container.

    Parameters
    ----------
    ig_account_id:
        The Instagram Business / Creator account ID.
    video_url:
        A publicly-accessible URL pointing to the video file.
    caption:
        The post caption (may include hashtags and mentions).
    access_token:
        A valid Meta user-access token with ``instagram_content_publish``
        permission.

    Returns
    -------
    str
        The ``creation_id`` (container ID) returned by the API.

    Raises
    ------
    RuntimeError
        If the API returns an error or the response is missing the expected
        ``id`` field.
    """
    url = f"{_base_url()}/{ig_account_id}/media"
    params: dict[str, str] = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token,
    }

    logger.info("Creating Instagram media container for account %s …", ig_account_id)
    logger.debug("video_url=%s", video_url)

    response = requests.post(url, params=params, timeout=REQUEST_TIMEOUT)
    data: dict = response.json()

    # ── Handle known error shapes ─────────────────────────────────────────
    if response.status_code == 429:
        raise RuntimeError(
            f"Instagram rate-limit hit (HTTP 429). "
            f"Details: {data.get('error', {}).get('message', 'N/A')}"
        )

    error_obj = data.get("error")
    if error_obj:
        code = error_obj.get("code", "")
        subcode = error_obj.get("error_subcode", "")
        message = error_obj.get("message", "Unknown error")

        # Expired / invalid token
        if code in (190,):
            raise RuntimeError(f"Access token expired or invalid: {message}")

        # Missing permissions
        if code in (10, 200) or subcode in (33,):
            raise RuntimeError(
                f"Insufficient permissions for Instagram publish: {message}"
            )

        # Invalid video format / URL
        if "video" in message.lower() or "url" in message.lower():
            raise RuntimeError(f"Invalid video or URL rejected by Instagram: {message}")

        raise RuntimeError(f"Instagram API error ({code}/{subcode}): {message}")

    response.raise_for_status()

    container_id: str | None = data.get("id")
    if not container_id:
        raise RuntimeError(f"No container ID in API response: {data}")

    logger.info("Media container created: %s", container_id)
    return container_id


# ── 2. Poll Container Status ─────────────────────────────────────────────────

def poll_container_status(
    container_id: str,
    access_token: str,
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL,
    poll_max_wait_seconds: int = DEFAULT_POLL_MAX_WAIT,
) -> str:
    """Poll the container until Instagram finishes processing the video.

    Parameters
    ----------
    container_id:
        The container / creation ID returned by :func:`create_media_container`.
    access_token:
        Valid Meta access token.
    poll_interval_seconds:
        Seconds between successive status checks.
    poll_max_wait_seconds:
        Maximum total seconds to wait before giving up.

    Returns
    -------
    str
        ``"FINISHED"`` when the video is ready, or ``"ERROR"`` if processing
        failed or timed out.
    """
    url = f"{_base_url()}/{container_id}"
    params: dict[str, str] = {
        "fields": "status_code",
        "access_token": access_token,
    }

    elapsed: int = 0
    attempt: int = 0

    while elapsed < poll_max_wait_seconds:
        attempt += 1
        logger.info(
            "Polling container %s – attempt %d (elapsed %ds / %ds) …",
            container_id,
            attempt,
            elapsed,
            poll_max_wait_seconds,
        )

        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            data: dict = response.json()
        except requests.RequestException as exc:
            logger.warning("Poll request failed: %s – will retry.", exc)
            time.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds
            continue

        status_code: str = data.get("status_code", "UNKNOWN").upper()
        logger.info("Container %s status: %s", container_id, status_code)

        if status_code == "FINISHED":
            return "FINISHED"

        if status_code == "ERROR":
            logger.error(
                "Instagram reported an error processing container %s: %s",
                container_id,
                data,
            )
            return "ERROR"

        # Still IN_PROGRESS (or unknown) – sleep then retry.
        time.sleep(poll_interval_seconds)
        elapsed += poll_interval_seconds

    logger.error(
        "Timed out waiting for container %s after %ds.", container_id, elapsed
    )
    return "ERROR"


# ── 3. Publish Container ─────────────────────────────────────────────────────

def publish_container(
    ig_account_id: str,
    container_id: str,
    access_token: str,
) -> str:
    """Publish a finished media container so it appears on the Instagram feed.

    Parameters
    ----------
    ig_account_id:
        Instagram Business / Creator account ID.
    container_id:
        The processed container ID.
    access_token:
        Valid Meta access token.

    Returns
    -------
    str
        The ``media_id`` of the newly published Reel.

    Raises
    ------
    RuntimeError
        On any API-level error.
    """
    url = f"{_base_url()}/{ig_account_id}/media_publish"
    params: dict[str, str] = {
        "creation_id": container_id,
        "access_token": access_token,
    }

    logger.info("Publishing container %s …", container_id)

    response = requests.post(url, params=params, timeout=REQUEST_TIMEOUT)
    data: dict = response.json()

    if response.status_code == 429:
        raise RuntimeError(
            f"Rate-limit hit while publishing (HTTP 429). "
            f"Details: {data.get('error', {}).get('message', 'N/A')}"
        )

    error_obj = data.get("error")
    if error_obj:
        code = error_obj.get("code", "")
        message = error_obj.get("message", "Unknown error")
        if code in (190,):
            raise RuntimeError(f"Access token expired or invalid: {message}")
        raise RuntimeError(f"Publish failed ({code}): {message}")

    response.raise_for_status()

    media_id: str | None = data.get("id")
    if not media_id:
        raise RuntimeError(f"No media ID in publish response: {data}")

    logger.info("Reel published – media_id=%s", media_id)
    return media_id


# ── 4. Get Upload Status ─────────────────────────────────────────────────────

def get_upload_status(media_id: str, access_token: str) -> dict:
    """Retrieve metadata for a published Instagram media object.

    Parameters
    ----------
    media_id:
        The media ID returned by :func:`publish_container`.
    access_token:
        Valid Meta access token.

    Returns
    -------
    dict
        Parsed JSON with keys such as ``id``, ``media_type``, ``permalink``,
        and ``timestamp``.
    """
    url = f"{_base_url()}/{media_id}"
    params: dict[str, str] = {
        "fields": "id,media_type,permalink,timestamp",
        "access_token": access_token,
    }

    logger.info("Fetching upload status for media %s …", media_id)
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    data: dict = response.json()
    logger.debug("Upload status response: %s", data)
    return data


# ── 5. Full Upload Workflow ───────────────────────────────────────────────────

def upload_instagram_reel(video_url: str, caption: str) -> str | None:
    """Execute the complete Instagram Reel upload workflow.

    1. Obtain a valid access token.
    2. Create a media container pointing at *video_url*.
    3. Poll until processing completes.
    4. Publish the Reel.
    5. Return the permalink (or ``None`` on failure).

    Parameters
    ----------
    video_url:
        Publicly-accessible URL to the video file.
    caption:
        Caption text (hashtags, mentions, etc.).

    Returns
    -------
    str | None
        The Instagram permalink URL, or ``None`` if any step failed.
    """
    try:
        # ── Token ─────────────────────────────────────────────────────────
        access_token: str = get_valid_token()
        if not access_token:
            logger.error("Could not obtain a valid Meta access token.")
            return None

        ig_account_id: str = get_instagram_account_id()
        if not ig_account_id:
            logger.error("Instagram account ID is not configured.")
            return None

        # ── Create container ──────────────────────────────────────────────
        container_id: str = create_media_container(
            ig_account_id, video_url, caption, access_token
        )

        # ── Poll ──────────────────────────────────────────────────────────
        poll_interval: int = int(
            get_setting("meta", "poll_interval_seconds", DEFAULT_POLL_INTERVAL)
        )
        poll_max_wait: int = int(
            get_setting("meta", "poll_max_wait_seconds", DEFAULT_POLL_MAX_WAIT)
        )

        status: str = poll_container_status(
            container_id,
            access_token,
            poll_interval_seconds=poll_interval,
            poll_max_wait_seconds=poll_max_wait,
        )

        if status != "FINISHED":
            logger.error(
                "Media processing did not finish successfully (status=%s).", status
            )
            return None

        # ── Publish ───────────────────────────────────────────────────────
        media_id: str = publish_container(ig_account_id, container_id, access_token)

        # ── Get permalink ─────────────────────────────────────────────────
        media_info: dict = get_upload_status(media_id, access_token)
        permalink: str | None = media_info.get("permalink")

        if permalink:
            logger.info("Instagram Reel live at %s", permalink)
        else:
            logger.warning(
                "Reel published (media_id=%s) but no permalink returned.", media_id
            )

        return permalink

    except RuntimeError as exc:
        logger.error("Instagram upload failed: %s", exc)
        return None
    except requests.ConnectionError as exc:
        logger.error("Network error during Instagram upload: %s", exc)
        return None
    except requests.Timeout as exc:
        logger.error("Request timed out during Instagram upload: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001 – non-fatal for pipeline
        logger.exception("Unexpected error during Instagram upload: %s", exc)
        return None


# ── 5b. Resumable Upload (direct binary) ─────────────────────────────────────

RUPLOAD_BASE: str = "https://rupload.facebook.com/ig-api-upload"


def create_resumable_container(
    ig_account_id: str,
    caption: str,
    access_token: str,
) -> str:
    """Create an Instagram Reels container for resumable (binary) upload.

    Unlike :func:`create_media_container`, this does **not** require a
    ``video_url``.  Instead the binary is uploaded separately via
    :func:`upload_video_binary`.

    Returns
    -------
    str
        The container / creation ID.
    """
    url = f"{_base_url()}/{ig_account_id}/media"
    params: dict[str, str] = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "access_token": access_token,
    }

    logger.info(
        "Creating resumable Instagram container for account %s …",
        ig_account_id,
    )

    response = requests.post(url, params=params, timeout=REQUEST_TIMEOUT)
    data: dict = response.json()

    error_obj = data.get("error")
    if error_obj:
        code = error_obj.get("code", "")
        subcode = error_obj.get("error_subcode", "")
        message = error_obj.get("message", "Unknown error")
        raise RuntimeError(
            f"Resumable container creation failed ({code}/{subcode}): {message}"
        )

    response.raise_for_status()

    container_id: str | None = data.get("id")
    if not container_id:
        raise RuntimeError(f"No container ID in resumable response: {data}")

    logger.info("Resumable container created: %s", container_id)
    return container_id


def upload_video_binary(
    container_id: str,
    video_path: Path,
    access_token: str,
) -> None:
    """Upload raw video bytes to Meta's resumable-upload endpoint.

    Parameters
    ----------
    container_id:
        The container ID returned by :func:`create_resumable_container`.
    video_path:
        Local path to the MP4 file.
    access_token:
        Valid Meta access token.

    Raises
    ------
    RuntimeError
        If the upload fails.
    """
    file_size = video_path.stat().st_size
    upload_url = f"{RUPLOAD_BASE}/{container_id}"

    logger.info(
        "Uploading binary (%d bytes) to %s …",
        file_size,
        upload_url,
    )

    with open(video_path, "rb") as fh:
        response = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {access_token}",
                "offset": "0",
                "file_size": str(file_size),
                "Content-Type": "video/mp4",
            },
            data=fh,
            timeout=300,  # large file – generous timeout
        )

    if response.status_code not in (200, 201):
        logger.error(
            "Binary upload failed: HTTP %d – %s",
            response.status_code,
            response.text,
        )
        raise RuntimeError(
            f"Binary upload to rupload failed (HTTP {response.status_code}): "
            f"{response.text[:500]}"
        )

    logger.info("Binary upload succeeded (HTTP %d).", response.status_code)


def upload_instagram_reel_local(video_path: Path, caption: str) -> str | None:
    """Upload a local video file as an Instagram Reel via resumable upload.

    This bypasses the need for a publicly-accessible video URL by uploading
    the binary directly to Meta's ``rupload.facebook.com`` endpoint.

    Parameters
    ----------
    video_path:
        Path to the local MP4 file.
    caption:
        Caption text (hashtags, mentions, etc.).

    Returns
    -------
    str | None
        The Instagram permalink URL, or ``None`` if any step failed.
    """
    try:
        if not video_path.exists():
            logger.error("Local video file not found: %s", video_path)
            return None

        # ── Token ─────────────────────────────────────────────────────────
        access_token: str = get_valid_token()
        if not access_token:
            logger.error("Could not obtain a valid Meta access token.")
            return None

        ig_account_id: str = get_instagram_account_id()
        if not ig_account_id:
            logger.error("Instagram account ID is not configured.")
            return None

        # ── Create resumable container ────────────────────────────────────
        container_id: str = create_resumable_container(
            ig_account_id, caption, access_token
        )

        # ── Upload binary ─────────────────────────────────────────────────
        upload_video_binary(container_id, video_path, access_token)

        # ── Poll ──────────────────────────────────────────────────────────
        poll_interval: int = int(
            get_setting("meta", "poll_interval_seconds", DEFAULT_POLL_INTERVAL)
        )
        poll_max_wait: int = int(
            get_setting("meta", "poll_max_wait_seconds", DEFAULT_POLL_MAX_WAIT)
        )

        status: str = poll_container_status(
            container_id,
            access_token,
            poll_interval_seconds=poll_interval,
            poll_max_wait_seconds=poll_max_wait,
        )

        if status != "FINISHED":
            logger.error(
                "Resumable media processing did not finish (status=%s).", status
            )
            return None

        # ── Publish ───────────────────────────────────────────────────────
        media_id: str = publish_container(ig_account_id, container_id, access_token)

        # ── Get permalink ─────────────────────────────────────────────────
        media_info: dict = get_upload_status(media_id, access_token)
        permalink: str | None = media_info.get("permalink")

        if permalink:
            logger.info("Instagram Reel live at %s (resumable upload)", permalink)
        else:
            logger.warning(
                "Reel published (media_id=%s) but no permalink returned.", media_id
            )

        return permalink

    except RuntimeError as exc:
        logger.error("Instagram resumable upload failed: %s", exc)
        return None
    except requests.ConnectionError as exc:
        logger.error("Network error during Instagram resumable upload: %s", exc)
        return None
    except requests.Timeout as exc:
        logger.error("Timeout during Instagram resumable upload: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error during Instagram resumable upload: %s", exc)
        return None


# ── 6. Pipeline Entry Point ──────────────────────────────────────────────────

def run() -> str | None:
    """Pipeline entry point – upload the latest video as an Instagram Reel.

    Steps
    -----
    1. Load metadata from :data:`METADATA_FILE`.
    2. Query the most recent row in the ``videos`` table for a YouTube or
       Facebook video URL.
    3. Build the caption from metadata ``title``, ``description``, and
       ``hashtags``.
    4. Call :func:`upload_instagram_reel`.
    5. Update the database row with the resulting Instagram media ID and URL.

    Returns
    -------
    str | None
        The Instagram permalink, or ``None`` if the upload was skipped or
        failed.
    """
    try:
        # ── Metadata ──────────────────────────────────────────────────────
        metadata: dict = load_json(str(METADATA_FILE))
        if not metadata:
            logger.warning("No metadata found at %s – skipping Instagram upload.", METADATA_FILE)
            return None

        title: str = metadata.get("title", "")
        description: str = metadata.get("description", "")
        hashtags: str = metadata.get("hashtags", "")

        # ── Video URL from database ───────────────────────────────────────
        video_url: str | None = None
        video_row_id: int | None = None

        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, youtube_id, facebook_url, facebook_id FROM videos "
                "ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        if row is None:
            logger.warning("No video rows in database – cannot determine video URL.")
            return None

        video_row_id = row[0]
        youtube_id: str | None = row[1] if len(row) > 1 else None
        facebook_url: str | None = row[2] if len(row) > 2 else None
        facebook_id: str | None = row[3] if len(row) > 3 else None

        # Try to resolve direct Facebook video source CDN URL
        facebook_source_url = None
        if facebook_id:
            try:
                user_token = get_valid_token()
                if user_token:
                    from utils.config import get_facebook_page_id
                    page_id = get_facebook_page_id()
                    page_token = meta_auth.get_page_access_token(user_token, page_id)
                    if page_token:
                        version = _api_version()
                        # Poll for source URL (up to 6 attempts, 5s interval)
                        for attempt in range(1, 7):
                            resp = requests.get(
                                f"{GRAPH_API_BASE}/{version}/{facebook_id}",
                                params={"fields": "source,status", "access_token": page_token},
                                timeout=15,
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                fb_source = data.get("source")
                                video_status = data.get("status", {}).get("video_status")
                                if fb_source:
                                    facebook_source_url = fb_source
                                    logger.info(
                                        "Retrieved direct Facebook video source URL (attempt %d): %s",
                                        attempt,
                                        facebook_source_url,
                                    )
                                    break
                                else:
                                    logger.info(
                                        "Facebook source URL not ready yet (status=%s) – retrying in 5s...",
                                        video_status,
                                    )
                            else:
                                logger.warning(
                                    "Failed to query Facebook video (attempt %d): HTTP %d: %s",
                                    attempt,
                                    resp.status_code,
                                    resp.text,
                                )
                            time.sleep(5)
            except Exception as e:
                logger.warning("Could not retrieve Facebook video source URL: %s", e)

        if facebook_source_url:
            video_url = facebook_source_url
            logger.info("Using direct Facebook source CDN URL for Instagram: %s", video_url)
        elif youtube_id:
            video_url = f"https://www.youtube.com/watch?v={youtube_id}"
            logger.info("Using YouTube watch URL fallback for Instagram: %s", video_url)
        elif facebook_url:
            video_url = facebook_url
            logger.info("Using Facebook post URL fallback for Instagram: %s", video_url)
        else:
            logger.warning(
                "No YouTube, Facebook source, or Facebook post URL available for video row %d – "
                "skipping Instagram upload.",
                video_row_id,
            )
            return None

        # ── Caption ───────────────────────────────────────────────────────
        def clean_part(part) -> str:
            if part is None:
                return ""
            if isinstance(part, list):
                return " ".join(str(item) for item in part if item is not None).strip()
            return str(part).strip()

        caption_parts: list[str] = []
        for p in [title, description, hashtags]:
            cleaned = clean_part(p)
            if cleaned:
                caption_parts.append(cleaned)

        caption: str = "\n\n".join(caption_parts) if caption_parts else "New Reel"

        # ── Upload (prefer local file via resumable upload) ────────────
        permalink: str | None = None

        if FINAL_VIDEO_FILE.exists():
            logger.info(
                "Local video file found (%s) – using resumable upload.",
                FINAL_VIDEO_FILE,
            )
            permalink = upload_instagram_reel_local(FINAL_VIDEO_FILE, caption)

        if not permalink:
            if FINAL_VIDEO_FILE.exists():
                logger.warning(
                    "Resumable upload failed – falling back to URL-based upload."
                )
            permalink = upload_instagram_reel(video_url, caption)

        # ── Update database ───────────────────────────────────────────────
        if permalink:
            try:
                # 1. Update central shortest_orbit_v3.db
                conn = None
                ig_media_id = permalink.rstrip("/").split("/")[-1]
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        UPDATE videos 
                        SET instagram_url = ?, instagram_id = ?, status = 'uploaded', uploaded_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (permalink, ig_media_id, video_row_id),
                    )
                    conn.commit()
                finally:
                    if conn:
                        conn.close()
                logger.info(
                    "Central database updated – instagram_url=%s for row %d.",
                    permalink,
                    video_row_id,
                )

                # 2. Update platform-specific instagram.db
                from automation.database.connection import get_instagram_conn
                ig_conn = None
                try:
                    ig_conn = get_instagram_conn()
                    ig_cursor = ig_conn.cursor()
                    ig_cursor.execute(
                        """
                        UPDATE videos
                        SET instagram_url = ?, instagram_id = ?, status = 'uploaded', uploaded_at = CURRENT_TIMESTAMP
                        WHERE id = (SELECT id FROM videos ORDER BY id DESC LIMIT 1)
                        """,
                        (permalink, ig_media_id),
                    )
                    ig_conn.commit()
                finally:
                    if ig_conn:
                        ig_conn.close()
                logger.info(
                    "Platform instagram.db updated – instagram_url=%s",
                    permalink,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to update database with Instagram info: %s", exc)

        return permalink

    except Exception as exc:  # noqa: BLE001 – non-fatal for pipeline
        logger.exception("Instagram run() failed: %s", exc)
        return None


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("  Instagram Upload Module -- Self-Test")
    print("=" * 60)

    # Load and validate credentials
    try:
        creds = load_credentials()
        print(f"\n[OK] Credentials loaded (app_id present: {'app_id' in creds})")
    except Exception as exc:
        print(f"\n[FAIL] Failed to load credentials: {exc}")
        sys.exit(1)

    # Obtain a valid token
    try:
        token = get_valid_token()
        if token:
            print(f"[OK] Access token obtained (length={len(token)})")
        else:
            print("[FAIL] Could not obtain a valid access token.")
            sys.exit(1)
    except Exception as exc:
        print(f"[FAIL] Token retrieval error: {exc}")
        sys.exit(1)

    # Fetch and display Instagram account info
    try:
        ig_id = get_instagram_account_id()
        if not ig_id:
            print("[FAIL] Instagram account ID not configured.")
            sys.exit(1)

        print(f"[OK] Instagram Account ID: {ig_id}")

        info_url = f"{_base_url()}/{ig_id}"
        info_params: dict[str, str] = {
            "fields": "name,username,profile_picture_url",
            "access_token": token,
        }
        resp = requests.get(info_url, params=info_params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        info: dict = resp.json()

        print(f"\n  Name              : {info.get('name', 'N/A')}")
        print(f"  Username          : {info.get('username', 'N/A')}")
        print(f"  Profile Picture   : {info.get('profile_picture_url', 'N/A')}")

    except Exception as exc:
        print(f"\n[FAIL] Could not fetch account info: {exc}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Self-test complete -- no uploads performed.")
    print("=" * 60)
