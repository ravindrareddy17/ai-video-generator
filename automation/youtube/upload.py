import sys
from pathlib import Path
import os
import pickle
import http.client
import httplib2
import random
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Google API imports
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.paths import FINAL_VIDEO_FILE, THUMBNAIL_FILE, METADATA_FILE, CLIENT_SECRET_FILE, TOKEN_FILE
from utils.config import get_setting
from utils.logger import get_logger
from utils.helpers import load_json
from automation.database.connection import get_youtube_conn

logger = get_logger("youtube.upload")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

import requests_oauthlib
from urllib.parse import urlparse, parse_qs

original_fetch_token = requests_oauthlib.OAuth2Session.fetch_token

def patched_fetch_token(self, token_url, *args, **kwargs):
    authorization_response = kwargs.get('authorization_response')
    if not authorization_response and len(args) > 1:
        authorization_response = args[1]
    if authorization_response:
        try:
            parsed = urlparse(authorization_response)
            qs = parse_qs(parsed.query)
            if 'state' in qs:
                new_state = qs['state'][0]
                self.state = new_state
                self._state = new_state
                if hasattr(self, '_client') and self._client:
                    self._client.state = new_state
        except Exception:
            pass
    return original_fetch_token(self, token_url, *args, **kwargs)

requests_oauthlib.OAuth2Session.fetch_token = patched_fetch_token

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

MAX_RETRIES = 5
RETRIABLE_EXCEPTIONS = (
    httplib2.error.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine
)

def get_daily_upload_cap() -> int | None:
    raw_cap = get_setting("upload", "daily_upload_cap", 5)
    try:
        daily_cap = int(raw_cap)
    except (TypeError, ValueError):
        return 5
    if daily_cap < 1:
        return None
    return daily_cap

def get_upload_timezone() -> timezone | ZoneInfo:
    timezone_name = get_setting("upload", "timezone", "Asia/Kolkata")
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return timezone.utc

def parse_db_timestamp(timestamp_text: str) -> datetime | None:
    if not timestamp_text:
        return None
    normalized = timestamp_text.strip()
    try:
        if normalized.endswith("Z"):
            return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        if "T" in normalized and ("+" in normalized[10:] or "-" in normalized[10:]):
            return datetime.fromisoformat(normalized)
        return datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None

def count_uploaded_videos_today() -> int:
    upload_timezone = get_upload_timezone()
    today_in_timezone = datetime.now(upload_timezone).date()
    conn = get_youtube_conn()
    try:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT COALESCE(uploaded_at, created_at) AS uploaded_on
            FROM videos
            WHERE status = 'uploaded'
        """).fetchall()
        total = 0
        for row in rows:
            uploaded_at = parse_db_timestamp(row["uploaded_on"])
            if uploaded_at and uploaded_at.astimezone(upload_timezone).date() == today_in_timezone:
                total += 1
        return total
    finally:
        conn.close()

class RequestsHttpAdapter:
    def __init__(self, session):
        self.session = session
    def request(self, method, url, **kwargs):
        return self.session.request(method, url, **kwargs)

def get_authenticated_service():
    credentials = None
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "rb") as token:
                credentials = pickle.load(token)
        except Exception as e:
            logger.warning(f"Could not load credentials pickle: {e}")

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                import requests
                session = requests.Session()
                credentials.refresh(Request(session=RequestsHttpAdapter(session)))
            except Exception as e:
                logger.warning(f"Failed to refresh YouTube credentials: {e}")
                credentials = None
        else:
            credentials = None

    if not credentials:
        if not CLIENT_SECRET_FILE.exists():
            logger.critical("client_secret.json does not exist. Authenticaton failed.")
            return None
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRET_FILE),
            scopes=SCOPES
        )
        credentials = flow.run_local_server(
            port=8080,
            authorization_prompt_message="Please authorize YouTube upload: ",
            success_message="Authorization complete. You can close this window now.",
            open_browser=False
        )

    try:
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)
    except Exception as e:
        logger.warning(f"Could not cache token: {e}")

    return build("youtube", "v3", credentials=credentials)

def upload_video(youtube, video_path: Path, title: str, description: str, tags: list[str] = None) -> str | None:
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or [],
            "categoryId": "28"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        chunksize=1024 * 1024,
        resumable=True
    )
    
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    error = None
    retry_count = 0
    
    while response is None:
        try:
            logger.info(f"Uploading chunk for {video_path.name}...")
            status, response = request.next_chunk()
            if response is not None:
                if "id" in response:
                    logger.info(f"Uploaded successfully. Video ID: {response['id']}")
                    return response["id"]
                else:
                    raise Exception("Video uploaded but server did not return ID.")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                error = e
            else:
                raise e
        except RETRIABLE_EXCEPTIONS as e:
            error = e

        if error is not None:
            retry_count += 1
            if retry_count > MAX_RETRIES:
                logger.error("Failed after maximum retries.")
                raise error
            sleep_time = random.random() * (2 ** retry_count)
            logger.warning(f"Error occurred: {error}. Retrying in {sleep_time:.2f}s...")
            time.sleep(sleep_time)
            
    return None

def run() -> str | None:
    if not FINAL_VIDEO_FILE.exists():
        logger.error(f"Final video file not found: {FINAL_VIDEO_FILE}")
        return None
        
    daily_cap = get_daily_upload_cap()
    if daily_cap is not None:
        uploaded_today = count_uploaded_videos_today()
        if uploaded_today >= daily_cap:
            logger.warning(f"Daily upload cap ({daily_cap}) reached today. Skipping upload.")
            return None

    try:
        youtube = get_authenticated_service()
        if not youtube:
            logger.error("YouTube authorization failed. Skipping upload.")
            return None
            
        metadata = load_json(METADATA_FILE)
        title = metadata.get("title", "AI Generated Short")
        description = metadata.get("description", "A video generated by the Shortest Orbit V3 engine.")
        tags = metadata.get("tags", [])
        
        video_id = upload_video(youtube, FINAL_VIDEO_FILE, title, description, tags)
        if video_id:
            video_url = f"https://youtube.com/shorts/{video_id}"
            
            # Update local database
            try:
                conn = get_youtube_conn()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE videos 
                    SET youtube_id = ?, status = 'uploaded', uploaded_at = CURRENT_TIMESTAMP
                    WHERE id = (SELECT MAX(id) FROM videos WHERE status = 'generating')
                """, (video_id,))
                conn.commit()
                conn.close()
                logger.info(f"Database video status updated in youtube.db for ID: {video_id}")
            except Exception as e:
                logger.warning(f"Database update error in youtube.db: {e}")
                
            return video_url
            
    except HttpError as e:
        logger.error(f"An HTTP error occurred during upload: {e.resp.status} : {e.content}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during upload: {e}")
        
    return None

if __name__ == "__main__":
    url = run()
    if url:
        print(f"YouTube Upload Success: {url}")
    else:
        print("YouTube Upload Failed")
