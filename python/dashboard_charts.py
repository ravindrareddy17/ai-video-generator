"""
dashboard_charts.py — Editorial Plotly Visualizations for White/Purple SaaS Dashboard V2.

Features:
- Pure white background (#FFFFFF)
- Primary Brand Purple line (#5B21F5)
- Subtle gray grid (#EEEEEE)
- Dark black text (#0A0A0A)
- Generous padding and minimal editorial styling
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def apply_editorial_theme(fig, title: str = ""):
    """Applies pure white / purple editorial SaaS Plotly theme."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color="#0A0A0A", family="Inter, Helvetica, Arial, sans-serif")),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#0A0A0A", family="Inter, Helvetica, Arial, sans-serif"),
        xaxis=dict(
            gridcolor="#EEEEEE",
            tickfont=dict(color="#555555"),
            zeroline=False,
            showline=True,
            linecolor="#E8E8E8"
        ),
        yaxis=dict(
            gridcolor="#EEEEEE",
            tickfont=dict(color="#555555"),
            zeroline=False,
            showline=True,
            linecolor="#E8E8E8"
        ),
        margin=dict(l=30, r=30, t=40, b=30),
        hovermode="x unified"
    )
    return fig


def render_performance_trend_chart(df_curr: pd.DataFrame, df_prev: pd.DataFrame, metric: str = "views"):
    """Renders one large clean line chart for performance trends over time using #5B21F5 purple."""
    if df_curr.empty:
        fig = go.Figure()
        fig.add_annotation(text="No video data available for selected date range", showarrow=False, font=dict(color="#555555", size=14))
        return apply_editorial_theme(fig, "Channel Growth Trend")

    df_sorted = df_curr.sort_values('uploaded_at')

    labels_map = {
        "views": "Views Over Time",
        "subscribers_gained": "Subscribers Gained Over Time",
        "watch_hours": "Watch Time (Hours) Over Time"
    }
    title = labels_map.get(metric, "Views Over Time")

    fig = go.Figure()

    # Current period purple line (#5B21F5)
    fig.add_trace(go.Scatter(
        x=df_sorted['uploaded_at'],
        y=df_sorted[metric],
        mode='lines+markers',
        name='Current Period',
        line=dict(color='#5B21F5', width=3.5),
        marker=dict(size=7, color='#5B21F5')
    ))

    # Previous period comparison line
    if not df_prev.empty and metric in df_prev.columns:
        df_prev_sorted = df_prev.sort_values('uploaded_at')
        fig.add_trace(go.Scatter(
            x=df_sorted['uploaded_at'],
            y=df_prev_sorted[metric].head(len(df_sorted)),
            mode='lines',
            name='Previous Period',
            line=dict(color='#888888', width=1.5, dash='dash')
        ))

    return apply_editorial_theme(fig, title)


def render_topic_confidence_chart(df: pd.DataFrame):
    """Renders Topic Intelligence bar chart in primary brand purple."""
    if df.empty:
        fig = go.Figure()
        return apply_editorial_theme(fig, "Topic Performance")

    summary = df.groupby('content_pillar').agg(
        median_views=('views', 'median'),
        video_count=('video_id', 'count')
    ).reset_index()

    fig = px.bar(
        summary,
        x='content_pillar',
        y='median_views',
        text='video_count',
        color_discrete_sequence=['#5B21F5'],
        labels={'content_pillar': 'Content Pillar', 'median_views': 'Median Views', 'video_count': 'Videos'}
    )
    fig.update_traces(texttemplate='%{text} videos', textposition='outside')
    return apply_editorial_theme(fig, "Median Views by Content Pillar")


def render_hook_pattern_chart(df: pd.DataFrame):
    """Renders Hook Intelligence bar chart."""
    if df.empty:
        fig = go.Figure()
        return apply_editorial_theme(fig, "Hook Pattern Performance")

    summary = df.groupby('hook_pattern').agg(
        avg_viewer_choice=('viewer_choice', 'mean')
    ).reset_index().sort_values('avg_viewer_choice', ascending=False)

    fig = px.bar(
        summary,
        x='hook_pattern',
        y='avg_viewer_choice',
        color_discrete_sequence=['#7C3AED'],
        labels={'hook_pattern': 'Hook Pattern', 'avg_viewer_choice': 'Avg Viewer Choice (%)'}
    )
    return apply_editorial_theme(fig, "Viewer Choice Rate by Hook Pattern")
