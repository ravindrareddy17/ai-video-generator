import sqlite3
import sys
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DB_DIR.parent.parent))
from utils.logger import get_logger
logger = get_logger("database.connection")

def ensure_column(cursor, table_name: str, column_name: str, definition: str):
    """Add a missing column to an existing table without breaking old databases."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row["name"] for row in cursor.fetchall()}
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
        logger.info(f"Added missing column '{column_name}' to table '{table_name}'.")

YOUTUBE_DB = DB_DIR / "youtube.db"
INSTAGRAM_DB = DB_DIR / "instagram.db"
FACEBOOK_DB = DB_DIR / "facebook.db"
AUTOMATION_DB = DB_DIR / "automation.db"
AI_LEARNING_DB = DB_DIR / "ai_learning.db"

def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn

def get_youtube_conn() -> sqlite3.Connection:
    return _connect(YOUTUBE_DB)

def get_instagram_conn() -> sqlite3.Connection:
    return _connect(INSTAGRAM_DB)

def get_facebook_conn() -> sqlite3.Connection:
    return _connect(FACEBOOK_DB)

def get_automation_conn() -> sqlite3.Connection:
    return _connect(AUTOMATION_DB)

def get_ai_learning_conn() -> sqlite3.Connection:
    return _connect(AI_LEARNING_DB)

def init_db():
    """Initialize schemas for all isolated databases."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. YouTube DB Schema
    conn = get_youtube_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            topic_id INTEGER,
            script TEXT,
            youtube_id TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            date TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            subscribers_gained INTEGER DEFAULT 0,
            retention_data TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(video_id) REFERENCES videos(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monetization_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            subscribers INTEGER,
            shorts_views INTEGER,
            watch_hours REAL,
            uploads_90_days INTEGER,
            progress_percentage REAL,
            readiness_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_monetization_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            remaining_days INTEGER,
            subs_needed_per_day INTEGER,
            views_needed_per_day INTEGER,
            hours_needed_per_day REAL,
            subs_today INTEGER,
            views_today INTEGER,
            hours_today REAL,
            subs_status TEXT,
            views_status TEXT,
            hours_status TEXT,
            ai_recommendation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    # 2. Instagram DB Schema
    conn = get_instagram_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            topic_id INTEGER,
            script TEXT,
            instagram_id TEXT,
            instagram_url TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            date TEXT,
            reach INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            profile_visits INTEGER DEFAULT 0,
            plays INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            accounts_reached INTEGER DEFAULT 0,
            follower_growth INTEGER DEFAULT 0,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(video_id) REFERENCES videos(id)
        )
    """)
    conn.commit()
    conn.close()

    # 3. Facebook DB Schema
    conn = get_facebook_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            topic_id INTEGER,
            script TEXT,
            facebook_id TEXT,
            facebook_url TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            date TEXT,
            reach INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            video_views INTEGER DEFAULT 0,
            watch_time REAL DEFAULT 0.0,
            likes INTEGER DEFAULT 0,
            reactions INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            audience_growth INTEGER DEFAULT 0,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(video_id) REFERENCES videos(id)
        )
    """)
    conn.commit()
    conn.close()

    # 4. Automation DB Schema
    conn = get_automation_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            source TEXT,
            trend_score REAL,
            engagement_potential REAL,
            retention_potential REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            text TEXT,
            score REAL,
            selected INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            log_level TEXT,
            message TEXT,
            module TEXT,
            exception TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            status TEXT,
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            error_count INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS automation_retries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_title TEXT,
            platform TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            status TEXT DEFAULT 'pending',
            last_attempt TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Ensure new V3 scoring columns exist in topics table
    ensure_column(cursor, "topics", "competition_score", "REAL DEFAULT 50.0")
    ensure_column(cursor, "topics", "audience_interest", "REAL DEFAULT 50.0")
    ensure_column(cursor, "topics", "evergreen_score", "REAL DEFAULT 50.0")
    ensure_column(cursor, "topics", "virality_score", "REAL DEFAULT 50.0")
    ensure_column(cursor, "topics", "education_score", "REAL DEFAULT 50.0")
    ensure_column(cursor, "topics", "ctr_prediction", "REAL DEFAULT 50.0")
    ensure_column(cursor, "topics", "retention_prediction", "REAL DEFAULT 50.0")
    ensure_column(cursor, "topics", "overall_growth_score", "REAL DEFAULT 50.0")
    
    conn.commit()
    conn.close()

    # 5. AI Learning DB Schema
    conn = get_ai_learning_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            date TEXT,
            niche TEXT,
            upload_hour INTEGER,
            views_achieved INTEGER,
            engagement REAL,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            date TEXT,
            category TEXT,
            advice TEXT,
            confidence_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            date TEXT,
            prediction_type TEXT,
            expected_metric TEXT,
            expected_date TEXT,
            target_value REAL,
            confidence_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_loops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            platform TEXT,
            date TEXT,
            metric_name TEXT,
            predicted_value REAL,
            actual_value REAL,
            accuracy_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competitor_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT UNIQUE,
            platform TEXT,
            niche TEXT,
            subscribers INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            upload_frequency TEXT,
            top_tags TEXT,
            last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("All platform databases initialized successfully.")
