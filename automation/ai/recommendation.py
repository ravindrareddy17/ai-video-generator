import sys
from pathlib import Path
from datetime import datetime

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from automation.database.connection import get_ai_learning_conn
from utils.logger import get_logger

logger = get_logger("ai.recommendation")

def get_latest_recommendations(platform: str) -> list[str]:
    """Retrieve list of generated recommendations from ai_learning.db."""
    conn = get_ai_learning_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT category, advice, confidence_score 
            FROM recommendations 
            WHERE platform = ? 
            ORDER BY id DESC LIMIT 5
        """, (platform,))
        rows = cursor.fetchall()
        return [f"({int(row['confidence_score'] * 100)}% Confidence) Category: {row['category'].title()} -> {row['advice']}" for row in rows]
    except Exception as e:
        logger.warning(f"Could not load recommendations for {platform}: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    for p in ["youtube", "facebook", "instagram", "combined"]:
        print(f"[{p.upper()} Recommendations]:", get_latest_recommendations(p))
