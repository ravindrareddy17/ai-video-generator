import sys
from pathlib import Path
import json
import re

# Bootstrap imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import CONTENT_FILE, WORD_TIMINGS_FILE, SUBTITLES_FILE, SUBTITLES_ASS_FILE
from utils.logger import get_logger
from utils.helpers import load_json
from utils.config import get_setting

logger = get_logger(__name__)


def format_srt_timestamp(ms: float) -> str:
    """Format milliseconds into SRT timestamp: HH:MM:SS,mmm"""
    if ms < 0:
        ms = 0.0
    total_ms = int(round(ms))
    hours, remainder = divmod(total_ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def format_ass_timestamp(ms: float) -> str:
    """Format milliseconds into ASS timestamp: H:MM:SS.cc"""
    if ms < 0:
        ms = 0.0
    total_cs = int(round(ms / 10.0))
    hours, remainder = divmod(total_cs, 360000)
    minutes, remainder = divmod(remainder, 6000)
    seconds, centis = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centis:02d}"


def format_word_casing(w: str) -> str:
    """Format word so first letter is Capital and rest is small (Title Case)."""
    clean = re.sub(r"[^a-zA-Z0-9]", "", w)
    if not clean:
        return w
        
    lower = clean.lower()
    # Special tech brands & acronyms
    if lower == "spacex":
        return w.replace(clean, "SpaceX")
    if lower == "starlink":
        return w.replace(clean, "Starlink")
    if lower == "ai":
        return w.replace(clean, "AI")
    if lower == "5g":
        return w.replace(clean, "5G")
    if lower == "nasa":
        return w.replace(clean, "NASA")

    # If hyphenated word like low-orbit -> Low-Orbit
    if "-" in w or "‑" in w:
        parts = re.split(r"([‑\-])", w)
        return "".join([p.capitalize() if p not in ["-", "‑"] else p for p in parts])

    # Standard: First letter capital, rest lowercase
    prefix = ""
    for ch in w:
        if ch.isalpha():
            break
        prefix += ch
    body = w[len(prefix):]
    if body:
        return prefix + body[0].upper() + body[1:].lower()
    return w


def is_important(word_text: str, is_first: bool) -> bool:
    clean_word = re.sub(r"[^a-zA-Z0-9]", "", word_text).lower()
    if not clean_word:
        return False
    # Filter common stop words from being highlighted
    if clean_word in {"the", "and", "from", "with", "that", "this", "into", "over", "under", "about"}:
        return False
    # Proper nouns/names (capitalized in original) or key thematic words
    if clean_word in {"starlink", "spacex", "secretly", "hijacks", "thousands", "monopolies", "satellites", "router", "backbone"}:
        return True
    if len(clean_word) >= 7:
        return True
    return False


def build_word_spans(sentence_timings: list[dict]) -> list[dict]:
    """Calculate proportional word timestamps from sentence timing boundaries."""
    word_spans = []
    for entry in sentence_timings:
        start_ms = entry["offset_ms"]
        duration_ms = entry["duration_ms"]
        sentence = entry["text"].strip()
        words = sentence.split()
        if not words:
            continue
            
        char_lengths = [len(re.sub(r"[^a-zA-Z0-9]", "", w)) for w in words]
        total_chars = sum(char_lengths)
        if total_chars == 0:
            total_chars = len(words)
            char_lengths = [1] * len(words)
            
        ms_per_char = duration_ms / total_chars
        current_time = start_ms
        for i, word in enumerate(words):
            word_dur = char_lengths[i] * ms_per_char
            cased_word = format_word_casing(word)
            word_spans.append({
                "raw_word": word,
                "word": cased_word,
                "start": current_time,
                "end": current_time + word_dur,
                "is_important": is_important(word, i == 0)
            })
            current_time += word_dur
    return word_spans


