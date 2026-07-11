import sys
import requests
from pathlib import Path
from datetime import datetime

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from automation.database.connection import get_instagram_conn
from python.meta_auth import get_valid_token, load_credentials
from utils.logger import get_logger

logger = get_logger("instagram.analytics")

def harvest_instagram_stats() -> bool:
    """Harvest performance metrics (plays, reach, likes, comments, saves) for all published Reels."""
    logger.info("Starting Instagram analytics harvesting...")
    
    try:
        creds = load_credentials()
        ig_id = creds.get("instagram_id")
        if not ig_id:
            logger.error("Instagram account ID missing. Skipping Instagram harvest.")
            return False
            
        token = get_valid_token()
        
        conn = get_instagram_conn()
        try:
            cursor = conn.cursor()
        
            # 1. Fetch Instagram follower statistics
            try:
                url = f"https://graph.facebook.com/v25.0/{ig_id}"
                params = {
                    "fields": "followers_count,media_count",
                    "access_token": token
                }
                response = requests.get(url, params=params, timeout=60)
                res_data = response.json()
                followers = res_data.get("followers_count", 0)
                logger.info(f"Instagram followers: {followers}")
            except Exception as fe:
                logger.warning(f"Could not fetch Instagram followers: {fe}")
                followers = 0
            
            # 2. Get tracked Instagram Reels
            cursor.execute("SELECT id, instagram_id, title FROM videos WHERE instagram_id IS NOT NULL")
            videos = cursor.fetchall()
        
            today_date = datetime.now().strftime("%Y-%m-%d")
        
            for video in videos:
                sqlite_video_id = video["id"]
                ig_media_id = video["instagram_id"]
            
                likes = 0
                comments = 0
                reach = 0
                impressions = 0
                plays = 0
                saves = 0
                shares = 0
            
                # Fetch Likes and Comments counts
                try:
                    url = f"https://graph.facebook.com/v25.0/{ig_media_id}"
                    params = {
                        "fields": "like_count,comments_count",
                        "access_token": token
                    }
                    res = requests.get(url, params=params, timeout=60).json()
                    likes = res.get("like_count", 0)
                    comments = res.get("comments_count", 0)
                except Exception as e:
                    logger.warning(f"Could not fetch likes/comments for IG media {ig_media_id}: {e}")
                
                # Fetch Reels insights (metric = plays, reach, impressions, saved, shares)
                try:
                    url = f"https://graph.facebook.com/v25.0/{ig_media_id}/insights"
                    params = {
                        "metric": "plays,reach,impressions,saved,shares",
                        "access_token": token
                    }
                    res = requests.get(url, params=params, timeout=60).json()
                    if "data" in res:
                        for metric in res["data"]:
                            name = metric.get("name")
                            val = metric.get("values", [{}])[0].get("value", 0)
                            if name == "plays":
                                plays = val
                            elif name == "reach":
                                reach = val
                            elif name == "impressions":
                                impressions = val
                            elif name == "saved":
                                saves = val
                            elif name == "shares":
                                shares = val
                except Exception as e:
                    logger.warning(f"Could not fetch insights for IG media {ig_media_id}: {e}")

                # Compute engagement rate
                total_eng = likes + comments + saves + shares
                engagement_rate = (total_eng / max(1, reach)) * 100
            
                # Update analytics table in instagram.db
                cursor.execute("""
                    SELECT id FROM analytics 
                    WHERE video_id = ? AND date = ?
                """, (sqlite_video_id, today_date))
                existing = cursor.fetchone()
            
                if existing:
                    cursor.execute("""
                        UPDATE analytics 
                        SET reach = ?, impressions = ?, plays = ?, likes = ?, comments = ?, shares = ?, saves = ?, engagement_rate = ?
                        WHERE id = ?
                    """, (reach, impressions, plays, likes, comments, shares, saves, engagement_rate, existing[0]))
                else:
                    cursor.execute("""
                        INSERT INTO analytics (video_id, date, reach, impressions, plays, likes, comments, shares, saves, engagement_rate, follower_growth)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (sqlite_video_id, today_date, reach, impressions, plays, likes, comments, shares, saves, engagement_rate))
                
                logger.info(f"Synced Instagram stats for Reel '{video['title'][:40]}...': Plays: {plays} | Reach: {reach} | Likes: {likes}")
            
            conn.commit()
        finally:
            conn.close()
        logger.info("Successfully completed Instagram analytics harvesting.")
        return True
    except Exception as e:
        logger.error(f"Instagram analytics harvest failed: {e}", exc_info=True)
        return False

def run() -> bool:
    return harvest_instagram_stats()

if __name__ == "__main__":
    run()
