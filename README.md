<div align="center">

# 🚀 THE SHORTEST ORBIT
### *Autonomous V4 Content Growth & AI Video Production Engine*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-4K_UHD_Render-0078D4?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org)
[![LLM Resilient](https://img.shields.io/badge/LLM-Groq_%2B_Gemini_Fallback-8E44AD?style=for-the-badge&logo=openai&logoColor=white)](#-resiliency--error-handling-architecture)
[![Status](https://img.shields.io/badge/Status-Under_Active_Development-FF6B6B?style=for-the-badge)](#-project-status)

<p align="center">
  <b>"Understand the biggest battles, discoveries, and technologies shaping space and the future — in seconds."</b>
</p>

---

</div>

> [!WARNING]  
> ### 🚧 Project Status: Under Active Development
> This repository is under **rapid active iteration**. Architecture, LLM prompt templates, database schemas, and video rendering filters are continuously optimized for maximum viewer retention and YouTube growth.

---

## 🌟 Key Highlights & Features

- 🤖 **100% Autonomous Pipeline**: From trending topic discovery to publishing & analytics harvesting without human intervention.
- 🎯 **Fact Verification Veto Gate**: Tiered 7-level scientific fact checking (*NASA, arXiv, Nature*) that automatically vetoes unverified claims.
- 🎬 **Topic-Aware Visual Query Engine**: Fuses overall topic context with sentence-level actions to download 100% relevant 4K UHD video clips.
- ⚡ **Resilient Multi-Tier LLM Architecture**: Automatic model rotation across Groq (`qwen3.6-27b`, `compound-mini`, `gpt-oss-120b`) with seamless fallback to **Gemini 2.5 Flash**.
- 📊 **YouTube Growth Command Center**: A modern White/Purple Editorial SaaS dashboard for real YouTube analytics and V4 internal strategy diagnostics.

---

## 🔄 Closed-Loop Growth Architecture

```text
                  THE SHORTEST ORBIT V4 CLOSED-LOOP PIPELINE
                  
  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ 1. VIRAL TOPIC   │ ───► │ 2. FACT CHECK &  │ ───► │ 3. VOICE &       │
  │    DISCOVERY     │      │    SCRIPTING     │      │    TIMINGS       │
  └──────────────────┘      └──────────────────┘      └────────┬─────────┘
                                                               │
  ┌──────────────────┐      ┌──────────────────┐               │
  │ 6. 4K STOCK CLIP │ ◄─── │ 5. VISUAL QUERY  │ ◄─────────────┘
  │    DOWNLOADER    │      │    EXTRACTOR     │
  └────────┬─────────┘      └──────────────────┘
           │
           ▼
  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ 7. MOOD MUSIC &  │ ───► │ 8. STITCH 1080x  │ ───► │ 9. BURN STYLED   │
  │    AUDIO MIXING  │      │    1920 SHORT    │      │    SUBTITLES     │
  └──────────────────┘      └──────────────────┘      └────────┬─────────┘
                                                               │
  ┌──────────────────┐      ┌──────────────────┐               │
  │ 12. GROWTH       │ ◄─── │ 11. PUBLISH &    │ ◄─────────────┘
  │     DASHBOARD    │      │     HARVEST      │
  └──────────────────┘      └──────────────────┘
```

---

## 🛠️ End-to-End Implementation Breakdown

| Step | Module File | Description & Technical Engine |
| :---: | :--- | :--- |
| **01** | [`python/find_viral_topics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/find_viral_topics.py) | **Viral Topic Discovery**: Scrapes Reddit (*r/space, r/spacex, r/science*), Google Trends, and NASA RSS feeds. Assigns V4 Opportunity Scores ($0.0 – 10.0$). |
| **02** | [`python/generate_content.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_content.py)<br>[`python/verify_facts.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/verify_facts.py) | **Fact Verification & Scripting**: Checks facts against 7 authority sources. Enforces a **Hard Accuracy Veto Gate** (`accuracy_score >= 7.0`). |
| **03** | [`python/generate_voice.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_voice.py) | **Neural Voice Synthesis**: Synthesizes broadcast voiceover via EdgeTTS (`en-US-AndrewMultilingualNeural`) and generates word-level timings. |
| **04** | [`python/create_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_subtitles.py) | **Subtitle Formatting**: Formats timestamps into SRT subtitles with smart 2-line wrapping to prevent screen clutter. |
| **05** | [`python/generate_search_queries.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_search_queries.py) | **Topic-Aware Visual Extraction**: Merges topic context with sentence actions (*e.g., `"china lunar mining robot"`*) for high retention visuals. |
| **06** | [`python/download_videos.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/download_videos.py) | **Dual-Source Asset Downloader**: Searches Pexels & Pixabay for vertical 4K/HD video clips ($2160\times3840\text{px}$) with zero static images. |
| **07** | [`python/download_music.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/download_music.py)<br>[`python/add_audio.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/add_audio.py) | **Audio Mixing**: Selects mood-matched royalty-free background music and mixes voice (1.0) with music (0.4). |
| **08** | [`python/create_video.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/create_video.py) | **Video Assembly**: Crops and scales clips into 1080x1920 vertical format. Applies seamless looping (`-stream_loop -1`) to short clips. |
| **09** | [`python/burn_subtitles.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/burn_subtitles.py) | **Hard Subtitle Burn**: Burns custom Bebas Neue / Cinzel styled subtitles with semi-transparent dark box background into `output/short.mp4`. |
| **10** | [`python/generate_thumbnail.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_thumbnail.py) | **Thumbnail Generator**: Extracts a frame at 30% duration, applies dark gradient overlay, and adds high-contrast editorial typography. |
| **11** | [`python/publish_service.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/publish_service.py)<br>[`python/harvest_analytics.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/harvest_analytics.py) | **Multi-Platform Publish & Analytics**: Uploads to YouTube, Facebook & Instagram, and periodically harvests views, retention & subscribers into SQLite. |
| **12** | [`python/youtube_dashboard.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/youtube_dashboard.py) | **YouTube Growth Command Center**: Streamlit dashboard with White/Purple Editorial SaaS styling (`#FFFFFF` bg, `#111827` text, `#4F46E5` accent). |

---

## 🛡️ Resiliency & Error Handling Architecture

> [!TIP]  
> The system is designed to run completely unattended with automated error recovery:

- 🔄 **Groq API Rate Limit Resiliency**: If HTTP 429 rate limit is hit, `call_groq_with_fallback()` automatically rotates through model tiers before triggering **Gemini 2.5 Flash REST API** as a final backup.
- 🧹 **Robust JSON Parser**: `extract_json_from_llm()` automatically strip reasoning tags (`<think>...</think>`) and markdown syntax blocks before parsing.
- ⚡ **FFmpeg 4K Memory Optimization**: Built-in `-preset fast -threads 4` arguments prevent memory allocation (`malloc`) failures when processing UHD 4K source footage.
- 🔁 **Duplicate Asset Prevention**: Queries SQLite memory to exclude any stock video clip IDs used in the last 15 published Shorts.

---

## 💻 Local Installation & Setup Guide

### 1. System Requirements
- **Python 3.11+**
- **FFmpeg** (added to system environment `PATH`)
- **Git**

### 2. Quick Start Commands

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

### 3. Environment Setup (`.env`)
Create a `.env` file in the root directory:

```ini
GROQ_API_KEY=your_groq_api_key
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 4. Running the Engine & Dashboard

```bash
# Run full video generation pipeline end-to-end:
python python/main.py

# Launch YouTube Growth Command Center Dashboard:
streamlit run python/youtube_dashboard.py
```

---

<div align="center">

<b>THE SHORTEST ORBIT V4</b> • *Autonomous AI Video Generation & Channel Growth Engine*

</div>
