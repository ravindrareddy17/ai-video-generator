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
from utils.database import get_connection

logger = get_logger(__name__)


def optimize_hook(topic_data: dict, client: Groq, model: str) -> tuple[str, list[dict]]:
    """Generate 3 hook variations, score them on shock value & brevity, and return the best."""
    viral_angle = topic_data.get("viral_angle", "")
    base_hook = topic_data.get("hook_line", "")
    
    system_prompt = (
        "You are an elite copywriter specializing in viral hooks for YouTube Shorts.\n"
        "Your task is to generate 3 different styles of hooks for this viral angle and score them.\n"
        "Styles:\n"
        "1. Curiosity Gap: Framed as a mystery, starts with an intriguing question or statement.\n"
        "2. Shock/Awe: Highlight the single most extreme, unbelievable statistic or fact.\n"
        "3. Urgency/Warning: Connects the topic directly to a risk, threat, or near-future impact.\n\n"
        "Evaluate and score each hook variation on a scale of 0.0 to 100.0 based on:\n"
        "- Shock Value / Stop-Scrolling Power\n"
        "- Pervasive Curiosity (forcing the user to find out what happens)\n"
        "- Brevity (under 10 words if possible)\n\n"
        "Respond in JSON format with this structure:\n"
        "{\n"
        "  \"hooks\": [\n"
        "    {\"style\": \"curiosity\", \"text\": \"The mystery hook...\", \"score\": 85.0},\n"
        "    {\"style\": \"shock\", \"text\": \"The shocking statistic...\", \"score\": 90.0},\n"
        "    {\"style\": \"warning\", \"text\": \"The warning statement...\", \"score\": 75.0}\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = f"Base Hook Line: {base_hook}\nViral Angle: {viral_angle}"
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        data = json.loads(completion.choices[0].message.content)
        hooks = data.get("hooks", [])
        
        # Sort by score desc
        hooks.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        best_hook = hooks[0]["text"]
        logger.info(f"Optimized hook selected: '{best_hook}' (Score: {hooks[0]['score']})")
        return best_hook, hooks
    except Exception as e:
        logger.error(f"Failed to generate optimized hooks: {e}")
        return base_hook, [{"style": "default", "text": base_hook, "score": 50.0}]


def generate_narration(topic_data: dict) -> dict:
    """Generate script content for the YouTube Short via Groq LLM using The Shortest Orbit prompt."""
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    
    client = Groq(api_key=api_key)
    
    # Optimize hook first
    chosen_hook, hooks_data = optimize_hook(topic_data, client, model)
    
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
        "6. REWATCH LOOP & COMMENT BAITING: The script's final sentence MUST be a mind-bending question designed to bait user comments. Do NOT append or repeat the hook sentence at the end of the narration. The script must end with the question itself. The loop effect is created by the phrasing of the question leading grammatically into the hook, NOT by repeating the hook."
    )
    
    viral_angle = topic_data.get("viral_angle", "")
    
    user_prompt = (
        f"Generate a script for this viral concept:\n"
        f"Hook Line: {chosen_hook}\n"
        f"Viral Angle (What to explain): {viral_angle}\n\n"
        f"CRITICAL STRUCTURE REQUIREMENTS TO HIT THE 50-60 WORD RANGE:\n"
        f"Your script must contain exactly 5 detailed sentences. Each sentence must be detailed and sophisticated (at least 10-15 words each):\n"
        f"Sentence 1 (Hook): Start exactly with the hook line.\n"
        f"Sentence 2 (Mechanism 1): Write a detailed sentence explaining the technical or scientific mechanism (how it works, neural networks, advanced physics, astronomical processes, etc.) related to: '{viral_angle}'.\n"
        f"Sentence 3 (Mechanism 2): Write another detailed sentence describing the deep technical details, data, or processes involved in: '{viral_angle}'.\n"
        f"Sentence 4 (Implication): Write a detailed sentence explaining the human, global, or cosmic implications of this topic.\n"
        f"Sentence 5 (Rewatch Loop Climax & Comment Bait): Write a final mind-bending question (at least 10 words) that baits viewers to leave comments. Do NOT repeat or append the hook line here; the narration must end with the question. The loop is created by the phrasing of the question leading grammatically into the hook when the video loops back to the start.\n\n"
        f"Count your words carefully. Ensure the script contains at least 40 words total!"
    )
    
    logger.info(f"Calling Groq to generate Shortest Orbit script...")
    
    # Retry loop to guarantee a minimum length of 40 words
    max_attempts = 4
    word_count = 0
    content = {}
    for attempt in range(max_attempts):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt if attempt == 0 else f"{user_prompt}\n\nCRITICAL: Your previous generation was only {word_count} words, which is too short! You MUST expand the narration to be between 45 and 50 words. Add more detail."}
                ],
                model=model,
                temperature=0.7 + (attempt * 0.05),
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            response_text = chat_completion.choices[0].message.content
            content = json.loads(response_text)
            content["hooks_data"] = hooks_data
            
            word_count = len(content["narration"].split())
            logger.info(f"Generated script (Attempt {attempt+1}/{max_attempts}). Word count: {word_count}")
            
            if word_count >= 40:
                import re
                sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', content["narration"]) if s.strip()]
                if not sentences:
                    sentences = [content["narration"]]
                    
                content["sentences"] = sentences
                content["word_count"] = word_count
                
                logger.info(f"Successfully generated script with adequate length: {content['title']}")
                return content
            else:
                logger.warning(f"Script word count ({word_count}) was under 40 words. Retrying...")
                
        except Exception as e:
            logger.error(f"Error on attempt {attempt+1}: {e}")
            if attempt == max_attempts - 1:
                raise
                
    logger.warning(f"Failed to generate a script with at least 40 words after {max_attempts} attempts. Proceeding to avoid crashing.")
    
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', content.get("narration", "")) if s.strip()]
    if not sentences:
        sentences = [content.get("narration", "")]
        
    content["sentences"] = sentences
    content["word_count"] = word_count
    content["hooks_data"] = hooks_data
    return content


