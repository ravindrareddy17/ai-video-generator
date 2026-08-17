"""
dashboard_charts.py — Clean Plotly Visualizations.

Features:
- Pure white background (#FFFFFF)
- High contrast black font (#111827)
- Royal Indigo/Purple primary line (#4F46E5)
- Subtle gray grid (#E5E7EB)
- Left-aligned clean titles
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def apply_clean_theme(fig, title: str = ""):
    """Applies clean white / indigo Plotly theme."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#111827", family="sans-serif"), x=0.01),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#111827", family="sans-serif"),
        xaxis=dict(
            gridcolor="#E5E7EB",
            tickfont=dict(color="#4B5563"),
            zeroline=False,
            showline=True,
            linecolor="#E5E7EB"
        ),
        yaxis=dict(
            gridcolor="#E5E7EB",
            tickfont=dict(color="#4B5563"),
            zeroline=False,
            showline=True,
            linecolor="#E5E7EB"
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    return fig


def render_performance_trend_chart(df_curr: pd.DataFrame, df_prev: pd.DataFrame, metric: str = "views"):
    """Renders one clean line chart for performance trends over time using #4F46E5."""
    if df_curr.empty:
        fig = go.Figure()
        fig.add_annotation(text="No video data available for selected date range", showarrow=False, font=dict(color="#4B5563", size=14))
        return apply_clean_theme(fig, "Performance Trend")

    df_sorted = df_curr.sort_values('uploaded_at')

    labels_map = {
        "views": "Views Over Time",
        "subscribers_gained": "Subscribers Gained Over Time",
        "watch_hours": "Watch Time (Hours) Over Time"
    }
    title = labels_map.get(metric, "Views Over Time")

    fig = go.Figure()

    # Current period line (#4F46E5)
    fig.add_trace(go.Scatter(
        x=df_sorted['uploaded_at'],
        y=df_sorted[metric],
        mode='lines+markers',
        name='Current Period',
        line=dict(color='#4F46E5', width=3),
        marker=dict(size=6, color='#4F46E5')
    ))

    # Previous period comparison line
    if not df_prev.empty and metric in df_prev.columns:
        df_prev_sorted = df_prev.sort_values('uploaded_at')
        fig.add_trace(go.Scatter(
            x=df_sorted['uploaded_at'],
            y=df_prev_sorted[metric].head(len(df_sorted)),
            mode='lines',
            name='Previous Period',
            line=dict(color='#9CA3AF', width=1.5, dash='dash')
        ))

    return apply_clean_theme(fig, title)


def render_topic_confidence_chart(df: pd.DataFrame):
    """Renders Topic Intelligence bar chart."""
    if df.empty:
        fig = go.Figure()
        return apply_clean_theme(fig, "Topic Performance")

    summary = df.groupby('content_pillar').agg(
        median_views=('views', 'median'),
        video_count=('video_id', 'count')
    ).reset_index()

    fig = px.bar(
        summary,
        x='content_pillar',
        y='median_views',
        text='video_count',
        color_discrete_sequence=['#4F46E5'],
        labels={'content_pillar': 'Content Pillar', 'median_views': 'Median Views', 'video_count': 'Videos'}
    )
    fig.update_traces(texttemplate='%{text} videos', textposition='outside')
    return apply_clean_theme(fig, "Median Views by Content Pillar")


def render_hook_pattern_chart(df: pd.DataFrame):
    """Renders Hook Intelligence bar chart."""
    if df.empty:
        fig = go.Figure()
        return apply_clean_theme(fig, "Hook Pattern Performance")

    summary = df.groupby('hook_pattern').agg(
        avg_viewer_choice=('viewer_choice', 'mean')
    ).reset_index().sort_values('avg_viewer_choice', ascending=False)

    fig = px.bar(
        summary,
        x='hook_pattern',
        y='avg_viewer_choice',
        color_discrete_sequence=['#6366F1'],
        labels={'hook_pattern': 'Hook Pattern', 'avg_viewer_choice': 'Avg Viewer Choice (%)'}
    )
    return apply_clean_theme(fig, "Viewer Choice Rate by Hook Pattern")
