import json
import sqlite3
import sys
import threading
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.database import DB_PATH, get_connection
from utils.paths import DATA_DIR, PROJECT_ROOT
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger("dashboard_server")

def calculate_growth_forecasts(conn, current_subs, current_views, current_watch_hours):
    # Retrieve all historic snapshots
    cursor = conn.cursor()
    cursor.execute("SELECT date, subscribers, shorts_views, watch_hours FROM monetization_snapshots ORDER BY date ASC")
    rows = cursor.fetchall()
    
    # Defaults
    daily_subs_rate = 1.0  # 1 sub per day default
    daily_views_rate = 150.0  # 150 views per day default
    
    # Calculate views growth from trend_data if available
    cursor.execute("""
        SELECT date, SUM(views) as views
        FROM (
            SELECT date, video_id, MAX(views) as views
            FROM analytics
            GROUP BY date, video_id
        )
        GROUP BY date
        ORDER BY date ASC
    """)
    trend_rows = cursor.fetchall()
    if len(trend_rows) >= 2:
        try:
            first_views = trend_rows[0]["views"] or 0
            last_views = trend_rows[-1]["views"] or 0
            
            d1 = datetime.strptime(trend_rows[0]["date"], "%Y-%m-%d")
            d2 = datetime.strptime(trend_rows[-1]["date"], "%Y-%m-%d")
            days = (d2 - d1).days
            if days > 0:
                daily_views_rate = max(1.0, (last_views - first_views) / days)
        except Exception:
            pass
            
    # Calculate subscribers growth from monetization snapshots
    if len(rows) >= 2:
        try:
            d1 = datetime.strptime(rows[0]["date"], "%Y-%m-%d")
            d2 = datetime.strptime(rows[-1]["date"], "%Y-%m-%d")
            days = (d2 - d1).days
            if days > 0:
                daily_subs_rate = max(0.1, (rows[-1]["subscribers"] - rows[0]["subscribers"]) / days)
        except Exception:
            pass
    else:
        # Fallback based on channel age / uploads
        cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'uploaded'")
        uploads_count = cursor.fetchone()[0]
        if uploads_count > 0:
            daily_subs_rate = max(0.2, current_subs / max(1, uploads_count * 2))
            
    # Ensure rates are strictly positive
    daily_subs_rate = max(0.01, daily_subs_rate)
    daily_views_rate = max(1.0, daily_views_rate)
    
    # Estimate Target Dates
    now = datetime.now()
    
    # 500 Subs
    days_to_500 = max(0, (500 - current_subs) / daily_subs_rate)
    date_500 = (now + timedelta(days=days_to_500)).strftime("%d %B %Y")
    conf_500 = min(95, max(50, int(80 + (len(rows) * 1.5) - (days_to_500 / 100))))
    
    # 1000 Subs
    days_to_1000 = max(0, (1000 - current_subs) / daily_subs_rate)
    date_1000 = (now + timedelta(days=days_to_1000)).strftime("%d %B %Y")
    conf_1000 = min(95, max(45, int(75 + (len(rows) * 1.5) - (days_to_1000 / 150))))
    
    # 3M Views
    days_to_3m = max(0, (3000000 - current_views) / daily_views_rate)
    date_3m = (now + timedelta(days=days_to_3m)).strftime("%d %B %Y")
    conf_3m = min(95, max(50, int(78 + (len(trend_rows) * 0.5) - (days_to_3m / 300))))
    
    # 10M Views
    days_to_10m = max(0, (10000000 - current_views) / daily_views_rate)
    date_10m = (now + timedelta(days=days_to_10m)).strftime("%d %B %Y")
    conf_10m = min(95, max(40, int(70 + (len(trend_rows) * 0.5) - (days_to_10m / 500))))
    
    return {
        "subs_500": {"date": date_500, "confidence": conf_500, "days": int(days_to_500), "rate": round(daily_subs_rate, 2)},
        "subs_1000": {"date": date_1000, "confidence": conf_1000, "days": int(days_to_1000), "rate": round(daily_subs_rate, 2)},
        "views_3m": {"date": date_3m, "confidence": conf_3m, "days": int(days_to_3m), "rate": round(daily_views_rate, 0)},
        "views_10m": {"date": date_10m, "confidence": conf_10m, "days": int(days_to_10m), "rate": round(daily_views_rate, 0)}
    }

