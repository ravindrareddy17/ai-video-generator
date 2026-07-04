"""
generate_visuals.py — Step 5 for MythX engine.

Generates AI images using Pollinations.ai based on `visual_prompts` from content.json,
and determines the timing for each image to fit the total narration duration.

Inputs:
    data/content.json
    captions/voice.srt (to get total duration, or we can just use word_timings.json)

Outputs:
    downloads/videos/scene_0.jpg ...
    data/visual_metadata.json (used by create_video.py)
"""

import sys
from pathlib import Path
import json
import urllib.parse
import time
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import CONTENT_FILE, DOWNLOADS_VIDEOS_DIR, WORD_TIMINGS_FILE, DATA_DIR
from utils.logger import get_logger
from utils.helpers import load_json, save_json, clean_directory

logger = get_logger(__name__)

VISUAL_METADATA_FILE = DATA_DIR / "visual_metadata.json"

def run():
    logger.info("=== STEP 5: GENERATE AI VISUALS (Pollinations.ai) ===")
    
    if not CONTENT_FILE.exists():
        raise FileNotFoundError("content.json missing. Run Step 2.")
    if not WORD_TIMINGS_FILE.exists():
        raise FileNotFoundError("word_timings.json missing. Run Step 3/4 first.")
        
    content = load_json(CONTENT_FILE)
    prompts = content.get("visual_prompts", [])
    if not prompts:
        raise ValueError("No visual_prompts found in content.json")
        
    timings = load_json(WORD_TIMINGS_FILE)
    if not timings:
        raise ValueError("No timings found in word_timings.json")
        
    # Calculate total duration from the last sentence's offset + duration
    last_timing = timings[-1]
    total_duration_ms = last_timing["offset_ms"] + last_timing["duration_ms"]
    total_duration_s = total_duration_ms / 1000.0
    
    # Calculate duration per prompt
    num_prompts = len(prompts)
    duration_per_prompt = total_duration_s / num_prompts
    
    clean_directory(DOWNLOADS_VIDEOS_DIR)
    DOWNLOADS_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    
    visual_metadata = []
    
    for i, prompt in enumerate(prompts):
        logger.info(f"Generating image {i+1}/{num_prompts}: {prompt[:50]}...")
        
        # URL encode the prompt
        safe_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true"
        
        output_file = DOWNLOADS_VIDEOS_DIR / f"scene_{i}.jpg"
        
        # Download with retry and a real user-agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                break
            except Exception as e:
                logger.warning(f"Download failed (attempt {attempt+1}): {e}")
                time.sleep(2)
        else:
            raise RuntimeError(f"Failed to download image for prompt: {prompt}")
            
        visual_metadata.append({
            "scene_index": i,
            "duration_s": duration_per_prompt,
            "file": str(output_file)
        })
        
    save_json(visual_metadata, VISUAL_METADATA_FILE)
    logger.info(f"Saved metadata for {len(visual_metadata)} images.")
    
    return visual_metadata

if __name__ == "__main__":
    run()
