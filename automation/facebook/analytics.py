import sys
import requests
from pathlib import Path
from datetime import datetime

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from automation.database.connection import get_facebook_conn
from python.meta_auth import get_valid_token, get_page_access_token, load_credentials
from utils.logger import get_logger

logger = get_logger("facebook.analytics")

def harvest_facebook_stats() -> bool:
    """Harvest performance metrics (views, likes, comments, reach) for all published Facebook Page Reels."""
    logger.info("Starting Facebook Page analytics harvesting...")
    
    try:
        creds = load_credentials()
        page_id = creds.get("page_id")
        if not page_id:
            logger.error("Facebook Page ID missing. Skipping Facebook harvest.")
            return False
            
        user_token = get_valid_token()
        page_token = get_page_access_token(user_token, page_id)
        if not page_token:
            logger.error("Failed to get Facebook Page access token.")
            return False
            
        conn = get_facebook_conn()
        try:
            cursor = conn.cursor()
        
            # 1. Fetch Page follower statistics
            try:
                url = f"https://graph.facebook.com/v25.0/{page_id}"
                params = {
                    "fields": "fan_count,followers_count",
                    "access_token": page_token
                }
                response = requests.get(url, params=params, timeout=60)
                res_data = response.json()
                followers = res_data.get("followers_count", 0)
                likes_count = res_data.get("fan_count", 0)
                logger.info(f"Facebook followers: {followers} | Page Likes: {likes_count}")
            except Exception as fe:
                logger.warning(f"Could not fetch Facebook Page followers: {fe}")
                followers = 0
                likes_count = 0
            
            # 2. Query tracked videos in facebook.db
            cursor.execute("SELECT id, facebook_id, title FROM videos WHERE facebook_id IS NOT NULL")
            videos = cursor.fetchall()
        
            today_date = datetime.now().strftime("%Y-%m-%d")
        
            for video in videos:
                sqlite_video_id = video["id"]
                fb_video_id = video["facebook_id"]
            
                views = 0
                likes = 0
                comments = 0
                shares = 0
                reach = 0
                impressions = 0
                watch_time = 0.0
            
                # Fetch views and standard video summary stats
                try:
                    url = f"https://graph.facebook.com/v25.0/{fb_video_id}"
                    params = {
                        "fields": "likes.summary(true),comments.summary(true),shares,views",
                        "access_token": page_token
                    }
                    res = requests.get(url, params=params, timeout=60).json()
                    views = res.get("views", 0)
                    likes = res.get("likes", {}).get("summary", {}).get("total_count", 0)
                    comments = res.get("comments", {}).get("summary", {}).get("total_count", 0)
                    shares = res.get("shares", {}).get("count", 0)
                except Exception as e:
                    logger.warning(f"Could not fetch views/likes/comments for FB video {fb_video_id}: {e}")
                
                # Fetch video insights (reach, impressions, average watch duration)
                try:
                    url = f"https://graph.facebook.com/v25.0/{fb_video_id}/video_insights"
                    params = {
                        "access_token": page_token
                    }
                    res = requests.get(url, params=params, timeout=60).json()
                    if "data" in res:
                        for metric in res["data"]:
                            name = metric.get("name")
                            val = metric.get("values", [{}])[0].get("value", 0)
                            if name == "post_impressions_unique" or name == "total_video_impressions_unique":
                                reach = val
                            elif name == "total_video_impressions":
                                impressions = val
                            elif name == "total_video_view_time":
                                watch_time = val / 3600000.0  # convert milliseconds to hours
                except Exception as e:
                    logger.warning(f"Could not fetch video_insights for FB video {fb_video_id}: {e}")

                if reach == 0:
                    reach = views
                if impressions == 0:
                    impressions = views * 2
                
                total_eng = likes + comments + shares
                engagement_rate = (total_eng / max(1, reach)) * 100
            
                # Update analytics table in facebook.db
                cursor.execute("""
                    SELECT id FROM analytics 
                    WHERE video_id = ? AND date = ?
                """, (sqlite_video_id, today_date))
                existing = cursor.fetchone()
            
                if existing:
                    cursor.execute("""
                        UPDATE analytics 
                        SET reach = ?, impressions = ?, video_views = ?, watch_time = ?, likes = ?, comments = ?, shares = ?, engagement_rate = ?
                        WHERE id = ?
                    """, (reach, impressions, views, watch_time, likes, comments, shares, engagement_rate, existing[0]))
                else:
                    cursor.execute("""
                        INSERT INTO analytics (video_id, date, reach, impressions, video_views, watch_time, likes, comments, shares, engagement_rate, audience_growth)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (sqlite_video_id, today_date, reach, impressions, views, watch_time, likes, comments, shares, engagement_rate))
                
                logger.info(f"Synced Facebook stats for Reel '{video['title'][:40]}...': Views: {views} | Likes: {likes}")
            
            conn.commit()
        finally:
            conn.close()
        logger.info("Successfully completed Facebook Page analytics harvesting.")
        return True
    except Exception as e:
        logger.error(f"Facebook analytics harvest failed: {e}", exc_info=True)
        return False

def run() -> bool:
    return harvest_facebook_stats()

if __name__ == "__main__":
    run()
