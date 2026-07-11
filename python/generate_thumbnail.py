"""
generate_thumbnail.py — Step 10 of the AI Video Generator V2 pipeline.

Generates a professional YouTube thumbnail (1280x720) for the video.
Uses Google Gemini (Imagen 3) as the primary generation tool, with a high-quality
Pillow-based design generation as a robust local fallback.

Inputs:
    data/content.json

Outputs:
    output/thumbnail.png (1280x720 resolution)
"""

import sys
import subprocess
from pathlib import Path
import io
from PIL import Image, ImageDraw, ImageFont

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import CONTENT_FILE, THUMBNAIL_FILE, FINAL_VIDEO_FILE, FONTS_DIR, TEMP_DIR
from utils.config import get_gemini_key, get_setting
from utils.logger import get_logger
from utils.helpers import load_json
from utils.ffmpeg import get_duration

logger = get_logger(__name__)


def _extract_video_frame(video_path: Path, output_frame: Path) -> bool:
    """Extract a frame at ~30% of the video duration using ffmpeg.

    Returns True on success, False if extraction fails for any reason.
    """
    if not video_path.exists():
        logger.warning(f"Video file not found at {video_path}, cannot extract frame.")
        return False

    try:
        duration = get_duration(video_path)
        seek_time = duration * 0.30
        logger.info(f"Extracting frame at {seek_time:.2f}s (30% of {duration:.2f}s)")

        output_frame.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(seek_time),
                "-i", str(video_path),
                "-frames:v", "1",
                "-q:v", "2",
                str(output_frame),
            ],
            capture_output=True,
            check=True,
        )
        return output_frame.exists()
    except Exception as exc:
        logger.warning(f"Frame extraction failed: {exc}")
        return False


def _create_gradient_background(width: int, height: int) -> Image.Image:
    """Create a vibrant diagonal gradient as a fallback background."""
    image = Image.new("RGB", (width, height))
    for y in range(height):
        for x in range(width):
            factor = (x / width + y / height) / 2.0
            r = int(20 + factor * (103))
            g = int(24 + factor * (7))
            b = int(82 + factor * (80))
            image.putpixel((x, y), (r, g, b))
    return image


