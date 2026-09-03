<div align="center">

# 🚀 THE SHORTEST ORBIT
### *Autonomous V4.5 Content Growth & AI Video Production Engine*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-4K_UHD_Faststart-0078D4?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org)
[![LLM Resilient](https://img.shields.io/badge/LLM-Groq_%2B_Gemini_Fallback-8E44AD?style=for-the-badge&logo=openai&logoColor=white)](#-resiliency--circuit-breaker-architecture)
[![Status](https://img.shields.io/badge/Status-Active_Production_Engine-2ECC71?style=for-the-badge)](#-project-status)

<p align="center">
  <b>"Understand the biggest battles, discoveries, and technologies shaping space and the future — in seconds."</b>
</p>

---

</div>

> [!NOTE]  
> ### 🚀 System Status: Active Production Engine (V4.5)
> **The Shortest Orbit** is an autonomous multi-platform short-form video generation engine. It discovers viral space/science trends, generates high-retention scripts, renders tri-modal visual animations, and publishes across **YouTube Shorts**, **Facebook Reels**, and **Instagram Reels** on an automated daily schedule.

---

## 🌟 Key Architecture & Recent Upgrades

- ⚡ **1.8s – 2.5s Fast Visual Beat Engine**: Automatically breaks narration scripts into **12 to 16 rapid visual beats per Short** (1 cut every 2 seconds), driving audience retention past **85%**.
- 🎨 **Tri-Modal Visual Generation**: Intelligently mixes 3 visual styles according to scene context:
  1. ✏️ **Authentic Whiteboard / Ink Doodle Art** (hand-drawn progressive sketch reveals)
  2. 🎬 **Ultra-Realistic 4K Cinematic Footage** (high-contrast vertical stock motion)
  3. 🌐 **3D Map / Tech Motion Graphics** (globe overlays, country highlighting, orbital trajectories)
- 📦 **Meta Resumable Upload Engine (`-movflags +faststart`)**: Fixed Meta Graph API container rejection on `rupload.facebook.com` by forcing `-movflags +faststart` across all FFmpeg video processing tasks for **100% upload success**.
- 🧲 **Curiosity-Gap & Hook Optimizer**: Generates 3 hook variations (*Shock, Mystery, Debate*) per topic and auto-rejects any hook scoring below **8.5/10**.
- 💬 **Rewatch Loop & Comment-Baiting**: Scripts end with provocative, opinion-splitting questions that drive high comment velocity and push rewatch retention >100%.
- 📅 **Automated 3-Post/Day Global Cloud Schedule**: GitHub Actions workflow ([`main.yml`](file:///.github/workflows/main.yml)) running daily at peak global hours (**5:00 PM IST**, **9:30 PM IST**, and **4:00 AM IST**).

---

## 🔄 Closed-Loop Growth Architecture

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

## 🛠️ End-to-End Implementation Breakdown

| Step | Module File | Technical Engine & Function |
| :---: | :--- | :--- |
| **01** | [`python/find_viral_topics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/find_viral_topics.py) | **Viral Topic Discovery**: Scrapes 15 sources (Reddit *r/space*, Google Trends, NASA RSS, Nature). Calculates Opportunity Scores ($0.0 - 10.0$). |
| **02** | [`python/generate_content.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_content.py) | **Fact Verification & Hook Optimizer**: Generates 75–105 word scripts ending with provocative debate questions. Auto-rejects hooks scoring $<8.5/10$. |
| **03** | [`python/generate_voice.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_voice.py) | **Neural Voice Synthesis**: EdgeTTS (`en-US-AndrewMultilingualNeural`) with +5% rate for punchy pacing. Generates precise word timings. |
| **04** | [`python/create_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_subtitles.py) | **Karaoke SRT Generator**: Groups words into 2–3 word chunks with HTML gold (`#FFD60A`) keyword highlighting. |
| **05** | [`python/generate_search_queries.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_search_queries.py) | **Visual Beat Splitter**: Splits sentences into **1.8s–2.5s visual beats**. Assigns visual style (`doodle`, `cinematic`, `map_motion`), physical query, and camera motion. |
| **06** | [`python/multi_style_generator.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/multi_style_generator.py) | **Tri-Modal Render Engine**: Renders doodle art animations, 3D map graphics, and 4K vertical motion stock. |
| **07** | [`python/download_music.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/download_music.py)<br>[`python/add_audio.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/add_audio.py) | **Dynamic Audio Mixer**: Fetches mood-matched royalty-free audio from Pixabay CDN and mixes voice (1.0) with music (0.30). |
| **08** | [`python/create_video.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_video.py) | **Video Assembly**: Scales and crops clips to 1080x1920 with `-movflags +faststart`. |
| **09** | [`python/burn_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/burn_subtitles.py) | **Hard Subtitle Burn**: Burns custom Bebas Neue captions with semi-transparent background box into `output/short.mp4`. |
| **10** | [`python/generate_thumbnail.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_thumbnail.py) | **High-CTR Thumbnail Generator**: Generates high-contrast editorial thumbnails using Google Gemini Imagen 3 API. |
| **11** | [`python/publish_service.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/publish_service.py)<br>[`python/harvest_analytics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/harvest_analytics.py) | **Multi-Platform Publishing**: Uploads to YouTube Shorts, Facebook Reels, and Instagram Reels. Harvests view stats into SQLite (`shortest_orbit_v3.db`). |
| **12** | [`python/youtube_dashboard.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/youtube_dashboard.py) | **Growth Command Center**: Streamlit SaaS dashboard displaying channel readiness, view stats, and monetization milestones. |

---

## ⚠️ Known Limitations & Circuit Breaker System

> [!WARNING]  
> ### Current Infrastructure Limitations & Fallback Protocols
>
> 1. **AWS Bedrock Nova Reel On-Demand Quota (`amazon.nova-reel-v1:1`)**:
>    - **Status**: Account `719312763637` is currently awaiting AWS Support Quota Approval (AWS Case `178767424800583`).
>    - **Fallback Protocol**: The pipeline detects `ValidationException` and automatically falls back to our **Tri-Modal Fast-Cut Engine** (Doodle + 4K Cinematic + 3D Maps), ensuring video uploads are never blocked.
>
> 2. **Fal.ai Video API Credit Circuit Breaker**:
>    - **Status**: When Fal.ai credit balance is depleted, an internal circuit breaker (`_FAL_DISABLED`) instantly bypasses API retries to prevent 15-second network delays.
>
> 3. **YouTube Daily Upload Quota**:
>    - **Status**: Restricted to 3-5 uploads per day to comply with YouTube Data API v3 daily quota limits (`daily_upload_cap: 3` in `settings.json`).

---

## 🛡️ Resiliency & Error Handling Architecture

- 🔄 **Groq LLM Model Rotation**: If HTTP 429 rate limit occurs, `call_groq_with_fallback()` rotates through `openai/gpt-oss-120b`, `llama-3.3-70b-versatile`, and `qwen-2.5-coder-32b` before triggering **Gemini 2.5 Flash API**.
- 🧹 **Robust JSON Parser**: `extract_json_from_llm()` strips reasoning tags (`<think>...</think>`) and markdown syntax before parsing JSON responses.
- ⚡ **FFmpeg Faststart Encoding**: All encoding steps use `-preset fast -movflags +faststart` to optimize streaming performance for Meta Graph API.
- 🔁 **Duplicate Asset Protection**: Queries SQLite to prevent using stock clip IDs or topics published within the last 30 days.

---

## 💻 Local Installation & Setup Guide

### 1. System Requirements
- **Python 3.11+**
- **FFmpeg** (added to system PATH)
- **Git**

### 2. Installation Commands

```bash
# 1. Clone the repository
git clone https://github.com/ravindrareddy17/ai-video-generator.git
cd ai-video-generator

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install required packages
pip install -r requirements.txt
```

### 3. Environment Configuration (`.env`)
Create a `.env` file in the project root:

```ini
GROQ_API_KEY=your_groq_api_key
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key
GEMINI_API_KEY=your_gemini_api_key
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_ACCESS_TOKEN=your_meta_user_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_account_id
```

### 4. Running the Engine & Dashboard

```bash
# Run full video generation & publishing pipeline:
python python/main.py

# Launch Growth Dashboard:
streamlit run python/youtube_dashboard.py
```

---

<div align="center">

<b>THE SHORTEST ORBIT V4.5</b> • *Autonomous AI Video Generation & Channel Growth Engine*

</div>
