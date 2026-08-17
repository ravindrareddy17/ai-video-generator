# 🚀 THE SHORTEST ORBIT — V4 Autonomous Content Growth & Learning Engine

**The Shortest Orbit V4** is a 100% autonomous, self-improving content intelligence and video production engine. It researches, fact-verifies, scores, scripts, renders, media-validates, publishes, and continuously learns from YouTube analytics to optimize audience growth for:

# THE SHORTEST ORBIT

> **"Understand the biggest battles, discoveries and technologies shaping space and the future — in seconds."**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq_Llama_3.3_70B-orange?logo=meta)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Zero_Freeze_Frames-success?logo=ffmpeg)
![Status](https://img.shields.io/badge/Schema-V4.0_Master_Contract-brightgreen?style=flat)

---

## 💡 The V4 Closed-Loop Growth Architecture

Most automation engines create static, unoptimized videos. **V4** operates an evidence-based, data-driven closed loop:

$$\text{RESEARCH} \longrightarrow \text{VERIFY} \longrightarrow \text{SCORE} \longrightarrow \text{SELECT} \longrightarrow \text{CREATE} \longrightarrow \text{MEDIA QA} \longrightarrow \text{PUBLISH} \longrightarrow \text{SNAPSHOT ANALYTICS} \longrightarrow \text{DIAGNOSE} \longrightarrow \text{LEARN} \longrightarrow \text{IMPROVE}$$

```text
               THE SHORTEST ORBIT V4 CLOSED LOOP
                             │
                             ▼
                    ┌─────────────────┐
                    │ Audience Memory │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Topic Discovery │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Fact Verification│ (Tiered 7-Level Hierarchy)
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Topic Scoring   │ (TopicScore + HistSim Bonus)
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Hook + Title    │ (Normalized H.I.S.T. Engine)
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Script + Visual │ (Fast B-Roll Pacing)
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Quality Gate    │ (11 Mandatory Checks + Accuracy Veto)
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Media QA        │ (1080x1920 H.264/AAC Validation)
                    └────────┬────────┘
                             ↓
                         PUBLISH
                             │
                             ▼
                    ┌─────────────────┐
                    │ YouTube Data    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Analytics       │ (Time-Series Snapshots & Velocity)
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Baseline Engine │ (Median, Mean, P25, P75)
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Diagnostic      │ (Bottleneck Case Engine)
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Learning Engine │ (Closed-Loop Feedback)
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Audience Memory │
                    └────────┬────────┘
                             │
                             └──────────→ NEXT VIDEO
```

---

## 🎯 Key Production Systems in V4.0

### 1. Hard Multi-Condition Accuracy Veto Gate
Accuracy is a non-negotiable publication gate:
- `IF verification_status == "rejected" ➔ REJECT`
- `IF claims_verified == false ➔ REJECT`
- `IF accuracy_score < 7.0 ➔ REVISE`
- `IF any HIGH importance claim is unverified ➔ REJECT`
- `IF source verification is insufficient ➔ REJECT`

### 2. 11 Mandatory Pre-Publish Quality Checks
Validated in `python/v4_contract_engine.py`:
1. `hook_understood_immediately`
2. `story_has_clear_stakes`
3. `claims_verified`
4. `visuals_support_narration`
5. `no_filler`
6. `payoff_delivered`
7. `title_is_accurate`
8. `content_is_original`
9. `channel_fit_is_strong`
10. `reason_to_return_exists`
11. `policy_risk_checked`

$$\text{Transition to APPROVED requires: } \mathbf{\text{all}(\text{checks.values}()) == \text{True}}$$

### 3. Tiered Source Verification Hierarchy (7 Levels)
- **Level 1**: Official / Primary Source (NASA, SpaceX, DoD, ISRO)
- **Level 2**: Government / Scientific Institution
- **Level 3**: Peer-Reviewed Research
- **Level 4**: High-Quality Specialist Journalism
- **Level 5**: General Reputable Journalism
- **Level 6**: Secondary Sources
- **Level 7**: Social Media (investigation leads only)
*High-impact claims require 2+ Level 1/2 sources; basic orbital facts require 1 authoritative source.*

### 4. Normalized 6-Dimension H.I.S.T. Hook Engine
$$\mathbf{\text{HookScore} = 0.20(\text{HighStakes}) + 0.20(\text{ImmediateCuriosity}) + 0.20(\text{Specificity}) + 0.15(\text{Tension}) + 0.15(\text{Clarity}) + 0.10(\text{VisualPotential})}$$

### 5. Zero Freeze Frame Fluid Motion Video Renderer (`python/create_video.py`)
- Completely eliminated frozen still-frame padding (`tpad`).
- Uses `-stream_loop -1` for continuous, dynamic motion.
- Dual-source aggregator (`download_videos.py`) queries **Pexels + Pixabay** simultaneously for top HD candidates.

### 6. Technical Media QA Validator (`python/media_qa.py`)
Pre-upload technical verification:
- 1080x1920 resolution & 9:16 vertical aspect ratio.
- Standard H.264 video & AAC audio codecs.
- Framerate (30 FPS) & 10s–60s duration window.
- Zero corrupted frames, zero missing tracks.

### 7. Statistical Channel Baselines & Minimum-Data Protection (`python/baseline_engine.py`)
- Calculates statistical medians, means, P25, and P75 across metrics (`views`, `APV`, `subscriber_conversion_rate`).
- Enforces `sample_size < 5 ➔ INSUFFICIENT DATA` protection so strategic shifts are only made with statistical confidence.

### 8. 5-Fingerprint Anti-Repetition Engine (`python/topic_fingerprint.py`)
Hashes and tracks `topic_fingerprint`, `story_fingerprint`, `claim_fingerprint`, `title_fingerprint`, and `hook_fingerprint` to block repetitive concepts.

---

## 🛠️ Project Directory Structure

```text
AI-VIDEO-V2/
├── python/
│   ├── main.py                     # Pipeline Orchestrator (Generation -> Media QA -> Upload)
│   ├── v4_contract_engine.py       # Master V4 JSON Contract & Validation Engine
│   ├── self_learning.py            # Diagnostic Engine & Audience Memory Manager
│   ├── learning_engine.py          # Closed-Loop Post-Publication Feedback Engine
│   ├── analytics_engine.py         # Time-Series Analytics & Velocity Calculator
│   ├── baseline_engine.py          # Channel Statistical Baselines (Mean, Median, P25, P75)
│   ├── audience_memory.py          # Persistent Historical Patterns (Winning/Weak)
│   ├── topic_engine.py             # Topic Selection & Fingerprint Deduplication
│   ├── topic_fingerprint.py        # 5-Fingerprint Concept Deduplication
│   ├── find_viral_topics.py        # Topic Discovery & TopicScore Engine
│   ├── verify_facts.py             # Tiered Source Hierarchy Fact Checker
│   ├── competitor_engine.py        # Competitor Gap Analyzer
│   ├── experiment_engine.py        # Controlled Experiment Matrix Manager
│   ├── generate_content.py         # Scriptwriter & H.I.S.T. Hook Generator
│   ├── download_videos.py          # Dual-Source Stock Video Aggregator (Pexels + Pixabay)
│   ├── create_video.py             # Zero Freeze Frame Fluid Motion Video Renderer
│   ├── media_qa.py                 # Technical Video & Audio Media QA Validator
│   └── upload_engine.py            # Multi-Platform Publisher (YouTube/FB/IG)
│
├── utils/
│   ├── db.py                       # Expanded SQLite 9-Table Database Manager
│   ├── config.py                   # Environment & Credentials Accessors
│   ├── ffmpeg.py                   # FFmpeg Core Utilities
│   └── paths.py                    # Central Path Definitions
│
├── data/
│   ├── v4_contracts/               # Stored V4 Video Contract JSONs
│   ├── source_cache/               # Source Verification Cache
│   └── topic_memory/               # Topic Fingerprints & History
│
├── output/
│   ├── videos/                     # Generated MP4 Files
│   ├── subtitles/                  # SRT / ASS Subtitle Files
│   └── v4_contract.json            # Current Video Contract Manifest
│
└── shortest_orbit_v3.db            # Persistent SQLite Database
```

---

## ⚡ Quick Start

### 1. Execute Pipeline End-to-End
```powershell
python python/main.py
```

### 2. Verify V4 Contract Manifest
```powershell
python -c "from python.v4_contract_engine import V4ContractEngine; print(V4ContractEngine().create_draft_contract('SpaceX Starshield'))"
```

---

*The Shortest Orbit V4 — Data ➔ Create ➔ Measure ➔ Learn ➔ Improve ➔ Repeat.*
