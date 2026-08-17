"""
download_videos.py — Step 6 of the AI Video Generator V2 pipeline.

Downloads one high-quality stock video for each search query.
Uses Pexels API as primary source and Pixabay API as fallback.

Inputs:
    data/search_queries.json

Outputs:
    downloads/videos/scene_{index}.mp4
"""

import sys
from pathlib import Path
import json
import random
import time
import requests
import subprocess
import urllib.parse

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import SEARCH_QUERIES_FILE, DOWNLOADS_VIDEOS_DIR
from utils.config import get_pexels_key, get_pixabay_key, get_setting
from utils.logger import get_logger
from utils.helpers import load_json, clean_directory
from utils.retry import retry
from utils.database import get_connection

logger = get_logger(__name__)


@retry(max_attempts=3, delay=3.0, backoff=2.0)
def download_file(url: str, output_path: Path) -> Path:
    """Download a file via streaming HTTP GET request."""
    logger.info(f"Downloading from URL: {url} -> {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use headers to look like a browser if needed (Pixabay doesn't require headers, Pexels download link usually doesn't either)
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                
    logger.info(f"Successfully downloaded file. Size: {output_path.stat().st_size} bytes")
    return output_path

def get_recent_used_visual_ids() -> set[str]:
    """Retrieve Pexels/Pixabay video IDs used in the last 15 videos to prevent repetition."""
    used_ids = set()
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT visual_queries FROM videos ORDER BY id DESC LIMIT 15")
            rows = cursor.fetchall()
            for row in rows:
                val = row[0]
                if val:
                    try:
                        data = json.loads(val)
                        ids = data.get("used_visual_ids", [])
                        for vid in ids:
                            used_ids.add(str(vid))
                    except Exception:
                        pass
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"Failed to query used visual IDs: {e}")
    return used_ids


def fetch_pexels_candidates(query: str, used_ids: set[str]) -> list[dict]:
    """Fetch video candidates from Pexels."""
    api_key = get_pexels_key()
    url = "https://api.pexels.com/v1/videos/search"
    headers = {"Authorization": api_key}
    params = {"query": query, "orientation": "portrait", "per_page": 15}
    
    candidates = []
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            videos = response.json().get("videos", [])
            for video in videos:
                v_id = f"pexels_{video.get('id')}"
                if v_id in used_ids:
                    continue
                video_files = video.get("video_files", [])
                hd_files = []
                for vf in video_files:
                    w = vf.get("width") or 0
                    h = vf.get("height") or 0
                    link = vf.get("link")
                    if link and "mp4" in link:
                        hd_files.append((h > w, h, link))
                if hd_files:
                    hd_files.sort(key=lambda x: x[1], reverse=True)
                    is_vert, height, link = hd_files[0]
                    candidates.append({"url": link, "id": v_id, "source": "Pexels", "is_vertical": is_vert, "height": height})
    except Exception as e:
        logger.error(f"Error fetching Pexels candidates: {e}")
    return candidates


def fetch_pixabay_candidates(query: str, used_ids: set[str]) -> list[dict]:
    """Fetch video candidates from Pixabay."""
    api_key = get_pixabay_key()
    url = "https://pixabay.com/api/videos/"
    params = {"key": api_key, "q": query, "video_type": "all", "per_page": 15}
    
    candidates = []
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            hits = response.json().get("hits", [])
            for hit in hits:
                v_id = f"pixabay_{hit.get('id')}"
                if v_id in used_ids:
                    continue
                videos_dict = hit.get("videos", {})
                for quality in ["large", "medium", "small"]:
                    v_info = videos_dict.get(quality)
                    if v_info and v_info.get("url"):
                        w = v_info.get("width") or 0
                        h = v_info.get("height") or 0
                        link = v_info.get("url")
                        candidates.append({"url": link, "id": v_id, "source": "Pixabay", "is_vertical": (h > w), "height": h})
                        break
    except Exception as e:
        logger.error(f"Error fetching Pixabay candidates: {e}")
    return candidates


