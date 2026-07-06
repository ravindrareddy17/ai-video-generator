import sqlite3
import json
from pathlib import Path
import sys

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.paths import DATA_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = DATA_DIR / "shortest_orbit_v3.db"

def get_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise SQLite tables if they do not exist."""
    logger.info(f"Initializing SQLite database at: {DB_PATH}")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table: topics
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
    
    # Table: videos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            topic_id INTEGER,
            script TEXT,
            youtube_id TEXT,
            status TEXT,
            visual_queries TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    """)
    
    # Table: hooks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            text TEXT,
            score REAL,
            selected INTEGER DEFAULT 0,
            FOREIGN KEY(video_id) REFERENCES videos(id)
        )
    """)
    
    # Table: analytics
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
    
    conn.commit()
    conn.close()
    logger.info("Database schema initialized successfully.")

# Initialize database on import
init_db()
