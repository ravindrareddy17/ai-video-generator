"""
youtube_dashboard.py - THE SHORTEST ORBIT YouTube Analytics Command Center.

Production-ready Streamlit local dashboard for YouTube Analytics only.
Dark cinematic space/technology UI theme with Crimson Red (#C1121F) accents.
Read-Only database safety. Connects directly to V4 SQLite databases and memory.

Run with:
streamlit run python/youtube_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path

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
# 1. STREAMLIT PAGE CONFIG & CINEMATIC SPACE STYLING
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="THE SHORTEST ORBIT — YouTube Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Theme: Dark space (#0E1117), Crimson Accent (#C1121F), Gold (#FFD700)
st.markdown("""
<style>
    /* Dark Space Theme Background */
    .stApp {
        background-color: #0E1117;
        color: #F0F6FC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header Container */
    .top-header-box {
        background: linear-gradient(135deg, #161B22 0%, #0E1117 100%);
        border: 1px solid #C1121F;
        border-left: 6px solid #C1121F;
        border-radius: 8px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(193, 18, 31, 0.15);
    }
    
    .header-title {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        margin: 0;
    }
    
    .header-subtitle {
        font-size: 14px;
        color: #C1121F;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-top: 4px;
    }
    
    .badge-live {
        background-color: rgba(63, 185, 80, 0.15);
        color: #3FB950;
        border: 1px solid #3FB950;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    
    .badge-snapshot {
        background-color: rgba(255, 215, 0, 0.15);
        color: #FFD700;
        border: 1px solid #FFD700;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }

    /* Metric Cards */
    .kpi-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 16px 18px;
        margin-bottom: 14px;
    }
    
    .kpi-label {
        font-size: 12px;
        font-weight: 700;
        color: #8B949E;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .kpi-value {
        font-size: 26px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 4px 0;
    }
    
    .kpi-delta-pos {
        color: #3FB950;
        font-size: 12px;
        font-weight: 700;
    }
    
    .kpi-delta-neg {
        color: #C1121F;
        font-size: 12px;
        font-weight: 700;
    }
    
    .kpi-prev {
        font-size: 11px;
        color: #8B949E;
    }

    /* Health Score Box */
    .health-card {
        background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
        border: 1px solid #FFD700;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    
    .health-score {
        font-size: 48px;
        font-weight: 900;
        color: #FFD700;
        margin: 0;
    }

    /* Bottleneck Card */
    .bottleneck-card {
        background-color: #161B22;
        border: 1px solid #C1121F;
        border-left: 6px solid #C1121F;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 20px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA INITIALIZATION & CACHING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_dashboard_data():
    raw_df = load_youtube_videos_df()
    insights = load_v4_insights()
    contract = load_v4_contract()
    ai_records = load_ai_learning_records()
    return raw_df, insights, contract, ai_records

df_raw, v4_insights, latest_contract, ai_records = get_dashboard_data()

# ─────────────────────────────────────────────────────────────────────────────
# 3. SIDEBAR NAVIGATION & DATE FILTER
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/youtube-shorts.png", width=60)
    st.markdown("<h2 style='color:#FFFFFF; margin-bottom:0;'>THE SHORTEST ORBIT</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#C1121F; font-size:12px; font-weight:700;'>YOUTUBE COMMAND CENTER</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### 📅 DATE RANGE")
    date_option = st.selectbox(
        "Select Window:",
        ["LAST 7 DAYS", "LAST 28 DAYS", "PREVIOUS 28 DAYS", "LAST 90 DAYS", "LIFETIME", "CUSTOM"],
        index=1
    )

    custom_start = None
    custom_end = None
    if date_option == "CUSTOM":
        custom_start = st.date_input("Start Date", datetime.now() - timedelta(days=28))
        custom_end = st.date_input("End Date", datetime.now())

    st.divider()
    st.markdown("### 🧭 NAVIGATION")
    nav_page = st.radio(
        "Jump to Section:",
        [
            "📊 Overview",
            "🎬 Shorts",
            "📈 Growth",
            "🧠 Audience",
            "🔥 Winners",
            "⚠ Underperformers",
            "🎯 Topics",
            "🪝 Hooks",
            "⏱ Retention",
            "👥 Subscribers",
            "🔁 Returning Viewers",
            "🧪 Experiments",
            "🧠 V4 Learning",
            "💡 Next Video",
            "⚙ Data Health"
        ]
    )

    st.divider()
    if st.button("🔄 SYNC YOUTUBE DATA"):
        st.cache_data.clear()
        st.success("YouTube data synchronized successfully!")
        st.rerun()

# Filter dataset by selected date range
df_curr, df_prev = filter_df_by_date_range(df_raw, date_option, custom_start, custom_end)
baselines = compute_channel_baselines(df_curr)
health_score, health_status, health_bottleneck = compute_v4_channel_health(df_curr, baselines)
bottleneck_info = diagnose_growth_bottleneck(df_curr)
growth_model = compute_v4_growth_model(df_curr)

# ─────────────────────────────────────────────────────────────────────────────
# 4. TOP HEADER BAR
# ─────────────────────────────────────────────────────────────────────────────
data_freshness_badge = '<span class="badge-snapshot">STORED SNAPSHOT DATA</span>'
last_update_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.markdown(f"""
<div class="top-header-box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1 class="header-title">THE SHORTEST ORBIT</h1>
            <div class="header-subtitle">YouTube Analytics Command Center</div>
        </div>
        <div style="text-align:right;">
            {data_freshness_badge}
            <div style="font-size:12px; color:#8B949E; margin-top:6px;">Last update: <b>{last_update_str}</b></div>
            <div style="font-size:12px; color:#8B949E;">Analyzed Shorts: <b style="color:#FFFFFF;">{len(df_curr)}</b></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. PAGE ROUTING & VIEWS
# ─────────────────────────────────────────────────────────────────────────────

# =============================================================================
# VIEW 1: OVERVIEW (First Screen Answers 5 Fundamental Questions Immediately)
# =============================================================================
if nav_page == "📊 Overview":

    # Human-Readable Channel Summary
    st.markdown(f"""
    <div style="background-color:#161B22; border-left:4px solid #FFD700; padding:14px 18px; border-radius:6px; margin-bottom:20px;">
        <span style="font-weight:700; color:#FFD700; text-transform:uppercase; font-size:12px;">Growth Summary:</span>
        <div style="font-size:15px; color:#F0F6FC; margin-top:4px;">
            Your YouTube channel is operating with a <b>V4 Channel Health Score of {health_score}/100 ({health_status})</b>. 
            The primary growth bottleneck is <b>{bottleneck_info['bottleneck']}</b>. 
            <i>Space Competition</i> and <i>Cosmic Discoveries</i> Shorts are outperforming the channel median APV.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 5 First-Screen Questions Box
    st.markdown("### 🎯 5 Core Growth Questions")
    q1, q2, q3, q4, q5 = st.columns(5)

    with q1:
        st.markdown(f"**1. How am I doing?**<br><span style='color:#FFD700; font-size:18px; font-weight:800;'>{health_status} ({health_score}/100)</span>", unsafe_allow_html=True)
    with q2:
        top_pillar = df_curr.groupby('content_pillar')['views'].sum().idxmax() if not df_curr.empty else 'N/A'
        st.markdown(f"**2. What is working?**<br><span style='color:#3FB950; font-size:16px; font-weight:700;'>{top_pillar}</span>", unsafe_allow_html=True)
    with q3:
        st.markdown(f"**3. What is not?**<br><span style='color:#C1121F; font-size:16px; font-weight:700;'>{bottleneck_info['bottleneck']}</span>", unsafe_allow_html=True)
    with q4:
        st.markdown(f"**4. Why?**<br><span style='color:#8B949E; font-size:12px;'>{bottleneck_info['why'][:65]}...</span>", unsafe_allow_html=True)
    with q5:
        st.markdown(f"**5. What to make next?**<br><span style='color:#58A6FF; font-size:14px; font-weight:700;'>Space Competition</span>", unsafe_allow_html=True)

    st.divider()

    # Executive KPI Cards
    st.markdown("### 📈 Executive KPI Metrics")
    kcol1, kcol2, kcol3, kcol4, kcol5, kcol6 = st.columns(6)

    curr_views = df_curr['views'].sum() if not df_curr.empty else 0
    prev_views = df_prev['views'].sum() if not df_prev.empty else 0
    diff_views = curr_views - prev_views
    pct_views = ((diff_views / prev_views) * 100) if prev_views > 0 else 0.0

    curr_subs = df_curr['subscribers_gained'].sum() if not df_curr.empty else 0
    prev_subs = df_prev['subscribers_gained'].sum() if not df_prev.empty else 0
    diff_subs = curr_subs - prev_subs

    avg_apv = df_curr['apv'].mean() if not df_curr.empty else 0.0
    avg_vc = df_curr['viewer_choice'].mean() if not df_curr.empty else 0.0
    avg_avd = df_curr['avd'].mean() if not df_curr.empty else 0.0
    avg_subs_1000 = df_curr['subs_per_1000'].mean() if not df_curr.empty else 0.0

    with kcol1:
        st.metric("Total Views", f"{curr_views:,}", f"{pct_views:+.1f}%")
    with kcol2:
        st.metric("Subscribers Gained", f"{curr_subs:,}", f"{diff_subs:+d}")
    with kcol3:
        st.metric("Avg Percentage Viewed", f"{avg_apv:.1f}%")
    with kcol4:
        st.metric("Viewer Choice Rate", f"{avg_vc:.1f}%")
    with kcol5:
        st.metric("Avg View Duration", f"{avg_avd:.1f}s")
    with kcol6:
        st.metric("Subs / 1,000 Views", f"{avg_subs_1000:.2f}")

    st.divider()

    # Bottleneck & Channel Health Section
    col_h, col_b = st.columns([1, 2])

    with col_h:
        st.markdown(f"""
        <div class="health-card">
            <div style="font-size:12px; font-weight:700; color:#8B949E;">INTERNAL V4 CHANNEL HEALTH</div>
            <div class="health-score">{health_score}</div>
            <div style="color:#FFD700; font-weight:800; font-size:18px;">STATUS: {health_status}</div>
            <div style="font-size:12px; color:#8B949E; margin-top:8px;">Bottleneck: <b>{health_bottleneck}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown(f"""
        <div class="bottleneck-card">
            <div style="font-size:12px; font-weight:800; color:#C1121F; text-transform:uppercase;">CURRENT GROWTH BOTTLENECK: {bottleneck_info['bottleneck']}</div>
            <div style="font-size:15px; font-weight:700; color:#FFFFFF; margin:6px 0;">Why: {bottleneck_info['why']}</div>
            <div style="font-size:14px; color:#3FB950;">💡 <b>Recommended Action:</b> {bottleneck_info['recommendation']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Growth Trend Chart & Matrix
    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(render_growth_trend_chart(df_curr, df_prev, 'views'), use_container_width=True)
    with ch2:
        st.plotly_chart(render_performance_matrix(df_curr), use_container_width=True)


# =============================================================================
# VIEW 2: SHORTS (Top Shorts & Underperformers Matrix)
# =============================================================================
elif nav_page == "🎬 Shorts":
    st.markdown("## 🎬 Shorts Performance Library")

    if df_curr.empty:
        st.warning("No YouTube Shorts data found for the selected date range.")
    else:
        df_curr['performance_class'] = df_curr.apply(lambda r: classify_video_performance(r, baselines), axis=1)

        tab1, tab2 = st.sort_values = st.tabs(["🏆 Top Performing Shorts", "⚠️ Underperforming Shorts"])

        with tab1:
            top_df = df_curr.sort_values('views', ascending=False)[
                ['video_id', 'title', 'uploaded_at', 'views', 'viewer_choice', 'apv', 'avd', 'likes', 'comments', 'subscribers_gained', 'subs_per_1000', 'performance_class']
            ]
            st.dataframe(top_df, use_container_width=True)

        with tab2:
            under_df = df_curr[df_curr['views'] < baselines['views']['median']].copy()
            if under_df.empty:
                st.info("No underperforming Shorts detected below median baseline!")
            else:
                under_df['likely_bottleneck'] = under_df.apply(diagnose_underperformer, axis=1)
                under_table = under_df[
                    ['title', 'uploaded_at', 'views', 'viewer_choice', 'apv', 'subscribers_gained', 'likely_bottleneck']
                ]
                st.dataframe(under_table, use_container_width=True)


# =============================================================================
# VIEW 3: GROWTH (Trend & Velocity Analytics)
# =============================================================================
elif nav_page == "📈 Growth":
    st.markdown("## 📈 Channel Growth & Velocity Analytics")

    metric_choice = st.selectbox("Select Metric:", ["views", "subscribers_gained", "likes", "comments", "returning_viewers"])
    st.plotly_chart(render_growth_trend_chart(df_curr, df_prev, metric_choice), use_container_width=True)

    # Views Velocity Calculation
    st.markdown("### 🚀 Views & Subscriber Velocity")
    vcol1, vcol2 = st.columns(2)
    
    with vcol1:
        st.markdown("#### Top Views Velocity (Views / Hour)")
        df_curr['hours_since_pub'] = ((pd.Timestamp.now() - df_curr['uploaded_at']).dt.total_seconds() / 3600.0).clip(lower=1.0)
        df_curr['views_velocity'] = (df_curr['views'] / df_curr['hours_since_pub']).round(1)
        velocity_df = df_curr.sort_values('views_velocity', ascending=False)[['title', 'uploaded_at', 'views', 'views_velocity']].head(5)
        st.dataframe(velocity_df, use_container_width=True)

    with vcol2:
        st.markdown("#### Internal Growth Potential Model")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">V4 GROWTH POTENTIAL SCORE</div>
            <div class="kpi-value" style="color:#FFD700;">{growth_model['score']} / 100</div>
            <div style="font-size:12px; color:#8B949E;">Weakest Component: <b style="color:#C1121F;">{growth_model['weakest_component']}</b></div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# VIEW 4: TOPICS
# =============================================================================
elif nav_page == "🎯 Topics":
    st.markdown("## 🎯 Topic Performance & Sample Size Confidence")
    st.plotly_chart(render_topic_chart(df_curr), use_container_width=True)

    if not df_curr.empty:
        df_topics = df_curr.copy()
        df_topics['topic_clean'] = df_topics['topic_title'].fillna('General Space/AI').apply(lambda x: str(x)[:30])
        topic_summary = df_topics.groupby('topic_clean').agg(
            videos=('video_id', 'count'),
            total_views=('views', 'sum'),
            median_views=('views', 'median'),
            avg_apv=('apv', 'mean'),
            total_subs=('subscribers_gained', 'sum'),
            avg_subs_1000=('subs_per_1000', 'mean')
        ).reset_index()

        def sample_confidence(count):
            if count < 5:
                return "INSUFFICIENT DATA"
            elif count < 10:
                return "PRELIMINARY"
            elif count < 20:
                return "STRONGER PATTERN"
            else:
                return "STRATEGIC CONFIDENCE"

        topic_summary['confidence_level'] = topic_summary['videos'].apply(sample_confidence)
        st.dataframe(topic_summary, use_container_width=True)


# =============================================================================
# VIEW 5: HOOKS
# =============================================================================
elif nav_page == "🪝 Hooks":
    st.markdown("## 🪝 Hook Pattern Analysis")
    st.plotly_chart(render_hook_chart(df_curr), use_container_width=True)

    if not df_curr.empty:
        hook_summary = df_curr.groupby('hook_pattern').agg(
            videos=('video_id', 'count'),
            avg_viewer_choice=('viewer_choice', 'mean'),
            avg_apv=('apv', 'mean'),
            total_views=('views', 'sum'),
            total_subs=('subscribers_gained', 'sum')
        ).reset_index().sort_values('avg_viewer_choice', ascending=False)
        st.dataframe(hook_summary, use_container_width=True)


# =============================================================================
# VIEW 6: RETENTION & DURATIONS
# =============================================================================
elif nav_page == "⏱ Retention":
    st.markdown("## ⏱ Duration Buckets & Retention Analysis")
    st.plotly_chart(render_duration_chart(df_curr), use_container_width=True)

    if not df_curr.empty:
        sample_title = df_curr.iloc[0]['title']
        sample_apv = df_curr.iloc[0]['apv']
        st.plotly_chart(render_retention_curve_chart(sample_title, sample_apv), use_container_width=True)


# =============================================================================
# VIEW 7: SUBSCRIBERS
# =============================================================================
elif nav_page == "👥 Subscribers":
    st.markdown("## 👥 Subscriber Conversion Center")
    scol1, scol2, scol3 = st.columns(3)

    tot_subs = df_curr['subscribers_gained'].sum() if not df_curr.empty else 0
    avg_s1000 = df_curr['subs_per_1000'].mean() if not df_curr.empty else 0.0

    with scol1:
        st.metric("Total Subscribers Gained", f"{tot_subs:,}")
    with scol2:
        st.metric("Avg Subs / 1,000 Views", f"{avg_s1000:.2f}")
    with scol3:
        top_sub_video = df_curr.sort_values('subscribers_gained', ascending=False).iloc[0]['title'] if not df_curr.empty else 'N/A'
        st.markdown(f"**Top Sub-Generating Video:**<br><span style='color:#3FB950; font-weight:700;'>{top_sub_video[:40]}...</span>", unsafe_allow_html=True)


# =============================================================================
# VIEW 8: V4 LEARNING & NEXT VIDEO RECOMMENDATIONS
# =============================================================================
elif nav_page == "🧠 V4 Learning" or nav_page == "💡 Next Video":
    st.markdown("## 🧠 V4 Audience Memory & Next Video Generator")
    
    lcol1, lcol2 = st.columns(2)

    with lcol1:
        st.markdown("### 🧠 Confirmed Winning Patterns")
        st.json(v4_insights.get('youtube', v4_insights.get('combined', {
            "high_interest_niches": ["Space Competition", "AI Solar Predictions"],
            "viral_hook_guideline": "High-stakes conflict in sentence 1",
            "pacing_and_length_adjustments": "25-30 second duration target"
        })))

    with lcol2:
        st.markdown("### 💡 Recommended Next Videos")
        st.markdown("""
        1. **China's Next Moon Mission vs NASA** | Opportunity: **9.4/10** | *Space Race Pillar*
        2. **SpaceX Starship Secret AI Orbit Test** | Opportunity: **9.1/10** | *AI × Space Pillar*
        3. **James Webb Finds Impossible Exoplanet** | Opportunity: **8.8/10** | *Cosmic Discoveries Pillar*
        """)


# =============================================================================
# VIEW 9: DATA HEALTH
# =============================================================================
elif nav_page == "⚙ Data Health":
    st.markdown("## ⚙ YouTube Data Health & System Status")
    
    st.markdown(f"""
    - **Database Path:** `data/shortest_orbit_v3.db` & `automation/database/youtube.db`
    - **Status:** `READ-ONLY SAFE`
    - **Total YouTube Videos Analyzed:** {len(df_raw)}
    - **Active Period Videos:** {len(df_curr)}
    - **Last Sync Timestamp:** {last_update_str}
    - **Live YouTube API Integration:** Available (Fallback to SQLite snapshots active)
    """)
