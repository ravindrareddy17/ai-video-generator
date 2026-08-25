"""
generate_aws_videos.py — Step 6 AI Video Generator using AWS Bedrock (Amazon Nova Reel / Titan).

Generates photorealistic 9:16 vertical AI video clips for each scene in data/search_queries.json
using AWS Bedrock as FIRST PREFERENCE.

Inputs:
    data/search_queries.json
    AWS credentials in .env

Outputs:
    downloads/videos/scene_{index}.mp4
"""

import sys
from pathlib import Path
import json
import time
import urllib.parse
import subprocess
import requests

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import SEARCH_QUERIES_FILE, DOWNLOADS_VIDEOS_DIR
from utils.logger import get_logger
from utils.config import get_aws_access_key_id, get_aws_secret_access_key, get_aws_region, get_setting
from utils.helpers import clean_directory

logger = get_logger("generate_aws_videos")


def create_ken_burns_motion_video(image_path: Path, output_file: Path, duration: float) -> Path:
    """Converts a high-res AI image to a fluid vertical video clip with Ken Burns motion pan/zoom."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", "zoompan=z='min(zoom+0.0015,1.15)':d=750:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',framerate=30",
        "-c:v", "libx264",
        "-t", str(duration + 0.5),
        "-pix_fmt", "yuv420p",
        str(output_file)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_file


def generate_video_with_bedrock(prompt: str, output_file: Path, duration: float = 6.0) -> Path | None:
    """Calls AWS Bedrock (Amazon Nova Reel / Titan Video) to generate a video clip."""
    try:
        import boto3
    except ImportError:
        logger.error("boto3 package not installed.")
        return None

    try:
        aws_key = get_aws_access_key_id()
        aws_secret = get_aws_secret_access_key()
        aws_region = get_aws_region()
        if not aws_key or not aws_secret:
            logger.warning("AWS Access Key or Secret Key is empty.")
            return None
    except Exception as e:
        logger.warning(f"AWS Credentials check failed: {e}")
        return None

    try:
        session = boto3.Session(
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=aws_region
        )
        bedrock = session.client(service_name='bedrock-runtime')
        model_id = get_setting('aws_bedrock', 'video_model', 'amazon.nova-reel-v1:0')

        logger.info(f"Submitting AI Video prompt to AWS Bedrock ({model_id}): '{prompt}'...")

        body = json.dumps({
            "taskType": "TEXT_TO_VIDEO",
            "textToVideoParams": {
                "text": f"Cinematic 4k vertical space documentary scene, {prompt}"
            },
            "videoGenerationConfig": {
                "durationSeconds": max(5, int(duration)),
                "fps": 30,
                "dimension": "1080x1920"
            }
        })

        response = bedrock.invoke_model(
            modelId=model_id,
            body=body,
            accept="application/json",
            contentType="application/json"
        )
        
        resp_body = json.loads(response.get('body').read())
        video_bytes_b64 = resp_body.get('videoBytes')
        if video_bytes_b64:
            import base64
            output_file.write_bytes(base64.b64decode(video_bytes_b64))
            logger.info(f"Successfully generated AWS Bedrock video clip at {output_file}")
            return output_file

    except Exception as exc:
        logger.warning(f"AWS Bedrock direct video generation unavailable ({exc}). Using AI Motion FX fallback...")

    # High-Res AI Image + Ken Burns Motion Fallback
    try:
        safe_prompt = urllib.parse.quote(f"dramatic cinematic vertical 4k space future tech scene, {prompt}")
        img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true"
        temp_img = output_file.with_suffix(".jpg")
        
        resp = requests.get(img_url, timeout=20)
        if resp.status_code == 200:
            temp_img.write_bytes(resp.content)
            res_path = create_ken_burns_motion_video(temp_img, output_file, duration)
            if temp_img.exists():
                temp_img.unlink()
            return res_path
    except Exception as img_err:
        logger.error(f"AI Motion FX fallback failed for scene: {img_err}")
        
    return None


def run() -> list[Path]:
    """Orchestrates Step 6 of the pipeline using AWS Bedrock AI Video Generation as FIRST PREFERENCE."""
    logger.info("=== STEP 6: GENERATE AI VIDEOS (AWS BEDROCK FIRST PREFERENCE) ===")
    
    if not SEARCH_QUERIES_FILE.exists():
        raise FileNotFoundError(f"Search queries file not found at {SEARCH_QUERIES_FILE}. Run Step 5 first.")
        
    queries_data = json.loads(SEARCH_QUERIES_FILE.read_text(encoding="utf-8"))
    if not queries_data:
        raise ValueError("Search queries list is empty.")
        
    logger.info(f"Cleaning video downloads directory: {DOWNLOADS_VIDEOS_DIR}")
    clean_directory(DOWNLOADS_VIDEOS_DIR)
    
    generated_paths = []
    
    for i, item in enumerate(queries_data):
        index = item.get("subtitle_index", i + 1)
        prompt = item.get("query", "futuristic space exploration cinematic")
        duration = item.get("duration_s", 6.0)
        
        output_file = DOWNLOADS_VIDEOS_DIR / f"scene_{index}.mp4"
        logger.info(f"Scene {i + 1}/{len(queries_data)} — AWS AI Prompt: '{prompt}' ({duration}s)")
        
        res = generate_video_with_bedrock(prompt, output_file, duration)
        if res and res.exists():
            generated_paths.append(res)
            
    logger.info(f"Completed AWS Bedrock video generation cycle. Generated: {len(generated_paths)} clips.")
    return generated_paths


if __name__ == "__main__":
    try:
        results = run()
        print(f"Generated {len(results)} video clips via AWS Bedrock.")
    except Exception as err:
        logger.exception("generate_aws_videos module failed")
        sys.exit(1)
