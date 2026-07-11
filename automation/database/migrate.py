import sqlite3
import json
from pathlib import Path

# Set up paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OLD_DB_PATH = PROJECT_ROOT / "data" / "shortest_orbit_v3.db"

import sys
sys.path.insert(0, str(PROJECT_ROOT))
from automation.database.connection import (
    get_youtube_conn, get_instagram_conn, get_facebook_conn,
    get_automation_conn, get_ai_learning_conn, init_db
)

def migrate_data():
    if not OLD_DB_PATH.exists():
        print(f"Old database not found at {OLD_DB_PATH}. Skipping migration (will start fresh).")
        return

    print(f"Migrating data from {OLD_DB_PATH}...")
    init_db()

    old_conn = sqlite3.connect(OLD_DB_PATH)
    old_conn.row_factory = sqlite3.Row
    old_cursor = old_conn.cursor()

    # 1. Migrate Topics to automation.db
    print("Migrating topics...")
    topics_rows = old_cursor.execute("SELECT * FROM topics").fetchall()
    auto_conn = get_automation_conn()
    auto_cursor = auto_conn.cursor()
    for row in topics_rows:
        try:
            auto_cursor.execute("""
                INSERT OR IGNORE INTO topics (id, title, source, trend_score, engagement_potential, retention_potential, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (row["id"], row["title"], row["source"], row["trend_score"], row["engagement_potential"], row["retention_potential"], row["status"], row["created_at"]))
        except Exception as e:
            print(f"Topic error: {e}")
    auto_conn.commit()

    # 2. Migrate Videos to isolated databases
    print("Migrating videos...")
    videos_rows = old_cursor.execute("SELECT * FROM videos").fetchall()
    
    yt_conn = get_youtube_conn()
    yt_cursor = yt_conn.cursor()
    fb_conn = get_facebook_conn()
    fb_cursor = fb_conn.cursor()
    ig_conn = get_instagram_conn()
    ig_cursor = ig_conn.cursor()

    # We map old video IDs to platform-specific video IDs to correctly link analytics
    yt_video_map = {}
    fb_video_map = {}
    ig_video_map = {}

    for row in videos_rows:
        vid_id = row["id"]
        # YouTube Video
        if row["youtube_id"]:
            yt_cursor.execute("""
                INSERT INTO videos (title, topic_id, script, youtube_id, status, created_at, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (row["title"], row["topic_id"], row["script"], row["youtube_id"], row["status"], row["created_at"], row["uploaded_at"]))
            yt_video_map[vid_id] = yt_cursor.lastrowid
        
        # Facebook Video
        if row["facebook_id"] or row["facebook_url"]:
            fb_cursor.execute("""
                INSERT INTO videos (title, topic_id, script, facebook_id, facebook_url, status, created_at, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (row["title"], row["topic_id"], row["script"], row["facebook_id"], row["facebook_url"], row["status"], row["created_at"], row["uploaded_at"]))
            fb_video_map[vid_id] = fb_cursor.lastrowid
            
        # Instagram Video
        if row["instagram_id"] or row["instagram_url"]:
            ig_cursor.execute("""
                INSERT INTO videos (title, topic_id, script, instagram_id, instagram_url, status, created_at, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (row["title"], row["topic_id"], row["script"], row["instagram_id"], row["instagram_url"], row["status"], row["created_at"], row["uploaded_at"]))
            ig_video_map[vid_id] = ig_cursor.lastrowid

    yt_conn.commit()
    fb_conn.commit()
    ig_conn.commit()

    # 3. Migrate Hooks to automation.db
    print("Migrating hooks...")
    hooks_rows = old_cursor.execute("SELECT * FROM hooks").fetchall()
    for row in hooks_rows:
        auto_cursor.execute("""
            INSERT INTO hooks (id, video_id, text, score, selected)
            VALUES (?, ?, ?, ?, ?)
        """, (row["id"], row["video_id"], row["text"], row["score"], row["selected"]))
    auto_conn.commit()

    # 4. Migrate Analytics
    print("Migrating analytics...")
    analytics_rows = old_cursor.execute("SELECT * FROM analytics").fetchall()
    for row in analytics_rows:
        old_vid = row["video_id"]
        
        # YouTube Analytics
        if old_vid in yt_video_map:
            new_yt_vid = yt_video_map[old_vid]
            yt_cursor.execute("""
                INSERT INTO analytics (video_id, date, views, likes, comments, shares, subscribers_gained, retention_data, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_yt_vid, row["date"], row["views"], row["likes"], row["comments"], row["shares"], row["subscribers_gained"], row["retention_data"], row["synced_at"]))

        # Facebook Analytics
        if old_vid in fb_video_map:
            new_fb_vid = fb_video_map[old_vid]
            fb_cursor.execute("""
                INSERT INTO analytics (video_id, date, reach, impressions, video_views, watch_time, likes, reactions, comments, shares, engagement_rate, audience_growth, synced_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, 0, 0.0, 0, ?)
            """, (new_fb_vid, row["date"], row["fb_views"], row["fb_views"] * 2, row["fb_views"], row["fb_likes"], row["fb_likes"], row["fb_comments"], row["synced_at"]))

        # Instagram Analytics
        if old_vid in ig_video_map:
            new_ig_vid = ig_video_map[old_vid]
            ig_cursor.execute("""
                INSERT INTO analytics (video_id, date, reach, impressions, profile_visits, plays, likes, comments, shares, saves, engagement_rate, accounts_reached, follower_growth, synced_at)
                VALUES (?, ?, ?, ?, 0, ?, ?, ?, 0, 0, 0.0, ?, 0, ?)
            """, (new_ig_vid, row["date"], row["ig_views"], row["ig_views"] * 2, row["ig_views"], row["ig_likes"], row["ig_comments"], row["ig_views"], row["synced_at"]))

    yt_conn.commit()
    fb_conn.commit()
    ig_conn.commit()

    # 5. Migrate Monetization Snapshots & Targets to youtube.db
    print("Migrating monetization records...")
    mon_snapshots = old_cursor.execute("SELECT * FROM monetization_snapshots").fetchall()
    for row in mon_snapshots:
        try:
            yt_cursor.execute("""
                INSERT OR IGNORE INTO monetization_snapshots (id, date, subscribers, shorts_views, watch_hours, uploads_90_days, progress_percentage, readiness_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (row["id"], row["date"], row["subscribers"], row["shorts_views"], row["watch_hours"], row["uploads_90_days"], row["progress_percentage"], row["readiness_score"], row["created_at"]))
        except Exception as e:
            print(f"Monetization snapshot error: {e}")
            
    mon_targets = old_cursor.execute("SELECT * FROM daily_monetization_targets").fetchall()
    for row in mon_targets:
        try:
            yt_cursor.execute("""
                INSERT OR IGNORE INTO daily_monetization_targets (id, date, remaining_days, subs_needed_per_day, views_needed_per_day, hours_needed_per_day, subs_today, views_today, hours_today, subs_status, views_status, hours_status, ai_recommendation, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (row["id"], row["date"], row["remaining_days"], row["subs_needed_per_day"], row["views_needed_per_day"], row["hours_needed_per_day"], row["subs_today"], row["views_today"], row["hours_today"], row["subs_status"], row["views_status"], row["hours_status"], row["ai_recommendation"], row["created_at"]))
        except Exception as e:
            print(f"Monetization target error: {e}")
            
    yt_conn.commit()

    # 6. Parse and seed Centralized AI recommendations into ai_learning.db
    print("Seeding Centralized AI learning databases...")
    insights_file = PROJECT_ROOT / "data" / "self_learning_insights.json"
    if insights_file.exists():
        try:
            with open(insights_file, "r") as f:
                insights = json.load(f)
            
            ai_conn = get_ai_learning_conn()
            ai_cursor = ai_conn.cursor()
            
            for platform in ["youtube", "facebook", "instagram", "combined"]:
                p_data = insights.get(platform, {})
                if p_data:
                    # Seed niche recommendation
                    niches = p_data.get("high_interest_niches", [])
                    if niches:
                        advice = f"Focus niches: {', '.join(niches)}"
                        ai_cursor.execute("""
                            INSERT INTO recommendations (platform, date, category, advice, confidence_score)
                            VALUES (?, date('now'), 'niches', ?, 0.9)
                        """, (platform, advice))
                    
                    # Seed upload predictions
                    pacing = p_data.get("pacing_and_length_adjustments", "")
                    if pacing:
                        ai_cursor.execute("""
                            INSERT INTO predictions (platform, date, prediction_type, expected_metric, expected_date, target_value, confidence_score)
                            VALUES (?, date('now'), 'pacing', ?, 'N/A', 0.0, 0.85)
                        """, (platform, pacing))
                        
            ai_conn.commit()
            ai_conn.close()
        except Exception as e:
            print(f"AI seed error: {e}")

    old_conn.close()
    yt_conn.close()
    fb_conn.close()
    ig_conn.close()
    auto_conn.close()

    print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_data()
