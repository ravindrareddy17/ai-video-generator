"""
paths.py — Centralised path definitions for AI Video Generator V2.

All project directories and key file paths are defined here using pathlib.Path.
Directories are auto-created on import via ensure_directories().
"""

from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Project root (parent of the utils/ directory)
# ──────────────────────────────────────────────
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────
# Top-level directories
# ──────────────────────────────────────────────
DATA_DIR: Path = PROJECT_ROOT / "data"
AUDIO_DIR: Path = PROJECT_ROOT / "audio"
CAPTIONS_DIR: Path = PROJECT_ROOT / "captions"
OUTPUT_DIR: Path = PROJECT_ROOT / "output"
DOWNLOADS_DIR: Path = PROJECT_ROOT / "downloads"
TEMP_DIR: Path = PROJECT_ROOT / "temp"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
ASSETS_DIR: Path = PROJECT_ROOT / "assets"
CONFIG_DIR: Path = PROJECT_ROOT / "config"

# ──────────────────────────────────────────────
# Sub-directories
# ──────────────────────────────────────────────
DOWNLOADS_VIDEOS_DIR: Path = DOWNLOADS_DIR / "videos"
DOWNLOADS_IMAGES_DIR: Path = DOWNLOADS_DIR / "images"
MUSIC_DIR: Path = ASSETS_DIR / "music"
FONTS_DIR: Path = ASSETS_DIR / "fonts"
LOGOS_DIR: Path = ASSETS_DIR / "logos"
OVERLAYS_DIR: Path = ASSETS_DIR / "overlays"

# ──────────────────────────────────────────────
# File paths
# ──────────────────────────────────────────────
ENV_FILE: Path = PROJECT_ROOT / ".env"
SETTINGS_FILE: Path = CONFIG_DIR / "settings.json"

VIRAL_TOPICS_FILE: Path = DATA_DIR / "viral_topics.json"
CONTENT_FILE: Path = DATA_DIR / "content.json"
METADATA_FILE: Path = DATA_DIR / "metadata.json"
SEARCH_QUERIES_FILE: Path = DATA_DIR / "search_queries.json"

VOICE_FILE: Path = AUDIO_DIR / "voice.mp3"
WORD_TIMINGS_FILE: Path = AUDIO_DIR / "word_timings.json"

SUBTITLES_FILE: Path = CAPTIONS_DIR / "voice.srt"

SILENT_VIDEO_FILE: Path = TEMP_DIR / "video.mp4"
VIDEO_AUDIO_FILE: Path = TEMP_DIR / "video_audio.mp4"

FINAL_VIDEO_FILE: Path = OUTPUT_DIR / "short.mp4"
THUMBNAIL_FILE: Path = OUTPUT_DIR / "thumbnail.png"

CLIENT_SECRET_FILE: Path = PROJECT_ROOT / "client_secret.json"
TOKEN_FILE: Path = PROJECT_ROOT / "token.pickle"

# ──────────────────────────────────────────────
# All directories that must exist at runtime
# ──────────────────────────────────────────────
_ALL_DIRS: list[Path] = [
    DATA_DIR,
    AUDIO_DIR,
    CAPTIONS_DIR,
    OUTPUT_DIR,
    DOWNLOADS_DIR,
    DOWNLOADS_VIDEOS_DIR,
    DOWNLOADS_IMAGES_DIR,
    TEMP_DIR,
    LOGS_DIR,
    ASSETS_DIR,
    MUSIC_DIR,
    FONTS_DIR,
    LOGOS_DIR,
    OVERLAYS_DIR,
    CONFIG_DIR,
]


def ensure_directories() -> None:
    """Create every project directory if it does not already exist."""
    for directory in _ALL_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
    logger.debug("All project directories verified/created.")


# Auto-create directories on first import
ensure_directories()


# ──────────────────────────────────────────────
# Self-test
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    print("=" * 60)
    print("  AI Video Generator V2 — Path Definitions")
    print("=" * 60)

    # Collect every Path constant defined in this module
    path_vars: dict[str, Path] = {
        name: value
        for name, value in globals().items()
        if isinstance(value, Path) and not name.startswith("_")
    }

    max_name_len = max(len(n) for n in path_vars)
    for name, path in path_vars.items():
        exists_marker = "[OK]" if path.exists() else "[--]"
        print(f"  {exists_marker}  {name:<{max_name_len}}  ->  {path}")

    print("=" * 60)
    print(f"  Total paths defined: {len(path_vars)}")
    print(f"  Total directories:   {len(_ALL_DIRS)}")
    print("=" * 60)
