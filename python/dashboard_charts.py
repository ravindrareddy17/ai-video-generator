"""
dashboard_charts.py — Minimal Plotly Visualizations for V2 Command Center.

Enforces clean dark space styling (#0B0F14 bg, #11161D panel bg, #C1121F accent),
no decorative clutter, responsive layouts, and single-chart displays.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def apply_clean_theme(fig, title: str = ""):
    """Applies V2 minimal dark space theme styling."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#F5F7FA", family="sans-serif")),
        paper_bgcolor="#11161D",
        plot_bgcolor="#11161D",
        font=dict(color="#F5F7FA", family="sans-serif"),
        xaxis=dict(
            gridcolor="#171D25",
            tickfont=dict(color="#9AA4B2"),
            zeroline=False
        ),
        yaxis=dict(
            gridcolor="#171D25",
            tickfont=dict(color="#9AA4B2"),
            zeroline=False
        ),
        margin=dict(l=24, r=24, t=36, b=24),
        hovermode="x unified"
    )
    return fig


def render_performance_trend_chart(df_curr: pd.DataFrame, df_prev: pd.DataFrame, metric: str = "views"):
    """Renders one large clean line chart for performance trends over time."""
    if df_curr.empty:
        fig = go.Figure()
        fig.add_annotation(text="No video data available for selected date range", showarrow=False, font=dict(color="#9AA4B2", size=14))
        return apply_clean_theme(fig, "Performance Trend")

    df_sorted = df_curr.sort_values('uploaded_at')

    labels_map = {
        "views": "Views Over Time",
        "subscribers_gained": "Subscribers Gained Over Time",
        "watch_hours": "Watch Time (Hours) Over Time"
    }
    title = labels_map.get(metric, "Views Over Time")

    fig = go.Figure()

    # Current period line
    fig.add_trace(go.Scatter(
        x=df_sorted['uploaded_at'],
        y=df_sorted[metric],
        mode='lines+markers',
        name='Current Period',
        line=dict(color='#C1121F', width=3),
        marker=dict(size=6, color='#C1121F')
    ))

    # Previous period comparison line if available
    if not df_prev.empty and metric in df_prev.columns:
        df_prev_sorted = df_prev.sort_values('uploaded_at')
        fig.add_trace(go.Scatter(
            x=df_sorted['uploaded_at'],
            y=df_prev_sorted[metric].head(len(df_sorted)),
            mode='lines',
            name='Previous Period',
            line=dict(color='#9AA4B2', width=1.5, dash='dash')
        ))

    return apply_clean_theme(fig, title)


def render_topic_confidence_chart(df: pd.DataFrame):
    """Renders Topic Intelligence chart for V4 Intelligence page."""
    if df.empty:
        fig = go.Figure()
        return apply_clean_theme(fig, "Topic Performance")

    summary = df.groupby('content_pillar').agg(
        median_views=('views', 'median'),
        avg_apv=('apv', 'mean'),
        video_count=('video_id', 'count')
    ).reset_index()

    fig = px.bar(
        summary,
        x='content_pillar',
        y='median_views',
        text='video_count',
        color_discrete_sequence=['#C1121F'],
        labels={'content_pillar': 'Content Pillar', 'median_views': 'Median Views', 'video_count': 'Videos'}
    )
    fig.update_traces(texttemplate='%{text} videos', textposition='outside')
    return apply_clean_theme(fig, "Median Views by Content Pillar")


def render_hook_pattern_chart(df: pd.DataFrame):
    """Renders Hook Intelligence chart for V4 Intelligence page."""
    if df.empty:
        fig = go.Figure()
        return apply_clean_theme(fig, "Hook Pattern Performance")

    summary = df.groupby('hook_pattern').agg(
        avg_viewer_choice=('viewer_choice', 'mean'),
        video_count=('video_id', 'count')
    ).reset_index().sort_values('avg_viewer_choice', ascending=False)

    fig = px.bar(
        summary,
        x='hook_pattern',
        y='avg_viewer_choice',
        color_discrete_sequence=['#2EA043'],
        labels={'hook_pattern': 'Hook Pattern', 'avg_viewer_choice': 'Avg Viewer Choice Rate (%)'}
    )
    return apply_clean_theme(fig, "Viewer Choice Rate by Hook Pattern")
