"""
dashboard_charts.py - Dark Cinematic Space/Technology Visualization Layer.

Uses Plotly Express & Plotly Graph Objects with primary Crimson Red (#C1121F),
Gold (#FFD700), and dark theme palette.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

DARK_BG = "#0E1117"
CARD_BG = "#161B22"
CRIMSON_RED = "#C1121F"
ACCENT_GOLD = "#FFD700"
TEXT_WHITE = "#F0F6FC"
TEXT_MUTED = "#8B949E"


def apply_cinematic_theme(fig: go.Figure, title: str = ""):
    """Applies clean dark cinematic styling to any Plotly chart."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT_WHITE, family="Arial, sans-serif")),
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_WHITE),
        xaxis=dict(
            gridcolor="#21262D",
            zerolinecolor="#30363D",
            tickfont=dict(color=TEXT_MUTED)
        ),
        yaxis=dict(
            gridcolor="#21262D",
            zerolinecolor="#30363D",
            tickfont=dict(color=TEXT_MUTED)
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(font=dict(color=TEXT_WHITE), bgcolor="rgba(0,0,0,0)")
    )
    return fig


def render_growth_trend_chart(curr_df: pd.DataFrame, prev_df: pd.DataFrame = None, metric: str = "views") -> go.Figure:
    """Line chart showing views/subscribers over time with period comparison overlay."""
    fig = go.Figure()

    if not curr_df.empty and 'uploaded_at' in curr_df.columns:
        df_sorted = curr_df.sort_values('uploaded_at')
        fig.add_trace(go.Scatter(
            x=df_sorted['uploaded_at'],
            y=df_sorted[metric],
            mode='lines+markers',
            name='Current Period',
            line=dict(color=CRIMSON_RED, width=3),
            marker=dict(size=6, color=ACCENT_GOLD)
        ))

    if prev_df is not None and not prev_df.empty and 'uploaded_at' in prev_df.columns:
        prev_sorted = prev_df.sort_values('uploaded_at')
        fig.add_trace(go.Scatter(
            x=prev_sorted['uploaded_at'],
            y=prev_sorted[metric],
            mode='lines',
            name='Previous Period',
            line=dict(color=TEXT_MUTED, width=2, dash='dot')
        ))

    return apply_cinematic_theme(fig, f"YouTube Channel Growth Trend — {metric.replace('_', ' ').title()}")


def render_performance_matrix(df: pd.DataFrame) -> go.Figure:
    """
    Video Performance Matrix (Scatter Plot):
    X-axis: Viewer Choice / Stayed to Watch (%)
    Y-axis: Average Percentage Viewed - APV (%)
    Bubble Size: Views
    Color: Content Pillar
    """
    if df.empty:
        return apply_cinematic_theme(go.Figure(), "Performance Matrix")

    fig = px.scatter(
        df,
        x='viewer_choice',
        y='apv',
        size='views',
        color='content_pillar',
        hover_name='title',
        hover_data=['views', 'subscribers_gained', 'subs_per_1000'],
        color_discrete_sequence=[CRIMSON_RED, ACCENT_GOLD, '#58A6FF', '#3FB950'],
        size_max=35
    )

    # Quadrant dividing lines (70% Viewer choice, 65% APV)
    fig.add_vline(x=70, line_dash="dash", line_color="#30363D")
    fig.add_hline(y=65, line_dash="dash", line_color="#30363D")

    # Add quadrant annotations
    fig.add_annotation(x=82, y=85, text="🏆 WINNERS<br>(High Choice + High Retention)", showarrow=False, font=dict(color="#3FB950", size=11))
    fig.add_annotation(x=82, y=50, text="⚠️ STORY PROBLEM<br>(High Choice + Low Retention)", showarrow=False, font=dict(color=ACCENT_GOLD, size=11))
    fig.add_annotation(x=55, y=85, text="🪝 HOOK PROBLEM<br>(Low Choice + High Retention)", showarrow=False, font=dict(color="#58A6FF", size=11))
    fig.add_annotation(x=55, y=50, text="❌ TOPIC PROBLEM<br>(Low Choice + Low Retention)", showarrow=False, font=dict(color=CRIMSON_RED, size=11))

    fig.update_xaxes(title="Viewer Choice / Stayed to Watch (%)")
    fig.update_yaxes(title="Average Percentage Viewed - APV (%)")

    return apply_cinematic_theme(fig, "Video Performance Matrix (Viewer Choice vs Retention)")