def generate_metadata(topic: str, title: str) -> dict:
    """Generate YouTube metadata (description, tags, hashtags) via Groq LLM."""
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert YouTube SEO manager.\n"
        "Your task is to generate metadata for a YouTube Short video.\n"
        "Keep the title engaging and relevant, and ensure it contains the hashtag #Shorts.\n"
        "Create a description that invites clicks explaining the video clearly without hashtags.\n\n"
        "Respond in JSON format with the following keys:\n"
        "- title: catchy YouTube video title (must end with #Shorts or contain #Shorts)\n"
        "- description: a 2-3 sentence description explaining the video, without adding hashtags\n"
        "- hashtags: an array of exactly 5-6 highly relevant, viral hashtags starting with # (e.g. ['#Shorts', '#Science', '#Space', '#AI', '#Physics', '#Technology'])\n"
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
    
    # Step 2c: Log to SQLite database
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insert video entry
        cursor.execute("""
            INSERT INTO videos (title, topic_id, script, status, visual_queries)
            VALUES (?, (SELECT id FROM topics WHERE title = ?), ?, ?, ?)
        """, (
            content["title"],
            topic_str,
            content["narration"],
            "generating",
            json.dumps([]) # will be filled later in Step 5
        ))
        video_id = cursor.lastrowid
        
        # Insert hooks variations
        hooks_list = content.get("hooks_data", [])
        for h in hooks_list:
            is_selected = 1 if h.get("text") == content.get("hook") else 0
            cursor.execute("""
                INSERT INTO hooks (video_id, text, score, selected)
                VALUES (?, ?, ?, ?)
            """, (
                video_id,
                h.get("text"),
                float(h.get("score", 50.0)),
                is_selected
            ))
            
        conn.commit()
        conn.close()
        logger.info(f"Video #{video_id} and hooks logged to SQLite database.")
    except Exception as e:
        logger.warning(f"Failed to log video or hooks to database: {e}")
        
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
