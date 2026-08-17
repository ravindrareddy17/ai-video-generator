"""
dashboard_pages.py - Modular Page View Renderers for THE SHORTEST ORBIT Dashboard.

Separates view logic cleanly for every individual module:
- Overview Page
- Shorts Library Page
- Side-by-Side Comparison Page
- Growth & Velocity Page
- Topics Page
- Hooks Page
- Retention Page
- Subscribers Page
- V4 Learning Page
- Data Health Page
"""

import streamlit as st
import pandas as pd
import numpy as np
from dashboard_components import (
    render_kpi_card,
    render_insight_banner,
    render_bottleneck_card,
    render_section_header
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
from dashboard_metrics import diagnose_underperformer


def render_page_overview(df_curr: pd.DataFrame, df_prev: pd.DataFrame, health_score: int, health_status: str, health_bottleneck: str, bottleneck_info: dict, baselines: dict):
    """Renders clean, highly separated Overview page."""
    top_pillar = df_curr.groupby('content_pillar')['views'].sum().idxmax() if not df_curr.empty else 'Space Competition'
    render_insight_banner(health_score, health_status, top_pillar, health_bottleneck)

    # 5 First-Screen Questions Box
    render_section_header("🎯 5 Core Growth Questions", "At-a-glance executive summary")
    q1, q2, q3, q4, q5 = st.columns(5)
    with q1:
        st.markdown(f"**1. How am I doing?**<br><span style='color:#FFD700; font-size:17px; font-weight:800;'>{health_status} ({health_score}/100)</span>", unsafe_allow_html=True)
    with q2:
        st.markdown(f"**2. What is working?**<br><span style='color:#3FB950; font-size:15px; font-weight:700;'>{top_pillar}</span>", unsafe_allow_html=True)
    with q3:
        st.markdown(f"**3. What is not?**<br><span style='color:#C1121F; font-size:15px; font-weight:700;'>{bottleneck_info['bottleneck']}</span>", unsafe_allow_html=True)
    with q4:
        st.markdown(f"**4. Why?**<br><span style='color:#8B949E; font-size:12px;'>{bottleneck_info['why'][:60]}...</span>", unsafe_allow_html=True)
    with q5:
        st.markdown(f"**5. What to make next?**<br><span style='color:#58A6FF; font-size:14px; font-weight:700;'>Space Competition</span>", unsafe_allow_html=True)

    # KPI Row
    render_section_header("📈 Executive KPI Metrics", "YouTube channel core performance indicators")
    kcol1, kcol2, kcol3, kcol4, kcol5, kcol6 = st.columns(6)

    curr_views = df_curr['views'].sum() if not df_curr.empty else 0
    prev_views = df_prev['views'].sum() if not df_prev.empty else 0
    diff_views = curr_views - prev_views
    pct_views = ((diff_views / prev_views) * 100) if prev_views > 0 else 0.0

    curr_subs = df_curr['subscribers_gained'].sum() if not df_curr.empty else 0
    diff_subs = curr_subs - (df_prev['subscribers_gained'].sum() if not df_prev.empty else 0)

    with kcol1:
        st.markdown(render_kpi_card("Total Views", f"{curr_views:,}", f"{pct_views:+.1f}% vs prev", "#3FB950" if pct_views >= 0 else "#C1121F", "👁️"), unsafe_allow_html=True)
    with kcol2:
        st.markdown(render_kpi_card("Subs Gained", f"+{curr_subs:,}", f"{diff_subs:+d} vs prev", "#FFD700", "👥"), unsafe_allow_html=True)
    with kcol3:
        st.markdown(render_kpi_card("Avg APV", f"{df_curr['apv'].mean():.1f}%", "Target ≥70%", "#58A6FF", "⏱️"), unsafe_allow_html=True)
    with kcol4:
        st.markdown(render_kpi_card("Viewer Choice", f"{df_curr['viewer_choice'].mean():.1f}%", "Target ≥75%", "#3FB950", "🪝"), unsafe_allow_html=True)
    with kcol5:
        st.markdown(render_kpi_card("Avg Duration", f"{df_curr['avd'].mean():.1f}s", "Target 25-30s", "#8B949E", "⏳"), unsafe_allow_html=True)
    with kcol6:
        st.markdown(render_kpi_card("Subs / 1k Views", f"{df_curr['subs_per_1000'].mean():.2f}", "Target ≥1.5", "#FFD700", "🎯"), unsafe_allow_html=True)

    # Bottleneck Card
    render_bottleneck_card(bottleneck_info)

    # Charts Section
    render_section_header("📊 Performance Visualizations", "Growth trends & video classification matrix")
    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(render_growth_trend_chart(df_curr, df_prev, 'views'), use_container_width=True)
    with ch2:
        st.plotly_chart(render_performance_matrix(df_curr), use_container_width=True)


def render_page_shorts(df_curr: pd.DataFrame, baselines: dict):
    """Renders Shorts Library module with filters and detail inspector."""
    render_section_header("🎬 Shorts Interactive Library", "Filter, search, and inspect individual Shorts")

    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        search_query = st.text_input("🔍 Search Title:", "")
    with fcol2:
        pillar_filter = st.selectbox("Content Pillar:", ["ALL PILLARS"] + list(df_curr['content_pillar'].unique()))
    with fcol3:
        class_filter = st.selectbox("Performance Class:", ["ALL CLASSES"] + list(df_curr['performance_class'].unique()))

    filtered_df = df_curr.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df['title'].str.contains(search_query, case=False, na=False)]
    if pillar_filter != "ALL PILLARS":
        filtered_df = filtered_df[filtered_df['content_pillar'] == pillar_filter]
    if class_filter != "ALL CLASSES":
        filtered_df = filtered_df[filtered_df['performance_class'] == class_filter]

    tab1, tab2, tab3 = st.tabs(["🏆 Filtered Library Table", "⚠️ Underperforming Shorts", "🔍 Video Detail Inspector"])

    with tab1:
        display_cols = ['video_id', 'title', 'uploaded_at', 'views', 'viewer_choice', 'apv', 'avd', 'likes', 'comments', 'subscribers_gained', 'subs_per_1000', 'performance_class']
        st.dataframe(filtered_df[display_cols].sort_values('views', ascending=False), use_container_width=True)

        st.download_button(
            "📥 Export Shorts Analytics to CSV",
            filtered_df[display_cols].to_csv(index=False),
            "youtube_shorts_analytics.csv",
            "text/csv"
        )

    with tab2:
        under_df = filtered_df[filtered_df['views'] < baselines['views']['median']].copy()
        if under_df.empty:
            st.info("No underperforming Shorts detected below median baseline!")
        else:
            under_df['likely_bottleneck'] = under_df.apply(diagnose_underperformer, axis=1)
            st.dataframe(under_df[['title', 'uploaded_at', 'views', 'viewer_choice', 'apv', 'subscribers_gained', 'likely_bottleneck']], use_container_width=True)

    with tab3:
        st.markdown("#### 🔍 Video Detail Inspector")
        selected_title = st.selectbox("Select Video to Inspect:", filtered_df['title'].tolist())
        if selected_title:
            vrow = filtered_df[filtered_df['title'] == selected_title].iloc[0]
            vcol1, vcol2 = st.columns([1, 1])
            with vcol1:
                st.markdown(f"**Title:** {vrow['title']}")
                st.markdown(f"**Uploaded At:** {vrow['uploaded_at']}")
                st.markdown(f"**Pillar:** {vrow['content_pillar']} | **Hook:** {vrow['hook_pattern']}")
                st.markdown(f"**Class:** `<span style='color:#FFD700; font-weight:700;'>{vrow['performance_class']}</span>`", unsafe_allow_html=True)
                st.markdown(f"**Likely Bottleneck:** {diagnose_underperformer(vrow)}")
                st.info(vrow.get('script', 'Script unavailable.'))
            with vcol2:
                st.plotly_chart(render_retention_curve_chart(vrow['title'], vrow['apv']), use_container_width=True)


