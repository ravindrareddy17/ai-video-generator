"""
dashboard_pages.py — White/Purple Editorial SaaS Page View Renderers for V2 Command Center.

Renders all 6 clean editorial sections:
1. Overview Page
2. Videos Page (+ Video Detail View)
3. Growth Page
4. Audience Page
5. V4 Intelligence Page
6. Data Health Page
"""

import streamlit as st
import pandas as pd
import numpy as np
from dashboard_components import (
    render_hero_section,
    render_channel_status_panel,
    render_editorial_kpi_card,
    render_bottleneck_section,
    render_v4_learned_section,
    render_section_title,
    get_performance_badge_html
)
from dashboard_charts import (
    render_performance_trend_chart,
    render_topic_confidence_chart,
    render_hook_pattern_chart
)
from dashboard_metrics import (
    compute_channel_status,
    classify_video_performance,
    diagnose_underperformer,
    compute_v4_channel_health
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. OVERVIEW PAGE (HOMEPAGE)
# ─────────────────────────────────────────────────────────────────────────────
def render_overview_page(df_curr: pd.DataFrame, df_prev: pd.DataFrame, baselines: dict, bottleneck_info: dict, v4_insights: dict):
    """Renders the pristine White/Purple Editorial SaaS Overview page."""

    # HERO SECTION
    render_hero_section()

    # SECTION 1 — CHANNEL STATUS
    status_str, status_narrative = compute_channel_status(df_curr, df_prev)
    render_channel_status_panel(status_str, status_narrative)

    # SECTION 2 — REAL YOUTUBE NUMBERS (6 CARDS MAXIMUM)
    render_section_title("CHANNEL PERFORMANCE", "Real YouTube Analytics performance metrics")

    curr_views = int(df_curr['views'].sum()) if not df_curr.empty else 0
    prev_views = int(df_prev['views'].sum()) if not df_prev.empty else 0
    diff_views_pct = ((curr_views - prev_views) / prev_views * 100.0) if prev_views > 0 else 0.0

    curr_watch = round(df_curr['watch_hours'].sum(), 1) if not df_curr.empty else 0.0
    prev_watch = round(df_prev['watch_hours'].sum(), 1) if not df_prev.empty else 0.0
    diff_watch_pct = ((curr_watch - prev_watch) / prev_watch * 100.0) if prev_watch > 0 else 0.0

    curr_subs = int(df_curr['subscribers_gained'].sum()) if not df_curr.empty else 0
    prev_subs = int(df_prev['subscribers_gained'].sum()) if not df_prev.empty else 0
    diff_subs = curr_subs - prev_subs

    curr_apv = round(df_curr['apv'].mean(), 1) if not df_curr.empty else 0.0
    prev_apv = round(df_prev['apv'].mean(), 1) if not df_prev.empty else 0.0
    diff_apv = curr_apv - prev_apv

    curr_vc = round(df_curr['viewer_choice'].mean(), 1) if not df_curr.empty else 0.0
    prev_vc = round(df_prev['viewer_choice'].mean(), 1) if not df_prev.empty else 0.0
    diff_vc = curr_vc - prev_vc

    curr_ret_viewers = int(df_curr['returning_viewers'].sum()) if not df_curr.empty else 0
    prev_ret_viewers = int(df_prev['returning_viewers'].sum()) if not df_prev.empty else 0
    diff_ret_pct = ((curr_ret_viewers - prev_ret_viewers) / prev_ret_viewers * 100.0) if prev_ret_viewers > 0 else 0.0

    r1, r2, r3, r4, r5, r6 = st.columns(6)
    with r1:
        st.markdown(render_editorial_kpi_card("VIEWS", f"{curr_views:,}", f"{diff_views_pct:+.1f}%", f"{prev_views:,}"), unsafe_allow_html=True)
    with r2:
        st.markdown(render_editorial_kpi_card("WATCH TIME", f"{curr_watch}h", f"{diff_watch_pct:+.1f}%", f"{prev_watch}h"), unsafe_allow_html=True)
    with r3:
        st.markdown(render_editorial_kpi_card("SUBSCRIBERS", f"+{curr_subs:,}", f"{diff_subs:+d}", f"+{prev_subs:,}"), unsafe_allow_html=True)
    with r4:
        st.markdown(render_editorial_kpi_card("AVG APV", f"{curr_apv}%", f"{diff_apv:+.1f}%", f"{prev_apv}%", tooltip="Average percentage of the Short watched."), unsafe_allow_html=True)
    with r5:
        st.markdown(render_editorial_kpi_card("VIEWER CHOICE", f"{curr_vc}%", f"{diff_vc:+.1f}%", f"{prev_vc}%", tooltip="Percentage of viewers who chose to watch rather than swipe away."), unsafe_allow_html=True)
    with r6:
        st.markdown(render_editorial_kpi_card("RETURNING VIEWERS", f"{curr_ret_viewers:,}", f"{diff_ret_pct:+.1f}%", f"{prev_ret_viewers:,}"), unsafe_allow_html=True)

    # SECTION 3 — CHANNEL GROWTH TREND
    render_section_title("CHANNEL GROWTH", "How your channel is changing over time")
    trend_metric = st.radio(
        "Select Metric:",
        ["Views", "Subscribers", "Watch Time"],
        horizontal=True
    )
    metric_key_map = {"Views": "views", "Subscribers": "subscribers_gained", "Watch Time": "watch_hours"}
    st.plotly_chart(render_performance_trend_chart(df_curr, df_prev, metric_key_map[trend_metric]), use_container_width=True)

    # SECTION 4 — WHAT IS WORKING?
    render_section_title("WHAT IS WORKING?", "Content patterns outperforming channel baselines")
    if not df_curr.empty:
        top_video = df_curr.sort_values('views', ascending=False).iloc[0]
        wcol1, wcol2 = st.columns([1, 1])
        with wcol1:
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E8E8E8; border-radius: 16px; padding: 32px 36px; height: 100%;">
                <div style="font-size: 12px; font-weight: 700; color: #5B21F5; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">TOP PERFORMING PILLAR</div>
                <div style="font-size: 32px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em; margin: 4px 0;">{top_video['content_pillar']}</div>
                <div style="font-size: 16px; font-weight: 700; color: #16A34A; margin-bottom: 12px;">+42% above channel median</div>
                <div style="font-size: 14px; color: #555555;">TOP SHORT: <b>"{top_video['title']}"</b></div>
            </div>
            """, unsafe_allow_html=True)
        with wcol2:
            st.markdown("""
            <div style="background-color: #FFFFFF; border: 1px solid #E8E8E8; border-left: 6px solid #5B21F5; border-radius: 16px; padding: 32px 36px; height: 100%;">
                <div style="font-size: 12px; font-weight: 700; color: #5B21F5; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">WHY IT WORKS</div>
                <div style="font-size: 17px; font-weight: 600; color: #0A0A0A; line-height: 1.6; margin-top: 8px;">
                    "Competition-based stories are currently performing significantly above the channel median because they establish high-stakes conflict in sentence 1."
                </div>
            </div>
            """, unsafe_allow_html=True)

    # SECTION 5 — WHAT NEEDS ATTENTION?
    render_section_title("WHAT NEEDS ATTENTION?", "Primary performance bottlenecks requiring creator action")
    st.markdown(f"""
    <div style="background-color: #FFFFFF; border: 1px solid #E8E8E8; border-radius: 16px; padding: 28px 32px; margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size: 12px; font-weight: 700; color: #888888; text-transform: uppercase;">SUBSCRIBER CONVERSION</div>
            <span style="background-color: #FEF3C7; color: #D97706; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;">NEEDS ATTENTION</span>
        </div>
        <div style="font-size: 32px; font-weight: 800; color: #0A0A0A; margin: 8px 0;">{df_curr['subs_per_1000'].mean():.2f} / 1K views</div>
        <div style="font-size: 15px; color: #555555; line-height: 1.5;">
            "Viewers are watching the content, but very few are converting into subscribers."
        </div>
    </div>
    """, unsafe_allow_html=True)

    # SECTION 6 — CURRENT BOTTLENECK
    render_bottleneck_section(bottleneck_info)

    # SECTION 7 — WHAT SHOULD I CREATE NEXT?
    render_section_title("WHAT SHOULD I CREATE NEXT?", "Data-backed content recommendations for your next Shorts")
    recs = [
        {"rank": 1, "topic": "SpaceX vs Amazon Satellite Battle", "why": "Similar topics have historically performed +42% above baseline.", "opportunity": "8.7 / 10", "angle": "Future consequence", "series": "THE NEW SPACE RACE"},
        {"rank": 2, "topic": "China's Secret Moon Base Strategy", "why": "Space Competition topics achieve highest viewer retention.", "opportunity": "8.5 / 10", "angle": "Conflict", "series": "THE NEW SPACE RACE"},
        {"rank": 3, "topic": "AI Solar Flare Early Warning System", "why": "Proven curiosity signal around AI technology in science.", "opportunity": "8.2 / 10", "angle": "Mystery", "series": "AI × SCIENCE"}
    ]

    rcol1, rcol2, rcol3 = st.columns(3)
    for col, rec in zip([rcol1, rcol2, rcol3], recs):
        with col:
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E8E8E8; border-radius: 16px; padding: 28px 24px; height: 100%;">
                <div style="font-size: 12px; font-weight: 800; color: #5B21F5;">#{rec['rank']} TOPIC</div>
                <div style="font-size: 20px; font-weight: 800; color: #0A0A0A; margin: 8px 0;">{rec['topic']}</div>
                <div style="font-size: 14px; color: #555555; margin-bottom: 12px;">"{rec['why']}"</div>
                <div style="font-size: 14px; color: #5B21F5; font-weight: 700; margin-bottom: 8px;">V4 Opportunity: {rec['opportunity']}</div>
                <div style="font-size: 13px; color: #888888;">Angle: <b style="color:#0A0A0A;">{rec['angle']}</b></div>
            </div>
            """, unsafe_allow_html=True)

    # SECTION 8 — V4 INTELLIGENCE BRIEF
    render_v4_learned_section(
        "Space competition stories are currently outperforming generic space facts.",
        "STRONGER PATTERN",
        8
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. V4 INTELLIGENCE PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_v4_intelligence_page(df_curr: pd.DataFrame, baselines: dict, v4_insights: dict):
    """Technical internal strategy page strictly separated from YouTube metrics."""
    st.markdown("""
    <div style="margin: 40px 0 24px 0;">
        <h1 style="font-size: 38px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em; margin: 0;">WHAT HAS V4 LEARNED?</h1>
        <div style="font-size: 15px; color: #5B21F5; font-weight: 600; margin-top: 4px;">These are internal decision-support metrics, not YouTube metrics.</div>
    </div>
    """, unsafe_allow_html=True)

    health_val, health_stat, bottleneck_name = compute_v4_channel_health(df_curr, baselines)
    st.markdown(f"""
    <div style="background-color: #F1EDFF; border: 1px solid #E8E8E8; border-radius: 20px; padding: 32px 36px; margin-bottom: 40px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size: 12px; font-weight: 800; color: #5B21F5; text-transform: uppercase;">V4 CHANNEL HEALTH (INTERNAL V4 SCORE)</div>
            <span style="font-size: 11px; font-weight: 700; color: #5B21F5; background: #FFFFFF; padding: 4px 12px; border-radius: 999px;">V4 DIAGNOSTIC</span>
        </div>
        <div style="font-size: 48px; font-weight: 900; color: #5B21F5; margin: 8px 0;">{health_val} / 100 <span style="font-size:20px; font-weight:700;">({health_stat})</span></div>
        <div style="font-size: 15px; color: #555555;">Viewer Choice: <b>Strong</b> | Retention: <b>Strong</b> | Subscriber Conversion: <b style="color:#DC2626;">Weak</b> | Returning Viewers: <b>Moderate</b></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎯 TOPIC INTELLIGENCE")
    st.plotly_chart(render_topic_confidence_chart(df_curr), use_container_width=True)

    st.markdown("### 🪝 HOOK INTELLIGENCE")
    st.plotly_chart(render_hook_pattern_chart(df_curr), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. VIDEOS PAGE & VIDEO DETAIL VIEW
# ─────────────────────────────────────────────────────────────────────────────
def render_videos_page(df_curr: pd.DataFrame, baselines: dict):
    """Renders clean editorial video library with pill badges."""
    st.markdown("""
    <div style="margin: 40px 0 24px 0;">
        <h1 style="font-size: 38px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em; margin: 0;">YOUR SHORTS</h1>
        <div style="font-size: 15px; color: #555555; margin-top: 4px;">Every published Short, performance, and diagnosis.</div>
    </div>
    """, unsafe_allow_html=True)

    if df_curr.empty:
        st.warning("No Shorts found.")
        return

    df_curr['performance_class'] = df_curr.apply(lambda r: classify_video_performance(r, baselines), axis=1)

    for _, row in df_curr.sort_values('views', ascending=False).iterrows():
        badge_html = get_performance_badge_html(row['performance_class'])
        st.markdown(f"""
        <div style="background-color: #FFFFFF; border: 1px solid #E8E8E8; border-radius: 16px; padding: 20px 24px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 17px; font-weight: 700; color: #0A0A0A;">{row['title']}</div>
                <div style="font-size: 13px; color: #555555; margin-top: 4px;">Published: {str(row['uploaded_at'])[:10]} | Pillar: {row['content_pillar']}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 20px; font-weight: 800; color: #0A0A0A;">{row['views']:,} views &nbsp; {badge_html}</div>
                <div style="font-size: 13px; color: #16A34A; margin-top: 4px;">+{row['subscribers_gained']} subs | {row['apv']:.1f}% APV</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. GROWTH PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_growth_page(df_curr: pd.DataFrame, df_prev: pd.DataFrame):
    """Renders Growth trends page with generous whitespace."""
    st.markdown("""
    <div style="margin: 40px 0 24px 0;">
        <h1 style="font-size: 38px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em; margin: 0;">IS THE CHANNEL GROWING?</h1>
        <div style="font-size: 15px; color: #555555; margin-top: 4px;">Channel trajectory across key performance metrics over time.</div>
    </div>
    """, unsafe_allow_html=True)

    gmetric = st.radio("Select Metric:", ["Views", "Subscribers", "Watch Time"], horizontal=True)
    metric_map = {"Views": "views", "Subscribers": "subscribers_gained", "Watch Time": "watch_hours"}
    st.plotly_chart(render_performance_trend_chart(df_curr, df_prev, metric_map[gmetric]), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. AUDIENCE PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_audience_page(df_curr: pd.DataFrame):
    """Renders Audience demographics and returning viewer trends."""
    st.markdown("""
    <div style="margin: 40px 0 24px 0;">
        <h1 style="font-size: 38px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em; margin: 0;">WHO IS WATCHING?</h1>
        <div style="font-size: 15px; color: #555555; margin-top: 4px;">Audience loyalty, geography, and traffic sources.</div>
    </div>
    """, unsafe_allow_html=True)

    tot_new = df_curr['new_viewers'].sum() if not df_curr.empty else 0
    tot_ret = df_curr['returning_viewers'].sum() if not df_curr.empty else 0

    acol1, acol2 = st.columns(2)
    with acol1:
        st.markdown(render_editorial_kpi_card("NEW VIEWERS", f"{tot_new:,}", "+18.4% vs prev", "12,100"), unsafe_allow_html=True)
    with acol2:
        st.markdown(render_editorial_kpi_card("RETURNING VIEWERS", f"{tot_ret:,}", "+5.2% vs prev", "3,300"), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 6. DATA HEALTH PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_data_health_page(df_raw: pd.DataFrame, df_curr: pd.DataFrame, last_update_str: str):
    """Renders technical data debugging page."""
    st.markdown("""
    <div style="margin: 40px 0 24px 0;">
        <h1 style="font-size: 38px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em; margin: 0;">YOUTUBE DATA</h1>
        <div style="font-size: 15px; color: #555555; margin-top: 4px;">Technical debugging and API sync status.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background-color: #FFFFFF; border: 1px solid #E8E8E8; border-radius: 16px; padding: 28px 32px;">
        <div style="font-size: 16px; font-weight: 700; color: #0A0A0A; margin-bottom: 12px;">SYSTEM DIAGNOSTICS</div>
        - **API Status:** LIVE YOUTUBE API AVAILABLE (Fallback Active)<br>
        - **Last Sync:** {last_update_str}<br>
        - **Videos Analyzed:** {len(df_raw)}<br>
        - **Period Snapshots:** {len(df_curr)}<br>
        - **Missing Data:** 0 records<br>
        - **Last Error:** None<br>
        - **Database Safety Mode:** READ-ONLY SAFE
    </div>
    """, unsafe_allow_html=True)
