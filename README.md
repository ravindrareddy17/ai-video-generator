<![CDATA[<div align="center">

# 🚀 AI Video Generator V2 — *The Shortest Orbit*

### Fully Autonomous AI-Powered Short-Form Video Pipeline

**Finds trending topics → Writes scripts → Generates voice → Downloads visuals → Edits video → Uploads to YouTube, Instagram & Facebook — all on autopilot.**

[![Pipeline](https://img.shields.io/badge/Pipeline-12_Steps-blueviolet?style=for-the-badge)](#-pipeline-overview)
[![Platforms](https://img.shields.io/badge/Platforms-YouTube_|_Instagram_|_Facebook-red?style=for-the-badge)](#-multi-platform-publishing)
[![Automation](https://img.shields.io/badge/Automation-GitHub_Actions-2088FF?style=for-the-badge)](#-cicd-automation-github-actions)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](#-license)

</div>

---

## 📖 What Is This?

**AI Video Generator V2** is a production-grade, end-to-end Python pipeline that automatically creates and publishes short-form vertical videos (YouTube Shorts, Instagram Reels, Facebook Reels) — with **zero human intervention**.

Every run of the pipeline:

1. 🔍 Scans **15+ real-time sources** (Google Trends, Google News, Reddit, NASA, SpaceX, Nature, arXiv, OpenAI, DeepMind, etc.) to find the most viral trending topic.
2. ✍️ Writes a concise, engaging narration script using an LLM with built-in **fact-checking** and **quality control**.
3. 🎙️ Generates a natural-sounding voiceover with Microsoft Neural TTS.
4. 🎬 Downloads matching royalty-free stock footage, assembles it into a vertical video, and mixes in mood-matched background music.
5. 💬 Burns stylized karaoke-style subtitles directly onto the video.
6. 🖼️ Generates a high-CTR thumbnail using AI image generation.
7. 📤 Uploads the finished video simultaneously to **YouTube**, **Instagram**, and **Facebook**.
8. 📊 Harvests post-upload analytics from all platforms and feeds them into a **self-learning AI engine** that improves future content.

The entire pipeline runs in **~5 minutes** and is scheduled to execute **5 times per day** via GitHub Actions — posting content at globally optimized prime-time hours.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔥 **Viral Topic Discovery** | Aggregates 1,500+ topics from 15 real-time sources every run |
| 🧠 **AI Script Generation** | Groq LLM writes scripts with psychological hooks for maximum retention |
| ✅ **Automated Fact-Checking** | AI verifies every claim before publishing; regenerates if inaccurate |
| 🎙️ **Neural Voice Narration** | Microsoft Edge TTS with multiple voice profiles and audio normalization |
| 🎬 **Smart Video Assembly** | Downloads stock footage from Pexels/Pixabay, handles deduplication, crops to 9:16 |
| 🎵 **Mood-Matched Music** | AI selects music profile based on topic; downloads royalty-free tracks |
| 💬 **Karaoke Subtitles** | Word-level timing alignment with custom fonts, colors, and styling |
| 🖼️ **AI Thumbnail Generation** | Google Imagen or intelligent local fallback with typography |
| 📤 **Multi-Platform Publishing** | Simultaneous upload to YouTube Shorts, Instagram Reels, and Facebook Reels |
| 📊 **Analytics Harvesting** | Automatically tracks views, likes, reach, and engagement across all platforms |
| 🤖 **Self-Learning Engine** | AI analyzes past performance to predict and improve future content |
| ⏰ **Fully Automated Scheduling** | GitHub Actions CI/CD runs 5x daily at global prime-time hours |
| 🛡️ **Visual Deduplication** | Tracks previously used stock footage to ensure every video looks unique |
| 📈 **Monetization Tracking** | Monitors YouTube Partner Program readiness (subscribers + watch hours) |

---

## 🏗️ Pipeline Overview

The pipeline consists of **12 sequential steps**, orchestrated by `main.py`:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI VIDEO GENERATOR V2                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Step 1   → 🔍 Find Viral Topics        (15+ real-time sources)        │
│  Step 2   → ✍️  Generate Script & SEO    (Groq LLM + metadata)         │
│  Step 2.5 → ✅ Fact-Check Script         (AI claim verification)        │
│  Step 2.6 → 🏆 Quality Control          (AI quality gate)              │
│  Step 3   → 🎙️ Generate Voice           (Microsoft Neural TTS)         │
│  Step 4   → 💬 Create Subtitles         (Word-level karaoke SRT)       │
│  Step 5   → 🔎 Generate Search Queries  (Visual scene prompts)         │
│  Step 6   → 📥 Download Stock Footage   (Pexels + Pixabay)             │
│  Step 7   → 🎬 Assemble Silent Video    (FFmpeg crop/scale/concat)     │
│  Step 7.5 → 🎵 Download Background Music(Mood-matched royalty-free)    │
│  Step 8   → 🔊 Mix Audio               (Voice + music + ducking)      │
│  Step 9   → 💬 Burn Subtitles           (Hardcoded styled captions)    │
│  Step 10  → 🖼️ Generate Thumbnail       (AI Imagen / local fallback)   │
│  Step 11  → 📤 Publish to Platforms     (YouTube + Instagram + FB)     │
│  Step 11.5→ 📊 Harvest Analytics        (Views, likes, engagement)     │
│  Step 12  → 🤖 Self-Learning Loop       (AI performance analysis)      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **LLM / Content Engine** | Groq Cloud API (`llama-3.3-70b-versatile`) |
| **Voice Narration (TTS)** | Microsoft Edge TTS (free, neural, high-quality) |
| **Stock Footage** | Pexels API (primary) + Pixabay API (fallback) |
| **Thumbnail Generation** | Google Gemini AI / Imagen (with Pillow local fallback) |
| **Video Processing** | FFmpeg (crop, scale, concat, audio mix, subtitle burn) |
| **YouTube Upload** | YouTube Data API v3 (OAuth 2.0) |
| **Instagram / Facebook** | Meta Graph API (OAuth) |
| **Database** | SQLite (video tracking, analytics, AI learning) |
| **CI/CD Automation** | GitHub Actions (5x daily cron schedule) |
| **Analytics Dashboard** | HTML + Chart.js (local browser dashboard) |
| **Language** | Python 3.11+ |

---

## 📂 Project Structure

```
AI-VIDEO-V2/
├── .github/
│   └── workflows/
│       └── main.yml                 # GitHub Actions CI/CD workflow
│
├── python/                          # Core pipeline modules
│   ├── main.py                      # 🎯 Pipeline orchestrator (entry point)
│   ├── find_viral_topics.py         # Step 1:  Viral topic discovery
│   ├── generate_content.py          # Step 2:  Script & metadata generation
│   ├── verify_facts.py              # Step 2.5: AI fact-checking
│   ├── quality_checker.py           # Step 2.6: Script quality control
│   ├── generate_voice.py            # Step 3:  TTS voice narration
│   ├── create_subtitles.py          # Step 4:  Karaoke subtitle alignment
│   ├── generate_search_queries.py   # Step 5:  Visual search prompts
│   ├── download_videos.py           # Step 6:  Stock footage downloader
│   ├── create_video.py              # Step 7:  Video assembly (FFmpeg)
│   ├── download_music.py            # Step 7.5: Background music
│   ├── add_audio.py                 # Step 8:  Audio mixing
│   ├── burn_subtitles.py            # Step 9:  Subtitle burning
│   ├── generate_thumbnail.py        # Step 10: Thumbnail generation
│   ├── publish_service.py           # Step 11: Multi-platform publisher
│   ├── upload_youtube.py            # YouTube Shorts uploader
│   ├── upload_instagram.py          # Instagram Reels uploader
│   ├── upload_facebook.py           # Facebook Reels uploader
│   ├── harvest_analytics.py         # Step 11.5: Analytics harvesting
│   ├── self_learning.py             # Step 12: AI self-learning engine
│   ├── meta_auth.py                 # Meta (Instagram/Facebook) auth
│   └── dashboard_app.py             # Analytics dashboard server
│
├── automation/                      # Platform-specific analytics & AI
│   ├── ai/                          # Self-learning, prediction, recommendation
│   ├── youtube/                     # YouTube analytics module
│   ├── instagram/                   # Instagram analytics module
│   ├── facebook/                    # Facebook analytics module
│   ├── competitor/                  # Competitor analysis module
│   └── database/                    # Platform-isolated SQLite databases
│
├── utils/                           # Shared utilities
│   ├── config.py                    # Configuration loader
│   ├── database.py                  # SQLite database manager
│   ├── ffmpeg.py                    # FFmpeg/FFprobe wrapper
│   ├── helpers.py                   # General helper functions
│   ├── logger.py                    # Structured logging
│   ├── paths.py                     # Centralized path definitions
│   └── retry.py                     # Retry/backoff utilities
│
├── config/
│   └── settings.json                # Global configuration & styling
│
├── dashboard/                       # Browser-based analytics dashboard
│   ├── index.html                   # Dashboard UI
│   └── chart.js                     # Chart.js library
│
├── assets/
│   ├── music/                       # Background music tracks
│   └── fonts/                       # Custom subtitle fonts (Bebas Neue, Cinzel)
│
├── data/                            # Runtime data (topics, scripts, databases)
├── audio/                           # Generated voiceovers & timing data
├── captions/                        # Generated subtitle files (.srt)
├── downloads/videos/                # Downloaded stock footage
├── output/                          # Final video (short.mp4) & thumbnail
├── logs/                            # Pipeline execution logs
├── temp/                            # Temporary processing files
│
├── .env                             # API keys (git-ignored)
├── client_secret.json               # Google OAuth credentials (git-ignored)
├── token.pickle                     # Cached YouTube auth token (git-ignored)
└── requirements.txt                 # Python dependencies
```

---

## 🚀 Setup & Installation

### Prerequisites

- **Python 3.11+**
- **FFmpeg** & **FFprobe** installed and added to your system's `PATH`

```bash
# Verify FFmpeg is installed
ffmpeg -version
ffprobe -version
```

> **Install FFmpeg:**
> - **Windows:** `winget install Gyan.FFmpeg` or download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
> - **macOS:** `brew install ffmpeg`
> - **Linux:** `sudo apt install ffmpeg`

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/ravindrareddy17/ai-video-generator.git
cd ai-video-generator
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```env
# Required — Content & Video Generation
GROQ_API_KEY=gsk_your_groq_api_key
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key
GEMINI_API_KEY=your_gemini_api_key

# Optional — Multi-Platform Publishing (Instagram & Facebook)
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_ACCESS_TOKEN=your_meta_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_id
```

> **Where to get API keys:**
> | Key | Source |
> |---|---|
> | `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) (free tier available) |
> | `PEXELS_API_KEY` | [pexels.com/api](https://www.pexels.com/api/) (free) |
> | `PIXABAY_API_KEY` | [pixabay.com/api/docs](https://pixabay.com/api/docs/) (free) |
> | `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) (free tier) |
> | Meta keys | [developers.facebook.com](https://developers.facebook.com/) |

### 3. Setup YouTube Upload (Google OAuth)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and enable the **YouTube Data API v3**.
3. Go to **APIs & Services** → **Credentials** → **Configure Consent Screen**.
4. Choose **External**, fill in basic details, and add your email to test users.
5. Create an **OAuth client ID** → select **Desktop app** → download the JSON.
6. Rename the file to `client_secret.json` and place it in the project root.

> On your first run, a browser window will open for authentication. After granting access, `token.pickle` is saved automatically and all future runs are headless.

### 4. Setup Instagram & Facebook (Optional)

If you want multi-platform publishing, configure a [Meta Developer App](https://developers.facebook.com/) with the following permissions:
- `instagram_content_publish`, `instagram_basic`, `pages_manage_posts`, `publish_video`

Set the corresponding environment variables in your `.env` file.

---

## ▶️ Running the Pipeline

### Full Pipeline (Recommended)

```bash
python python/main.py
```

This single command runs all 12 steps end-to-end in approximately **5 minutes**, producing a finished video and uploading it to all configured platforms.

### Individual Steps (For Debugging)

Each module can be run independently:

```bash
python python/find_viral_topics.py       # Step 1:   Find trending topics
python python/generate_content.py        # Step 2:   Generate script & metadata
python python/verify_facts.py            # Step 2.5: Fact-check the script
python python/quality_checker.py         # Step 2.6: Quality control
python python/generate_voice.py          # Step 3:   Generate voiceover
python python/create_subtitles.py        # Step 4:   Create subtitles
python python/generate_search_queries.py # Step 5:   Generate visual queries
python python/download_videos.py         # Step 6:   Download stock footage
python python/create_video.py            # Step 7:   Assemble silent video
python python/download_music.py          # Step 7.5: Download background music
python python/add_audio.py              # Step 8:   Mix audio
python python/burn_subtitles.py         # Step 9:   Burn subtitles
python python/generate_thumbnail.py     # Step 10:  Generate thumbnail
python python/upload_youtube.py         # Step 11:  Upload to YouTube
```

---

## ⏰ CI/CD Automation (GitHub Actions)

The pipeline runs fully automated via GitHub Actions on a **5x daily schedule**, optimized for global prime-time hours:

| Schedule (UTC) | US (EST) | UK (BST) | India (IST) | Target Audience |
|---|---|---|---|---|
| `0 11 * * *` | 7:00 AM | 12:00 PM | 4:30 PM | Morning commute peak |
| `0 15 * * *` | 11:00 AM | 4:00 PM | 8:30 PM | US lunch & EU afternoon |
| `30 18 * * *` | 2:30 PM | 7:30 PM | 12:00 AM | US afternoon & EU prime-time |
| `0 22 * * *` | 6:00 PM | 11:00 PM | 3:30 AM | US evening peak |
| `30 1 * * *` | 9:30 PM | 2:30 AM | 7:00 AM | US late night & Asia morning |

### Setting Up GitHub Actions

1. Push this repository to GitHub.
2. Go to **Settings** → **Secrets and variables** → **Actions**.
3. Add the following **Repository Secrets**:

| Secret Name | Value |
|---|---|
| `GROQ_API_KEY` | Your Groq API key |
| `PEXELS_API_KEY` | Your Pexels API key |
| `PIXABAY_API_KEY` | Your Pixabay API key |
| `GEMINI_API_KEY` | Your Gemini API key |
| `TOKEN_PICKLE_BASE64` | Base64-encoded `token.pickle` * |
| `CLIENT_SECRET_BASE64` | Base64-encoded `client_secret.json` * |
| `META_APP_ID` | Your Meta App ID |
| `META_APP_SECRET` | Your Meta App Secret |
| `META_ACCESS_TOKEN` | Your Meta Access Token |
| `FACEBOOK_PAGE_ID` | Your Facebook Page ID |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Your Instagram Business Account ID |

> \* **To encode files to base64:**
> ```bash
> # On Linux/Mac
> base64 -w 0 token.pickle
> base64 -w 0 client_secret.json
>
> # On Windows (PowerShell)
> [Convert]::ToBase64String([IO.File]::ReadAllBytes("token.pickle"))
> [Convert]::ToBase64String([IO.File]::ReadAllBytes("client_secret.json"))
> ```

4. The pipeline will now run automatically 5 times per day!

You can also trigger a manual run from the **Actions** tab → **Run workflow**.

---

## 📊 Analytics Dashboard

A built-in browser-based analytics dashboard is included for tracking performance across all platforms.

```bash
# Launch the dashboard
python python/dashboard_app.py
```

Then open `dashboard/index.html` in your browser to view:
- 📈 Views, likes, and engagement trends over time
- 📊 Platform-by-platform performance comparison
- 🎯 Monetization progress tracking (YouTube Partner Program)
- 🤖 AI prediction accuracy metrics

---

## 🤖 Self-Learning AI Engine

The pipeline includes a built-in **self-learning feedback loop** that continuously improves content quality:

1. **Analytics Harvesting** — After each upload, the system collects real performance data (views, likes, engagement) from YouTube, Instagram, and Facebook.
2. **Prediction vs. Reality** — The AI compares its predicted performance against actual results to calibrate its models.
3. **Insight Generation** — The learning engine analyzes patterns across all historical videos to identify what topics, hooks, and styles perform best.
4. **Content Optimization** — Future scripts and metadata are influenced by these learned insights, creating a positive feedback loop.

All learning data is stored in local SQLite databases and synced to the repository automatically.

---

## ⚙️ Configuration

Customize video properties, voice, subtitles, and more in `config/settings.json`:

| Setting | Options |
|---|---|
| **LLM Model** | Groq model selection & temperature |
| **Voice Profile** | Microsoft Neural voices (`en-US-SteffanNeural`, `en-US-GuyNeural`, `en-US-AvaNeural`, etc.) |
| **Video Format** | Target resolution (default: 1080×1920), framerate, CRF quality |
| **Audio Mix** | Voice volume, music volume, sidechain ducking parameters |
| **Subtitle Style** | Font family, size, colors, outline thickness, vertical position |
| **Upload Settings** | Privacy status, category, daily upload limits per platform |

---

## 🔒 Security

All sensitive data is protected:

- API keys are stored in `.env` (git-ignored) and GitHub Secrets (encrypted)
- OAuth tokens (`token.pickle`, `client_secret.json`) are git-ignored
- The `.gitignore` is pre-configured to prevent accidental credential leaks
- Meta/YouTube tokens are reconstructed at runtime from encrypted GitHub Secrets

---

## 📈 Logging & Troubleshooting

- **Logs:** `logs/pipeline.log` — Detailed execution log for every pipeline run
- **Output:** `output/short.mp4` and `output/thumbnail.png` — Final generated assets
- **Temp files:** `temp/` — Automatically cleaned up after each successful run
- **Database:** `data/shortest_orbit_v3.db` — Central video tracking database

If a pipeline run fails, check `logs/pipeline.log` for detailed error messages and stack traces.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ by [@ravindrareddy17](https://github.com/ravindrareddy17)**

*Automating content creation, one video at a time.*

</div>
]]>