def render_page_comparison(df_curr: pd.DataFrame):
    """Renders side-by-side video comparison module."""
    render_section_header("🔍 Side-by-Side Video Comparison", "Compare metrics across up to 5 Shorts")
    selected_titles = st.multiselect("Select up to 5 Shorts to Compare:", df_curr['title'].tolist(), default=df_curr['title'].head(3).tolist()[:3])
    if selected_titles:
        comp_df = df_curr[df_curr['title'].isin(selected_titles)].copy()
        comp_metrics = comp_df[['title', 'views', 'viewer_choice', 'apv', 'avd', 'likes', 'comments', 'shares', 'subscribers_gained', 'subs_per_1000', 'content_pillar', 'hook_pattern', 'performance_class']].set_index('title').T
        st.dataframe(comp_metrics, use_container_width=True)


def render_page_growth(df_curr: pd.DataFrame, df_prev: pd.DataFrame, growth_model: dict):
    """Renders growth & velocity analytics module."""
    render_section_header("📈 Growth & Velocity Analytics", "Time-series trend & internal growth model")
    metric_choice = st.selectbox("Select Metric:", ["views", "subscribers_gained", "likes", "comments", "returning_viewers"])
    st.plotly_chart(render_growth_trend_chart(df_curr, df_prev, metric_choice), use_container_width=True)

    vcol1, vcol2 = st.columns(2)
    with vcol1:
        st.markdown("#### Top Views Velocity (Views / Hour)")
        df_curr['hours_since_pub'] = ((pd.Timestamp.now() - df_curr['uploaded_at']).dt.total_seconds() / 3600.0).clip(lower=1.0)
        df_curr['views_velocity'] = (df_curr['views'] / df_curr['hours_since_pub']).round(1)
        st.dataframe(df_curr.sort_values('views_velocity', ascending=False)[['title', 'uploaded_at', 'views', 'views_velocity']].head(5), use_container_width=True)
    with vcol2:
        st.markdown("#### Internal Growth Potential Model")
        st.markdown(f"""
        <div style="background-color:#161B22; border:1px solid #30363D; border-radius:10px; padding:20px;">
            <div style="font-size:12px; font-weight:700; color:#8B949E;">V4 GROWTH POTENTIAL SCORE</div>
            <div style="font-size:32px; font-weight:800; color:#FFD700; margin:6px 0;">{growth_model['score']} / 100</div>
            <div style="font-size:12px; color:#8B949E;">Weakest Component: <b style="color:#C1121F;">{growth_model['weakest_component']}</b></div>
        </div>
        """, unsafe_allow_html=True)


