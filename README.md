# 🚀 THE SHORTEST ORBIT — V4 Autonomous Short Video Engine & YouTube Growth Command Center

> ⚠️ **PROJECT STATUS: UNDER ACTIVE DEVELOPMENT**  
> *This repository is currently under rapid iteration and active development. Systems, database schemas, and AI models are continuously updated for maximum performance, accuracy, and viewer retention.*

---

## 📌 Project Overview

**THE SHORTEST ORBIT V4** is a 100% automated, self-learning AI video generator and growth command center designed specifically for short-form video channels (YouTube Shorts, Facebook Reels, Instagram Reels).

It researches viral space & tech news, fact-verifies claims against authority sources, crafts high-retention scripts, synthesizes voiceovers, retrieves topic-matched 4K UHD stock video clips, burns custom subtitles, renders vertical Shorts, publishes across platforms, and harvests analytics to continually self-optimize future video topics.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE SHORTEST ORBIT                                     │
│     "Understand the biggest battles, discoveries and technologies shaping space and   │
│                              the future — in seconds."                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 End-to-End Pipeline Implementation (Steps 1 – 12)

The engine executes an automated 12-step closed-loop production workflow:

```
[1. FIND VIRAL TOPICS] ──► [2. VERIFY FACTS & SCRIPT] ──► [3. VOICE SYNTHESIS]
                                                                  │
[6. DOWNLOAD 4K CLIPS] ◄── [5. VISUAL QUERIES] ◄── [4. SUBTITLES] ◄┘
         │
         ▼
[7. MUSIC & MIXING] ────► [8. STITCH VIDEO] ────► [9. BURN SUBTITLES]
                                                              │
[12. DASHBOARD] ◄────── [11. PUBLISH & HARVEST] ◄── [10. THUMBNAIL]
```

### 🔹 Step 1: Viral Topic Discovery ([`python/find_viral_topics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/find_viral_topics.py))
- Scrapes trending space & technology topics from Reddit (r/space, r/spacex, r/science, r/technology), Google Trends API, and NASA/ESA RSS feeds.
- Calculates an **Opportunity Score** ($0.0 – 10.0$) using V4 historical performance memory to prioritize winning pillars (*e.g., SpaceX Starship, Lunar Mining, AI Satellite Warfare*).

### 🔹 Step 2: Fact Verification & Script Generation ([`python/generate_content.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_content.py) & [`python/verify_facts.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/verify_facts.py))
- Evaluates topic claims against 7 authority tiers (NASA, arXiv, Nature, Space.com).
- Enforces a **Hard Accuracy Veto Gate**: if `accuracy_score < 7.0` or key claims are unverified, the topic is automatically vetoed.
- Generates a 50–60 second high-retention narration script following proven hook patterns (*Sentence 1 high-stakes conflict*).

### 🔹 Step 3: Voice Synthesis & Word-Level Timings ([`python/generate_voice.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_voice.py))
- Uses EdgeTTS neural voice (`en-US-AndrewMultilingualNeural`) to render broadcast-quality voice audio (`audio/voice.mp3`).
- Generates precise word-level and sentence-level timing boundaries (`audio/word_timings.json`).

### 🔹 Step 4: Subtitle Generation ([`python/create_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_subtitles.py))
- Converts timing boundaries into clean sentence-level SRT subtitle files (`captions/voice.srt`).
- Applies line-wrapping algorithms (max 2 lines per subtitle card, max 42 characters per line) to prevent UI truncation.

