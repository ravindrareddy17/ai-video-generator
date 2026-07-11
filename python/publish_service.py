"""
publish_service.py – Multi-platform publishing orchestrator.

Coordinates uploads to YouTube, Facebook, and Instagram,
tracks per-platform results, and persists outcomes to both
the database and a JSON artefact.
"""

import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import get_logger
from utils.paths import FINAL_VIDEO_FILE, THUMBNAIL_FILE, METADATA_FILE
from utils.helpers import load_json
from utils.database import get_connection
from utils.config import get_setting

import upload_youtube
import upload_facebook
import upload_instagram

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PublishResult:
    """Aggregated result across all publishing platforms."""

    youtube_url: str | None = None
    facebook_url: str | None = None
    instagram_url: str | None = None
    status: str = "pending"  # 'success', 'partial', 'failed'
    upload_time: float = 0.0
    errors: list[str] = field(default_factory=list)
    platforms_published: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Platform dispatcher
# ---------------------------------------------------------------------------

_PLATFORM_MAP: dict[str, tuple[str, object]] = {
    "youtube":   ("youtube_url",   upload_youtube),
    "facebook":  ("facebook_url",  upload_facebook),
    "instagram": ("instagram_url", upload_instagram),
}


def publish_everywhere() -> PublishResult:
    """Upload the final video to every enabled platform.

    Reads ``publish.platforms`` from *settings.json* to decide which
    platforms are active.  Each upload is wrapped in its own
    ``try / except`` so that a single failure does not necessarily
    block the remaining platforms (controlled by the
    ``publish.continue_on_failure`` setting).

    Returns
    -------
    PublishResult
        Dataclass summarising URLs, timing, errors, and overall status.
    """

    enabled: list[str] = get_setting("publish", "platforms", ["youtube", "facebook", "instagram"])
    continue_on_failure: bool = get_setting("publish", "continue_on_failure", True)

    logger.info("Publishing to platforms: %s", enabled)

    result = PublishResult()
    start = time.time()

    for platform in enabled:
        if platform not in _PLATFORM_MAP:
            msg = f"Unknown platform '{platform}' – skipping"
            logger.warning(msg)
            result.errors.append(msg)
            continue

        url_attr, module = _PLATFORM_MAP[platform]

        try:
            logger.info("Uploading to %s …", platform)
            url: str | None = module.run()

            if url:
                setattr(result, url_attr, url)
                result.platforms_published.append(platform)
                logger.info("%s upload succeeded: %s", platform.capitalize(), url)
            else:
                msg = f"{platform.capitalize()} upload returned no URL"
                logger.warning(msg)
                result.errors.append(msg)

        except Exception as exc:
            msg = f"{platform.capitalize()} upload failed: {exc}"
            logger.error(msg, exc_info=True)
            result.errors.append(msg)

            if not continue_on_failure:
                logger.warning("continue_on_failure is False – aborting remaining uploads")
                break

    result.upload_time = round(time.time() - start, 2)

    # --- Determine overall status ----------------------------------------
    total_enabled = len([p for p in enabled if p in _PLATFORM_MAP])
    succeeded = len(result.platforms_published)

    if succeeded == total_enabled and total_enabled > 0:
        result.status = "success"
    elif succeeded > 0:
        result.status = "partial"
    else:
        result.status = "failed"

    # --- Persist to database ---------------------------------------------
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE videos SET platforms_published = ? WHERE rowid = (SELECT MAX(rowid) FROM videos)",
            (json.dumps(result.platforms_published),),
        )
        conn.commit()
        logger.info("Database updated with platforms_published: %s", result.platforms_published)
    except Exception as exc:
        logger.error("Failed to update database: %s", exc, exc_info=True)
        result.errors.append(f"Database update failed: {exc}")
    finally:
        if conn:
            conn.close()

    return result


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_publish_result(result: PublishResult) -> None:
    """Serialise *result* to ``data/publish_result.json``.

    The output includes all URLs, the overall status, any errors
    that occurred, and a human-readable timestamp.
    """

    output_path = Path(__file__).resolve().parent.parent / "data" / "publish_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict = {
        "youtube_url": result.youtube_url,
        "facebook_url": result.facebook_url,
        "instagram_url": result.instagram_url,
        "status": result.status,
        "upload_time": result.upload_time,
        "errors": result.errors,
        "platforms_published": result.platforms_published,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Publish result saved to %s", output_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run() -> PublishResult:
    """High-level entry point: publish → persist → summarise."""

    logger.info("=== Publish Service started ===")

    result = publish_everywhere()
    save_publish_result(result)

    # --- Log a human-friendly summary ------------------------------------
    logger.info("--- Publish Summary ---")
    logger.info("Status        : %s", result.status)
    logger.info("Upload time   : %.2f s", result.upload_time)
    logger.info("Platforms     : %s", ", ".join(result.platforms_published) or "(none)")

    if result.youtube_url:
        logger.info("YouTube URL   : %s", result.youtube_url)
    if result.facebook_url:
        logger.info("Facebook URL  : %s", result.facebook_url)
    if result.instagram_url:
        logger.info("Instagram URL : %s", result.instagram_url)

    if result.errors:
        logger.warning("Errors        : %s", "; ".join(result.errors))

    logger.info("=== Publish Service finished ===")
    return result


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    platforms = get_setting("publish", "platforms", ["youtube", "facebook", "instagram"])
    print(f"Configured platforms: {platforms}")
    print("Ready to publish")
