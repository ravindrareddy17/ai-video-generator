import sys
import json
import time
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import get_logger
from python.baseline_engine import calculate_channel_baselines
from python.v4_contract_engine import V4ContractEngine

logger = get_logger(__name__)

class ClosedLoopLearningEngine:
    """Post-Publication Closed-Loop Learning & Audience Memory Engine."""

    def __init__(self):
        self.contract_engine = V4ContractEngine()

    def process_publication_feedback(self, contract: Dict[str, Any], analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs baseline comparison, bottleneck diagnosis, and updates learning history."""
        logger.info(f"Processing closed-loop feedback for video {contract.get('video_id')}...")
        
        # 1. Update contract with analytics
        contract["analytics"]["data_available"] = True
        contract["analytics"]["collected_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        contract["analytics"].update(analytics_data)

        # Transition to ANALYZED
        if contract.get("status") == "PUBLISHED":
            self.contract_engine.transition_state(contract, "ANALYZED")

        # 2. Extract key metrics
        apv = float(analytics_data.get("average_percentage_viewed", 0.0) or 0.0)
        stayed = float(analytics_data.get("viewed_vs_swiped_away", 0.0) or 0.0)
        subs = int(analytics_data.get("subscribers_gained", 0) or 0)
        views = int(analytics_data.get("views", 0) or 1)
        sub_conv_rate = round((subs / views) * 100.0, 2)

        # 3. Baseline comparison
        baselines = calculate_channel_baselines([analytics_data])
        baseline_apv = baselines.get("baselines", {}).get("apv", {}).get("median", 60.0)

        # 4. Bottleneck Diagnosis Logic
        bottleneck = "None"
        diagnosis = "Performance meets or exceeds baseline expectations."
        classification = "average"

        if stayed < 70.0:
            bottleneck = "Viewer Choice (Hook & Opening Frame)"
            diagnosis = "Low Stayed-to-Watch rate (<70%). Action: Rewrite first 1-2 seconds."
            classification = "underperformer"
        elif apv < baseline_apv:
            bottleneck = "Story Pacing & Visual Movement"
            diagnosis = f"APV ({apv:.1f}%) is below channel baseline ({baseline_apv:.1f}%). Action: Accelerate story delivery."
            classification = "underperformer"
        elif sub_conv_rate < 2.0:
            bottleneck = "Subscriber Conversion & Series Callouts"
            diagnosis = f"Sub conversion rate ({sub_conv_rate}%) is low despite good retention. Action: Strengthen reason to return."
            classification = "average"
        else:
            classification = "winner"

        # Update performance analysis in contract
        contract["performance_analysis"] = {
            "channel_baseline_comparison": {
                "apv_vs_baseline": round(apv - baseline_apv, 2),
                "subscriber_conversion_rate": sub_conv_rate
            },
            "performance_classification": classification,
            "bottleneck": bottleneck,
            "diagnosis": diagnosis,
            "what_worked": ["Visual motion pacing", "Documentary narration tone"] if classification == "winner" else [],
            "what_failed": [bottleneck] if classification == "underperformer" else [],
            "recommended_changes": [diagnosis]
        }

        # 5. Update Audience Learning
        if classification == "winner":
            topic = contract.get("video_strategy", {}).get("topic", "")
            contract["learning"]["winning_topic_pattern"] = topic
            contract["learning"]["patterns_confirmed"].append(f"Winner: '{topic}' (+{apv - baseline_apv:.1f}% APV vs baseline)")

        # Transition to LEARNED
        self.contract_engine.transition_state(contract, "LEARNED")
        self.contract_engine.save_contract(contract)

        logger.info(f"Closed-loop feedback cycle completed. Classification: {classification}. Bottleneck: {bottleneck}")
        return contract

def run_feedback_cycle(contract_path: Path, analytics_data: Dict[str, Any]) -> bool:
    """Orchestrate post-publication learning cycle."""
    engine = ClosedLoopLearningEngine()
    if not contract_path.exists():
        logger.error(f"Contract file not found at {contract_path}")
        return False

    with open(contract_path, "r", encoding="utf-8") as f:
        contract = json.load(f)

    updated_contract = engine.process_publication_feedback(contract, analytics_data)
    return True