def render_pillar_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart comparing Content Pillars by Total Views & Median APV."""
    if df.empty or 'content_pillar' not in df.columns:
        return apply_cinematic_theme(go.Figure(), "Content Pillar Analysis")

    grouped = df.groupby('content_pillar').agg(
        total_views=('views', 'sum'),
        avg_apv=('apv', 'mean'),
        subs_gained=('subscribers_gained', 'sum'),
        video_count=('video_id', 'count')
    ).reset_index()

    fig = px.bar(
        grouped,
        x='content_pillar',
        y='total_views',
        color='avg_apv',
        hover_data=['video_count', 'subs_gained'],
        color_continuous_scale=['#30363D', CRIMSON_RED, ACCENT_GOLD],
        labels={'total_views': 'Total Views', 'avg_apv': 'Average APV (%)', 'content_pillar': 'Content Pillar'}
    )

    return apply_cinematic_theme(fig, "Content Pillar Performance (Total Views & APV)")


def render_topic_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart showing Views by Topic Keyword."""
    if df.empty or 'topic_title' not in df.columns:
        return apply_cinematic_theme(go.Figure(), "Topic Performance")

    df_topics = df.copy()
    df_topics['topic_clean'] = df_topics['topic_title'].fillna('General Space/AI').apply(lambda x: str(x)[:30])
    grouped = df_topics.groupby('topic_clean').agg(
        views=('views', 'sum'),
        median_apv=('apv', 'median'),
        subs=('subscribers_gained', 'sum'),
        count=('video_id', 'count')
    ).reset_index().sort_values('views', ascending=True).tail(10)

    fig = px.bar(
        grouped,
        y='topic_clean',
        x='views',
        orientation='h',
        color='median_apv',
        color_continuous_scale=[CRIMSON_RED, ACCENT_GOLD],
        labels={'views': 'Total Views', 'topic_clean': 'Topic', 'median_apv': 'Median APV (%)'}
    )

    return apply_cinematic_theme(fig, "Top 10 Performing Topics")


def render_hook_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart showing Viewer Choice by Hook Pattern."""
    if df.empty or 'hook_pattern' not in df.columns:
        return apply_cinematic_theme(go.Figure(), "Hook Analysis")

    grouped = df.groupby('hook_pattern').agg(
        avg_viewer_choice=('viewer_choice', 'mean'),
        avg_apv=('apv', 'mean'),
        total_views=('views', 'sum'),
        video_count=('video_id', 'count')
    ).reset_index().sort_values('avg_viewer_choice', ascending=False)

    fig = px.bar(
        grouped,
        x='hook_pattern',
        y='avg_viewer_choice',
        color='avg_apv',
        color_continuous_scale=[CRIMSON_RED, ACCENT_GOLD],
        labels={'avg_viewer_choice': 'Avg Viewer Choice (%)', 'hook_pattern': 'Hook Pattern'}
    )

    return apply_cinematic_theme(fig, "Hook Pattern Performance (Viewer Choice & APV)")


def render_duration_chart(df: pd.DataFrame) -> go.Figure:
    """Duration Bucket Performance bar chart."""
    if df.empty or 'duration_sec' not in df.columns:
        return apply_cinematic_theme(go.Figure(), "Duration Buckets")

    bins = [0, 20, 25, 30, 35, 40, 60]
    labels = ['10–20 sec', '21–25 sec', '26–30 sec', '31–35 sec', '36–40 sec', '41–60 sec']
    df_dur = df.copy()
    df_dur['duration_bucket'] = pd.cut(df_dur['duration_sec'], bins=bins, labels=labels, right=True)

    grouped = df_dur.groupby('duration_bucket', observed=False).agg(
        median_views=('views', 'median'),
        avg_apv=('apv', 'mean'),
        video_count=('video_id', 'count')
    ).reset_index()

    fig = px.bar(
        grouped,
        x='duration_bucket',
        y='median_views',
        color='avg_apv',
        color_continuous_scale=[CRIMSON_RED, ACCENT_GOLD],
        labels={'median_views': 'Median Views', 'duration_bucket': 'Duration Bucket', 'avg_apv': 'Average APV (%)'}
    )

    return apply_cinematic_theme(fig, "Performance by Video Duration Bucket")


def render_retention_curve_chart(video_title: str, apv: float) -> go.Figure:
    """Generates realistic retention curve line chart for video detail page."""
    time_pts = np.linspace(0, 100, 50)
    # Model retention curve dropoff based on APV
    start_drop = 100.0
    mid_val = max(30.0, apv * 0.9)
    end_val = max(15.0, apv * 0.7)
    
    retention_curve = start_drop * np.exp(-time_pts / 40.0) + (apv * 0.5)
    retention_curve = np.clip(retention_curve, 10.0, 100.0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_pts,
        y=retention_curve,
        mode='lines',
        name='Audience Retention %',
        line=dict(color=CRIMSON_RED, width=3),
        fill='tozeroy',
        fillcolor='rgba(193, 18, 31, 0.15)'
    ))

    fig.add_hline(y=apv, line_dash="dash", line_color=ACCENT_GOLD, annotation_text=f"Average APV ({apv:.1f}%)")

    fig.update_xaxes(title="Video Duration Elapsed (%)")
    fig.update_yaxes(title="Audience Remaining (%)", range=[0, 105])

    return apply_cinematic_theme(fig, f"Audience Retention Curve — {video_title[:35]}...")
