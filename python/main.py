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
import generate_aws_videos
import create_video
import download_music
import add_audio
import burn_subtitles
from python.v4_contract_engine import V4ContractEngine
import generate_thumbnail
import publish_service
import media_qa
import automation.youtube.analytics as yt_analytics
import automation.instagram.analytics as ig_analytics
import automation.facebook.analytics as fb_analytics
import automation.ai.learning as ai_learning
import automation.ai.prediction as ai_prediction

logger = get_logger("orchestrator")


def mark_pending_videos_failed():
    try:
        from automation.database.connection import get_youtube_conn, get_instagram_conn, get_facebook_conn
        for conn_getter in [get_youtube_conn, get_instagram_conn, get_facebook_conn]:
            try:
                conn = conn_getter()
                cursor = conn.cursor()
                cursor.execute("UPDATE videos SET status = 'failed' WHERE status = 'generating'")
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning(f"Could not update status to failed in DB: {e}")
    except Exception as e:
        logger.warning(f"Could not update database status to failed: {e}")


def run_pipeline() -> bool:
    """Run the entire 11-step pipeline from end to end."""
    start_time = time.time()
    upload_succeeded = False
    logger.info("==================================================")
    logger.info("   STARTING AI VIDEO GENERATOR V2 PIPELINE        ")
    logger.info("==================================================")
    
    # ── Verify FFmpeg & FFprobe ─────────────────────────────────────
    if not verify_ffmpeg():
        logger.critical("FFmpeg or FFprobe is missing or not working correctly. Please install them and try again.")
        return False
        
    # ── Initialize Platform Databases ────────────────────────────────
    try:
        from automation.database.connection import init_db as init_platform_dbs
        init_platform_dbs()
        logger.info("Platform isolated databases initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize platform databases: {e}")
        
    try:
        # ── Step 1: Find Viral Topics ───────────────
        step_start = time.time()
        logger.info(">>> Step 1: Searching for viral space/science/AI topics...")
        topic = find_viral_topics.run()
        topic_title = topic.get('selected_topic', 'Space Exploration Breakthrough')
        logger.info(f"Step 1 Complete. Selected topic: '{topic_title}' ({time.time() - step_start:.2f}s)")
        
        # Initialize V4 Master Contract
        v4_engine = V4ContractEngine()
        contract = v4_engine.create_draft_contract(topic_title)
        v4_engine.transition_state(contract, "RESEARCHED")
        
        # ── Step 2: Generate Content ────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 2: Generating narration script and metadata...")
        content, metadata = generate_content.run(topic)
        contract["video_strategy"]["topic"] = topic_title
        contract["script"]["text"] = content.get("narration", "")
        logger.info(f"Step 2 Complete. Title: '{content.get('title')}' ({time.time() - step_start:.2f}s)")
        
        # ── Step 2.5: Verify Facts ──────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 2.5: Running AI fact checking on script narration...")
        fact_passed = verify_facts.run()
        if not fact_passed:
            logger.warning("Fact checking flagged critical claims! Attempting script regeneration...")
            mark_pending_videos_failed()
            content, metadata = generate_content.run(topic)
            fact_passed = verify_facts.run()
            if not fact_passed:
                logger.critical("Regenerated script failed fact checking again. Aborting run for safety.")
                contract["research"]["verification_status"] = "rejected"
                v4_engine.save_contract(contract)
                mark_pending_videos_failed()
                return False
        contract["research"]["verification_status"] = "verified"
        v4_engine.transition_state(contract, "VERIFIED")
        logger.info(f"Step 2.5 Complete. Script narration fact-verified. ({time.time() - step_start:.2f}s)")
        
        # ── Step 2.6: Run Quality Checker ───────────────────────────
        step_start = time.time()
        logger.info(">>> Step 2.6: Running script quality control...")
        if not quality_checker.run():
            logger.critical("Script failed quality control checks. Aborting run.")
            v4_engine.save_contract(contract)
            mark_pending_videos_failed()
            return False
            
        gate_passed, gate_msg = v4_engine.validate_accuracy_gate(contract)
        if not gate_passed:
            logger.critical(f"Accuracy Gate Veto Triggered! {gate_msg}. Aborting publication.")
            v4_engine.save_contract(contract)
            mark_pending_videos_failed()
            return False
            
        v4_engine.transition_state(contract, "SCORED")
        logger.info(f"Step 2.6 Complete. Script quality & accuracy gate verified. ({time.time() - step_start:.2f}s)")
        
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
        
        # ── Step 6: Download Real Animated / Motion MP4 Videos ───────────
        step_start = time.time()
        logger.info(">>> Step 6: Fetching Real Animated / High-Motion 4K Video Clips...")
        clips = download_videos.run()
        logger.info(f"Step 6 Complete. Downloaded {len(clips)} real animated motion video clips. ({time.time() - step_start:.2f}s)")
        
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
        
        # ── Step 10: Burn Subtitles ─────────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 10: Burning subtitles onto video...")
        final_video = burn_subtitles.run()
        v4_engine.transition_state(contract, "CREATED")
        logger.info(f"Step 10 Complete. Final video burned at: {final_video.name} ({time.time() - step_start:.2f}s)")
        
        # ── Step 10.5: Technical Media QA ───────────────────────────
        step_start = time.time()
        logger.info(">>> Step 10.5: Running Technical Media QA validation...")
        if not media_qa.run():
            logger.critical("Technical Media QA Failed! Video file is invalid or corrupt. Aborting upload.")
            v4_engine.save_contract(contract)
            mark_pending_videos_failed()
            return False
            
        v4_engine.transition_state(contract, "QUALITY_CHECKED")
        v4_engine.transition_state(contract, "APPROVED")
        logger.info(f"Step 10.5 Complete. Technical Media QA PASSED. ({time.time() - step_start:.2f}s)")
        
        # ── Step 10: Generate Thumbnail ─────────────────────────────
        step_start = time.time()
        logger.info(">>> Step 10: Generating YouTube thumbnail...")
        thumbnail = generate_thumbnail.run()
        logger.info(f"Step 10 Complete. Thumbnail saved at: {thumbnail.name} ({time.time() - step_start:.2f}s)")
        
        # ── Step 11: Multi-Platform Publishing (YouTube + Meta) ──────
        step_start = time.time()
        logger.info(">>> Step 11: Publishing to configured platforms...")
        publish_res = publish_service.run()
        youtube_url = publish_res.youtube_url
        facebook_url = publish_res.facebook_url
        instagram_url = publish_res.instagram_url
        upload_succeeded = publish_res.status in ("success", "partial")
        logger.info(f"Step 11 Complete. Status: {publish_res.status} ({time.time() - step_start:.2f}s)")
        
        # ── Step 11.5: Harvest Platform-Specific Analytics ───────────
        step_start = time.time()
        logger.info(">>> Step 11.5: Harvesting channel analytics for all configured platforms...")
        try:
            yt_analytics.run()
            ig_analytics.run()
            fb_analytics.run()
            logger.info("Independent platform analytics harvested successfully.")
        except Exception as ae:
            logger.warning(f"Analytics harvesting failed: {ae}")
        logger.info(f"Step 11.5 Complete. ({time.time() - step_start:.2f}s)")
        
        # ── Step 12: Run Decoupled AI Self-Learning Engine ───────────
        step_start = time.time()
        logger.info(">>> Step 12: Running self-learning feedback optimization loop...")
        try:
            ai_learning.run()
            ai_prediction.run_predictions()
            logger.info("Decoupled self-learning insights compiled successfully.")
        except Exception as le:
            logger.warning(f"Decoupled self-learning cycle failed: {le}")
        logger.info(f"Step 12 Complete. ({time.time() - step_start:.2f}s)")
        
        # ── Pipeline Success Summary ────────────────────────────────
        total_time = time.time() - start_time
        logger.info("==================================================")
        if upload_succeeded:
            logger.info("   PIPELINE COMPLETED SUCCESSFULLY!              ")
        else:
            logger.warning("   PIPELINE PARTIALLY COMPLETED                  ")
        logger.info("==================================================")
        logger.info(f"Total time elapsed: {total_time // 60:.0f}m {total_time % 60:.2f}s")
        logger.info(f"Final Video File: {FINAL_VIDEO_FILE}")
        logger.info(f"Thumbnail File: {THUMBNAIL_FILE}")
        if youtube_url:
            logger.info(f"Watch live on YouTube: {youtube_url}")
        else:
            logger.error("YouTube upload failed or was skipped. Local assets were generated, but automation did not finish end-to-end.")
        if facebook_url:
            logger.info(f"Facebook Reel: {facebook_url}")
        if instagram_url:
            logger.info(f"Instagram Reel: {instagram_url}")
            
        # Clean up temporary processing directories/files
        try:
            logger.info("Cleaning up temporary processing files...")
            clean_directory(TEMP_DIR)
            logger.info("Cleanup complete.")
        except Exception as e:
            logger.warning(f"Could not clean temporary directory: {e}")
            
        return upload_succeeded
        
    except Exception as e:
        logger.critical(f"Pipeline crashed during execution! Error: {e}", exc_info=True)
        mark_pending_videos_failed()
        return False


if __name__ == "__main__":
    max_attempts = 5
    success = False
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- PIPELINE ATTEMPT {attempt}/{max_attempts} ---")
        success = run_pipeline()
        if success:
            print("Pipeline executed and uploaded successfully!")
            break
        
        if attempt < max_attempts:
            print(f"Attempt {attempt} failed to upload. Waiting 30 seconds before retrying with a new topic...")
            time.sleep(30)
            
    if success:
        sys.exit(0)
    else:
        print("Pipeline execution failed after all attempts. See logs/pipeline.log for details.")
        sys.exit(1)
