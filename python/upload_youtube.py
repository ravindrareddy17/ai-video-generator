"""
upload_youtube.py — Step 11 of the AI Video Generator V2 pipeline.

Authenticates with YouTube Data API v3 using OAuth 2.0 and uploads the finalized
Short video along with its generated title, description, tags, and thumbnail.

Inputs:
    output/short.mp4
    output/thumbnail.png
    data/metadata.json
    client_secret.json (OAuth client secret in root)

Outputs:
    token.pickle (cached OAuth token)
"""

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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import FINAL_VIDEO_FILE, THUMBNAIL_FILE, METADATA_FILE, CLIENT_SECRET_FILE, TOKEN_FILE
from utils.config import get_setting
from utils.logger import get_logger
from utils.helpers import load_json
from utils.database import get_connection

logger = get_logger(__name__)

# Explicitly tell the library that we are running locally for OAuth redirect
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Monkey-patch requests_oauthlib to bypass CSRF state mismatch errors
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


# Scopes required to upload videos and set thumbnails
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

# Max retries for upload failures
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
    """Return the configured daily upload cap, or None when disabled."""
    raw_cap = get_setting("upload", "daily_upload_cap", 5)
    try:
        daily_cap = int(raw_cap)
    except (TypeError, ValueError):
        logger.warning(f"Invalid upload.daily_upload_cap value '{raw_cap}'. Falling back to 5.")
        return 5

    if daily_cap < 1:
        logger.info("Daily upload cap is disabled in settings.")
        return None

    return daily_cap


def get_upload_timezone() -> timezone | ZoneInfo:
    """Return the configured timezone used for daily upload counting."""
    timezone_name = get_setting("upload", "timezone", "Asia/Kolkata")
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        fallback_timezones = {
            "UTC": timezone.utc,
            "Asia/Kolkata": timezone(timedelta(hours=5, minutes=30)),
            "Asia/Calcutta": timezone(timedelta(hours=5, minutes=30)),
        }
        fallback_timezone = fallback_timezones.get(timezone_name)
        if fallback_timezone is not None:
            logger.info(
                f"Using fixed-offset fallback for upload.timezone '{timezone_name}'."
            )
            return fallback_timezone
        logger.warning(
            f"Invalid upload.timezone value '{timezone_name}'. Falling back to UTC."
        )
        return timezone.utc


def parse_db_timestamp(timestamp_text: str) -> datetime | None:
    """Parse SQLite timestamps, which are stored as UTC strings."""
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
        logger.warning(f"Could not parse upload timestamp '{timestamp_text}'.")
        return None


def count_uploaded_videos_today() -> int:
    """Count videos already uploaded today using the configured upload timezone."""
    upload_timezone = get_upload_timezone()
    today_in_timezone = datetime.now(upload_timezone).date()

    conn = get_connection()
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
        
    def request(self, uri, method="GET", body=None, headers=None, **kwargs):
        logger.debug(f"[API Request] {method} {uri}")
        r = self.session.request(
            method=method,
            url=uri,
            data=body,
            headers=headers
        )
        logger.debug(f"[API Response] Status: {r.status_code}")
        if r.status_code >= 400:
            logger.error(f"[API Error Body] {r.text[:500]}")
            
        import httplib2
        resp = httplib2.Response(dict(r.headers))
        resp.status = r.status_code
        resp.reason = r.reason
        return resp, r.content


