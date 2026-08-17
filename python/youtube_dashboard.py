"""
youtube_dashboard.py - THE SHORTEST ORBIT YouTube Command Center Dashboard.

Clean master orchestrator using fully separated modular architecture:
- dashboard_data.py       (Data Access & Caching)
- dashboard_metrics.py    (Metrics & Growth Calculations)
- dashboard_charts.py     (Plotly Visualizations)
- dashboard_components.py (Visual UI Components)
- dashboard_pages.py      (Modular Page View Renderers)
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import modular layers
from dashboard_data import (
    load_youtube_videos_df,
    filter_df_by_date_range,
    load_v4_insights,
    load_v4_contract
)
from dashboard_metrics import (
    compute_channel_baselines,
    compute_v4_channel_health,
    diagnose_growth_bottleneck,
    classify_video_performance,
    compute_v4_growth_model
)
from dashboard_components import render_header_component
from dashboard_pages import (
    render_page_overview,
    render_page_shorts,
    render_page_comparison,
    render_page_growth,
    render_page_topics,
    render_page_hooks,
    render_page_retention,
    render_page_subscribers,
    render_page_learning,
    render_page_health
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. STREAMLIT PAGE CONFIG & GLOBAL STYLING
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="THE SHORTEST ORBIT — YouTube Command Center",
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
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
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
    return raw_df, insights, contract

df_raw, v4_insights, latest_contract = load_data()

# ─────────────────────────────────────────────────────────────────────────────
# 3. SIDEBAR NAVIGATION & CONTROLS
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/youtube-shorts.png", width=55)
    st.markdown("<h2 style='color:#FFFFFF; margin-bottom:0; font-size:20px;'>THE SHORTEST ORBIT</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#C1121F; font-size:11px; font-weight:700;'>YOUTUBE COMMAND CENTER</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### 📅 DATE RANGE")
    date_option = st.selectbox(
        "Select Time Window:",
        ["LAST 7 DAYS", "LAST 28 DAYS", "PREVIOUS 28 DAYS", "LAST 90 DAYS", "LIFETIME"],
        index=1
    )

    st.divider()
    st.markdown("### 🧭 MODULE SELECTOR")
    nav_module = st.radio(
        "Jump to Module:",
        [
            "📊 Executive Overview",
            "🎬 Shorts Library",
            "🔍 Side-by-Side Comparison",
            "📈 Growth & Velocity",
            "🎯 Topic Analysis",
            "🪝 Hook Analysis",
            "⏱ Retention & Durations",
            "👥 Subscribers",
            "🧠 V4 Learning",
            "⚙ Data Health"
        ]
    )

    st.divider()
    if st.button("🔄 SYNC YOUTUBE DATA"):
        st.cache_data.clear()
        st.success("YouTube data synchronized!")
        st.rerun()

# Filter data
df_curr, df_prev = filter_df_by_date_range(df_raw, date_option)
baselines = compute_channel_baselines(df_curr)
health_score, health_status, health_bottleneck = compute_v4_channel_health(df_curr, baselines)
bottleneck_info = diagnose_growth_bottleneck(df_curr)
growth_model = compute_v4_growth_model(df_curr)

if not df_curr.empty:
    df_curr['performance_class'] = df_curr.apply(lambda r: classify_video_performance(r, baselines), axis=1)

# ─────────────────────────────────────────────────────────────────────────────
# 4. RENDER TOP HEADER BANNER
# ─────────────────────────────────────────────────────────────────────────────
last_update_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
render_header_component(len(df_curr), last_update_str)

# ─────────────────────────────────────────────────────────────────────────────
# 5. DELEGATE TO SEPARATED PAGE MODULES
# ─────────────────────────────────────────────────────────────────────────────
if nav_module == "📊 Executive Overview":
    render_page_overview(df_curr, df_prev, health_score, health_status, health_bottleneck, bottleneck_info, baselines)

elif nav_module == "🎬 Shorts Library":
    render_page_shorts(df_curr, baselines)

elif nav_module == "🔍 Side-by-Side Comparison":
    render_page_comparison(df_curr)

elif nav_module == "📈 Growth & Velocity":
    render_page_growth(df_curr, df_prev, growth_model)

elif nav_module == "🎯 Topic Analysis":
    render_page_topics(df_curr)

elif nav_module == "🪝 Hook Analysis":
    render_page_hooks(df_curr)

elif nav_module == "⏱ Retention & Durations":
    render_page_retention(df_curr)

elif nav_module == "👥 Subscribers":
    render_page_subscribers(df_curr)

elif nav_module == "🧠 V4 Learning":
    render_page_learning(v4_insights)

elif nav_module == "⚙ Data Health":
    render_page_health(df_raw, df_curr, last_update_str)
