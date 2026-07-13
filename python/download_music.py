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

# Reliable viral and trending music profiles with direct MP3 streams
MUSIC_URLS: dict[str, list[str]] = {
    "viral-phonk-ai": [
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Neon%20Laser%20Horizon.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Voxel%20Revolution.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Blippy%20Trance.mp3",
    ],
    "viral-space-epic": [
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Canon%20In%20D%20Interstellar%20Mix.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sovereign.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/The%20Ice%20Giants.mp3",
    ],
    "viral-mythology-epic": [
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Temple%20of%20the%20Manes.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sati.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/The%20Descent.mp3",
    ],
    "viral-wildlife-adventure": [
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Carefree.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Cattails.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Heartwarming.mp3",
    ],
    "viral-mystery-dark": [
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Mystic%20Force.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Echoes%20of%20Time.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Quiet%20Panic.mp3",
    ],
    "viral-history-epic": [
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sovereign.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/The%20Ice%20Giants.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Industrial%20Cinematic.mp3",
    ],
    "viral-science-tech": [
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Newer%20Wave.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Winner%20Winner.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Double%20Drift.mp3",
    ],
}

VALID_MOODS = list(MUSIC_URLS.keys())
DEFAULT_MOOD = "viral-space-epic"

DOWNLOAD_TIMEOUT_SECONDS = 60


def analyze_mood(topic: str) -> str:
    """Use Groq LLM to pick the best viral music profile for *topic*.

    Returns one of the valid viral keys, falling back to DEFAULT_MOOD.
    """
    api_key = get_groq_key()
    model = get_setting("llm", "model", "llama-3.3-70b-versatile")
    client = Groq(api_key=api_key)

    mood_list = ", ".join(VALID_MOODS)
    system_prompt = (
        "You are an expert AI Audio Supervisor & Short-Form Content Strategist.\n"
        "Your sole objective is to select the perfect viral audio profile for a short video to maximize audience retention, replays, and engagement.\n\n"
        "Analyze the provided video topic across these dimensions:\n"
        "1. Niche & Topic (AI/Tech, Space/Physics, Biology/Wildlife, Indian Mythology, Mystery/Dark, History, Science)\n"
        "2. Storytelling & Emotion (Futuristic, Cosmic/Inspiring, Epic/Devotional, Adventurous, Suspenseful/Dark, Dramatic)\n"
        "3. Energy & Editing Pace (High Energy, Slow Suspense, Epic Build-up, Upbeat/Energetic)\n\n"
        "Choose EXACTLY ONE profile key from this list:\n"
        f"{mood_list}\n\n"
        "Rules:\n"
        "1. Reply with ONLY the profile key string (e.g. 'viral-phonk-ai') — nothing else.\n"
        "2. No punctuation, no explanation, no markdown backticks, no extra words.\n"
        "3. Match mythology/devotional topics to 'viral-mythology-epic'; match exoplanets/astrophysics to 'viral-space-epic'; match AI/code/robots to 'viral-phonk-ai'; match animals/nature to 'viral-wildlife-adventure'; match physics/science to 'viral-science-tech'; match history/historical events to 'viral-history-epic'; match suspense/crime/horror/mysteries to 'viral-mystery-dark'."
    )

    logger.info(f"Asking Groq to determine viral audio profile for topic: '{topic}'")

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
    logger.info(f"Groq returned profile: '{raw_mood}'")

    # Validate against the allowed profiles
    if raw_mood in VALID_MOODS:
        return raw_mood

    # Try a fuzzy match
    normalised = raw_mood.replace(" ", "-")
    if normalised in VALID_MOODS:
        logger.info(f"Normalised profile '{raw_mood}' → '{normalised}'")
        return normalised

    logger.warning(
        f"Groq returned unrecognised profile '{raw_mood}'. "
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
    import random
    urls = MUSIC_URLS[mood]
    url = random.choice(urls)
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
    
    # 2. Analyze mood via Groq LLM based on video title
    mood = analyze_mood(content.get("title", ""))

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
