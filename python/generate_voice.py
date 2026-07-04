"""
generate_voice.py — Step 3 of the AI Video Generator V2 pipeline.

Uses edge-tts (Microsoft Edge Text-to-Speech) to generate a natural-sounding
narration audio file (voice.mp3) and captures precise sentence boundary timestamps.
Normalizes the volume using FFmpeg.

Inputs:
    data/content.json

Outputs:
    audio/voice.mp3 (volume-normalized)
    audio/word_timings.json (sentence boundary timing details)
"""

import sys
from pathlib import Path
import json
import asyncio
import edge_tts

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import CONTENT_FILE, VOICE_FILE, WORD_TIMINGS_FILE
from utils.config import get_setting, get_groq_key
from utils.logger import get_logger
from utils.helpers import load_json, save_json
from utils.ffmpeg import normalize_audio
from groq import Groq

logger = get_logger(__name__)

# Valid voice styles for LLM to choose from
VOICE_PROFILES = {
    "deep_story": {"voice": "en-US-SteffanNeural", "rate": "+3%"},
    "energetic": {"voice": "en-US-ChristopherNeural", "rate": "+8%"},
    "casual": {"voice": "en-US-GuyNeural", "rate": "+3%"},
    "serious": {"voice": "en-US-EricNeural", "rate": "+3%"},
}

def analyze_voice_style(topic: str) -> dict:
    """Use Groq LLM to pick the best voice style for the topic."""
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    client = Groq(api_key=api_key)
    
    style_list = ", ".join(VOICE_PROFILES.keys())
    system_prompt = (
        "You are a voice casting director.\n"
        f"Pick ONE voice style for this topic: {style_list}\n"
        "deep_story is for mysteries/history.\n"
        "energetic is for tech/fast-paced.\n"
        "casual is for lifestyle/fun.\n"
        "serious is for news/warnings.\n"
        "Respond with ONLY the exact keyword."
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Topic: {topic}"}
            ],
            temperature=0.3,
            max_tokens=10
        )
        style = response.choices[0].message.content.strip().lower()
        if style in VOICE_PROFILES:
            return VOICE_PROFILES[style]
    except Exception as e:
        logger.warning(f"Voice style selection failed: {e}")
        
    return VOICE_PROFILES["energetic"]  # Fallback


async def _generate_speech(text: str, voice: str, rate: str, pitch: str, output_path: Path) -> tuple[Path, list[dict]]:
    """Call edge-tts to generate voice narration and extract sentence boundary timings."""
    logger.info(f"Using Edge-TTS with voice='{voice}', rate='{rate}', pitch='{pitch}'")
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    word_timings = []
    
    # We write to a raw temp path first, then normalize it
    raw_audio_path = output_path.parent / "voice_raw.mp3"
    raw_audio_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Streaming audio from edge-tts to raw file: {raw_audio_path}")
    with open(raw_audio_path, 'wb') as f:
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                f.write(chunk['data'])
            elif chunk['type'] == 'SentenceBoundary':
                # edge-tts returns offset and duration in 100ns (nanoseconds) ticks.
                # 1 tick = 100ns = 1e-7 seconds = 0.0001 ms.
                # So to convert ticks to milliseconds: ticks / 10,000
                offset_ms = chunk['offset'] / 10000.0
                duration_ms = chunk['duration'] / 10000.0
                word_timings.append({
                    "offset_ms": offset_ms,
                    "duration_ms": duration_ms,
                    "text": chunk['text']
                })
                
    logger.info(f"Raw voice narration saved. Captured {len(word_timings)} sentence boundaries.")
    return raw_audio_path, word_timings


def run() -> Path:
    """Orchestrates Step 3 of the pipeline."""
    logger.info("=== STEP 3: GENERATE VOICE ===")
    
    if not CONTENT_FILE.exists():
        raise FileNotFoundError(f"Content file not found at {CONTENT_FILE}. Run Step 2 first.")
        
    content_data = load_json(CONTENT_FILE)
    narration_text = content_data.get("narration")
    title = content_data.get("title", "")
    if not narration_text:
        raise ValueError("No narration script found in content.json.")
        
    # Dynamically select voice style based on the video title/topic
    voice_profile = analyze_voice_style(title)
    voice = voice_profile["voice"]
    rate = voice_profile["rate"]
    pitch = get_setting('tts', 'pitch', '+0Hz')
    
    logger.info(f"Selected voice profile: {voice} at {rate} rate")
    
    # Configure event loop policy for Windows if needed
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    # Run async TTS speech generation
    logger.info("Starting speech generation...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        raw_audio_path, word_timings = loop.run_until_complete(
            _generate_speech(narration_text, voice, rate, pitch, VOICE_FILE)
        )
    finally:
        loop.close()
    
    # Save word timings (these contain sentence boundaries)
    save_json(word_timings, WORD_TIMINGS_FILE)
    logger.info(f"Word timings saved to {WORD_TIMINGS_FILE}")
    
    # Step 3b: Normalize volume of the audio
    logger.info(f"Normalizing audio volume of {raw_audio_path}...")
    try:
        normalize_audio(raw_audio_path, VOICE_FILE)
        logger.info(f"Normalized audio saved to final path: {VOICE_FILE}")
    except Exception as e:
        logger.error(f"Error during audio normalization: {e}. Falling back to copying raw audio.")
        # Fallback: copy raw audio to VOICE_FILE directly
        import shutil
        shutil.copy2(raw_audio_path, VOICE_FILE)
        
    # Clean up raw temp file
    if raw_audio_path.exists():
        try:
            raw_audio_path.unlink()
            logger.debug(f"Removed temporary raw audio file {raw_audio_path}")
        except Exception as e:
            logger.warning(f"Could not remove temp raw audio file: {e}")
            
    return VOICE_FILE


if __name__ == "__main__":
    try:
        out_path = run()
        print(f"Voice generation complete. File saved at: {out_path}")
    except Exception as exc:
        logger.exception("generate_voice module execution failed")
        sys.exit(1)
