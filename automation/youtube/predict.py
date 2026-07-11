import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from automation.database.connection import get_youtube_conn, get_ai_learning_conn
from utils.logger import get_logger

logger = get_logger("youtube.predict")

def generate_predictions() -> dict:
    """Analyze historical YouTube stats and write forecast predictions to ai_learning.db."""
    logger.info("Running YouTube prediction models...")
    
    conn = get_youtube_conn()
    try:
        cursor = conn.cursor()
        
        # 1. Fetch historical subscriber gains
        cursor.execute("""
            SELECT subscribers, date FROM monetization_snapshots 
            ORDER BY date DESC LIMIT 30
        """)
        snapshots = cursor.fetchall()
        
        # 2. Fetch video performance stats
        cursor.execute("""
            SELECT v.title, MAX(a.views) as views, MAX(a.likes) as likes, v.created_at
            FROM videos v
            LEFT JOIN analytics a ON v.id = a.video_id
            GROUP BY v.id
        """)
        videos = cursor.fetchall()
    finally:
        conn.close()
    
    # Default fallback metrics
    daily_subs_rate = 1.2
    current_subs = 57
    estimated_100k_date = "N/A"
    confidence = 85.0
    best_time = "18:30"
    best_duration = "45 seconds"
    best_topic = "Accidental Discoveries"
    revenue_forecast = 0.0

    if len(snapshots) >= 2:
        try:
            current_subs = snapshots[0]["subscribers"] or 57
            first_subs = snapshots[-1]["subscribers"] or 50
            days_diff = (datetime.strptime(snapshots[0]["date"], "%Y-%m-%d") - datetime.strptime(snapshots[-1]["date"], "%Y-%m-%d")).days or 1
            daily_subs_rate = max(0.1, (current_subs - first_subs) / float(days_diff))
        except Exception as e:
            logger.warning(f"Error computing subs rate: {e}")

    # Estimate milestone dates
    if daily_subs_rate > 0:
        subs_needed = 100000 - current_subs
        days_needed = int(subs_needed / daily_subs_rate)
        target_date = datetime.now() + timedelta(days=days_needed)
        estimated_100k_date = target_date.strftime("%B %Y")
        confidence = min(98.0, max(50.0, 95.0 - (days_needed / 365.0) * 5))
    
    # Analyze best performing topic from titles
    if videos:
        try:
            topic_views = {}
            for v in videos:
                title = v["title"].lower()
                views = v["views"] or 0
                topic = "General Space & Science"
                if "ai" in title or "robot" in title or "computer" in title:
                    topic = "Quantum AI & Computing"
                elif "fusion" in title or "cancer" in title or "seal" in title:
                    topic = "Accidental Discoveries"
                elif "star" in title or "universe" in title or "telescope" in title:
                    topic = "Exoplanets & Deep Space"
                
                topic_views[topic] = topic_views.get(topic, 0) + views
            
            if topic_views:
                best_topic = max(topic_views, key=topic_views.get)
        except Exception as e:
            logger.warning(f"Error computing best topic: {e}")

    # Write prediction results to ai_learning.db
    try:
        ai_conn = get_ai_learning_conn()
        try:
            cursor = ai_conn.cursor()
            today_date = datetime.now().strftime("%Y-%m-%d")
            
            # 1. Milestone Prediction
            cursor.execute("""
                INSERT OR REPLACE INTO predictions (platform, date, prediction_type, expected_metric, expected_date, target_value, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('youtube', today_date, 'milestone_100k', '100,000 Subscribers', estimated_100k_date, 100000.0, confidence / 100.0))
            
            # 2. Best performing topic prediction
            cursor.execute("""
                INSERT OR REPLACE INTO predictions (platform, date, prediction_type, expected_metric, expected_date, target_value, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('youtube', today_date, 'best_topic', best_topic, 'N/A', 0.0, 0.90))

            ai_conn.commit()
        finally:
            ai_conn.close()
        logger.info("Saved YouTube prediction calculations to ai_learning.db successfully.")
    except Exception as e:
        logger.error(f"Failed to save predictions: {e}")

    return {
        "daily_subs_rate": daily_subs_rate,
        "estimated_100k_date": estimated_100k_date,
        "confidence": confidence,
        "best_upload_time": best_time,
        "best_video_duration": best_duration,
        "best_performing_topic": best_topic,
        "revenue_forecast": revenue_forecast
    }

if __name__ == "__main__":
    preds = generate_predictions()
    print("YouTube Predictions Generated:", preds)