def generate_karaoke_ass(word_spans: list[dict], chunk_size: int = 2, outro_cutoff_ms: float = None) -> str:
    """Generate high-end, responsive ASS subtitle script matching viral creator typography."""
    font_name = get_setting('subtitles', 'font', 'Plus Jakarta Sans ExtraBold')
    font_size = get_setting('subtitles', 'fontsize', 86)
    margin_v = get_setting('subtitles', 'margin_vertical', 440)
    outline_width = get_setting('subtitles', 'outline_width', 6.5)
    highlight_tag = get_setting('subtitles', 'highlight_color', '&H00E6FF&')
    if not highlight_tag.startswith("&H"):
        highlight_tag = f"&H{highlight_tag}"
    if not highlight_tag.endswith("&"):
        highlight_tag = f"{highlight_tag}&"

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline_width},2.5,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogues = []
    chunks = [word_spans[i:i + chunk_size] for i in range(0, len(word_spans), chunk_size)]
    
    for chunk in chunks:
        start_ms = chunk[0]["start"]
        end_ms = chunk[-1]["end"]
        
        # Stop subtitles during outro animation to keep screen 100% clean
        if outro_cutoff_ms and start_ms >= outro_cutoff_ms:
            continue
        if outro_cutoff_ms and end_ms > outro_cutoff_ms:
            end_ms = outro_cutoff_ms
            
        start_ts = format_ass_timestamp(start_ms)
        end_ts = format_ass_timestamp(end_ms)
        
        # Format chunk words with golden accent highlight for important words (Combo 1: Cyber Gold #FFE600)
        formatted_words = []
        for w in chunk:
            if w["is_important"]:
                formatted_words.append(f"{{\\c{highlight_tag}}}{w['word']}{{\\c&HFFFFFF&}}")
            else:
                formatted_words.append(w["word"])
                
        line_text = " ".join(formatted_words)
        dialogues.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{line_text}")
        
    return header + "\n".join(dialogues) + "\n"


def generate_karaoke_srt(word_spans: list[dict], chunk_size: int = 2, outro_cutoff_ms: float = None) -> str:
    """Generate SRT format with Title Case and HTML color tags."""
    srt_blocks = []
    block_index = 1
    chunks = [word_spans[i:i + chunk_size] for i in range(0, len(word_spans), chunk_size)]
    
    for chunk in chunks:
        start_ms = chunk[0]["start"]
        end_ms = chunk[-1]["end"]
        
        if outro_cutoff_ms and start_ms >= outro_cutoff_ms:
            continue
        if outro_cutoff_ms and end_ms > outro_cutoff_ms:
            end_ms = outro_cutoff_ms
            
        start_ts = format_srt_timestamp(start_ms)
        end_ts = format_srt_timestamp(end_ms)
        
        display_words = []
        for w in chunk:
            if w["is_important"]:
                display_words.append(f"<font color=\"#FFE600\">{w['word']}</font>")
            else:
                display_words.append(w["word"])
                
        text_line = " ".join(display_words)
        srt_blocks.append(f"{block_index}\n{start_ts} --> {end_ts}\n{text_line}")
        block_index += 1
        
    return "\n\n".join(srt_blocks) + "\n"


def run() -> Path:
    logger.info("== Step 4: Create Karaoke Subtitles (Plus Jakarta Sans, Lower-Third, Title Case) ==")
    
    word_timings = load_json(WORD_TIMINGS_FILE)
    if not isinstance(word_timings, list) or len(word_timings) == 0:
        raise ValueError(f"Invalid timings in {WORD_TIMINGS_FILE}")
        
    word_spans = build_word_spans(word_timings)
    
    # Calculate outro cutoff: 5.5s before end of speech/video
    total_speech_ms = word_spans[-1]["end"] if word_spans else 0.0
    outro_cutoff_ms = max(0.0, total_speech_ms - 5500.0) if total_speech_ms > 12000.0 else None
    
    # 1. Generate ASS (Primary)
    ass_content = generate_karaoke_ass(word_spans, chunk_size=2, outro_cutoff_ms=outro_cutoff_ms)
    SUBTITLES_ASS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUBTITLES_ASS_FILE.write_text(ass_content, encoding="utf-8")
    logger.info(f"Karaoke ASS written to {SUBTITLES_ASS_FILE}")
    
    # 2. Generate SRT (Fallback)
    srt_content = generate_karaoke_srt(word_spans, chunk_size=2, outro_cutoff_ms=outro_cutoff_ms)
    SUBTITLES_FILE.write_text(srt_content, encoding="utf-8")
    logger.info(f"Karaoke SRT written to {SUBTITLES_FILE}")
    
    return SUBTITLES_ASS_FILE


if __name__ == "__main__":
    run()
