"""
generate_ai_videos.py

Reads the AI-generated Veo prompts from data/search_queries.json
Calls the Google Gemini API (Veo) to generate short video clips.
Saves the videos to downloads/videos/scene_{index}.mp4
"""

import sys
import json
import time
from pathlib import Path
from google import genai
from google.genai import types

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import SEARCH_QUERIES_FILE, DOWNLOADS_VIDEOS_DIR
from utils.logger import get_logger
from utils.config import get_gemini_key, get_setting
from utils.helpers import clean_directory

logger = get_logger("generate_ai_videos")

def run() -> list[str]:
    """Orchestrates Step 6 of the pipeline using Google Veo AI."""
    logger.info("=== STEP 6: GENERATE AI VIDEOS ===")
    
    if not SEARCH_QUERIES_FILE.exists():
        raise FileNotFoundError(f"Search queries file not found at {SEARCH_QUERIES_FILE}. Run Step 5 first.")
        
    with open(SEARCH_QUERIES_FILE, "r", encoding="utf-8") as f:
        queries_data = json.load(f)
        
    if not queries_data:
        raise ValueError("Search queries list is empty.")
        
    # Clear downloads/videos/ directory to start fresh
    logger.info(f"Cleaning video downloads directory: {DOWNLOADS_VIDEOS_DIR}")
    clean_directory(DOWNLOADS_VIDEOS_DIR)
    
    api_key = get_gemini_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables.")
        
    client = genai.Client(api_key=api_key)
    model_name = get_setting('veo_generation', 'model', 'veo-2.0-generate-001')
    aspect_ratio = get_setting('veo_generation', 'aspect_ratio', '9:16')
    
    downloaded_paths = []
    
    for i, item in enumerate(queries_data):
        index = item.get("subtitle_index", i+1)
        prompt = item.get("query", "abstract background")
        duration = item.get("duration_s", 5.0)
        
        output_file = DOWNLOADS_VIDEOS_DIR / f"scene_{index}.mp4"
        logger.info(f"Scene {i + 1}/{len(queries_data)} — Veo Prompt: '{prompt}' (Target duration: {duration}s)")
        
        try:
            # Initiate the video generation request
            logger.info(f"Sending prompt to Gemini API ({model_name})...")
            operation = client.models.generate_videos(
                model=model_name,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    # We might not be able to precisely control duration, Veo defaults to ~5s
                ),
            )
            
            # Wait for the operation to complete
            while not operation.done:
                logger.info("Generating video... waiting 10 seconds.")
                time.sleep(10)
                operation = client.operations.get(operation)
                
            # Check for errors in the operation response
            if hasattr(operation, "error") and operation.error:
                raise Exception(f"API returned error: {operation.error.message}")
                
            # Download and save the result
            generated_video = operation.response.generated_videos[0]
            
            logger.info(f"Video generated successfully! Downloading to {output_file}")
            
            # Save the file (SDK usually has a way to fetch bytes directly)
            video_bytes = client.files.get_bytes(file=generated_video.video)
            
            with open(output_file, 'wb') as f:
                f.write(video_bytes)

            downloaded_paths.append(str(output_file))
            
        except Exception as e:
            logger.error(f"Failed to generate AI video for scene {index}: {e}")
            
    logger.info(f"Completed generating AI videos. Total downloaded: {len(downloaded_paths)} clips.")
    return downloaded_paths

if __name__ == "__main__":
    run()