def get_cached_coach_advice(current_subs, current_views, niche_data, speech_rate):
    cache_path = PROJECT_ROOT / "data" / "monetization_coach.json"
    
    # Check cache freshness
    if cache_path.exists():
        try:
            mtime = cache_path.stat().st_mtime
            if time.time() - mtime < 21600:  # 6 hours cache
                with open(cache_path, "r") as f:
                    return json.load(f)
        except Exception:
            pass
            
    # Default fallbacks
    fallback = {
        "best_upload_time": "08:30 PM IST",
        "best_niche": "AI & Tech",
        "worst_niche": "Wildlife",
        "advice": [
            "Leverage Curiosity Gap hooks to increase viewer swipe-away resistance in the first 2 seconds.",
            "Double down on AI & Tech topics as they have the highest view count on your channel.",
            "Optimize call-to-actions (CTAs) at the 15-second mark to boost subscriber conversion rate."
        ]
    }
    
    try:
        from utils.config import get_groq_key, get_setting
        api_key = get_groq_key()
        model = get_setting('llm', 'model', 'llama-3.3-70b-versatile')
        if not api_key:
            return fallback
            
        from groq import Groq
        client = Groq(api_key=api_key, timeout=10.0)
        
        system_prompt = (
            "You are the 'Shorts Orbit AI Monetization Coach'. Your job is to analyze the channel's performance statistics "
            "and provide 3 highly actionable, bulleted recommendations to help the creator reach monetization faster.\n\n"
            "Inputs:\n"
            f"- Subscribers: {current_subs}/1000\n"
            f"- Total Views: {current_views}/10,000,000\n"
            f"- Niche Performance: {json.dumps(niche_data)}\n"
            f"- Voiceover Pacing: {speech_rate}\n\n"
            "Provide your response in JSON format with exactly these keys:\n"
            "- best_upload_time: specific IST time string\n"
            "- best_niche: name of the top niche\n"
            "- worst_niche: name of the lowest performing niche\n"
            "- advice: array of 3 strings containing concise recommendations."
        )
        
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Analyze stats and generate advice."}
            ],
            model=model,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        advice_data = json.loads(completion.choices[0].message.content)
        with open(cache_path, "w") as f:
            json.dump(advice_data, f, indent=2)
        return advice_data
    except Exception:
        return fallback

