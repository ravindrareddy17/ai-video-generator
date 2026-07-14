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
from automation.database.connection import get_youtube_conn, get_instagram_conn, get_facebook_conn, get_automation_conn

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
        "2. Shock/Awe: Highlight the single most extreme, scientifically true fact from the story.\n"
        "3. Urgency/Warning: Connects the topic directly to a verified risk or impact.\n\n"
        "Evaluate and score each hook variation on a scale of 0.0 to 100.0 based on:\n"
        "- Shock Value / Stop-Scrolling Power\n"
        "- Pervasive Curiosity (forcing the user to find out what happens)\n"
        "- Brevity (under 10 words if possible)\n\n"
        "STRICT HOOK HONESTY RULE:\n"
        "Never fabricate statistics, numbers, or percentages (e.g. do NOT invent statements like '90% of X', '10 years', '1 in 5', or 'millions of years'). The hook must represent a 100% true, verifiable scientific or historical fact. If the source headline does not contain specific numbers, do NOT include any numbers in your hooks. Focus instead on curiosity-gap phrasing and intriguing qualitative questions.\n\n"
        "Respond in JSON format with this structure (replace the text values with your actual generated hooks based on the topic):\n"
        "{\n"
        "  \"hooks\": [\n"
        "    {\"style\": \"curiosity\", \"text\": \"[Write your actual curiosity hook here]\", \"score\": 85.0},\n"
        "    {\"style\": \"shock\", \"text\": \"[Write your actual shocking fact hook here]\", \"score\": 90.0},\n"
        "    {\"style\": \"warning\", \"text\": \"[Write your actual warning hook here]\", \"score\": 75.0}\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = f"Base Hook Line: {base_hook}\nViral Angle: {viral_angle}"
    
    best_hook = base_hook
    all_attempts_hooks = []
    
    # Retry loop to get a hook that scores at least 85.0 (8.5/10)
    for attempt in range(3):
        try:
            logger.info(f"Generating optimized hooks (attempt {attempt + 1}/3)...")
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt if attempt == 0 else f"{user_prompt}\n\nCRITICAL: Make sure the hooks are highly engaging and score at least 85.0!"}
                ],
                model=model,
                temperature=0.7 + (attempt * 0.1),
                response_format={"type": "json_object"}
            )
            data = json.loads(completion.choices[0].message.content)
            hooks = data.get("hooks", [])
            if not hooks:
                continue
                
            # Sort by score desc
            hooks.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            all_attempts_hooks.extend(hooks)
            
            top_score = hooks[0].get("score", 0.0)
            if top_score >= 85.0:
                best_hook = hooks[0]["text"]
                logger.info(f"Optimized hook accepted on attempt {attempt + 1}: '{best_hook}' (Score: {top_score})")
                return best_hook, hooks
            else:
                logger.warning(f"Attempt {attempt + 1} best hook score was {top_score} (under target 85.0). Retrying...")
                
        except Exception as e:
            logger.error(f"Failed to generate optimized hooks on attempt {attempt + 1}: {e}")
            
    # Fallback to the highest scoring hook generated across all attempts
    if all_attempts_hooks:
        all_attempts_hooks.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        best_hook = all_attempts_hooks[0]["text"]
        logger.warning(f"Could not generate a hook scoring >= 85.0. Falling back to best available: '{best_hook}' (Score: {all_attempts_hooks[0].get('score', 0.0)})")
        return best_hook, all_attempts_hooks[:3]
        
    return base_hook, [{"style": "default", "text": base_hook, "score": 50.0}]


