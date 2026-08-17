"""
create_video.py — Step 7 of the AI Video Generator V2 pipeline.

Trims, loops, scales, and crops each scene's stock video to fit its corresponding
subtitle segment duration, and outputs a single combined silent vertical video.

Inputs:
    captions/voice.srt
    downloads/videos/scene_{index}.mp4

Outputs:
    temp/video.mp4 (1080x1920 vertical, no audio)
"""

import sys
from pathlib import Path
import json

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import SUBTITLES_FILE, SILENT_VIDEO_FILE, TEMP_DIR, DOWNLOADS_VIDEOS_DIR, SEARCH_QUERIES_FILE
from utils.logger import get_logger
from utils.helpers import clean_directory, load_json
from utils.ffmpeg import get_duration, get_video_info, concat_videos, _run_ffmpeg

logger = get_logger(__name__)

def process_scene(scene_index: int, input_path: Path, target_duration: float, temp_scene_dir: Path) -> Path:
    """Scale, crop, and loop/trim a single stock video to match the target subtitle duration."""
    output_path = temp_scene_dir / f"processed_scene_{scene_index}.mp4"
    logger.info(f"Processing scene {scene_index} ({input_path.name}) -> target duration: {target_duration}s")
    
    # 1. Get info on the input video
    try:
        video_info = get_video_info(input_path)
        clip_duration = video_info.get("duration", 0.0)
        logger.debug(f"Input clip duration: {clip_duration}s, resolution: {video_info.get('width')}x{video_info.get('height')}")
    except Exception as e:
        logger.error(f"Failed to get video info for {input_path.name}: {e}. Assuming duration 5.0.")
        clip_duration = 5.0
        
    # 2. Build the FFmpeg command
    # Filter to scale to cover 1080x1920, crop to center 1080x1920, and set output framerate to 30 fps
    vf_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30"
    
    # If the clip is shorter than the target duration, loop it.
    # Otherwise, just trim it to the target duration.
    # We can do this efficiently by using stream_loop if looping, or simple -t if trimming.
    args = []
    
    if clip_duration < target_duration:
        # Seamless motion looping to ensure video NEVER freezes motionless
        logger.info(f"Clip ({clip_duration}s) is shorter than target ({target_duration}s). Looping clip for fluid motion.")
        args.extend(["-stream_loop", "-1"])
        
    args.extend(["-i", str(input_path)])
    
    # Apply filters, select video encoder, set bitrate, set target duration, and format
    args.extend([
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-t", str(target_duration),
        "-an",  # remove audio track from clip
        str(output_path)
    ])
    
    _run_ffmpeg(args)
    logger.info(f"Successfully processed scene {scene_index}. File size: {output_path.stat().st_size} bytes")
    return output_path


def run() -> Path:
    """Orchestrates Step 7 of the pipeline."""
    logger.info("=== STEP 7: CREATE SILENT VIDEO ===")
    
    # 1. Validate inputs
    if not SEARCH_QUERIES_FILE.exists():
        raise FileNotFoundError(f"Search queries file not found at {SEARCH_QUERIES_FILE}. Run Step 5 first.")
        
    # Parse scenes from search_queries to get timing and duration for each stock video
    scenes = load_json(SEARCH_QUERIES_FILE)
    if not scenes:
        raise ValueError("No scenes found in search queries.")
        
    # Create temp directory for processed scene files
    temp_scene_dir = TEMP_DIR / "scenes"
    temp_scene_dir.mkdir(parents=True, exist_ok=True)
    clean_directory(temp_scene_dir)
    
    processed_scenes = []
    
    # 2. Process each scene
    for sub in scenes:
        idx = sub["subtitle_index"]
        target_dur = sub["duration_s"]
        
        # Downloaded file name should match the scene index
        input_video = DOWNLOADS_VIDEOS_DIR / f"scene_{idx}.mp4"
        if not input_video.exists():
            logger.warning(f"Stock video for scene {idx} not found at {input_video}. Finding any scene to copy.")
            # Fallback: find any file in DOWNLOADS_VIDEOS_DIR
            existing_clips = list(DOWNLOADS_VIDEOS_DIR.glob("scene_*.mp4"))
            if existing_clips:
                input_video = existing_clips[0]
                logger.warning(f"Fallback: Using {input_video.name} for scene {idx}")
            else:
                raise FileNotFoundError(f"No stock video files found in {DOWNLOADS_VIDEOS_DIR}.")
                
        processed_clip = process_scene(idx, input_video, target_dur, temp_scene_dir)
        processed_scenes.append(processed_clip)
        
    # 3. Concatenate all processed scenes into a single silent video file
    logger.info(f"Concatenating {len(processed_scenes)} processed scenes into final silent video: {SILENT_VIDEO_FILE}")
    try:
        concat_videos(processed_scenes, SILENT_VIDEO_FILE)
        logger.info(f"Silent video successfully assembled at: {SILENT_VIDEO_FILE}")
    except Exception as e:
        logger.error(f"Failed to concatenate videos: {e}")
        raise
        
    # Clean up scene temporary files
    try:
        clean_directory(temp_scene_dir)
        temp_scene_dir.rmdir()
        logger.debug("Cleaned up temporary scenes directory.")
    except Exception as e:
        logger.warning(f"Could not clean up temporary scenes directory: {e}")
        
    return SILENT_VIDEO_FILE


if __name__ == "__main__":
    try:
        out_path = run()
        print(f"Silent video creation complete. File saved at: {out_path}")
    except Exception as exc:
        logger.exception("create_video module execution failed")
        sys.exit(1)
