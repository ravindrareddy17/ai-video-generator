"""
generate_whiteboard.py — Authentic AI Hand-Drawn Doodle & Sketch Engine.

Generates real AI-drawn artistic whiteboard sketches and infographic doodle illustrations
for each scene, then animates them with smooth dynamic sketch motion, zooms, and reveals.

Outputs:
    downloads/videos/scene_{index}.mp4 (1080x1920, 30fps high-retention doodle animation)
"""

import sys
from pathlib import Path
import json
import urllib.parse
import requests
import time
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import TEMP_DIR, DOWNLOADS_VIDEOS_DIR, SEARCH_QUERIES_FILE, CONTENT_FILE, ASSETS_DIR
from utils.logger import get_logger
from utils.helpers import load_json

logger = get_logger(__name__)


def generate_ai_doodle_artwork(query: str, output_path: Path, scene_index: int = 1) -> Path:
    """Generates an authentic AI hand-drawn doodle sketch illustration on white canvas."""
    logger.info(f"Generating AI Doodle Sketch for Scene {scene_index}: '{query}'...")
    
    prompt = (
        f"Authentic hand-drawn whiteboard doodle illustration of {query}, "
        "crisp black ink marker sketch on pure white background, educational infographic diagram, "
        "hand-drawn arrows and sketch notes, vibrant orange and cyan marker accent colors, "
        "clean detailed linework, professional visual storytelling doodle art, 9:16 vertical"
    )
    
    encoded = urllib.parse.quote(prompt)
    seed = (int(time.time()) + scene_index * 137) % 999999
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&seed={seed}&model=flux"
    
    for attempt in range(3):
        try:
            logger.info(f"Fetching AI Doodle from generator (Attempt {attempt+1}/3)...")
            resp = requests.get(url, timeout=40)
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Successfully generated AI Doodle Art: {output_path} ({len(resp.content)} bytes)")
                return output_path
        except Exception as e:
            logger.warning(f"Fetch attempt {attempt+1} failed: {e}. Retrying...")
            time.sleep(2)

    # Fallback to local high-contrast sketch if network fails
    logger.warning("Network generation timed out. Generating local fallback sketch...")
    img = Image.new("RGB", (1080, 1920), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((100, 200), query.upper()[:30], fill=(230, 90, 20))
    img.save(output_path, "PNG")
    return output_path


def render_sketch_motion_clip(
    image_path: Path,
    output_video_path: Path,
    duration: float = 4.0,
    fps: int = 30
) -> Path:
    """Renders a dynamic Ken-Burns zoom and sketch wipe animation on the AI doodle artwork."""
    logger.info(f"Rendering sketch motion clip for {image_path.name} ({duration:.2f}s, {fps}fps)...")
    
    base_img = Image.open(image_path).convert("RGB")
    # Ensure 1080x1920
    if base_img.size != (1080, 1920):
        base_img = base_img.resize((1080, 1920), Image.Resampling.LANCZOS)

    img_w, img_h = base_img.size
    total_frames = max(1, int(duration * fps))
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (1080, 1920))

    for frame_idx in range(total_frames):
        t = frame_idx / float(total_frames)
        
        # Subtle, smooth cinematic zoom (1.00 -> 1.08)
        zoom = 1.0 + 0.08 * math.sin(t * math.pi * 0.5)
        crop_w = int(img_w / zoom)
        crop_h = int(img_h / zoom)
        
        # Center crop with slight vertical pan
        pan_y = int(t * 30)
        x1 = (img_w - crop_w) // 2
        y1 = min(img_h - crop_h, max(0, (img_h - crop_h) // 2 + pan_y))
        x2 = x1 + crop_w
        y2 = y1 + crop_h
        
        frame_pil = base_img.crop((x1, y1, x2, y2)).resize((1080, 1920), Image.Resampling.BILINEAR)
        
        # In the first 0.8 seconds (24 frames), apply progressive sketch-in reveal
        reveal_progress = min(1.0, (frame_idx + 1) / float(min(total_frames, 24)))
        if reveal_progress < 1.0:
            # Mask reveal from top to bottom
            reveal_h = int(1920 * reveal_progress)
            frame_np = np.full((1920, 1080, 3), 255, dtype=np.uint8)
            frame_np[0:reveal_h, :] = np.array(frame_pil)[0:reveal_h, :]
        else:
            frame_np = np.array(frame_pil)

        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

    out.release()
    logger.info(f"Rendered dynamic sketch motion clip: {output_video_path}")
    return output_video_path


def generate_single_scene(query: str, output_path: Path, duration: float, scene_index: int = 1) -> Path:
    """Generates a single authentic AI Doodle scene clip."""
    img_path = TEMP_DIR / f"ai_doodle_{scene_index}.png"
    generate_ai_doodle_artwork(query, img_path, scene_index=scene_index)
    render_sketch_motion_clip(img_path, output_path, duration=duration)
    return output_path


def run() -> list[Path]:
    """Generates authentic AI doodle video clips for all scenes in data/search_queries.json."""
    logger.info("=== STEP 6 (WHITEBOARD DOODLE): GENERATING AI SKETCH SCENES ===")
    
    queries_raw = load_json(SEARCH_QUERIES_FILE)
    if isinstance(queries_raw, list):
        queries = queries_raw
    else:
        queries = queries_raw.get("queries", [])
    
    DOWNLOADS_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    generated_clips = []

    for i, q in enumerate(queries, start=1):
        prompt = q.get("query", f"Scene {i}")
        duration = float(q.get("duration_s", q.get("duration", 4.0)))
        
        doodle_img_path = TEMP_DIR / f"ai_doodle_{i}.png"
        video_out_path = DOWNLOADS_VIDEOS_DIR / f"scene_{i}.mp4"
        
        generate_ai_doodle_artwork(prompt, doodle_img_path, scene_index=i)
        render_sketch_motion_clip(doodle_img_path, video_out_path, duration=duration)
        generated_clips.append(video_out_path)

    logger.info(f"Successfully generated {len(generated_clips)} Authentic AI Doodle scene clips!")
    return generated_clips


if __name__ == "__main__":
    test_img = TEMP_DIR / "test_ai_doodle.png"
    test_vid = TEMP_DIR / "test_ai_doodle.mp4"
    generate_ai_doodle_artwork("Black hole singularity and time dilation", test_img, scene_index=1)
    render_sketch_motion_clip(test_img, test_vid, duration=3.0)
    print(f"Test clip generated: {test_vid}")
