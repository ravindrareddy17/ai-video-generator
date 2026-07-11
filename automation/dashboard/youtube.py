import sys
import json
from pathlib import Path

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from automation.database.connection import get_youtube_conn, get_ai_learning_conn

def get_youtube_dashboard_data() -> dict:
    """Queries and returns YouTube-only analytics, predictions, and recommendations."""
    # 1. Fetch channel metadata from file (true real-time counts from API)
    subscribers = 0
    total_channel_views = None
    watch_hours_from_meta = None
    
    metadata_file = Path(__file__).resolve().parent.parent.parent / "data" / "channel_metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, "r") as f:
                meta = json.load(f)
                subscribers = meta.get("subscribers", 0)
                total_channel_views = meta.get("total_channel_views")
                watch_hours_from_meta = meta.get("watch_hours")
        except Exception:
            pass

    conn = get_youtube_conn()
    try:
        cursor = conn.cursor()
        
        # Query unique video views, likes, comments (avoiding snapshot double counting)
        cursor.execute("""
            SELECT SUM(max_views) as total_views, SUM(max_likes) as total_likes, SUM(max_comments) as total_comments
            FROM (
                SELECT video_id, MAX(views) as max_views, MAX(likes) as max_likes, MAX(comments) as max_comments
                FROM analytics
                GROUP BY video_id
            )
        """)
        totals = cursor.fetchone()
        db_views = totals["total_views"] or 0
        total_likes = totals["total_likes"] or 0
        total_comments = totals["total_comments"] or 0
        
        # Use live channel views if available, otherwise fallback to database
        final_views = total_channel_views if total_channel_views is not None else db_views
        
        # Load watch hours from metadata if available, otherwise calculate using consistent factor
        if watch_hours_from_meta is not None:
            watch_time = watch_hours_from_meta
        else:
            watch_time = round(final_views * 0.0044, 1)

        # 2. Daily trends list
        cursor.execute("""
            SELECT date, SUM(views) as views, SUM(likes) as likes, SUM(comments) as comments
            FROM analytics GROUP BY date ORDER BY date ASC LIMIT 30
        """)
        trend = [dict(row) for row in cursor.fetchall()]

        # 3. Video uploads list with views and likes joined from analytics
        cursor.execute("""
            SELECT v.id, v.title, v.youtube_id, v.status, v.created_at,
                   COALESCE(a.views, 0) as views, COALESCE(a.likes, 0) as likes
            FROM videos v
            LEFT JOIN (
                SELECT video_id, MAX(views) as views, MAX(likes) as likes
                FROM analytics
                GROUP BY video_id
            ) a ON v.id = a.video_id
            ORDER BY v.id DESC LIMIT 20
        """)
        videos = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

    # 4. Fetch predictions and recommendations from ai_learning.db
    ai_conn = get_ai_learning_conn()
    try:
        cursor = ai_conn.cursor()
        
        cursor.execute("""
            SELECT expected_metric, expected_date, target_value, confidence_score 
            FROM predictions WHERE platform = 'youtube' ORDER BY id DESC LIMIT 5
        """)
        preds = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT category, advice FROM recommendations 
            WHERE platform = 'youtube' ORDER BY id DESC LIMIT 5
        """)
        recs = [dict(row) for row in cursor.fetchall()]
    finally:
        ai_conn.close()

    # Default static details (revenue and milestone estimates)
    rpm = 0.12
    cpm = 0.25
    
    # YouTube monetization eligibility rules
    fan_funding_eligible = subscribers >= 500 and (final_views >= 3000000 or watch_time >= 3000)
    full_monetization_eligible = subscribers >= 1000 and (final_views >= 10000000 or watch_time >= 4000)
    
    if full_monetization_eligible:
        monetization_status = "Monetized"
        revenue = round((final_views / 1000.0) * rpm, 2)
    elif fan_funding_eligible:
        monetization_status = "Fan Funding Eligible"
        revenue = 0.00  # Not fully monetized yet
    else:
        monetization_status = "Not Monetized"
        revenue = 0.00  # Channel is not monetized - no revenue
    
    # Watch hours: YouTube Data API v3 does NOT provide watch hours.
    # Only the YouTube Analytics API (requires different OAuth scope) can give real data.
    # Don't show a fabricated estimate - show null so frontend can display "N/A".
    real_watch_hours = watch_hours_from_meta  # Will be None if not available
    
    return {
        "channel_name": "The Shortest Orbit",
        "subscribers": subscribers,
        "views": final_views,
        "watch_time": real_watch_hours,
        "likes": total_likes,
        "comments": total_comments,
        "rpm": rpm,
        "cpm": cpm,
        "revenue": revenue,
        "monetization_status": monetization_status,
        "trend_data": trend,
        "videos": videos,
        "predictions": preds,
        "recommendations": recs
    }
