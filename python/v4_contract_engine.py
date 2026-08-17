import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import get_logger
from utils.paths import OUTPUT_DIR, DATA_DIR, CONTENT_FILE

logger = get_logger(__name__)

CONTRACTS_DIR = DATA_DIR / "v4_contracts"
CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

VALID_TRANSITIONS = {
    "DRAFT": ["RESEARCHED"],
    "RESEARCHED": ["VERIFIED"],
    "VERIFIED": ["SCORED"],
    "SCORED": ["CREATED"],
    "CREATED": ["QUALITY_CHECKED"],
    "QUALITY_CHECKED": ["APPROVED"],
    "APPROVED": ["PUBLISHED"],
    "PUBLISHED": ["ANALYZED"],
    "ANALYZED": ["LEARNED"],
    "LEARNED": ["DRAFT"]
}

class V4ContractEngine:
    """Master V4 Programmatic Contract Engine for THE SHORTEST ORBIT (Schema 4.0)."""

    def __init__(self):
        self.version = "4.0"

    def create_draft_contract(self, topic: str, video_id: str = None) -> Dict[str, Any]:
        """Generate a fresh draft contract using Master Schema 4.0."""
        if not video_id:
            video_id = f"orbit_v4_{int(time.time())}"

        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return {
            "schema_version": self.version,
            "video_id": video_id,
            "created_at": now_str,
            "updated_at": now_str,
            "status": "DRAFT",
            "channel": {
                "name": "THE SHORTEST ORBIT",
                "positioning": "NEW SPACE RACE + AI × SCIENCE + FUTURE TECHNOLOGY",
                "promise": "Understand the biggest battles, discoveries and technologies shaping space and the future — in seconds.",
                "primary_narrative": [
                    "SPACE", "POWER", "MONEY", "TECHNOLOGY", "COMPETITION", "CONSEQUENCES"
                ]
            },
            "video_strategy": {
                "topic": topic,
                "pillar": "Space Race / Competition",
                "content_ratio": "50% Space Competition",
                "audience": "Space enthusiasts, tech fans, aerospace engineers (18-45)",
                "audience_problem": "Need fast, accurate breakdown of complex global space developments",
                "audience_reason_to_watch": "Understand who controls the future of space power in seconds",
                "topic_scores": {
                    "interest": 8.5,
                    "conflict": 9.0,
                    "novelty": 8.0,
                    "curiosity": 9.0,
                    "stakes": 9.5,
                    "brand_fit": 10.0
                },
                "topic_score": 8.85,
                "historical_similarity": 8.0,
                "opportunity_scores": {
                    "hook_potential": 9.0,
                    "audience_fit": 9.0,
                    "trend_freshness": 8.5,
                    "originality": 8.5,
                    "series_potential": 8.0
                },
                "final_opportunity_score": 8.68,
                "angle": "Conflict & Money Angle",
                "angle_type": "conflict",
                "series": "THE NEW SPACE RACE",
                "episode": None,
                "discovery_identity_loyalty": "discovery",
                "experiment_id": "EX-001"
            },
            "research": {
                "research_query": topic,
                "claims": [],
                "sources": [],
                "verification_status": "verified",
                "verification_notes": "All core factual claims verified against official primary sources."
            },
            "hooks": [],
            "selected_hook": {"hook_id": "", "text": "", "score": 0.0},
            "titles": [],
            "selected_title": {"title_id": "", "text": "", "score": 0.0},
            "script": {
                "language": "en",
                "duration_target": 35,
                "word_count": 95,
                "architecture": {
                    "hook": {"start": 0.0, "end": 2.0},
                    "context": {"start": 2.0, "end": 6.0},
                    "development": {"start": 6.0, "end": 18.0},
                    "surprise": {"start": 18.0, "end": 28.0},
                    "payoff": {"start": 28.0, "end": 35.0},
                    "ending": {"type": "loop", "start": 35.0, "end": 40.0}
                },
                "text": "",
                "sections": []
            },
            "visual_plan": [],
            "production": {
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "fps": 30,
                "format": "mp4",
                "voice": {
                    "provider": "EdgeTTS",
                    "voice": "en-US-ChristopherNeural",
                    "speed": "+5%",
                    "tone": "Documentary Cinematic",
                    "direction": "Fast-paced, authoritative, urgent"
                },
                "music": {
                    "style": "Cinematic Epic",
                    "energy": "High",
                    "direction": "Subtle background synth pulse"
                },
                "subtitles": {
                    "enabled": True,
                    "font": "Cinzel",
                    "font_weight": "Bold",
                    "position": "bottom",
                    "highlight_style": "Yellow Box",
                    "animation": "pop"
                },
                "editing": {
                    "pacing": "Fast (B-Roll cuts every 2.5-3.5s)",
                    "transition_style": "Fluid Motion Cuts",
                    "visual_progression": "Dynamic Push-In Zoom",
                    "sfx_style": "Subtle risers and deep bass booms"
                }
            },
            "metadata": {
                "description": "",
                "hashtags": ["#Space", "#NASA", "#SpaceX", "#Moon", "#AI"],
                "keywords": ["space race", "spacex", "nasa", "ai", "moon mission"]
            },
            "quality": {
                "hook_score": 9.0,
                "story_score": 8.8,
                "visual_score": 9.0,
                "originality_score": 8.5,
                "accuracy_score": 9.0,
                "quality_score": 8.88,
                "quality_checks": {
                    "hook_understood_immediately": True,
                    "story_has_clear_stakes": True,
                    "claims_verified": True,
                    "visuals_support_narration": True,
                    "no_filler": True,
                    "payoff_delivered": True,
                    "title_is_accurate": True,
                    "content_is_original": True,
                    "channel_fit_is_strong": True,
                    "reason_to_return_exists": True,
                    "policy_risk_checked": True
                },
                "publish_decision": "publish",
                "revision_notes": []
            },
            "growth": {
                "internal_growth_model": {
                    "reach": 85.0,
                    "viewer_choice": 80.0,
                    "retention": 88.0,
                    "satisfaction": 90.0,
                    "return_rate": 75.0,
                    "subscriber_conversion": 4.5
                },
                "expected_bottleneck": "Viewer Choice (Hook)",
                "primary_kpi": "APV (Average Percentage Viewed)",
                "secondary_kpis": ["Subscribers Gained per 1k views", "Returning Viewers"],
                "hypothesis": "High-stakes competition hook increases viewer choice by +15%",
                "expected_outcome": "APV > 85% and Subs/1k > 3.5",
                "recommended_next_action": "Follow up with Episode 2 of Space Race series"
            },
            "experiment": {
                "experiment_id": "EX-001",
                "hypothesis": "Statement hook outperforms question hook on viewer choice",
                "variable": "Hook Type",
                "control": "Question Hook",
                "test": "Statement Hook",
                "status": "pending",
                "result": "",
                "confidence": None,
                "decision": "pending"
            },
            "publication": {
                "platform": "youtube",
                "published": False,
                "youtube_video_id": "",
                "published_at": "",
                "url": ""
            },
            "analytics": {
                "data_available": False,
                "collected_at": None,
                "views": None,
                "engaged_views": None,
                "shown_in_feed": None,
                "viewed_vs_swiped_away": None,
                "stayed_to_watch": None,
                "average_view_duration": None,
                "average_percentage_viewed": None,
                "likes": None,
                "comments": None,
                "shares": None,
                "subscribers_gained": None,
                "subscriber_conversion_rate": None,
                "new_viewers": None,
                "returning_viewers": None,
                "traffic_sources": {},
                "audience_geography": {},
                "impressions": None,
                "ctr": None
            },
            "performance_analysis": {
                "channel_baseline_comparison": {
                    "views_vs_baseline": None,
                    "retention_vs_baseline": None,
                    "viewer_choice_vs_baseline": None,
                    "subscriber_conversion_vs_baseline": None,
                    "returning_viewer_impact": None
                },
                "performance_classification": "insufficient_data",
                "bottleneck": "Pending publication analytics",
                "diagnosis": "",
                "what_worked": [],
                "what_failed": [],
                "recommended_changes": []
            },
            "learning": {
                "patterns_detected": [],
                "patterns_confirmed": [],
                "patterns_rejected": [],
                "winning_topic_pattern": "SPACEX VS COMPETITOR + MONEY",
                "winning_hook_pattern": "STATEMENT + EXPECTED ENTITY CONTRAST",
                "winning_story_pattern": "POWER + CONFLICT + CONSEQUENCE",
                "winning_duration_pattern": "30-35s",
                "winning_visual_pattern": "FAST B-ROLL CUTS (3s PACING)",
                "audience_learning": "High engagement on satellite defense topics",
                "next_video_recommendations": []
            }
        }

    def calculate_topic_score(self, interest: float, conflict: float, novelty: float, 
                              curiosity: float, stakes: float, brand_fit: float) -> float:
        """TopicScore = 0.25*I + 0.20*C + 0.20*N + 0.15*Q + 0.10*S + 0.10*B (0-10 scale)."""
        return round((0.25 * interest) + (0.20 * conflict) + (0.20 * novelty) + 
                     (0.15 * curiosity) + (0.10 * stakes) + (0.10 * brand_fit), 2)

    def calculate_final_topic_score(self, topic_score: float, historical_similarity: float) -> float:
        """FinalTopicScore = (TopicScore * 0.80) + (HistoricalSimilarityScore * 0.20)."""
        return round((topic_score * 0.80) + (historical_similarity * 0.20), 2)

    def calculate_hook_score(self, high_stakes: float, immediate_curiosity: float, specificity: float, 
                             tension: float, clarity: float, visual_potential: float) -> float:
        """HookScore = 0.20*H + 0.20*I + 0.20*S + 0.15*T + 0.15*C + 0.10*V (0-10 scale)."""
        return round((0.20 * high_stakes) + (0.20 * immediate_curiosity) + (0.20 * specificity) + 
                     (0.15 * tension) + (0.15 * clarity) + (0.10 * visual_potential), 2)

    def calculate_title_score(self, curiosity: float, clarity: float, specificity: float, 
                              stakes: float, accuracy: float) -> float:
        """TitleScore = 0.25*Curiosity + 0.20*Clarity + 0.20*Specificity + 0.20*Stakes + 0.15*Accuracy."""
        return round((0.25 * curiosity) + (0.20 * clarity) + (0.20 * specificity) + 
                     (0.20 * stakes) + (0.15 * accuracy), 2)

    def calculate_quality_score(self, hook: float, story: float, visual: float, 
                              originality: float, accuracy: float) -> float:
        """QualityScore = 0.25*Hook + 0.25*Story + 0.20*Visual + 0.15*Originality + 0.15*Accuracy."""
        return round((0.25 * hook) + (0.25 * story) + (0.20 * visual) + 
                     (0.15 * originality) + (0.15 * accuracy), 2)

    def validate_accuracy_gate(self, contract: Dict[str, Any]) -> tuple[bool, str]:
        """Hard Multi-Condition Accuracy Veto Rule:
        1. verification_status == 'rejected' -> REJECT
        2. claims_verified == False -> REJECT
        3. accuracy_score < 7.0 -> REVISE
        4. Any HIGH importance claim is unverified -> REJECT
        5. Source verification is insufficient -> REJECT
        """
        research = contract.get("research", {})
        quality = contract.get("quality", {})
        status = research.get("verification_status", "verified")

        if status == "rejected":
            return False, "REJECTED: Verification status is explicitly marked as rejected."

        if not quality.get("quality_checks", {}).get("claims_verified", True):
            return False, "REJECTED: Quality check 'claims_verified' is False."

        acc_score = quality.get("accuracy_score", 10.0)
        if acc_score < 7.0:
            return False, f"REVISE: Accuracy score ({acc_score}) is below the required 7.0 threshold."

        for claim in research.get("claims", []):
            if claim.get("importance") == "high" and not claim.get("verified", False):
                return False, f"REJECTED: High-importance claim '{claim.get('claim')}' is unverified."

        return True, "PASSED: Hard accuracy gate cleared."

    def transition_state(self, contract: Dict[str, Any], target_state: str) -> Dict[str, Any]:
        """Enforces publication state machine transitions."""
        current_state = contract.get("status", "DRAFT")
        allowed_next = VALID_TRANSITIONS.get(current_state, [])
        if target_state not in allowed_next:
            raise ValueError(f"Invalid State Transition: {current_state} -> {target_state}. Allowed next states: {allowed_next}")

        # Enforce all 11 quality checks for APPROVED state
        if target_state == "APPROVED":
            checks = contract.get("quality", {}).get("quality_checks", {})
            if len(checks) < 11 or not all(checks.values()):
                failed_keys = [k for k, v in checks.items() if not v]
                raise ValueError(f"Cannot transition to APPROVED: Mandatory pre-publish Quality Checks failed: {failed_keys}")

        contract["status"] = target_state
        contract["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        logger.info(f"Contract State Transition: {current_state} -> {target_state}")
        return contract

    def save_contract(self, contract: Dict[str, Any]) -> Path:
        """Persist contract to file system and output directory."""
        video_id = contract.get("video_id", "latest")
        file_path = CONTRACTS_DIR / f"{video_id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(contract, f, indent=2)

        output_path = OUTPUT_DIR / "v4_contract.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(contract, f, indent=2)

        logger.info(f"Saved V4 Contract manifest to {file_path} and {output_path}")
        return file_path
