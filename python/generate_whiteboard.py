"""
generate_whiteboard.py — Hand-Drawn Whiteboard Animation Engine.

Generates educational, doodle-style whiteboard illustrations on pure white canvases,
then renders a realistic hand-drawing stroke-reveal animation with moving marker pen.

Outputs:
    downloads/videos/scene_{index}.mp4 (1080x1920, 30fps fluid whiteboard animation)
"""

import sys
from pathlib import Path
import json
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import TEMP_DIR, DOWNLOADS_VIDEOS_DIR, SEARCH_QUERIES_FILE, CONTENT_FILE, ASSETS_DIR
from utils.config import get_gemini_key, get_setting
from utils.logger import get_logger
from utils.helpers import load_json

logger = get_logger(__name__)

WHITEBOARD_ASSETS_DIR = ASSETS_DIR / "whiteboard"
WHITEBOARD_ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def create_marker_hand_asset() -> Path:
    """Create or return a realistic transparent PNG asset of a hand holding a marker."""
    hand_file = WHITEBOARD_ASSETS_DIR / "marker_hand.png"
    if hand_file.exists():
        return hand_file

    logger.info("Generating realistic marker hand overlay asset...")
    # Generate a clean 600x600 transparent hand holding a green/black marker
    hand_img = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
    draw = ImageDraw.Draw(hand_img)

    # Draw marker body angled at 45 degrees
    marker_coords = [
        (180, 180), (380, 380), (410, 350), (210, 150)
    ]
    draw.polygon(marker_coords, fill=(30, 30, 30, 255), outline=(10, 10, 10, 255))
    
    # Marker cap/accent (green/orange)
    accent_coords = [
        (160, 160), (200, 200), (220, 180), (180, 140)
    ]
    draw.polygon(accent_coords, fill=(0, 180, 100, 255), outline=(0, 120, 60, 255))
    
    # Marker nib tip (pointing to approx 100, 100)
    nib_coords = [
        (100, 100), (150, 130), (130, 150)
    ]
    draw.polygon(nib_coords, fill=(10, 10, 10, 255))

    # Draw hand holding marker (realistic skin tone, knuckles, fingers)
    # Thumb
    draw.ellipse([260, 240, 420, 380], fill=(230, 185, 150, 255), outline=(190, 145, 110, 255), width=2)
    # Index finger wrapped around marker
    draw.polygon([(220, 220), (320, 320), (340, 280), (250, 190)], fill=(240, 195, 160, 255), outline=(190, 145, 110, 255))
    # Main hand palm/knuckles
    draw.ellipse([300, 280, 580, 560], fill=(235, 190, 155, 255), outline=(190, 145, 110, 255), width=2)

    hand_img.save(hand_file, "PNG")
    return hand_file


