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

from utils.database import DB_PATH
from utils.paths import DATA_DIR, PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger("dashboard_server")

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

            conn = sqlite3.connect(DB_PATH)
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
                    
            conn.close()
            
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
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT status, title FROM videos ORDER BY id DESC LIMIT 1")
                latest_video_row = cursor.fetchone()
                conn.close()
                if latest_video_row and latest_video_row["status"] == "failed":
                    engine_status = f"WARNING: Fact-Check / Quality Check failed on '{latest_video_row['title'][:25]}...'"
            except Exception:
                pass
                
            # 2. Check if the log contains critical errors
            if logs:
                for line in logs[-10:]:
                    if "ERROR" in line or "CRITICAL" in line:
                        engine_status = "ERROR: Exception detected in last run. Check engine console logs."
                        break

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
                "engine_status": engine_status
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
                "speech_rate": "+3%"
            }

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
    logger.info("Background YouTube stats harvester thread initialized successfully (Interval: 15m).")

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
