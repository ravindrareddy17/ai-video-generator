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

def query_platform_performance(cursor, view_col: str, like_col: str, comment_col: str, id_col: str = None) -> dict:
    """Helper to query top and low performing videos for a specific platform or combined views."""
    where_clause = f"WHERE v.{id_col} IS NOT NULL" if id_col else ""
    
    # Query top videos
    cursor.execute(f"""
        SELECT v.id, v.title, v.script, MAX({view_col}) as total_views, MAX({like_col}) as total_likes, MAX({comment_col}) as total_comments, a.retention_data
        FROM videos v
        JOIN analytics a ON v.id = a.video_id
        {where_clause}
        GROUP BY v.id
        ORDER BY total_views DESC
        LIMIT 5
    """)
    top_videos = cursor.fetchall()
    
    # Query low videos
    cursor.execute(f"""
        SELECT v.id, v.title, MAX({view_col}) as total_views
        FROM videos v
        JOIN analytics a ON v.id = a.video_id
        {where_clause}
        GROUP BY v.id
        ORDER BY total_views ASC
        LIMIT 5
    """)
    low_videos = cursor.fetchall()
    
    return {
        "top_performing": [
            {
                "title": row["title"],
                "script": (row["script"] or "")[:200] + "...",
                "views": row["total_views"] or 0,
                "likes": row["total_likes"] or 0,
                "comments_count": row["total_comments"] or 0,
                "viewer_comments_feedback": json.loads(row["retention_data"]) if row["retention_data"] else []
            } for row in top_videos
        ],
        "under_performing": [
            {
                "title": row["title"],
                "views": row["total_views"] or 0
            } for row in low_videos
        ]
    }

def run_self_learning_loop() -> bool:
    """Analyze historical multi-platform analytics in SQLite to optimize topic selection and prompts."""
    logger.info("Executing Multi-Platform Self-Learning Engine updates...")
    
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Check if we have any video records at all
            cursor.execute("SELECT COUNT(*) FROM videos")
            total_videos_count = cursor.fetchone()[0]
            if total_videos_count == 0:
                logger.info("No video records in database yet. Skipping self-learning.")
                return True
                
            # 1. Retrieve performance data for YouTube, Facebook, Instagram, and Combined
            youtube_data = query_platform_performance(cursor, "a.views", "a.likes", "a.comments", "youtube_id")
            facebook_data = query_platform_performance(cursor, "a.fb_views", "a.fb_likes", "a.fb_comments", "facebook_id")
            instagram_data = query_platform_performance(cursor, "a.ig_views", "a.ig_likes", "a.ig_comments", "instagram_id")
            combined_data = query_platform_performance(cursor, "(a.views + a.fb_views + a.ig_views)", "(a.likes + a.fb_likes + a.ig_likes)", "(a.comments + a.fb_comments + a.ig_comments)")
        finally:
            conn.close()
        
        # Structure multi-platform performance data for Groq
        perf_data = {
            "youtube": youtube_data,
            "facebook": facebook_data,
            "instagram": instagram_data,
            "combined": combined_data
        }
        
        # 2. Call Groq to formulate new learning insights
        api_key = get_groq_key()
        model = get_setting('llm', 'model', 'qwen/qwen3.6-27b')
        client = Groq(api_key=api_key)
        
        system_prompt = (
            "You are an expert audience analyst and data scientist for multi-platform short-form content. "
            "You analyze performance data across YouTube Shorts, Facebook Reels, Instagram Reels, and combined metrics.\n"
            "Formulate specific, platform-appropriate insights for each channel/platform based on views, engagement, and user feedback.\n\n"
            "Respond in JSON format with this exact structure:\n"
            "{\n"
            "  \"youtube\": {\n"
            "    \"high_interest_niches\": [\"Niche 1\", \"Niche 2\"],\n"
            "    \"failed_concepts\": [\"Avoid X\", \"Avoid Y\"],\n"
            "    \"pacing_and_length_adjustments\": \"recommendation...\",\n"
            "    \"viral_hook_guideline\": \"guideline...\",\n"
            "    \"algorithm_boost_keywords\": [\"Keyword 1\", \"Keyword 2\"]\n"
            "  },\n"
            "  \"facebook\": {\n"
            "    \"high_interest_niches\": [\"Niche 1\", \"Niche 2\"],\n"
            "    \"failed_concepts\": [\"Avoid X\", \"Avoid Y\"],\n"
            "    \"pacing_and_length_adjustments\": \"recommendation...\",\n"
            "    \"viral_hook_guideline\": \"guideline...\",\n"
            "    \"algorithm_boost_keywords\": [\"Keyword 1\", \"Keyword 2\"]\n"
            "  },\n"
            "  \"instagram\": {\n"
            "    \"high_interest_niches\": [\"Niche 1\", \"Niche 2\"],\n"
            "    \"failed_concepts\": [\"Avoid X\", \"Avoid Y\"],\n"
            "    \"pacing_and_length_adjustments\": \"recommendation...\",\n"
            "    \"viral_hook_guideline\": \"guideline...\",\n"
            "    \"algorithm_boost_keywords\": [\"Keyword 1\", \"Keyword 2\"]\n"
            "  },\n"
            "  \"combined\": {\n"
            "    \"high_interest_niches\": [\"Niche 1\", \"Niche 2\"],\n"
            "    \"failed_concepts\": [\"Avoid X\", \"Avoid Y\"],\n"
            "    \"pacing_and_length_adjustments\": \"recommendation...\",\n"
            "    \"viral_hook_guideline\": \"guideline...\",\n"
            "    \"algorithm_boost_keywords\": [\"Keyword 1\", \"Keyword 2\"]\n"
            "  }\n"
            "}"
        )
        
        user_prompt = f"Analyze this multi-platform performance data and output separate platform parameters:\n\n{json.dumps(perf_data, indent=2)}"
        
        logger.info("Calling Groq to analyze multi-platform performance analytics...")
        from utils.config import call_groq_with_fallback
        from utils.helpers import extract_json_from_llm
        completion = call_groq_with_fallback(
            client=client,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            initial_model=model,
            temperature=0.3
        )
        insights = extract_json_from_llm(completion.choices[0].message.content)
        
        # Add root-level keys for backwards compatibility using the combined channel insights
        combined = insights.get("combined", {})
        insights["high_interest_niches"] = combined.get("high_interest_niches", [])
        insights["failed_concepts"] = combined.get("failed_concepts", [])
        insights["pacing_and_length_adjustments"] = combined.get("pacing_and_length_adjustments", "")
        insights["viral_hook_guideline"] = combined.get("viral_hook_guideline", "")
        insights["algorithm_boost_keywords"] = combined.get("algorithm_boost_keywords", [])
        
        # Save insights as JSON
        with open(INSIGHTS_FILE, 'w') as f:
            json.dump(insights, f, indent=2)
            
        logger.info(f"Self-learning insights saved to: {INSIGHTS_FILE}")
        logger.info(f"Identified high-interest combined niches: {insights.get('high_interest_niches')}")
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
