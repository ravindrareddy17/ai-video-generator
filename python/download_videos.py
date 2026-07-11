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
import time
import requests

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


def search_pexels(query: str, used_ids: set[str] = None) -> tuple[str | None, str | None]:
    """Search Pexels for a vertical video matching the query. Returns (download_url, video_id)."""
    if used_ids is None:
        used_ids = set()
        
    api_key = get_pexels_key()
    url = "https://api.pexels.com/v1/videos/search"
    headers = {"Authorization": api_key}
    
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": 8
    }
    
    logger.info(f"Searching Pexels for: '{query}'")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            logger.warning(f"Pexels search API returned status {response.status_code}")
            return None, None
            
        data = response.json()
        videos = data.get("videos", [])
        if not videos:
            return None, None
            
        for video in videos:
            v_id = str(video.get("id"))
            if v_id in used_ids:
                logger.info(f"Visual Deduplication: Skipping used Pexels video {v_id}")
                continue
                
            video_files = video.get("video_files", [])
            hd_files = []
            for vf in video_files:
                w = vf.get("width") or 0
                h = vf.get("height") or 0
                link = vf.get("link")
                if h > w and link and "mp4" in link:
                    hd_files.append(vf)
                    
            if hd_files:
                hd_files.sort(key=lambda x: x.get("height") or 0, reverse=True)
                best_link = hd_files[0]["link"]
                return best_link, v_id
                
        # Landscape fallback
        for video in videos:
            v_id = str(video.get("id"))
            if v_id in used_ids:
                continue
            files = sorted(video.get("video_files", []), key=lambda x: x.get("height") or 0, reverse=True)
            if files:
                return files[0]["link"], v_id
                
    except Exception as e:
        logger.error(f"Error searching Pexels: {e}")
        
    return None, None


def search_pixabay(query: str, used_ids: set[str] = None) -> tuple[str | None, str | None]:
    """Search Pixabay for a vertical video matching the query. Returns (download_url, video_id)."""
    if used_ids is None:
        used_ids = set()
        
    api_key = get_pixabay_key()
    url = "https://pixabay.com/api/videos/"
    
    params = {
        "key": api_key,
        "q": query,
        "video_type": "all",
        "per_page": 8
    }
    
    logger.info(f"Searching Pixabay for: '{query}'")
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            logger.warning(f"Pixabay search API returned status {response.status_code}")
            return None, None
            
        data = response.json()
        hits = data.get("hits", [])
        if not hits:
            return None, None
            
        for hit in hits:
            v_id = str(hit.get("id"))
            if v_id in used_ids:
                logger.info(f"Visual Deduplication: Skipping used Pixabay video {v_id}")
                continue
                
            videos_dict = hit.get("videos", {})
            for quality in ["large", "medium", "small"]:
                v_info = videos_dict.get(quality)
                if v_info:
                    w = v_info.get("width") or 0
                    h = v_info.get("height") or 0
                    url_link = v_info.get("url")
                    if h > w and url_link:
                        return url_link, v_id
                        
        # Landscape fallback
        for hit in hits:
            v_id = str(hit.get("id"))
            if v_id in used_ids:
                continue
            videos_dict = hit.get("videos", {})
            for quality in ["large", "medium", "small"]:
                v_info = videos_dict.get(quality)
                if v_info and v_info.get("url"):
                    return v_info["url"], v_id
                    
    except Exception as e:
        logger.error(f"Error searching Pixabay: {e}")
        
    return None, None


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
        
        # 1. Try Pexels Search
        try:
            download_url, asset_id = search_pexels(query, used_ids)
        except Exception as e:
            logger.error(f"Pexels search failed for scene {index}: {e}")
            
        # 2. Try Pixabay Fallback
        if not download_url:
            logger.info("Pexels failed/empty. Trying Pixabay fallback...")
            try:
                download_url, asset_id = search_pixabay(query, used_ids)
            except Exception as e:
                logger.error(f"Pixabay search failed for scene {index}: {e}")
                
        # 3. If query fails, try generic queries
        generic_queries = ["abstract corporate motion", "neon abstract loop", "colorful smoke loop", "scenic nature slow motion"]
        g_idx = 0
        while not download_url and g_idx < len(generic_queries):
            generic_query = generic_queries[g_idx]
            logger.warning(f"No stock video found for '{query}'. Trying generic search: '{generic_query}'...")
            download_url, asset_id = search_pexels(generic_query, used_ids)
            if not download_url:
                download_url, asset_id = search_pixabay(generic_query, used_ids)
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
