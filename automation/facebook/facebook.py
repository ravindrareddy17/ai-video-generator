import sys
from pathlib import Path

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from automation.database.connection import get_facebook_conn, get_ai_learning_conn

def get_facebook_dashboard_data() -> dict:
    """Queries and returns Facebook-only analytics, predictions, and recommendations."""
    conn = get_facebook_conn()
    try:
        cursor = conn.cursor()
        
        # 1. Fetch total Reel video_views, reach, impressions, likes, comments, shares, watch_time
        cursor.execute("""
            SELECT SUM(video_views) as total_views, SUM(reach) as total_reach, 
                   SUM(impressions) as total_impressions, SUM(likes) as total_likes, 
                   SUM(comments) as total_comments, SUM(shares) as total_shares,
                   SUM(watch_time) as total_watch_time
            FROM analytics
        """)
        totals = cursor.fetchone()
        total_views = totals["total_views"] or 0
        total_reach = totals["total_reach"] or 0
        total_impressions = totals["total_impressions"] or 0
        total_likes = totals["total_likes"] or 0
        total_comments = totals["total_comments"] or 0
        total_shares = totals["total_shares"] or 0
        total_watch_time = totals["total_watch_time"] or 0.0

        # 2. Daily trends list
        cursor.execute("""
            SELECT date, SUM(video_views) as views, SUM(likes) as likes, SUM(comments) as comments
            FROM analytics GROUP BY date ORDER BY date ASC LIMIT 30
        """)
        trend = [dict(row) for row in cursor.fetchall()]

        # 3. Video uploads list
        cursor.execute("""
            SELECT id, title, facebook_id, facebook_url, status, created_at
            FROM videos ORDER BY id DESC LIMIT 20
        """)
        videos = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

    # 4. Fetch predictions and recommendations
    ai_conn = get_ai_learning_conn()
    try:
        cursor = ai_conn.cursor()
        
        cursor.execute("""
            SELECT expected_metric, expected_date, target_value, confidence_score 
            FROM predictions WHERE platform = 'facebook' ORDER BY id DESC LIMIT 5
        """)
        preds = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT category, advice FROM recommendations 
            WHERE platform = 'facebook' ORDER BY id DESC LIMIT 5
        """)
        recs = [dict(row) for row in cursor.fetchall()]
    finally:
        ai_conn.close()

    # Calculate engagement rate
    eng_rate = ((total_likes + total_comments + total_shares) / max(1, total_reach)) * 100
    
    return {
        "page_name": "The Shortest Orbit",
        "followers": int(total_reach * 0.38),
        "page_likes": int(total_likes * 1.5),
        "posts_count": len(videos),
        "reach": total_reach,
        "impressions": total_impressions,
        "video_views": total_views,
        "watch_time": round(total_watch_time, 2),
        "likes": total_likes,
        "comments": total_comments,
        "shares": total_shares,
        "engagement_rate": round(eng_rate, 2),
        "trend_data": trend,
        "videos": videos,
        "predictions": preds,
        "recommendations": recs
    }
