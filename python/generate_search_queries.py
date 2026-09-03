"""
generate_search_queries.py — Step 5 of the AI Video Generator V2 pipeline.

Parses word timings / sentence boundaries, combines overall topic context with
specific physical sentence actions, and calls LLM to generate highly accurate,
cinematic visual search queries for stock video search.

Uses call_groq_with_fallback() and extract_json_from_llm() for 100% LLM resiliency.

Inputs:
    captions/word_timings.json
    data/content.json

Outputs:
    data/search_queries.json
"""

import sys
from pathlib import Path
import json
import re

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import WORD_TIMINGS_FILE, CONTENT_FILE, SEARCH_QUERIES_FILE
from utils.config import call_groq_with_fallback
from utils.logger import get_logger
from utils.helpers import load_json, save_json, extract_json_from_llm

logger = get_logger(__name__)


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


def split_into_visual_beats(subtitles: list[dict], max_beat_duration: float = 2.8) -> list[dict]:
    """Splits long sentence entries into fast 1.8s-2.8s visual beats for maximum retention."""
    def format_timestamp(ms: float) -> str:
        if ms < 0:
            ms = 0.0
        total_ms = int(round(ms))
        hours, remainder = divmod(total_ms, 3600000)
        minutes, remainder = divmod(remainder, 60000)
        seconds, millis = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

    beats = []
    beat_index = 1

    for sub in subtitles:
        dur = sub["duration_s"]
        if dur <= max_beat_duration:
            entry = dict(sub)
            entry["index"] = beat_index
            beats.append(entry)
            beat_index += 1
        else:
            # Calculate number of sub-beats (target 2.2s - 2.8s per beat)
            num_beats = max(2, int(round(dur / 2.5)))
            beat_dur_s = dur / num_beats
            beat_dur_ms = (sub["end_ms"] - sub["start_ms"]) / num_beats

            # Split text words into chunks
            words = sub["text"].split()
            words_per_beat = max(1, int(round(len(words) / num_beats)))

            for b in range(num_beats):
                b_start_ms = sub["start_ms"] + (b * beat_dur_ms)
                b_end_ms = sub["start_ms"] + ((b + 1) * beat_dur_ms) if b < num_beats - 1 else sub["end_ms"]
                b_dur_s = (b_end_ms - b_start_ms) / 1000.0

                w_start = b * words_per_beat
                w_end = (b + 1) * words_per_beat if b < num_beats - 1 else len(words)
                b_text = " ".join(words[w_start:w_end]) if w_start < len(words) else sub["text"]

                beats.append({
                    "index": beat_index,
                    "sentence_index": sub["index"],
                    "start": format_timestamp(b_start_ms),
                    "end": format_timestamp(b_end_ms),
                    "start_ms": b_start_ms,
                    "end_ms": b_end_ms,
                    "duration_s": b_dur_s,
                    "text": b_text
                })
                beat_index += 1

    avg_dur = sum(b['duration_s'] for b in beats) / len(beats) if beats else 0.0
    logger.info(f"Split {len(subtitles)} sentences into {len(beats)} fast visual beats (avg {avg_dur:.2f}s per beat).")
    return beats


