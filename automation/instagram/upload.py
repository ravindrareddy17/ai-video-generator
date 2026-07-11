import sys
from pathlib import Path
import time
import requests

# Bootstrap imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.paths import METADATA_FILE
from utils.logger import get_logger
from utils.helpers import load_json
from automation.database.connection import get_youtube_conn, get_facebook_conn, get_instagram_conn
from python.meta_auth import get_valid_token, load_credentials

logger = get_logger("instagram.upload")

def create_media_container(ig_account_id: str, video_url: str, caption: str, access_token: str, version: str = "v25.0", base_url: str = "https://graph.facebook.com") -> str:
    url = f"{base_url}/{version}/{ig_account_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token,
    }
    
    logger.info("Initializing Instagram media container for Reels...")
    response = requests.post(url, data=payload, timeout=60)
    res_data = response.json()
    
    if "id" not in res_data:
        raise Exception(f"Failed to create Instagram Reels container: {res_data}")
        
    return res_data["id"]

def poll_container_status(container_id: str, access_token: str, version: str = "v25.0", base_url: str = "https://graph.facebook.com", poll_interval: int = 5, max_wait: int = 300) -> str:
    url = f"{base_url}/{version}/{container_id}"
    params = {
        "fields": "status_code",
        "access_token": access_token
    }
    
    start_time = time.time()
    logger.info("Polling Reels container status...")
    
    while time.time() - start_time < max_wait:
        response = requests.get(url, params=params, timeout=60)
        res_data = response.json()
        
        status = res_data.get("status_code", "ERROR")
        logger.info(f"Container {container_id} status: {status}")
        
        if status == "FINISHED":
            return "FINISHED"
        if status == "ERROR":
            raise Exception(f"Instagram Reels container failed: {res_data}")
            
        time.sleep(poll_interval)
        
    raise TimeoutError("Timeout waiting for Instagram Reels container processing.")

def publish_container(ig_account_id: str, container_id: str, access_token: str, version: str = "v25.0", base_url: str = "https://graph.facebook.com") -> str:
    url = f"{base_url}/{version}/{ig_account_id}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": access_token,
    }
    
    logger.info("Publishing Instagram Reels container...")
    response = requests.post(url, data=payload, timeout=60)
    res_data = response.json()
    
    if "id" not in res_data:
        raise Exception(f"Failed to publish Instagram Reels container: {res_data}")
        
    return res_data["id"]

def upload_instagram_reel(video_url: str, caption: str) -> str | None:
    try:
        creds = load_credentials()
        ig_id = creds.get("instagram_id")
        if not ig_id:
            logger.warning("Instagram Business Account ID is missing.")
            return None
            
        token = get_valid_token()
        container_id = create_media_container(ig_id, video_url, caption, token)
        
        # Wait for processing
        poll_container_status(container_id, token)
        
        media_id = publish_container(ig_id, container_id, token)
        
        # Get permalink
        url = f"https://graph.facebook.com/v25.0/{media_id}"
        params = {"fields": "permalink", "access_token": token}
        response = requests.get(url, params=params, timeout=60)
        res_data = response.json()
        
        return res_data.get("permalink")
    except Exception as e:
        logger.error(f"Failed to publish Instagram Reels: {e}")
        return None

def run() -> str | None:
    try:
        metadata = load_json(METADATA_FILE)
        if not metadata:
            logger.warning("No metadata found.")
            return None

        # Fetch public video URL from youtube.db or facebook.db
        video_url = None
        
        # 1. Try YouTube ID first
        try:
            yt_conn = get_youtube_conn()
            cursor = yt_conn.cursor()
            row = cursor.execute("SELECT youtube_id FROM videos WHERE status = 'uploaded' ORDER BY id DESC LIMIT 1").fetchone()
            if row and row["youtube_id"]:
                video_url = f"https://youtube.com/shorts/{row['youtube_id']}"
            yt_conn.close()
        except Exception as e:
            logger.warning(f"Could not read youtube_id from youtube.db: {e}")

        # 2. Fallback to Facebook URL
        if not video_url:
            try:
                fb_conn = get_facebook_conn()
                cursor = fb_conn.cursor()
                row = cursor.execute("SELECT facebook_url FROM videos WHERE status = 'uploaded' ORDER BY id DESC LIMIT 1").fetchone()
                if row and row["facebook_url"]:
                    video_url = row["facebook_url"]
                fb_conn.close()
            except Exception as e:
                logger.warning(f"Could not read facebook_url: {e}")

        if not video_url:
            logger.warning("No public video URL found in youtube.db or facebook.db. Instagram Reels upload requires a hosted URL.")
            return None

        caption_parts = []
        title = metadata.get("title", "")
        desc = metadata.get("description", "")
        tags = metadata.get("tags", [])
        
        if title:
            caption_parts.append(title)
        if desc:
            caption_parts.append(desc)
        if tags:
            caption_parts.append(" ".join(tags))
            
        caption = "\n\n".join(caption_parts)
        
        permalink = upload_instagram_reel(video_url, caption)
        
        if permalink:
            try:
                ig_id = permalink.rstrip("/").split("/")[-1]
                conn = get_instagram_conn()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE videos SET instagram_url = ?, instagram_id = ?, status = 'uploaded', uploaded_at = CURRENT_TIMESTAMP
                    WHERE id = (SELECT MAX(id) FROM videos WHERE status = 'generating')
                """, (permalink, ig_id))
                conn.commit()
                conn.close()
                logger.info(f"Database instagram_url updated to: {permalink}")
            except Exception as e:
                logger.error(f"Failed to update instagram.db: {e}")
                
            return permalink
    except Exception as e:
        logger.error(f"Instagram upload runner error: {e}")
        
    return None

if __name__ == "__main__":
    url = run()
    if url:
        print(f"Instagram Upload Success: {url}")
    else:
        print("Instagram Upload Failed")
