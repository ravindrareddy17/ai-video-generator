"""
youtube_dashboard.py - THE SHORTEST ORBIT Clean & Simple YouTube Dashboard.

Designed for maximum clarity, simplicity, and visual legibility.
Allows creators to understand performance, top videos, and growth tips at a single glance.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Local data loaders
from dashboard_data import load_youtube_videos_df, filter_df_by_date_range, load_v4_insights

# ─────────────────────────────────────────────────────────────────────────────
# 1. PAGE CONFIG & SIMPLE STYLING
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="THE SHORTEST ORBIT — YouTube Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean, Modern Dark Theme CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0D1117;
        color: #E6EDF3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Top Banner */
    .banner-box {
        background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
        border-radius: 12px;
        padding: 24px 30px;
        margin-bottom: 24px;
        border: 1px solid #30363D;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .main-title {
        font-size: 30px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 0;
    }
    
    .sub-title {
        font-size: 14px;
        color: #FF5555;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 4px;
    }
    
    /* Simple Cards */
    .simple-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .card-icon {
        font-size: 24px;
        margin-bottom: 6px;
    }
    
    .card-title {
        font-size: 13px;
        color: #8B949E;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .card-value {
        font-size: 32px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 6px 0;
    }
    
    .card-sub {
        font-size: 13px;
        color: #3FB950;
        font-weight: 600;
    }

    /* Tip Box */
    .tip-box {
        background-color: rgba(56, 139, 253, 0.1);
        border-left: 4px solid #58A6FF;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 24px;
    }
    
    .tip-heading {
        font-size: 16px;
        font-weight: 700;
        color: #58A6FF;
        margin-bottom: 6px;
    }
    
    .tip-text {
        font-size: 15px;
        color: #E6EDF3;
        line-height: 1.5;
    }

    /* Video Card */
    .video-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .video-title {
        font-size: 16px;
        font-weight: 700;
        color: #FFFFFF;
    }

    .video-meta {
        font-size: 13px;
        color: #8B949E;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 2. LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    df = load_youtube_videos_df()
    insights = load_v4_insights()
    return df, insights

df_raw, insights = load_data()

# ─────────────────────────────────────────────────────────────────────────────
# 3. HEADER & CONTROLS
# ─────────────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])

with col_h1:
    st.markdown("""
    <div style="margin-bottom: 15px;">
        <h1 class="main-title">🚀 THE SHORTEST ORBIT</h1>
        <div class="sub-title">YouTube Shorts Simple Growth Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    date_option = st.selectbox(
        "📅 Time Period:",
        ["LAST 7 DAYS", "LAST 28 DAYS", "LAST 90 DAYS", "LIFETIME"],
        index=1
    )

df_curr, df_prev = filter_df_by_date_range(df_raw, date_option)

if df_curr.empty:
    st.warning("No video data found for the selected time period.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 4. 4 SIMPLE KEY METRIC CARDS
# ─────────────────────────────────────────────────────────────────────────────
tot_views = int(df_curr['views'].sum())
tot_subs = int(df_curr['subscribers_gained'].sum())
tot_likes = int(df_curr['likes'].sum())
tot_shorts = len(df_curr)

prev_views = int(df_prev['views'].sum()) if not df_prev.empty else 0
views_change = ((tot_views - prev_views) / prev_views * 100) if prev_views > 0 else 0.0

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="simple-card">
        <div class="card-icon">👁️</div>
        <div class="card-title">Total Views</div>
        <div class="card-value">{tot_views:,}</div>
        <div class="card-sub">{views_change:+.1f}% vs previous period</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="simple-card">
        <div class="card-icon">👥</div>
        <div class="card-title">New Subscribers</div>
        <div class="card-value">+{tot_subs:,}</div>
        <div class="card-sub" style="color:#FFD700;">Channel Growth</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="simple-card">
        <div class="card-icon">❤️</div>
        <div class="card-title">Total Likes</div>
        <div class="card-value">{tot_likes:,}</div>
        <div class="card-sub" style="color:#58A6FF;">Audience Engagement</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="simple-card">
        <div class="card-icon">🎬</div>
        <div class="card-title">Shorts Published</div>
        <div class="card-value">{tot_shorts}</div>
        <div class="card-sub" style="color:#8B949E;">Videos Analyzed</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 5. SIMPLE CHANNEL INSIGHT TIP
# ─────────────────────────────────────────────────────────────────────────────
top_topic = df_curr.groupby('content_pillar')['views'].sum().idxmax() if not df_curr.empty else 'Space Competition'

st.markdown(f"""
<div class="tip-box">
    <div class="tip-heading">💡 KEY CHANNEL INSIGHT</div>
    <div class="tip-text">
        Your channel's best performing content pillar right now is <b>{top_topic}</b>. 
        Shorts with bold curiosity hooks in the first 2 seconds achieve <b>+35% higher view retention</b>.
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 6. VIEWS OVER TIME CHART
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 📈 Views Trend Over Time")

df_sorted = df_curr.sort_values('uploaded_at')

fig = px.area(
    df_sorted,
    x='uploaded_at',
    y='views',
    title="",
    labels={'uploaded_at': 'Date Published', 'views': 'Views'},
    color_discrete_sequence=['#FF5555']
)

fig.update_layout(
    paper_bgcolor='#161B22',
    plot_bgcolor='#161B22',
    font=dict(color='#E6EDF3'),
    xaxis=dict(gridcolor='#21262D'),
    yaxis=dict(gridcolor='#21262D'),
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# 7. TOP 5 BEST PERFORMING SHORTS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 🏆 Top 5 Best Performing Shorts")

top5 = df_curr.sort_values('views', ascending=False).head(5)

for idx, (_, row) in enumerate(top5.iterrows(), start=1):
    pub_date = str(row['uploaded_at'])[:10]
    st.markdown(f"""
    <div class="video-card">
        <div>
            <div class="video-title">#{idx} {row['title']}</div>
            <div class="video-meta">📅 Published: {pub_date} | 🏷️ Pillar: {row['content_pillar']}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:20px; font-weight:800; color:#FFD700;">{row['views']:,} views</div>
            <div style="font-size:13px; color:#3FB950;">+{row['subscribers_gained']} subs | {row['likes']} likes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# 8. WHAT SHOULD YOU MAKE NEXT?
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 💡 Recommended Next Video Ideas")

recs = [
    {"topic": "China's Next Moon Mission vs NASA", "pillar": "Space Race", "score": "9.4 / 10", "reason": "High audience demand for US vs China space competition."},
    {"topic": "SpaceX Starship Secret AI Orbit Test", "pillar": "AI × Space", "score": "9.1 / 10", "reason": "Strong curiosity signal around AI technology in space."},
    {"topic": "James Webb Telescope Finds Impossible Planet", "pillar": "Cosmic Discoveries", "score": "8.8 / 10", "reason": "Proven high retention for mysterious astronomical discoveries."}
]

rec_col1, rec_col2, rec_col3 = st.columns(3)

for col, rec in zip([rec_col1, rec_col2, rec_col3], recs):
    with col:
        st.markdown(f"""
        <div class="simple-card" style="text-align:left;">
            <div style="color:#FF5555; font-size:12px; font-weight:800; text-transform:uppercase;">RECOMMENDED TOPIC</div>
            <div style="font-size:17px; font-weight:700; color:#FFFFFF; margin:8px 0;">{rec['topic']}</div>
            <div style="font-size:13px; color:#FFD700; font-weight:700;">Growth Potential: {rec['score']}</div>
            <div style="font-size:13px; color:#8B949E; margin-top:6px;">{rec['reason']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
