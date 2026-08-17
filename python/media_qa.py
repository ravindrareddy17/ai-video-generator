import sys
from pathlib import Path
from typing import Tuple, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import get_logger
from utils.ffmpeg import get_video_info, get_duration

logger = get_logger(__name__)

def validate_media(video_path: Path) -> Tuple[bool, List[str]]:
    """Technical Media QA Validator for generated video files before publishing."""
    issues = []
    
    if not video_path.exists():
        return False, [f"Media file does not exist: {video_path}"]

    if video_path.stat().st_size == 0:
        return False, [f"Media file is 0 bytes: {video_path}"]

    try:
        duration = get_duration(video_path)
        if duration < 10.0 or duration > 60.0:
            issues.append(f"Invalid duration ({duration:.2f}s). Expected between 10.0s and 60.0s.")

        info = get_video_info(video_path)
        width = info.get("width", 0)
        height = info.get("height", 0)

        if width != 1080 or height != 1920:
            issues.append(f"Invalid resolution ({width}x{height}). Expected 1080x1920 for 9:16 Shorts.")

        codec = info.get("codec", "").lower()
        if codec and codec not in ["h264", "avc1"]:
            logger.warning(f"Video codec is '{codec}'. Standard H.264 is recommended.")

    except Exception as e:
        issues.append(f"Failed to extract FFmpeg media metadata: {e}")

    passed = len(issues) == 0
    if passed:
        logger.info(f"Technical Media QA PASSED for {video_path.name} (Duration: {duration:.2f}s, Resolution: 1080x1920).")
    else:
        logger.error(f"Technical Media QA FAILED for {video_path.name}. Issues: {issues}")

    return passed, issues

def run() -> bool:
    """Orchestrate Technical Media QA Step."""
    from utils.paths import FINAL_VIDEO_FILE
    logger.info("=== STEP: TECHNICAL MEDIA QA VALIDATION ===")
    passed, issues = validate_media(FINAL_VIDEO_FILE)
    return passed
