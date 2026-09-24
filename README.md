<div align="center">

# 🚀 THE SHORTEST ORBIT
### *Autonomous V4.5+ Closed-Loop AI Video Production & Growth Engine*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Cloud_CI%2FCD-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-4K_UHD_Faststart-0078D4?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org)
[![Groq LPU](https://img.shields.io/badge/Groq-Ultra_Fast_LPU-F55036?style=for-the-badge&logo=fastapi&logoColor=white)](#-multi-tier-llm-resiliency)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](#-multi-tier-llm-resiliency)
[![AWS Bedrock](https://img.shields.io/badge/AWS_Bedrock-Nova_Lite-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](#-multi-tier-llm-resiliency)
[![YouTube Data API](https://img.shields.io/badge/YouTube_API-v3_Staged_Release-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](#-staged-release-unlisted-buffer-system)
[![Meta Graph API](https://img.shields.io/badge/Meta_Graph_API-v25.0_Reels-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](https://developers.facebook.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+_Growth_SaaS-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)

<p align="center">
  <b>"Understand the biggest battles, discoveries, and technologies shaping space, Earth, and the future — in seconds."</b>
</p>

---

</div>

> [!NOTE]  
> ### 🌐 What is The Shortest Orbit?
> **The Shortest Orbit** is an enterprise-grade, 100% autonomous, closed-loop AI video generation and multi-platform publishing engine. Running hands-free in the cloud on **GitHub Actions runners**, it monitors 15 global news & trend feeds, verifies facts against scientific authorities, synthesizes neural voiceovers, curates ultra-realistic 4K vertical cinematic footage, synchronizes kinetic karaoke subtitles, mixes ducked audio, and orchestrates multi-platform publishing across **YouTube Shorts**, **Facebook Reels**, and **Instagram Reels** on a strict 3-post daily cadence.

---

## 📋 TABLE OF CONTENTS

1. [🌟 Architectural Breakthroughs & Upgrades](#-architectural-breakthroughs--upgrades)
2. [🏗️ End-to-End Technology Stack Reference](#%EF%B8%8F-end-to-end-technology-stack-reference)
3. [🔄 System Architecture & State Machine](#-system-architecture--state-machine)
4. [🎬 Style 2: Ultra-Realistic 4K Cinematic Engine](#-style-2-ultra-realistic-4k-cinematic-engine)
5. [⏳ Staged Release (Unlisted Buffer) System](#-staged-release-unlisted-buffer-system)
6. [📈 32-Second Algorithmic Retention Formula](#-32-second-algorithmic-retention-formula)
7. [🛠️ End-to-End 12-Step Implementation Breakdown](#%EF%B8%8F-end-to-end-12-step-implementation-breakdown)
8. [⏰ Global Posting Schedule & Prime-Time Windows](#-global-posting-schedule--prime-time-windows)
9. [🛡️ Resiliency, Rate Limits & Circuit Breakers](#%EF%B8%8F-resiliency-rate-limits--circuit-breakers)
10. [🗄️ Database Architecture & Schemas](#%EF%B8%8F-database-architecture--schemas)
11. [📁 Complete Project Directory Tree](#-complete-project-directory-tree)
12. [⚙️ Environment Variables & Configuration](#%EF%B8%8F-environment-variables--configuration)
13. [💻 Installation & Deployment Guide](#-installation--deployment-guide)

---

## 🌟 ARCHITECTURAL BREAKTHROUGHS & UPGRADES

* **🎬 Style 2 — 4K Ultra-Realistic Cinematic Footage**: Prioritizes genuine, high-contrast, real-world vertical footage over abstract doodling. The prompt engine strictly decomposes abstract ideas into tangible, camera-ready physical objects (e.g., *"liquid nitrogen thruster firing in vacuum"*, *"deep sea submersible lights illuminating hydrothermal vent"*).
* **⏳ Automated Staged Release Buffer (`unlisted` $\rightarrow$ `public`)**: Eliminates the common YouTube Shorts "0-views / low-quality debut" penalty. Videos upload immediately as `unlisted` to give YouTube's transcoding pipelines 2–3 hours to render optimal 1080p VP9/AV1 codecs. The next scheduled pipeline automatically flips the buffer video to `public` and pins a discussion-starter comment.
* **🛡️ 3-Tier LLM Resiliency Cascade**: Zero pipeline downtime. If Groq LPU experiences rate limits (HTTP 429), the system automatically rolls over to **Google Gemini 2.5 Flash**, and subsequently to **AWS Bedrock Nova Lite** (`amazon.nova-lite-v1:0`).
* **🛑 Strict 20-Video Multi-Keyword Deduplication**: Compares incoming trending topic candidates against the last 20 published titles using an $N$-gram keyword intersection filter. Any candidate sharing $\ge 2$ core nouns is rejected to eliminate repetitive content loops.
* **🎵 Dynamic Audio Ducking (-14 LUFS & 18% Music)**: Automatically balances spoken neural narration (normalized to -14 LUFS broadcast standard) against Pixabay royalty-free cinematic music ducked to 18% volume, preventing ear fatigue while maintaining emotional drive.
* **⚡ Meta Faststart Resumable Engine (`-movflags +faststart`)**: Overcomes Meta Graph API byte-0 container rejections on `rupload.facebook.com` by strictly injecting MOOV atoms at the beginning of MP4 files, guaranteeing 100% upload reliability for Instagram Reels and Facebook Reels.

---

## 🏗️ END-TO-END TECHNOLOGY STACK REFERENCE

The table below details every technology integrated into the pipeline, what it is, why it was chosen, and its role in production:

| Layer | Technology | Category | What It Is | Why We Chose It (Advantages) | Fallback / Redundancy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Trend Discovery** | **Reddit API (PRAW)** | Ingestion | Scrapes viral discussions from *r/space*, *r/science*, *r/Futurology*, *r/natureismetal*. | Unfiltered public sentiment, high upvote velocity, early signal detection before mainstream news. | RSS Feeds / Google Trends |
| **Trend Discovery** | **Feedparser** | Ingestion | RSS/Atom feed parser for NASA, ESA, MIT Tech Review, Nature, SpaceX. | Authoritative scientific breakthroughs, 100% factual accuracy, structured timestamps. | Direct Web Scraper |
| **Trend Discovery** | **PyTrends / Google Trends** | Ingestion | Real-time search trend scraper for US and global regions. | Validates actual search interest and audience demand volume. | Wikipedia Trending API |
| **Intelligence** | **Groq LPU (`gpt-oss-120b`, `llama-3.3-70b`)** | Reasoning LLM | Ultra-low-latency Language Processing Unit hardware. | Generates scripts, hooks, and beat splits in **<600ms**, enabling instant pipeline iterations. | Gemini 2.5 Flash |
| **Intelligence** | **Google Gemini 2.5 Flash** | Reasoning LLM | Google's multimodal large language model API. | Generates high-CTR thumbnail prompts, fact verification checks, and acts as Primary LLM fallback. | AWS Bedrock Nova |
| **Intelligence** | **AWS Bedrock (`amazon.nova-lite-v1:0`)** | Reasoning LLM | Amazon's enterprise cloud AI model endpoint. | Dedicated enterprise quota with zero rate-limit collisions, serving as final LLM tier. | Local heuristics |
| **Voice Synthesis** | **Microsoft EdgeTTS** | Audio TTS | Deep learning neural speech synthesis (`en-US-AndrewMultilingualNeural`). | Broadcast-grade natural inflection, free unlimited tier, precise millisecond word-level timing offsets. | gTTS / Local TTS |
| **Visual Footage** | **Pexels Video API** | Visual Assets | Curated collection of high-resolution 4K stock video clips. | High visual aesthetics, vertical 9:16 portrait native filtering, generous free rate limits. | Pixabay Video API |
| **Visual Footage** | **Pixabay Video API** | Visual Assets | Royalty-free stock video library. | Secondary stock video pool ensuring 100% clip match rate on obscure scientific queries. | Fal.ai AI Video / Whiteboard |
| **Visual Footage** | **Fal.ai (Minimax Hailuo / Kling 1.5)** | Generative AI | Cloud video generation endpoint for custom speculative visuals. | Produces hyper-realistic science/space footage when physical footage does not exist. | Pexels / Pixabay Fallback |
| **Audio & Music** | **Pixabay Audio CDN** | Sound Engine | Curated direct CDN links to high-energy royalty-free background tracks. | Mood-matched tracks (`cinematic`, `ambient`, `beats`, `upbeat`) that avoid copyright claims. | Local MP3 Library |
| **Video Engine** | **FFmpeg 7.x** | Compositing | Industry-standard audio/video processing and multiplexing suite. | Frame-accurate stitching, dynamic audio ducking, sub-pixel subtitle burning, `-movflags +faststart`. | MoviePy |
| **Subtitles** | **FFmpeg `libass`** | Typography | High-performance subtitle renderer for SSA/ASS and SRT. | Renders custom fonts (Bebas Neue / Cinzel), semi-transparent opaque backing boxes, gold karaoke highlights. | OpenCV Text Overlay |
| **Thumbnail** | **Pillow (PIL)** | Image Engine | Python Imaging Library for programmatic image manipulation. | Extracts video frames at 30% duration, applies dark gradients, draws high-contrast stroke typography. | Gemini Imagen 3 |
| **Distribution** | **YouTube Data API v3** | Cloud API | Google OAuth2 YouTube upload and playlist management endpoint. | Direct channel publishing, automated metadata tagging, privacy switching, pinned comments. | Manual Upload |
| **Distribution** | **Meta Graph API v25.0** | Cloud API | Facebook & Instagram Pages Graph API. | Chunked resumable container uploads to `rupload.facebook.com`, native Reels distribution. | Third-party aggregators |
| **State Persistence**| **SQLite 3** | Database | Embedded relational database (`shortest_orbit_v3.db`). | Zero-configuration, zero-latency local ACID storage for video history, analytics, and upload statuses. | PostgreSQL / JSON logs |
| **Automation** | **GitHub Actions** | CI/CD Runner | Automated cloud Linux execution environment (`ubuntu-latest`). | Runs 3x daily cron jobs, syncs SQLite database commits back to GitHub, 100% serverless. | Local Cron / VPS |
| **Analytics SaaS** | **Streamlit** | UI / Dashboard | Python data application framework (`youtube_dashboard.py`). | Real-time channel analytics, retention charts, monetization milestone tracking, visual audit logs. | Grafana |

---

## 🔄 SYSTEM ARCHITECTURE & STATE MACHINE

```text
                               THE SHORTEST ORBIT CLOSED-LOOP ENGINE
                               
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                              1. TREND INGESTION & FILTER                         │
  │   Reddit (r/space, r/science) ──► RSS (NASA, ESA, MIT) ──► Google Trends (US)    │
  │                                       │                                         │
  │               SQLite 20-Video Keyword Deduplication & Overlap Check              │
  └───────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                         2. INTELLIGENCE & SCRIPT ENGINE                          │
  │   Fact-Checking (7 Sources) ──► 32s Script Creation ──► Curiosity Hook (>= 8.5) │
  │   [Groq LPU (gpt-oss-120b) ──► Fallback: Gemini 2.5 Flash ──► Fallback: Bedrock]│
  └───────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                         3. AUDIO & TIMING SYNTHESIS                             │
  │   EdgeTTS (en-US-Andrew) ──► Word-Level JSON Timings ──► Karaoke SRT Generator   │
  └───────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                         4. VISUAL BEAT & FOOTAGE ENGINE                         │
  │   Split Script into 1.8s–2.5s Beats ──► Decompose to Physical Tangible Queries  │
  │   Download 4K Ultra-Realistic Footage (Pexels / Pixabay / Fal.ai Gen)           │
  └───────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                     5. FFmpeg COMPOSITING & POLISHING                           │
  │   Stitch 1080x1920 9:16 Video ──► Audio Ducking (18% Music) ──► Burn Subtitles │
  │   Generate High-CTR Thumbnail ──► Quality Gatekeeper Check (Score >= 8.5)        │
  └───────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                    6. STAGED RELEASE & MULTI-PLATFORM SYNC                      │
  │                                                                                 │
  │   [Slot N Step A]: Release PREVIOUS unlisted video to PUBLIC + Pin Comment      │
  │   [Slot N Step B]: Upload CURRENT video to YouTube as UNLISTED (Pre-warm 1080p) │
  │   [Slot N Step C]: Upload CURRENT video to Facebook Reels & Instagram Reels     │
  └───────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                    7. ANALYTICS HARVEST & GROWTH DASHBOARD                      │
  │   Harvest Views, Likes, Retention ──► Sync SQLite ──► Push Commit to GitHub     │
  │   Visualize Progress via Streamlit Command Center (Monetization Tracker)       │
  └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎬 STYLE 2: ULTRA-REALISTIC 4K CINEMATIC ENGINE

By default, the engine runs in **`"visual_mode": "cinematic"`** (`config/settings.json`), completely transforming the visual identity of the channel from abstract sketches to high-production real-world documentary footage.

### Physical Object Decomposition Logic
Instead of querying vague abstract terms like *"quantum supremacy"* or *"AI takeover"*, [`python/generate_search_queries.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_search_queries.py) instructs the LLM to identify concrete physical nouns:

```text
❌ Abstract Query (Weak): "artificial intelligence thinking about space"
✅ Physical Query (Cinematic): "glowing supercomputer server rack data center cables blinking"

❌ Abstract Query (Weak): "asteroid mining economics"
✅ Physical Query (Cinematic): "craggy rotating asteroid close up deep space stars sunlight"
```

### Visual Fallback Chain
```text
1. Pexels 4K UHD Video (Portrait 9:16)
   └── If no match: Pixabay High-Bitrate Video (Portrait 9:16)
       └── If no match: Fal.ai Gen / Procedural Space Motion Graphic
```

---

## ⏳ STAGED RELEASE (UNLISTED BUFFER) SYSTEM

### The Problem: YouTube's Low-Resolution Transcoding Delay
When an MP4 file is uploaded directly as **Public**, YouTube's servers immediately serve low-bitrate **360p AVC1** stream files to the first wave of viewers. High-efficiency **1080p60 VP9 / AV1** transcode profiles take **45 to 120 minutes** to compute. Viewers who see a grainy 360p video swipe away within the first 2 seconds, destroying the video's initial Retention Score and causing the algorithm to freeze recommendations.

### The Solution: Automated Unlisted Pre-Warming
The Shortest Orbit solves this with a 2-stage unlisted buffer:

```text
SLOT 1 (e.g. 5:00 PM IST):
├── 1. Release previous Video #1 from UNLISTED ──► PUBLIC.
│      - YouTube has already generated 1080p60 VP9/AV1 codecs!
│      - Viewers immediately receive crystal-clear 1080p quality.
│      - System automatically writes and pins an engaging discussion comment.
└── 2. Generate Video #2 and upload to YouTube as UNLISTED.
       - Video #2 sits quietly in the unlisted buffer for 4-5 hours.
       - YouTube's servers finish all HD transcoding pipelines.

SLOT 2 (e.g. 9:30 PM IST):
├── 1. Release Video #2 from UNLISTED ──► PUBLIC (+ pinned comment).
└── 2. Generate Video #3 and upload as UNLISTED.
```

The database status transitions smoothly:
$$\text{created} \longrightarrow \text{uploaded\_unlisted} \longrightarrow \text{published\_public}$$

---

## 📈 32-SECOND ALGORITHMIC RETENTION FORMULA

Every parameter of the video generation pipeline is scientifically tuned for YouTube Shorts and Instagram Reels retention algorithms:

| Factor | Technical Specification | Strategic Rationale |
| :--- | :--- | :--- |
| **Duration** | **32 seconds** (~75–85 spoken words) | Maximizes $>100\%$ completion rate; short enough for full rewatches. |
| **Cut Velocity** | **1.8s – 2.5s per scene cut** | Resets user attention 14–18 times per video, defeating swipe-away instincts. |
| **Hook Score** | **Curiosity-Gap $\ge 8.5/10$** | First 3 seconds trigger psychological curiosity gaps without clickbait penalties. |
| **Voiceover** | **EdgeTTS `en-US-AndrewMultilingualNeural` (+5% rate)** | Punchy, authoritative, documentary-style delivery without robotic cadence. |
| **Subtitles** | **Bebas Neue / Cinzel + Gold Highlight (`#FFD60A`)** | Centered, high-contrast, black backing box (`BorderStyle=3`) keeps eyes glued to center frame. |
| **Audio Ducking** | **Narration: 1.0 (-14 LUFS) \| Music: 0.18** | Music provides emotional rhythm without masking speech clarity. |
| **Comment Bait** | **Opinion-Splitting Question + Auto-Pinned Comment** | Provokes immediate comment discussions, driving algorithmic velocity. |

---

## 🛠️ END-TO-END 12-STEP IMPLEMENTATION BREAKDOWN

| Step | Script File | Core Technical Function |
| :---: | :--- | :--- |
| **01** | [`python/find_viral_topics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/find_viral_topics.py) | **15-Source Trend Scouting & Deduplication**: Scrapes Reddit, NASA/ESA RSS, and Google Trends. Evaluates topics with Opportunity Scoring formula. Enforces 20-video keyword deduplication to eliminate topic repetition. |
| **02** | [`python/generate_content.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_content.py)<br>[`python/verify_facts.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/verify_facts.py) | **Scientific Fact-Checking & Script Creation**: Cross-checks claims against 7 authorities. Evaluates 3 hook variations (*Curiosity, Shock, Debate*). Emits a strict 32-second script ending in a debate prompt. |
| **03** | [`python/generate_voice.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_voice.py) | **Neural Speech & Timestamp Synthesis**: Uses Microsoft EdgeTTS to generate studio-grade voiceover audio and writes word-level millisecond timestamps to `data/word_timings.json`. |
| **04** | [`python/create_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_subtitles.py) | **Karaoke Subtitle Generation**: Groups narration words into 2–3 word visual bursts with HTML gold highlighting (`#FFD60A`) on impact words. Saves `temp/subtitles.srt`. |
| **05** | [`python/generate_search_queries.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_search_queries.py) | **1.8s Fast Beat Decomposition**: Analyzes sentence structure to partition narration into 14–18 visual beats. Derives concrete physical stock footage search queries. |
| **06** | [`python/multi_style_generator.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/multi_style_generator.py)<br>[`python/download_videos.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/download_videos.py) | **Style 2 4K Asset Retrieval**: Queries Pexels 4K API with portrait orientation filters. Falls back gracefully to Pixabay Video API or procedural motion graphics. |
| **07** | [`python/create_video.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_video.py) | **FFmpeg Timeline Assembly**: Scales, crops, and stitches clips into a portrait $1080\times1920$ timeline. Enforces `-movflags +faststart` for instant streaming. |
| **07.5** | [`python/download_music.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/download_music.py) | **Mood Audio Acquisition**: Determines emotional tone (`cinematic`, `ambient`, `beats`) and downloads royalty-free background MP3 from Pixabay CDN to `assets/music/background.mp3`. |
| **08** | [`python/add_audio.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/add_audio.py) | **Precision Audio Ducking**: Mixes narration voiceover at full volume ($1.0$) with background music ducked to $0.18$, applying EBU R128 loudness normalization. |
| **09** | [`python/burn_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/burn_subtitles.py) | **Kinetic Subtitle Burning**: Invokes FFmpeg `subtitles` filter with custom font paths, semi-transparent black backing boxes, and strict vertical positioning into `output/short.mp4`. |
| **10** | [`python/generate_thumbnail.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_thumbnail.py) | **Editorial Thumbnail Generation**: Extracts video frame at 30% duration, applies a dark gradient, and draws bold two-tone typography stroke text. |
| **10.5** | [`python/quality_checker.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/quality_checker.py) | **Quality Gatekeeper**: Automated inspection verifying video resolution ($1080\times1920$), frame rate (30 FPS), audio presence, and engagement criteria. Rejects scores $<8.5$. |
| **11** | [`python/upload_youtube.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/upload_youtube.py)<br>[`python/upload_facebook.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/upload_facebook.py)<br>[`python/upload_instagram.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/upload_instagram.py) | **Multi-Platform Publishing & Staged Release**: Releases previously unlisted YouTube video to public, pins discussion comment, uploads new video as unlisted, and publishes to Facebook & Instagram Reels. |
| **11.5** | [`python/harvest_analytics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/harvest_analytics.py) | **Analytics Harvester**: Collects real-time YouTube views, likes, comments, and subscriber counts, storing them in SQLite to power the feedback loop. |
| **12** | [`python/youtube_dashboard.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/youtube_dashboard.py) | **Growth Command Center**: Streamlit SaaS dashboard displaying channel readiness, retention curves, view pace, and monetization progress. |

---

## ⏰ GLOBAL POSTING SCHEDULE & PRIME-TIME WINDOWS

Configured in [`.github/workflows/main.yml`](file:///.github/workflows/main.yml) to capture peak active commuting and evening hours across the United States, Europe, and India:

```yaml
  schedule:
    - cron: "30 11 * * *"  # Slot 1: 5:00 PM IST  / 7:30 AM EST  / 12:30 PM BST (US Morning Commute Peak)
    - cron: "0 16 * * *"   # Slot 2: 9:30 PM IST  / 12:00 PM EST / 5:00 PM BST  (US Lunch & EU Evening Peak)
    - cron: "30 22 * * *"  # Slot 3: 4:00 AM IST  / 6:30 PM EST  / 11:30 PM BST (US Evening Prime-Time Peak)
```

---

## 🛡️ RESILIENCY, RATE LIMITS & CIRCUIT BREAKERS

### 1. Multi-Tier LLM Cascading Fallback
[`utils/config.py`](file:///E:/ai_gen/AI-VIDEO-V2/utils/config.py) wraps all intelligence calls in a fault-tolerant try-except cascade:
1. **Tier 1 — Groq LPU**: `openai/gpt-oss-120b` $\rightarrow$ `llama-3.3-70b-versatile`.
2. **Tier 2 — Google Gemini**: `gemini-2.5-flash` API if Groq returns HTTP 429 or rate exhaustion.
3. **Tier 3 — AWS Bedrock**: `amazon.nova-lite-v1:0` if both external APIs are unreachable.

### 2. Meta Graph API Resumable Container Faststart
Meta Reels ingestion (`rupload.facebook.com`) strictly requires the MP4 MOOV atom at byte 0. All FFmpeg encoding stages enforce:
```bash
-movflags +faststart -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.2
```

### 3. Fal.ai Circuit Breaker
If cloud generative video balance reaches zero, the `_FAL_DISABLED` circuit breaker immediately switches scene synthesis to Pexels 4K stock clips, preventing 15-second network timeout delays.

---

## 🗄️ DATABASE ARCHITECTURE & SCHEMAS

The SQLite database ([`data/shortest_orbit_v3.db`](file:///E:/ai_gen/AI-VIDEO-V2/data/shortest_orbit_v3.db)) tracks state and analytics across 7 core relational tables:

```sql
-- 1. Published and pending video records
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    topic_id INTEGER,
    script TEXT,
    youtube_id TEXT,
    facebook_id TEXT,
    facebook_url TEXT,
    instagram_id TEXT,
    instagram_url TEXT,
    status TEXT DEFAULT 'pending',  -- 'pending', 'uploaded_unlisted', 'published_public'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_at TIMESTAMP
);

-- 2. Discovered topics with quality scores
CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    source TEXT,
    trend_score REAL,
    engagement_potential REAL,
    retention_potential REAL,
    status TEXT DEFAULT 'discovered',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Curiosity-gap hook evaluations
CREATE TABLE hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER,
    text TEXT NOT NULL,
    score REAL,
    selected INTEGER DEFAULT 0,
    FOREIGN KEY(video_id) REFERENCES videos(id)
);

-- 4. Cross-platform daily analytics performance
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER,
    date DATE,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    subscribers_gained INTEGER DEFAULT 0,
    fb_views INTEGER DEFAULT 0,
    ig_views INTEGER DEFAULT 0,
    FOREIGN KEY(video_id) REFERENCES videos(id)
);

-- 5. YouTube partner monetization snapshots
CREATE TABLE monetization_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE,
    subscribers INTEGER,
    shorts_views INTEGER,
    watch_hours REAL,
    uploads_90_days INTEGER,
    progress_percentage REAL,
    readiness_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📁 COMPLETE PROJECT DIRECTORY TREE

```text
AI-VIDEO-V2/
├── .github/
│   └── workflows/
│       └── main.yml                   # Cloud GitHub Actions workflow (3x daily schedule)
├── assets/
│   ├── fonts/                         # Custom typography (Bebas Neue, Cinzel, Montserrat)
│   └── music/                         # Royalty-free mood background audio
├── config/
│   └── settings.json                  # System configuration (Style 2, unlisted buffer, audio)
├── data/
│   ├── shortest_orbit_v3.db           # Central SQLite database
│   ├── content.json                   # Generated script, hook, and topic
│   ├── metadata.json                  # YouTube & Meta SEO metadata & hashtags
│   ├── viral_topics.json              # Selected viral topic details
│   └── word_timings.json              # EdgeTTS word-level timestamps
├── downloads/
│   └── videos/                        # Downloaded 4K stock clips & rendered scenes
├── logs/
│   └── pipeline.log                   # Comprehensive execution logs
├── output/
│   └── short.mp4                      # Final stitched, ducked & subtitled video
├── python/
│   ├── main.py                        # Master pipeline orchestrator
│   ├── find_viral_topics.py           # Step 1: 15-source discovery & deduplication
│   ├── generate_content.py            # Step 2: Fact-checking & hook optimization
│   ├── verify_facts.py                # Step 2b: Scientific fact cross-checking
│   ├── generate_voice.py              # Step 3: EdgeTTS voiceover & word timings
│   ├── create_subtitles.py            # Step 4: Karaoke SRT generator
│   ├── generate_search_queries.py     # Step 5: 1.8s visual beat splitter & physical queries
│   ├── multi_style_generator.py       # Step 6: Style 2 4K cinematic asset manager
│   ├── download_videos.py             # Step 6b: Pexels & Pixabay 4K stock downloader
│   ├── generate_fal_videos.py         # Step 6c: Fal.ai generative video circuit breaker
│   ├── generate_whiteboard.py         # Step 6d: Procedural doodle fallback generator
│   ├── generate_map_graphics.py       # Step 6e: 3D globe & map motion generator
│   ├── create_video.py                # Step 7: FFmpeg 1080x1920 video stitching
│   ├── download_music.py              # Step 7.5: Pixabay CDN mood music downloader
│   ├── add_audio.py                   # Step 8: Audio mixing & dynamic ducking (18% volume)
│   ├── burn_subtitles.py              # Step 9: Hard kinetic subtitle burning
│   ├── generate_thumbnail.py          # Step 10: High-CTR editorial thumbnail generator
│   ├── quality_checker.py             # Step 10.5: Automated quality gatekeeper (Score >= 8.5)
│   ├── publish_service.py             # Step 11: Multi-platform publishing coordinator
│   ├── upload_youtube.py              # Step 11a: YouTube API staged release & unlisted buffer
│   ├── upload_facebook.py             # Step 11b: Facebook Reels Graph API uploader
│   ├── upload_instagram.py            # Step 11c: Instagram Reels resumable container uploader
│   ├── harvest_analytics.py           # Step 11.5: Multi-platform analytics harvester
│   └── youtube_dashboard.py           # Step 12: Streamlit Growth SaaS Command Center
├── utils/
│   ├── config.py                      # Multi-tier LLM fallback & environment helper
│   ├── ffmpeg.py                      # FFmpeg subprocess wrapper with -movflags +faststart
│   ├── helpers.py                     # JSON sanitization & filesystem operations
│   ├── logger.py                      # Colorized console & file logger
│   ├── paths.py                       # Absolute project path definitions
│   └── retry.py                       # Exponential backoff retry decorators
├── .env                               # Local secrets & API keys (gitignored)
├── requirements.txt                   # Production Python dependencies
└── README.md                          # Comprehensive project documentation manual
```

---

## ⚙️ ENVIRONMENT VARIABLES & CONFIGURATION

### 1. Environment Secrets (`.env`)
Create a `.env` file in the root directory:

```ini
# LLM Intelligence
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIzaSy...

# Visual Assets
PEXELS_API_KEY=...
PIXABAY_API_KEY=...
FAL_KEY=...

# Meta Graph API (Facebook & Instagram)
META_APP_ID=...
META_APP_SECRET=...
META_ACCESS_TOKEN=EAAG...
FACEBOOK_PAGE_ID=1168804842990122
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841435307918273
ENABLE_META_AI_DUBBING=True

# YouTube OAuth (Local: uses token.pickle; Cloud: uses GitHub Secrets)
```

### 2. System Settings (`config/settings.json`)
Core settings controlling Style 2, the unlisted buffer, and audio mixing:

```json
{
  "llm": {
    "model": "openai/gpt-oss-120b",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "tts": {
    "voice": "en-US-AndrewMultilingualNeural",
    "rate": "+5%",
    "pitch": "+0Hz"
  },
  "video": {
    "visual_mode": "cinematic",
    "target_duration_seconds": 32,
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "codec": "libx264",
    "fade_duration": 0.3
  },
  "audio": {
    "voice_volume": 1.0,
    "music_volume": 0.18
  },
  "subtitles": {
    "font": "Bebas Neue",
    "fontsize": 22,
    "primary_color": "&H00FFFFFF",
    "back_color": "&H40000000",
    "outline_color": "&H00000000",
    "outline_width": 2,
    "margin_vertical": 60,
    "max_lines": 2
  },
  "upload": {
    "privacy": "unlisted",
    "staged_release": true,
    "category": "22",
    "daily_upload_cap": 3,
    "timezone": "Asia/Kolkata"
  },
  "publish": {
    "platforms": ["youtube", "facebook", "instagram"],
    "continue_on_failure": true
  }
}
```

---

## 💻 INSTALLATION & DEPLOYMENT GUIDE

### 1. Local Prerequisites
* **Python 3.11+**
* **FFmpeg 7.x** (installed and added to system `PATH`)
* **Git**

### 2. Local Setup
```bash
# 1. Clone repository
git clone https://github.com/ravindrareddy17/ai-video-generator.git
cd ai-video-generator

# 2. Set up virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install streamlit pandas

# 4. Generate YouTube OAuth token (first-time only)
python python/upload_youtube.py  # Follow browser prompt to generate token.pickle
```

### 3. Execution Commands
```bash
# Execute end-to-end video pipeline:
python python/main.py

# Launch Streamlit Growth SaaS Dashboard:
streamlit run python/youtube_dashboard.py
```

### 4. Cloud GitHub Actions Deployment
To enable 100% autonomous 3x daily posting in the cloud:
1. Fork or push this repository to GitHub.
2. Navigate to **Settings > Secrets and variables > Actions** and add:
   - `GROQ_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `GEMINI_API_KEY`
   - `META_APP_ID`, `META_APP_SECRET`, `META_ACCESS_TOKEN`
   - `FACEBOOK_PAGE_ID`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`
   - `TOKEN_PICKLE_BASE64` (run `base64 -w 0 token.pickle` and paste value)
   - `CLIENT_SECRET_BASE64` (run `base64 -w 0 client_secret.json` and paste value)
3. Enable Workflows under the **Actions** tab. The pipeline will automatically execute at 11:30, 16:00, and 22:30 UTC every day.

---

<div align="center">

<b>THE SHORTEST ORBIT V4.5+</b> • *Autonomous AI Video Generation & Channel Growth Engine*

</div>
