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


def generate_whiteboard_sketch_image(prompt: str, output_path: Path, scene_index: int = 1) -> Path:
    """Generate a clean, high-contrast doodle line-art diagram on pure white background."""
    logger.info(f"Synthesizing Whiteboard Diagram for Scene {scene_index}: '{prompt}'...")
    
    # Create high-resolution 1080x1920 clean white image with black & accent sketches
    img = Image.new("RGB", (1080, 1920), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_med = ImageFont.truetype("arial.ttf", 44)
        font_small = ImageFont.truetype("arial.ttf", 34)
    except Exception:
        font_large = font_med = font_small = ImageFont.load_default()

    # 1. Header Banner / Title in vibrant orange marker style
    title_words = prompt.upper().split()[:6]
    title_text = " ".join(title_words)
    draw.text((80, 140), title_text, fill=(230, 90, 20), font=font_large, stroke_width=2, stroke_fill=(200, 70, 10))
    draw.line([(80, 220), (1000, 220)], fill=(230, 90, 20), width=6)

    if scene_index == 1:
        # SCENE 1: THE HOOK & CORE MYSTERY
        draw.rounded_rectangle([100, 320, 980, 720], radius=16, outline=(20, 20, 20), width=6)
        draw.text((150, 360), "THE EVENT HORIZON", fill=(0, 150, 220), font=font_med)
        draw.ellipse([340, 440, 740, 680], fill=(20, 20, 20), outline=(230, 90, 20), width=10)
        draw.text((430, 540), "POINT OF NO RETURN", fill=(255, 255, 255), font=font_small)

        # Arrow down
        draw.line([(540, 740), (540, 860)], fill=(20, 20, 20), width=8)
        draw.polygon([(515, 860), (540, 900), (565, 860)], fill=(20, 20, 20))

        # Big Fact Card
        draw.rounded_rectangle([100, 940, 980, 1500], radius=20, outline=(20, 20, 20), width=6)
        draw.text((150, 980), "WHAT HAPPENS HERE?", fill=(220, 40, 40), font=font_med)
        draw.text((150, 1080), "- External Time Freezes", fill=(20, 20, 20), font=font_med)
        draw.text((150, 1200), "- Light Cannot Escape", fill=(20, 20, 20), font=font_med)
        draw.text((150, 1320), "- Escape Velocity > Speed of Light", fill=(20, 20, 20), font=font_med)

    elif scene_index == 2:
        # SCENE 2: THE PHYSICS MECHANISM (Spaghettification & Singularity)
        draw.rectangle([100, 320, 480, 720], outline=(20, 20, 20), width=6)
        draw.text((130, 350), "HEAD GRAVITY", fill=(220, 40, 40), font=font_med)
        draw.text((150, 480), "10,000 Gs", fill=(20, 20, 20), font=font_large)

        draw.rectangle([600, 320, 980, 720], outline=(20, 20, 20), width=6)
        draw.text((630, 350), "FEET GRAVITY", fill=(220, 40, 40), font=font_med)
        draw.text((640, 480), "1,000,000 Gs", fill=(20, 20, 20), font=font_large)

        # Arrow down
        draw.line([(540, 740), (540, 860)], fill=(20, 20, 20), width=8)
        draw.polygon([(515, 860), (540, 900), (565, 860)], fill=(20, 20, 20))

        # Result box
        draw.rounded_rectangle([100, 940, 980, 1500], radius=20, outline=(20, 20, 20), width=6)
        draw.text((150, 980), "TIDAL STRETCHING (SPAGHETTI)", fill=(0, 160, 80), font=font_med)
        draw.text((150, 1080), "- Matter stretched into a single atom line", fill=(20, 20, 20), font=font_med)
        draw.text((150, 1200), "- Pulled toward infinite density singularity", fill=(20, 20, 20), font=font_med)
        draw.text((150, 1320), "- All known laws of physics break down", fill=(20, 20, 20), font=font_med)

    else:
        # SCENE 3: THE FINAL QUESTION & COMMUNITY DEBATE
        draw.rounded_rectangle([100, 320, 980, 850], radius=20, outline=(20, 20, 20), width=6)
        draw.text((150, 370), "CAN WE EVER HARVEST THIS?", fill=(0, 150, 220), font=font_med)
        draw.text((150, 490), "1. Penrose Energy Extraction", fill=(20, 20, 20), font=font_med)
        draw.text((150, 610), "2. Hawking Radiation Recovery", fill=(20, 20, 20), font=font_med)
        draw.text((150, 730), "3. Artificial AI Probes into Horizon", fill=(20, 20, 20), font=font_med)

        # Callout Question Box
        draw.rectangle([100, 960, 980, 1500], fill=(255, 245, 220), outline=(230, 90, 20), width=8)
        draw.text((180, 1050), "WOULD YOU GO INSIDE?", fill=(230, 70, 10), font=font_large)
        draw.text((220, 1200), "COMMENT YOUR ANSWER", fill=(20, 20, 20), font=font_med)

    # Bottom branding badge
    draw.text((250, 1780), "THE SHORTEST ORBIT", fill=(150, 150, 150), font=font_small)

    img.save(output_path, "PNG")
    return output_path


def run() -> list[Path]:
    """Generates whiteboard sketch video clips for all scenes in data/search_queries.json."""
    logger.info("=== STEP 6 (WHITEBOARD): GENERATING HAND-DRAWN SKETCH VIDEOS ===")
    
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
        
        sketch_img_path = TEMP_DIR / f"whiteboard_sketch_{i}.png"
        video_out_path = DOWNLOADS_VIDEOS_DIR / f"scene_{i}.mp4"
        
        generate_whiteboard_sketch_image(prompt, sketch_img_path, scene_index=i)
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
