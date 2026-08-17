"""
generate_search_queries.py — Step 5 of the AI Video Generator V2 pipeline.

Parses captions/voice.srt, extracts sentences, and calls the Groq LLM to
generate visual search queries for each sentence (suitable for stock video search).

Inputs:
    captions/voice.srt
    data/content.json

Outputs:
    data/search_queries.json
"""

import sys
from pathlib import Path
import json
import re
from groq import Groq

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import WORD_TIMINGS_FILE, CONTENT_FILE, SEARCH_QUERIES_FILE
from utils.config import get_groq_key, get_setting
from utils.logger import get_logger
from utils.helpers import load_json, save_json

logger = get_logger(__name__)


def srt_time_to_ms(time_str: str) -> float:
    """Convert an SRT timestamp string (HH:MM:SS,mmm) to milliseconds."""
    match = re.match(r"(\d+):(\d+):(\d+),(\d+)", time_str)
    if not match:
        raise ValueError(f"Invalid SRT timestamp format: {time_str}")
        
    hours, minutes, seconds, millis = map(int, match.groups())
    total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + millis
    return float(total_ms)


def load_sentence_timings(timings_path: Path) -> list[dict]:
    """Parse word_timings.json (which contains sentence boundaries) into subtitle entries."""
    if not timings_path.exists():
        raise FileNotFoundError(f"Timings file does not exist at: {timings_path}")
        
    logger.info(f"Parsing sentence timings file: {timings_path}")
    raw_timings = load_json(timings_path)
    
    def format_timestamp(ms: float) -> str:
        if ms < 0:
            ms = 0.0
        total_ms = int(round(ms))
        hours, remainder = divmod(total_ms, 3600000)
        minutes, remainder = divmod(remainder, 60000)
        seconds, millis = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
    
    subtitles = []
    
    for i, entry in enumerate(raw_timings, start=1):
        try:
            start_ms = entry["offset_ms"]
            duration_ms = entry["duration_ms"]
            end_ms = start_ms + duration_ms
            duration_s = duration_ms / 1000.0
            text = entry["text"].strip()
            
            start_str = format_timestamp(start_ms)
            end_str = format_timestamp(end_ms)
            
            subtitles.append({
                "index": i,
                "start": start_str,
                "end": end_str,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_s": duration_s,
                "text": text
            })
        except Exception as e:
            logger.error(f"Error parsing timing entry: {entry}. Error: {e}")
            
    logger.info(f"Loaded {len(subtitles)} sentence entries from timings.")
    return subtitles


def generate_queries(subtitles: list[dict]) -> list[dict]:
    """Call Groq to generate a search query for each subtitle sentence."""
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    client = Groq(api_key=api_key)
    
    # Build list of subtitles for the user prompt
    input_items = []
    for sub in subtitles:
        input_items.append({
            "index": sub["index"],
            "text": sub["text"]
        })
    system_prompt = (
        "You are an expert Hollywood Film Editor and Visual Director.\n"
        "Your task is to extract the EXACT PHYSICAL SUBJECT / OBJECT from each narration sentence into concrete stock video search terms.\n"
        "EVERY SCENE MUST BE A REAL VIDEO CLIP (type: 'video').\n\n"
        "RULES:\n"
        "1. Extract the primary PHYSICAL SUBJECT of the sentence as 'query' (1-2 simple, concrete nouns, e.g. 'rocket launch', 'satellite', 'sun flare', 'telescope', 'planet earth', 'computer server', 'astronaut'). NEVER use abstract terms like 'code', 'budget', or 'impact'.\n"
        "2. Provide 2 simple concrete alternative terms in 'fallback_queries' (e.g. ['rocket', 'spaceship']).\n"
        "3. Stock video search engines index SIMPLE CONCRETE NOUNS best. Keep terms short and direct.\n\n"
        "Respond in JSON format with the following structure:\n"
        "{\n"
        "  \"queries\": [\n"
        "    {\n"
        "       \"index\": 1,\n"
        "       \"type\": \"video\",\n"
        "       \"query\": \"rocket launch\",\n"
        "       \"fallback_queries\": [\"rocket\", \"spacecraft\"]\n"
        "    },\n"
        "    ...\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = f"Generate search queries for these narration lines:\n\n{json.dumps(input_items, indent=2)}"
    
    logger.info("Calling Groq LLM to generate visual search queries...")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        response_text = chat_completion.choices[0].message.content
        result_json = json.loads(response_text)
        queries_list = result_json.get("queries", [])
        
        query_map = {item.get("index"): item.get("query", "space motion") for item in queries_list}
        fallback_map = {item.get("index"): item.get("fallback_queries", []) for item in queries_list}
        prompt_map = {item.get("index"): "" for item in queries_list}
        type_map = {item.get("index"): "video" for item in queries_list}
        
        output_queries = []
        for sub in subtitles:
            q = query_map.get(sub["index"], "space motion")
            fb = fallback_map.get(sub["index"], [])
            t = "video"
            # Sanitize query (remove punctuation, normalize spaces)
            q = re.sub(r'[^\w\s]', '', q).strip().lower()
            if not q:
                q = "space motion"
                
            clean_fallbacks = []
            for f in fb:
                cf = re.sub(r'[^\w\s]', '', str(f)).strip().lower()
                if cf:
                    clean_fallbacks.append(cf)
                    
            output_queries.append({
                "subtitle_index": sub["index"],
                "text": sub["text"],
                "type": t,
                "query": q,
                "fallback_queries": clean_fallbacks,
                "image_prompt": "",
                "start": sub["start"],
                "end": sub["end"],
                "start_ms": sub["start_ms"],
                "end_ms": sub["end_ms"],
                "duration_s": sub["duration_s"]
            })
            
        return output_queries
        
    except Exception as e:
        logger.error(f"Error calling Groq for search queries: {e}")
        # Return fallback queries based on keywords in each sentence
        logger.warning("Using fallback keyword extraction for search queries.")
        output_queries = []
        for sub in subtitles:
            # simple fallback: take first 3 words of text
            words = [w.strip().lower() for w in sub["text"].split() if len(w) > 3][:3]
            q = " ".join(words) if words else "science background"
            output_queries.append({
                "subtitle_index": sub["index"],
                "text": sub["text"],
                "query": q,
                "start": sub["start"],
                "end": sub["end"],
                "start_ms": sub["start_ms"],
                "end_ms": sub["end_ms"],
                "duration_s": sub["duration_s"]
            })
        return output_queries


def run() -> list[dict]:
    """Orchestrates Step 5 of the pipeline."""
    logger.info("=== STEP 5: GENERATE SEARCH QUERIES ===")
    
    if not WORD_TIMINGS_FILE.exists():
        raise FileNotFoundError(f"Timings file not found at {WORD_TIMINGS_FILE}. Run Step 3 first.")
        
    subtitles = load_sentence_timings(WORD_TIMINGS_FILE)
    if not subtitles:
        raise ValueError("Loaded timings are empty or invalid.")
        
    queries = generate_queries(subtitles)
    save_json(queries, SEARCH_QUERIES_FILE)
    logger.info(f"Search queries saved to {SEARCH_QUERIES_FILE}")
    
    return queries


if __name__ == "__main__":
    try:
        results = run()
        print(json.dumps(results, indent=2))
    except Exception as exc:
        logger.exception("generate_search_queries module execution failed")
        sys.exit(1)
