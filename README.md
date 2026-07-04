# AI Video Generator V2 🎬

AI Video Generator V2 is a clean, modular, production-ready python application that automatically builds a professional, high-retention YouTube Short from trending topics. It finds viral subjects, writes an engaging script, generates a natural-sounding Microsoft voiceover, downloads matching portrait stock videos, mixes background music, burns formatted subtitles, generates a custom high-CTR thumbnail, and uploads the video automatically to YouTube.

---

## 🛠️ Technology Stack & Services

- **LLM / Content Generator:** Groq Cloud API (`llama-3.3-70b-versatile`)
- **Voice Narration (TTS):** Microsoft Edge Text-to-Speech (free, neural, high quality)
- **Subtitles Aligning:** Edge TTS Word Boundaries / Timing metadata
- **Visual Stock Footage:** Pexels API (primary) & Pixabay API (fallback)
- **Image Generation (Thumbnail):** Google Gemini AI / Imagen 3 (with Pillow local graphic fallback)
- **Video Assembly:** FFmpeg CLI
- **YouTube Uploading:** YouTube Data API v3 (OAuth 2.0 Client credentials)

---

## 📂 Project Structure

```
AI-VIDEO-V2/
├── .env                          # API Keys
├── requirements.txt              # Python Dependencies
├── README.md                     # Documentation & setup guide
├── client_secret.json            # Google OAuth Client Credentials (you download this)
├── token.pickle                  # Cached YouTube API token (auto-generated)
│
├── config/
│   └── settings.json             # Global parameters & custom styling
│
├── assets/
│   ├── music/                    # Background music audio tracks (.mp3/.wav)
│   ├── fonts/                    # Custom subtitle fonts (.ttf)
│   ├── logos/                    # Branding assets
│   └── overlays/                 # Visual overlays
│
├── downloads/
│   ├── videos/                   # Raw downloaded scene stock clips
│   └── images/                   # Raw downloaded images
│
├── data/                         # Intermediate script/topic json data
├── audio/                        # Voiceover narration and timing data
├── captions/                     # Subtitles files (.srt)
├── output/                       # Final completed short.mp4 & thumbnail.png
├── logs/                         # Execution logs
└── temp/                         # Temporary video processing clips
```

---

## 🚀 Setup & Installation

### Prerequisite: Install FFmpeg
Make sure you have **FFmpeg** and **FFprobe** installed on your system and added to your system's Environment Variables `PATH`.
- **Windows:** Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or install via package manager: `winget install Gyan.FFmpeg`.
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

Verify it is installed by running:
```bash
ffmpeg -version
ffprobe -version
```

### 1. Clone the project and install requirements
Navigate to the project root and run:
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys in `.env`
Edit the `.env` file in the root directory and replace the placeholders with your API keys:
```env
GROQ_API_KEY=gsk_your_groq_api_key
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Setup YouTube Upload Credentials (Google Cloud OAuth)
To upload videos automatically, you need a Google Cloud Project with the YouTube Data API enabled:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Search for and enable the **YouTube Data API v3**.
4. Go to **APIs & Services** > **Credentials**.
5. Click **Configure Consent Screen**, choose **External**, enter basic app details, and **add your email to the test users list** (since your app will be in testing mode).
6. Go back to **Credentials**, click **Create Credentials** > **OAuth client ID**.
7. Select **Desktop app** as the Application Type, name it, and click **Create**.
8. Download the client secret JSON file from the credentials list.
9. Rename the file to `client_secret.json` and place it in the **root directory** of this project.

*Note: On your first upload, the script will open your web browser to authenticate. Accept the permissions, and it will save `token.pickle` in the root so future uploads run completely headless.*

### 4. Put background music in `assets/music/`
Place one or more royalty-free `.mp3` or `.wav` music tracks in the `assets/music/` directory. The program will randomly select one for the background music. If no files are present, the program will skip background music and mix voice-only.

---

## 🎮 Running the Generator

To generate and upload a viral YouTube Short end-to-end, simply run:
```bash
python python/main.py
```

This single command will sequentially run all 11 steps of the pipeline.

### Step-by-Step Testing
Every module is built to run independently for debugging:
```bash
# Step 1: Find trending topics
python python/find_viral_topics.py

# Step 2: Generate script & metadata
python python/generate_content.py

# Step 3: Speak narration
python python/generate_voice.py

# Step 4: Create aligned subtitles
python python/create_subtitles.py

# Step 5: Convert script into visual queries
python python/generate_search_queries.py

# Step 6: Download stock video clips
python python/download_videos.py

# Step 7: Crop, scale, & assemble silent video
python python/create_video.py

# Step 8: Mix narration & background music
python python/add_audio.py

# Step 9: Burn subtitles into video
python python/burn_subtitles.py

# Step 10: Generate YouTube thumbnail
python python/generate_thumbnail.py

# Step 11: Upload final short to YouTube
python python/upload_youtube.py
```

---

## ⚙️ Configuration & Customization (`config/settings.json`)

You can customize video properties, voice selections, subtitle styles, and more in `config/settings.json`:
- **LLM Settings:** Adjust creativity temperature and Groq models.
- **Voice Narration (TTS):** Choose different Microsoft neural voices (e.g. `en-US-GuyNeural`, `en-US-AvaNeural`, `en-GB-RyanNeural`).
- **Video Formatting:** Adjust target dimensions (default: 1080x1920 portrait) and framerates.
- **Audio Mix:** Adjust volume balance between voice narration and background music.
- **Subtitle Styling:** Customize font size, primary color, outline thickness, and vertical positioning.

---

## 📈 Logging & Troubleshooting

- Output files are generated in the `output/` directory (`short.mp4` and `thumbnail.png`).
- Logs are written to `logs/pipeline.log`. If anything fails, check this file for details.
- Temporary files are stored in `temp/` and automatically cleaned up after successful runs.
