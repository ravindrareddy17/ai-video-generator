import sys, os, time, json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import get_logger
from utils.ffmpeg import verify_ffmpeg, get_duration, get_video_info
from utils.paths import OUTPUT_DIR, TEMP_DIR, FINAL_VIDEO_FILE, CONTENT_FILE

import python.generate_voice as generate_voice
import python.create_subtitles as create_subtitles
import python.generate_search_queries as generate_search_queries
import python.multi_style_generator as multi_style_generator
import python.create_video as create_video
import python.download_music as download_music
import python.add_audio as add_audio
import python.burn_subtitles as burn_subtitles

logger = get_logger("demo_generator")

def generate_demo():
    print("=" * 60)
    print("🎬 RENDERING DEMO VIDEO WITH ALL NEW UPGRADES")
    print("=" * 60)
    
    if not verify_ffmpeg():
        print("❌ FFmpeg verification failed!")
        return False
        
    start_time = time.time()
    
    # Check content
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        content = json.load(f)
    print(f"  👉 Title: {content.get('title')}")
    print(f"  👉 Script: {content.get('narration')}")
    
    # 3. Voice Synthesis
    print("\n[1/6] Synthesizing neural voiceover via EdgeTTS...")
    voice_path = generate_voice.run()
    print(f"  👉 Voice generated: {voice_path.name}")
    
    # 4. Subtitles
    print("\n[2/6] Generating karaoke word-timed subtitles...")
    srt_path = create_subtitles.run()
    print(f"  👉 Subtitles generated: {srt_path.name}")
    
    # 5. Visual Queries (Fixed item mapping!)
    print("\n[3/6] Generating scene-matched visual queries (fixed item mapping)...")
    queries = generate_search_queries.run()
    print(f"  👉 Generated {len(queries)} search queries:")
    for q in queries[:5]:
        print(f"     - Scene #{q['subtitle_index']}: '{q['text'][:35]}...' -> Query: '{q['query']}'")
        
    # 6. Clip Retrieval
    print("\n[4/6] Downloading 4K stock clips from Pexels & Pixabay...")
    clips = multi_style_generator.run()
    print(f"  👉 Retrieved {len(clips)} matching clips.")
    
    # 7. Video Assembly & Audio Mixing
    print("\n[5/6] Stitched timeline & dynamic audio ducking...")
    create_video.run()
    download_music.run()
    add_audio.run()
    
    # 8. Burning Subtitles & Subscribe Outro Overlay
    print("\n[6/6] Burning subtitles in safe zone (280px) + animated Subscribe/Like/Bell outro...")
    final_video = burn_subtitles.run()
    
    # Rename/copy to demo_short.mp4
    demo_video = OUTPUT_DIR / "demo_short.mp4"
    if final_video.exists():
        import shutil
        shutil.copy2(final_video, demo_video)
        
    total_time = time.time() - start_time
    info = get_video_info(demo_video)
    dur = get_duration(demo_video)
    
    print("\n" + "=" * 60)
    print("🎉 DEMO VIDEO CREATED SUCCESSFULLY!")
    print(f"  📁 File: {demo_video.resolve()}")
    print(f"  ⏱ Duration: {dur:.1f}s")
    print(f"  📐 Resolution: {info.get('width')}x{info.get('height')}")
    print(f"  ⚡ Generation Time: {total_time:.1f}s")
    print("=" * 60)
    return True

if __name__ == "__main__":
    generate_demo()
