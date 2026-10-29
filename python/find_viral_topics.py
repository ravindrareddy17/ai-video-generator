import re
"""
find_viral_topics.py — Step 1 of the AI Video Generator V2 pipeline.

Searches for trending topics from reliable sources (Google Trends, Reddit,
Google News), deduplicates them, and scores them using the Groq LLM to select
the best topic for a YouTube Short.

Outputs:
    data/viral_topics.json
"""

import sys
import re
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
from automation.database.connection import get_automation_conn

logger = get_logger(__name__)

# ==============================================================================
# THE WINNING NICHES: High-Stakes Tech/Aerospace & Extreme Apex Showdowns
# ==============================================================================
NICHE_A_KEYWORDS = [
    "spacex", "tesla", "starlink", "nasa", "starship", "elon musk",
    "falcon 9", "artemis", "blue origin", "space race", "boeing space",
    "faa spacex", "superheavy", "propulsion", "launch pad", "astronaut",
    "moon base", "mars colony", "orbital", "humanoid robot", "ai chip",
    "isro", "cnsa", "rocket launch", "spacecraft"
]

NICHE_B_KEYWORDS = [
    "tiger", "lion", "croc", "crocodile", "alligator", "buffalo", "orca",
    "killer whale", "shark", "great white", "deep ocean", "mariana trench",
    "squid", "colossal squid", "predator", "apex predator", "abyssal", "leopard",
    "hyena", "cheetah", "anaconda", "python", "komodo dragon", "grizzly bear",
    "polar bear", "wolf pack", "sea monster", "megalodon", "anglerfish",
    "viperfish", "chimera", "abyss", "deep sea creature", "apex showdown",
    "river ambush", "deadly duel"
]

def classify_niche(text: str) -> str:
    """Classify text into Niche A, Niche B, or Unknown."""
    t = str(text or "").lower()
    score_a = sum(1 for kw in NICHE_A_KEYWORDS if kw in t)
    score_b = sum(1 for kw in NICHE_B_KEYWORDS if kw in t)
    if score_a > score_b and score_a > 0:
        return "Niche A"
    elif score_b > score_a and score_b > 0:
        return "Niche B"
    return "Unknown"



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
    """Fetch hot topics from specified subreddits via RSS feed."""
    topics = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    for sub in subreddits:
        logger.info(f"Fetching hot topics from r/{sub}...")
        url = f"https://www.reddit.com/r/{sub}/hot/.rss"
        try:
            feed = feedparser.parse(url, request_headers=headers)
            if hasattr(feed, 'entries') and feed.entries:
                for entry in feed.entries[:10]:
                    title = entry.title
                    if len(title.split()) > 3:
                        topics.append({
                            "title": title.strip(),
                            "source": f"Reddit r/{sub}",
                            "score_signal": 60
                        })
                logger.info(f"Fetched {len(topics)} topics from r/{sub}.")
        except Exception as e:
            logger.warning(f"Error fetching Reddit r/{sub}: {e}")
            
    logger.info(f"Fetched {len(topics)} topics total from Reddit RSS.")
    return topics


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def fetch_google_news() -> list[dict]:
    """Fetch top headlines from Google News RSS feed."""
    logger.info("Fetching Google News headlines...")
    url = "https://news.google.com/rss/search?q=(artificial+intelligence+OR+robotics+OR+biotechnology+OR+genetics+OR+biology+OR+zoology+OR+evolutionary+biology+OR+quantum+OR+astronomy+OR+exoplanet)&hl=en-US&gl=US&ceid=US:en"
    
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


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def fetch_rss_feed(url: str, source_name: str, base_score: int = 40) -> list[dict]:
    """Helper to parse a standard RSS feed and return list of topics."""
    logger.info(f"Fetching RSS feed from {source_name}...")
    topics = []
    try:
        feed = feedparser.parse(url)
        if hasattr(feed, 'entries') and feed.entries:
            for entry in feed.entries:
                title = entry.title
                if " - " in title:
                    title = title.rsplit(" - ", 1)[0]
                topics.append({
                    "title": title.strip(),
                    "source": source_name,
                    "score_signal": base_score
                })
        logger.info(f"Fetched {len(topics)} topics from {source_name}.")
    except Exception as e:
        logger.warning(f"Error fetching RSS from {source_name}: {e}")
    return topics