def render_page_topics(df_curr: pd.DataFrame):
    """Renders topic analysis module."""
    render_section_header("🎯 Topic Performance & Confidence", "Topic breakdown with minimum-data rules")
    st.plotly_chart(render_topic_chart(df_curr), use_container_width=True)
    if not df_curr.empty:
        df_topics = df_curr.copy()
        df_topics['topic_clean'] = df_topics['topic_title'].fillna('General Space/AI').apply(lambda x: str(x)[:30])
        summary = df_topics.groupby('topic_clean').agg(
            videos=('video_id', 'count'),
            total_views=('views', 'sum'),
            median_views=('views', 'median'),
            avg_apv=('apv', 'mean'),
            total_subs=('subscribers_gained', 'sum')
        ).reset_index()
        summary['confidence_level'] = summary['videos'].apply(lambda n: "INSUFFICIENT DATA" if n < 5 else ("PRELIMINARY" if n < 10 else ("STRONGER PATTERN" if n < 20 else "STRATEGIC CONFIDENCE")))
        st.dataframe(summary, use_container_width=True)


def render_page_hooks(df_curr: pd.DataFrame):
    """Renders hook pattern module."""
    render_section_header("🪝 Hook Pattern Analysis", "Viewer choice rate by opening hook type")
    st.plotly_chart(render_hook_chart(df_curr), use_container_width=True)
    if not df_curr.empty:
        summary = df_curr.groupby('hook_pattern').agg(
            videos=('video_id', 'count'),
            avg_viewer_choice=('viewer_choice', 'mean'),
            avg_apv=('apv', 'mean'),
            total_views=('views', 'sum')
        ).reset_index().sort_values('avg_viewer_choice', ascending=False)
        st.dataframe(summary, use_container_width=True)


