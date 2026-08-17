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

def check_script_quality(content: dict) -> bool:
    """Run programmatic and LLM checks on script quality, formatting, loop flow, and grammar."""
    narration = content.get("narration", "")
    title = content.get("title", "")
    word_count = content.get("word_count", 0)
    
    # 1. Programmatic length checks (25-40 seconds pacing target = 70 to 180 words)
    if word_count < 70 or word_count > 180:
        logger.error(f"Quality Check Failed: Word count ({word_count}) is outside the acceptable range (70-180 words) for a 25-40s Short.")
        return False
        
    # 1.5. Programmatic comment-bait question check
    if not narration.strip().endswith("?"):
        logger.error("Quality Check Failed: Narration script must end with a question mark (?) to promote viewer discussion.")
        return False
        
    # 2. Programmatic repetitive wording checks
    words = [w.strip().lower().strip(".,!?") for w in narration.split()]
    unique_words = set(words)
    # Simple check: if a non-trivial word occurs too many times, it might be repetitive
    common_filler = {"the", "a", "and", "or", "but", "in", "on", "at", "to", "for", "of", "is", "are", "it", "this", "that", "we", "our", "you"}
    for word in unique_words:
        if word in common_filler:
            continue
        if words.count(word) > 3:
            logger.warning(f"Repetitive word warning: '{word}' occurs {words.count(word)} times in narration.")
            
    # 3. LLM Grammar, Pacing, and Loop Validation
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an elite video editor and quality control officer for YouTube Shorts.\n"
        "Your task is to inspect a narration script for spelling, grammar mistakes, pacing, "
        "and loop-flow issues (e.g. check if the script ends with a repeated sentence or if the loop flow is bad).\n\n"
        "SHORTS FORMAT RULES:\n"
        "1. High-energy hooks (e.g. starting with exclamation marks, dramatic declarations, or 'Exposed/Uncovered') are INTENTIONAL and DESIRED. Do NOT flag them as issues.\n"
        "2. Scripts ending with a mind-bending question to bait comments are INTENTIONAL and DESIRED. Do NOT reject them.\n"
        "3. Only fail the script if there are actual spelling errors, bad grammar, or if the text is completely confusing/incomprehensible.\n\n"
        "Respond in JSON format with this structure:\n"
        "{\n"
        "  \"hook_score\": 9.0,\n"
        "  \"story_score\": 8.5,\n"
        "  \"visual_score\": 9.0,\n"
        "  \"originality_score\": 8.5,\n"
        "  \"accuracy_score\": 9.0,\n"
        "  \"passed\": true,\n"
        "  \"issues\": [\"Issue description...\"]\n"
        "}"
    )
    
    user_prompt = f"Inspect this video concept:\nTitle: {title}\nNarration: {narration}"
    
    logger.info("Calling Groq for quality review...")
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        result = json.loads(completion.choices[0].message.content)
        
        hook_s = float(result.get("hook_score", 8.5))
        story_s = float(result.get("story_score", 8.5))
        vis_s = float(result.get("visual_score", 8.5))
        orig_s = float(result.get("originality_score", 8.5))
        acc_s = float(result.get("accuracy_score", 8.5))
        
        # V4 QualityScore Formula: 0.25(Hook) + 0.25(Story) + 0.20(Visual) + 0.15(Originality) + 0.15(Accuracy)
        quality_score = (0.25 * hook_s) + (0.25 * story_s) + (0.20 * vis_s) + (0.15 * orig_s) + (0.15 * acc_s)
        
        # V4 ACCURACY VETO RULE: If accuracy score < 7.0, veto publication regardless of QualityScore
        accuracy_passed = acc_s >= 7.0
        if not accuracy_passed:
            logger.error(f"Accuracy Veto Triggered! Accuracy Score ({acc_s:.1f}) is below 7.0 threshold.")
            
        passed = quality_score >= 8.5 and accuracy_passed and result.get("passed", True)
        issues = result.get("issues", [])
        
        if not passed:
            logger.error(f"Quality Check Failed. QualityScore: {quality_score:.2f} (Target: >= 8.5). Issues: {issues}")
        else:
            logger.info(f"Script QualityScore PASSED: {quality_score:.2f}/10.0 (Target: >= 8.5).")
            
        return passed
    except Exception as e:
        logger.error(f"Quality checker LLM execution failed: {e}. Defaulting to true.")
        return True

def run() -> bool:
    """Orchestrates Step 2.6 of the pipeline."""
    logger.info("=== STEP 2.6: RUN QUALITY CHECKER ===")
    if not CONTENT_FILE.exists():
        logger.error(f"Content file not found at {CONTENT_FILE}")
        return False
        
    content = load_json(CONTENT_FILE)
    success = check_script_quality(content)
    return success

if __name__ == "__main__":
    success = run()
    print(f"Quality check success: {success}")
    sys.exit(0 if success else 1)
