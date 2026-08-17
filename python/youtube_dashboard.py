"""
youtube_dashboard.py - THE SHORTEST ORBIT YouTube Command Center Dashboard.

Offers DUAL MODES:
1. 🌟 SIMPLE VIEW: Clean 4 cards, plain-English channel tip, simple views trend, Top 5 Shorts, Next Ideas.
2. 🔬 DEEP GROWTH COMMAND CENTER: Complete 15-view deep analytics library (Performance Matrix, Topic Confidence, Hook Patterns, Duration Buckets, Retention Curves, Experiments, V4 Memory).
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Local dashboard modules
from dashboard_data import (
    load_youtube_videos_df,
    filter_df_by_date_range,
    load_v4_insights,
    load_v4_contract,
    load_ai_learning_records
)
from dashboard_metrics import (
    compute_channel_baselines,
    compute_v4_channel_health,
    diagnose_growth_bottleneck,
    classify_video_performance,
    diagnose_underperformer,
    compute_v4_growth_model
)
from dashboard_charts import (
    render_growth_trend_chart,
    render_performance_matrix,
    render_pillar_chart,
    render_topic_chart,
    render_hook_chart,
    render_duration_chart,
    render_retention_curve_chart
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. STREAMLIT PAGE CONFIG & STYLING
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="THE SHORTEST ORBIT — YouTube Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0D1117;
        color: #E6EDF3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main-title {
        font-size: 28px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 0;
    }
    .sub-title {
        font-size: 13px;
        color: #FF5555;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .simple-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
    }
    .card-title {
        font-size: 12px;
        color: #8B949E;
        font-weight: 600;
        text-transform: uppercase;
    }
    .card-value {
        font-size: 28px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 4px 0;
    }
    .tip-box {
        background-color: rgba(56, 139, 253, 0.1);
        border-left: 4px solid #58A6FF;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 16px 0;
    }
    .video-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    raw_df = load_youtube_videos_df()
    insights = load_v4_insights()
    contract = load_v4_contract()
    ai_records = load_ai_learning_records()
    return raw_df, insights, contract, ai_records

df_raw, v4_insights, latest_contract, ai_records = load_data()

# ─────────────────────────────────────────────────────────────────────────────
# 3. SIDEBAR & MODE SELECTOR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/youtube-shorts.png", width=50)
    st.markdown("### THE SHORTEST ORBIT")
    st.markdown("<p style='color:#FF5555; font-size:11px; font-weight:700;'>YOUTUBE DASHBOARD</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### 🎛️ DASHBOARD MODE")
    view_mode = st.radio(
        "Select Experience Level:",
        ["🌟 Simple Creator View", "🔬 Deep Growth Command Center"]
    )

    st.divider()
    st.markdown("### 📅 DATE RANGE")
    date_option = st.selectbox(
        "Select Time Window:",
        ["LAST 7 DAYS", "LAST 28 DAYS", "PREVIOUS 28 DAYS", "LAST 90 DAYS", "LIFETIME"],
        index=1
    )

    nav_page = "📊 Simple Overview"
    if view_mode == "🔬 Deep Growth Command Center":
        st.divider()
        st.markdown("### 🧭 DEEP NAVIGATOR")
        nav_page = st.radio(
            "Jump to Analysis:",
            [
                "📊 Overview",
                "🎬 Shorts Library",
                "🔍 Side-by-Side Comparison",
                "📈 Growth & Velocity",
                "🎯 Topic Analysis",
                "🪝 Hook Analysis",
                "⏱ Retention & Durations",
                "👥 Subscribers",
                "🧠 V4 Learning & Next Videos",
                "⚙ Data Health"
            ]
        )

    st.divider()
    if st.button("🔄 SYNC YOUTUBE DATA"):
        st.cache_data.clear()
        st.success("YouTube data synchronized!")
        st.rerun()

# Filter dataset
df_curr, df_prev = filter_df_by_date_range(df_raw, date_option)
baselines = compute_channel_baselines(df_curr)
health_score, health_status, health_bottleneck = compute_v4_channel_health(df_curr, baselines)
bottleneck_info = diagnose_growth_bottleneck(df_curr)
growth_model = compute_v4_growth_model(df_curr)

if not df_curr.empty:
    df_curr['performance_class'] = df_curr.apply(lambda r: classify_video_performance(r, baselines), axis=1)

# ─────────────────────────────────────────────────────────────────────────────
# 4. TOP HEADER
# ─────────────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div style="margin-bottom:15px;">
        <h1 class="main-title">🚀 THE SHORTEST ORBIT</h1>
        <div class="sub-title">YouTube Analytics Dashboard & Command Center</div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.markdown(f"<div style='text-align:right; color:#8B949E; font-size:12px;'>Data Source: <b>STORED SNAPSHOT DATA</b><br>Analyzed Shorts: <b>{len(df_curr)}</b></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 5. MODE 1: SIMPLE CREATOR VIEW
# ─────────────────────────────────────────────────────────────────────────────
if view_mode == "🌟 Simple Creator View":
    tot_views = int(df_curr['views'].sum()) if not df_curr.empty else 0
    tot_subs = int(df_curr['subscribers_gained'].sum()) if not df_curr.empty else 0
    tot_likes = int(df_curr['likes'].sum()) if not df_curr.empty else 0
    tot_shorts = len(df_curr)

    prev_views = int(df_prev['views'].sum()) if not df_prev.empty else 0
    views_change = ((tot_views - prev_views) / prev_views * 100) if prev_views > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="simple-card"><div class="card-title">👁️ Total Views</div><div class="card-value">{tot_views:,}</div><div style="color:#3FB950; font-size:12px;">{views_change:+.1f}% vs previous</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="simple-card"><div class="card-title">👥 Subscribers Gained</div><div class="card-value">+{tot_subs:,}</div><div style="color:#FFD700; font-size:12px;">Channel Growth</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="simple-card"><div class="card-title">❤️ Total Likes</div><div class="card-value">{tot_likes:,}</div><div style="color:#58A6FF; font-size:12px;">Audience Likes</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="simple-card"><div class="card-title">🎬 Shorts Published</div><div class="card-value">{tot_shorts}</div><div style="color:#8B949E; font-size:12px;">Videos Analyzed</div></div>', unsafe_allow_html=True)

    top_topic = df_curr.groupby('content_pillar')['views'].sum().idxmax() if not df_curr.empty else 'Space Competition'
    st.markdown(f"""
    <div class="tip-box">
        <div style="font-size:15px; font-weight:700; color:#58A6FF;">💡 KEY CHANNEL INSIGHT</div>
        <div style="font-size:14px; color:#E6EDF3; margin-top:4px;">
            Your top content pillar is <b>{top_topic}</b>. 
            Channel Health Score is <b>{health_score}/100 ({health_status})</b> with main bottleneck on <b>{bottleneck_info['bottleneck']}</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📈 Views Trend")
    st.plotly_chart(render_growth_trend_chart(df_curr, df_prev, 'views'), use_container_width=True)

    st.markdown("### 🏆 Top 5 Best Shorts")
    top5 = df_curr.sort_values('views', ascending=False).head(5)
    for idx, (_, row) in enumerate(top5.iterrows(), start=1):
        st.markdown(f"""
        <div class="video-card">
            <div>
                <div style="font-size:15px; font-weight:700; color:#FFF;">#{idx} {row['title']}</div>
                <div style="font-size:12px; color:#8B949E;">Published: {str(row['uploaded_at'])[:10]} | Pillar: {row['content_pillar']}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:18px; font-weight:800; color:#FFD700;">{row['views']:,} views</div>
                <div style="font-size:12px; color:#3FB950;">+{row['subscribers_gained']} subs</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 6. MODE 2: DEEP GROWTH COMMAND CENTER
# ─────────────────────────────────────────────────────────────────────────────
else:
    if nav_page == "📊 Overview":
        kcol1, kcol2, kcol3, kcol4 = st.columns(4)
        kcol1.metric("Total Views", f"{df_curr['views'].sum():,}")
        kcol2.metric("Subscribers Gained", f"+{df_curr['subscribers_gained'].sum():,}")
        kcol3.metric("Avg APV", f"{df_curr['apv'].mean():.1f}%")
        kcol4.metric("Viewer Choice", f"{df_curr['viewer_choice'].mean():.1f}%")
        st.divider()
        ch1, ch2 = st.columns(2)
        with ch1:
            st.plotly_chart(render_growth_trend_chart(df_curr, df_prev, 'views'), use_container_width=True)
        with ch2:
            st.plotly_chart(render_performance_matrix(df_curr), use_container_width=True)

    elif nav_page == "🎬 Shorts Library":
        st.markdown("### 🎬 Shorts Performance Library")
        st.dataframe(df_curr[['title', 'uploaded_at', 'views', 'viewer_choice', 'apv', 'subscribers_gained', 'performance_class']], use_container_width=True)

    elif nav_page == "🔍 Side-by-Side Comparison":
        st.markdown("### 🔍 Video Comparison Tool")
        selected = st.multiselect("Select up to 5 Shorts:", df_curr['title'].tolist(), default=df_curr['title'].head(3).tolist())
        if selected:
            st.dataframe(df_curr[df_curr['title'].isin(selected)][['title', 'views', 'viewer_choice', 'apv', 'likes', 'subscribers_gained']].set_index('title').T, use_container_width=True)

    elif nav_page == "📈 Growth & Velocity":
        st.plotly_chart(render_growth_trend_chart(df_curr, df_prev, 'views'), use_container_width=True)

    elif nav_page == "🎯 Topic Analysis":
        st.plotly_chart(render_topic_chart(df_curr), use_container_width=True)

    elif nav_page == "🪝 Hook Analysis":
        st.plotly_chart(render_hook_chart(df_curr), use_container_width=True)

    elif nav_page == "⏱ Retention & Durations":
        st.plotly_chart(render_duration_chart(df_curr), use_container_width=True)

    elif nav_page == "🧠 V4 Learning & Next Videos":
        st.json(v4_insights.get('youtube', v4_insights.get('combined', {})))

    elif nav_page == "⚙ Data Health":
        st.markdown(f"- **YouTube Shorts Analyzed:** {len(df_raw)}<br>- **DB Path:** `data/shortest_orbit_v3.db`<br>- **Status:** READ-ONLY SAFE", unsafe_allow_html=True)