PORT = 8080

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress request spam logs to keep output clean
        pass
        
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            
            # Fetch data from SQLite
            stats = self.get_stats_data()
            self.wfile.write(json.dumps(stats).encode("utf-8"))
            
        elif path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            
            html_file = PROJECT_ROOT / "dashboard" / "index.html"
            if html_file.exists():
                self.wfile.write(html_file.read_bytes())
            else:
                self.wfile.write(b"<h1>Dashboard HTML file not found.</h1>")
        elif path == "/dashboard/chart.js":
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.end_headers()
            
            chart_file = PROJECT_ROOT / "dashboard" / "chart.js"
            if chart_file.exists():
                self.wfile.write(chart_file.read_bytes())
            else:
                self.wfile.write(b"")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            
    def get_stats_data(self) -> dict:
        conn = None
        try:
            # Load metadata for subscribers and real-time total views
            subscribers = 0
            total_views_from_meta = None
            metadata_file = PROJECT_ROOT / "data" / "channel_metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r") as f:
                        meta = json.load(f)
                        subscribers = meta.get("subscribers", 0)
                        total_views_from_meta = meta.get("total_channel_views")
                except Exception:
                    pass

            conn = get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Total uploads
            cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'uploaded'")
            total_uploads = cursor.fetchone()[0]
            
            # Aggregate views, likes, comments
            cursor.execute("""
                SELECT SUM(max_views) as total_views, SUM(max_likes) as total_likes, SUM(max_comments) as total_comments
                FROM (
                    SELECT video_id, MAX(views) as max_views, MAX(likes) as max_likes, MAX(comments) as max_comments
                    FROM analytics
                    GROUP BY video_id
                )
            """)
            agg_row = cursor.fetchone()
            db_views = agg_row["total_views"] or 0
            meta_views = total_views_from_meta if total_views_from_meta is not None else 0
            total_views = max(db_views, meta_views)
            total_likes = agg_row["total_likes"] or 0
            total_comments = agg_row["total_comments"] or 0
            
            # Daily views/likes trend
            cursor.execute("""
                SELECT date, SUM(views) as views, SUM(likes) as likes, SUM(comments) as comments
                FROM (
                    SELECT date, video_id, MAX(views) as views, MAX(likes) as likes, MAX(comments) as comments
                    FROM analytics
                    GROUP BY date, video_id
                )
                GROUP BY date
                ORDER BY date ASC
                LIMIT 30
            """)
            trend_data = []
            for row in cursor.fetchall():
                trend_data.append({
                    "date": row["date"],
                    "views": row["views"] or 0,
                    "likes": row["likes"] or 0,
                    "comments": row["comments"] or 0
                })
                
            # Fetch all hooks grouped by video_id
            cursor.execute("SELECT video_id, text, score, selected FROM hooks")
            hooks_map = {}
            for row in cursor.fetchall():
                v_id = row["video_id"]
                if v_id not in hooks_map:
                    hooks_map[v_id] = []
                hooks_map[v_id].append({
                    "text": row["text"],
                    "score": row["score"],
                    "selected": row["selected"]
                })
                
            # List of videos with their stats
            cursor.execute("""
                SELECT v.id, v.title, v.script, v.youtube_id, v.status, v.created_at,
                       MAX(a.views) as views, MAX(a.likes) as likes, MAX(a.comments) as comments
                FROM videos v
                LEFT JOIN analytics a ON v.id = a.video_id
                GROUP BY v.id
                ORDER BY v.id DESC
            """)
            videos = []
            for row in cursor.fetchall():
                v_id = row["id"]
                videos.append({
                    "id": v_id,
                    "title": row["title"],
                    "script": row["script"],
                    "youtube_id": row["youtube_id"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "views": row["views"] or 0,
                    "likes": row["likes"] or 0,
                    "comments": row["comments"] or 0,
                    "hooks": hooks_map.get(v_id, [])
                })
                
            # Views by Niche (Classified based on video titles)
            niche_counts = {"AI & Tech": 0, "Space & Spaceflight": 0, "Wildlife & Biology": 0, "Science & Physics": 0}
            for v in videos:
                t_lower = v["title"].lower()
                views = v["views"]
                if any(x in t_lower for x in ["ai", "robot", "computer", "language", "machine", "tech", "coder", "coding", "software", "digit", "network"]):
                    niche_counts["AI & Tech"] += views
                elif any(x in t_lower for x in ["space", "moon", "star", "universe", "planet", "orbit", "telescope", "exoplanet", "nasa", "mars", "jupiter", "astronom", "comet"]):
                    niche_counts["Space & Spaceflight"] += views
                elif any(x in t_lower for x in ["seal", "fish", "biologist", "body", "cancer", "heat", "evolution", "health", "disease", "genetics", "dna", "animal"]):
                    niche_counts["Wildlife & Biology"] += views
                else:
                    niche_counts["Science & Physics"] += views
            niche_data = [{"niche": k, "views": v} for k, v in niche_counts.items() if v > 0]
                
            # Fetch self-learning insights
            insights = {}
            insights_file = DATA_DIR / "self_learning_insights.json"
            if insights_file.exists():
                try:
                    with open(insights_file, "r") as f:
                        insights = json.load(f)
                except Exception:
                    pass
                    
            
            # Tailing the log file
            logs = []
            log_file = PROJECT_ROOT / "logs" / "pipeline.log"
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        # Extract the last 30 log lines
                        logs = [l.strip() for l in lines[-30:]]
                except Exception:
                    pass
                    
            # System file sizes
            db_size_kb = 0
            log_size_kb = 0
            try:
                db_size_kb = round(DB_PATH.stat().st_size / 1024, 1) if DB_PATH.exists() else 0
                log_file = PROJECT_ROOT / "logs" / "pipeline.log"
                log_size_kb = round(log_file.stat().st_size / 1024, 1) if log_file.exists() else 0
            except Exception:
                pass
                
            # Load settings for Retention Optimizer
            from utils.config import get_setting
            music_volume = get_setting('audio', 'music_volume', 0.1)
            voice_volume = get_setting('audio', 'voice_volume', 1.0)
            speech_rate = get_setting('tts', 'rate', '+3%')

            # Calculate daily gains first to enable proper period aggregations

            # Calculate daily gains first to enable proper period aggregations
            from datetime import datetime
            daily_gains = []
            for idx in range(len(trend_data)):
                cur = trend_data[idx]
                if idx == 0:
                    gains = {
                        "date": cur["date"],
                        "views": cur["views"],
                        "likes": cur["likes"],
                        "comments": cur["comments"]
                    }
                else:
                    prev = trend_data[idx - 1]
                    gains = {
                        "date": cur["date"],
                        "views": max(0, cur["views"] - prev["views"]),
                        "likes": max(0, cur["likes"] - prev["likes"]),
                        "comments": max(0, cur["comments"] - prev["comments"])
                    }
                daily_gains.append(gains)

            # Aggregate Weekly
            weekly_map = {}
            for g in daily_gains:
                try:
                    dt = datetime.strptime(g["date"], "%Y-%m-%d")
                    year, week, _ = dt.isocalendar()
                    key = f"{year}-W{week:02d}"
                    if key not in weekly_map:
                        weekly_map[key] = {"views": 0, "likes": 0, "comments": 0}
                    weekly_map[key]["views"] += g["views"]
                    weekly_map[key]["likes"] += g["likes"]
                    weekly_map[key]["comments"] += g["comments"]
                except Exception:
                    pass
            weekly_data = [{"period": k, "views": v["views"], "likes": v["likes"], "comments": v["comments"]} for k, v in weekly_map.items()]

            # Aggregate Monthly
            monthly_map = {}
            for g in daily_gains:
                try:
                    dt = datetime.strptime(g["date"], "%Y-%m-%d")
                    key = dt.strftime("%Y-%m")
                    if key not in monthly_map:
                        monthly_map[key] = {"views": 0, "likes": 0, "comments": 0}
                    monthly_map[key]["views"] += g["views"]
                    monthly_map[key]["likes"] += g["likes"]
                    monthly_map[key]["comments"] += g["comments"]
                except Exception:
                    pass
            monthly_data = [{"period": k, "views": v["views"], "likes": v["likes"], "comments": v["comments"]} for k, v in monthly_map.items()]

            # Aggregate Yearly
            yearly_map = {}
            for g in daily_gains:
                try:
                    dt = datetime.strptime(g["date"], "%Y-%m-%d")
                    key = dt.strftime("%Y")
                    if key not in yearly_map:
                        yearly_map[key] = {"views": 0, "likes": 0, "comments": 0}
                    yearly_map[key]["views"] += g["views"]
                    yearly_map[key]["likes"] += g["likes"]
                    yearly_map[key]["comments"] += g["comments"]
                except Exception:
                    pass
            yearly_data = [{"period": k, "views": v["views"], "likes": v["likes"], "comments": v["comments"]} for k, v in yearly_map.items()]

            # Determine engine status
            engine_status = "HEALTHY (100% OPERATIONAL)"
            try:
                # 1. Check if the latest video entry has 'failed' status
                cursor.execute("SELECT status, title FROM videos ORDER BY id DESC LIMIT 1")
                latest_video_row = cursor.fetchone()
                if latest_video_row and latest_video_row["status"] == "failed":
                    engine_status = f"WARNING: Fact-Check / Quality Check failed on '{latest_video_row['title'][:25]}...'"
            except Exception:
                pass
                
            # Calculate rolling 90-day uploads
            cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'uploaded' AND datetime(created_at) >= datetime('now', '-90 days')")
            uploads_90 = cursor.fetchone()[0]

            # Estimated watch hours
            estimated_watch_hours = round(total_views * 0.0044, 1)

            # Growth forecasts
            forecasts = calculate_growth_forecasts(conn, subscribers, total_views, estimated_watch_hours)
            
            # Fan Funding Eligibility
            fan_funding_subs_pct = min(100.0, (subscribers / 500.0) * 100.0)
            fan_funding_uploads_pct = min(100.0, (uploads_90 / 3.0) * 100.0)
            
            # Whichever is growing faster between watch hours and views
            views_3m_pct = (total_views / 3000000.0) * 100.0
            wh_3k_pct = (estimated_watch_hours / 3000.0) * 100.0
            
            if views_3m_pct >= wh_3k_pct:
                fan_funding_views_pct = min(100.0, views_3m_pct)
                fan_funding_views_current = total_views
                fan_funding_views_target = 3000000
                fan_funding_views_label = "Shorts Views"
                fan_funding_views_remaining = max(0, 3000000 - total_views)
            else:
                fan_funding_views_pct = min(100.0, wh_3k_pct)
                fan_funding_views_current = estimated_watch_hours
                fan_funding_views_target = 3000
                fan_funding_views_label = "Watch Hours"
                fan_funding_views_remaining = max(0.0, 3000.0 - estimated_watch_hours)
                
            fan_funding_progress = (fan_funding_subs_pct + fan_funding_uploads_pct + fan_funding_views_pct) / 3.0
            fan_funding_eligible = subscribers >= 500 and uploads_90 >= 3 and (total_views >= 3000000 or estimated_watch_hours >= 3000)
            
            # Full Monetization Eligibility
            full_subs_pct = min(100.0, (subscribers / 1000.0) * 100.0)
            
            views_10m_pct = (total_views / 10000000.0) * 100.0
            wh_4k_pct = (estimated_watch_hours / 4000.0) * 100.0
            
            if views_10m_pct >= wh_4k_pct:
                full_views_pct = min(100.0, views_10m_pct)
                full_views_current = total_views
                full_views_target = 10000000
                full_views_label = "Shorts Views"
                full_views_remaining = max(0, 10000000 - total_views)
            else:
                full_views_pct = min(100.0, wh_4k_pct)
                full_views_current = estimated_watch_hours
                full_views_target = 4000
                full_views_label = "Watch Hours"
                full_views_remaining = max(0.0, 4000.0 - estimated_watch_hours)
                
            full_progress = (full_subs_pct + full_views_pct) / 2.0
            full_eligible = subscribers >= 1000 and (total_views >= 10000000 or estimated_watch_hours >= 4000)
            
            readiness_score = round((fan_funding_progress + full_progress) / 2.0, 1)

            # AI Monetization Coach advice
            coach_data = get_cached_coach_advice(subscribers, total_views, niche_data, speech_rate)

            # Live Eligibility Check details
            reasons = []
            if subscribers < 500:
                reasons.append("Subscribers Missing")
            if uploads_90 < 3:
                reasons.append("Uploads Count Missing")
            if total_views < 3000000 and estimated_watch_hours < 3000:
                reasons.append("Views or Watch Hours Missing")
                
            next_milestone = "Fan Funding Eligibility"
            if subscribers >= 500 and uploads_90 >= 3 and (total_views >= 3000000 or estimated_watch_hours >= 3000):
                next_milestone = "Full Monetization Partner"
                reasons = []
                if subscribers < 1000:
                    reasons.append("Subscribers Missing")
                if total_views < 10000000 and estimated_watch_hours < 4000:
                    reasons.append("Views or Watch Hours Missing")
            if subscribers >= 1000 and (total_views >= 10000000 or estimated_watch_hours >= 4000):
                next_milestone = "All Milestones Achieved!"
                reasons = []
                
            # Assemble monetization dictionary
            monetization = {
                "fan_funding": {
                    "eligible": fan_funding_eligible,
                    "progress_pct": round(fan_funding_progress, 1),
                    "subscribers": subscribers,
                    "subscribers_target": 500,
                    "subscribers_remaining": max(0, 500 - subscribers),
                    "uploads_90": uploads_90,
                    "uploads_target": 3,
                    "uploads_eligible": uploads_90 >= 3,
                    "views_current": fan_funding_views_current,
                    "views_target": fan_funding_views_target,
                    "views_pct": round(fan_funding_views_pct, 1),
                    "views_remaining": fan_funding_views_remaining,
                    "views_label": fan_funding_views_label,
                    "status_text": "Eligible" if fan_funding_eligible else "In Progress"
                },
                "full_monetization": {
                    "eligible": full_eligible,
                    "progress_pct": round(full_progress, 1),
                    "subscribers": subscribers,
                    "subscribers_target": 1000,
                    "subscribers_remaining": max(0, 1000 - subscribers),
                    "views_current": full_views_current,
                    "views_target": full_views_target,
                    "views_pct": round(full_views_pct, 1),
                    "views_remaining": full_views_remaining,
                    "views_label": full_views_label,
                    "status_text": "Eligible" if full_eligible else ("In Progress" if subscribers >= 500 else "Not Eligible")
                },
                "readiness_score": readiness_score,
                "forecasts": forecasts,
                "coach": coach_data,
                "live_eligibility": {
                    "eligible": full_eligible,
                    "reasons": reasons,
                    "next_milestone": next_milestone,
                    "status_text": "Eligible" if full_eligible else "Not Eligible"
                }
            }

            return {
                "total_uploads": total_uploads,
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "videos": videos,
                "insights": insights,
                "trend_data": trend_data,
                "weekly_data": weekly_data,
                "monthly_data": monthly_data,
                "yearly_data": yearly_data,
                "logs": logs,
                "niche_data": niche_data,
                "db_size_kb": db_size_kb,
                "log_size_kb": log_size_kb,
                "music_volume": music_volume,
                "voice_volume": voice_volume,
                "speech_rate": speech_rate,
                "subscribers": subscribers,
                "engine_status": engine_status,
                "monetization": monetization
            }
        except Exception as e:
            logger.error(f"Error querying database stats: {e}")
            return {
                "total_uploads": 0,
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "videos": [],
                "insights": {},
                "trend_data": [],
                "logs": [],
                "niche_data": [],
                "db_size_kb": 0,
                "log_size_kb": 0,
                "music_volume": 0.1,
                "voice_volume": 1.0,
                "speech_rate": "+3%",
                "subscribers": 0,
                "engine_status": "HEALTHY",
                "monetization": {}
            }
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

def start_background_harvester():
    """Starts a background thread that periodically harvests YouTube statistics to keep the dashboard updated."""
    def run_harvest_loop():
        # Delay initial harvest slightly to allow dashboard server to start cleanly
        time.sleep(5)
        while True:
            try:
                logger.info("Background thread triggering stats harvest from YouTube API...")
                from python.harvest_analytics import harvest_channel_stats
                success = harvest_channel_stats()
                logger.info(f"Background stats harvest completed successfully: {success}")
            except Exception as e:
                logger.error(f"Error in background stats harvester: {e}", exc_info=True)
            # Sleep for 2 minutes before the next update
            time.sleep(120)

    t = threading.Thread(target=run_harvest_loop, daemon=True)
    t.start()
    logger.info("Background YouTube stats harvester thread initialized successfully (Interval: 2m).")

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, DashboardHandler)
    logger.info(f"Starting Glassmorphism Performance Dashboard on http://localhost:{PORT}")
    
    # Start background stats harvesting to keep dashboard updated time-to-time
    start_background_harvester()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping dashboard server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
