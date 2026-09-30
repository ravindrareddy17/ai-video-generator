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

import re

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import VIRAL_TOPICS_FILE, CONTENT_FILE, METADATA_FILE, DATA_DIR
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
        "You are the world's #1 viral copywriter. Your hooks have generated BILLIONS of views on YouTube Shorts.\n"
        "Your task is to generate 3 different styles of hooks for this viral angle and score them.\n"
        "Styles:\n"
        "1. Curiosity Gap: Framed as an unsolvable mystery that FORCES the viewer to keep watching. Use 'Nobody talks about...', 'They don't want you to know...', 'What they're hiding about...'\n"
        "2. Shock/Awe: The single most JAW-DROPPING fact. Make the viewer's brain short-circuit. Use power words: EXPOSED, TERRIFYING, INSANE, BROKE, DESTROYED, SECRETLY.\n"
        "3. Controversy/Debate: A bold, divisive claim that splits opinion and FORCES comments. Pick a side. Be provocative.\n\n"
        "Evaluate and score each hook variation on a scale of 0.0 to 100.0 based on:\n"
        "- Stop-Scrolling Power (would someone PHYSICALLY stop scrolling?)\n"
        "- Emotional Trigger (fear, awe, outrage, curiosity)\n"
        "- Comment-Bait Potential (does this FORCE people to argue in comments?)\n"
        "- Brevity (under 10 words — shorter = more powerful)\n\n"
        "HOOK HONESTY RULE:\n"
        "Never fabricate specific statistics or exact percentages. But you CAN use dramatic framing, comparisons, and provocative questions based on real events.\n\n"
        "Respond in JSON format with this structure (replace the text values with your actual generated hooks based on the topic):\n"
        "{\n"
        "  \"hooks\": [\n"
        "    {\"style\": \"curiosity\", \"text\": \"[Write your actual curiosity hook here]\", \"score\": 85.0},\n"
        "    {\"style\": \"shock\", \"text\": \"[Write your actual shocking fact hook here]\", \"score\": 90.0},\n"
        "    {\"style\": \"controversy\", \"text\": \"[Write your actual controversial hook here]\", \"score\": 75.0}\n"
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
            from utils.config import call_groq_with_fallback
            completion = call_groq_with_fallback(
                client=client,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt if attempt == 0 else f"{user_prompt}\n\nCRITICAL: Make sure the hooks are highly engaging and score at least 85.0!"}
                ],
                initial_model=model,
                temperature=0.7 + (attempt * 0.1),
                response_format={"type": "json_object"}
            )
            from utils.helpers import extract_json_from_llm
            data = extract_json_from_llm(completion.choices[0].message.content)
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
    model = get_setting('llm', 'model', 'openai/gpt-oss-120b')
    
    client = Groq(api_key=api_key)
    
    # Optimize hook first
    chosen_hook, hooks_data = optimize_hook(topic_data, client, model)
    
    system_prompt = (
        "SYSTEM PROMPT - SPACE FRONTIER ENGINE MASTER PROMPT (v4.0 - Countries + AI + Space)\n\n"
        "You are an elite AI filmmaker, documentary editor, and storytelling expert.\n"
        "Your objective is to create a premium YouTube Shorts script (20 seconds max) that maximizes retention, "
        "watch time, and replay value while maintaining a luxury cinematic documentary aesthetic.\n\n"
        "CORE NICHE: You generate high-retention video scripts covering Space Exploration, Extreme Nature, Breakthrough Science, Technology, or AI.\n"
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
        "Documentary-style storytelling, cinematic narration, easy to understand, fast-paced, curiosity-driven.\n"
        "GROWTH & ENGAGEMENT HACK: To maximize virality and dominate the algorithm, make the content slightly controversial and edgy. Challenge popular beliefs, spark debate, and highlight intense global rivalries.\n"
        "FACTUAL REQUIREMENT: You MUST rely on the absolute latest, most original, and cutting-edge facts. Do NOT use generic or outdated knowledge.\n"
        "ENGAGEMENT BOOSTER: The narration MUST include a direct call-to-action phrase naturally woven into the script. Examples: 'Drop your answer below', 'Comment which side you're on', 'Tell us what you think'. This is CRITICAL for algorithm growth.\n\n"
        "Respond in valid JSON format only:\n"
        "{\n"
        "  \"title\": \"Curiosity-driven, stop-scrolling English title (e.g. 'Why is China investing billions in lunar AI?'), under 50 characters\",\n"
        "  \"hook\": \"The exact hook line provided in the prompt\",\n"
        "  \"narration\": \"A 20-second script that explains the viral angle. Include the hook as the first sentence. Make it sound dramatic, scientific but accessible, and fast-paced.\"\n"
        "}\n\n"
        "NON-NEGOTIABLE RULES:\n"
        "1. Start the narration exactly with the provided hook line.\n"
        "2. Keep the script between 75 and 105 words total for an ultra-fast, high-retention 35-40 second Short.\n"
        "3. Use plain English, avoiding overly dense scientific jargon, but sound authoritative.\n"
        "4. Information quality must be scientifically accurate. Do not exaggerate.\n"
        "5. The final result must sound like a premium documentary produced by a world-class creative studio.\n"
        "6. REWATCH LOOP & COMMENT BAITING: The script's final sentence MUST be a provocative, opinion-splitting question that FORCES viewers to comment. Do NOT repeat or append the hook sentence at the end of the narration. The script must end with the question itself. Make it divisive — pick a side! Choose from or base it on these high-engagement questions:\n"
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
    
    # Load audience feedback insights if available
    insights_guidelines = ""
    insights_path = DATA_DIR / "self_learning_insights.json"
    if insights_path.exists():
        try:
            with open(insights_path, "r", encoding="utf-8") as f:
                insights_data = json.load(f)
            hg = insights_data.get("viral_hook_guideline", "")
            pg = insights_data.get("pacing_and_length_adjustments", "")
            if hg or pg:
                insights_guidelines = f"\nAUDIENCE ENGAGEMENT CALIBRATION:\n- Hook Guideline: {hg}\n- Pacing Guideline: {pg}\n"
                logger.info("Injected self-learning guidelines into script generation prompt.")
        except Exception as ie:
            logger.warning(f"Could not read self-learning insights: {ie}")

    viral_angle = topic_data.get("viral_angle", "")
    
    user_prompt = (
        f"Generate a script for this viral concept:\n"
        f"Hook Line: {chosen_hook}\n"
        f"Viral Angle (What to explain): {viral_angle}\n"
        f"{insights_guidelines}\n"
        f"CRITICAL STRUCTURE REQUIREMENTS (75-105 WORDS TOTAL):\n"
        f"Your script must contain exactly 3 concise, high-impact sentences:\n"
        f"Sentence 1 (Hook): Start exactly with the hook line (approx 8-12 words).\n"
        f"Sentence 2 (Explanation & Conflict): Write dense, high-tension sentences explaining what happened, why it matters, global impact, and controversy/different viewpoints of '{viral_angle}' (approx 55-75 words).\n"
        f"Sentence 3 (Loop Climax & Comment Bait): Write a final discussion-promoting question (approx 12-18 words) that baits viewers to leave comments. Do NOT repeat or append the hook line here. The narration must end with this question.\n\n"
        f"Count your words carefully. Ensure the script contains between 75 and 105 words total for maximum viewer retention!"
    )
    
    logger.info(f"Calling Groq to generate Shortest Orbit script...")
    
    # Retry loop to guarantee high retention length of 75-105 words
    max_attempts = 3
    content = None
    
    for attempt in range(max_attempts):
        try:
            from utils.config import call_groq_with_fallback
            chat_completion = call_groq_with_fallback(
                client=client,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                initial_model="openai/gpt-oss-120b",
                temperature=0.7,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            
            response_text = chat_completion.choices[0].message.content
            from utils.helpers import extract_json_from_llm
            content = extract_json_from_llm(response_text)
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
            if 70 <= word_count <= 115 and narration_text.endswith("?"):
                import re
                sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', content["narration"]) if s.strip()]
                if not sentences:
                    sentences = [content["narration"]]
                    
                content["sentences"] = sentences
                content["word_count"] = word_count
                
                logger.info(f"Successfully generated script with optimal retention length: {content['title']}")
                return content
            else:
                logger.warning(f"Script verification failed (word count: {word_count}, ends with '?': {narration_text.endswith('?')}). Retrying...")
                
        except Exception as e:
            logger.error(f"Error on attempt {attempt+1}: {e}")
            if attempt == max_attempts - 1:
                raise
                
    logger.warning(f"Using fallback generated script. Proceeding.")
    
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
    """Generate YouTube metadata (description, tags, hashtags, translations) via Groq LLM with strict title variety."""
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    client = Groq(api_key=api_key)
    
    # Query last 15 titles to extract and block repetitive starting prefixes (e.g. "The HIDDEN...")
    blocked_prefixes = {"the hidden", "the untold", "hidden truth", "hidden ai", "the secret"}
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM videos WHERE title IS NOT NULL ORDER BY id DESC LIMIT 15")
            rows = cursor.fetchall()
            for r in rows:
                t_str = re.sub(r'^[^\w]+', '', str(r[0])).strip().lower()
                words = t_str.split()
                if len(words) >= 2:
                    blocked_prefixes.add(f"{words[0]} {words[1]}")
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"Could not load recent title prefixes: {e}")

    blocked_prefixes_str = ", ".join(sorted(list(blocked_prefixes))[:20])

    system_prompt = (
        "You are an elite YouTube SEO manager and copywriter specializing in viral YouTube Shorts.\n"
        "Your task is to generate metadata for a YouTube Short video, including translations for international auto-dubbing.\n\n"
        "1. TITLE DESIGN (MAXIMUM VIRALITY & VARIETY):\n"
        "STRICT DIVERSITY RULE: You MUST vary the title structure completely from past videos.\n"
        f"STRICTLY FORBIDDEN: NEVER start the title with 'The HIDDEN', 'The Untold', 'The Secret', or any of these recent prefixes:\n"
        f"[{blocked_prefixes_str}]\n\n"
        "Pick ONE of these 6 proven high-CTR viral title archetypes that best fits the video:\n"
        " - Archetype 1 (Intriguing Question): 'Can [Subject] Really Outsmart [Target]?' / 'Why Did [Entity] Just Ban This?'\n"
        " - Archetype 2 (Bizarre Paradox / Animal / Nature): '[Creature/Phenomenon] Defies All Laws of Nature' / '1-Ton Beast Disrespects [Target]'\n"
        " - Archetype 3 (High-Stakes Showdown): '[Entity A] vs [Entity B]: Who Survives?' / '[Entity] Caught in Sabotage'\n"
        " - Archetype 4 (Shocking Discovery): 'Scientists Stumbled Upon This by Complete Mistake' / 'What Was Found Deep Inside [Location]'\n"
        " - Archetype 5 (Human vs Machine): 'Robots Caught Doing What Humans Thought Impossible'\n"
        " - Archetype 6 (Urgent Breakthrough): 'A Dangerous Discovery That Changes [Field] in Seconds'\n\n"
        "CRITICAL TITLE LENGTH RULE: The English title MUST be UNDER 48 CHARACTERS (excluding #Shorts) so it doesn't get cut off on mobile Shorts feeds!\n"
        "Ensure it contains the hashtag #Shorts at the very end.\n\n"
        "2. DESCRIPTION & CALL-TO-ACTION SEO:\n"
        "Create a 2-sentence description that invites clicks, followed by a subscriber invitation:\n"
        "'Subscribe to @theshortestorbit for daily 30-second science, nature & space discoveries.'\n"
        "At the absolute end of the description, append a 'Trending Audio' SEO block:\n"
        "'🎧 Trending Audio: [Pick one: Interstellar Main Theme - Hans Zimmer | Metamorphosis (Phonk) | Blade Runner 2049 Synth | Paris - Else | Suspense Dark Cinematic]'\n\n"
        "3. VIRAL HASHTAGS:\n"
        "Select exactly 6 hashtags appropriate for the topic from this high-traffic list:\n"
        "#Shorts #Science #NatureIsMetal #SpaceExploration #ArtificialIntelligence #FutureTech #Astrophysics #UniverseMystery #OceanExploration #ScienceFacts #WildNature #TechBreakthrough\n\n"
        "4. LOCALIZATION:\n"
        "Translate the final English title and description (including the audio recommendation) into Spanish (es), Hindi (hi), French (fr), Portuguese (pt), and Telugu (te).\n"
        "CRITICAL: Write both the titles and descriptions in their native scripts (e.g. Hindi script for Hindi). Do not write localized titles in English script unless natural to the language.\n"
        "CRITICAL JSON RULE: Output raw UTF-8 characters (e.g., 'स्पेसएक्स'). Do NOT output escaped Unicode (like \\u0938).\n\n"
        "Respond in JSON format with the following keys:\n"
        "- title: The ultra-viral YouTube title in English (under 50 chars, ending with #Shorts)\n"
        "- description: 2-3 sentence description + subscribe CTA + trending audio block\n"
        "- hashtags: array of 6 hashtags chosen from the list above\n"
        "- keywords: array of 6-10 search keywords for tagging\n"
        "- category: '28' (Science & Technology)\n"
        "- localizations: dictionary containing 'es', 'hi', 'fr', 'pt', and 'te'. Format:\n"
        "  {\n"
        "    \"es\": { \"title\": \"catchy Spanish title #Shorts\", \"description\": \"Spanish description + audio\" },\n"
        "    \"hi\": { \"title\": \"catchy Hindi title #Shorts\", \"description\": \"Hindi description + audio\" },\n"
        "    ... \n"
        "  }"
    )
    
    user_prompt = f"Generate SEO metadata for a video on topic '{topic}' with script title '{title}'"
    
    logger.info("Calling Groq to generate YouTube metadata with high title variety...")
    try:
        from utils.config import call_groq_with_fallback
        from utils.helpers import extract_json_from_llm
        chat_completion = call_groq_with_fallback(
            client=client,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            initial_model=model,
            temperature=0.75,
            response_format={"type": "json_object"}
        )
        
        response_text = chat_completion.choices[0].message.content
        metadata = extract_json_from_llm(response_text)
        
        raw_title = metadata.get("title", title).strip()
        
        # Clean #Shorts from raw title for prefix analysis
        title_core = re.sub(r'#\w+', '', raw_title).strip()
        
        # Programmatic sanitization: Strip formulaic "The HIDDEN..." prefixes if LLM still hallucinated them
        lower_core = title_core.lower()
        for formulaic_prefix in [
            "the hidden truth about", "the hidden truth:", "the hidden truth", 
            "the hidden secret behind", "the hidden ai secret behind", "the hidden ai power",
            "the hidden ai pilot", "the hidden war between", "the hidden $", "the hidden",
            "the untold story of", "the untold story:", "the untold", "the secret behind", "the secret"
        ]:
            if lower_core.startswith(formulaic_prefix):
                title_core = title_core[len(formulaic_prefix):].strip()
                if title_core.startswith(":") or title_core.startswith("-"):
                    title_core = title_core[1:].strip()
                if title_core:
                    title_core = title_core[0].upper() + title_core[1:]
                logger.info(f"Sanitized formulaic title prefix -> '{title_core}'")
                break

        # Check against blocked prefixes from last 15 videos
        lower_sanitized = title_core.lower()
        for bp in blocked_prefixes:
            if lower_sanitized.startswith(bp) and len(title_core) > len(bp):
                title_core = title_core[len(bp):].strip()
                if title_core.startswith(":") or title_core.startswith("-"):
                    title_core = title_core[1:].strip()
                if title_core:
                    title_core = title_core[0].upper() + title_core[1:]
                logger.info(f"Sanitized repetitive title prefix '{bp}' -> '{title_core}'")
                break

        # Enforce mobile length: keep under 50 characters before #Shorts
        if len(title_core) > 50:
            title_core = title_core[:47].rsplit(" ", 1)[0] + "..."
            
        final_title = f"{title_core} #Shorts"
        metadata["title"] = final_title
        logger.info(f"Final Optimized Video Title: '{final_title}' ({len(final_title)} chars)")
            
        # Ensure #Shorts is in localized titles as well
        localizations = metadata.get("localizations", {})
        for lang, loc in localizations.items():
            if "title" in loc and "#shorts" not in loc["title"].lower():
                loc["title"] = f"{loc['title']} #Shorts"
            
        return metadata
    except Exception as e:
        logger.error(f"Error generating SEO metadata: {e}")
        # High quality fallback metadata
        clean_title = re.sub(r'^[^\w]+', '', title).strip()
        clean_topic = re.sub(r'^[^\w]+', '', topic).strip()
        if len(clean_title) > 48:
            clean_title = clean_title[:45] + "..."
        return {
            "title": f"{clean_title} #Shorts",
            "description": f"The untold science behind {clean_topic}.\n\n🚀 Subscribe to @theshortestorbit for daily 30-second science & nature breakdowns.\n\n🔥 Trending Audio: Interstellar Main Theme - Hans Zimmer",
            "hashtags": ["#Shorts", "#Science", "#NatureIsMetal", "#SpaceExploration", "#FutureTech", "#Viral"],
            "keywords": [clean_topic, "science", "nature", "space", "discovery", "mystery", "documentary"],
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
