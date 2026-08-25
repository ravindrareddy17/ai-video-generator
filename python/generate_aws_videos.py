"""
generate_aws_videos.py — Step 6 AI Video Generator using Amazon Bedrock Nova Reel (amazon.nova-reel-v1:0).

Generates photorealistic 9:16 vertical AI video clips for each scene in data/search_queries.json
using Amazon Bedrock Nova Reel Video Generation API.

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
import base64

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import SEARCH_QUERIES_FILE, DOWNLOADS_VIDEOS_DIR
from utils.logger import get_logger
from utils.config import (
    get_aws_bedrock_api_key,
    get_aws_access_key_id,
    get_aws_secret_access_key,
    get_aws_region,
    get_setting
)
from utils.helpers import clean_directory

logger = get_logger("generate_aws_videos")


def generate_video_with_bedrock_nova_reel(prompt: str, output_file: Path, duration: float = 6.0) -> Path | None:
    """Calls Amazon Bedrock Nova Reel API (amazon.nova-reel-v1:0) to generate AI video scenes."""
    aws_key = get_aws_access_key_id()
    aws_secret = get_aws_secret_access_key()
    aws_region = get_aws_region()
    model_id = get_setting('aws_bedrock', 'video_model', 'amazon.nova-reel-v1:0')

    logger.info(f"Submitting AI Video Prompt to Amazon Bedrock Nova Reel API ({model_id}): '{prompt}'...")

    # Attempt 1: Boto3 AWS Bedrock Async / Model Invocation
    try:
        import boto3
        session = boto3.Session(
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=aws_region
        )
        bedrock = session.client(service_name='bedrock-runtime')

        payload = {
            "taskType": "TEXT_TO_VIDEO",
            "textToVideoParams": {
                "text": f"Cinematic 4k vertical space documentary scene, {prompt}"
            },
            "videoGenerationConfig": {
                "durationSeconds": max(5, int(duration)),
                "fps": 24,
                "dimension": "1280x720"
            }
        }

        # Call Bedrock model
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(payload),
            accept="application/json",
            contentType="application/json"
        )
        
        resp_body = json.loads(response.get('body').read())
        video_bytes_b64 = resp_body.get('videoBytes') or resp_body.get('output', {}).get('videoBytes')
        if video_bytes_b64:
            output_file.write_bytes(base64.b64decode(video_bytes_b64))
            logger.info(f"Successfully generated Amazon Bedrock Nova Reel AI video clip: {output_file.name}")
            return output_file

    except Exception as exc:
        logger.warning(f"Amazon Bedrock Nova Reel direct invocation notice: {exc}")

    return None


def run() -> list[Path]:
    """Orchestrates Step 6 using Amazon Bedrock Nova Reel AI Video Generation API."""
    logger.info("=== STEP 6: GENERATE AI VIDEOS (AMAZON BEDROCK NOVA REEL API) ===")
    
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
        logger.info(f"Scene {i + 1}/{len(queries_data)} — Amazon Nova Reel Prompt: '{prompt}' ({duration}s)")
        
        res = generate_video_with_bedrock_nova_reel(prompt, output_file, duration)
        if res and res.exists():
            generated_paths.append(res)
            
    logger.info(f"Completed Amazon Bedrock Nova Reel generation cycle. Generated: {len(generated_paths)} clips.")
    return generated_paths


if __name__ == "__main__":
    try:
        results = run()
        print(f"Generated {len(results)} video clips via Amazon Bedrock Nova Reel API.")
    except Exception as err:
        logger.exception("generate_aws_videos module failed")
        sys.exit(1)