def search_dual_sources(query: str, used_ids: set[str] = None) -> tuple[str | None, str | None, str | None]:
    """Query BOTH Pexels and Pixabay simultaneously, aggregate candidates, and pick the best video clip."""
    if used_ids is None:
        used_ids = set()
        
    logger.info(f"Searching DUAL SOURCES (Pexels + Pixabay) for: '{query}'")
    pexels_cands = fetch_pexels_candidates(query, used_ids)
    pixabay_cands = fetch_pixabay_candidates(query, used_ids)
    
    all_candidates = pexels_cands + pixabay_cands
    if not all_candidates:
        return None, None, None
        
    # Separate vertical and landscape clips
    verticals = [c for c in all_candidates if c["is_vertical"]]
    landscapes = [c for c in all_candidates if not c["is_vertical"]]
    
    pool = verticals if verticals else landscapes
    if not pool:
        return None, None, None
        
    # Sort pool by resolution/height descending
    pool.sort(key=lambda x: x["height"], reverse=True)
    
    # Pick randomly from the top 5 highest resolution candidates across both platforms for variety
    top_candidates = pool[:min(5, len(pool))]
    winner = random.choice(top_candidates)
    
    logger.info(f"Selected best candidate from {winner['source']} (Res Height: {winner['height']}px, ID: {winner['id']})")
    return winner["url"], winner["id"], winner["source"]


def generate_ai_image_video(prompt: str, output_file: Path, duration: float) -> Path:
    """Generate an AI image from Pollinations and convert it to a video with a Ken Burns effect."""
    logger.info(f"Generating AI Image for prompt: '{prompt}'")
    
    # URL encode the prompt and use the default reliable model (Flux)
    safe_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true"
    
    temp_image_path = output_file.with_suffix('.jpg')
    
    # Retry logic to ensure the image downloads successfully
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading AI Image from Pollinations (Attempt {attempt+1}/{max_retries})...")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(temp_image_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Successfully downloaded AI Image.")
                break
            else:
                logger.warning(f"Failed to download AI Image (Status {response.status_code}).")
        except Exception as e:
            logger.warning(f"Error downloading AI Image: {e}")
            
        if attempt == max_retries - 1:
            raise Exception("Failed to generate AI image after multiple attempts.")
        time.sleep(2)
                
    logger.info(f"AI Image downloaded. Converting to video with FFmpeg...")
    
    # zoompan=z='min(zoom+0.0015,1.15)' means zoom in slowly up to 115%
    # d=750 ensures the zoompan doesn't reset or loop within our short clip (750 frames = 25 seconds)
    # s=1080x1920 strictly forces output size to prevent ffmpeg dimension errors
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(temp_image_path),
        "-vf", "zoompan=z='min(zoom+0.0015,1.15)':d=750:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',framerate=30",
        "-c:v", "libx264",
        "-t", str(duration + 1.0), # give a 1s buffer
        "-pix_fmt", "yuv420p",
        str(output_file)
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"Successfully created AI video clip at {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed to create AI video: {e}")
        raise
    finally:
        if temp_image_path.exists():
            temp_image_path.unlink()
            
    return output_file


