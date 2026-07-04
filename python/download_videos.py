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


def search_pexels(query: str) -> str | None:
    """Search Pexels for a vertical stock video matching the query."""
    api_key = get_pexels_key()
    url = "https://api.pexels.com/v1/videos/search"
    headers = {"Authorization": api_key}
    
    # Request vertical/portrait orientation
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": 5
    }
    
    logger.info(f"Searching Pexels for: '{query}'")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            logger.warning(f"Pexels search API returned status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        videos = data.get("videos", [])
        if not videos:
            logger.info(f"No Pexels videos found for query: '{query}'")
            return None
            
        # Select the best video file
        for video in videos:
            video_files = video.get("video_files", [])
            # Filter for HD vertical files. Pexels video files include width and height.
            # We want aspect ratio vertical (height > width) and height >= 720 (ideally 1920)
            hd_files = []
            for vf in video_files:
                w = vf.get("width") or 0
                h = vf.get("height") or 0
                link = vf.get("link")
                
                # Check height > width (portrait) and is mp4
                if h > w and link and "mp4" in link:
                    hd_files.append(vf)
                    
            if hd_files:
                # Sort by height descending to get best quality (e.g. 1920 first)
                hd_files.sort(key=lambda x: x.get("height") or 0, reverse=True)
                best_link = hd_files[0]["link"]
                logger.info(f"Found suitable Pexels video (ID: {video.get('id')}, Resolution: {hd_files[0].get('width')}x{hd_files[0].get('height')})")
                return best_link
                
        # If no strict portrait file is found, just take the first video's highest res file
        # We will crop/scale it to 9:16 portrait in the video compilation step
        first_video = videos[0]
        files = sorted(first_video.get("video_files", []), key=lambda x: x.get("height") or 0, reverse=True)
        if files:
            logger.info(f"No portrait Pexels video found. Using landscape video ID {first_video.get('id')} to crop later.")
            return files[0]["link"]
            
    except Exception as e:
        logger.error(f"Error searching Pexels: {e}")
        
    return None


def search_pixabay(query: str) -> str | None:
    """Search Pixabay for a vertical/portrait stock video matching the query."""
    api_key = get_pixabay_key()
    url = "https://pixabay.com/api/videos/"
    
    # Pixabay API uses params for key and q
    params = {
        "key": api_key,
        "q": query,
        "video_type": "all",
        "per_page": 5
    }
    
    # Wait, does Pixabay have an orientation filter? 
    # Pixabay video API does NOT strictly have an 'orientation' parameter like Pexels,
    # or if it does, it's not always reliable. Let's filter post-search.
    logger.info(f"Searching Pixabay for: '{query}'")
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            logger.warning(f"Pixabay search API returned status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        hits = data.get("hits", [])
        if not hits:
            logger.info(f"No Pixabay videos found for query: '{query}'")
            return None
            
        # Select best video file
        for hit in hits:
            # Pixabay provides videos structure under hit['videos'] with keys like 'large', 'medium', 'small', 'tiny'
            # Each key has: url, width, height, size
            videos_dict = hit.get("videos", {})
            
            # Prefer vertical videos (height > width)
            for quality in ["large", "medium", "small"]:
                v_info = videos_dict.get(quality)
                if v_info:
                    w = v_info.get("width") or 0
                    h = v_info.get("height") or 0
                    url_link = v_info.get("url")
                    
                    if h > w and url_link:
                        logger.info(f"Found portrait Pixabay video (ID: {hit.get('id')}, Quality: {quality}, {w}x{h})")
                        return url_link
                        
        # Fallback to landscape if no portrait
        first_hit = hits[0]
        videos_dict = first_hit.get("videos", {})
        for quality in ["large", "medium", "small"]:
            v_info = videos_dict.get(quality)
            if v_info and v_info.get("url"):
                logger.info(f"No portrait Pixabay video found. Using landscape Pixabay video ID {first_hit.get('id')} to crop later.")
                return v_info["url"]
                
    except Exception as e:
        logger.error(f"Error searching Pixabay: {e}")
        
    return None


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
    
    downloaded_paths = []
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
        
        # 1. Try Pexels Search
        try:
            download_url = search_pexels(query)
        except Exception as e:
            logger.error(f"Pexels search failed for scene {index}: {e}")
            
        # 2. Try Pixabay Fallback
        if not download_url:
            logger.info("Pexels failed/empty. Trying Pixabay fallback...")
            try:
                download_url = search_pixabay(query)
            except Exception as e:
                logger.error(f"Pixabay search failed for scene {index}: {e}")
                
        # 3. If query fails, try generic queries
        generic_queries = ["abstract corporate motion", "neon abstract loop", "colorful smoke loop", "scenic nature slow motion"]
        g_idx = 0
        while not download_url and g_idx < len(generic_queries):
            generic_query = generic_queries[g_idx]
            logger.warning(f"No stock video found for '{query}'. Trying generic search: '{generic_query}'...")
            download_url = search_pexels(generic_query)
            if not download_url:
                download_url = search_pixabay(generic_query)
            g_idx += 1
            
        # 4. Perform Download
        if download_url:
            try:
                downloaded_file = download_file(download_url, output_file)
                downloaded_paths.append(downloaded_file)
                successful_downloads.append(downloaded_file)
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
            
    logger.info(f"Completed downloading stock videos. Total downloaded: {len(downloaded_paths)} clips.")
    return downloaded_paths


if __name__ == "__main__":
    try:
        paths = run()
        print(f"Downloaded video paths: {[str(p) for p in paths]}")
    except Exception as exc:
        logger.exception("download_videos module execution failed")
        sys.exit(1)
