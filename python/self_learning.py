import sys
import json
from pathlib import Path
from groq import Groq

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.database import get_connection
from utils.paths import DATA_DIR
from utils.config import get_groq_key, get_setting
from utils.logger import get_logger

logger = get_logger(__name__)

INSIGHTS_FILE = DATA_DIR / "self_learning_insights.json"

def run_self_learning_loop() -> bool:
    """Analyze historical YouTube analytics in SQLite to optimize topic selection and prompts."""
    logger.info("Executing Self-Learning Engine updates...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Query top performing videos based on views, likes, and comments
        cursor.execute("""
            SELECT v.id, v.title, v.script, MAX(a.views) as total_views, MAX(a.likes) as total_likes, MAX(a.comments) as total_comments, a.retention_data
            FROM videos v
            JOIN analytics a ON v.id = a.video_id
            GROUP BY v.id
            ORDER BY total_views DESC
            LIMIT 10
        """)
        top_videos = cursor.fetchall()
        
        # Query recently failed/underperforming videos (lowest views)
        cursor.execute("""
            SELECT v.id, v.title, MAX(a.views) as total_views
            FROM videos v
            JOIN analytics a ON v.id = a.video_id
            GROUP BY v.id
            ORDER BY total_views ASC
            LIMIT 10
        """)
        low_videos = cursor.fetchall()
        conn.close()
        
        if not top_videos:
            logger.info("Not enough video analytics data to execute self-learning yet.")
            return True
            
        # Structure the data to pass to Groq
        perf_data = {
            "top_performing": [
                {
                    "title": row["title"],
                    "script": (row["script"] or "")[:200] + "...",
                    "views": row["total_views"],
                    "likes": row["total_likes"],
                    "comments_count": row["total_comments"],
                    "viewer_comments_feedback": json.loads(row["retention_data"]) if row["retention_data"] else []
                } for row in top_videos
            ],
            "under_performing": [
                {
                    "title": row["title"],
                    "views": row["total_views"]
                } for row in low_videos
            ]
        }
        
        # 2. Call Groq to formulate new learning insights
        api_key = get_groq_key()
        model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
        client = Groq(api_key=api_key)
        
        system_prompt = (
            "You are an expert audience analyst and data scientist for YouTube Shorts.\n"
            "Your task is to review historical channel performance data (successful vs underperforming topics) "
            "along with actual user feedback comments in 'viewer_comments_feedback'.\n"
            "Read comments carefully: if viewers complain about speed, topic, voice, or express high interest in certain concepts/subtopics, "
            "incorporate that directly into failed concepts, pacing adjustments, and algorithm boost keywords.\n\n"
            "Respond in JSON format with this structure:\n"
            "{\n"
            "  \"high_interest_niches\": [\"Niche 1\", \"Niche 2\"],\n"
            "  \"failed_concepts\": [\"Avoid X\", \"Avoid Y\"],\n"
            "  \"pacing_and_length_adjustments\": \"1 sentence recommendation...\",\n"
            "  \"viral_hook_guideline\": \"1 sentence guideline for copywriters...\",\n"
            "  \"algorithm_boost_keywords\": [\"Keyword 1\", \"Keyword 2\"]\n"
            "}"
        )
        
        user_prompt = f"Analyze this performance data and output optimization parameters:\n\n{json.dumps(perf_data, indent=2)}"
        
        logger.info("Calling Groq to analyze performance analytics...")
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        insights = json.loads(completion.choices[0].message.content)
        
        # Save insights as JSON
        with open(INSIGHTS_FILE, 'w') as f:
            json.dump(insights, f, indent=2)
            
        logger.info(f"Self-learning insights saved to: {INSIGHTS_FILE}")
        logger.info(f"Identified high-interest niches: {insights.get('high_interest_niches')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed executing self-learning loop: {e}", exc_info=True)
        return False

def run() -> bool:
    """Orchestrates Step 12 of the pipeline."""
    logger.info("=== STEP 12: EXECUTE SELF-LEARNING ENGINE ===")
    return run_self_learning_loop()

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
