import os, sys
sys.path.append('python')
from upload_youtube import get_authenticated_service

try:
    youtube = get_authenticated_service()
    print("YouTube Authentication SUCCESS")
except Exception as e:
    print(f"YouTube Authentication FAILED: {e}")
