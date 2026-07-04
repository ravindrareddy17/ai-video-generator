"""
find_viral_topics.py — Step 1 of the AI Video Generator V2 pipeline.

Searches for trending topics from reliable sources (Google Trends, Reddit,
Google News), deduplicates them, and scores them using the Groq LLM to select
the best topic for a YouTube Short.

Outputs:
    data/viral_topics.json
"""

import sys
from pathlib import Path
import json
import urllib.parse
from datetime import datetime
import feedparser
import requests
from groq import Groq

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.paths import DATA_DIR, VIRAL_TOPICS_FILE
from utils.config import load_settings, get_setting, get_groq_key
from utils.logger import get_logger
from utils.helpers import save_json
from utils.retry import retry

logger = get_logger(__name__)


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def fetch_google_trends(geo: str = 'US') -> list[dict]:
    """Fetch trending queries from Google Trends RSS feed."""
    logger.info(f"Fetching Google Trends for geo={geo}...")
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    
    feed = feedparser.parse(url)
    topics = []
    
    if hasattr(feed, 'entries') and feed.entries:
        for entry in feed.entries:
            title = entry.title
            # Google Trends title format is often just the keyword/topic name
            topics.append({
                "title": title.strip(),
                "source": "Google Trends",
                "score_signal": 50  # base weight for Google Trends
            })
    logger.info(f"Fetched {len(topics)} topics from Google Trends.")
    return topics


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def fetch_reddit_topics(subreddits: list[str]) -> list[dict]:
    """Fetch hot topics from specified subreddits."""
    topics = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for sub in subreddits:
        logger.info(f"Fetching hot topics from r/{sub}...")
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    post_data = post.get("data", {})
                    if post_data.get("stickied"):
                        continue  # Skip stickied posts
                    
                    title = post_data.get("title", "")
                    upvotes = post_data.get("ups", 0)
                    
                    # Exclude very short titles
                    if len(title.split()) > 3:
                        topics.append({
                            "title": title.strip(),
                            "source": f"Reddit r/{sub}",
                            "score_signal": min(upvotes // 10, 100)  # scale upvotes to a signal score
                        })
            else:
                logger.warning(f"Reddit r/{sub} returned status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching Reddit r/{sub}: {e}")
            
    logger.info(f"Fetched {len(topics)} topics from Reddit.")
    return topics


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def fetch_google_news() -> list[dict]:
    """Fetch top headlines from Google News RSS feed."""
    logger.info("Fetching Google News headlines...")
    url = "https://news.google.com/rss/search?q=space+OR+science+OR+AI&hl=en-US&gl=US&ceid=US:en"
    
    feed = feedparser.parse(url)
    topics = []
    
    if hasattr(feed, 'entries') and feed.entries:
        for entry in feed.entries:
            title = entry.title
            # Strip source name from title if present, e.g. "Headline - CNN"
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            
            topics.append({
                "title": title.strip(),
                "source": "Google News",
                "score_signal": 40  # base weight for news
            })
    logger.info(f"Fetched {len(topics)} topics from Google News.")
    return topics


def collect_all_topics() -> list[dict]:
    """Gather topics from all sources and deduplicate them."""
    settings = load_settings()
    subreddits = ['space', 'science', 'Futurology', 'artificial']
    geo = get_setting('trending', 'google_trends_geo', 'US')
    
    all_topics = []
    
    # Try Trends
    try:
        all_topics.extend(fetch_google_trends(geo))
    except Exception as e:
        logger.error(f"Failed to fetch Google Trends: {e}")
        
    # Try Reddit
    try:
        all_topics.extend(fetch_reddit_topics(subreddits))
    except Exception as e:
        logger.error(f"Failed to fetch Reddit topics: {e}")
        
    # Try Google News
    try:
        all_topics.extend(fetch_google_news())
    except Exception as e:
        logger.error(f"Failed to fetch Google News: {e}")
        
    # Deduplicate based on title similarity/exact match
    seen_titles = set()
    unique_topics = []
    
    for t in all_topics:
        norm_title = t["title"].strip().lower()
        if norm_title not in seen_titles:
            seen_titles.add(norm_title)
            unique_topics.append(t)
            
    logger.info(f"Total unique topics collected: {len(unique_topics)}")
    return unique_topics


def get_recent_uploaded_titles() -> list[str]:
    """Retrieve the titles of the last 15 uploaded videos from the YouTube channel."""
    try:
        from python.upload_youtube import get_authenticated_service
        youtube = get_authenticated_service()
        if not youtube:
            logger.info("YouTube client not available, skipping recent uploads fetch.")
            return []
            
        channels_response = youtube.channels().list(
            mine=True,
            part="contentDetails"
        ).execute()
        
        if not channels_response.get("items"):
            logger.info("No channel found for current credentials.")
            return []
            
        uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        playlist_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="snippet",
            maxResults=15
        ).execute()
        
        titles = []
        for item in playlist_response.get("items", []):
            titles.append(item["snippet"]["title"])
        logger.info(f"Fetched {len(titles)} recent uploaded titles from channel to prevent duplicate concepts.")
        return titles
    except Exception as e:
        logger.warning(f"Could not fetch recent uploaded titles: {e}")
        return []