@retry(max_attempts=3, delay=2.0, backoff=2.0)
def fetch_wikipedia_trending() -> list[dict]:
    """Fetch top english wikipedia pageviews for yesterday."""
    logger.info("Fetching Wikipedia Trending pages...")
    topics = []
    headers = {
        "User-Agent": "TheShortestOrbitV3/1.0 (contact@theshortestorbit.com)"
    }
    from datetime import datetime, timedelta
    yesterday = (datetime.now() - timedelta(days=1))
    year = yesterday.strftime("%Y")
    month = yesterday.strftime("%m")
    day = yesterday.strftime("%d")
    
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{year}/{month}/{day}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("items", [{}])[0].get("articles", [])
            skipped_keywords = ["main_page", "special:", "search", "wikipedia:", "portal:", "file:", "help:", "talk:"]
            for art in articles[:100]:
                title = art.get("article", "").replace("_", " ")
                if any(kw in title.lower() for kw in skipped_keywords):
                    continue
                science_keywords = ["space", "universe", "planet", "galaxy", "nasa", "spacex", "telescope", "physics", 
                                    "quantum", "ai", "robot", "intelligence", "biology", "dna", "chemistry", "star", 
                                    "fusion", "nature", "evolution", "molecule", "earth", "moon", "mars"]
                if any(kw in title.lower() for kw in science_keywords):
                    topics.append({
                        "title": f"Wikipedia Trend: {title}",
                        "source": "Wikipedia Trending",
                        "score_signal": min(art.get("views", 0) // 1000, 100)
                    })
    except Exception as e:
        logger.error(f"Error fetching Wikipedia Trending: {e}")
    logger.info(f"Fetched {len(topics)} topics from Wikipedia.")
    return topics


def collect_all_topics() -> list[dict]:
    """Gather topics from all 15 sources and deduplicate them."""
    settings = load_settings()
    subreddits = get_setting('trending', 'subreddits', ['space', 'science', 'Futurology', 'artificial', 'nature', 'biology'])
    geo = get_setting('trending', 'google_trends_geo', 'US')
    
    all_topics = []
    
    # 1. Google Trends
    try:
        all_topics.extend(fetch_google_trends(geo))
    except Exception as e:
        logger.error(f"Failed to fetch Google Trends: {e}")
        
    # 2. Reddit subreddits
    try:
        all_topics.extend(fetch_reddit_topics(subreddits))
    except Exception as e:
        logger.error(f"Failed to fetch Reddit topics: {e}")
        
    # 3. Google News
    try:
        all_topics.extend(fetch_google_news())
    except Exception as e:
        logger.error(f"Failed to fetch Google News: {e}")

    # Helper function to safely extend RSS feeds
    def safe_fetch_rss(url: str, source_name: str, score: float):
        try:
            feeds = fetch_rss_feed(url, source_name, score)
            all_topics.extend(feeds)
        except Exception as err:
            logger.error(f"Failed to fetch RSS feed for {source_name} ({url}): {err}")

    # 4. NASA RSS feed
    safe_fetch_rss("https://www.nasa.gov/feed/", "NASA News", 55)
    
    # 5. ESA Space Science
    safe_fetch_rss("https://www.esa.int/rssfeed/Our_Activities/Space_Science", "ESA Space Science", 50)
    
    # 6. SpaceX (via Google News RSS search)
    safe_fetch_rss("https://news.google.com/rss/search?q=SpaceX&hl=en-US&gl=US&ceid=US:en", "SpaceX", 60)
    
    # 7. MIT News
    safe_fetch_rss("https://news.mit.edu/rss/feed", "MIT News", 50)
    
    # 8. Nature journal
    safe_fetch_rss("https://www.nature.com/nature.rss", "Nature Journal", 55)
    
    # 9 & 10. Science Daily (Space & AI)
    safe_fetch_rss("https://www.sciencedaily.com/rss/space_time/astronomy.xml", "ScienceDaily Space", 45)
    safe_fetch_rss("https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", "ScienceDaily AI", 50)
    
    # 11 & 12. arXiv (AI & Astro)
    safe_fetch_rss("https://export.arxiv.org/rss/cs.AI", "arXiv AI", 45)
    safe_fetch_rss("https://export.arxiv.org/rss/astro-ph", "arXiv Astro", 45)
    
    # 13. OpenAI Blog (via Google News keyword)
    safe_fetch_rss("https://news.google.com/rss/search?q=OpenAI&hl=en-US&gl=US&ceid=US:en", "OpenAI", 60)
    
    # 14. Anthropic Blog (via Google News keyword)
    safe_fetch_rss("https://news.google.com/rss/search?q=Anthropic&hl=en-US&gl=US&ceid=US:en", "Anthropic", 55)
    
    # Winning Niche A Feeds (High-Stakes Tech & Aerospace Rivalries):
    safe_fetch_rss("https://news.google.com/rss/search?q=(SpaceX+OR+Starlink+OR+Tesla+OR+NASA+OR+%22Blue+Origin%22+OR+Artemis)&hl=en-US&gl=US&ceid=US:en", "Niche A: Aerospace News", 75)
    safe_fetch_rss("https://news.google.com/rss/search?q=(%22SpaceX+vs%22+OR+%22Tesla+vs%22+OR+%22NASA+vs%22+OR+%22Starship+launch%22+OR+%22FAA+SpaceX%22)&hl=en-US&gl=US&ceid=US:en", "Niche A: Tech Rivalries", 75)

    # Winning Niche B Feeds (Extreme Apex Showdowns & Deep Ocean):
    safe_fetch_rss("https://news.google.com/rss/search?q=(%22apex+predator%22+OR+%22tiger%22+OR+%22lion+vs%22+OR+%22crocodile%22+OR+%22orca%22+OR+%22great+white+shark%22+OR+%22buffalo+herd%22)&hl=en-US&gl=US&ceid=US:en", "Niche B: Apex Showdowns", 75)
    safe_fetch_rss("https://news.google.com/rss/search?q=(%22deep+ocean%22+OR+%22mariana+trench%22+OR+%22colossal+squid%22+OR+%22abyssal+zone%22+OR+%22deep+sea+creature%22)&hl=en-US&gl=US&ceid=US:en", "Niche B: Deep Ocean", 75)

    # 15. DeepMind, Microsoft AI, and Wikipedia Trending
    safe_fetch_rss("https://news.google.com/rss/search?q=%22Google+DeepMind%22&hl=en-US&gl=US&ceid=US:en", "DeepMind", 60)
    safe_fetch_rss("https://news.google.com/rss/search?q=%22Microsoft+AI%22&hl=en-US&gl=US&ceid=US:en", "Microsoft AI", 55)
    # Wikipedia Trending disabled to prevent repetitive Wikipedia topics
        
    junk_keywords = ["rule #", "in regards to rule", "megathread", "weekly discussion", "submission rules", "moderator", "daily thread", "subreddit rules", "read before posting"]
    
    # Deduplicate based on title similarity/exact match & filter junk
    seen_titles = set()
    unique_topics = []
    
    for t in all_topics:
        norm_title = t["title"].strip().lower()
        if any(junk in norm_title for junk in junk_keywords):
            continue
        if norm_title not in seen_titles:
            seen_titles.add(norm_title)
            unique_topics.append(t)
            
    logger.info(f"Total unique topics collected across 15 sources: {len(unique_topics)}")
    return unique_topics


def get_recent_uploaded_titles() -> list[str]:
    """Retrieve the titles of the last 15 uploaded videos from the YouTube channel and database."""
    titles = []
    try:
        from python.upload_youtube import get_authenticated_service
        youtube = get_authenticated_service()
        if youtube:
            channels_response = youtube.channels().list(
                mine=True,
                part="contentDetails"
            ).execute()
            
            if channels_response.get("items"):
                uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
                playlist_response = youtube.playlistItems().list(
                    playlistId=uploads_playlist_id,
                    part="snippet",
                    maxResults=15
                ).execute()
                
                for item in playlist_response.get("items", []):
                    titles.append(item["snippet"]["title"])
                logger.info(f"Fetched {len(titles)} recent uploaded titles from channel.")
    except Exception as e:
        logger.warning(f"Could not fetch recent uploaded titles from YouTube: {e}")
        
    # Also fetch recent generated titles from the database to exclude failed/generating ones
    try:
        from utils.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        db_titles = [row[0] for row in cursor.execute("SELECT title FROM videos ORDER BY id DESC LIMIT 20").fetchall() if row[0]]
        conn.close()
        titles.extend(db_titles)
        logger.info(f"Fetched {len(db_titles)} recent titles from central database to prevent duplicates/retries.")
    except Exception as dbe:
        logger.warning(f"Could not fetch recent titles from database: {dbe}")
        
    # Unique titles list preserving order (case-insensitive deduplication)
    seen = set()
    unique_titles = []
    for t in titles:
        norm = t.strip().lower()
        if norm not in seen:
            seen.add(norm)
            unique_titles.append(t)
            
    return unique_titles


def select_best_topic(topics: list[dict], recent_titles: list[str] = None) -> dict:
    """Send topics to Groq LLM to score angles and select the best candidate strictly alternating between Winning Niches."""
    if not topics:
        return {
            "selected_topic": "Tiger vs Hidden Croc: Jungle Clash",
            "viral_angle": "Default fallback topic",
            "hook_line": "Could an apex tiger survive a mega crocodile ambush?",
            "niche": "Niche B",
            "source": "Fallback",
            "trend_score": 50.0,
            "competition_score": 50.0,
            "audience_interest": 50.0,
            "evergreen_score": 50.0,
            "virality_score": 50.0,
            "education_score": 50.0,
            "ctr_prediction": 50.0,
            "retention_prediction": 50.0,
            "overall_growth_score": 50.0
        }
        
    api_key = get_groq_key()
    model = get_setting('llm', 'model', 'openai/gpt-oss-120b')
    client = Groq(api_key=api_key)
    
    # Detect most recent winning niche to strictly alternate:
    last_detected_niche = None
    if recent_titles:
        for r_title in recent_titles:
            n = classify_niche(r_title)
            if n in ["Niche A", "Niche B"]:
                last_detected_niche = n
                logger.info(f"Most recent uploaded niche detected: {last_detected_niche} ('{r_title}')")
                break
                
    if last_detected_niche == "Niche A":
        target_niche = "Niche B"
        target_niche_title = "Niche B: Extreme Apex Showdowns (Tiger, Lion vs Croc, Deep Ocean)"
    elif last_detected_niche == "Niche B":
        target_niche = "Niche A"
        target_niche_title = "Niche A: High-Stakes Tech & Aerospace Rivalries (SpaceX, Tesla, Starlink, NASA)"
    else:
        # Default starting point: Niche B (since recent video was SpaceX Niche A)
        target_niche = "Niche B"
        target_niche_title = "Niche B: Extreme Apex Showdowns (Tiger, Lion vs Croc, Deep Ocean)"

    logger.info(f"Target Winning Niche locked for this generation: {target_niche_title}")

    # Prioritize candidates belonging to target_niche
    target_kws = NICHE_B_KEYWORDS if target_niche == "Niche B" else NICHE_A_KEYWORDS

    def get_candidate_priority(t: dict) -> float:
        title_text = t.get("title", "").lower()
        target_match = any(kw in title_text for kw in target_kws)
        either_match = classify_niche(title_text) in ["Niche A", "Niche B"]
        boost = 150.0 if target_match else (75.0 if either_match else 0.0)
        return boost + float(t.get("score_signal", 50))

    topics_sorted = sorted(topics, key=get_candidate_priority, reverse=True)
    
    # Pre-filter topics against recent uploaded titles (last 20) to eliminate repeating topics before prompt creation
    stop_words = {"space", "future", "world", "first", "about", "could", "would", "what", "where", "which", "there", "their", "hidden", "truth", "secret", "video", "shorts", "revealed", "shock", "shocking", "exposed", "eating", "swallows", "whole"}
    filtered_topics = []
    if recent_titles:
        for t in topics_sorted:
            t_words = set(re.findall(r'[a-zA-Z]{4,}', t['title'].lower())) - stop_words
            overlap_found = False
            for r_title in recent_titles[:20]:
                r_words = set(re.findall(r'[a-zA-Z]{4,}', r_title.lower())) - stop_words
                if len(t_words & r_words) >= 2:
                    overlap_found = True
                    break
            if not overlap_found:
                filtered_topics.append(t)
    else:
        filtered_topics = topics_sorted
        
    # Strictly filter candidates belonging to the target winning niche
    niche_candidates = [t for t in filtered_topics if classify_niche(t["title"]) == target_niche]
    if len(niche_candidates) >= 4:
        top_candidates = niche_candidates[:14]
        logger.info(f"Filtered {len(niche_candidates)} candidates strictly belonging to {target_niche}.")
    else:
        top_candidates = [t for t in filtered_topics if classify_niche(t["title"]) in ["Niche A", "Niche B"]][:14] or filtered_topics[:14]
    candidate_list_str = "\n".join([f"- {t['title']} (Source: {t['source']})" for t in top_candidates])
    
    system_prompt = (
        f"""SYSTEM PROMPT - The Shortest Orbit: Winning Niches Viral Engine

You are the Lead Creative Director and Viral Strategist for 'The Shortest Orbit'.
The channel focuses strictly on 2 proven high-performing winning niches:
- Niche A: High-Stakes Tech & Aerospace Rivalries (SpaceX, Tesla, Starlink, NASA, Artemis, Moon/Mars race, AI robotics).
- Niche B: Extreme Apex Showdowns (Tiger, Lion vs Croc, Buffalo, Orcas, Deep Ocean / Mariana Trench monsters).

MANDATORY NICHE TARGET FOR THIS VIDEO:
===> {target_niche_title} <===

Your objective: Extract and formulate the single most shocking, high-CTR viral Shorts concept that strictly belongs to {target_niche}.

NICHE-SPECIFIC DIRECTIVES:
- When targeting Niche A (High-Stakes Tech & Aerospace Rivalries):
  Spotlight billionaire clashes (Elon Musk vs FAA/NASA), Falcon 9/Starship launch anomalies, Starlink orbital dominance, lunar base races (USA vs China), or autonomous AI robotics.
- When targeting Niche B (Extreme Apex Showdowns & Deep Ocean):
  Spotlight brutal predator clashes (Tiger in epic escapes, Lion vs Crocodile river ambushes, Cape Buffalo vengeance, Orca pods outsmarting Great Whites), or Mariana Trench alien-like leviathans surviving impossible pressure.

Input: a list of recent news headlines/summaries.
Output: valid JSON object with a single 'topics' key containing an array of objects:

{{
  "topics": [
    {{
      "source_headline": "the original news item this is based on",
      "niche": "{target_niche}",
      "viral_angle": "the ONE most surprising, jaw-dropping fact hiding in this story - stated in plain language a 12-year-old would understand",
      "hook_line": "first 2 seconds - must sound almost unbelievable, framed as a question or shocking observation. MUST be a scientifically true statement, NEVER fabricate statistics, numbers, or percentages.",
      "why_it_could_go_viral": "1 sentence: what makes people want to comment, share, or argue about this",
      "interest_score": 9.0,
      "conflict_score": 9.5,
      "novelty_score": 8.5,
      "curiosity_score": 9.0,
      "stakes_score": 9.5,
      "brand_fit_score": 10.0,
      "risk_flag": "none"
    }}
  ]
}}

RULES:
1. Reject stories that cannot be simplified without becoming misleading.
2. Hook_line MUST sound natural, conversational, and intriguing. DO NOT start hooks with 'EXPOSED:' or 'UNCOVERED:'.
3. STRICT WINNING NICHE COMPLIANCE: The selected concept MUST belong to {target_niche_title}.
4. HOOK HONESTY RULE: The hook_line must be grounded in real events or verified science. Do NOT invent numbers."""
    )
    
    # Load audience feedback insights if available
    insights_context = ""
    insights_path = DATA_DIR / "self_learning_insights.json"
    if insights_path.exists():
        try:
            with open(insights_path, "r", encoding="utf-8") as f:
                insights_data = json.load(f)
            hi_niches = insights_data.get("high_interest_niches", [])
            boost_kws = insights_data.get("algorithm_boost_keywords", [])
            if hi_niches or boost_kws:
                niche_str = ", ".join(hi_niches[:5])
                kw_str = ", ".join(boost_kws[:6])
                insights_context = f"\nAUDIENCE ENGAGEMENT INSIGHTS:\n- High-Interest Niches: {niche_str}\n- High-Velocity Keywords: {kw_str}\n"
                logger.info("Injected audience performance insights into topic discovery prompt.")
        except Exception as ie:
            logger.warning(f"Could not load self-learning insights: {ie}")

    user_prompt = (
        f"Extract and score viral angles strictly for {target_niche_title} from these candidates:\n\n"
        f"{candidate_list_str}{insights_context}\n\n"
        f"CRITICAL INSTRUCTION: Your output MUST focus on {target_niche} to maintain the 2-niche daily rotation!"
    )
    
    logger.info("Calling Groq LLM to scan and score viral topics...")
    try:
        from utils.config import call_groq_with_fallback
        completion = call_groq_with_fallback(
            client=client,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            initial_model=model,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        response_text = completion.choices[0].message.content
        from utils.helpers import extract_json_from_llm
        result_dict = extract_json_from_llm(response_text)
        concepts = result_dict if isinstance(result_dict, list) else result_dict.get("topics", result_dict.get("concepts", []))
        if not concepts and isinstance(result_dict, dict):
            concepts = [result_dict]
            
        safe_concepts = []
        for c in concepts:
            risk = c.get("risk_flag", "")
            if risk and str(risk).lower() not in ["none", "null", "false", "no", ""]:
                continue
            c_text = (str(c.get("source_headline", "")) + " " + str(c.get("viral_angle", "")) + " " + str(c.get("hook_line", ""))).lower()
            if "wikipedia" in c_text:
                logger.info(f"Filtered out Wikipedia topic to prevent repetition: {c.get('source_headline')}")
                continue
            
            # Anti-repetition: Reject candidate if 2 or more distinct keywords overlap with any of the last 20 video titles
            if recent_titles:
# (re imported at top)
                c_words = set(re.findall(r'[a-z]{4,}', c_text))
                stop_words = {"space", "future", "world", "first", "about", "could", "would", "what", "where", "which", "there", "their", "hidden", "truth", "secret", "video", "shorts", "revealed", "shock", "shocking", "exposed", "eating", "swallows", "whole"}
                meaningful_c_words = c_words - stop_words
                is_duplicate = False
                for r_title in recent_titles[:20]:
                    r_words = set(re.findall(r'[a-z]{4,}', r_title.lower())) - stop_words
                    overlap = meaningful_c_words & r_words
                    if len(overlap) >= 2:
                        logger.warning(f"Filtered out candidate '{c.get('source_headline')}' due to repeated keywords {overlap} with recent video '{r_title}'")
                        is_duplicate = True
                        break
                if is_duplicate:
                    continue

            safe_concepts.append(c)
                
        if not safe_concepts:
            # Fallback to the concept with the least overlap rather than blindly accepting duplicates
            safe_concepts = [c for c in concepts if c.get("risk_flag") in ["none", "null", "false", "no", ""]] or (concepts[:1] if concepts else [{}])
            
        # Score each candidate and write to database
        db_candidates = []
        for c in safe_concepts:
            i_score = float(c.get("interest_score", c.get("audience_interest", 8.0)))
            c_score = float(c.get("conflict_score", 8.0))
            n_score = float(c.get("novelty_score", 8.0))
            q_score = float(c.get("curiosity_score", 8.0))
            s_score = float(c.get("stakes_score", 8.0))
            b_score = float(c.get("brand_fit_score", 9.0))
            
            # Normalize to 0-10 scale if on 0-100
            if i_score > 10.0: i_score /= 10.0
            if c_score > 10.0: c_score /= 10.0
            if n_score > 10.0: n_score /= 10.0
            if q_score > 10.0: q_score /= 10.0
            if s_score > 10.0: s_score /= 10.0
            if b_score > 10.0: b_score /= 10.0
            
            # V4 TopicScore Formula: 0.25(I) + 0.20(C) + 0.20(N) + 0.15(Q) + 0.10(S) + 0.10(B)
            topic_score = (0.25 * i_score) + (0.20 * c_score) + (0.20 * n_score) + (0.15 * q_score) + (0.10 * s_score) + (0.10 * b_score)
            
            # V4 Historical Winner Bonus: 0.80 * TopicScore + 0.20 * HistoricalSimilarityScore
            hist_sim_score = float(c.get("historical_similarity_score", 8.0))
            if hist_sim_score > 10.0: hist_sim_score /= 10.0
            
            final_topic_score = (topic_score * 0.80) + (hist_sim_score * 0.20)
            overall_growth_score = final_topic_score * 10.0  # scale to 100 for legacy compatibility
            
            # Apply priority boost for Target Winning Niche
            text_to_check = (str(c.get("viral_angle", "")) + " " + str(c.get("hook_line", "")) + " " + str(c.get("source_headline", ""))).lower()
            c_niche = classify_niche(text_to_check)
            c["niche"] = c_niche if c_niche in ["Niche A", "Niche B"] else target_niche
            
            if c_niche == target_niche:
                overall_growth_score = min(overall_growth_score + 35.0, 100.0)
            elif c_niche in ["Niche A", "Niche B"]:
                overall_growth_score = min(overall_growth_score + 15.0, 100.0)
            else:
                overall_growth_score = max(overall_growth_score - 15.0, 10.0)
                
            c["trend_score"] = float(c.get("trend_score", 80.0))
            c["competition_score"] = float(c.get("competition_score", 80.0))
            c["audience_interest"] = float(c.get("audience_interest", 85.0))
            c["evergreen_score"] = float(c.get("evergreen_score", 80.0))
            c["virality_score"] = float(c.get("virality_score", 85.0))
            c["education_score"] = float(c.get("education_score", 80.0))
            c["ctr_prediction"] = float(c.get("ctr_prediction", 85.0))
            c["retention_prediction"] = float(c.get("retention_prediction", 85.0))
            c["overall_growth_score"] = overall_growth_score
            hook = str(c.get("hook_line") or "").strip()
            angle = str(c.get("viral_angle") or "").strip()
            fallback_title = top_candidates[0]["title"] if top_candidates else "Space & AI Frontier Discovery"
            if not hook or hook.lower() in ["none", "null", ""]:
                hook = f"Did you know about {fallback_title}?"
            if not angle or angle.lower() in ["none", "null", ""]:
                angle = fallback_title

            c["hook_line"] = hook
            c["viral_angle"] = angle
            c["selected_topic"] = f"{hook} - {angle}"
            c["source_headline"] = str(c.get("source_headline") or fallback_title)
            c["source"] = c["source_headline"]
            
            db_candidates.append(c)
            
        # Sort by overall growth score
        db_candidates.sort(key=lambda x: x.get("overall_growth_score", 0.0), reverse=True)
        best_concept = db_candidates[0]
        
        # Save all evaluated candidates into the database
        conn = get_automation_conn()
        try:
            cursor = conn.cursor()
            for cand in db_candidates:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO topics (
                            title, source, trend_score, engagement_potential, retention_potential,
                            competition_score, audience_interest, evergreen_score, virality_score,
                            education_score, ctr_prediction, retention_prediction, overall_growth_score, status
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                    """, (
                        cand.get("selected_topic"),
                        cand.get("source_headline"),
                        float(cand.get("trend_score", 50.0)),
                        float(cand.get("audience_interest", 50.0)),
                        float(cand.get("retention_prediction", 50.0)),
                        float(cand.get("competition_score", 50.0)),
                        float(cand.get("audience_interest", 50.0)),
                        float(cand.get("evergreen_score", 50.0)),
                        float(cand.get("virality_score", 50.0)),
                        float(cand.get("education_score", 50.0)),
                        float(cand.get("ctr_prediction", 50.0)),
                        float(cand.get("retention_prediction", 50.0)),
                        float(cand.get("overall_growth_score", 50.0))
                    ))
                except Exception as e:
                    logger.warning(f"Database topic insertion error: {e}")
            cursor.execute("UPDATE topics SET status = 'used' WHERE title = ?", (best_concept.get("selected_topic"),))
            conn.commit()
        finally:
            conn.close()
            
        logger.info(f"Groq selected and scored topic. Growth Score: {best_concept.get('overall_growth_score'):.2f} | Hook: '{best_concept.get('hook_line')}'")
        
        return best_concept
        
    except Exception as e:
        logger.error(f"Error calling Groq for topic selection: {e}")
        best_fallback = top_candidates[0] if top_candidates else {"title": "Default space mystery"}
        return {
            "selected_topic": best_fallback.get("title", "Default space mystery"),
            "viral_angle": best_fallback.get("title", "Default space mystery"),
            "hook_line": "Did you know about this?",
            "source": best_fallback.get("source", "Fallback"),
            "trend_score": 50.0,
            "competition_score": 50.0,
            "audience_interest": 50.0,
            "evergreen_score": 50.0,
            "virality_score": 50.0,
            "education_score": 50.0,
            "ctr_prediction": 50.0,
            "retention_prediction": 50.0,
            "overall_growth_score": 50.0
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
        "niche": selected.get("niche", "Niche B"),
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