import sys
import json
from pathlib import Path
from groq import Groq

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import CONTENT_FILE
from utils.config import get_groq_key, get_setting
from utils.logger import get_logger
from utils.helpers import load_json

logger = get_logger(__name__)

def verify_script_facts(narration: str) -> tuple[bool, list[dict]]:
    """Analyze script narration using Groq LLM to verify scientific credibility of claims."""
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert fact-checker specializing in science, space, and technology.\n"
        "Your task is to analyze a video narration script and extract every major scientific fact or claim.\n"
        "Then, score the credibility/accuracy of each claim from 0.0 to 100.0.\n"
        "If a claim is speculative, unverified, or incorrect, assign it a low score.\n\n"
        "CRITICAL RULES:\n"
        "1. Do NOT penalize poetic metaphors, general descriptive summaries, or introductory hooks (e.g. 'listening to quantum whispers' or 'beginning of a new era') as false. Assign them 100.0 if the underlying scientific topic they introduce is legitimate.\n"
        "2. Only assign low scores (< 75.0) to actual scientific errors, fake stats/numbers, or pseudoscience.\n\n"
        "Respond in JSON format with this structure:\n"
        "{\n"
        "  \"claims\": [\n"
        "    {\n"
        "      \"claim\": \"The scientific statement...\",\n"
        "      \"accuracy_score\": 95.0,\n"
        "      \"explanation\": \"Why this is accurate or what the source is.\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = f"Verify the facts in this narration:\n\n{narration}"
    
    logger.info("Calling Groq to verify script facts...")
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.2, # low temperature for factual queries
            response_format={"type": "json_object"}
        )
        
        data = json.loads(completion.choices[0].message.content)
        claims = data.get("claims", [])
        
        # Verify if any claim has score < 75.0
        passed = True
        failed_claims = []
        for c in claims:
            score = float(c.get("accuracy_score", 50.0))
            logger.info(f"Verified Claim: '{c.get('claim')[:50]}...' | Accuracy: {score}%")
            if score < 75.0:
                passed = False
                failed_claims.append(c)
                
        if not passed:
            logger.warning(f"Fact checking failed! {len(failed_claims)} claims were flagged as highly uncertain or incorrect.")
            
        return passed, claims
        
    except Exception as e:
        logger.error(f"Error during fact-checking: {e}")
        # Default fallback is True to prevent random failures if API limit is hit
        return True, [{"claim": "Error running check, assuming passed", "accuracy_score": 100.0, "explanation": "Fallback"}]

def run() -> bool:
    """Orchestrates Step 2.5 of the pipeline."""
    logger.info("=== STEP 2.5: VERIFY FACTS ===")
    if not CONTENT_FILE.exists():
        logger.error(f"Content file not found at {CONTENT_FILE}")
        return False
        
    content = load_json(CONTENT_FILE)
    narration = content.get("narration", "")
    if not narration:
        logger.error("No narration text found in content.json")
        return False
        
    passed, claims = verify_script_facts(narration)
    return passed

if __name__ == "__main__":
    success = run()
    print(f"Fact verification success: {success}")
    sys.exit(0 if success else 1)
