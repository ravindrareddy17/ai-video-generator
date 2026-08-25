import sys
import json
from pathlib import Path
from datetime import datetime
from groq import Groq

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from automation.database.connection import (
    get_youtube_conn, get_instagram_conn, get_facebook_conn, get_ai_learning_conn
)
from utils.config import get_groq_key, get_setting
from utils.logger import get_logger

logger = get_logger("ai.learning")

def analyze_platform_metrics(platform: str) -> dict:
    """Query separate platform databases and return top/low performing video lists."""
    videos_data = []
    
    if platform == "youtube":
        conn = get_youtube_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.title, MAX(a.views) as views, MAX(a.likes) as likes, MAX(a.comments) as comments
                FROM videos v
                LEFT JOIN analytics a ON v.id = a.video_id
                GROUP BY v.id ORDER BY views DESC
            """)
            videos_data = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
            
    elif platform == "instagram":
        conn = get_instagram_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.title, MAX(a.plays) as views, MAX(a.likes) as likes, MAX(a.comments) as comments
                FROM videos v
                LEFT JOIN analytics a ON v.id = a.video_id
                GROUP BY v.id ORDER BY views DESC
            """)
            videos_data = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
            
    elif platform == "facebook":
        conn = get_facebook_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.title, MAX(a.video_views) as views, MAX(a.likes) as likes, MAX(a.comments) as comments
                FROM videos v
                LEFT JOIN analytics a ON v.id = a.video_id
                GROUP BY v.id ORDER BY views DESC
            """)
            videos_data = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # Split into top and low performing lists
    top_list = []
    low_list = []
    
    if videos_data:
        # Sort by views (which are normalized across platforms as 'views')
        sorted_vids = sorted(videos_data, key=lambda x: x.get("views") or 0, reverse=True)
        top_list = sorted_vids[:5]
        low_list = sorted_vids[-5:] if len(sorted_vids) > 5 else []
        
    return {
        "top": top_list,
        "low": low_list
    }

def update_feedback_loops():
    """Compare predicted metrics with actual harvested metrics and calculate accuracy score."""
    logger.info("Running prediction vs reality feedback loop calibration...")
    try:
        ai_conn = get_ai_learning_conn()
        cursor = ai_conn.cursor()
        
        # Pull all completed predictions that don't have a feedback loop record yet
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT p.id, p.platform, p.expected_metric, p.target_value, p.date
            FROM predictions p
            LEFT JOIN feedback_loops f ON p.id = f.video_id
            WHERE f.id IS NULL AND p.date <= ?
        """, (today_str,))
        
        pending_predictions = [dict(row) for row in cursor.fetchall()]
        if not pending_predictions:
            logger.info("No pending predictions to calibrate in feedback loop.")
            ai_conn.close()
            return
            
        for pred in pending_predictions:
            pred_id = pred["id"]
            platform = pred["platform"]
            metric = pred["expected_metric"]
            predicted = pred["target_value"]
            date_val = pred["date"]
            
            actual_value = 0.0
            
            # Retrieve actual value from the corresponding platform database
            if platform == "youtube":
                try:
                    conn = get_youtube_conn()
                    c = conn.cursor()
                    if "subscribers" in metric.lower():
                        c.execute("SELECT MAX(subscribers) FROM monetization_snapshots")
                        res = c.fetchone()
                        actual_value = float(res[0]) if res and res[0] else 0.0
                    elif "watch" in metric.lower() or "hours" in metric.lower():
                        c.execute("SELECT MAX(watch_time) FROM monetization_snapshots")
                        res = c.fetchone()
                        actual_value = float(res[0]) if res and res[0] else 0.0
                    else:
                        c.execute("SELECT SUM(views) FROM analytics")
                        res = c.fetchone()
                        actual_value = float(res[0]) if res and res[0] else 0.0
                    conn.close()
                except Exception:
                    pass
            elif platform == "instagram":
                try:
                    conn = get_instagram_conn()
                    c = conn.cursor()
                    if "followers" in metric.lower():
                        c.execute("SELECT SUM(reach) FROM analytics")
                        res = c.fetchone()
                        actual_value = float(res[0]) if res and res[0] else 0.0
                    else:
                        c.execute("SELECT SUM(plays) FROM analytics")
                        res = c.fetchone()
                        actual_value = float(res[0]) if res and res[0] else 0.0
                    conn.close()
                except Exception:
                    pass
            elif platform == "facebook":
                try:
                    conn = get_facebook_conn()
                    c = conn.cursor()
                    if "followers" in metric.lower():
                        c.execute("SELECT SUM(reach) FROM analytics")
                        res = c.fetchone()
                        actual_value = float(res[0]) if res and res[0] else 0.0
                    else:
                        c.execute("SELECT SUM(video_views) FROM analytics")
                        res = c.fetchone()
                        actual_value = float(res[0]) if res and res[0] else 0.0
                    conn.close()
                except Exception:
                    pass
            
            # Calculate accuracy percentage
            if predicted > 0:
                deviation = abs(predicted - actual_value) / predicted
                accuracy = max(0.0, min(100.0, (1.0 - deviation) * 100.0))
            else:
                accuracy = 100.0 if actual_value == 0 else 0.0
                
            cursor.execute("""
                INSERT INTO feedback_loops (video_id, platform, date, metric_name, predicted_value, actual_value, accuracy_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pred_id, platform, date_val, metric, predicted, actual_value, accuracy))
            
        ai_conn.commit()
        ai_conn.close()
        logger.info(f"Feedback loop processed {len(pending_predictions)} prediction metrics.")
    except Exception as e:
        logger.error(f"Failed to update feedback loops: {e}")


def run_learning_engine() -> bool:
    """Continuously learns upload parameters and trending guidelines for each platform without mixing metrics."""
    logger.info("Initializing Centralized AI Learning Engine snapshot cycle...")
    
    # 1. Run accuracy loop calibration first
    update_feedback_loops()
    
    groq_key = get_groq_key()
    if not groq_key:
        logger.error("Groq API key not found. Skipping self-learning analysis.")
        return False
        
    client = Groq(api_key=groq_key)
    model = get_setting("llm", "learning_model", "llama-3.3-70b-versatile")
    
    insights = {}
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    # Query recent feedback accuracy metrics
    feedback_context = []
    try:
        ai_conn = get_ai_learning_conn()
        cursor = ai_conn.cursor()
        cursor.execute("""
            SELECT platform, metric_name, predicted_value, actual_value, accuracy_score, date
            FROM feedback_loops
            ORDER BY created_at DESC LIMIT 10
        """)
        feedback_context = [dict(row) for row in cursor.fetchall()]
        ai_conn.close()
    except Exception as fe:
        logger.warning(f"Could not load feedback logs context: {fe}")
    
    for platform in ["youtube", "facebook", "instagram", "combined"]:
        logger.info(f"Analyzing {platform} metrics independently...")
        
        # Aggregate performance data specifically for this platform
        if platform == "combined":
            yt_data = analyze_platform_metrics("youtube")
            fb_data = analyze_platform_metrics("facebook")
            ig_data = analyze_platform_metrics("instagram")
            top_vids = yt_data["top"] + fb_data["top"] + ig_data["top"]
            low_vids = yt_data["low"] + fb_data["low"] + ig_data["low"]
        else:
            p_data = analyze_platform_metrics(platform)
            top_vids = p_data["top"]
            low_vids = p_data["low"]

        # Call Groq LLM to formulate guidelines
        user_prompt = f"""
        You are the Brain of an Autonomous AI Social Media engine. Analyze the performance of recently published short-form video concepts for the platform '{platform}' and formulate optimizations.
        
        Top Performing Videos:
        {json.dumps(top_vids, indent=2)}
        
        Low Performing Videos:
        {json.dumps(low_vids, indent=2)}
        
        Recent Prediction vs Reality Accuracy Logs (Calibrate targets based on these discrepancies):
        {json.dumps(feedback_context, indent=2)}
        
        Analyze niche trends, watch metrics, and generate:
        1. High-interest niches to focus on (up to 4)
        2. Concepts/topics to avoid (low engagement) (up to 4)
        3. Pacing and video length guidelines (e.g. recommended duration)
        4. Viral hook guidelines
        5. Keywords that boost the recommendation algorithm
        
        Respond with ONLY a clean JSON object matching this schema:
        {{
            "high_interest_niches": ["niche1", "niche2"],
            "failed_concepts": ["concept1", "concept2"],
            "pacing_and_length_adjustments": "Text description of pacing adjustments",
            "viral_hook_guideline": "Text description of hook guidelines",
            "algorithm_boost_keywords": ["keyword1", "keyword2"]
        }}
        """
        
        try:
            chat_completion = call_groq_with_fallback(
                client=client,
                messages=[
                    {"role": "system", "content": "You are a database analytics learning model. Return JSON only."},
                    {"role": "user", "content": user_prompt}
                ],
                initial_model="qwen/qwen3.6-27b",
                temperature=0.2,
                max_tokens=1024
            )
            
            content_str = chat_completion.choices[0].message.content
            p_insights = extract_json_from_llm(content_str)
            insights[platform] = p_insights
            logger.info(f"Learned insights successfully for: {platform}")
            
            # Save learning snapshots and recommendations in sqlite
            try:
                ai_conn = get_ai_learning_conn()
                cursor = ai_conn.cursor()
                
                # 1. Save Recommendations
                cursor.execute("""
                    INSERT INTO recommendations (platform, date, category, advice, confidence_score)
                    VALUES (?, ?, 'niches', ?, 0.92)
                """, (platform, today_date, ", ".join(p_insights.get("high_interest_niches", []))))
                
                cursor.execute("""
                    INSERT INTO recommendations (platform, date, category, advice, confidence_score)
                    VALUES (?, ?, 'hooks', ?, 0.88)
                """, (platform, today_date, p_insights.get("viral_hook_guideline", "")))

                # 2. Save Learning Snapshot
                cursor.execute("""
                    INSERT INTO learning_snapshots (platform, date, niche, upload_hour, views_achieved, engagement, status)
                    VALUES (?, ?, ?, 18, 0, 0.0, 'completed')
                """, (platform, today_date, ", ".join(p_insights.get("high_interest_niches", []))[:250]))
                
                ai_conn.commit()
                ai_conn.close()
            except Exception as dbe:
                logger.warning(f"Could not write self-learning data to ai_learning.db: {dbe}")
                
        except Exception as e:
            logger.error(f"Groq analysis failed for platform {platform}: {e}")
            insights[platform] = {
                "high_interest_niches": ["Space & Science", "Accidental Discoveries", "Deep Physics"],
                "failed_concepts": [],
                "pacing_and_length_adjustments": "Keep video duration between 35-50 seconds for optimal audience retention.",
                "viral_hook_guideline": "Hook viewers within the first 3 seconds using active paradox titles.",
                "algorithm_boost_keywords": ["uncovered", "mind-blowing", "science", "secret"]
            }

    # Backward compatibility file support
    try:
        legacy_insights = dict(insights)
        combined = insights.get("combined", {})
        legacy_insights["high_interest_niches"] = combined.get("high_interest_niches", [])
        legacy_insights["failed_concepts"] = combined.get("failed_concepts", [])
        legacy_insights["pacing_and_length_adjustments"] = combined.get("pacing_and_length_adjustments", "")
        legacy_insights["viral_hook_guideline"] = combined.get("viral_hook_guideline", "")
        legacy_insights["algorithm_boost_keywords"] = combined.get("algorithm_boost_keywords", [])
        
        legacy_file = Path(__file__).resolve().parent.parent.parent / "data" / "self_learning_insights.json"
        with open(legacy_file, "w") as lf:
            json.dump(legacy_insights, lf, indent=2)
        logger.info(f"Centralized legacy file synced: {legacy_file}")
    except Exception as legacy_err:
        logger.warning(f"Failed to write fallback insights file: {legacy_err}")

    logger.info("Centralized AI learning cycle completed successfully.")
    return True

def run() -> bool:
    return run_learning_engine()

if __name__ == "__main__":
    run()
