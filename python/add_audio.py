"""
add_audio.py — Step 8 of the AI Video Generator V2 pipeline.

Mixes the generated voiceover audio (100% volume) and a selected background
music track (10% volume, looped) onto the silent compiled video.

Inputs:
    temp/video.mp4
    audio/voice.mp3
    assets/music/ (directory containing background music .mp3s)

Outputs:
    temp/video_audio.mp4
"""

import sys
from pathlib import Path
import random

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import SILENT_VIDEO_FILE, VOICE_FILE, VIDEO_AUDIO_FILE, MUSIC_DIR
from utils.config import get_setting
from utils.logger import get_logger
from utils.ffmpeg import mix_audio, _run_ffmpeg, get_duration

logger = get_logger(__name__)


def select_background_music() -> Path | None:
    """Select a random background music file from assets/music/."""
    if not MUSIC_DIR.exists():
        logger.warning(f"Background music directory does not exist at {MUSIC_DIR}")
        return None
        
    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    if not music_files:
        logger.warning(f"No audio files (.mp3 or .wav) found in background music directory: {MUSIC_DIR}")
        return None
        
    selected = random.choice(music_files)
    logger.info(f"Selected background music: {selected.name}")
    return selected


def mix_voice_only(video_path: Path, voice_path: Path, output_path: Path, voice_vol: float = 1.0) -> Path:
    """Fallback function: mix only the voiceover track onto the video (no music)."""
    logger.info(f"Fallback: Mixing ONLY voiceover {voice_path.name} onto video (no background music)...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run FFmpeg to map video and voice audio directly
    # Adjust volume of the voice input
    filter_complex = f"[1:a]volume={voice_vol}[v_audio]"
    
    _run_ffmpeg([
        "-i", str(video_path),
        "-i", str(voice_path),
        "-filter_complex", filter_complex,
        "-map", "0:v:0",
        "-map", "[v_audio]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path)
    ])
    logger.info(f"Voice-only mixed video saved to {output_path.name}")
    return output_path


def run() -> Path:
    """Orchestrates Step 8 of the pipeline."""
    logger.info("=== STEP 8: ADD AUDIO ===")
    
    # 1. Validate inputs
    if not SILENT_VIDEO_FILE.exists():
        raise FileNotFoundError(f"Silent video not found at {SILENT_VIDEO_FILE}. Run Step 7 first.")
    if not VOICE_FILE.exists():
        raise FileNotFoundError(f"Voiceover audio not found at {VOICE_FILE}. Run Step 3 first.")
        
    voice_volume = get_setting('audio', 'voice_volume', 1.0)
    music_volume = get_setting('audio', 'music_volume', 0.1)
    
    # 2. Select background music
    music_file = select_background_music()
    
    # 3. Mix audio
    if music_file:
        try:
            mix_audio(
                video_path=SILENT_VIDEO_FILE,
                voice_path=VOICE_FILE,
                music_path=music_file,
                output_path=VIDEO_AUDIO_FILE,
                voice_vol=voice_volume,
                music_vol=music_volume
            )
            logger.info(f"Audio mixing completed successfully: {VIDEO_AUDIO_FILE}")
        except Exception as e:
            logger.error(f"Failed mixing background music: {e}. Trying voice-only fallback...")
            mix_voice_only(SILENT_VIDEO_FILE, VOICE_FILE, VIDEO_AUDIO_FILE, voice_volume)
    else:
        logger.info("No background music track selected. Mixing voice-only.")
        mix_voice_only(SILENT_VIDEO_FILE, VOICE_FILE, VIDEO_AUDIO_FILE, voice_volume)
        
    return VIDEO_AUDIO_FILE


if __name__ == "__main__":
    try:
        out_path = run()
        print(f"Audio addition complete. File saved at: {out_path}")
    except Exception as exc:
        logger.exception("add_audio module execution failed")
        sys.exit(1)