def generate_narration(topic_data: dict) -> dict:
    """Generate script content for the YouTube Short via Groq LLM using The Shortest Orbit prompt."""
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    
    client = Groq(api_key=api_key)
    
    # Optimize hook first
    chosen_hook, hooks_data = optimize_hook(topic_data, client, model)
    
    system_prompt = (
        "SYSTEM PROMPT - SPACE FRONTIER ENGINE MASTER PROMPT (v4.0 - Countries + AI + Space)\n\n"
        "You are an elite AI filmmaker, documentary editor, and storytelling expert.\n"
        "Your objective is to create a premium YouTube Shorts script (20 seconds max) that maximizes retention, "
        "watch time, and replay value while maintaining a luxury cinematic documentary aesthetic.\n\n"
        "CORE STRICT NICHE: You must ONLY generate content where the central theme is: Countries + Space Exploration + AI + Global Competition. "
        "Every video must naturally connect these four elements. Never generate AI-only, space-only, country-politics-only, or military-only news.\n"
        "Every script must answer: 'How is a country using space and AI to shape the future of humanity?'\n\n"
        "STORY STRUCTURE (6-STEP STORYFLOW):\n"
        "1. Strong 3-second hook (Sentence 1): E.g. 'The next world superpower may not be decided on Earth...', 'One country just made a move that could change space forever...'\n"
        "2. The Event: Explain country, what happened, mission name, AI technology involved, goal, timeline, importance.\n"
        "3. Why This Matters: Scientific, economic, strategic, or technological importance, and global impact.\n"
        "4. Healthy Debate: Balanced discussion of credible viewpoints (e.g. NASA vs CNSA, government vs private, Moon vs Mars, AI autonomy vs human control).\n"
        "5. Future Outlook: What happens next, challenges, responses.\n"
        "6. Community Question (Sentence 3): End with ONE engaging question (e.g. 'Which country do you think will lead the next space era?', 'Would you trust AI to control a Mars mission?').\n\n"
        "RETENTION RULES:\n"
        "- Strong qualitative hook (no fabricated statistics or numbers)\n"
        "- A surprising fact\n"
        "- A comparison between countries or missions\n"
        "- AI's role in the story\n"
        "- Why viewers should care\n"
        "- A future prediction (possibility, not fact)\n"
        "- A discussion question at the end\n\n"
        "CONTENT TONE:\n"
        "Documentary-style storytelling, cinematic narration, easy to understand, fast-paced, curiosity-driven, balanced, factual, inspirational, global perspective.\n\n"
        "Respond in valid JSON format only:\n"
        "{\n"
        "  \"title\": \"Curiosity-driven, stop-scrolling English title (e.g. 'Why is China investing billions in lunar AI?'), under 50 characters\",\n"
        "  \"hook\": \"The exact hook line provided in the prompt\",\n"
        "  \"narration\": \"A 20-second script that explains the viral angle. Include the hook as the first sentence. Make it sound dramatic, scientific but accessible, and fast-paced.\"\n"
        "}\n\n"
        "NON-NEGOTIABLE RULES:\n"
        "1. Start the narration exactly with the provided hook line.\n"
        "2. Keep the script between 45 and 55 words total for a strict 20-second pacing.\n"
        "3. Use plain English, avoiding overly dense scientific jargon, but sound authoritative.\n"
        "4. Information quality must be scientifically accurate. Do not exaggerate.\n"
        "5. The final result must sound like a premium documentary produced by a world-class creative studio.\n"
        "6. REWATCH LOOP & COMMENT BAITING: The script's final sentence MUST be a natural, discussion-promoting question to bait comments. Do NOT repeat or append the hook sentence at the end of the narration. The script must end with the question itself. Choose from or base it on these high-engagement questions:\n"
        "   - 'Which country do you think will lead the next space era?'\n"
        "   - 'Should countries compete or collaborate in space?'\n"
        "   - 'Would you trust AI to control a Mars mission?'\n"
        "   - 'Would you support building a permanent Moon base?'\n"
        "   - 'Is Mars the right destination, or should humanity focus elsewhere?'\n"
        "   - 'Which mission excites you the most?'\n"
        "   - 'Could AI discover alien life before humans?'\n"
        "7. EXOPLANET ACCURACY: Exoplanets orbit other stars, NOT our Sun. Always describe them as orbiting distant stars in other star systems.\n"
        "8. AUTO-DUBBING & TRANSLATION FRIENDLINESS: Avoid complex local idioms, localized slang, or metaphors. Use clean, globally standard grammar for seamless translation."
    )
    
    viral_angle = topic_data.get("viral_angle", "")
    
    user_prompt = (
        f"Generate a script for this viral concept:\n"
        f"Hook Line: {chosen_hook}\n"
        f"Viral Angle (What to explain): {viral_angle}\n\n"
        f"CRITICAL STRUCTURE REQUIREMENTS TO HIT THE 45-55 WORD RANGE:\n"
        f"Your script must contain exactly 3 concise, high-impact sentences:\n"
        f"Sentence 1 (Hook): Start exactly with the hook line (approx 8-12 words).\n"
        f"Sentence 2 (Explanation & Context): Write a single detailed sentence explaining what happened, why it matters, global impact, and controversy/different viewpoints of '{viral_angle}' (approx 18-24 words).\n"
        f"Sentence 3 (Loop Climax & Comment Bait): Write a final discussion-promoting question (approx 15-20 words) that baits viewers to leave comments. Do NOT repeat or append the hook line here. The narration must end with this question. The loop is created by the phrasing of the question leading grammatically into the hook when the video loops back to the start.\n\n"
        f"Count your words carefully. Ensure the script contains between 40 and 60 words total!"
    )
    
    logger.info(f"Calling Groq to generate Shortest Orbit script...")
    
    # Retry loop to guarantee a minimum length of 40 words and max of 60 words
    max_attempts = 5
    word_count = 0
    content = {}
    for attempt in range(max_attempts):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt if attempt == 0 else f"{user_prompt}\n\nCRITICAL: Your previous generation was {word_count} words. You MUST write a script that is strictly between 40 and 60 words total! Please write exactly 3 sentences."}
                ],
                model=model,
                temperature=0.7 + (attempt * 0.05),
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            response_text = chat_completion.choices[0].message.content
            content = json.loads(response_text)
            content["hooks_data"] = hooks_data
            
            # Clean title if it contains only hashtags or is empty
            title_val = content.get("title", "").strip()
            if not title_val or (title_val.startswith("#") and len(title_val.split()) > 0):
                cleaned_title = topic_data.get("selected_topic", "Space/Science Discovery")
                if len(cleaned_title) > 50:
                    cleaned_title = cleaned_title[:47] + "..."
                content["title"] = cleaned_title
                logger.warning(f"Sanitized title from raw hashtags to: '{content['title']}'")

            word_count = len(content["narration"].split())
            logger.info(f"Generated script (Attempt {attempt+1}/{max_attempts}). Word count: {word_count}")
            
            narration_text = content.get("narration", "").strip()
            ai_keywords = ["ai", "robot", "autonomous", "machine learning", "neural network", "algorithm", "automation", "artificial intelligence"]
            has_ai_element = any(kw in narration_text.lower() for kw in ai_keywords)
            if 40 <= word_count <= 60 and narration_text.endswith("?") and has_ai_element:
                import re
                sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', content["narration"]) if s.strip()]
                if not sentences:
                    sentences = [content["narration"]]
                    
                content["sentences"] = sentences
                content["word_count"] = word_count
                
                logger.info(f"Successfully generated script with adequate length: {content['title']}")
                return content
            else:
                logger.warning(f"Script verification failed (word count: {word_count}, ends with '?': {narration_text.endswith('?')}, has AI: {has_ai_element}). Retrying...")
                
        except Exception as e:
            logger.error(f"Error on attempt {attempt+1}: {e}")
            if attempt == max_attempts - 1:
                raise
                
    logger.warning(f"Failed to generate a script with at least 40 words after {max_attempts} attempts. Proceeding to avoid crashing.")
    
    # Clean title fallback
    title_val = content.get("title", "").strip()
    if not title_val or (title_val.startswith("#") and len(title_val.split()) > 0):
        cleaned_title = topic_data.get("selected_topic", "Space/Science Discovery")
        if len(cleaned_title) > 50:
            cleaned_title = cleaned_title[:47] + "..."
        content["title"] = cleaned_title
        logger.warning(f"Sanitized fallback title to: '{content['title']}'")

    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', content.get("narration", "")) if s.strip()]
    if not sentences:
        sentences = [content.get("narration", "")]
        
    content["sentences"] = sentences
    content["word_count"] = word_count
    content["hooks_data"] = hooks_data
    return content


