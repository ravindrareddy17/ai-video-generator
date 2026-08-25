# 🚀 THE SHORTEST ORBIT V4 — MASTER SYSTEM & ARCHITECTURE GUIDE

---

## 📌 Executive Overview
**The Shortest Orbit V4** is a fully autonomous, enterprise-grade AI media production studio. It automatically discovers high-velocity trending topics across 15+ global intelligence feeds, crafts controversial viral scripts, verifies hard facts, synthesizes human-grade voiceovers, generates photorealistic vertical AI video scenes using **Amazon Bedrock Nova Reel v1:1**, renders 4K vertical Shorts with dynamic typography, and publishes live across **YouTube, Facebook Reels, and Instagram Reels** with self-learning optimization.

---

## 🏗️ End-to-End Pipeline Architecture (12 Steps)

```mermaid
graph TD
    A[Step 1: Viral Topic Discovery] -->|NASA, SpaceX, Google News, arXiv| B[Step 2: Script & Hook Generation]
    B -->|Groq / Gemini / Nova Lite| C[Step 2.5: Hard Fact Verification]
    C -->|Fact Veto Guard| D[Step 3: EdgeTTS Voice Synthesis]
    D -->|en-US-AndrewMultilingualNeural| E[Step 4: Subtitle Generation & Alignment]
    E -->|Bebas Neue Word Highlighting| F[Step 5: Visual Prompt Formulation]
    F -->|data/search_queries.json| G[Step 6: AI Video Scene Generation]
    G -->|1st Preference: Amazon Nova Reel v1:1| H[Step 7: Video Clip Assembly & Rendering]
    H -->|FFmpeg 1080x1920 60fps| I[Step 7.5: Mood-Matched Background Music]
    I -->|Audio Ducking & Mixing| J[Step 8: Audio Multiplexing]
    J -->|Burn Subtitles & Color Grading| K[Step 9: High-CTR Thumbnail Generation]
    K -->|Cinzel Bold Word Styling| L[Step 10: Video Quality Check]
    L -->|10-Point QC Validator| M[Step 11: Multi-Platform Publishing]
    M -->|YouTube + Facebook + Instagram| N[Step 11.5: Analytics Harvesting]
    N -->|Step 12: Self-Learning AI Loop| O[Autonomous Feedback Loop]
```

---

## ☁️ AWS Bedrock & Cloud Infrastructure

### 1. Amazon Bedrock Nova Reel AI Video Generation
- **Active Video Model**: `amazon.nova-reel-v1:1`
- **Output Modality**: Full-motion 9:16 vertical video scenes (MP4 format, 24fps)
- **Primary Generator**: [`python/generate_aws_videos.py`](file:///E:/ai_gen/AI-VIDEO-V2/python/generate_aws_videos.py)

### 2. AWS S3 Storage
- **Bucket Name**: `the-shortest-orbit-nova-reel` (Region: `us-east-1`)
- **Bucket Policy**: `AmazonBedrockS3Policy` applied to allow `bedrock.amazonaws.com` write access for video rendering.

### 3. AWS IAM Security & Credentials
- **IAM User**: `BedrockAPIKey-ei0w` (`AKIA2O6TBXL2ZB56Z2OK`)
- **Execution Role**: `BedrockNovaReelExecutionRole` (`arn:aws:iam::719312763637:role/BedrockNovaReelExecutionRole`)
- **Permissions**: `AdministratorAccess`, `AmazonBedrockFullAccess`, `AmazonS3FullAccess`.

### 4. Zero-Rate-Limit LLM Resilience
- **LLM Hierarchy**: Groq (`openai/gpt-oss-120b`, `qwen/qwen3.6-27b`) $\rightarrow$ Gemini 2.5 Flash $\rightarrow$ **AWS Bedrock Nova Lite (`amazon.nova-lite-v1:0`)**.

---

## 📂 Core Repository Directory Map

```text
E:/ai_gen/AI-VIDEO-V2/
├── .env                              # Encrypted environment credentials (AWS, Meta, Groq, YouTube)
├── config/
│   └── settings.json                 # Master configuration (resolutions, models, volumes, quotas)
├── python/
│   ├── main.py                       # Master 12-Step pipeline orchestrator
│   ├── generate_aws_videos.py        # Amazon Bedrock Nova Reel v1:1 AI video generator
│   ├── download_videos.py            # Dual-source 4K full-motion MP4 fetcher (Pexels + Pixabay)
│   ├── find_viral_topics.py          # 15-source trending intelligence harvester
│   ├── generate_content.py           # High-retention script writer with comment hooks
│   ├── verify_facts.py               # Real-time fact verification & claim validator
│   ├── generate_audio.py             # EdgeTTS voice synthesizer (Andrew Multilingual)
│   ├── generate_subtitles.py         # Subtitle timing & alignment generator
│   ├── generate_search_queries.py    # Visual scene prompt synthesizer
│   ├── create_video.py               # FFmpeg multi-clip 1080x1920 video stitcher
│   ├── download_music.py             # Mood-matched background music selector
│   ├── add_audio.py                  # Dual-track audio mixer with speech ducking
│   ├── burn_subtitles.py             # Dynamic Cinzel / Bebas Neue typography burner
│   ├── generate_thumbnail.py         # 1280x720 high-CTR thumbnail compositor
│   ├── quality_checker.py            # 10-point automated video QC validator
│   ├── publish_service.py            # Multi-platform publishing coordinator
│   ├── upload_youtube.py             # YouTube Data API v3 OAuth2 publisher
│   ├── upload_facebook.py            # Facebook Graph API Reels publisher
│   ├── upload_instagram.py           # Instagram Graph API container publisher
│   ├── harvest_analytics.py          # Multi-platform performance metrics extractor
│   └── youtube_dashboard.py          # Streamlit White/Purple Editorial SaaS Dashboard
├── automation/
│   ├── ai/
│   │   ├── learning.py               # Autonomous self-learning optimization loop
│   │   └── prediction.py             # Pre-upload view & retention prediction models
│   └── database/                     # SQLite analytics & learning databases
├── assets/
│   ├── fonts/                        # Cinzel & Bebas Neue TrueType typography
│   └── music/                        # Royalty-free curated audio tracks
└── output/
    ├── short.mp4                     # Final production 1080x1920 Short video
    └── thumbnail.png                 # Final production high-CTR thumbnail
```

---

## ⚡ Tomorrow's Live Action Checklist (When AWS Approves Quota)

1. **Step 1 — Verify Approval**:
   Check your email or AWS Support Case (`Case ID: 178767424800583`).
2. **Step 2 — Trigger Single Live Generation**:
   ```bash
   python python/main.py
   ```
3. **Step 3 — Review Pure AI Video Output**:
   - Verify `output/short.mp4` contains custom **Amazon Nova Reel** scenes.
   - Verify automated publication across YouTube, Facebook, and Instagram.

---
*Created and maintained for THE SHORTEST ORBIT Production Team.*
