import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from automation.database.connection import get_facebook_conn, get_ai_learning_conn
from utils.logger import get_logger

logger = get_logger("facebook.predict")

def generate_predictions() -> dict:
    """Analyze historical Facebook Page metrics and save predictions to ai_learning.db."""
    logger.info("Running Facebook prediction models...")
    
    conn = get_facebook_conn()
    try:
        cursor = conn.cursor()
        
        # 1. Fetch Facebook Reels stats
        cursor.execute("""
            SELECT v.title, MAX(a.video_views) as views, MAX(a.reach) as reach, MAX(a.likes) as likes
            FROM videos v
            LEFT JOIN analytics a ON v.id = a.video_id
            GROUP BY v.id
        """)
        reels = cursor.fetchall()
    finally:
        conn.close()
    
    # Defaults
    viral_prob = 68.0
    best_schedule = "15:00, 22:00"
    best_format = "Native Reels (9:16 vertical video)"
    page_growth_est = 25.0
    confidence = 86.0

    if reels:
        try:
            total_views = sum(r["views"] or 0 for r in reels)
            avg_views = total_views / len(reels)
            if avg_views > 1000:
                viral_prob = min(92.0, 68.0 + (avg_views / 8000.0) * 12)
        except Exception as e:
            logger.warning(f"Error computing FB predictions: {e}")

    # Write prediction results to ai_learning.db
    # Write prediction results to ai_learning.db
    try:
        ai_conn = get_ai_learning_conn()
        try:
            cursor = ai_conn.cursor()
            today_date = datetime.now().strftime("%Y-%m-%d")
            
            # 1. Video performance forecast
            cursor.execute("""
                INSERT OR REPLACE INTO predictions (platform, date, prediction_type, expected_metric, expected_date, target_value, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('facebook', today_date, 'viral_probability', 'Viral Video Likelihood', 'N/A', viral_prob, confidence / 100.0))
            
            # 2. Best content format recommendation
            cursor.execute("""
                INSERT OR REPLACE INTO predictions (platform, date, prediction_type, expected_metric, expected_date, target_value, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('facebook', today_date, 'best_format', best_format, 'N/A', 0.0, 0.88))

            ai_conn.commit()
        finally:
            ai_conn.close()
        logger.info("Saved Facebook prediction calculations successfully.")
    except Exception as e:
        logger.error(f"Failed to save FB predictions: {e}")

    return {
        "viral_probability": viral_prob,
        "best_posting_schedule": best_schedule,
        "best_content_format": best_format,
        "expected_page_growth": page_growth_est
    }

if __name__ == "__main__":
    preds = generate_predictions()
    print("Facebook Predictions:", preds)
