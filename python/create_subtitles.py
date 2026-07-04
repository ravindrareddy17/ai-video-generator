import sys
from pathlib import Path
import json
import re

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import CONTENT_FILE, WORD_TIMINGS_FILE, SUBTITLES_FILE
from utils.logger import get_logger
from utils.helpers import load_json

logger = get_logger(__name__)

def format_timestamp(ms: float) -> str:
    if ms < 0:
        ms = 0.0
    total_ms = int(round(ms))
    hours, remainder = divmod(total_ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

def is_important(word_text, is_first):
    clean_word = re.sub(r"[^a-zA-Z0-9]", "", word_text)
    if not clean_word: return False
    
    # Proper nouns/names (capitalized and not first word)
    if not is_first and word_text[0].isupper():
        return True
    
    # Long words are usually important
    if len(clean_word) >= 6:
        return True
        
    return False

def generate_karaoke_srt(sentence_timings, chunk_size=5):
    srt_blocks = []
    block_index = 1
    
    for entry in sentence_timings:
        start_ms = entry["offset_ms"]
        duration_ms = entry["duration_ms"]
        sentence = entry["text"].strip()
        
        words = sentence.split()
        if not words:
            continue
            
        # Calculate time per character to distribute duration proportionally
        char_lengths = [len(re.sub(r"[^a-zA-Z0-9]", "", w)) for w in words]
        total_chars = sum(char_lengths)
        if total_chars == 0:
            total_chars = len(words)
            char_lengths = [1] * len(words)
            
        ms_per_char = duration_ms / total_chars
        
        # Calculate start and end times for each word
        word_spans = []
        current_time = start_ms
        for i, word in enumerate(words):
            word_dur = char_lengths[i] * ms_per_char
            word_spans.append({
                "word": word,
                "start": current_time,
                "end": current_time + word_dur,
                "is_important": is_important(word, i == 0)
            })
            current_time += word_dur
            
        # Group words into chunks
        chunks = [word_spans[i:i + chunk_size] for i in range(0, len(word_spans), chunk_size)]
        
        for chunk in chunks:
            start_ts = format_timestamp(chunk[0]["start"])
            end_ts = format_timestamp(chunk[-1]["end"])
            
            # Build the text for this block
            display_words = []
            for w in chunk:
                if w["is_important"]:
                    # Highlighted (Crimson Red BGR in ASS format is &H1F12C1&)
                    display_words.append(f"{{\\c&H1F12C1&}}{w['word']}{{\\c&HFFFFFF&}}")
                else:
                    display_words.append(w['word'])
                    
            text_line = " ".join(display_words)
            
            srt_blocks.append(f"{block_index}\n{start_ts} --> {end_ts}\n{text_line}")
            block_index += 1
                
    return "\n\n".join(srt_blocks) + "\n"

def run():
    logger.info("== Step 4: Create Karaoke Subtitles =========================")
    
    word_timings = load_json(WORD_TIMINGS_FILE)
    if not isinstance(word_timings, list) or len(word_timings) == 0:
        raise ValueError(f"Invalid timings in {WORD_TIMINGS_FILE}")
        
    srt_content = generate_karaoke_srt(word_timings, chunk_size=3)
    
    SUBTITLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUBTITLES_FILE.write_text(srt_content, encoding="utf-8")
    
    logger.info(f"Karaoke SRT written to {SUBTITLES_FILE}")
    return SUBTITLES_FILE

if __name__ == "__main__":
    run()
