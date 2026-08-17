"""
youtube_dashboard.py — THE SHORTEST ORBIT YouTube Growth Command Center V2.

Production-ready Streamlit dashboard for YouTube Analytics & V4 Intelligence.
Clean dark space styling (#0B0F14 bg, #11161D panel, #171D25 secondary panel, #C1121F accent).
Enforces 6 compact navigation items and strict separation between YouTube data and V4 scores.

Run with:
streamlit run python/youtube_dashboard.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Local modular layers
from dashboard_data import (
    load_youtube_videos_df,
    filter_df_by_date_range,
    load_v4_insights
)
from dashboard_metrics import (
    compute_channel_baselines,
    diagnose_growth_bottleneck
)
from dashboard_components import render_top_header
from dashboard_pages import (
    render_overview_page,
    render_videos_page,
    render_growth_page,
    render_audience_page,
    render_v4_intelligence_page,
    render_data_health_page
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. STREAMLIT PAGE CONFIG & CLEAN V2 DARK THEME STYLING
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="THE SHORTEST ORBIT — YouTube Growth Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Strict V2 CSS Palette (#0B0F14 bg, #11161D panel, #171D25 secondary panel, #F5F7FA text, #9AA4B2 subtext, #C1121F accent)
st.markdown("""
<style>
    /* Dark Space V2 Background */
    .stApp {
        background-color: #0B0F14;
        color: #F5F7FA;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #11161D;
        border-right: 1px solid #171D25;
    }

    /* Radio button options spacing */
    div[role="radiogroup"] > label {
        padding: 6px 10px;
        border-radius: 4px;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #171D25;
        color: #F5F7FA;
        border: 1px solid #30363D;
        border-radius: 6px;
        font-weight: 600;
        width: 100%;
    }
    .stButton>button:hover {
        border-color: #C1121F;
        color: #C1121F;
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
# 3. SIDEBAR NAVIGATION (EXACTLY 6 ITEMS)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='color:#F5F7FA; margin-bottom:0; font-size:22px; font-weight:800;'>THE SHORTEST ORBIT</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#C1121F; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px;'>YOUTUBE COMMAND CENTER</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### DATE RANGE")
    date_option = st.selectbox(
        "Select Window:",
        ["Last 7 Days", "Last 28 Days", "Previous 28 Days", "Last 90 Days", "Lifetime", "Custom"],
        index=1
    )

    custom_start = None
    custom_end = None
    if date_option == "Custom":
        custom_start = st.date_input("Start Date", datetime.now() - pd.Timedelta(days=28))
        custom_end = st.date_input("End Date", datetime.now())

    st.divider()
    st.markdown("### NAVIGATION")
    nav_page = st.radio(
        "Select Section:",
        [
            "Overview",
            "Videos",
            "Growth",
            "Audience",
            "V4 Intelligence",
            "Data Health"
        ]
    )

    st.divider()
    last_update_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"<div style='font-size:11px; color:#9AA4B2;'>LAST SYNC:<br><b style='color:#F5F7FA;'>{last_update_str}</b></div><br>", unsafe_allow_html=True)

    if st.button("🔄 SYNC YOUTUBE DATA"):
        st.cache_data.clear()
        st.success("YouTube data synchronized!")
        st.rerun()

# Filter data
df_curr, df_prev = filter_df_by_date_range(df_raw, date_option, custom_start, custom_end)
baselines = compute_channel_baselines(df_curr)
bottleneck_info = diagnose_growth_bottleneck(df_curr)

# ─────────────────────────────────────────────────────────────────────────────
# 4. RENDER TOP HEADER BANNER
# ─────────────────────────────────────────────────────────────────────────────
render_top_header("STORED YOUTUBE DATA", last_update_str)

# ─────────────────────────────────────────────────────────────────────────────
# 5. ROUTE TO 6 COMPACT SECTIONS
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

elif nav_page == "Data Health":
    render_data_health_page(df_raw, df_curr, last_update_str)
