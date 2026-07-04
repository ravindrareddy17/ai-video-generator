"""
burn_subtitles.py — Step 9 of the AI Video Generator V2 pipeline.

Burns the SRT subtitle captions into the video. Custom subtitle styling
(font, size, margin, color, outline) is loaded from config.

Inputs:
    temp/video_audio.mp4
    captions/voice.srt

Outputs:
    output/short.mp4
"""

import sys
from pathlib import Path

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import VIDEO_AUDIO_FILE, SUBTITLES_FILE, FINAL_VIDEO_FILE, FONTS_DIR
from utils.config import get_setting
from utils.logger import get_logger
from utils.ffmpeg import burn_subtitles

logger = get_logger(__name__)


def run() -> Path:
    """Orchestrates Step 9 of the pipeline."""
    logger.info("=== STEP 9: BURN SUBTITLES ===")
    
    # Validate inputs
    if not VIDEO_AUDIO_FILE.exists():
        raise FileNotFoundError(f"Source video with audio not found at {VIDEO_AUDIO_FILE}. Run Step 8 first.")
    if not SUBTITLES_FILE.exists():
        raise FileNotFoundError(f"Subtitles SRT file not found at {SUBTITLES_FILE}. Run Step 4 first.")
        
    # Load subtitle styling configurations
    font_name = get_setting('subtitles', 'font', 'Cinzel')
    font_size = get_setting('subtitles', 'fontsize', 24)
    margin_v = get_setting('subtitles', 'margin_vertical', 60)
    back_color = get_setting('subtitles', 'back_color', '&H80800000')
    
    logger.info(f"Burning subtitles. Font: '{font_name}', Size: {font_size}, BackColor: {back_color}")
    
    try:
        burn_subtitles(
            video_path=VIDEO_AUDIO_FILE,
            srt_path=SUBTITLES_FILE,
            output_path=FINAL_VIDEO_FILE,
            font_name=font_name,
            font_size=font_size,
            margin_v=margin_v,
            fonts_dir=FONTS_DIR,
            back_color=back_color,
        )
        logger.info(f"Subtitles burned successfully. Final output saved to: {FINAL_VIDEO_FILE}")
    except Exception as e:
        logger.error(f"Failed to burn subtitles: {e}")
        raise
        
    return FINAL_VIDEO_FILE


if __name__ == "__main__":
    try:
        out_path = run()
        print(f"Subtitle burning complete. File saved at: {out_path}")
    except Exception as exc:
        logger.exception("burn_subtitles module execution failed")
        sys.exit(1)
