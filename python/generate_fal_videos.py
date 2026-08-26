"""
generate_fal_videos.py — Ultra-Realistic AI Video Generator via Fal.ai API.

Generates 100% pure cinematic AI video clips using cutting-edge models:
- Minimax Hailuo AI (fal-ai/minimax-video/text-to-video)
- Kling 1.5 (fal-ai/kling-video/v1.5/pro/text-to-video)
- Luma Dream Machine (fal-ai/luma-dream-machine)
- Hunyuan Video / CogVideoX

Outputs:
    downloads/videos/scene_{index}.mp4 (1080x1920 30fps fluid video)
"""

import sys
import os
import requests
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import TEMP_DIR, DOWNLOADS_VIDEOS_DIR, SEARCH_QUERIES_FILE, ENV_FILE
from utils.logger import get_logger
from utils.helpers import load_json
from dotenv import load_dotenv

load_dotenv(ENV_FILE)
logger = get_logger(__name__)


def generate_fal_ai_video_clip(prompt: str, output_path: Path, duration: float = 5.0, scene_index: int = 1) -> Path:
    """Calls Fal.ai Minimax / Kling text-to-video to generate a full cinematic AI video."""
    fal_key = os.getenv("FAL_KEY") or os.getenv("FAL_API_KEY")
    if not fal_key:
        raise ValueError("FAL_KEY is missing from environment variables.")

    import fal_client
    os.environ["FAL_KEY"] = fal_key

    logger.info(f"Generating Hollywood-Grade AI Video on Fal.ai for Scene {scene_index}: '{prompt[:60]}...'")
    
    # Enhanced cinematic vertical prompt
    enhanced_prompt = (
        f"{prompt}, ultra-realistic 4K documentary footage, cinematic lighting, volumetric atmosphere, "
        "fluid motion, photorealistic rendering, 9:16 vertical cinema camera"
    )
    
    # Try Minimax Video-01 first, then Kling, then Luma
    models = [
        ("fal-ai/minimax-video/text-to-video", {"prompt": enhanced_prompt, "prompt_optimizer": True}),
        ("fal-ai/kling-video/v1.5/pro/text-to-video", {"prompt": enhanced_prompt, "aspect_ratio": "9:16", "duration": "5"}),
        ("fal-ai/luma-dream-machine", {"prompt": enhanced_prompt, "aspect_ratio": "9:16"}),
        ("fal-ai/hunyuan-video", {"prompt": enhanced_prompt, "aspect_ratio": "9:16"})
    ]

    for model_id, arguments in models:
        try:
            logger.info(f"Attempting video generation with model '{model_id}'...")
            handler = fal_client.submit(model_id, arguments=arguments)
            result = handler.get()
            
            video_url = None
            if isinstance(result, dict):
                video_url = result.get("video", {}).get("url") or result.get("url")
                
            if video_url:
                logger.info(f"Video generated! Downloading from URL: {video_url} -> {output_path}")
                r = requests.get(video_url, stream=True, timeout=60)
                if r.status_code == 200:
                    with open(output_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    logger.info(f"Successfully saved Fal.ai video clip: {output_path} ({output_path.stat().st_size} bytes)")
                    return output_path
        except Exception as me:
            logger.warning(f"Model '{model_id}' generation failed: {me}. Trying next model...")

    raise RuntimeError(f"All Fal.ai video generation models failed for Scene {scene_index}.")


def generate_single_scene(prompt: str, output_path: Path, duration: float = 4.0, scene_index: int = 1) -> Path:
    """Single scene wrapper for multi_style_generator."""
    return generate_fal_ai_video_clip(prompt, output_path, duration=duration, scene_index=scene_index)
