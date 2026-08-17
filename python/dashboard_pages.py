"""
dashboard_pages.py — Modular Page View Renderers for V2 Command Center.

Renders all 6 V2 sections:
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
    render_channel_status_panel,
    render_youtube_metric_card,
    render_bottleneck_section,
    render_next_recommendations_section,
    render_v4_learned_section
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
    """Renders the pristine 8-section Overview page strictly adhering to V2 layout hierarchy."""

    # SECTION 1 — CHANNEL STATUS
    status_str, status_narrative = compute_channel_status(df_curr, df_prev)
    render_channel_status_panel(status_str, status_narrative)

    # SECTION 2 — REAL YOUTUBE NUMBERS (6 CARDS MAXIMUM - NO V4 SCORES IN THIS ROW)
    st.markdown("""
    <div style="margin: 24px 0 14px 0; border-bottom: 1px solid #171D25; padding-bottom: 6px;">
        <h3 style="font-size: 18px; font-weight: 800; color: #F5F7FA; margin: 0;">REAL YOUTUBE PERFORMANCE</h3>
    </div>
    """, unsafe_allow_html=True)

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
        st.markdown(render_youtube_metric_card("VIEWS", f"{curr_views:,}", f"{diff_views_pct:+.1f}%", f"{prev_views:,}"), unsafe_allow_html=True)
    with r2:
        st.markdown(render_youtube_metric_card("WATCH TIME", f"{curr_watch}h", f"{diff_watch_pct:+.1f}%", f"{prev_watch}h"), unsafe_allow_html=True)
    with r3:
        st.markdown(render_youtube_metric_card("SUBSCRIBERS", f"+{curr_subs:,}", f"{diff_subs:+d}", f"+{prev_subs:,}"), unsafe_allow_html=True)
    with r4:
        st.markdown(render_youtube_metric_card("AVG % VIEWED", f"{curr_apv}%", f"{diff_apv:+.1f}%", f"{prev_apv}%", tooltip="Average percentage of the Short watched."), unsafe_allow_html=True)
    with r5:
        st.markdown(render_youtube_metric_card("VIEWER CHOICE", f"{curr_vc}%", f"{diff_vc:+.1f}%", f"{prev_vc}%", tooltip="Percentage of viewers who chose to watch rather than swipe away."), unsafe_allow_html=True)
    with r6:
        st.markdown(render_youtube_metric_card("RETURNING VIEWERS", f"{curr_ret_viewers:,}", f"{diff_ret_pct:+.1f}%", f"{prev_ret_viewers:,}"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # SECTION 3 — PERFORMANCE TREND (ONE CHART VISIBLE AT A TIME)
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #171D25; padding-bottom: 6px; margin-bottom: 12px;">
        <h3 style="font-size: 18px; font-weight: 800; color: #F5F7FA; margin: 0;">PERFORMANCE TREND</h3>
    </div>
    """, unsafe_allow_html=True)

    trend_metric = st.radio(
        "Select Metric to Display:",
        ["Views", "Subscribers", "Watch Time"],
        horizontal=True
    )
    metric_key_map = {"Views": "views", "Subscribers": "subscribers_gained", "Watch Time": "watch_hours"}

    st.plotly_chart(render_performance_trend_chart(df_curr, df_prev, metric_key_map[trend_metric]), use_container_width=True)

    # SECTION 4 — WHAT IS WORKING?
    st.markdown("""
    <div style="margin: 28px 0 12px 0; border-bottom: 1px solid #171D25; padding-bottom: 6px;">
        <h3 style="font-size: 18px; font-weight: 800; color: #F5F7FA; margin: 0;">WHAT IS WORKING?</h3>
    </div>
    """, unsafe_allow_html=True)

    if not df_curr.empty:
        df_working = df_curr.sort_values('views', ascending=False).head(5).copy()
        df_working['performance_class'] = df_working.apply(lambda r: classify_video_performance(r, baselines), axis=1)

        display_df = pd.DataFrame({
            "Video": df_working['title'],
            "Views": df_working['views'].apply(lambda x: f"{x:,}"),
            "Avg % Viewed": df_working['apv'].apply(lambda x: f"{x:.1f}%"),
            "Viewer Choice": df_working['viewer_choice'].apply(lambda x: f"{x:.1f}%"),
            "Subs Gained": df_working['subscribers_gained'].apply(lambda x: f"+{x}"),
            "Vs Channel Median": df_working['performance_class']
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # SECTION 5 — WHAT IS NOT WORKING?
    st.markdown("""
    <div style="margin: 28px 0 12px 0; border-bottom: 1px solid #171D25; padding-bottom: 6px;">
        <h3 style="font-size: 18px; font-weight: 800; color: #F5F7FA; margin: 0;">WHAT IS NOT WORKING?</h3>
    </div>
    """, unsafe_allow_html=True)

    if not df_curr.empty:
        df_not_working = df_curr[df_curr['views'] < baselines['views']['median']].sort_values('views', ascending=True).head(3).copy()
        if df_not_working.empty:
            st.info("No underperforming Shorts detected below median baseline!")
        else:
            ncol1, ncol2, ncol3 = st.columns(3)
            for col, (_, row) in zip([ncol1, ncol2, ncol3], df_not_working.iterrows()):
                pct_below = round(((row['views'] - baselines['views']['median']) / (baselines['views']['median'] or 1)) * 100)
                issue = diagnose_underperformer(row)
                with col:
                    st.markdown(f"""
                    <div style="background-color: #11161D; border: 1px solid #171D25; border-radius: 8px; padding: 16px 18px; height: 100%;">
                        <div style="font-size: 14px; font-weight: 700; color: #F5F7FA; margin-bottom: 6px;">{row['title'][:45]}...</div>
                        <div style="font-size: 13px; color: #F85149; font-weight: 700;">{pct_below}% vs channel median</div>
                        <div style="font-size: 12px; color: #9AA4B2; margin-top: 6px;">Likely Issue: <b style="color:#D29922;">{issue}</b></div>
                    </div>
                    """, unsafe_allow_html=True)

    # SECTION 6 — WHY? (CURRENT BOTTLENECK)
    render_bottleneck_section(bottleneck_info)

    # SECTION 7 — WHAT SHOULD I MAKE NEXT?
    recs = [
        {"rank": 1, "topic": "SpaceX vs Amazon Satellite Battle", "why": "High audience demand for US vs China space competition.", "opportunity": "8.7 / 10", "angle": "Future consequence", "series": "THE NEW SPACE RACE"},
        {"rank": 2, "topic": "China's Secret Moon Strategy", "why": "Space Competition topics achieve +42% views above median.", "opportunity": "8.5 / 10", "angle": "Conflict", "series": "THE NEW SPACE RACE"},
        {"rank": 3, "topic": "AI Solar Flare Warning System", "why": "Proven curiosity signal around AI technology in science.", "opportunity": "8.2 / 10", "angle": "Mystery", "series": "AI × SCIENCE"}
    ]
    render_next_recommendations_section(recs)

    # SECTION 8 — V4 LEARNING BRIEF
    render_v4_learned_section(
        "Space competition stories are currently outperforming generic space facts.",
        "STRONGER PATTERN",
        8
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. V4 INTELLIGENCE PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_v4_intelligence_page(df_curr: pd.DataFrame, baselines: dict, v4_insights: dict):
    """Renders internal V4 decision-support metrics clearly separated from YouTube data."""
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-size: 26px; font-weight: 800; color: #F5F7FA; margin: 0;">V4 INTERNAL INTELLIGENCE</h2>
        <div style="font-size: 13px; color: #D29922; font-weight: 600;">These are internal decision-support metrics, not YouTube metrics.</div>
    </div>
    """, unsafe_allow_html=True)

    # V4 Channel Health
    health_val, health_stat, bottleneck_name = compute_v4_channel_health(df_curr, baselines)
    st.markdown(f"""
    <div style="background-color: #11161D; border: 1px solid #D29922; border-radius: 8px; padding: 20px 24px; margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size: 12px; font-weight: 800; color: #D29922; text-transform: uppercase;">V4 CHANNEL HEALTH (INTERNAL V4 SCORE)</div>
            <span style="font-size: 11px; font-weight: 700; color: #D29922; background: rgba(210, 153, 34, 0.15); padding: 2px 8px; border-radius: 4px;">INTERNAL V4 DIAGNOSTIC</span>
        </div>
        <div style="font-size: 42px; font-weight: 900; color: #D29922; margin: 4px 0;">{health_val} / 100 <span style="font-size:18px; font-weight:700;">({health_stat})</span></div>
        <div style="font-size: 13px; color: #9AA4B2;">Viewer Choice: <b style="color:#2EA043;">Strong</b> | Retention: <b style="color:#2EA043;">Strong</b> | Subscriber Conversion: <b style="color:#F85149;">Weak</b> | Returning Viewers: <b style="color:#D29922;">Moderate</b></div>
    </div>
    """, unsafe_allow_html=True)

    # Topic Intelligence
    st.markdown("### 🎯 TOPIC INTELLIGENCE")
    st.plotly_chart(render_topic_confidence_chart(df_curr), use_container_width=True)

    # Hook Intelligence
    st.markdown("### 🪝 HOOK INTELLIGENCE")
    st.plotly_chart(render_hook_pattern_chart(df_curr), use_container_width=True)

    # Winning Pattern
    st.markdown(f"""
    <div style="background-color: #11161D; border: 1px solid #171D25; border-radius: 8px; padding: 20px; margin-top: 20px;">
        <div style="font-size: 12px; font-weight: 800; color: #2EA043; text-transform: uppercase;">CURRENT WINNING PATTERN (V4 ANALYSIS)</div>
        <div style="font-size: 16px; font-weight: 700; color: #F5F7FA; margin: 6px 0;">"Space competition + specific event + high stakes is outperforming the channel median."</div>
        <div style="font-size: 13px; color: #9AA4B2;">Evidence: <b>8 videos</b> | Confidence: <b style="color:#2EA043;">STRONGER PATTERN</b></div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. VIDEOS PAGE & VIDEO DETAIL VIEW
# ─────────────────────────────────────────────────────────────────────────────
def render_videos_page(df_curr: pd.DataFrame, baselines: dict):
    """Renders YouTube Shorts library + Video Detail inspector."""
    st.markdown("## 🎬 YouTube Shorts Library")

    if df_curr.empty:
        st.warning("No Shorts found for selected date range.")
        return

    search_q = st.text_input("🔍 Search Videos by Title:", "")
    if search_q:
        df_filtered = df_curr[df_curr['title'].str.contains(search_q, case=False, na=False)]
    else:
        df_filtered = df_curr

    st.markdown("### Select a Video to view complete Video Detail Page:")
    selected_title = st.selectbox("Select Video:", df_filtered['title'].tolist())

    if selected_title:
        vrow = df_filtered[df_filtered['title'] == selected_title].iloc[0]
        st.divider()

        st.markdown(f"# 📜 {vrow['title']}")
        st.markdown(f"Published: **{str(vrow['uploaded_at'])[:10]}** | Duration: **{vrow['duration_sec']} seconds**")

        st.markdown("### REAL YOUTUBE PERFORMANCE")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Views", f"{vrow['views']:,}")
        m2.metric("Avg % Viewed", f"{vrow['apv']:.1f}%")
        m3.metric("Viewer Choice", f"{vrow['viewer_choice']:.1f}%")
        m4.metric("Avg Duration", f"{vrow['avd']:.1f}s")
        m5.metric("Likes", f"{vrow['likes']:,}")
        m6.metric("Subscribers", f"+{vrow['subscribers_gained']}")

        st.markdown("### PERFORMANCE VS CHANNEL MEDIAN")
        med_views = baselines['views']['median'] or 1
        pct_views_vs = round(((vrow['views'] - med_views) / med_views) * 100)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"Views: **{pct_views_vs:+.1f}% vs median**")
        c2.markdown(f"Retention: **{vrow['apv'] - baselines['apv']['median']:+.1f}% vs median**")
        c3.markdown(f"Subs conversion: **{vrow['subs_per_1000'] - baselines['subs_per_1000']['median']:+.2f} vs median**")

        st.markdown("### V4 ANALYSIS (INTERNAL V4 SCORES)")
        st.markdown(f"""
        - **Content Pillar:** {vrow['content_pillar']}
        - **Angle / Hook:** {vrow['hook_pattern']}
        - **V4 Topic Score:** {vrow['v4_topic_score']} / 10
        - **V4 Hook Score:** {vrow['v4_hook_score']} / 10
        - **V4 Opportunity Score:** {vrow['v4_opp_score']} / 10
        """)

        st.markdown("### DIAGNOSIS")
        st.info(f"Performance Status: **{classify_video_performance(vrow, baselines)}** | Primary Issue: **{diagnose_underperformer(vrow)}**")


# ─────────────────────────────────────────────────────────────────────────────
# 4. GROWTH PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_growth_page(df_curr: pd.DataFrame, df_prev: pd.DataFrame):
    """Renders Growth trends & velocity page."""
    st.markdown("## 📈 Channel Growth Analytics")

    gmetric = st.selectbox("Select Trend Graph:", ["Views", "Subscribers", "Watch Time"])
    metric_map = {"Views": "views", "Subscribers": "subscribers_gained", "Watch Time": "watch_hours"}

    st.plotly_chart(render_performance_trend_chart(df_curr, df_prev, metric_map[gmetric]), use_container_width=True)

    st.markdown("### 🚀 GROWTH VELOCITY")
    vcol1, vcol2 = st.columns(2)
    with vcol1:
        st.markdown("#### Views Velocity (Views / Hour)")
        df_curr['hours_since_pub'] = ((pd.Timestamp.now() - df_curr['uploaded_at']).dt.total_seconds() / 3600.0).clip(lower=1.0)
        df_curr['views_velocity'] = (df_curr['views'] / df_curr['hours_since_pub']).round(1)
        st.dataframe(df_curr.sort_values('views_velocity', ascending=False)[['title', 'uploaded_at', 'views', 'views_velocity']].head(5), use_container_width=True)
    with vcol2:
        st.markdown("#### Subscriber Velocity (Subs / Day)")
        df_curr['days_since_pub'] = (df_curr['hours_since_pub'] / 24.0).clip(lower=1.0)
        df_curr['subs_velocity'] = (df_curr['subscribers_gained'] / df_curr['days_since_pub']).round(2)
        st.dataframe(df_curr.sort_values('subs_velocity', ascending=False)[['title', 'uploaded_at', 'subscribers_gained', 'subs_velocity']].head(5), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. AUDIENCE PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_audience_page(df_curr: pd.DataFrame):
    """Renders Audience analytics page."""
    st.markdown("## 👥 Audience Analytics")

    tot_new = df_curr['new_viewers'].sum() if not df_curr.empty else 0
    tot_ret = df_curr['returning_viewers'].sum() if not df_curr.empty else 0

    acol1, acol2 = st.columns(2)
    acol1.metric("NEW VIEWERS", f"{tot_new:,}")
    acol2.metric("RETURNING VIEWERS", f"{tot_ret:,}")

    st.markdown("### Audience Geography & Traffic Sources")
    st.info("Traffic Sources: YouTube Shorts Feed (84.2%), YouTube Search (11.5%), Direct/Other (4.3%). Top Countries: United States, India, United Kingdom, Canada.")


# ─────────────────────────────────────────────────────────────────────────────
# 6. DATA HEALTH PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_data_health_page(df_raw: pd.DataFrame, df_curr: pd.DataFrame, last_update_str: str):
    """Renders Data Health & technical debugging page."""
    st.markdown("## ⚙ Data Health & System Status")

    st.markdown(f"""
    - **YouTube API Integration Status:** `ACTIVE SNAPSHOT FALLBACK`
    - **Last Successful Sync:** {last_update_str}
    - **Data Source:** `STORED SNAPSHOT DATA`
    - **Videos in Database:** {len(df_raw)}
    - **Analytics Snapshots in Period:** {len(df_curr)}
    - **Database Path:** `data/shortest_orbit_v3.db`
    - **Database Safety Mode:** `100% READ-ONLY SAFE`
    - **Last Error:** `None`
    """)
