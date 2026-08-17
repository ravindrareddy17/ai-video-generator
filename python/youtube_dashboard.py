"""
youtube_dashboard.py — THE SHORTEST ORBIT YouTube Growth Command Center V2.

White / Black / Purple Editorial SaaS Redesign.
Reproduces the design language of modern SaaS products:
- Pure white background (#FFFFFF)
- Bold black typography (#0A0A0A)
- Brand Purple accent (#5B21F5)
- Clean horizontal top navigation
- Generous whitespace & editorial typography (1280px controlled width)

Run with:
streamlit run python/youtube_dashboard.py
"""

import sys
import importlib
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd

# Ensure parent directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import local modular layers with explicit reload to guarantee hot-reload synchronization
import dashboard_data
import dashboard_metrics
import dashboard_charts
import dashboard_components
import dashboard_pages

importlib.reload(dashboard_data)
importlib.reload(dashboard_metrics)
importlib.reload(dashboard_charts)
importlib.reload(dashboard_components)
importlib.reload(dashboard_pages)

from dashboard_data import (
    load_youtube_videos_df,
    filter_df_by_date_range,
    load_v4_insights
)
from dashboard_metrics import (
    compute_channel_baselines,
    diagnose_growth_bottleneck
)
from dashboard_components import (
    render_purple_top_announcement_bar
)
from dashboard_pages import (
    render_overview_page,
    render_videos_page,
    render_growth_page,
    render_audience_page,
    render_v4_intelligence_page,
    render_data_health_page
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. STREAMLIT PAGE CONFIG & PURE WHITE EDITORIAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="THE SHORTEST ORBIT — YouTube Growth Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Pure White / Black / Purple Editorial CSS (#FFFFFF bg, #0A0A0A text, #5B21F5 purple)
st.markdown("""
<style>
    /* Pure White App Background */
    .stApp {
        background-color: #FFFFFF;
        color: #0A0A0A;
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Control Container Max Width (1280px Centered) */
    .block-container {
        max-width: 1280px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin: 0 auto !important;
    }

    /* Hide default Streamlit sidebar toggle if not needed */
    section[data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E8E8E8;
    }

    /* Purple Pill Buttons */
    .stButton>button {
        background-color: #5B21F5 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 10px 24px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background-color: #7C3AED !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(91, 33, 245, 0.25) !important;
    }

    /* Horizontal Radio Tabs Styling */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        gap: 16px;
    }
    div[role="radiogroup"] > label {
        background-color: #FFFFFF;
        border: 1px solid #E8E8E8;
        border-radius: 999px;
        padding: 8px 18px;
        font-weight: 600;
        font-size: 14px;
        color: #555555;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    div[role="radiogroup"] > label:hover {
        border-color: #5B21F5;
        color: #5B21F5;
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
    return raw_df, insights

df_raw, v4_insights = load_data()

# ─────────────────────────────────────────────────────────────────────────────
# 3. TOP PURPLE ANNOUNCEMENT BAR
# ─────────────────────────────────────────────────────────────────────────────
last_update_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
render_purple_top_announcement_bar("STORED YOUTUBE DATA", last_update_str)

# ─────────────────────────────────────────────────────────────────────────────
# 4. MAIN HORIZONTAL NAVIGATION BAR & CONTROLS
# ─────────────────────────────────────────────────────────────────────────────
nav_col1, nav_col2, nav_col3 = st.columns([2, 4, 1])

with nav_col1:
    st.markdown("""
    <div style="padding-top: 6px;">
        <span style="font-size: 22px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em;">THE SHORTEST ORBIT</span>
    </div>
    """, unsafe_allow_html=True)

with nav_col2:
    nav_page = st.radio(
        "",
        ["Overview", "Videos", "Growth", "Audience", "V4 Intelligence", "Data"],
        horizontal=True,
        label_visibility="collapsed"
    )

with nav_col3:
    if st.button("SYNC YOUTUBE"):
        st.cache_data.clear()
        st.success("YouTube data refreshed!")
        st.rerun()

st.divider()

# Optional Date Range selector dropdown
date_col1, date_col2 = st.columns([1, 4])
with date_col1:
    date_option = st.selectbox(
        "Time Window:",
        ["Last 7 Days", "Last 28 Days", "Previous 28 Days", "Last 90 Days", "Lifetime"],
        index=1
    )

df_curr, df_prev = filter_df_by_date_range(df_raw, date_option)
baselines = compute_channel_baselines(df_curr)
bottleneck_info = diagnose_growth_bottleneck(df_curr)

# ─────────────────────────────────────────────────────────────────────────────
# 5. ROUTE TO EDITORIAL SAAS PAGES
# ─────────────────────────────────────────────────────────────────────────────
if nav_page == "Overview":
    render_overview_page(df_curr, df_prev, baselines, bottleneck_info, v4_insights)

elif nav_page == "Videos":
    render_videos_page(df_curr, baselines)

elif nav_page == "Growth":
    render_growth_page(df_curr, df_prev)

elif nav_page == "Audience":
    render_audience_page(df_curr)

elif nav_page == "V4 Intelligence":
    render_v4_intelligence_page(df_curr, baselines, v4_insights)

elif nav_page == "Data":
    render_data_health_page(df_raw, df_curr, last_update_str)
