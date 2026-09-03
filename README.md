<div align="center">

# 🚀 THE SHORTEST ORBIT
### *Autonomous V4.5 Content Growth & AI Video Production Engine*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-4K_UHD_Faststart-0078D4?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org)
[![Meta Graph API](https://img.shields.io/badge/Meta_Graph_API-v25.0-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](https://developers.facebook.com)
[![LLM Resilient](https://img.shields.io/badge/LLM-Groq_%2B_Gemini_Fallback-8E44AD?style=for-the-badge&logo=openai&logoColor=white)](#-resiliency--fallback-architecture)
[![Status](https://img.shields.io/badge/Status-Active_Production_Engine-2ECC71?style=for-the-badge)](#-project-status)

<p align="center">
  <b>"Understand the biggest battles, discoveries, and technologies shaping space, Earth, and the future — in seconds."</b>
</p>

---

</div>

> [!NOTE]  
> ### 🚀 System Overview
> **The Shortest Orbit** is a 100% autonomous, closed-loop AI video generation and multi-platform publishing engine. It discovers trending space, science, and technology stories across 15 global sources, verifies facts, generates 1.8s–2.5s fast-cut visual animations across 3 visual modalities, burns kinetic captions, and publishes across **YouTube Shorts**, **Facebook Reels**, and **Instagram Reels** 3 times daily on Cloud GitHub Actions servers.

---

## 📋 TABLE OF CONTENTS
1. [🌟 Core Features & Recent Upgrades](#-core-features--recent-upgrades)
2. [🔄 Closed-Loop Growth Architecture](#-closed-loop-growth-architecture)
3. [🛠️ End-to-End 12-Step Implementation Breakdown](#-end-to-end-12-step-implementation-breakdown)
4. [⏰ Global Posting Strategy & Schedule](#-global-posting-strategy--schedule)
5. [🗄️ Database Architecture & Schemas](#-database-architecture--schemas)
6. [⚠️ Limitations & Circuit Breakers](#%EF%B8%8F-limitations--circuit-breakers)
7. [🛡️ Resiliency & Fallback Architecture](#%EF%B8%8F-resiliency--fallback-architecture)
8. [📁 Complete Directory Structure](#-complete-directory-structure)
9. [⚙️ Environment Variables & Settings](#%EF%B8%8F-environment-variables--settings)
10. [💻 Installation & Running Guide](#-installation--running-guide)

---

## 🌟 CORE FEATURES & RECENT UPGRADES

- ⚡ **1.8s – 2.5s Fast Visual Beat Engine**: Automatically breaks narration scripts into **12 to 16 rapid visual beats per Short** (1 cut every 2 seconds), driving audience retention past **85%**.
- 🎨 **Tri-Modal Visual Generation**: Intelligently mixes 3 visual styles depending on scene context:
  1. ✏️ **Authentic Whiteboard / Ink Doodle Art** (hand-drawn progressive marker reveals on paper)
  2. 🎬 **Ultra-Realistic 4K Cinematic Footage** (high-contrast vertical stock motion from Pexels & Pixabay)
  3. 🌐 **3D Map / Tech Motion Graphics** (globe overlays, country highlighting, orbital trajectories)
- 📦 **Meta Resumable Upload Engine (`-movflags +faststart`)**: Fixed Meta Graph API container rejection on `rupload.facebook.com` by forcing `-movflags +faststart` across all FFmpeg video processing tasks for **100% upload success** on Instagram Reels & Facebook Reels.
- 🧲 **Curiosity-Gap & Hook Optimizer**: Generates 3 hook variations (*Shock, Mystery, Debate*) per topic and auto-rejects any hook scoring below **8.5/10**.
- 💬 **Rewatch Loop & Comment-Baiting**: Scripts end with provocative, opinion-splitting questions that drive high comment velocity and push rewatch retention >100%.
- 📊 **Automated Daily Analytics Harvester**: Periodically syncs view counts, likes, and subscriber growth from YouTube and Meta APIs into SQLite (`shortest_orbit_v3.db`).
- 🖥️ **YouTube Growth Command Center**: Modern Streamlit SaaS dashboard displaying channel readiness, view stats, and monetization milestones.

---

## 🔄 CLOSED-LOOP GROWTH ARCHITECTURE

```text
                  THE SHORTEST ORBIT V4.5 CLOSED-LOOP PIPELINE
                  
  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ 1. VIRAL TOPIC   │ ───► │ 2. FACT CHECK &  │ ───► │ 3. VOICE &       │
  │    DISCOVERY     │      │    HOOK ENGINE   │      │    WORD TIMINGS  │
  └──────────────────┘      └──────────────────┘      └────────┬─────────┘
                                                                │
  ┌──────────────────┐      ┌──────────────────┐               │
  │ 6. TRI-MODAL SCENE│ ◄─── │ 5. VISUAL BEAT   │ ◄─────────────┘
  │    GENERATOR     │      │    SPLITTER      │
  │ (Doodle/4K/3DMap)│      └──────────────────┘
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ 7. MOOD MUSIC &  │ ───► │ 8. STITCH FAST-  │ ───► │ 9. BURN KINETIC  │
  │    AUDIO MIXING  │      │    CUT 1080x1920 │      │    SUBTITLES     │
  └──────────────────┘      └──────────────────┘      └────────┬─────────┘
                                                                │
  ┌──────────────────┐      ┌──────────────────┐               │
  │ 12. GROWTH       │ ◄─── │ 11. TRIPLE-PLATFORM│ ◄───────────┘
  │     DASHBOARD    │      │    PUBLISH & SYNC│ (YouTube/FB/IG)
  └──────────────────┘      └──────────────────┘
```

---

## 🛠️ END-TO-END 12-STEP IMPLEMENTATION BREAKDOWN

| Step | Module File | Technical Engine & Function |
| :---: | :--- | :--- |
| **01** | [`python/find_viral_topics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/find_viral_topics.py) | **Viral Topic Discovery**: Scrapes 15 global sources (Reddit *r/space*, *r/science*, *r/Futurology*, Google Trends US, Google News, NASA RSS, ESA, SpaceX, MIT, Nature, ScienceDaily, arXiv, OpenAI, Anthropic, DeepMind, Wikipedia Trending). Calculates V4 Opportunity Score: $$TopicScore = 0.25(I) + 0.20(C) + 0.20(N) + 0.15(Q) + 0.10(S) + 0.10(B)$$ |
| **02** | [`python/generate_content.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_content.py)<br>[`python/verify_facts.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/verify_facts.py) | **Fact Verification & Hook Optimizer**: Checks facts against 7 authority sources (`accuracy_score >= 7.0`). Evaluates 3 hook styles (*Curiosity, Shock, Debate*). Generates 75–105 word scripts ending with provocative debate questions. Auto-rejects hooks scoring $<8.5/10$. |
| **03** | [`python/generate_voice.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_voice.py) | **Neural Voice Synthesis**: EdgeTTS (`en-US-AndrewMultilingualNeural`) with +5% rate for punchy pacing. Generates precise JSON word-level timings. |
| **04** | [`python/create_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_subtitles.py) | **Karaoke SRT Generator**: Groups words into 2–3 word chunks with HTML gold (`#FFD60A`) keyword highlighting. |
| **05** | [`python/generate_search_queries.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_search_queries.py) | **Visual Beat Splitter**: Splits long narration sentences into **1.8s–2.5s visual beats**. Assigns visual style (`doodle`, `cinematic`, `map_motion`), physical search query, camera motion, and prompt. |
| **06** | [`python/multi_style_generator.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/multi_style_generator.py)<br>[`python/generate_whiteboard.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_whiteboard.py)<br>[`python/generate_map_graphics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_map_graphics.py)<br>[`python/generate_fal_videos.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_fal_videos.py) | **Tri-Modal Render Engine**: Renders doodle art marker sketch reveals on paper surface, 3D map globe overlays with camera pan/zoom motion, 4K vertical stock motion downloads, and Fal.ai Minimax/Kling 1.5 video generation (with `_FAL_DISABLED` circuit breaker). |
| **07** | [`python/create_video.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_video.py) | **Video Assembly**: Concatenates 12–16 visual clips, scales/crops to 1080x1920 portrait format, applies smooth looping for short clips, and encodes with `-movflags +faststart`. |
| **07.5** | [`python/download_music.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/download_music.py) | **Music Downloader**: Asks Groq for viral audio mood keyword (`viral-space-epic`, `upbeat`, `cinematic`) and downloads royalty-free MP3 from Pixabay CDN to `assets/music/background.mp3`. |
| **08** | [`python/add_audio.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/add_audio.py) | **Audio Mixer**: Mixes narration voiceover (vol 1.0) with background music (vol 0.30) into `temp/video_audio.mp4`. |
| **09** | [`python/burn_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/burn_subtitles.py) | **Hard Subtitle Burn**: Burns custom Bebas Neue captions with semi-transparent background box into `output/short.mp4` using `-movflags +faststart`. |
| **10** | [`python/generate_thumbnail.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_thumbnail.py) | **High-CTR Thumbnail Generator**: Generates high-contrast editorial thumbnails using Google Gemini Imagen 3 API with frame extraction fallback. |
| **10.5** | [`python/quality_checker.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/quality_checker.py) | **Quality Gatekeeper**: Automated validation of script engagement, video resolution ($1080\times1920$), FPS ($30$), and audio presence. Minimum passing score: 8.5/10. |
| **11** | [`python/publish_service.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/publish_service.py)<br>[`python/upload_youtube.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/upload_youtube.py)<br>[`python/upload_facebook.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/upload_facebook.py)<br>[`python/upload_instagram.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/upload_instagram.py) | **Triple-Platform Publishing**: Uploads to YouTube Shorts, Facebook Reels, and Instagram Reels via Meta Graph API v25.0, with resumable container polling. |
| **11.5** | [`python/harvest_analytics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/harvest_analytics.py) | **Analytics Harvester**: Pulls real-time YouTube views, likes, subscriber count, Facebook Reel views, and Instagram Reel plays into SQLite database (`shortest_orbit_v3.db`). |
| **12** | [`python/youtube_dashboard.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/youtube_dashboard.py) | **Growth Command Center**: Streamlit SaaS dashboard displaying channel readiness, daily view progress, and monetization milestones. |

---

## ⏰ GLOBAL POSTING STRATEGY & SCHEDULE

The channel is configured to publish **exactly 3 Shorts per day** across 3 global prime-time slots in [`.github/workflows/main.yml`](file:///.github/workflows/main.yml):

```yaml
  schedule:
    - cron: "30 11 * * *"  # Slot 1: 5:00 PM IST  / 7:30 AM EST  (US Morning Commute Peak)
    - cron: "0 16 * * *"   # Slot 2: 9:30 PM IST  / 12:00 PM EST (US Lunch & European Evening)
    - cron: "30 22 * * *"  # Slot 3: 4:00 AM IST  / 6:30 PM EST  (US Evening Prime-Time Peak)
```

---

## 🗄️ DATABASE ARCHITECTURE & SCHEMAS

The system uses SQLite databases (`data/shortest_orbit_v3.db`, `data/automation.db`, `data/youtube.db`, `data/facebook.db`, `data/instagram.db`) to track production and analytics across 7 core tables:

1. **`videos`**: `id`, `title`, `topic_id`, `script`, `youtube_id`, `facebook_id`, `facebook_url`, `instagram_id`, `instagram_url`, `status`, `created_at`, `uploaded_at`
2. **`topics`**: `id`, `title`, `source`, `trend_score`, `engagement_potential`, `retention_potential`, `status`, `created_at`
3. **`hooks`**: `id`, `video_id`, `text`, `score`, `selected`
4. **`analytics`**: `id`, `video_id`, `date`, `views`, `likes`, `comments`, `shares`, `subscribers_gained`, `fb_views`, `fb_likes`, `fb_comments`, `ig_views`, `ig_likes`, `ig_comments`
5. **`monetization_snapshots`**: `id`, `date`, `subscribers`, `shorts_views`, `watch_hours`, `uploads_90_days`, `progress_percentage`, `readiness_score`, `created_at`
6. **`daily_monetization_targets`**: `id`, `date`, `remaining_days`, `subs_needed_per_day`, `views_needed_per_day`, `hours_needed_per_day`, `ai_recommendation`
7. **`sqlite_sequence`**: Sequence tracker.

---

## ⚠️ LIMITATIONS & CIRCUIT BREAKERS

> [!WARNING]  
> ### Active System Limitations & Graceful Fallbacks
>
> 1. **AWS Bedrock Nova Reel On-Demand Quota (`amazon.nova-reel-v1:1`)**:
>    - **Status**: AWS Account `719312763637` is currently awaiting AWS Support Quota Provisioning (AWS Case `178767424800583`).
>    - **Fallback Protocol**: Upon encountering `ValidationException`, the pipeline seamlessly falls back to the **Tri-Modal Visual Engine** (Doodle + 4K Cinematic + 3D Maps) without blocking execution.
>
> 2. **Fal.ai Video API Balance Circuit Breaker**:
>    - **Status**: If Fal.ai credit balance reaches 0, the internal circuit breaker (`_FAL_DISABLED`) instantly bypasses API retries to prevent 15-second network delays.
>
> 3. **Meta Graph API Faststart Requirement**:
>    - **Status**: Meta Graph API `rupload.facebook.com` rejects binary video uploads that lack `-movflags +faststart` at byte offset 0. All FFmpeg encoders hardcode `-movflags +faststart`.
>
> 4. **YouTube Daily Upload Quota**:
>    - **Status**: Capped at `daily_upload_cap: 3` in `settings.json` to prevent API quota exhaustion.

---

## 🛡️ RESILIENCY & FALLBACK ARCHITECTURE

- 🔄 **Multi-Tier LLM Rotation**: If Groq API rate limits (HTTP 429) occur, `call_groq_with_fallback()` rotates model tiers (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`, `qwen-2.5-coder-32b`) before triggering **Gemini 2.5 Flash API**.
- 🧹 **Robust JSON Parsing**: `extract_json_from_llm()` automatically strips reasoning tags (`<think>...</think>`) and markdown blocks before parsing JSON.
- ⚡ **FFmpeg Faststart Encoding**: Encodes videos using `-preset fast -movflags +faststart` to optimize streaming performance for Meta Graph API.
- 🔁 **Duplicate Asset Protection**: Queries SQLite to prevent re-using stock video clip IDs or topic titles published within the last 30 days.

---

## 📁 COMPLETE DIRECTORY STRUCTURE

```text
AI-VIDEO-V2/
├── .github/
│   └── workflows/
│       └── main.yml                   # Cloud GitHub Actions workflow (3 posts/day schedule)
├── assets/
│   ├── fonts/                         # Custom typography (Bebas Neue, Cinzel, Montserrat)
│   └── music/                         # Royalty-free background music files
├── config/
│   └── settings.json                  # System configuration settings
├── data/
│   ├── shortest_orbit_v3.db           # Central SQLite database
│   ├── content.json                   # Generated narration script
│   ├── metadata.json                  # YouTube & Meta SEO metadata
│   ├── viral_topics.json              # Selected viral topic
│   └── word_timings.json              # Word-level TTS timestamps
├── downloads/
│   └── videos/                        # Downloaded & rendered scene video clips
├── logs/
│   └── pipeline.log                   # Execution logs
├── output/
│   └── short.mp4                      # Final subtitled video output
├── python/
│   ├── main.py                        # Master pipeline orchestrator
│   ├── find_viral_topics.py           # Step 1: 15-source topic discovery
│   ├── generate_content.py            # Step 2: Fact checking & hook optimization
│   ├── verify_facts.py                # Step 2b: 7-level scientific fact check
│   ├── generate_voice.py              # Step 3: EdgeTTS voiceover & word timings
│   ├── create_subtitles.py            # Step 4: Karaoke SRT generator
│   ├── generate_search_queries.py     # Step 5: Visual beat splitter (1.8s-2.5s cuts)
│   ├── multi_style_generator.py       # Step 6: Tri-modal visual scene generator
│   ├── generate_whiteboard.py         # Step 6a: Doodle sketch animation generator
│   ├── generate_map_graphics.py       # Step 6b: 3D globe map motion graphic generator
│   ├── generate_fal_videos.py         # Step 6c: Fal.ai Minimax/Kling generator (circuit breaker)
│   ├── create_video.py                # Step 7: Video clip stitching (-movflags +faststart)
│   ├── download_music.py              # Step 7.5: Pixabay CDN music downloader
│   ├── add_audio.py                   # Step 8: Voice + music audio mixer
│   ├── burn_subtitles.py              # Step 9: Kinetic subtitle hard-burner
│   ├── generate_thumbnail.py          # Step 10: Gemini Imagen 3 thumbnail generator
│   ├── quality_checker.py             # Step 10.5: Automated quality gatekeeper
│   ├── publish_service.py             # Step 11: Multi-platform publisher
│   ├── upload_youtube.py              # Step 11a: YouTube API uploader
│   ├── upload_facebook.py             # Step 11b: Facebook Reels Graph API uploader
│   ├── upload_instagram.py            # Step 11c: Instagram Reels resumable container uploader
│   ├── harvest_analytics.py           # Step 11.5: Daily analytics harvester
│   └── youtube_dashboard.py           # Step 12: Streamlit Growth SaaS dashboard
├── utils/
│   ├── config.py                      # Config & LLM fallback helper
│   ├── ffmpeg.py                      # FFmpeg wrapper with -movflags +faststart
│   ├── helpers.py                     # JSON extraction & filesystem helpers
│   ├── logger.py                      # Logging utility
│   ├── paths.py                       # Project path definitions
│   └── retry.py                       # Retrying decorator
├── .env                               # Secret credentials & API keys
├── requirements.txt                   # Python dependencies
└── README.md                          # Comprehensive project documentation
```

---

## ⚙️ ENVIRONMENT VARIABLES & SETTINGS

### Required Environment Variables (`.env`)

```ini
GROQ_API_KEY=gsk_...
PEXELS_API_KEY=...
PIXABAY_API_KEY=...
GEMINI_API_KEY=AIzaSy...
META_APP_ID=...
META_APP_SECRET=...
META_ACCESS_TOKEN=EAAG...
FACEBOOK_PAGE_ID=1168804842990122
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841435307918273
FAL_KEY=...
REPLICATE_API_TOKEN=...
```

### Core Configuration (`config/settings.json`)

```json
{
  "upload": {
    "privacy": "public",
    "category": "22",
    "daily_upload_cap": 3,
    "timezone": "Asia/Kolkata"
  },
  "audio": {
    "voice_volume": 1.0,
    "music_volume": 0.30
  },
  "subtitles": {
    "font": "Bebas Neue",
    "fontsize": 22,
    "margin_vertical": 60
  },
  "publish": {
    "platforms": ["youtube", "facebook", "instagram"],
    "continue_on_failure": true
  }
}
```

---

## 💻 INSTALLATION & RUNNING GUIDE

### 1. System Prerequisites
- **Python 3.11+**
- **FFmpeg** (installed and added to system PATH)
- **Git**

### 2. Setup Commands

```bash
# 1. Clone the repository
git clone https://github.com/ravindrareddy17/ai-video-generator.git
cd ai-video-generator

# 2. Create and activate virtual environment
python -m venv venv
# On Windows PowerShell:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt
```

### 3. Execution Commands

```bash
# Run full end-to-end video generation and multi-platform upload:
python python/main.py

# Launch Streamlit Growth SaaS Dashboard:
streamlit run python/youtube_dashboard.py
```

---

<div align="center">

<b>THE SHORTEST ORBIT V4.5</b> • *Autonomous AI Video Generation & Channel Growth Engine*

</div>
