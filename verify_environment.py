#!/usr/bin/env python3
"""
Diagnostic Environment Verification Tool for The Shortest Orbit / AI Video Generator V2
Tests every technology, API key, external binary, font, and database in the project.
"""

import os
import sys
import shutil
import subprocess
import pickle
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ANSI Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}   {title.center(54)}   {RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")

def report(name, status, message=""):
    if status == "PASS":
        badge = f"{GREEN}[PASS]{RESET}"
    elif status == "WARN":
        badge = f"{YELLOW}[WARN]{RESET}"
    else:
        badge = f"{RED}[FAIL]{RESET}"
    print(f" {badge} {BOLD}{name:<25}{RESET} : {message}")

def check_python_version():
    v = sys.version_info
    v_str = f"{v.major}.{v.minor}.{v.micro}"
    if v.major == 3 and v.minor >= 11:
        report("Python Runtime", "PASS", f"Python {v_str} (Compatible)")
        return True
    else:
        report("Python Runtime", "FAIL", f"Python {v_str} (Python 3.11 or 3.12 is required!)")
        return False

def check_external_binaries():
    all_ok = True
    
    # Check Git
    git_path = shutil.which("git")
    if git_path:
        try:
            ver = subprocess.check_output(["git", "--version"], text=True, stderr=subprocess.STDOUT).strip()
            report("Git CLI", "PASS", ver)
        except Exception:
            report("Git CLI", "PASS", f"Found at {git_path}")
    else:
        report("Git CLI", "FAIL", "Git not found in PATH! Run 'winget install Git.Git -e'")
        all_ok = False

    # Check FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            out = subprocess.check_output(["ffmpeg", "-version"], text=True, stderr=subprocess.STDOUT)
            ver_line = out.splitlines()[0] if out.splitlines() else "Available"
            report("FFmpeg Engine", "PASS", ver_line[:40])
        except Exception:
            report("FFmpeg Engine", "PASS", f"Found at {ffmpeg_path}")
    else:
        report("FFmpeg Engine", "FAIL", "FFmpeg not in PATH! Run 'winget install Gyan.FFmpeg -e'")
        all_ok = False

    # Check FFprobe
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        report("FFprobe Utility", "PASS", "Available")
    else:
        report("FFprobe Utility", "FAIL", "FFprobe not in PATH!")
        all_ok = False

    return all_ok

def check_python_packages():
    packages = [
        ("groq", "Groq AI SDK"),
        ("edge_tts", "Edge-TTS Neural Voice"),
        ("requests", "Requests HTTP Client"),
        ("dotenv", "Python-Dotenv (.env support)"),
        ("google.genai", "Google GenAI (Gemini SDK)"),
        ("googleapiclient", "Google API Client (YouTube)"),
        ("google_auth_oauthlib", "Google OAuth 2.0 Library"),
        ("PIL", "Pillow (Image Processing)"),
        ("cv2", "OpenCV (Video Processing)"),
        ("feedparser", "Feedparser (RSS Trends)"),
        ("numpy", "NumPy (Array Computations)"),
        ("scipy", "SciPy (Audio & Signal Processing)"),
        ("pandas", "Pandas (Analytics DataFrames)"),
        ("plotly", "Plotly (Dashboard Graphs)"),
        ("streamlit", "Streamlit (Web Dashboard)")
    ]
    
    all_ok = True
    for mod_name, label in packages:
        try:
            __import__(mod_name)
            report(label, "PASS", "Installed & importable")
        except ImportError:
            report(label, "FAIL", f"Missing! Run 'pip install -r requirements.txt'")
            all_ok = False
            
    return all_ok

def check_assets():
    all_ok = True
    
    # 1. Plus Jakarta Sans ExtraBold
    font_file = PROJECT_ROOT / "assets" / "fonts" / "PlusJakartaSans-ExtraBold.ttf"
    if font_file.exists() and font_file.stat().st_size > 10000:
        report("Subtitle Font", "PASS", f"Plus Jakarta Sans ExtraBold ({font_file.stat().st_size // 1024} KB)")
    else:
        report("Subtitle Font", "FAIL", f"Missing font at {font_file}")
        all_ok = False

    # 2. Outro Animation & SFX
    outro_mov = PROJECT_ROOT / "assets" / "animations" / "subscribe_outro.mov"
    outro_sfx = PROJECT_ROOT / "assets" / "animations" / "subscribe_outro_sfx.wav"
    if outro_mov.exists() and outro_mov.stat().st_size > 100000:
        report("Animated Outro MOV", "PASS", f"Found ({outro_mov.stat().st_size // 1024} KB)")
    else:
        report("Animated Outro MOV", "FAIL", f"Missing at {outro_mov}")
        all_ok = False

    if outro_sfx.exists() and outro_sfx.stat().st_size > 10000:
        report("Outro SFX Audio", "PASS", f"Found ({outro_sfx.stat().st_size // 1024} KB)")
    else:
        report("Outro SFX Audio", "FAIL", f"Missing at {outro_sfx}")
        all_ok = False

    # 3. Background Music
    music_file = PROJECT_ROOT / "assets" / "music" / "background.mp3"
    if music_file.exists() and music_file.stat().st_size > 10000:
        report("Background Music", "PASS", f"Found ({music_file.stat().st_size // 1024} KB)")
    else:
        report("Background Music", "WARN", f"Missing default background.mp3")

    return all_ok

def check_secrets_and_api():
    all_ok = True
    
    # Check .env existence
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        report(".env Config", "FAIL", "Missing .env file! Copy .env.example to .env and insert API keys.")
        return False
        
    report(".env Config", "PASS", "Found .env file")
    
    # Read env variables
    from dotenv import load_dotenv
    load_dotenv(env_file, override=True)
    
    keys = [
        ("GROQ_API_KEY", "Groq Cloud API Key", True),
        ("PEXELS_API_KEY", "Pexels Stock Video API Key", True),
        ("PIXABAY_API_KEY", "Pixabay Stock Footage API Key", True),
        ("GEMINI_API_KEY", "Google Gemini AI API Key", True),
        ("META_ACCESS_TOKEN", "Meta Graph Access Token", False),
        ("FACEBOOK_PAGE_ID", "Facebook Page ID", False),
        ("INSTAGRAM_BUSINESS_ACCOUNT_ID", "Instagram Business ID", False),
    ]
    
    for k, desc, req in keys:
        val = os.getenv(k, "").strip()
        if val and not val.startswith("your_"):
            report(desc, "PASS", f"Configured ({val[:4]}...{val[-4:] if len(val) > 8 else ''})")
        else:
            if req:
                report(desc, "FAIL", f"Missing or placeholder in .env ({k})")
                all_ok = False
            else:
                report(desc, "WARN", f"Optional: Not configured ({k})")

    # Check client_secret.json
    cs_file = PROJECT_ROOT / "client_secret.json"
    if cs_file.exists() and cs_file.stat().st_size > 50:
        report("YouTube Client Secret", "PASS", "client_secret.json present")
    else:
        report("YouTube Client Secret", "FAIL", "client_secret.json missing! Required for YouTube OAuth.")
        all_ok = False

    # Check token.pickle
    tok_file = PROJECT_ROOT / "token.pickle"
    if tok_file.exists() and tok_file.stat().st_size > 50:
        try:
            with open(tok_file, "rb") as f:
                creds = pickle.load(f)
            if creds.valid:
                report("YouTube OAuth Token", "PASS", "token.pickle is ACTIVE & VALID")
            elif creds.refresh_token:
                report("YouTube OAuth Token", "PASS", "token.pickle is expired but has REFRESH TOKEN (Auto-refreshable)")
            else:
                report("YouTube OAuth Token", "WARN", "token.pickle expired without refresh token! Run python get_fresh_token.py")
        except Exception as te:
            report("YouTube OAuth Token", "WARN", f"Could not inspect token: {te}")
    else:
        report("YouTube OAuth Token", "FAIL", "token.pickle missing! Run 'python get_fresh_token.py' to generate.")
        all_ok = False

    return all_ok

def check_database():
    try:
        from utils.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM videos")
        video_count = cursor.fetchone()[0]
        conn.close()
        report("Central Database", "PASS", f"shortest_orbit_v3.db connected ({table_count} tables, {video_count} video records)")
        return True
    except Exception as e:
        report("Central Database", "FAIL", f"Database error: {e}")
        return False

def test_neural_tts():
    try:
        import asyncio
        import edge_tts
        
        async def _test():
            communicate = edge_tts.Communicate("Test", "en-US-BrianMultilingualNeural")
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    return True
            return False
            
        success = asyncio.run(_test())
        if success:
            report("Edge-TTS Voice Test", "PASS", "Successfully streamed 'en-US-BrianMultilingualNeural'")
            return True
        else:
            report("Edge-TTS Voice Test", "WARN", "TTS returned no audio chunk")
            return False
    except Exception as e:
        report("Edge-TTS Voice Test", "WARN", f"Network or TTS error: {e}")
        return False

def main():
    print_header("THE SHORTEST ORBIT - SYSTEM HEALTH & CONFIG CHECK")
    
    p1 = check_python_version()
    p2 = check_external_binaries()
    p3 = check_python_packages()
    p4 = check_assets()
    p5 = check_secrets_and_api()
    p6 = check_database()
    p7 = test_neural_tts()
    
    print(f"\n{BOLD}{CYAN}{'-'*60}{RESET}")
    if p1 and p2 and p3 and p4 and p5 and p6:
        print(f"{BOLD}{GREEN} >>> ALL CRITICAL SYSTEMS OPERATIONAL! READY FOR PRODUCTION. <<<{RESET}")
    else:
        print(f"{BOLD}{RED} >>> ATTENTION: Some components require setup. Review above warnings. <<<{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")

if __name__ == "__main__":
    main()