def select_best_topic(topics: list[dict], recent_titles: list[str] = None) -> dict:
    """Send topics to Groq LLM to extract viral angles and choose the best one."""
    if not topics:
        return {
            "selected_topic": "Scientists just found something hiding in our solar system.",
            "viral_angle": "Default fallback topic",
            "hook_line": "Scientists just found something hiding in our solar system.",
            "source": "Fallback"
        }
        
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
    client = Groq(api_key=api_key)
    
    # Take top 30 to limit token usage
    topics_sorted = sorted(topics, key=lambda x: x["score_signal"], reverse=True)
    top_candidates = topics_sorted[:30]
    
    candidate_list_str = "\n".join([f"- {t['title']} (Source: {t['source']})" for t in top_candidates])
    
    system_prompt = (
        "SYSTEM PROMPT — The Shortest Orbit: Viral Topic Scanner\n\n"
        "You take raw current news items about space, science, or AI and convert "
        "each into a viral-ready Shorts concept. Your job is NOT to explain the news "
        "like a journalist — it's to find the single most shocking, curiosity-driving "
        "angle inside it that a general audience (not scientists) would stop scrolling for.\n\n"
        "Input: a list of recent news headlines/summaries.\n"
        "Output: valid JSON array, no preamble, no markdown fences.\n\n"
        "[\n"
        "  {\n"
        "    \"source_headline\": \"the original news item this is based on\",\n"
        "    \"viral_angle\": \"the ONE most surprising fact hiding in this story — stated in plain language a 12-year-old would understand\",\n"
        "    \"hook_line\": \"first 2 seconds — must sound almost unbelievable, framed as a question or shocking statement\",\n"
        "    \"why_it_could_go_viral\": \"1 sentence: what makes people want to comment, share, or argue about this\",\n"
        "    \"risk_flag\": \"note if this topic is too technical, too uncertain/early-stage research, or too niche to simplify honestly — flag rather than force it\"\n"
        "  }\n"
        "]\n\n"
        "RULES:\n"
        "1. Reject stories that can't be simplified without becoming misleading. Skip them rather than oversimplify to the point of being wrong.\n"
        "2. Prioritize stories with a \"wait, that's real?\" reaction over purely incremental research news. Shift focus towards 'bizarre science facts,' 'cosmic scale comparisons,' and 'sci-fi real-life tech'.\n"
        "3. Never sensationalize to the point of inaccuracy — surprising != false.\n"
        "4. The hook_line MUST use powerful, high-emotion viral power words like 'Uncovered', 'Exposed', 'Game Changer', 'Forbidden', or 'Breaking' to capture immediate viewer attention.\n"
        "5. CRITICAL: The chosen topic MUST bridge the intersection of all three: SPACE, SCIENCE, and AI (e.g., using AI to map Mars features, neural networks decoding deep space radio signals, AI analyzing exoplanet biosignatures). Frame or select the story to capture this powerful synergy!"
    )
    
    user_prompt = f"Extract viral angles from these raw headlines:\n\n{candidate_list_str}"
    
    if recent_titles:
        recent_titles_str = "\n".join([f"- {t}" for t in recent_titles])
        user_prompt += f"\n\nCRITICAL: DO NOT select any topic that overlaps or is similar to these recently uploaded videos on the channel:\n{recent_titles_str}"
    
    logger.info("Calling Groq LLM to scan for viral topics...")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.7
        )
        
        response_text = chat_completion.choices[0].message.content
        # Try to parse the JSON array
        # Clean markdown fences if any slipped through
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:-3]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:-3]
            
        concepts = json.loads(clean_text)
        
        # Filter out concepts with a risk flag
        safe_concepts = []
        for c in concepts:
            risk = c.get("risk_flag", "")
            if not risk or str(risk).lower() in ["none", "null", "false", "no"]:
                safe_concepts.append(c)
                
        if safe_concepts:
            best_concept = safe_concepts[0]  # Just take the first safe one
        else:
            best_concept = concepts[0] # Fallback if all are risky
            
        logger.info(f"Groq selected topic hook: '{best_concept.get('hook_line')}'")
        
        return {
            "selected_topic": f"{best_concept.get('hook_line')} {best_concept.get('viral_angle')}",
            "viral_angle": best_concept.get("viral_angle"),
            "hook_line": best_concept.get("hook_line"),
            "source": best_concept.get("source_headline")
        }
        
    except Exception as e:
        logger.error(f"Error calling Groq for topic selection: {e}")
        best_fallback = top_candidates[0]
        return {
            "selected_topic": best_fallback["title"],
            "viral_angle": best_fallback["title"],
            "hook_line": "Did you know about this?",
            "source": best_fallback["source"]
        }


def run() -> dict:
    """Orchestrates Step 1 of the pipeline."""
    logger.info("=== STEP 1: FIND VIRAL TOPICS ===")
    
    topics = collect_all_topics()
    recent_titles = get_recent_uploaded_titles()
    selected = select_best_topic(topics, recent_titles)
    
    import datetime
    
    # Package output data
    output_data = {
        "topics": [t["title"] for t in topics],
        "selected_topic": selected.get("selected_topic"),
        "viral_angle": selected.get("viral_angle"),
        "hook_line": selected.get("hook_line"),
        "source": selected.get("source"),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    save_json(output_data, VIRAL_TOPICS_FILE)
    logger.info(f"Selected topic saved to {VIRAL_TOPICS_FILE}")
    
    return output_data


if __name__ == "__main__":
    try:
        result = run()
        print(json.dumps(result, indent=2))
    except Exception as exc:
        logger.exception("find_viral_topics module execution failed")
        sys.exit(1)