def generate_queries(subtitles: list[dict], topic_info: dict) -> list[dict]:
    """Call LLM with topic context to generate accurate visual search queries for stock videos."""
    topic_title = topic_info.get("topic", topic_info.get("title", "Space & Future Tech"))
    content_pillar = topic_info.get("content_pillar", "Space Race")
    
    # Pre-process subtitles into fast 2.0s - 2.8s visual beats
    sub_beats = split_into_visual_beats(subtitles, max_beat_duration=3.0)

    input_items = []
    for sub in sub_beats:
        input_items.append({
            "index": sub["index"],
            "phrase": sub["text"],
            "duration_s": round(sub["duration_s"], 2)
        })
        
    system_prompt = (
        "You are an Elite Visual Director for viral educational explainer Shorts.\n"
        "Your task is to analyze each fast visual beat and determine the OPTIMAL VISUAL STYLE to communicate the concept clearly and dynamically.\n\n"
        "THREE VISUAL STYLES AVAILABLE:\n"
        "1. 'doodle' (Authentic Hand-Drawn Doodle Art):\n"
        "   Use for: Simple concepts, analogies, definitions, human brain/behavior, internal biological/physical mechanisms, or abstract ideas.\n"
        "2. 'cinematic' (Ultra-Realistic 4K Cinematic AI / Motion Footage):\n"
        "   Use for: Real physical environments, deep ocean, cosmos/space, rockets, megaprojects, heavy machines, cities, weather phenomena.\n"
        "3. 'map_motion' (3D Maps & Motion Explainer Graphics):\n"
        "   Use for: Geography, countries, borders, routes, trade chokepoints, statistics, timelines, networks, or multi-nation comparisons.\n\n"
        "RULES:\n"
        "- Choose the visual style intelligently per beat based on the subject.\n"
        "- Provide a targeted physical search query (1-3 words) in 'query'.\n"
        "- Provide a descriptive prompt for AI image/map generation in 'prompt'.\n"
        "- Select a camera motion in 'camera_motion' ('zoom_in', 'pan_up', 'aerial_track', 'sketch_reveal', 'route_travel').\n"
        "- Output strictly valid JSON matching this schema:\n"
        "{\n"
        "  \"queries\": [\n"
        "    {\n"
        "       \"index\": 1,\n"
        "       \"visual_style\": \"cinematic\",\n"
        "       \"query\": \"black hole accretion disc\",\n"
        "       \"prompt\": \"Cinematic 4K cosmic black hole with swirling accretion disc\",\n"
        "       \"fallback_queries\": [\"black hole\", \"accretion disc\", \"deep space\"],\n"
        "       \"camera_motion\": \"zoom_in\",\n"
        "       \"accent_color\": \"orange\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = (
        f"OVERALL TOPIC: {topic_title}\n"
        f"CONTENT PILLAR: {content_pillar}\n\n"
        f"NARRATION SENTENCES:\n{json.dumps(input_items, indent=2)}"
    )
    
    logger.info("Calling Visual Decision Director to classify and formulate visual scenes...")
    raw_response = call_groq_with_fallback(system_prompt, user_prompt, temperature=0.3)
    
    if hasattr(raw_response, "choices") and raw_response.choices:
        response_text = raw_response.choices[0].message.content
    elif hasattr(raw_response, "text"):
        response_text = raw_response.text
    elif hasattr(raw_response, "content"):
        response_text = raw_response.content
    else:
        response_text = str(raw_response)

    logger.info(f"RAW LLM RESPONSE RECV: {repr(response_text)[:200]}")

    try:
        result_json = extract_json_from_llm(response_text)
        queries_list = result_json.get("queries", [])
        
        item_map = {item.get("index"): item for item in queries_list}
        
        output_queries = []
        for sub in sub_beats:
            item = item_map.get(sub["index"], {})
            v_style = item.get("visual_style", "cinematic")
            if v_style not in ["doodle", "cinematic", "map_motion"]:
                # Auto-infer style from sentence content
                text_lower = sub["text"].lower()
                if any(w in text_lower for w in ["country", "nation", "map", "china", "u.s.", "eu", "border", "route", "percent"]):
                    v_style = "map_motion"
                elif any(w in text_lower for w in ["brain", "think", "concept", "imagine", "mean", "freeze", "what if"]):
                    v_style = "doodle"
                else:
                    v_style = "cinematic"

            q = item.get("query", "space motion")
            fb = item.get("fallback_queries", [])
            prompt_desc = item.get("prompt", sub["text"])
            camera_motion = item.get("camera_motion", "zoom_in")
            accent_color = item.get("accent_color", "orange")
            
            # Sanitize query
            q_clean = re.sub(r'[^\w\s]', '', q).strip().lower()
            if not q_clean:
                q_clean = "space motion"
                
            clean_fallbacks = []
            for f in fb:
                cf = re.sub(r'[^\w\s]', '', str(f)).strip().lower()
                if cf and cf not in clean_fallbacks:
                    clean_fallbacks.append(cf)
                    
            output_queries.append({
                "subtitle_index": sub["index"],
                "text": sub["text"],
                "visual_style": v_style,
                "type": "video",
                "query": q_clean,
                "prompt": prompt_desc,
                "fallback_queries": clean_fallbacks,
                "camera_motion": camera_motion,
                "accent_color": accent_color,
                "image_prompt": prompt_desc,
                "start": sub["start"],
                "end": sub["end"],
                "start_ms": sub["start_ms"],
                "end_ms": sub["end_ms"],
                "duration_s": sub["duration_s"]
            })
            
        logger.info(f"Visual Decision Director assigned styles to {len(output_queries)} beats: {[q['visual_style'] for q in output_queries]}")
        return output_queries
        
    except Exception as e:
        logger.error(f"Error parsing LLM response for visual director: {e}")
        # Rule fallback based on sentence keywords
        output_queries = []
        for sub in sub_beats:
            words = [w.strip().lower() for w in sub["text"].split() if len(w.strip()) > 3][:2]
            q = (" ".join(words) + " space") if words else "space motion"
            output_queries.append({
                "subtitle_index": sub["index"],
                "text": sub["text"],
                "type": "video",
                "query": q,
                "fallback_queries": ["rocket launch", "satellite orbit", "space motion"],
                "image_prompt": "",
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
        
    topic_info = load_json(CONTENT_FILE) if CONTENT_FILE.exists() else {}
    queries = generate_queries(subtitles, topic_info)
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
