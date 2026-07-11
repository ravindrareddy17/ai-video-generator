import sys
from pathlib import Path

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from automation.database.connection import get_ai_learning_conn
from utils.logger import get_logger

logger = get_logger("ai.prediction")

def compute_confidence(days_projected: int, base_accuracy: float = 0.95) -> float:
    """Helper function to calculate decay-based prediction confidence score."""
    # Decay confidence score by 0.5% per projected day out
    decay = days_projected * 0.005
    return max(0.50, min(1.0, base_accuracy - decay))

def run_predictions() -> bool:
    """Centralized triggers for all predictions. Delegates to platform predict modules."""
    logger.info("Initializing predictions generation...")
    try:
        from automation.youtube.predict import generate_predictions as yt_pred
        yt_pred()
    except Exception as e:
        logger.warning(f"YouTube prediction trigger failed: {e}")
        
    try:
        from automation.instagram.predict import generate_predictions as ig_pred
        ig_pred()
    except Exception as e:
        logger.warning(f"Instagram prediction trigger failed: {e}")

    try:
        from automation.facebook.predict import generate_predictions as fb_pred
        fb_pred()
    except Exception as e:
        logger.warning(f"Facebook prediction trigger failed: {e}")

    return True

if __name__ == "__main__":
    run_predictions()
