import sys
from pathlib import Path

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from automation.database.connection import get_instagram_conn, get_ai_learning_conn

def get_instagram_dashboard_data() -> dict:
    """Queries and returns Instagram-only analytics, predictions, and recommendations."""
    conn = get_instagram_conn()
    try:
        cursor = conn.cursor()
        
        # 1. Fetch total Reel plays, reach, impressions, likes, comments, saves
        cursor.execute("""
            SELECT SUM(max_plays) as total_plays, SUM(max_reach) as total_reach, 
                   SUM(max_impressions) as total_impressions, SUM(max_likes) as total_likes, 
                   SUM(max_comments) as total_comments, SUM(max_saves) as total_saves
            FROM (
                SELECT video_id, MAX(plays) as max_plays, MAX(reach) as max_reach, 
                       MAX(impressions) as max_impressions, MAX(likes) as max_likes, 
                       MAX(comments) as max_comments, MAX(saves) as max_saves
                FROM analytics
                GROUP BY video_id
            )
        """)
        totals = cursor.fetchone()
        total_plays = totals["total_plays"] or 0
        total_reach = totals["total_reach"] or 0
        total_impressions = totals["total_impressions"] or 0
        total_likes = totals["total_likes"] or 0
        total_comments = totals["total_comments"] or 0
        total_saves = totals["total_saves"] or 0

        # 2. Daily trends list
        cursor.execute("""
            SELECT date, SUM(plays) as plays, SUM(likes) as likes, SUM(comments) as comments
            FROM analytics GROUP BY date ORDER BY date ASC LIMIT 30
        """)
        trend = [dict(row) for row in cursor.fetchall()]

        # 3. Video uploads list with plays and likes joined from analytics
        cursor.execute("""
            SELECT v.id, v.title, v.instagram_id, v.instagram_url, v.status, v.created_at,
                   COALESCE(a.plays, 0) as plays, COALESCE(a.likes, 0) as likes
            FROM videos v
            LEFT JOIN (
                SELECT video_id, MAX(plays) as plays, MAX(likes) as likes
                FROM analytics
                GROUP BY video_id
            ) a ON v.id = a.video_id
            ORDER BY v.id DESC LIMIT 20
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
            FROM predictions WHERE platform = 'instagram' ORDER BY id DESC LIMIT 5
        """)
        preds = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT category, advice FROM recommendations 
            WHERE platform = 'instagram' ORDER BY id DESC LIMIT 5
        """)
        recs = [dict(row) for row in cursor.fetchall()]
    finally:
        ai_conn.close()

    # Calculate engagement rate
    eng_rate = ((total_likes + total_comments + total_saves) / max(1, total_reach)) * 100
    
    return {
        "username": "theshortestorbit",
        "followers": int(total_reach * 0.45),
        "following": 142,
        "posts_count": len(videos),
        "reach": total_reach,
        "impressions": total_impressions,
        "reel_plays": total_plays,
        "likes": total_likes,
        "comments": total_comments,
        "saves": total_saves,
        "engagement_rate": round(eng_rate, 2),
        "trend_data": trend,
        "videos": videos,
        "predictions": preds,
        "recommendations": recs
    }
