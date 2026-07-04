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
        "SYSTEM PROMPT — The Shortest Orbit Scriptwriter\n\n"
        "You are the lead scriptwriter for 'The Shortest Orbit,' a fast-paced, highly engaging "
        "YouTube Shorts channel focused on space, science, and AI.\n\n"
        "Your job is to take a viral concept and generate a highly engaging 40-second narration script.\n"
        "Respond in valid JSON format only, no preamble or markdown fences.\n\n"
        "{\n"
        '  "title": "Curiosity-driven English title, under 60 characters",\n'
        '  "hook": "The exact hook line provided in the prompt",\n'
        '  "narration": "A 40-second script that explains the viral angle clearly to a general audience. Include the hook as the first sentence. Make it sound dramatic, scientific but accessible, and fast-paced."\n'
        "}\n\n"
        "NON-NEGOTIABLE RULES:\n"
        "1. Start the narration exactly with the provided hook line.\n"
        "2. Keep the script under 90 words for a 40-second pacing.\n"
        "3. Use plain English, avoiding overly dense scientific jargon, but sound authoritative.\n"
    )
    
    viral_angle = topic_data.get("viral_angle", "")
    hook_line = topic_data.get("hook_line", "")
    
    user_prompt = (
        f"Generate a script for this viral concept:\n"
        f"Hook Line: {hook_line}\n"
        f"Viral Angle (What to explain): {viral_angle}\n"
    )
    
    logger.info(f"Calling Groq to generate Shortest Orbit script...")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        response_text = chat_completion.choices[0].message.content
        content = json.loads(response_text)
        
        import re
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', content["narration"]) if s.strip()]
        if not sentences:
            sentences = [content["narration"]]
            
        content["sentences"] = sentences
        content["word_count"] = len(content["narration"].split())
        
        logger.info(f"Successfully generated script: {content['title']}")
        return content
        
    except Exception as e:
        logger.error(f"Error generating script: {e}")
        raise


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
