import sys
import statistics
from typing import Dict, Any, List
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_channel_baselines(history_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistical baselines (Median, Mean, P25, P75) across historical video data."""
    sample_size = len(history_metrics)
    if sample_size < 5:
        logger.warning(f"Baseline Sample Size ({sample_size}) < 5. Minimum-data protection active: INSUFFICIENT DATA.")
        return {
            "sample_size": sample_size,
            "status": "INSUFFICIENT DATA",
            "baselines": {}
        }

    confidence_level = "preliminary"
    if sample_size >= 20:
        confidence_level = "strategic_confidence"
    elif sample_size >= 10:
        confidence_level = "stronger_pattern"

    apv_list = [m.get("average_percentage_viewed", 0.0) for m in history_metrics if m.get("average_percentage_viewed")]
    views_list = [m.get("views", 0) for m in history_metrics if m.get("views")]
    subs_list = [m.get("subscriber_conversion_rate", 0.0) for m in history_metrics if m.get("subscriber_conversion_rate")]

    def quantiles(lst, q):
        if not lst: return 0.0
        sorted_lst = sorted(lst)
        idx = int(len(sorted_lst) * q)
        return sorted_lst[min(idx, len(sorted_lst) - 1)]

    baselines = {
        "apv": {
            "median": statistics.median(apv_list) if apv_list else 60.0,
            "mean": statistics.mean(apv_list) if apv_list else 60.0,
            "p25": quantiles(apv_list, 0.25),
            "p75": quantiles(apv_list, 0.75)
        },
        "views": {
            "median": statistics.median(views_list) if views_list else 500,
            "mean": statistics.mean(views_list) if views_list else 500,
            "p25": quantiles(views_list, 0.25),
            "p75": quantiles(views_list, 0.75)
        },
        "subscriber_conversion_rate": {
            "median": statistics.median(subs_list) if subs_list else 2.5,
            "mean": statistics.mean(subs_list) if subs_list else 2.5,
            "p25": quantiles(subs_list, 0.25),
            "p75": quantiles(subs_list, 0.75)
        }
    }

    return {
        "sample_size": sample_size,
        "confidence_level": confidence_level,
        "status": "SUFFICIENT DATA",
        "baselines": baselines
    }