def _load_title_font(size: int = 64) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load Cinzel Bold from project assets, falling back to system Arial Bold."""
    cinzel_path = FONTS_DIR / "Cinzel-Variable.ttf"
    if cinzel_path.exists():
        try:
            font = ImageFont.truetype(str(cinzel_path), size)
            logger.info(f"Loaded Cinzel font from {cinzel_path}")
            return font
        except IOError:
            logger.warning("Cinzel font file exists but failed to load.")

    # System font fallback chain
    for name in ["arialbd.ttf", "Arial Bold.ttf", "arial.ttf", "segoeuib.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            continue

    logger.warning("No TrueType fonts available — using PIL default font.")
    return ImageFont.load_default()


def _draw_play_button(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int = 50) -> None:
    """Draw a semi-transparent red circle with a white triangle play icon."""
    # Outer circle (red)
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=(220, 30, 30, 200),
        outline=(255, 255, 255, 220),
        width=3,
    )
    # Inner triangle (white) — points: left-center, top-right, bottom-right
    tri_offset = int(radius * 0.4)
    tri_left = cx - int(tri_offset * 0.6)
    tri_right = cx + tri_offset
    tri_top = cy - tri_offset
    tri_bottom = cy + tri_offset
    draw.polygon(
        [(tri_left, tri_top), (tri_right, cy), (tri_left, tri_bottom)],
        fill=(255, 255, 255, 240),
    )


def generate_local_fallback(title: str, output_path: Path) -> Path:
    """Create an eye-catching thumbnail with a video-frame background and styled text."""
    logger.info("Generating eye-catching local fallback thumbnail...")

    width, height = 1280, 720

    # ── 1. Background: extract a frame from the final video, or use gradient ──
    frame_tmp = TEMP_DIR / "_thumb_frame.jpg"
    frame_extracted = _extract_video_frame(FINAL_VIDEO_FILE, frame_tmp)

    if frame_extracted:
        bg = Image.open(frame_tmp).convert("RGBA")
        bg = bg.resize((width, height), Image.Resampling.LANCZOS)
        logger.info("Using extracted video frame as thumbnail background.")
    else:
        bg = _create_gradient_background(width, height).convert("RGBA")
        logger.info("Using gradient fallback as thumbnail background.")

    # ── 2. Darken the background for text contrast ──
    # Overall darkening (multiply by 0.6)
    darkened = Image.eval(bg.split()[0], lambda px: int(px * 0.6))  # R
    g_chan = Image.eval(bg.split()[1], lambda px: int(px * 0.6))    # G
    b_chan = Image.eval(bg.split()[2], lambda px: int(px * 0.6))    # B
    a_chan = bg.split()[3]
    bg = Image.merge("RGBA", (darkened, g_chan, b_chan, a_chan))

    # Bottom-to-top gradient overlay (transparent top → near-black bottom)
    gradient_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient_overlay)
    for y in range(height):
        alpha = int((y / height) ** 1.5 * 200)  # Ease-in curve for natural falloff
        grad_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    bg = Image.alpha_composite(bg, gradient_overlay)

    # ── 3. Semi-transparent dark bar over the bottom third for text area ──
    text_bar = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    bar_draw = ImageDraw.Draw(text_bar)
    bar_top = int(height * 0.50)
    bar_draw.rectangle([0, bar_top, width, height], fill=(0, 0, 0, 120))
    bg = Image.alpha_composite(bg, text_bar)

    # ── 4. Draw play button icon in the upper-center area ──
    play_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    play_draw = ImageDraw.Draw(play_layer)
    _draw_play_button(play_draw, cx=width // 2, cy=int(height * 0.32), radius=52)
    bg = Image.alpha_composite(bg, play_layer)

    # ── 5. Prepare title text ──
    clean_title = title.replace("#Shorts", "").replace("#shorts", "").strip().upper()
    font = _load_title_font(64)

    # Create a transparent layer for text drawing
    text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    # Word-wrap into lines that fit within the image (with padding)
    max_text_width = width - 120  # 60px padding on each side
    words = clean_title.split()
    lines: list[list[str]] = []
    current_line: list[str] = []

    for word in words:
        test_line = " ".join(current_line + [word])
        if isinstance(font, ImageFont.FreeTypeFont):
            bbox = text_draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width > max_text_width and current_line:
                lines.append(current_line)
                current_line = [word]
            else:
                current_line.append(word)
        else:
            # Default font fallback: wrap after ~4 words
            current_line.append(word)
            if len(current_line) >= 4:
                lines.append(current_line)
                current_line = []
    if current_line:
        lines.append(current_line)

    # ── 6. Draw each word with alternating colors and outline ──
    color_white = (255, 255, 255, 255)
    color_gold = (255, 215, 0, 255)
    outline_color = (0, 0, 0, 255)
    outline_offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2)]

    # Calculate total text block height for vertical centering in bottom half
    line_height = 78  # spacing between lines
    total_text_height = len(lines) * line_height
    text_start_y = bar_top + (height - bar_top - total_text_height) // 2

    word_index = 0  # global counter for alternating colors
    for line_idx, line_words in enumerate(lines):
        # Measure the full line width to center it
        full_line = " ".join(line_words)
        if isinstance(font, ImageFont.FreeTypeFont):
            bbox = text_draw.textbbox((0, 0), full_line, font=font)
            line_w = bbox[2] - bbox[0]
        else:
            line_w = len(full_line) * 10  # rough estimate

        x_cursor = (width - line_w) // 2
        y_pos = text_start_y + line_idx * line_height

        for word in line_words:
            # Choose color: alternate per word
            word_color = color_white if word_index % 2 == 0 else color_gold
            word_index += 1

            # Draw outline (4 offsets in black)
            for ox, oy in outline_offsets:
                text_draw.text(
                    (x_cursor + ox, y_pos + oy),
                    word, font=font, fill=outline_color,
                )
            # Draw the word itself
            text_draw.text((x_cursor, y_pos), word, font=font, fill=word_color)

            # Advance cursor by word width + space
            if isinstance(font, ImageFont.FreeTypeFont):
                w_bbox = text_draw.textbbox((0, 0), word + " ", font=font)
                x_cursor += w_bbox[2] - w_bbox[0]
            else:
                x_cursor += (len(word) + 1) * 10

    # Composite text onto background
    bg = Image.alpha_composite(bg, text_layer)

    # ── 7. Add bright border/frame ──
    final = bg.convert("RGB")
    final_draw = ImageDraw.Draw(final)
    border_color = (255, 215, 0)  # Bright gold border
    for i in range(3):  # 3px thick border
        final_draw.rectangle(
            [i, i, width - 1 - i, height - 1 - i],
            outline=border_color,
        )

    # ── 8. Save ──
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.save(output_path, "PNG")
    logger.info(f"Eye-catching thumbnail saved at: {output_path}")

    # Clean up temp frame
    if frame_tmp.exists():
        try:
            frame_tmp.unlink()
        except OSError:
            pass

    return output_path


def run() -> Path:
    """Orchestrates Step 10 of the pipeline."""
    logger.info("=== STEP 10: GENERATE THUMBNAIL ===")
    
    # Validate inputs
    if not CONTENT_FILE.exists():
        raise FileNotFoundError(f"Content file not found at {CONTENT_FILE}. Run Step 2 first.")
        
    content_data = load_json(CONTENT_FILE)
    title = content_data.get("title", "AI Video Short")
    
    # Try calling Google GenAI API
    gemini_key = None
    try:
        gemini_key = get_gemini_key()
    except Exception:
        logger.warning("GEMINI_API_KEY is not configured in .env file.")
        
    if gemini_key:
        try:
            logger.info("Attempting to generate thumbnail using Google GenAI SDK (Imagen)...")
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=gemini_key)
            
            # Auto-detect available Imagen models
            model_to_use = None
            try:
                available_models = [m.name for m in client.models.list()]
                logger.info(f"Available API models: {len(available_models)}")
                
                # Check for preferred image models in order of preference
                preferred_patterns = [
                    "imagen-4.0-generate",
                    "imagen-4.0",
                    "imagen-3.0-generate",
                    "imagen-3.0",
                    "imagen"
                ]
                for pattern in preferred_patterns:
                    for m_name in available_models:
                        if pattern in m_name:
                            model_to_use = m_name.replace("models/", "")
                            break
                    if model_to_use:
                        break
            except Exception as le:
                logger.warning(f"Could not list available models via API: {le}. Will use default fallback list.")
            
            # List of models to try in sequence
            models_to_try = []
            if model_to_use:
                models_to_try.append(model_to_use)
            
            # Add general fallbacks
            for fallback in ["imagen-4.0-generate-001", "imagen-3.0-generate-002"]:
                if fallback not in models_to_try:
                    models_to_try.append(fallback)
                    
            prompt = (
                f"A cinematic, high-retention YouTube video thumbnail about: '{title}'. "
                "Vibrant cinematic lighting, dark background, highly contrasted, "
                "center-focused high CTR visual composition. 1280x720 landscape. "
                "Include large clean bold typographic text of the title."
            )
            
            generated_image_bytes = None
            used_model = None
            
            for m_name in models_to_try:
                try:
                    logger.info(f"Attempting image generation with model '{m_name}'...")
                    response = client.models.generate_images(
                        model=m_name,
                        prompt=prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            aspect_ratio="16:9"
                        )
                    )
                    if response and response.generated_images:
                        generated_image_bytes = response.generated_images[0].image.image_bytes
                        used_model = m_name
                        logger.info(f"Successfully generated image using model '{m_name}'")
                        break
                except Exception as ex:
                    logger.warning(f"Model '{m_name}' failed to generate image: {ex}")
            
            # Process and save the image if succeeded
            if generated_image_bytes:
                image = Image.open(io.BytesIO(generated_image_bytes))
                # Ensure correct resolution
                image = image.resize((1280, 720), Image.Resampling.LANCZOS)
                
                THUMBNAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
                image.save(THUMBNAIL_FILE, "PNG")
                logger.info(f"Gemini-generated thumbnail saved successfully using {used_model} at: {THUMBNAIL_FILE}")
                return THUMBNAIL_FILE
            else:
                logger.warning("All attempted Gemini Imagen models failed. Falling back to local design.")
                
        except Exception as e:
            logger.error(f"Failed to generate thumbnail via Gemini API: {e}")
            
    # Local design fallback
    generate_local_fallback(title, THUMBNAIL_FILE)
    return THUMBNAIL_FILE


if __name__ == "__main__":
    try:
        out_path = run()
        print(f"Thumbnail generation complete. File saved at: {out_path}")
    except Exception as exc:
        logger.exception("generate_thumbnail module execution failed")
        sys.exit(1)
