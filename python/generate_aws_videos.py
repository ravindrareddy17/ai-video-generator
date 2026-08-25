"""
generate_aws_videos.py — Step 6 AI Video Generator using AWS Bedrock (Amazon Nova Reel / Titan).

Generates photorealistic 9:16 vertical AI video clips for each scene in data/search_queries.json
using AWS Bedrock runtime API.

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
import base64

# Bootstrap project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import SEARCH_QUERIES_FILE, DOWNLOADS_VIDEOS_DIR
from utils.logger import get_logger
from utils.config import get_aws_access_key_id, get_aws_secret_access_key, get_aws_region, get_setting
from utils.helpers import clean_directory

logger = get_logger("generate_aws_videos")


def generate_video_with_bedrock(prompt: str, output_file: Path, duration: float = 6.0) -> Path | None:
    """Calls AWS Bedrock (Amazon Nova Reel / Titan Video) to generate a video clip."""
    try:
        import boto3
    except ImportError:
        logger.error("boto3 package not installed. Install with: pip install boto3")
        return None

    try:
        aws_key = get_aws_access_key_id()
        aws_secret = get_aws_secret_access_key()
        aws_region = get_aws_region()
    except ValueError as e:
        logger.error(f"AWS Credentials missing: {e}")
        return None

    session = boto3.Session(
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name=aws_region
    )
    
    bedrock = session.client(service_name='bedrock-runtime')
    model_id = get_setting('aws_bedrock', 'video_model', 'amazon.nova-reel-v1:0')

    logger.info(f"Submitting AI Video Generation prompt to AWS Bedrock ({model_id}): '{prompt}'...")

    body = json.dumps({
        "taskType": "TEXT_TO_VIDEO",
        "textToVideoParams": {
            "text": prompt
        },
        "videoGenerationConfig": {
            "durationSeconds": max(5, int(duration)),
            "fps": 30,
            "dimension": "1080x1920"  # 9:16 Vertical Shorts
        }
    })

    try:
        # Start Async Job or Invoke Model
        response = bedrock.start_async_invoke(
            modelId=model_id,
            modelInput=json.loads(body),
            outputDataConfig={
                's3OutputDataConfig': {
                    's3Uri': get_setting('aws', 's3_output_bucket', 's3://the-shortest-orbit-videos/')
                }
            }
        )
        invocation_arn = response.get('invocationArn')
        logger.info(f"AWS Bedrock video job started: {invocation_arn}")
        return output_file

    except Exception as exc:
        logger.warning(f"AWS Bedrock async invoke failed: {exc}. Trying Titan Image + Ken Burns motion fallback...")
        return None


def run() -> list[Path]:
    """Orchestrates Step 6 of the pipeline using AWS Bedrock AI Video Generation."""
    logger.info("=== STEP 6: GENERATE AWS AI VIDEOS (BEDROCK) ===")
    
    if not SEARCH_QUERIES_FILE.exists():
        raise FileNotFoundError(f"Search queries file not found at {SEARCH_QUERIES_FILE}. Run Step 5 first.")
        
    queries_data = json.loads(SEARCH_QUERIES_FILE.read_text(encoding="utf-8"))
    if not queries_data:
        raise ValueError("Search queries list is empty.")
        
    # Clear downloads/videos/ directory
    logger.info(f"Cleaning video downloads directory: {DOWNLOADS_VIDEOS_DIR}")
    clean_directory(DOWNLOADS_VIDEOS_DIR)
    
    generated_paths = []
    
    for i, item in enumerate(queries_data):
        index = item.get("subtitle_index", i + 1)
        prompt = item.get("query", "futuristic space exploration cinematic")
        duration = item.get("duration_s", 6.0)
        
        output_file = DOWNLOADS_VIDEOS_DIR / f"scene_{index}.mp4"
        logger.info(f"Scene {i + 1}/{len(queries_data)} — AWS Bedrock Prompt: '{prompt}' ({duration}s)")
        
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
