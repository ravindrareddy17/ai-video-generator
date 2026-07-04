"""
download_music.py — Step 7.5 of the AI Video Generator V2 pipeline.

Analyzes the video topic with Groq LLM to determine the content's mood,
then downloads a matching royalty-free background music track from Pixabay.

Inputs:
    data/content.json  (title / topic from Step 2)

Outputs:
    assets/music/background.mp3
"""

import sys
from pathlib import Path

import requests
from groq import Groq

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import MUSIC_DIR, CONTENT_FILE
from utils.config import get_groq_key, get_setting
from utils.logger import get_logger
from utils.helpers import load_json

logger = get_logger(__name__)

# Reliable royalty-free MP3 URLs for different moods
MUSIC_URLS: dict[str, str] = {
    "upbeat": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Decisions.mp3",
    "chill": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Deep%20Haze.mp3",
    "cinematic": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Industrial%20Cinematic.mp3",
    "inspiring": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Impact%20Lento.mp3",
    "ambient": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Echoes%20of%20Time.mp3",
    "lo-fi": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Deep%20Haze.mp3",
    "acoustic": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Decisions.mp3",
    "beats": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Decisions.mp3",
}

VALID_MOODS = list(MUSIC_URLS.keys())
DEFAULT_MOOD = "ambient"

DOWNLOAD_TIMEOUT_SECONDS = 60


def analyze_mood(topic: str) -> str:
    """Use Groq LLM to pick the best mood keyword for *topic*.

    Returns one of the valid mood keywords, falling back to DEFAULT_MOOD
    if the model returns something unexpected.
    """
    api_key = get_groq_key()
    model = get_setting("llm", "model", "llama-3.3-70b-versatile")
    client = Groq(api_key=api_key)

    mood_list = ", ".join(VALID_MOODS)
    system_prompt = (
        "You are a music supervisor for short-form video content.\n"
        "Given a video topic, pick the single best background music mood.\n\n"
        f"Choose EXACTLY ONE mood from this list: {mood_list}\n\n"
        "Rules:\n"
        "1. Reply with ONLY the mood keyword — nothing else.\n"
        "2. No punctuation, no explanation, no extra words.\n"
    )

    logger.info(f"Asking Groq to determine mood for topic: '{topic}'")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Video topic: {topic}"},
        ],
        temperature=0.3,
        max_tokens=16,
    )

    raw_mood = response.choices[0].message.content.strip().lower()
    logger.info(f"Groq returned mood: '{raw_mood}'")

    # Validate against the allowed moods
    if raw_mood in VALID_MOODS:
        return raw_mood

    # Try a fuzzy match (e.g. model returned "lo fi" instead of "lo-fi")
    normalised = raw_mood.replace(" ", "-")
    if normalised in VALID_MOODS:
        logger.info(f"Normalised mood '{raw_mood}' → '{normalised}'")
        return normalised

    logger.warning(
        f"Groq returned unrecognised mood '{raw_mood}'. "
        f"Falling back to '{DEFAULT_MOOD}'."
    )
    return DEFAULT_MOOD


def download_track(mood: str) -> Path:
    """Download the music track for *mood* to ``assets/music/background.mp3``.

    Any existing files in ``assets/music/`` are removed first so only
    the freshly-downloaded track is present for Step 8 (add_audio).

    Returns:
        Path to the downloaded MP3 file.
    """
    url = MUSIC_URLS[mood]
    output_path = MUSIC_DIR / "background.mp3"

    # Clean old music files
    logger.info(f"Cleaning old music files from {MUSIC_DIR}")
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in MUSIC_DIR.iterdir():
        if old_file.is_file():
            old_file.unlink()
            logger.debug(f"Removed old music file: {old_file.name}")

    # Download the track
    logger.info(f"Downloading '{mood}' music track from Pixabay CDN...")
    logger.debug(f"URL: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT_SECONDS, stream=True)
    response.raise_for_status()

    with output_path.open("wb") as fh:
        for chunk in response.iter_content(chunk_size=8192):
            fh.write(chunk)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(
        f"Music downloaded successfully: {output_path.name} "
        f"({size_mb:.2f} MB)"
    )
    return output_path


def run() -> Path:
    """Orchestrates Step 7.5 of the pipeline.

    1. Reads the video title/topic from content.json.
    2. Uses Groq to determine the best mood.
    3. Downloads the matching background music track.

    Returns:
        Path to the downloaded background music file.
    """
    logger.info("=== STEP 7.5: DOWNLOAD BACKGROUND MUSIC ===")

    # 1. Load topic from content.json
    if not CONTENT_FILE.exists():
        raise FileNotFoundError(
            f"Content file not found at {CONTENT_FILE}. Run Step 2 first."
        )

    content = load_json(CONTENT_FILE)
    
    # MythX schema provides audio_direction
    audio_direction = content.get("audio_direction", {})
    mood_keywords = audio_direction.get("mood_keywords", [])
    
    selected_mood = "cinematic"
    if mood_keywords:
        mood_str = " ".join(mood_keywords).lower()
        for valid_mood in MUSIC_URLS.keys():
            if valid_mood in mood_str:
                selected_mood = valid_mood
                break
    
    logger.info(f"Music mood determined as: '{selected_mood}' based on audio direction")
    mood = selected_mood

    # 3. Download the track
    music_path = download_track(mood)

    logger.info(f"Step 7.5 complete. Music file ready at: {music_path}")
    return music_path


if __name__ == "__main__":
    try:
        out = run()
        print(f"Music download complete. File saved at: {out}")
    except Exception as exc:
        logger.exception("download_music module execution failed")
        sys.exit(1)
