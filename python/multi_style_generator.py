"""
multi_style_generator.py — Tri-Modal Visual Scene Generator.

Orchestrates per-scene rendering across the 3 visual styles:
1. 'doodle'     -> Authentic Hand-Drawn Whiteboard Doodle Art (generate_whiteboard)
2. 'cinematic'  -> Ultra-Realistic 4K Cinematic AI / Stock Footage (download_videos)
3. 'map_motion' -> 3D Maps & Motion Explainer Graphics (generate_map_graphics)

Outputs:
    downloads/videos/scene_{index}.mp4 (1080x1920, 30fps fluid video clips)
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import SEARCH_QUERIES_FILE, DOWNLOADS_VIDEOS_DIR, TEMP_DIR
from utils.logger import get_logger
from utils.helpers import load_json

import generate_whiteboard
import generate_map_graphics
import download_videos

logger = get_logger(__name__)


def generate_all_scenes() -> list[Path]:
    """Generates all scene video clips using the Tri-Modal Visual Decision System."""
    logger.info("=== STEP 6 (TRI-MODAL): GENERATING DYNAMIC MULTI-STYLE SCENES ===")
    
    queries_raw = load_json(SEARCH_QUERIES_FILE)
    if isinstance(queries_raw, list):
        queries = queries_raw
    else:
        queries = queries_raw.get("queries", [])
        
    DOWNLOADS_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    generated_clips = []
    
    for i, item in enumerate(queries, start=1):
        v_style = item.get("visual_style", "cinematic")
        prompt = item.get("prompt", item.get("text", "Scene"))
        query = item.get("query", "space motion")
        duration = float(item.get("duration_s", item.get("duration", 4.0)))
        
        output_clip = DOWNLOADS_VIDEOS_DIR / f"scene_{i}.mp4"
        logger.info(f">>> Generating Scene {i}/{len(queries)} [Style: {v_style.upper()}] (Duration: {duration:.2f}s) — Prompt: '{prompt[:60]}...'")
        
        scene_start = time.time()
        try:
            if v_style == "doodle":
                generate_whiteboard.generate_single_scene(prompt, output_clip, duration=duration, scene_index=i)
            elif v_style == "map_motion":
                generate_map_graphics.generate_single_scene(prompt, output_clip, duration=duration, scene_index=i)
            else:
                # Cinematic stock / AI footage
                logger.info(f"Searching 4K Cinematic footage for: '{query}'...")
                # Search single video via Pexels/Pixabay
                used_ids = download_videos.get_recent_used_visual_ids()
                dl_url, asset_id, src = download_videos.search_dual_sources(query, used_ids)
                if not dl_url and item.get("fallback_queries"):
                    for fb_q in item["fallback_queries"]:
                        dl_url, asset_id, src = download_videos.search_dual_sources(fb_q, used_ids)
                        if dl_url:
                            break
                            
                if dl_url:
                    download_videos.download_file(dl_url, output_clip)
                else:
                    logger.warning(f"Stock video not found for '{query}'. Generating AI cinematic visual...")
                    generate_map_graphics.generate_single_scene(prompt, output_clip, duration=duration, scene_index=i)
                    
            if output_clip.exists() and output_clip.stat().st_size > 1000:
                generated_clips.append(output_clip)
                logger.info(f"Scene {i} generated successfully ({time.time() - scene_start:.2f}s) -> {output_clip.name}")
            else:
                raise RuntimeError(f"Scene {i} clip failed to create or is empty.")
                
        except Exception as e:
            logger.error(f"Error generating Scene {i} ({v_style}): {e}. Falling back to AI Doodle...")
            try:
                generate_whiteboard.generate_single_scene(prompt, output_clip, duration=duration, scene_index=i)
                generated_clips.append(output_clip)
            except Exception as fe:
                logger.error(f"Critical fallback failure on Scene {i}: {fe}")

    logger.info(f"Tri-Modal Video Generation complete. Total clips: {len(generated_clips)}")
    return generated_clips


def run() -> list[Path]:
    """Entry point for Step 6."""
    return generate_all_scenes()


if __name__ == "__main__":
    clips = run()
    print(f"Generated {len(clips)} multi-style clips.")