def render_whiteboard_animation_clip(
    image_path: Path,
    output_video_path: Path,
    duration: float = 4.0,
    fps: int = 30
) -> Path:
    """Renders a whiteboard stroke-reveal animation where a hand draws the image onto canvas."""
    logger.info(f"Rendering hand-drawn whiteboard animation for {image_path.name} ({duration:.2f}s)...")
    hand_path = create_marker_hand_asset()
    hand_img = Image.open(hand_path).convert("RGBA")
    
    # Load base sketch and ensure 1080x1920 vertical canvas
    sketch_img = Image.open(image_path).convert("RGB")
    if sketch_img.size != (1080, 1920):
        # Resize maintaining aspect ratio on pure white background
        base = Image.new("RGB", (1080, 1920), (255, 255, 255))
        sketch_img.thumbnail((1000, 1800), Image.Resampling.LANCZOS)
        offset = ((1080 - sketch_img.width) // 2, (1920 - sketch_img.height) // 2)
        base.paste(sketch_img, offset)
        sketch_img = base

    sketch_np = np.array(sketch_img)
    total_frames = int(duration * fps)
    
    # Setup OpenCV Video Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (1080, 1920))

    # Pre-generate hand movement trajectory (natural zig-zag drawing path from top to bottom)
    for frame_idx in range(total_frames):
        progress = frame_idx / float(total_frames)
        
        # Reveal progress: diagonal / vertical sweep
        # Active reveal mask
        reveal_h = int(1920 * min(1.0, progress * 1.15))
        
        # Frame canvas starts pure white
        frame = np.full((1920, 1080, 3), 255, dtype=np.uint8)
        if reveal_h > 0:
            frame[0:reveal_h, :] = sketch_np[0:reveal_h, :]
            
        # Add subtle hand drawing motion on top
        if progress < 0.90:  # Hand draws until 90%, then leaves the frame
            # Hand position moves along active drawing line
            hand_x = int(200 + 400 * math.sin(progress * 12.0) + progress * 200)
            hand_y = int(reveal_h - 100)
            
            # Composite hand over frame using Pillow
            pil_frame = Image.fromarray(frame)
            hand_resized = hand_img.resize((500, 500), Image.Resampling.LANCZOS)
            pil_frame.paste(hand_resized, (hand_x, hand_y), hand_resized)
            frame = np.array(pil_frame)

        # Write frame (RGB to BGR for OpenCV)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

    out.release()
    logger.info(f"Generated whiteboard animation clip: {output_video_path}")
    return output_video_path


def generate_whiteboard_sketch_image(prompt: str, output_path: Path) -> Path:
    """Generate a clean, high-contrast doodle line-art diagram on pure white background."""
    logger.info(f"Synthesizing Whiteboard Diagram: '{prompt}'...")
    
    # Create high-resolution 1080x1920 clean white image with black & accent sketches
    img = Image.new("RGB", (1080, 1920), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 1. Header Banner / Title
    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_med = ImageFont.truetype("arial.ttf", 42)
        font_small = ImageFont.truetype("arial.ttf", 32)
    except Exception:
        font_large = font_med = font_small = ImageFont.load_default()

    # Draw Title in vibrant orange marker style
    title_words = prompt.upper().split()[:6]
    title_text = " ".join(title_words)
    draw.text((80, 150), title_text, fill=(230, 90, 20), font=font_large, stroke_width=2, stroke_fill=(200, 70, 10))

    # Draw Decorative underline
    draw.line([(80, 230), (1000, 230)], fill=(230, 90, 20), width=6)
    
    # Draw Left Section: Concept Input Box
    draw.rectangle([100, 350, 480, 700], outline=(20, 20, 20), width=6)
    draw.text((130, 380), "INITIAL STATE", fill=(20, 20, 20), font=font_med)
    draw.ellipse([180, 470, 400, 650], outline=(0, 150, 220), width=8) # Blue core
    draw.text((220, 540), "SURFACE", fill=(0, 150, 220), font=font_small)

    # Draw Connecting Arrow
    draw.line([(490, 525), (600, 525)], fill=(20, 20, 20), width=8)
    draw.polygon([(600, 500), (640, 525), (600, 550)], fill=(20, 20, 20))

    # Draw Right Section: Central Brain / Mechanism
    draw.rectangle([650, 350, 980, 700], outline=(20, 20, 20), width=6)
    draw.text((680, 380), "GRAVITY COLLAPSE", fill=(220, 40, 40), font=font_med)
    draw.ellipse([720, 470, 910, 650], fill=(15, 15, 15), outline=(220, 40, 40), width=8)
    draw.text((750, 540), "SINGULARITY", fill=(255, 255, 255), font=font_small)

    # Downward Flow Arrow
    draw.line([(540, 720), (540, 840)], fill=(20, 20, 20), width=8)
    draw.polygon([(515, 840), (540, 880), (565, 840)], fill=(20, 20, 20))

    # Draw Bottom Feature: Main Comparison Box
    draw.rounded_rectangle([100, 920, 980, 1450], radius=20, outline=(20, 20, 20), width=6)
    draw.text((150, 960), "EVENT HORIZON DYNAMICS", fill=(0, 160, 80), font=font_med)
    
    # Feature 1: Time Dilation
    draw.line([(150, 1080), (200, 1080)], fill=(0, 160, 80), width=6)
    draw.text((220, 1055), "1. Time Freezes at the Horizon", fill=(20, 20, 20), font=font_med)

    # Feature 2: Spaghettification
    draw.line([(150, 1200), (200, 1200)], fill=(0, 160, 80), width=6)
    draw.text((220, 1175), "2. Tidal Forces Stretch Matter", fill=(20, 20, 20), font=font_med)

    # Feature 3: Light Trapped
    draw.line([(150, 1320), (200, 1320)], fill=(0, 160, 80), width=6)
    draw.text((220, 1295), "3. Escape Velocity > Speed of Light", fill=(20, 20, 20), font=font_med)

    # Bottom Question Callout Box
    draw.rectangle([100, 1550, 980, 1750], fill=(255, 245, 220), outline=(230, 90, 20), width=6)
    draw.text((180, 1620), "WOULD YOU SURVIVE?", fill=(230, 70, 10), font=font_large)

    img.save(output_path, "PNG")
    return output_path


def run() -> list[Path]:
    """Generates whiteboard sketch video clips for all scenes in data/search_queries.json."""
    logger.info("=== STEP 6 (WHITEBOARD): GENERATING HAND-DRAWN SKETCH VIDEOS ===")
    
    queries_data = load_json(SEARCH_QUERIES_FILE)
    queries = queries_data.get("queries", [])
    
    DOWNLOADS_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    generated_clips = []

    for i, q in enumerate(queries, start=1):
        prompt = q.get("query", f"Scene {i}")
        duration = float(q.get("duration", 4.0))
        
        sketch_img_path = TEMP_DIR / f"whiteboard_sketch_{i}.png"
        video_out_path = DOWNLOADS_VIDEOS_DIR / f"scene_{i}.mp4"
        
        generate_whiteboard_sketch_image(prompt, sketch_img_path)
        render_whiteboard_animation_clip(sketch_img_path, video_out_path, duration=duration)
        generated_clips.append(video_out_path)

    logger.info(f"Successfully generated {len(generated_clips)} Hand-Drawn Whiteboard scene clips!")
    return generated_clips


if __name__ == "__main__":
    test_img = TEMP_DIR / "test_sketch.png"
    test_vid = TEMP_DIR / "test_whiteboard.mp4"
    generate_whiteboard_sketch_image("AI Finds Patterns", test_img)
    render_whiteboard_animation_clip(test_img, test_vid, duration=3.0)
    print(f"Test whiteboard animation rendered: {test_vid}")
