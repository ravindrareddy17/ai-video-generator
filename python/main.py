"""
main.py — The orchestrator of the AI Video Generator V2 pipeline.

Verifies system dependencies (FFmpeg), then coordinates the sequential
execution of Steps 1 through 11. Handles pipeline timings, final cleanup,
and error reporting.

Usage:
    python python/main.py
"""

import sys
from pathlib import Path
import time
import shutil

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import TEMP_DIR, FINAL_VIDEO_FILE, THUMBNAIL_FILE
from utils.logger import get_logger
from utils.helpers import clean_directory
from utils.ffmpeg import verify_ffmpeg

# Import step modules
import find_viral_topics
import generate_content
import verify_facts
import quality_checker
import generate_voice
import create_subtitles
import generate_search_queries
import download_videos
import create_video
import download_music
import add_audio
import burn_subtitles
import generate_thumbnail
import upload_youtube
import harvest_analytics
import self_learning

logger = get_logger("orchestrator")


def mark_pending_videos_failed():
    try:
        from utils.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE videos SET status = 'failed' WHERE status = 'generating'")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not update database status to failed: {e}")


def run_pipeline() -> bool:
    """Run the entire 11-step pipeline from end to end."""
    start_time = time.time()
    logger.info("==================================================")
    logger.info("   STARTING AI VIDEO GENERATOR V2 PIPELINE        ")
    logger.info("==================================================")
    
    # ── Verify FFmpeg & FFprobe ─────────────────────────────────────
    if not verify_ffmpeg():
        logger.critical("FFmpeg or FFprobe is missing or not working correctly. Please install them and try again.")
        return False
        
    try:
        # ── Step 1: Find Viral Topics ───────────────
        step_start = time.time()
        logger.info(">>> Step 1: Searching for viral space/science/AI topics...")
        topic = find_viral_topics.run()
        logger.info(f"Step 1 Complete. Selected topic: '{topic.get('selected_topic')}' ({time.time() - step_start:.2f}s)")
        
        # ── Step 2: Generate Content ────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 2: Generating narration script and metadata...")
        content, metadata = generate_content.run(topic)
        logger.info(f"Step 2 Complete. Title: '{content.get('title')}' ({time.time() - step_start:.2f}s)")
        
        # ── Step 2.5: Verify Facts ──────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 2.5: Running AI fact checking on script narration...")
        if not verify_facts.run():
            logger.warning("Fact checking flagged critical claims! Attempting script regeneration...")
            mark_pending_videos_failed()
            content, metadata = generate_content.run(topic)
            if not verify_facts.run():
                logger.critical("Regenerated script failed fact checking again. Aborting run for safety.")
                mark_pending_videos_failed()
                return False
        logger.info(f"Step 2.5 Complete. Script narration fact-verified. ({time.time() - step_start:.2f}s)")
        
        # ── Step 2.6: Run Quality Checker ───────────────────────────
        step_start = time.time()
        logger.info(">>> Step 2.6: Running script quality control...")
        if not quality_checker.run():
            logger.critical("Script failed quality control checks. Aborting run.")
            mark_pending_videos_failed()
            return False
        logger.info(f"Step 2.6 Complete. Script quality verified. ({time.time() - step_start:.2f}s)")
        
        # ── Step 3: Generate Voice ──────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 3: Generating voice narration...")
        voice_path = generate_voice.run()
        logger.info(f"Step 3 Complete. Narration voice file generated at: {voice_path.name} ({time.time() - step_start:.2f}s)")
        
        # ── Step 4: Create Subtitles ────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 4: Aligning word timings and generating subtitles...")
        srt_path = create_subtitles.run()
        logger.info(f"Step 4 Complete. Subtitles generated at: {srt_path.name} ({time.time() - step_start:.2f}s)")
        
        # ── Step 5: Generate Search Queries ─────────────────────────
        step_start = time.time()
        logger.info(">>> Step 5: Generating visual search queries...")
        queries = generate_search_queries.run()
        logger.info(f"Step 5 Complete. Generated {len(queries)} scene search prompts. ({time.time() - step_start:.2f}s)")
        
        # ── Step 6: Download Videos ─────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 6: Downloading stock visual clips...")
        clips = download_videos.run()
        logger.info(f"Step 6 Complete. Downloaded {len(clips)} stock clips. ({time.time() - step_start:.2f}s)")
        
        # ── Step 7: Create Silent Video ──────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 7: Processing and assembling silent vertical video...")
        silent_video = create_video.run()
        logger.info(f"Step 7 Complete. Silent video compiled: {silent_video.name} ({time.time() - step_start:.2f}s)")
        
        # ── Step 7.5: Download Background Music ─────────────────────
        step_start = time.time()
        logger.info(">>> Step 7.5: Downloading mood-matched background music...")
        music_path = download_music.run()
        logger.info(f"Step 7.5 Complete. Music downloaded: {music_path.name} ({time.time() - step_start:.2f}s)")
        
        # ── Step 8: Add Audio ───────────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 8: Mixing voice and music onto video...")
        video_audio = add_audio.run()
        logger.info(f"Step 8 Complete. Audio mixed: {video_audio.name} ({time.time() - step_start:.2f}s)")
        
        # ── Step 9: Burn Subtitles ──────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 9: Hardcoding styled subtitles...")
        final_video = burn_subtitles.run()
        logger.info(f"Step 9 Complete. Final Short generated at: {final_video.name} ({time.time() - step_start:.2f}s)")
        
        # ── Step 10: Generate Thumbnail ─────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 10: Generating YouTube thumbnail...")
        thumbnail = generate_thumbnail.run()
        logger.info(f"Step 10 Complete. Thumbnail saved at: {thumbnail.name} ({time.time() - step_start:.2f}s)")
        
        # ── Step 11: Upload to YouTube ──────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 11: Uploading video to YouTube...")
        youtube_url = upload_youtube.run()
        logger.info(f"Step 11 Complete. YouTube URL: {youtube_url} ({time.time() - step_start:.2f}s)")
        
        # ── Step 11.5: Harvest YouTube Analytics ────────────────────
        step_start = time.time()
        logger.info(">>> Step 11.5: Harvesting YouTube channel analytics...")
        harvest_analytics.run()
        logger.info(f"Step 11.5 Complete. Stats synced to database. ({time.time() - step_start:.2f}s)")
        
        # ── Step 12: Run Self-Learning Engine ───────────────────────
        step_start = time.time()
        logger.info(">>> Step 12: Running self-learning feedback optimization loop...")
        self_learning.run()
        logger.info(f"Step 12 Complete. Prompt optimization weights updated. ({time.time() - step_start:.2f}s)")
        
        # ── Pipeline Success Summary ────────────────────────────────
        total_time = time.time() - start_time
        logger.info("==================================================")
        logger.info("   PIPELINE COMPLETED SUCCESSFULLY!              ")
        logger.info("==================================================")
        logger.info(f"Total time elapsed: {total_time // 60:.0f}m {total_time % 60:.2f}s")
        logger.info(f"Final Video File: {FINAL_VIDEO_FILE}")
        logger.info(f"Thumbnail File: {THUMBNAIL_FILE}")
        if youtube_url:
            logger.info(f"Watch live on YouTube: {youtube_url}")
        else:
            logger.info("YouTube upload was skipped. You can upload the generated short.mp4 manually.")
            
        # Clean up temporary processing directories/files
        try:
            logger.info("Cleaning up temporary processing files...")
            clean_directory(TEMP_DIR)
            logger.info("Cleanup complete.")
        except Exception as e:
            logger.warning(f"Could not clean temporary directory: {e}")
            
        return True
        
    except Exception as e:
        logger.critical(f"Pipeline crashed during execution! Error: {e}", exc_info=True)
        mark_pending_videos_failed()
        return False


if __name__ == "__main__":
    success = run_pipeline()
    if success:
        sys.exit(0)
    else:
        print("Pipeline execution failed. See logs/pipeline.log for details.")
        sys.exit(1)
