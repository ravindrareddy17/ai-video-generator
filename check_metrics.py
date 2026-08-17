import sqlite3
import json
from pathlib import Path

db_path = Path("E:/ai_gen/AI-VIDEO-V2/data/shortest_orbit_v3.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 1. Current channel metadata
print("=== CHANNEL METADATA ===")
meta_file = Path("E:/ai_gen/AI-VIDEO-V2/data/channel_metadata.json")
if meta_file.exists():
    with open(meta_file) as f:
        meta = json.load(f)
    print(json.dumps(meta, indent=2))

# 2. Monetization snapshots (all time)
print("\n=== MONETIZATION GROWTH ===")
rows = conn.execute("SELECT * FROM monetization_snapshots ORDER BY date ASC").fetchall()
for r in rows:
    print(dict(r))

# 3. Today's analytics - top 20 videos by views
print("\n=== TOP 20 VIDEOS BY VIEWS (Today's Snapshot) ===")
rows = conn.execute("""
    SELECT a.video_id, v.title, a.views, a.likes, a.comments, a.fb_views, a.fb_likes, a.ig_views, a.ig_likes, a.date
    FROM analytics a
    JOIN videos v ON a.video_id = v.id
    WHERE a.date = '2026-08-06'
    ORDER BY a.views DESC
    LIMIT 20
""").fetchall()
for r in rows:
    print(dict(r))

# 4. Total views/likes/comments across all videos
print("\n=== AGGREGATE STATS (Today) ===")
row = conn.execute("""
    SELECT 
        COUNT(DISTINCT video_id) as total_tracked_videos,
        SUM(views) as total_yt_views,
        SUM(likes) as total_yt_likes,
        SUM(comments) as total_yt_comments,
        SUM(fb_views) as total_fb_views,
        SUM(fb_likes) as total_fb_likes,
        SUM(ig_views) as total_ig_views,
        SUM(ig_likes) as total_ig_likes
    FROM analytics 
    WHERE date = '2026-08-06'
""").fetchone()
print(dict(row))

# 5. Growth comparison: Jul 10 vs Aug 6
print("\n=== GROWTH COMPARISON ===")
jul10 = conn.execute("""
    SELECT SUM(views) as total_views, SUM(likes) as total_likes, SUM(comments) as total_comments
    FROM analytics WHERE date = '2026-07-10'
""").fetchone()
aug6 = conn.execute("""
    SELECT SUM(views) as total_views, SUM(likes) as total_likes, SUM(comments) as total_comments
    FROM analytics WHERE date = '2026-08-06'
""").fetchone()
print(f"Jul 10: Views={jul10['total_views']}, Likes={jul10['total_likes']}, Comments={jul10['total_comments']}")
print(f"Aug 06: Views={aug6['total_views']}, Likes={aug6['total_likes']}, Comments={aug6['total_comments']}")

# 6. Videos with most engagement
print("\n=== MOST COMMENTED VIDEOS ===")
rows = conn.execute("""
    SELECT a.video_id, v.title, a.views, a.likes, a.comments, a.date
    FROM analytics a
    JOIN videos v ON a.video_id = v.id
    WHERE a.date = '2026-08-06' AND a.comments > 0
    ORDER BY a.comments DESC
    LIMIT 10
""").fetchall()
for r in rows:
    print(dict(r))

# 7. Upload count by week
print("\n=== WEEKLY UPLOADS ===")
rows = conn.execute("""
    SELECT 
        strftime('%Y-W%W', created_at) as week,
        COUNT(*) as uploaded
    FROM videos 
    WHERE status = 'uploaded'
    GROUP BY week
    ORDER BY week DESC
    LIMIT 8
""").fetchall()
for r in rows:
    print(dict(r))

conn.close()
