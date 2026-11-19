# The Shortest Orbit - Complete Setup & Laptop Reinstallation Guide

> **Purpose:** This guide ensures that whenever you reset, format, or switch laptops, you can configure the entire AI Video Generator stack (**Python, FFmpeg, API keys, OAuth credentials, fonts, databases, and dependencies**) in under 5 minutes without missing a single file or making any mistakes.

---

## 🛑 STEP 0: PRE-RESET BACKUP (DO THIS BEFORE RESETTING YOUR LAPTOP!)

Because `.gitignore` protects your private API keys and OAuth tokens from being pushed publicly to GitHub, **certain critical files exist ONLY on your local machine**:

1. **`.env`** (Contains your Groq, Gemini, Pexels, Pixabay, and Meta API keys)
2. **`client_secret.json`** (Google Cloud OAuth 2.0 Client credentials for YouTube upload)
3. **`token.pickle`** (Active YouTube OAuth access & refresh token)
4. **`automation/database/*.db`** (Local SQLite databases tracking performance, predictions, and uploads)
5. **`data/*.json`** (Local caches and metrics)

### How to back them up with 1 click:
Open PowerShell inside `AI-VIDEO-V2` and run:
```powershell
powershell -ExecutionPolicy Bypass -File backup_before_reset.ps1
```
* **What this does:** Automatically scans your project, collects all secret credentials and database files, and packs them into a single file:
  `ShortestOrbit_BACKUP_SAVE_TO_PENDRIVE_YYYYMMDD_HHMMSS.zip`
* **CRITICAL:** **Copy this ZIP file to a USB Pen Drive or upload it to Google Drive before you reset Windows!**

---

## 💻 STEP 1: FRESH WINDOWS PREREQUISITES (AFTER RESETTING)

Once Windows is reinstalled, open PowerShell as Administrator and run this single command to install Git, Python 3.12, and FFmpeg via Windows Package Manager (`winget`):

```powershell
winget install --id Git.Git -e --source winget
winget install --id Python.Python.3.12 -e --source winget
winget install --id Gyan.FFmpeg -e --source winget
```

> 💡 **Important:** When installing Python, ensure **"Add python.exe to PATH"** is enabled. Close and reopen PowerShell after running the above command so your system PATH updates.

---

## 📂 STEP 2: CLONE REPOSITORY & RESTORE YOUR BACKUP

### 1. Clone the project from GitHub:
```powershell
cd E:\ai_gen    # (Or your chosen workspace directory)
git clone https://github.com/ravindrareddy17/ai-video-generator.git AI-VIDEO-V2
cd AI-VIDEO-V2
```

### 2. Restore your backup:
Copy your `ShortestOrbit_BACKUP_SAVE_TO_PENDRIVE_*.zip` file into the project folder (or parent folder), then run:
```powershell
powershell -ExecutionPolicy Bypass -File restore_after_reset.ps1
```
* This extracts and automatically places `.env`, `client_secret.json`, `token.pickle`, and all database files into their exact required locations!

*(Alternative manual method: If you prefer to manually copy, just extract the zip file directly into the `AI-VIDEO-V2` folder).*

---

## ⚡ STEP 3: ONE-CLICK AUTOMATED WORKSTATION SETUP

Now run the master setup script:
```powershell
powershell -ExecutionPolicy Bypass -File setup_windows.ps1
```

**What `setup_windows.ps1` does automatically:**
1. Checks that Git, Python 3.12, and FFmpeg are properly recognized.
2. Initializes all project directories (`downloads/`, `output/`, `temp/`, `logs/`, `data/`, `audio/`, `captions/`).
3. Upgrades `pip` and installs all dependencies from `requirements.txt`.
4. Validates that `.env`, `client_secret.json`, and `token.pickle` are present.
5. Runs the diagnostic verification suite.

---

## 🔍 STEP 4: DIAGNOSTIC HEALTH CHECK

To verify that every single technology and API connection is working 100%, run:
```powershell
python verify_environment.py
```

This diagnostic script runs an automated 10-point check:
* ✅ **Python Runtime** (Python 3.11/3.12 compatibility)
* ✅ **FFmpeg & FFprobe** (Video/audio rendering engine)
* ✅ **AI & Video Packages** (Groq, Edge-TTS, Pillow, OpenCV, NumPy, SciPy, Pandas, Streamlit)
* ✅ **Brand Typography** (Plus Jakarta Sans ExtraBold font)
* ✅ **Animated Outro & Audio SFX** (Transparent outro MOV & 48kHz stereo WAV chime)
* ✅ **API Keys** (Groq, Gemini, Pexels, Pixabay, Meta)
* ✅ **YouTube OAuth Credentials** (Validates `client_secret.json` and refreshable `token.pickle`)
* ✅ **Central Database** (`shortest_orbit_v3.db`)
* ✅ **Live Voice Synthesis** (Tests streaming `en-US-BrianMultilingualNeural`)

When all items report **`[PASS]`**, your workstation is completely ready.

---

## 🚀 STEP 5: HOW TO RUN & TEST

| Action | Command / Script | Description |
| :--- | :--- | :--- |
| **Dry Run Test (No Upload)** | `python python/main.py --no-upload` | Generates a complete 1080x1920 video to `output/short.mp4` without publishing. |
| **Full Local Production Run** | `.\run_pipeline.bat` | Discovers viral topic, generates script, voices, edits 4K footage, burns subtitles + outro, and uploads. |
| **Channel Web Dashboard** | `.\run_dashboard.bat` | Launches the interactive performance and analytics dashboard. |
| **Refresh YouTube Login** | `python get_fresh_token.py` | If `token.pickle` ever expires or needs re-auth, opens browser OAuth flow. |

---

## 🛠️ TROUBLESHOOTING & FAQ

### Q1: `ffmpeg` is not recognized as an internal or external command
* **Fix:** Open System Environment Variables -> Edit `Path` -> Add the directory containing `ffmpeg.exe` (e.g. `C:\Users\<user>\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_...` or your extraction path). Reopen terminal.

### Q2: Google OAuth token expired or invalid
* **Fix:** Ensure `client_secret.json` is present in the project root, then run:
  ```powershell
  python get_fresh_token.py
  ```
  Follow the on-screen browser prompt to sign in and grant YouTube Upload permissions.

### Q3: Python packages install failed or permission error
* **Fix:** Ensure you run:
  ```powershell
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```
