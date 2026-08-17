import os
import sys
import pickle
import base64
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRET_FILE = Path("client_secret.json")
TOKEN_FILE = Path("token.pickle")

def get_fresh_token():
    credentials = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)
            
    if credentials and credentials.expired and credentials.refresh_token:
        print("Refreshing token...")
        try:
            import requests
            session = requests.Session()
            session.verify = False
            credentials.refresh(Request(session=session))
        except Exception as e:
            print(f"Failed to refresh. Starting new login: {e}")
            credentials = None
            
    if not credentials or not credentials.valid:
        print("Starting browser OAuth flow...")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
        flow.redirect_uri = "http://localhost:8090/"
        credentials = flow.run_local_server(
            host="localhost",
            port=8090,
            authorization_prompt_message="Please authorize YouTube Upload API access",
            open_browser=True
        )
        
    # Save the token
    with open(TOKEN_FILE, "wb") as token:
        pickle.dump(credentials, token)
        
    # Generate Base64
    b64 = base64.b64encode(open(TOKEN_FILE, "rb").read()).decode('utf-8')
    with open("token_base64.txt", "w") as f:
        f.write(b64)
        
    print("\nSUCCESS! New token saved.")
    print("Base64 string saved to token_base64.txt")

if __name__ == "__main__":
    get_fresh_token()
