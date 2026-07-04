"""
generate_content.py — Step 2 of the AI Video Generator V2 pipeline.

Reads the selected topic from Step 1, generates a highly engaging narration
script (content.json) and YouTube metadata (metadata.json) using the Groq LLM.

Inputs:
    data/viral_topics.json

Outputs:
    data/content.json
    data/metadata.json
"""

import sys
from pathlib import Path
import json
from groq import Groq

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import VIRAL_TOPICS_FILE, CONTENT_FILE, METADATA_FILE
from utils.config import get_groq_key, get_setting
from utils.logger import get_logger
from utils.helpers import save_json, load_json

logger = get_logger(__name__)


def generate_narration(topic_data: dict) -> dict:
    """Generate script content for the YouTube Short via Groq LLM using The Shortest Orbit prompt."""
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    
    client = Groq(api_key=api_key)
    system_prompt = (
        "SYSTEM PROMPT - THE SHORTEST ORBIT MASTER AI VIDEO PRODUCTION PROMPT (v3.0)\n\n"
        "You are an elite AI filmmaker, documentary editor, and storytelling expert.\n"
        "Your objective is to create a premium YouTube Shorts script (20 seconds max) that maximizes retention, "
        "watch time, and replay value while maintaining a luxury cinematic documentary aesthetic.\n\n"
        "CHANNEL IDENTITY: Science, Space, AI, Astronomy, Physics, Biology, Technology, Universe.\n"
        "Brand Style: Dark, cinematic, futuristic, luxurious, premium, intelligent.\n\n"
        "STORY STRUCTURE:\n"
        "- 0-3s: Irresistible hook.\n"
        "- 3-12s: Explain topic using progressively stronger visuals.\n"
        "- 12-20s: Deliver the reveal, payoff, or surprising fact, ending with a memorable line.\n\n"
        "Respond in valid JSON format only:\n"
        "{\n"
        '  "title": "Curiosity-driven English title, under 60 characters",\n'
        '  "hook": "The exact hook line provided in the prompt",\n'
        '  "narration": "A 20-second script that explains the viral angle. Include the hook as the first sentence. Make it sound dramatic, scientific but accessible, and fast-paced."\n'
        "}\n\n"
        "NON-NEGOTIABLE RULES:\n"
        "1. Start the narration exactly with the provided hook line.\n"
        "2. Keep the script between 45 and 50 words for a strict 20-second pacing.\n"
        "3. Use plain English, avoiding overly dense scientific jargon, but sound authoritative.\n"
        "4. Information quality must be scientifically accurate. Do not exaggerate.\n"
        "5. The final result must sound like a premium documentary produced by a world-class creative studio.\n"
    )
    
    viral_angle = topic_data.get("viral_angle", "")
    hook_line = topic_data.get("hook_line", "")
    
    user_prompt = (
        f"Generate a script for this viral concept:\n"
        f"Hook Line: {hook_line}\n"
        f"Viral Angle (What to explain): {viral_angle}\n\n"
        f"CRITICAL REQUIREMENT: The narration script MUST be between 45 and 50 words total. "
        f"Start with the hook line. Count your words carefully before outputting!"
    )
    
    logger.info(f"Calling Groq to generate Shortest Orbit script...")
    
    # Retry loop to guarantee a minimum length of 42 words (which translates to ~20 seconds at -10% TTS speed)
    max_attempts = 4
    for attempt in range(max_attempts):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt if attempt == 0 else f"{user_prompt}\n\nCRITICAL: Your previous generation was only {word_count} words, which is too short! You MUST expand the narration to be between 45 and 50 words. Add more detail."}
                ],
                model=model,
                temperature=0.7 + (attempt * 0.05),  # slightly increase temperature for variety if it fails
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            response_text = chat_completion.choices[0].message.content
            content = json.loads(response_text)
            
            word_count = len(content["narration"].split())
            logger.info(f"Generated script (Attempt {attempt+1}/{max_attempts}). Word count: {word_count}")
            
            if word_count >= 42:
                import re
                sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', content["narration"]) if s.strip()]
                if not sentences:
                    sentences = [content["narration"]]
                    
                content["sentences"] = sentences
                content["word_count"] = word_count
                
                logger.info(f"Successfully generated script with adequate length: {content['title']}")
                return content
            else:
                logger.warning(f"Script word count ({word_count}) was under 42 words. Retrying...")
                
        except Exception as e:
            logger.error(f"Error on attempt {attempt+1}: {e}")
            if attempt == max_attempts - 1:
                raise
                
    raise ValueError(f"Failed to generate a script with at least 42 words after {max_attempts} attempts.")")


def generate_metadata(topic: str, title: str) -> dict:
    """Generate YouTube metadata (description, tags, hashtags) via Groq LLM."""
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert YouTube SEO manager.\n"
        "Your task is to generate metadata for a YouTube Short video.\n"
        "Keep the title engaging and relevant, and ensure it contains the hashtag #Shorts.\n"
        "Create a descriptions that invites clicks and includes relevant hashtags.\n\n"
        "Respond in JSON format with the following keys:\n"
        "- title: catchy YouTube video title (must end with #Shorts or contain #Shorts)\n"
        "- description: a 2-3 sentence description explaining the video, followed by 3-5 relevant hashtags\n"
        "- hashtags: an array of 3-5 strings starting with # (e.g. ['#Shorts', '#Science', ...])\n"
        "- keywords: an array of 6-10 search keywords for tagging\n"
        "- category: standard YouTube category ID. Choose '28' (Science & Technology) if scientific, otherwise '22' (People & Blogs)"
    )
    
    user_prompt = f"Generate SEO metadata for a video on topic '{topic}' with script title '{title}'"
    
    logger.info("Calling Groq to generate YouTube metadata...")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        response_text = chat_completion.choices[0].message.content
        metadata = json.loads(response_text)
        
        # Ensure #Shorts is in the title
        if "#shorts" not in metadata.get("title", "").lower():
            metadata["title"] = f"{metadata.get('title', 'Interesting Topic')} #Shorts"
            
        return metadata
    except Exception as e:
        logger.error(f"Error generating SEO metadata: {e}")
        # Fallback metadata
        return {
            "title": f"{title} #Shorts",
            "description": f"An educational look at {topic}. Discover the science behind this viral topic! #shorts #education #viral",
            "hashtags": ["#Shorts", "#Education", "#Science", "#Viral"],
            "keywords": [topic, "education", "science", "facts", "mystery"],
            "category": "28"
        }


def run(topic_data: dict = None) -> tuple[dict, dict]:
    """Orchestrates Step 2 of the pipeline."""
    logger.info("=== STEP 2: GENERATE CONTENT ===")
    
    if topic_data is None:
        topic_data = load_json(VIRAL_TOPICS_FILE)
        
    topic_str = topic_data.get("selected_topic", "Space Science")
    
    # Step 2a: Generate narration script
    content = generate_narration(topic_data)
    save_json(content, CONTENT_FILE)
    logger.info(f"Content saved to {CONTENT_FILE}")
    
    # Step 2b: Generate YouTube SEO metadata
    metadata = generate_metadata(topic_str, content["title"])
    save_json(metadata, METADATA_FILE)
    logger.info(f"YouTube metadata saved to {METADATA_FILE}")
    
    return content, metadata


if __name__ == "__main__":
    try:
        content, metadata = run()
        print("--- CONTENT ---")
        print(json.dumps(content, indent=2))
        print("--- METADATA ---")
        print(json.dumps(metadata, indent=2))
    except Exception as exc:
        logger.exception("generate_content module execution failed")
        sys.exit(1)
