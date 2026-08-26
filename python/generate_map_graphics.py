"""
generate_map_graphics.py — Style 3: 3D Map & Motion Explainer Graphics Engine.

Generates premium 3D geographic maps, country boundaries, glowing connection lines,
satellite terrain fly-overs, and statistical motion graphics (Vox / Kurzgesagt documentary style).

Outputs:
    downloads/videos/scene_{index}.mp4 (1080x1920, 30fps smooth map navigation clip)
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


def generate_3d_map_artwork(query: str, output_path: Path, scene_index: int = 1) -> Path:
    """Generates an ultra-clean 3D topographic / geographic map visual."""
    logger.info(f"Generating 3D Map Graphic for Scene {scene_index}: '{query}'...")
    
    prompt = (
        f"3D topographic dark earth map showing {query}, "
        "glowing neon geopolitical connection routes, highlighted country borders in cyan and orange, "
        "satellite orbital perspective, high-tech HUD overlays, Vox documentary explainer graphics, "
        "cinematic volumetric lighting, ultra high resolution, 9:16 vertical"
    )
    
    encoded = urllib.parse.quote(prompt)
    seed = (int(time.time()) + scene_index * 313) % 999999
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&seed={seed}&model=flux"
    
    for attempt in range(3):
        try:
            logger.info(f"Fetching 3D Map Visual from generator (Attempt {attempt+1}/3)...")
            resp = requests.get(url, timeout=40)
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Successfully generated 3D Map Visual: {output_path} ({len(resp.content)} bytes)")
                return output_path
        except Exception as e:
            logger.warning(f"Map fetch attempt {attempt+1} failed: {e}. Retrying...")
            time.sleep(2)

    # Local Fallback 3D Map Card
    logger.warning("Generating local fallback 3D map visual...")
    img = Image.new("RGB", (1080, 1920), (15, 20, 30))
    draw = ImageDraw.Draw(img)
    draw.text((100, 300), "GLOBAL GEOPOLITICAL MAP", fill=(0, 200, 255))
    draw.text((100, 450), query.upper()[:30], fill=(255, 140, 0))
    img.save(output_path, "PNG")
    return output_path


def render_3d_map_motion_clip(
    image_path: Path,
    output_video_path: Path,
    duration: float = 4.0,
    fps: int = 30
) -> Path:
    """Renders a smooth 3D satellite fly-over / zoom motion clip."""
    logger.info(f"Rendering 3D Map motion clip for {image_path.name} ({duration:.2f}s, {fps}fps)...")
    
    base_img = Image.open(image_path).convert("RGB")
    if base_img.size != (1080, 1920):
        base_img = base_img.resize((1080, 1920), Image.Resampling.LANCZOS)

    img_w, img_h = base_img.size
    total_frames = max(1, int(duration * fps))
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (1080, 1920))

    for frame_idx in range(total_frames):
        t = frame_idx / float(total_frames)
        
        # Smooth orbital zoom & dynamic diagonal pan (simulate 3D satellite tracking)
        zoom = 1.0 + 0.12 * math.sin(t * math.pi * 0.5)
        crop_w = int(img_w / zoom)
        crop_h = int(img_h / zoom)
        
        pan_x = int((t - 0.5) * 40)
        pan_y = int((t - 0.5) * 60)
        
        x1 = min(img_w - crop_w, max(0, (img_w - crop_w) // 2 + pan_x))
        y1 = min(img_h - crop_h, max(0, (img_h - crop_h) // 2 + pan_y))
        x2 = x1 + crop_w
        y2 = y1 + crop_h
        
        frame_pil = base_img.crop((x1, y1, x2, y2)).resize((1080, 1920), Image.Resampling.BILINEAR)
        frame_np = np.array(frame_pil)
        
        # Write BGR frame
        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

    out.release()
    logger.info(f"Rendered 3D Map motion clip: {output_video_path}")
    return output_video_path


def generate_single_scene(query: str, output_path: Path, duration: float, scene_index: int = 1) -> Path:
    """Generate a single 3D Map motion scene clip."""
    img_path = TEMP_DIR / f"map_graphic_{scene_index}.png"
    generate_3d_map_artwork(query, img_path, scene_index=scene_index)
    render_3d_map_motion_clip(img_path, output_path, duration=duration)
    return output_path
