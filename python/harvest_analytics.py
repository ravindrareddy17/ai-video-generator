import sys
import json
from pathlib import Path
from datetime import datetime

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.upload_youtube import get_authenticated_service
from utils.database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)

def harvest_channel_stats():
    """Harvest real-time stats (views, likes, comments) for all uploaded videos on the channel."""
    logger.info("Starting YouTube analytics harvesting...")
    
    youtube = get_authenticated_service()
    if not youtube:
        logger.error("YouTube service is not authenticated. Skipping stats harvest.")
        return False
        
    try:
        # 1. Fetch channel's uploads playlist ID
        channels_response = youtube.channels().list(mine=True, part="contentDetails").execute()
        if not channels_response.get("items"):
            logger.error("No channel found for current credentials.")
            return False
            
        uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # 2. Retrieve last 50 video IDs from uploads playlist
        playlist_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="snippet",
            maxResults=50
        ).execute()
        
        items = playlist_response.get("items", [])
        if not items:
            logger.info("No videos found on the channel.")
            return True
            
        video_map = {}
        for item in items:
            title = item["snippet"]["title"]
            video_id = item["snippet"]["resourceId"]["videoId"]
            video_map[video_id] = title
            
        video_ids = list(video_map.keys())
        
        # 3. Query video statistics in batches of 50
        stats_response = youtube.videos().list(
            id=",".join(video_ids),
            part="statistics"
        ).execute()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        for video_stat in stats_response.get("items", []):
            video_id = video_stat["id"]
            stats = video_stat.get("statistics", {})
            
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            
            # Map this video ID back to SQLite tables
            # First, check if video is tracked in 'videos' table. If not, insert it!
            cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", (video_id,))
            row = cursor.fetchone()
            if row:
                sqlite_video_id = row[0]
            else:
                title = video_map.get(video_id, "Unknown Title")
                cursor.execute("""
                    INSERT INTO videos (title, youtube_id, status)
                    VALUES (?, ?, ?)
                """, (title, video_id, "uploaded"))
                sqlite_video_id = cursor.lastrowid
                
            # Log video analytics snapshot for today
            # Check if we already have an entry for today for this video
            cursor.execute("""
                SELECT id FROM analytics 
                WHERE video_id = ? AND date = ?
            """, (sqlite_video_id, today_date))
            existing_row = cursor.fetchone()
            
            if existing_row:
                cursor.execute("""
                    UPDATE analytics 
                    SET views = ?, likes = ?, comments = ?
                    WHERE id = ?
                """, (views, likes, comments, existing_row[0]))
            else:
                cursor.execute("""
                    INSERT INTO analytics (video_id, date, views, likes, comments)
                    VALUES (?, ?, ?, ?, ?)
                """, (sqlite_video_id, today_date, views, likes, comments))
                
            logger.info(f"Synced stats for video '{video_map.get(video_id)[:40]}...': Views: {views} | Likes: {likes} | Comments: {comments}")
            
        # Update the overall channel metrics (views, subscribers) in settings if needed, or simply log them
        conn.commit()
        conn.close()
        logger.info("Successfully harvested and saved channel stats.")
        return True
        
    except Exception as e:
        logger.error(f"Error harvesting YouTube stats: {e}", exc_info=True)
        return False

def run() -> bool:
    """Orchestrates Step 11.5 of the pipeline."""
    logger.info("=== STEP 11.5: HARVEST YOUTUBE ANALYTICS ===")
    return harvest_channel_stats()

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