def generate_metadata(topic: str, title: str) -> dict:
    """Generate YouTube metadata (description, tags, hashtags, translations) via Groq LLM."""
    api_key = get_groq_key()
    model = 'llama-3.3-70b-versatile' # Hardcode 70B for high-quality translations
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an elite YouTube SEO manager and copywriter.\n"
        "Your task is to generate metadata for a YouTube Short video, including translations for international auto-dubbing.\n"
        "Title Design: The title MUST be a highly curiosity-driven, clickbait-style question or a mind-bending hook that makes viewers stop scrolling. "
        "Do NOT write dry scientific labels (e.g., do NOT write 'Quantum AI Cancer Breakthrough'). Instead, frame it as an intriguing question or statement "
        "(e.g., 'What's behind Elon Musk's trillion-dollar bet on AI?' or 'Did scientists just crack the code to curing cancer?').\n"
        "Keep the title engaging and relevant, and ensure it contains the hashtag #Shorts.\n"
        "Create a description that invites clicks explaining the video clearly without hashtags. At the end of the description, append a new line with a recommended trending platform sound/song that perfectly matches the video's topic and emotion (e.g. '🎵 Sound: Interstellar Theme - Hans Zimmer' for space/physics, or '🎵 Sound: Metamorphosis (Phonk)' for AI/robotics, or an epic cinematic mythological song for Indian Mythology). This helps search indexing and Content ID matching.\n"
        "Translate the final English title and description (including the sound recommendation) into Spanish (es), Hindi (hi), French (fr), Portuguese (pt), and Telugu (te).\n"
        "CRITICAL: You MUST write both the titles and descriptions in their native scripts (e.g. use Hindi script for Hindi, Telugu script for Telugu, etc.). Do not write localized titles in English script unless the target language naturally uses it.\n"
        "CRITICAL JSON RULE: You MUST output raw, actual UTF-8 characters for localized text (e.g., write 'स्पेसएक्स' or 'తెలుగు' directly in the JSON). Do NOT output escaped Unicode escape sequences (like \\u0938). Escaped unicode sequences can cause validation failures.\n\n"
        "Respond in JSON format with the following keys:\n"
        "- title: catchy YouTube video title in English (must be a curiosity-inducing question or statement, and must end with #Shorts or contain #Shorts)\n"
        "- description: a 2-3 sentence description explaining the video in English, without adding hashtags\n"
        "- hashtags: an array of exactly 5-6 highly relevant, viral hashtags starting with # (e.g. ['#Shorts', '#Science', '#Space', '#AI', '#Physics', '#Technology'])\n"
        "- keywords: an array of 6-10 search keywords for tagging\n"
        "- category: standard YouTube category ID. Choose '28' (Science & Technology) if scientific, otherwise '22' (People & Blogs)\n"
        "- localizations: a dictionary containing translated titles and descriptions for 'es', 'hi', 'fr', 'pt', and 'te'. Follow this structure:\n"
        "  {\n"
        "    \"es\": { \"title\": \"catchy Spanish title ending with #Shorts\", \"description\": \"Spanish description\" },\n"
        "    \"hi\": { \"title\": \"catchy Hindi title ending with #Shorts\", \"description\": \"Hindi description\" },\n"
        "    \"fr\": { \"title\": \"catchy French title ending with #Shorts\", \"description\": \"French description\" },\n"
        "    \"pt\": { \"title\": \"catchy Portuguese title ending with #Shorts\", \"description\": \"Portuguese description\" },\n"
        "    \"te\": { \"title\": \"catchy Telugu title ending with #Shorts\", \"description\": \"Telugu description\" }\n"
        "  }"
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
            
        # Ensure #Shorts is in localized titles as well
        localizations = metadata.get("localizations", {})
        for lang, loc in localizations.items():
            if "title" in loc and "#shorts" not in loc["title"].lower():
                loc["title"] = f"{loc['title']} #Shorts"
            
        return metadata
    except Exception as e:
        logger.error(f"Error generating SEO metadata: {e}")
        # Fallback metadata
        return {
            "title": f"{title} #Shorts",
            "description": f"An educational look at {topic}. Discover the science behind this viral topic! #shorts #education #viral",
            "hashtags": ["#Shorts", "#Education", "#Science", "#Viral"],
            "keywords": [topic, "education", "science", "facts", "mystery"],
            "category": "28",
            "localizations": {}
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
    
    # Step 2c: Log to centralized database (shortest_orbit_v3.db) and separate platform databases
    youtube_video_id = 1
    topic_id = None
    
    # 1. Get topic_id from automation.db
    auto_conn = None
    try:
        auto_conn = get_automation_conn()
        auto_cursor = auto_conn.cursor()
        row = auto_cursor.execute("SELECT id FROM topics WHERE title = ?", (topic_str,)).fetchone()
        if row:
            topic_id = row["id"]
    except Exception as e:
        logger.warning(f"Could not find topic_id from automation.db: {e}")
    finally:
        if auto_conn:
            auto_conn.close()

    # 2. Write to central shortest_orbit_v3.db
    central_conn = None
    try:
        central_conn = get_connection()
        central_cursor = central_conn.cursor()
        central_cursor.execute("""
            INSERT INTO videos (title, topic_id, script, status)
            VALUES (?, ?, ?, ?)
        """, (content["title"], topic_id, content["narration"], "generating"))
        central_video_id = central_cursor.lastrowid
        central_conn.commit()
        logger.info(f"Video logged to central shortest_orbit_v3.db as ID: {central_video_id}")
    except Exception as e:
        logger.warning(f"Failed to log video to central shortest_orbit_v3.db: {e}")
    finally:
        if central_conn:
            central_conn.close()

    # 3. Write to youtube.db
    yt_conn = None
    try:
        yt_conn = get_youtube_conn()
        yt_cursor = yt_conn.cursor()
        yt_cursor.execute("""
            INSERT INTO videos (title, topic_id, script, status)
            VALUES (?, ?, ?, ?)
        """, (content["title"], topic_id, content["narration"], "generating"))
        youtube_video_id = yt_cursor.lastrowid
        yt_conn.commit()
        logger.info(f"Video logged to youtube.db as ID: {youtube_video_id}")
    except Exception as e:
        logger.warning(f"Failed to log video to youtube.db: {e}")
    finally:
        if yt_conn:
            yt_conn.close()

    # 4. Write to instagram.db
    ig_conn = None
    try:
        ig_conn = get_instagram_conn()
        ig_cursor = ig_conn.cursor()
        ig_cursor.execute("""
            INSERT INTO videos (title, topic_id, script, status)
            VALUES (?, ?, ?, ?)
        """, (content["title"], topic_id, content["narration"], "generating"))
        ig_conn.commit()
        logger.info("Video logged to instagram.db")
    except Exception as e:
        logger.warning(f"Failed to log video to instagram.db: {e}")
    finally:
        if ig_conn:
            ig_conn.close()

    # 5. Write to facebook.db
    fb_conn = None
    try:
        fb_conn = get_facebook_conn()
        fb_cursor = fb_conn.cursor()
        fb_cursor.execute("""
            INSERT INTO videos (title, topic_id, script, status)
            VALUES (?, ?, ?, ?)
        """, (content["title"], topic_id, content["narration"], "generating"))
        fb_conn.commit()
        logger.info("Video logged to facebook.db")
    except Exception as e:
        logger.warning(f"Failed to log video to facebook.db: {e}")
    finally:
        if fb_conn:
            fb_conn.close()

    # 6. Log hooks variations to automation.db
    auto_conn = None
    try:
        auto_conn = get_automation_conn()
        auto_cursor = auto_conn.cursor()
        hooks_list = content.get("hooks_data", [])
        for h in hooks_list:
            is_selected = 1 if h.get("text") == content.get("hook") else 0
            auto_cursor.execute("""
                INSERT INTO hooks (video_id, text, score, selected)
                VALUES (?, ?, ?, ?)
            """, (
                youtube_video_id, # linked to YouTube video index as standard
                h.get("text"),
                float(h.get("score", 50.0)),
                is_selected
            ))
        auto_conn.commit()
        logger.info("Video hooks logged to automation.db")
    except Exception as e:
        logger.warning(f"Failed to log hooks to automation.db: {e}")
    finally:
        if auto_conn:
            auto_conn.close()
        
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
