import json
import sqlite3
import sys
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
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Total uploads
            cursor.execute("SELECT COUNT(*) FROM videos")
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
            total_views = agg_row["total_views"] or 0
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
                
            # Views by Niche
            cursor.execute("""
                SELECT t.title as niche, SUM(a.views) as views
                FROM videos v
                JOIN topics t ON v.topic_id = t.id
                JOIN analytics a ON v.id = a.video_id
                GROUP BY t.id
            """)
            niche_data = []
            for row in cursor.fetchall():
                niche_data.append({
                    "niche": row["niche"],
                    "views": row["views"] or 0
                })
                
            # Fallback text-classification if database maps are empty in first stage
            if not niche_data or sum(nd["views"] for nd in niche_data) == 0:
                niche_counts = {"AI & Tech": 0, "Space & Spaceflight": 0, "Wildlife & Biology": 0, "Science & Physics": 0}
                for v in videos:
                    t_lower = v["title"].lower()
                    views = v["views"]
                    if "ai" in t_lower or "robot" in t_lower or "computer" in t_lower or "language" in t_lower or "machine" in t_lower:
                        niche_counts["AI & Tech"] += views
                    elif "space" in t_lower or "moon" in t_lower or "star" in t_lower or "universe" in t_lower:
                        niche_counts["Space & Spaceflight"] += views
                    elif "seal" in t_lower or "fish" in t_lower or "biologist" in t_lower or "body" in t_lower or "cancer" in t_lower:
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
                
            return {
                "total_uploads": total_uploads,
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "videos": videos,
                "insights": insights,
                "trend_data": trend_data,
                "logs": logs,
                "niche_data": niche_data,
                "db_size_kb": db_size_kb,
                "log_size_kb": log_size_kb
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
                "log_size_kb": 0
            }

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, DashboardHandler)
    logger.info(f"Starting Glassmorphism Performance Dashboard on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping dashboard server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