def get_authenticated_service():
    """Authenticate the user and return the YouTube API client service."""
    credentials = None
    
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            try:
                credentials = pickle.load(token)
            except Exception as e:
                logger.warning(f"Could not load cached tokens from pickle: {e}. Re-authenticating.")
                
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            logger.info("Refreshing expired YouTube access token...")
            try:
                import requests
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                session = requests.Session()
                session.verify = False
                credentials.refresh(Request(session=session))
            except Exception as e:
                logger.error(f"Failed to refresh access token: {e}. Initiating full OAuth flow.")
                credentials = None
                
        if not credentials:
            if not CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"Missing OAuth client secret file at {CLIENT_SECRET_FILE}.\n"
                    "Please follow the setup instructions in the README to download client_secret.json "
                    "from Google Cloud Console and place it in the project root."
                )
                
            logger.info("No valid cached credentials found. Starting browser OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            flow.redirect_uri = "http://localhost:8090/"
            auth_url, _ = flow.authorization_url(prompt="consent")
            
            # Print and log the URL immediately
            print(f"\n--- OAUTH_URL_START ---\n{auth_url}\n--- OAUTH_URL_END ---\n", flush=True)
            logger.info(f"Please visit this URL in your browser to authorize: {auth_url}")
            sys.stdout.flush()
            
            credentials = flow.run_local_server(
                host="localhost",
                port=8090,
                authorization_prompt_message="Please authorize YouTube Upload API access",
                open_browser=False
            )
            
        # Save the credentials for the next run
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)
            logger.info(f"Cached authenticated credentials to {TOKEN_FILE}")
            
    # Use modern requests-based AuthorizedSession to bypass TLS/handshake block issues with httplib2
    from google.auth.transport.requests import AuthorizedSession
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    session = AuthorizedSession(credentials)
    session.verify = False
    http_adapter = RequestsHttpAdapter(session)
    return build("youtube", "v3", http=http_adapter)


def resumable_upload(insert_request, thumbnail_path: Path = None, youtube_client=None, video_id_holder=None):
    """Perform resumable video upload with exponential backoff retries."""
    response = None
    error = None
    retry = 0
    
    logger.info("Initializing video upload stream...")
    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if response is not None:
                if "id" in response:
                    video_id = response["id"]
                    logger.info(f"Video uploaded successfully! Video ID: {video_id}")
                    if video_id_holder is not None:
                        video_id_holder.append(video_id)
                        
                    # Upload custom thumbnail if provided
                    if thumbnail_path and thumbnail_path.exists() and youtube_client:
                        upload_thumbnail(youtube_client, video_id, thumbnail_path)
                else:
                    raise RuntimeError(f"The upload succeeded but no video ID was returned: {response}")
            else:
                if status:
                    logger.info(f"Uploading... {int(status.progress() * 100)}% complete.")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                error = e
            else:
                raise e
        except RETRIABLE_EXCEPTIONS as e:
            error = e
            
        if error is not None:
            logger.warning(f"Retriable error encountered: {error}")
            retry += 1
            if retry > MAX_RETRIES:
                raise RuntimeError("Failed to upload video after maximum retries.")
                
            max_sleep = 2 ** retry
            sleep_time = random.random() * max_sleep
            logger.info(f"Sleeping {sleep_time:.2f} seconds before retry #{retry}...")
            time.sleep(sleep_time)
            error = None


def upload_thumbnail(youtube, video_id: str, thumbnail_path: Path):
    """Upload a custom thumbnail for the specified YouTube video ID."""
    logger.info(f"Uploading custom thumbnail {thumbnail_path.name} for video {video_id}...")
    try:
        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumbnail_path))
        )
        response = request.execute()
        logger.info("Custom thumbnail successfully uploaded and linked to video.")
    except Exception as e:
        logger.error(f"Failed to upload thumbnail: {e}. The video will use a default auto-generated thumbnail.")