### 🔹 Step 5: Topic-Aware Visual Query Extraction ([`python/generate_search_queries.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_search_queries.py))
- Fuses overall topic context (*e.g., China's Autonomous Lunar Mining*) with physical sentence actions.
- Calls LLM to generate 3 multi-stage search queries per scene (*e.g., `"china lunar mining robot"`, `"future lunar research station"`*) to ensure 100% visual relevance.

### 🔹 Step 6: Dual-Source 4K/HD Video Asset Downloader ([`python/download_videos.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/download_videos.py))
- Simultaneously searches **Pexels API** and **Pixabay API** for stock video clips.
- Filters and ranks candidates based on vertical aspect ratio ($h > w$) and 4K UHD resolution ($2160\times3840\text{px}$ or $4096\text{px}$).
- Tracks previously used asset IDs in SQLite database to prevent repetitive visuals across consecutive videos.

### 🔹 Step 7: Mood-Based Background Music & Audio Mixing ([`python/download_music.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/download_music.py) & [`python/add_audio.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/add_audio.py))
- Analyzes topic mood using LLM (*beats, acoustic, ambient, upbeat, inspiring, cinematic*) and fetches matching Pixabay royalty-free music (`assets/music/background.mp3`).
- Mixes voice narration (1.0 volume) and background music (0.4 volume) using FFmpeg (`temp/video_audio.mp4`).

### 🔹 Step 8: Video Assembly & Stitching ([`python/create_video.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_video.py))
- Crops and scales source clips to $1080\times1920$ portrait format.
- Applies seamless video looping (`-stream_loop -1`) to shorter clips to guarantee zero frozen frames.
- Uses `-preset fast -threads 4` encoding parameters to handle 4K source footage smoothly.

### 🔹 Step 9: Subtitle Burning ([`python/burn_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/burn_subtitles.py))
- Hard-codes custom-styled subtitles (*Bebas Neue / Cinzel font, white text with semi-transparent dark box background*) into the final vertical Short (`output/short.mp4`).

### 🔹 Step 10: Eye-Catching Thumbnail Generation ([`python/generate_thumbnail.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_thumbnail.py))
- Extracts a high-res video frame at 30% duration of `output/short.mp4`.
- Applies dark gradient contrast overlays and bold editorial typography to create `output/thumbnail.png` ($1280\times720$).

### 🔹 Step 11: Multi-Platform Publishing & Analytics Harvest ([`python/publish_service.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/publish_service.py) & [`python/harvest_analytics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/harvest_analytics.py))
- Publishes videos to YouTube Shorts, Facebook Reels, and Instagram Reels via Graph APIs.
- Periodically snapshots performance metrics (Views, Watch Time, Subscribers, APV, Viewer Choice) into SQLite database (`data/analytics.db`).

### 🔹 Step 12: YouTube Growth Command Center ([`python/youtube_dashboard.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/youtube_dashboard.py))
- Production-ready local Streamlit dashboard featuring a clean White/Purple Editorial SaaS aesthetic (`#FFFFFF` bg, `#111827` black text, `#4F46E5` indigo accent, `1280px` controlled layout).
- Strictly separates Real YouTube Performance metrics from V4 Internal Diagnostics.

---

## 🛡️ Error Handling, Resiliency & Optimization Mechanics

| Issue / Failure Mode | Automated Resiliency Solution | Implementation File |
| :--- | :--- | :--- |
| **Groq API Rate Limit (HTTP 429)** | `call_groq_with_fallback()` automatically rotates through Groq models (`qwen3.6-27b` $\rightarrow$ `compound-mini` $\rightarrow$ `gpt-oss-120b`). If all rate limit out, it seamlessly falls back to **Gemini 2.5 Flash REST API**. | [`utils/config.py`](file:///E:/ai_gen/AI-VIDEO-V2/utils/config.py#L91) |
| **LLM Reasoning & Markdown Pollution** | `extract_json_from_llm()` strips `<think>...</think>` tags and ```json markdown blocks, parsing nested JSON safely. | [`utils/helpers.py`](file:///E:/ai_gen/AI-VIDEO-V2/utils/helpers.py#L46) |
| **FFmpeg 4K UHD Memory Overflow (`malloc` error)** | Scaled down preset from `medium` to `fast` and set strict thread limits (`-threads 4`) to prevent x264 memory allocation failures on 4K clips. | [`python/create_video.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_video.py#L60) |
| **Duplicate Video Clips Across Uploads** | Queries SQLite database for used Pexels/Pixabay asset IDs in the last 15 videos and excludes them from candidate pools. | [`python/download_videos.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/download_videos.py#L54) |
| **Streamlit Module Import Caching** | Explicit `importlib.reload()` on all dashboard sub-modules to prevent hot-reload `ImportError` exceptions. | [`python/youtube_dashboard.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/youtube_dashboard.py#L29) |

---

## 📂 Codebase File Structure Map

```text
E:/ai_gen/AI-VIDEO-V2/
├── config/
│   └── settings.json              # Global pipeline configurations (Voices, Resolutions, Schedules)
├── data/
│   ├── analytics.db               # SQLite database (Videos, Analytics Snapshots, V4 Memory)
│   ├── content.json               # Generated topic, script, and fact verification payload
│   └── search_queries.json        # Scene-by-scene visual search query definitions
├── downloads/
│   └── videos/                    # Downloaded 4K/HD stock video clips (scene_1.mp4, etc.)
├── output/
│   ├── short.mp4                  # Final rendered 1080x1920 subtitled Short video
│   └── thumbnail.png              # High-contrast 1280x720 thumbnail image
├── python/
│   ├── main.py                    # Master orchestrator for pipeline execution
│   ├── find_viral_topics.py       # Step 1: Trending topic discovery
│   ├── generate_content.py        # Step 2: Script generation
│   ├── verify_facts.py            # Step 2.5: Fact verification veto gate
│   ├── generate_voice.py          # Step 3: EdgeTTS audio synthesis
│   ├── create_subtitles.py        # Step 4: SRT subtitle timing generator
│   ├── generate_search_queries.py # Step 5: Topic-aware visual query extractor
│   ├── download_videos.py         # Step 6: Dual-source Pexels/Pixabay video downloader
│   ├── download_music.py          # Step 7.5: Mood-based background music retriever
│   ├── add_audio.py               # Step 8: Voice + music audio mixing
│   ├── create_video.py            # Step 7: Video clip scaling, cropping & stitching
│   ├── burn_subtitles.py          # Step 9: FFmpeg hard-subtitles burner
│   ├── generate_thumbnail.py      # Step 10: Video frame extraction & thumbnail generator
│   ├── publish_service.py         # Step 11: Multi-platform publishing service
│   ├── harvest_analytics.py       # Step 11.5: Real YouTube analytics harvester
│   └── youtube_dashboard.py       # Step 12: YouTube Growth Command Center Dashboard
├── utils/
│   ├── config.py                  # API key manager & call_groq_with_fallback() handler
│   ├── ffmpeg.py                  # FFmpeg execution wrappers & filter strings
│   ├── helpers.py                 # File I/O & extract_json_from_llm()
│   ├── logger.py                  # Standardized logging formatter
│   └── database.py                # SQLite connection pool & table migration engine
└── README.md
```

---

## 💻 Local Installation & Setup Guide

### 1. Prerequisites
- **Python 3.11+**
- **FFmpeg** installed and added to system `PATH`
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/ravindrareddy17/ai-video-generator.git
cd ai-video-generator
```

### 3. Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables (`.env`)
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 6. Run Full Pipeline Locally
```bash
python python/main.py
```

### 7. Launch YouTube Growth Command Center Dashboard
```bash
streamlit run python/youtube_dashboard.py
```
> Open browser at: **`http://localhost:8501`**

---

> ⚠️ **REMINDEER**: *This repository is under active development. Features, schemas, and AI models may change as new optimizations are committed.*