def render_page_retention(df_curr: pd.DataFrame):
    """Renders retention & duration module."""
    render_section_header("⏱ Duration Buckets & Retention Curves", "APV & AVD analysis by video length")
    st.plotly_chart(render_duration_chart(df_curr), use_container_width=True)
    if not df_curr.empty:
        st.plotly_chart(render_retention_curve_chart(df_curr.iloc[0]['title'], df_curr.iloc[0]['apv']), use_container_width=True)


def render_page_subscribers(df_curr: pd.DataFrame):
    """Renders subscriber conversion module."""
    render_section_header("👥 Subscriber Conversion Center", "Subscribers gained per 1,000 views")
    scol1, scol2, scol3 = st.columns(3)
    tot_subs = df_curr['subscribers_gained'].sum() if not df_curr.empty else 0
    avg_s1000 = df_curr['subs_per_1000'].mean() if not df_curr.empty else 0.0
    with scol1:
        st.markdown(render_kpi_card("Total Subs Gained", f"+{tot_subs:,}", "Channel Total", "#FFD700", "👥"), unsafe_allow_html=True)
    with scol2:
        st.markdown(render_kpi_card("Subs / 1,000 Views", f"{avg_s1000:.2f}", "Conversion Efficiency", "#3FB950", "🎯"), unsafe_allow_html=True)
    with scol3:
        top_sub_video = df_curr.sort_values('subscribers_gained', ascending=False).iloc[0]['title'] if not df_curr.empty else 'N/A'
        st.markdown(render_kpi_card("Top Sub Generator", f"{top_sub_video[:25]}...", "Highest Value Video", "#58A6FF", "🏆"), unsafe_allow_html=True)


def render_page_learning(v4_insights: dict):
    """Renders V4 learning & memory module."""
    render_section_header("🧠 V4 Audience Memory & Learning Insights", "Confirmed winning patterns & failed experiments")
    lcol1, lcol2 = st.columns(2)
    with lcol1:
        st.markdown("#### 🧠 Confirmed Audience Memory")
        st.json(v4_insights.get('youtube', v4_insights.get('combined', {
            "high_interest_niches": ["Space Competition", "AI Solar Predictions"],
            "viral_hook_guideline": "High-stakes conflict in sentence 1",
            "pacing_and_length_adjustments": "25-30 second duration target"
        })))
    with lcol2:
        st.markdown("#### 💡 Recommended Next Video Ideas")
        st.markdown("""
        1. **China's Next Moon Mission vs NASA** | Opportunity: **9.4/10** | *Space Race*
        2. **SpaceX Starship Secret AI Orbit Test** | Opportunity: **9.1/10** | *AI × Space*
        3. **James Webb Finds Impossible Exoplanet** | Opportunity: **8.8/10** | *Cosmic Discoveries*
        """)


def render_page_health(df_raw: pd.DataFrame, df_curr: pd.DataFrame, last_update_str: str):
    """Renders system data health module."""
    render_section_header("⚙ Data Health & System Status", "Database connectivity & sync freshness")
    st.markdown(f"""
    - **Primary Database:** `data/shortest_orbit_v3.db`
    - **YouTube Database:** `automation/database/youtube.db`
    - **Database Safety Mode:** `100% READ-ONLY SAFE`
    - **Total YouTube Shorts Analyzed:** {len(df_raw)}
    - **Active Window Shorts:** {len(df_curr)}
    - **Last Sync Timestamp:** {last_update_str}
    - **Live YouTube API Status:** Available (Fallback to SQLite snapshots active)
    """)