def run() -> str | None:
    """Orchestrates Step 11 of the pipeline. Returns video URL if successful."""
    logger.info("=== STEP 11: UPLOAD TO YOUTUBE ===")
    
    # 1. Validate inputs
    if not FINAL_VIDEO_FILE.exists():
        raise FileNotFoundError(f"Final output video not found at {FINAL_VIDEO_FILE}. Run Step 9 first.")
    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"SEO metadata file not found at {METADATA_FILE}. Run Step 2 first.")
        
    metadata = load_json(METADATA_FILE)
    
    # 2. Check client secret file
    if not CLIENT_SECRET_FILE.exists():
        logger.error(
            f"YouTube client credentials not found at {CLIENT_SECRET_FILE}!\n"
            "=== YOUTUBE UPLOAD SKIPPED ===\n"
            "Please follow the setup guide to generate your client_secret.json.\n"
            "Your finished video is ready locally at: " + str(FINAL_VIDEO_FILE)
        )
        return None

    # 3. Respect the configured per-day upload cap before touching the API.
    daily_upload_cap = get_daily_upload_cap()
    if daily_upload_cap is not None:
        try:
            uploads_today = count_uploaded_videos_today()
        except Exception as e:
            logger.warning(f"Could not verify today's upload count: {e}. Continuing with upload attempt.")
        else:
            configured_timezone = get_setting("upload", "timezone", "Asia/Kolkata")
            logger.info(
                f"Daily upload usage: {uploads_today}/{daily_upload_cap} completed today "
                f"in timezone {configured_timezone}."
            )
            if uploads_today >= daily_upload_cap:
                logger.warning(
                    f"Daily upload cap reached ({uploads_today}/{daily_upload_cap}). "
                    "Skipping YouTube upload until the next configured day window."
                )
                return None
        
    # 4. Authenticate with YouTube API
    try:
        youtube = get_authenticated_service()
    except Exception as e:
        logger.error(f"YouTube authentication failed: {e}. Skipping upload.")
        return None
        
    # 5. Prepare upload body
    privacy_status = get_setting('upload', 'privacy', 'unlisted')
    category_id = metadata.get("category", get_setting('upload', 'category', '22'))
    
    # Format description to include exactly 5-6 hashtags at the end
    raw_desc = metadata.get("description", "Created with AI Video Generator V2.")
    import re
    # Clean description of any inline hashtags to avoid duplicates
    clean_desc = re.sub(r'#\w+', '', raw_desc).strip()
    
    hashtags_list = metadata.get("hashtags", [])
    if not hashtags_list:
        # Fallback hashtags if somehow missing
        hashtags_list = ["#Shorts", "#Science", "#Space", "#AI", "#Technology", "#Future"]
        
    # Standardize format and format as a single string
    formatted_hashtags = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags_list])
    final_description = f"{clean_desc}\n\n{formatted_hashtags}"
    
    body = {
        "snippet": {
            "title": metadata.get("title", "AI Generated Short #Shorts")[:100], # title limit 100 chars
            "description": final_description,
            "tags": metadata.get("keywords", ["#Shorts"]),
            "categoryId": category_id,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }
    
    # Add localizations if generated
    if "localizations" in metadata and metadata["localizations"]:
        body["localizations"] = metadata["localizations"]
    
    logger.info(f"Video Title: '{body['snippet']['title']}'")
    logger.info(f"Privacy Status: '{body['status']['privacyStatus']}'")
    logger.info(f"Category ID: '{body['snippet']['categoryId']}'")
    
    # Use chunksize of 1MB for upload (Shorts are small files)
    media = MediaFileUpload(
        str(FINAL_VIDEO_FILE),
        mimetype="video/mp4",
        chunksize=1024 * 1024,
        resumable=True
    )
    
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )
    
    # 6. Start uploading
    video_id_holder = []
    try:
        resumable_upload(
            insert_request=insert_request,
            thumbnail_path=THUMBNAIL_FILE if THUMBNAIL_FILE.exists() else None,
            youtube_client=youtube,
            video_id_holder=video_id_holder
        )
        
        if video_id_holder:
            video_id = video_id_holder[0]
            video_url = f"https://youtube.com/shorts/{video_id}"
            logger.info(f"Upload complete! Watch your video here: {video_url}")
            
            # Update SQLite DB
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE videos 
                    SET youtube_id = ?, status = 'uploaded', uploaded_at = CURRENT_TIMESTAMP
                    WHERE id = (SELECT MAX(id) FROM videos WHERE status = 'generating')
                """, (video_id,))
                conn.commit()
                conn.close()
                logger.info(f"Database video status updated to 'uploaded' for YouTube ID: {video_id}")
            except Exception as e:
                logger.warning(f"Database video upload update error: {e}")
                
            return video_url
            
    except HttpError as e:
        logger.error(f"An HTTP error occurred during upload: {e.resp.status} : {e.content}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during upload: {e}")
        
    return None


if __name__ == "__main__":
    try:
        video_url = run()
        if video_url:
            print(f"Uploaded successfully. URL: {video_url}")
        else:
            print("Upload was skipped or failed. See logs for details.")
    except Exception as exc:
        logger.exception("upload_youtube module execution failed")
        sys.exit(1)
