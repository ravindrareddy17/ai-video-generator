# 🚀 AI Video Generator V2 — The Shortest Orbit

**Fully autonomous AI pipeline that creates and publishes short-form videos to YouTube, Instagram & Facebook — with zero human intervention.**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-orange?logo=ffmpeg)
![GitHub Actions](https://img.shields.io/badge/Automation-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active_Development-yellow?style=flat)

> **⚠️ Note:** This project is under **active development**. The core video generation pipeline is stable and running 100% on autopilot, but some secondary features are still being polished. See the [Project Status & Known Issues](#-project-status--known-issues) section at the bottom for more details.

---

## 💡 Why This Project?

Most content creators spend **hours every day** manually creating, editing, and uploading videos. This project was built with one simple idea:

> **What if AI could handle the entire process — from idea to upload — while you sleep?**

That's exactly what this does. Set it up once, and it works for you **24/7**:

- 🎥 **5 videos per day** — posted automatically across 3 platforms
- 🧠 **AI picks trending topics** — so your content is always relevant
- ✅ **AI fact-checks everything** — so you never post misinformation
- 📈 **AI learns from analytics** — so your content improves over time
- 💰 **Zero cost to run** — uses free APIs and free GitHub Actions

Whether you're a **student**, a **content creator**, or a **developer** exploring AI automation — this project is for you. Fork it, customize it, make it yours.

---

## 🎯 What Does This Do?

This project automatically creates viral short videos and posts them to social media **5 times per day** — completely hands-free.

**One command. One pipeline. Three platforms. Zero effort.**

```bash
python python/main.py
```

**The 12-Step Autonomous Pipeline:**

1. 🔍 **Scans 15+ sources** (Google Trends, NASA, arXiv, Reddit, etc.) for trending topics
2. ✍️ **AI writes** a short, engaging video script using Groq LLM
3. ✅ **AI fact-checks** the script and fixes any inaccuracies
4. 🎙️ **Generates voiceover** using Microsoft Neural TTS
5. 🎬 **Downloads stock footage** matching the context from Pexels/Pixabay
6. 🎵 **Selects background music** matched to the video's mood
7. 🔊 **Assembles audio** with professional ducking (voice + music)
8. 💬 **Burns subtitles** in a stylized, modern karaoke format
9. 🖼️ **Generates thumbnail** using AI
10. 📤 **Uploads to** YouTube Shorts, Instagram Reels, and Facebook Reels
11. 📊 **Collects analytics** (views, likes, engagement) from all platforms
12. 🤖 **AI learns** from past performance to make better videos next time

**Total time: ~5 minutes per video.**

---

## 📋 Table of Contents

- [Tech Stack](#%EF%B8%8F-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Automated Scheduling (GitHub Actions)](#-automated-scheduling-github-actions)
- [Customization](#%EF%B8%8F-customization)
- [Troubleshooting](#-troubleshooting)
- [Project Status & Known Issues](#-project-status--known-issues)
- [Support This Project](#-support-this-project)

---

## 🛠️ Tech Stack

| Component | Technology |
|:----------|:-----------|
| **AI Brain** | Groq Cloud API (Llama 3.3 70B) |
| **Voice** | Microsoft Edge TTS (free, neural) |
| **Stock Footage** | Pexels API + Pixabay API |
| **Thumbnails** | Google Imagen AI + Pillow fallback |
| **Video Editing** | FFmpeg |
| **YouTube Upload** | YouTube Data API v3 (OAuth 2.0) |
| **Insta/FB Upload** | Meta Graph API |
| **Database** | SQLite |
| **Automation** | GitHub Actions (5x daily cron) |

---

## 📂 Project Structure

```text
AI-VIDEO-V2/
├── python/                     ← Core pipeline modules (main.py, etc.)
├── automation/                 ← Analytics + AI learning logic
├── utils/                      ← Shared utilities (config, ffmpeg wrapper)
├── config/settings.json        ← Customization settings
├── dashboard/index.html        ← Analytics dashboard (browser UI)
├── assets/                     ← Fonts and background music
├── output/                     ← Final generated videos and thumbnails
├── logs/                       ← Execution logs (pipeline.log)
├── .github/workflows/main.yml  ← GitHub Actions automation config
└── .env                        ← API keys (git-ignored for security)
```

---

## 🚀 Quick Start

### Step 1: Install FFmpeg

```bash
# Windows
winget install Gyan.FFmpeg

# Mac
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### Step 2: Clone & Install

```bash
git clone https://github.com/ravindrareddy17/ai-video-generator.git
cd ai-video-generator
pip install -r requirements.txt
```

### Step 3: Add Your API Keys

Create a `.env` file in the project root:

```env
# Required
GROQ_API_KEY=your_groq_key
PEXELS_API_KEY=your_pexels_key
PIXABAY_API_KEY=your_pixabay_key
GEMINI_API_KEY=your_gemini_key

# Optional (for Instagram & Facebook)
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_ACCESS_TOKEN=your_meta_token
FACEBOOK_PAGE_ID=your_fb_page_id
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_id
```

**Where to get free API keys:**
- **Groq:** [console.groq.com](https://console.groq.com)
- **Pexels:** [pexels.com/api](https://www.pexels.com/api/)
- **Pixabay:** [pixabay.com/api/docs](https://pixabay.com/api/docs/)
- **Gemini:** [aistudio.google.com](https://aistudio.google.com/apikey)
- **Meta:** [developers.facebook.com](https://developers.facebook.com/)

### Step 4: Setup YouTube Upload

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project and enable **YouTube Data API v3**
3. Create **OAuth Client ID** (Desktop App) credentials
4. Download the JSON file → rename to `client_secret.json` → place in project root
5. Run the pipeline once — a browser window opens for login
6. After login, `token.pickle` is saved and all future runs are automatic

### Step 5: Run It!

```bash
python python/main.py
```

That's it! Your video will be generated and uploaded in ~5 minutes.

---

## ⏰ Automated Scheduling (GitHub Actions)

The pipeline runs **5 times per day** automatically via GitHub Actions:

| Time (UTC) | Time (IST) | Time (EST) | Target Audience |
|:-----------|:-----------|:-----------|:----------------|
| 11:00 AM | 4:30 PM | 7:00 AM | Morning commute peak |
| 3:00 PM | 8:30 PM | 11:00 AM | US lunch + EU afternoon |
| 6:30 PM | 12:00 AM | 2:30 PM | US afternoon + EU prime-time |
| 10:00 PM | 3:30 AM | 6:00 PM | US evening peak |
| 1:30 AM | 7:00 AM | 9:30 PM | US late night + Asia morning |

### How to Enable GitHub Actions

1. Push the repo to GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Add these base64-encoded secrets:
   - `GROQ_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `GEMINI_API_KEY`
   - `TOKEN_PICKLE_BASE64` (Base64 of your `token.pickle` file)
   - `CLIENT_SECRET_BASE64` (Base64 of your `client_secret.json` file)
   - Meta keys (if uploading to Instagram/Facebook)
4. Go to **Actions** tab → click **Run workflow** to test it!

---

## ⚙️ Customization

Edit `config/settings.json` to customize:
- **AI Voice:** Choose from Microsoft Neural voices (e.g., `en-US-GuyNeural`, `en-US-AvaNeural`)
- **Subtitle Style:** Font, size, color, outline, position
- **Video Quality:** Resolution, framerate, CRF quality level
- **Audio Mix:** Voice vs. music volume balance
- **Upload Settings:** Privacy status, category, daily limits

---

## 🔒 Security Note

Your credentials are always safe:
- `.env`, `token.pickle`, and `client_secret.json` are in `.gitignore` — they never get uploaded
- GitHub Secrets are encrypted — nobody can see them
- Making the repo public does **NOT** expose your API keys

---

## 📝 Troubleshooting

| Problem | Solution |
|:--------|:---------|
| Pipeline fails at Step 1 | Check your `GROQ_API_KEY` in `.env` |
| No stock footage downloaded | Check your `PEXELS_API_KEY` in `.env` |
| YouTube upload fails | Delete `token.pickle` and re-authenticate |
| GitHub Actions fails | Check **Actions** tab for error logs |
| "Token expired" error | Re-run auth and update `TOKEN_PICKLE_BASE64` secret |

Full logs are saved to `logs/pipeline.log`.

---

## 📌 Project Status & Known Issues

This project is under **active development** and will continue to receive updates, bug fixes, and new features based on real-world testing. 

While the core video generation and uploading pipeline is fully stable, please be aware of the following:

- **Analytics Dashboard:** The local browser dashboard (`dashboard/index.html`) is not fully finished and has some known bugs. It will be improved in future updates.
- **Reddit Source:** The Reddit API sometimes returns 403 errors when called from GitHub Actions servers. The pipeline handles this gracefully by falling back to other trending sources.
- **Thumbnail AI:** Some Google Imagen models may occasionally be unavailable; the pipeline will automatically fall back to a local typography-based thumbnail generator when this happens.
- **Running Locally:** If you want to customize the pipeline (change topics, voices, posting schedule, etc.), clone the repo, make your changes, and run `python python/main.py` locally. 

---

## 🤝 Contributing

1. Fork this repo
2. Create a branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 🌟 Support This Project

If you find this project useful, consider giving it a ⭐ **star** on GitHub — it helps others discover it!

- ⭐ **Star this repo** to show your support
- 🍴 **Fork it** to create your own version
- 🐛 **Report issues** if you find bugs
- 💡 **Suggest features** you'd like to see

---

## 📄 License

Open source under the [MIT License](LICENSE).

---

**Built with ❤️ by [@ravindrareddy17](https://github.com/ravindrareddy17)**

*Stop creating content manually. Let AI do it for you.*
