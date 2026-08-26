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
from automation.database.connection import get_automation_conn

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
    
    # 15. DeepMind, Microsoft AI, and Wikipedia Trending
    safe_fetch_rss("https://news.google.com/rss/search?q=%22Google+DeepMind%22&hl=en-US&gl=US&ceid=US:en", "DeepMind", 60)
    safe_fetch_rss("https://news.google.com/rss/search?q=%22Microsoft+AI%22&hl=en-US&gl=US&ceid=US:en", "Microsoft AI", 55)
    try:
        all_topics.extend(fetch_wikipedia_trending())
    except Exception as e:
        logger.error(f"Failed to fetch Wikipedia Trending: {e}")
        logger.error(f"Failed to fetch Wikipedia Trending: {e}")
        
    # Deduplicate based on title similarity/exact match
    seen_titles = set()
    unique_topics = []
    
    for t in all_topics:
        norm_title = t["title"].strip().lower()
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
    """Send topics to Groq LLM to score angles and select the best candidate."""
    if not topics:
        return {
            "selected_topic": "Scientists just found something hiding in our solar system.",
            "viral_angle": "Default fallback topic",
            "hook_line": "Scientists just found something hiding in our solar system.",
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
    
    # Take top 12 candidates to optimize token usage
    topics_sorted = sorted(topics, key=lambda x: x["score_signal"], reverse=True)
    top_candidates = topics_sorted[:12]
    
    candidate_list_str = "\n".join([f"- {t['title']} (Source: {t['source']})" for t in top_candidates])
    
    system_prompt = (
        "SYSTEM PROMPT — The Shortest Orbit: Viral Topic Selector v3.1 (Global Space Race Edition)\n\n"
        "You take raw current news items about space, science, or AI and convert "
        "each into a viral-ready Shorts concept. Your job is to extract the single "
        "most shocking, curiosity-driving angle inside it that a general audience would stop scrolling for.\n\n"
        "PRIORITY HIERARCHY:\n"
        "1. Mind-Blowing Nature & Earth Wonders (extreme weather, bioluminescent oceans, volcanic phenomenon, mysterious creature adaptations, unmapped natural secrets)\n"
        "2. Breaking space news & discoveries (James Webb, exoplanets, black holes, solar flares, asteroid mining)\n"
        "3. Major technological & mission announcements from ANY country (ISRO, NASA, ESA, JAXA, CNSA)\n"
        "4. Deep Ocean & Earth Mysteries (Mariana Trench anomalies, Antarctica declassified findings, geothermal vents)\n"
        "5. Global technological competition & rivalries\n"
        "6. AI breakthroughs & human evolution (Neuralink, humanoid robotics, autonomous exploration)\n"
        "7. Future planetary survival & extreme habitats\n"
        "8. Evergreen educational wonders (Earth's magnetic field, deepest depths, alien-like Earth ecosystems)\n\n"
        "CRITICAL DIVERSITY RULE: You MUST rotate themes between Nature/Earth Wonders, Deep Ocean mysteries, Space discoveries, and Mega-Technology. VARIETY IS KING for explosive algorithm growth.\n\n"
        "HIGH-VIRAL TOPIC THEMES TO MONITOR & GENERATE:\n"
        "- Nature & Earth Wonders: Extreme natural forces, monster waves, volcanic eruptions, bioluminescent sea life, aurora borealis, deepest cave systems, ancient frozen secrets in ice caps, nature vs modern engineering.\n"
        "- Global Space Race: USA vs China space developments, India's latest ISRO missions (Chandrayaan, Gaganyaan), Artemis Program, Moon/Mars race, Deep-space exploration, Habitable worlds.\n"
        "- Scientific Discoveries: Exoplanets, black holes, dark matter, dark energy, Fast Radio Bursts (FRBs), supernovae, telescope discoveries (JWST), extreme planetary conditions.\n"
        "- Future Technologies: AI in scientific discovery, humanoid robots, Moon bases, deep-sea exploration subs, autonomous systems.\n\n"
        "TREND DETECTION:\n"
        "Detect and prioritize breaking launches, mission delays, successes, failures, spacecraft anomalies, major funding announcements, international agreements, astronaut missions, space policy changes, historic milestones, and record-breaking achievements.\n\n"
        "Input: a list of recent news headlines/summaries.\n"
        "Output: valid JSON object with a single 'topics' key containing an array of objects:\n\n"
        "{\n"
        "  \"topics\": [\n"
        "    {\n"
        "      \"source_headline\": \"the original news item this is based on\",\n"
        "      \"viral_angle\": \"the ONE most surprising fact hiding in this story — stated in plain language a 12-year-old would understand\",\n"
        "      \"hook_line\": \"first 2 seconds — must sound almost unbelievable, framed as a question or shocking statement. MUST be a scientifically true statement, NEVER fabricate statistics, numbers, or percentages.\",\n"
        "      \"why_it_could_go_viral\": \"1 sentence: what makes people want to comment, share, or argue about this\",\n"
        "      \"interest_score\": 8.5, // 0.0 to 10.0 scale (Public Interest)\n"
        "      \"conflict_score\": 9.0, // 0.0 to 10.0 scale (Geopolitical / Space Race Conflict)\n"
        "      \"novelty_score\": 8.0, // 0.0 to 10.0 scale (Freshness / Uniqueness)\n"
        "      \"curiosity_score\": 9.0, // 0.0 to 10.0 scale (Immediate Question in Viewer Mind)\n"
        "      \"stakes_score\": 9.5, // 0.0 to 10.0 scale (Money, Power, Future Consequence)\n"
        "      \"brand_fit_score\": 10.0, // 0.0 to 10.0 scale (Fit for The Shortest Orbit: Space + AI + Future Tech)\n"
        "      \"risk_flag\": \"note if this topic is too technical, too uncertain/early-stage research, or too niche to simplify honestly — flag rather than force it\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "RULES:\n"
        "1. Reject stories that can't be simplified without becoming misleading. Skip them rather than oversimplify.\n"
        "2. Hook_line MUST use powerful, high-emotion viral power words like 'Uncovered', 'Exposed', 'Game Changer', 'Forbidden', or 'Breaking'.\n"
        "3. STRICT SPACE FRONTIER NICHE INTERSECTION: The chosen topic MUST strictly combine Countries/Agencies + Space Exploration + AI + Global Competition. Every video must connect these elements naturally. Reject purely AI-only, space-only, country-politics-only, or military-only news. Target a weight distribution of 70% Space-primary (space exploration assisted by AI) and 30% AI-primary (AI breakthroughs supporting space programs) across your selections.\n"
        "4. STRICT BAN: Do NOT select biology, wildlife, general political news, geopolitical wars, financial stocks, lifestyle/beauty hacks, or speculative pop-psychology.\n"
        "5. HOOK HONESTY RULE: The hook_line must be a 100% true fact. Do NOT invent numbers.\n"
        "6. FACTUAL TRUTH GATING: Do NOT select speculative rumors, clickbait conspiracy theories, or fake-sounding news. Only select topics backed by solid scientific reports, official announcements, or reputable journal publications. Reject sensationalized headlines that claim a company's product did something illegal or highly unlikely."
    )
    
    user_prompt = f"Extract and score viral angles from these raw headlines:\n\n{candidate_list_str}"
    
    if recent_titles:
        recent_titles_str = "\n".join([f"- {t}" for t in recent_titles])
        user_prompt += (
            f"\n\nHere are the recently uploaded videos on the channel:\n{recent_titles_str}\n\n"
            "CRITICAL: Do NOT select any topic that overlaps or is similar to the above list. "
            "Analyze the above list and select the next topic category to move the channel closer to a strict "
            "70% Space-primary / 30% AI-primary global publishing ratio within the Space Frontier intersection."
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
            temperature=0.7
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
            if not risk or str(risk).lower() in ["none", "null", "false", "no", ""]:
                safe_concepts.append(c)
                
        if not safe_concepts:
            safe_concepts = concepts if concepts else [{}]
            
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
            
            # Apply priority boost for strict Space Frontier niche (Country + Space + AI)
            text_to_check = (c.get("viral_angle", "") + " " + c.get("hook_line", "")).lower()
            countries = ["usa", "united states", "china", "india", "japan", "russia", "south korea", "uae", "united arab emirates", "israel", "european union", "eu", "canada", "australia", "saudi arabia", "türkiye", "turkey", "brazil", "nasa", "isro", "cnsa", "esa", "jaxa", "roscosmos", "kari", "csa"]
            space_kws = ["space", "exploration", "rocket", "launch", "landing", "moon", "mars", "satellite", "exoplanet", "telescope", "black hole", "asteroid", "orbit", "astronaut", "artemis", "starship", "spacex", "blue origin", "rocket lab", "hail mary"]
            ai_kws = ["ai", "artificial intelligence", "robot", "autonomous", "machine learning", "neural network", "algorithm", "automation"]
            
            has_country = any(c_kw in text_to_check for c_kw in countries)
            has_space = any(s_kw in text_to_check for s_kw in space_kws)
            has_ai = any(a_kw in text_to_check for a_kw in ai_kws)
            
            if has_country and has_space and has_ai:
                overall_growth_score = min(overall_growth_score + 25.0, 100.0)
                
            c["trend_score"] = float(c.get("trend_score", 80.0))
            c["competition_score"] = float(c.get("competition_score", 80.0))
            c["audience_interest"] = float(c.get("audience_interest", 85.0))
            c["evergreen_score"] = float(c.get("evergreen_score", 80.0))
            c["virality_score"] = float(c.get("virality_score", 85.0))
            c["education_score"] = float(c.get("education_score", 80.0))
            c["ctr_prediction"] = float(c.get("ctr_prediction", 85.0))
            c["retention_prediction"] = float(c.get("retention_prediction", 85.0))
            c["overall_growth_score"] = overall_growth_score
            c["selected_topic"] = f"{c.get('hook_line')} {c.get('viral_angle')}"
            c["source_headline"] = c.get("source_headline", best_fallback["title"] if 'best_fallback' in locals() else "Unknown Source")
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
