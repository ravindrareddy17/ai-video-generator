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
        # 1. Fetch channel's uploads playlist ID and subscriber count statistics
        channels_response = youtube.channels().list(mine=True, part="contentDetails,statistics").execute()
        if not channels_response.get("items"):
            logger.error("No channel found for current credentials.")
            return False
            
        uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Extract subscriber count and total channel views
        stats = channels_response["items"][0].get("statistics", {})
        subscribers = int(stats.get("subscriberCount", 0))
        total_channel_views = int(stats.get("viewCount", 0))
        
        # Save channel metadata
        metadata_file = Path(__file__).resolve().parent.parent / "data" / "channel_metadata.json"
        try:
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                except Exception:
                    pass
            metadata["subscribers"] = subscribers
            metadata["total_channel_views"] = total_channel_views
            # Note: watch_hours is NOT available via YouTube Data API v3
            # It requires YouTube Analytics API. Don't store a fake estimate.
            if "watch_hours" in metadata:
                del metadata["watch_hours"]
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved channel subscribers: {subscribers}, views: {total_channel_views}")
        except Exception as me:
            logger.warning(f"Could not save channel metadata: {me}")
        
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
            published_at_raw = item["snippet"].get("publishedAt", "")
            published_at = published_at_raw.replace("T", " ").replace("Z", "")[:19]
            video_map[video_id] = {
                "title": title,
                "published_at": published_at
            }
            
        video_ids = list(video_map.keys())
        
        # 3. Query video statistics in batches of 50
        stats_response = youtube.videos().list(
            id=",".join(video_ids),
            part="statistics"
        ).execute()
        
        # Pre-cache comment threads from YouTube to avoid database locking during network requests
        video_comments = {}
        for video_stat in stats_response.get("items", []):
            video_id = video_stat["id"]
            stats = video_stat.get("statistics", {})
            comments = int(stats.get("commentCount", 0))
            comment_texts = []
            if comments > 0:
                try:
                    comments_response = youtube.commentThreads().list(
                        videoId=video_id,
                        part="snippet",
                        maxResults=5,
                        textFormat="plainText"
                    ).execute()
                    for c_item in comments_response.get("items", []):
                        top_comment = c_item["snippet"]["topLevelComment"]["snippet"]
                        comment_texts.append(top_comment["textDisplay"])
                except Exception as ce:
                    logger.warning(f"Could not fetch comments for video {video_id}: {ce}")
            video_comments[video_id] = comment_texts

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
                video_info = video_map.get(video_id, {})
                title = video_info.get("title", "Unknown Title")
                published_at = video_info.get("published_at", today_date + " 00:00:00")
                cursor.execute("""
                    INSERT INTO videos (title, youtube_id, status, created_at)
                    VALUES (?, ?, ?, ?)
                """, (title, video_id, "uploaded", published_at))
                sqlite_video_id = cursor.lastrowid
                
            comment_texts = video_comments.get(video_id, [])
            retention_json = json.dumps(comment_texts)

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
                    SET views = ?, likes = ?, comments = ?, retention_data = ?
                    WHERE id = ?
                """, (views, likes, comments, retention_json, existing_row[0]))
            else:
                cursor.execute("""
                    INSERT INTO analytics (video_id, date, views, likes, comments, retention_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sqlite_video_id, today_date, views, likes, comments, retention_json))
                
            logger.info(f"Synced stats and comments for video '{video_map.get(video_id, {}).get('title', '')[:40]}...': Views: {views} | Likes: {likes} | Comments: {comments}")
            
        # Log a daily snapshot of monetization progress if it doesn't exist yet
        try:
            # Query rolling 90-day uploads
            cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'uploaded' AND datetime(created_at) >= datetime('now', '-90 days')")
            uploads_90 = cursor.fetchone()[0]
            
            # Watch hours estimate
            estimated_watch_hours = round(total_channel_views * 0.0044, 1)
            
            # Progress percentages
            fan_funding_subs_pct = min(100.0, (subscribers / 500.0) * 100.0)
            fan_funding_uploads_pct = min(100.0, (uploads_90 / 3.0) * 100.0)
            views_3m_pct = (total_channel_views / 3000000.0) * 100.0
            wh_3k_pct = (estimated_watch_hours / 3000.0) * 100.0
            fan_funding_views_pct = min(100.0, max(views_3m_pct, wh_3k_pct))
            fan_funding_progress = round(min(100.0, (fan_funding_subs_pct + fan_funding_uploads_pct + fan_funding_views_pct) / 3.0), 1)
            
            full_subs_pct = min(100.0, (subscribers / 1000.0) * 100.0)
            views_10m_pct = (total_channel_views / 10000000.0) * 100.0
            wh_4k_pct = (estimated_watch_hours / 4000.0) * 100.0
            full_views_pct = min(100.0, max(views_10m_pct, wh_4k_pct))
            full_progress = round(min(100.0, (full_subs_pct + full_views_pct) / 2.0), 1)
            
            readiness_score = int(round((fan_funding_progress + full_progress) / 2.0))

            cursor.execute("SELECT id FROM monetization_snapshots WHERE date = ?", (today_date,))
            existing_snapshot = cursor.fetchone()
            if existing_snapshot:
                cursor.execute("""
                    UPDATE monetization_snapshots
                    SET subscribers = ?, shorts_views = ?, watch_hours = ?, uploads_90_days = ?, progress_percentage = ?, readiness_score = ?
                    WHERE id = ?
                """, (
                    subscribers,
                    total_channel_views,
                    estimated_watch_hours,
                    uploads_90,
                    fan_funding_progress,
                    readiness_score,
                    existing_snapshot[0]
                ))
                logger.info(f"Updated daily monetization snapshot for {today_date} (Readiness: {readiness_score}%)")
            else:
                cursor.execute("""
                    INSERT INTO monetization_snapshots (date, subscribers, shorts_views, watch_hours, uploads_90_days, progress_percentage, readiness_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    today_date,
                    subscribers,
                    total_channel_views,
                    estimated_watch_hours,
                    uploads_90,
                    fan_funding_progress,
                    readiness_score
                ))
                logger.info(f"Logged daily monetization snapshot for {today_date} (Readiness: {readiness_score}%)")
        except Exception as se:
            logger.warning(f"Failed to log monetization snapshot: {se}", exc_info=True)
            
        # --- Harvest Meta Stats (Facebook & Instagram) -------------------
        try:
            from python import meta_auth
            from utils.config import get_facebook_page_id, get_instagram_account_id
            import requests

            token = meta_auth.get_valid_token()
            if token:
                # Facebook
                fb_page_id = get_facebook_page_id()
                if fb_page_id:
                    logger.info("Harvesting Facebook Reels analytics...")
                    cursor.execute("SELECT id, facebook_id FROM videos WHERE facebook_id IS NOT NULL")
                    fb_videos = cursor.fetchall()
                    for row in fb_videos:
                        video_id, fb_id = row[0], row[1]
                        try:
                            resp = requests.get(
                                f"https://graph.facebook.com/v25.0/{fb_id}",
                                params={
                                    "fields": "views,likes.summary(true).limit(0),comments.summary(true).limit(0)",
                                    "access_token": token
                                },
                                timeout=15
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                fb_views = data.get("views", 0)
                                fb_likes = data.get("likes", {}).get("summary", {}).get("total_count", 0)
                                fb_comments = data.get("comments", {}).get("summary", {}).get("total_count", 0)
                                
                                cursor.execute("SELECT id FROM analytics WHERE video_id = ? AND date = ?", (video_id, today_date))
                                existing = cursor.fetchone()
                                if existing:
                                    cursor.execute("""
                                        UPDATE analytics SET fb_views = ?, fb_likes = ?, fb_comments = ?
                                        WHERE id = ?
                                    """, (fb_views, fb_likes, fb_comments, existing[0]))
                                else:
                                    cursor.execute("""
                                        INSERT INTO analytics (video_id, date, fb_views, fb_likes, fb_comments)
                                        VALUES (?, ?, ?, ?, ?)
                                    """, (video_id, today_date, fb_views, fb_likes, fb_comments))
                                logger.info(f"Facebook Reels stats synced for video ID {video_id}: Views: {fb_views} | Likes: {fb_likes} | Comments: {fb_comments}")
                        except Exception as fe:
                            logger.warning(f"Failed to sync Facebook stats for video ID {video_id}: {fe}")
                
                # Instagram
                ig_acc_id = get_instagram_account_id()
                if ig_acc_id:
                    logger.info("Harvesting Instagram Reels analytics...")
                    cursor.execute("SELECT id, instagram_id FROM videos WHERE instagram_id IS NOT NULL")
                    ig_videos = cursor.fetchall()
                    for row in ig_videos:
                        video_id, ig_id = row[0], row[1]
                        try:
                            # Base stats (likes, comments)
                            resp = requests.get(
                                f"https://graph.facebook.com/v25.0/{ig_id}",
                                params={
                                    "fields": "like_count,comments_count",
                                    "access_token": token
                                },
                                timeout=15
                            )
                            # Insights stats (views/plays)
                            ig_views = 0
                            try:
                                insights_resp = requests.get(
                                    f"https://graph.facebook.com/v25.0/{ig_id}/insights",
                                    params={
                                        "metric": "plays",
                                        "access_token": token
                                    },
                                    timeout=15
                                )
                                if insights_resp.status_code == 200:
                                    insights_data = insights_resp.json()
                                    for item in insights_data.get("data", []):
                                        if item.get("name") == "plays":
                                            ig_views = item.get("values", [{}])[0].get("value", 0)
                            except Exception:
                                pass

                            if resp.status_code == 200:
                                data = resp.json()
                                ig_likes = data.get("like_count", 0)
                                ig_comments = data.get("comments_count", 0)
                                
                                cursor.execute("SELECT id FROM analytics WHERE video_id = ? AND date = ?", (video_id, today_date))
                                existing = cursor.fetchone()
                                if existing:
                                    cursor.execute("""
                                        UPDATE analytics SET ig_views = ?, ig_likes = ?, ig_comments = ?
                                        WHERE id = ?
                                    """, (ig_views, ig_likes, ig_comments, existing[0]))
                                else:
                                    cursor.execute("""
                                        INSERT INTO analytics (video_id, date, ig_views, ig_likes, ig_comments)
                                        VALUES (?, ?, ?, ?, ?)
                                    """, (video_id, today_date, ig_views, ig_likes, ig_comments))
                                logger.info(f"Instagram Reels stats synced for video ID {video_id}: Views: {ig_views} | Likes: {ig_likes} | Comments: {ig_comments}")
                        except Exception as ie:
                            logger.warning(f"Failed to sync Instagram stats for video ID {video_id}: {ie}")
        except Exception as me:
            logger.warning(f"Could not complete Meta stats harvest: {me}")
            
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