def run() -> list[Path]:
    """Orchestrates Step 6 of the pipeline."""
    logger.info("=== STEP 6: DOWNLOAD VIDEOS ===")
    
    if not SEARCH_QUERIES_FILE.exists():
        raise FileNotFoundError(f"Search queries file not found at {SEARCH_QUERIES_FILE}. Run Step 5 first.")
        
    queries_data = load_json(SEARCH_QUERIES_FILE)
    if not queries_data:
        raise ValueError("Search queries list is empty.")
        
    # Clear downloads/videos/ directory to start fresh
    logger.info(f"Cleaning video downloads directory: {DOWNLOADS_VIDEOS_DIR}")
    clean_directory(DOWNLOADS_VIDEOS_DIR)
    
    # Query recently used visual IDs to avoid duplicate visual downloads
    used_ids = get_recent_used_visual_ids()
    logger.info(f"Found {len(used_ids)} recently used visual asset IDs to exclude.")
    
    downloaded_paths = []
    downloaded_visual_ids = set()
    delay = get_setting('download', 'delay_between_requests', 1.0)
    
    # We will track previously downloaded files to reuse as fallback if search fails
    successful_downloads = []
    
    for i, item in enumerate(queries_data):
        index = item.get("subtitle_index")
        query = item.get("query", "abstract background")
        duration = item.get("duration_s", 5.0)
        
        output_file = DOWNLOADS_VIDEOS_DIR / f"scene_{index}.mp4"
        logger.info(f"Scene {i + 1}/{len(queries_data)} — Query: '{query}' (Target duration: {duration}s)")
        
        download_url = None
        asset_id = None
        
        # 100% Video Mode: No static images/photos
        is_ai_scene = False
        
        if is_ai_scene:
            logger.info(f">>> CONTEXT: Chosen 'image' for scene {index}.")
            image_prompt = item.get("image_prompt", query)
            try:
                downloaded_file = generate_ai_image_video(image_prompt, output_file, duration)
                downloaded_paths.append(downloaded_file)
                successful_downloads.append(downloaded_file)
                download_url = "AI_GENERATED"
            except Exception as e:
                logger.error(f"Failed to generate AI image video: {e}")
                download_url = None
        else:
            logger.info(f">>> NARRATIVE MATCH ENGINE: Searching videos for scene {index} ('{query}')...")
            
            # Construct multi-stage physical subject search list
            search_terms = []
            if query:
                search_terms.append(query)
            for fb in item.get("fallback_queries", []):
                if fb and fb not in search_terms:
                    search_terms.append(fb)
            # Add individual concrete words as fallback (e.g. "rocket" from "rocket launch")
            if query:
                words = [w.strip() for w in query.split() if len(w.strip()) > 3]
                for w in words:
                    if w not in search_terms:
                        search_terms.append(w)
                        
            for term in search_terms:
                try:
                    logger.info(f"Targeted search for narration subject: '{term}'...")
                    download_url, asset_id, source_name = search_dual_sources(term, used_ids)
                    if download_url:
                        logger.info(f"Matched video clip for '{term}' from {source_name}!")
                        break
                except Exception as e:
                    logger.error(f"Search for term '{term}' failed for scene {index}: {e}")
                    
            # If all targeted terms fail, try generic queries
            if not download_url:
                generic_queries = ["cinematic galaxy motion", "futuristic neon city loop", "abstract technology background", "dramatic nature slow motion"]
                g_idx = 0
                while not download_url and g_idx < len(generic_queries):
                    generic_query = generic_queries[g_idx]
                    logger.warning(f"No targeted video found for scene {index}. Trying generic search: '{generic_query}'...")
                    download_url, asset_id, source_name = search_dual_sources(generic_query, used_ids)
                    g_idx += 1
                
            # 4. Perform Download
            if download_url:
                try:
                    downloaded_file = download_file(download_url, output_file)
                    downloaded_paths.append(downloaded_file)
                    successful_downloads.append(downloaded_file)
                    if asset_id:
                        downloaded_visual_ids.add(str(asset_id))
                except Exception as e:
                    logger.error(f"Failed to download video file: {e}")
                    download_url = None  # trigger next fallback
                
        # 5. Ultimate Fallback: Reuse a previous successful video or use a dummy file
        if not download_url or not output_file.exists():
            if successful_downloads:
                fallback_source = successful_downloads[-1]
                logger.warning(f"Ultimate fallback: copying previous scene {fallback_source.name} as scene_{index}.mp4")
                import shutil
                shutil.copy2(fallback_source, output_file)
                downloaded_paths.append(output_file)
            else:
                raise RuntimeError(
                    f"Unable to download or copy any stock video for scene_{index}.mp4. "
                    "Please ensure you have internet access and valid API keys."
                )
                
        # Respect rate limits
        if delay > 0 and i < len(queries_data) - 1:
            logger.info(f"Waiting {delay}s before next query...")
            time.sleep(delay)
            
    # Update SQLite database video row with list of downloaded visual IDs
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM videos WHERE status = 'generating' ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                vid_id = row[0]
                cursor.execute("""
                    UPDATE videos 
                    SET visual_queries = ? 
                    WHERE id = ?
                """, (
                    json.dumps({
                        "queries": [item.get("query") for item in queries_data],
                        "used_visual_ids": list(downloaded_visual_ids)
                    }),
                    vid_id
                ))
                conn.commit()
                logger.info(f"Updated video #{vid_id} in database with downloaded asset IDs: {list(downloaded_visual_ids)}")
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"Failed to record visual ID metadata in database: {e}")
        
    logger.info(f"Completed downloading stock videos. Total downloaded: {len(downloaded_paths)} clips.")
    return downloaded_paths


if __name__ == "__main__":
    try:
        paths = run()
        print(f"Downloaded video paths: {[str(p) for p in paths]}")
    except Exception as exc:
        logger.exception("download_videos module execution failed")
        sys.exit(1)
