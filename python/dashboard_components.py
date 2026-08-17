"""
dashboard_components.py — Ultra-Simple Clean UI Component Library.

Provides high contrast text (#111827), clean light backgrounds (#FFFFFF, #F8F9FA),
left-aligned typography, and simple rounded cards (#E5E7EB border).
"""

import streamlit as st


def render_top_banner(data_source: str = "STORED YOUTUBE DATA", last_update_str: str = ""):
    """Simple, clean top banner."""
    st.markdown(f"""
    <div style="background-color: #4F46E5; color: #FFFFFF; padding: 12px 24px; margin: -6rem -6rem 20px -6rem; display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 14px; font-weight: 700; text-align: left;">
            🚀 THE SHORTEST ORBIT &nbsp; | &nbsp; <span style="font-weight: 400; opacity: 0.9;">YouTube Analytics Dashboard</span>
        </div>
        <div style="font-size: 12px; font-weight: 600; text-align: right;">
            Status: <span style="background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 4px;">{data_source}</span>
            &nbsp; Synced: {last_update_str}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hero_section():
    """Clean hero section with left-aligned typography."""
    st.markdown("""
    <div style="margin: 24px 0 32px 0; text-align: left;">
        <h1 style="font-size: 42px; font-weight: 800; color: #111827; margin: 0; letter-spacing: -0.02em;">
            THE SHORTEST ORBIT
        </h1>
        <div style="font-size: 16px; font-weight: 600; color: #4F46E5; text-transform: uppercase; margin-top: 4px; letter-spacing: 0.05em;">
            YouTube Growth Command Center
        </div>
        <p style="font-size: 16px; color: #4B5563; margin-top: 8px; line-height: 1.5;">
            Track video performance, analyze audience retention, and discover your channel's next winning topics.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_channel_status_panel(status: str, narrative: str):
    """Clean status panel with simple background and high-contrast text."""
    status_color = "#4F46E5" if status in ["GROWING", "STABLE"] else ("#DC2626" if status == "DECLINING" else "#6B7280")

    st.markdown(f"""
    <div style="background-color: #F8F9FA; border: 1px solid #E5E7EB; border-left: 5px solid {status_color}; border-radius: 12px; padding: 24px 28px; margin-bottom: 32px; text-align: left;">
        <div style="font-size: 12px; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em;">CHANNEL GROWTH STATUS</div>
        <div style="font-size: 32px; font-weight: 800; color: {status_color}; margin: 4px 0 8px 0;">{status}</div>
        <div style="font-size: 15px; color: #111827; line-height: 1.6; font-weight: 500;">
            {narrative}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_simple_kpi_card(title: str, value: str, change_str: str, prev_val: str, tooltip: str = ""):
    """Clean white KPI card with left-aligned text and high contrast numbers."""
    is_pos = "+" in change_str or change_str.startswith("+")
    is_neg = "-" in change_str and not change_str.startswith("0")
    change_color = "#16A34A" if is_pos else ("#DC2626" if is_neg else "#6B7280")

    return f"""
    <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; text-align: left; height: 100%;" title="{tooltip}">
        <div style="font-size: 12px; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em;">{title}</div>
        <div style="font-size: 30px; font-weight: 800; color: #111827; margin: 6px 0;">{value}</div>
        <div style="font-size: 13px; font-weight: 700; color: {change_color};">{change_str}</div>
        <div style="font-size: 12px; color: #9CA3AF; margin-top: 4px;">Previous: {prev_val}</div>
    </div>
    """


def render_bottleneck_section(bottleneck_info: dict):
    """Clean bottleneck card with left alignment."""
    st.markdown(f"""
    <div style="background-color: #F8F9FA; border: 1px solid #E5E7EB; border-radius: 12px; padding: 28px; margin: 32px 0; text-align: left;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="font-size: 12px; font-weight: 700; color: #4F46E5; text-transform: uppercase;">GROWTH BOTTLENECK</div>
            <span style="font-size: 11px; font-weight: 700; color: #4F46E5; background: #EEF2FF; padding: 3px 10px; border-radius: 4px;">V4 DIAGNOSTIC</span>
        </div>
        <div style="font-size: 26px; font-weight: 800; color: #111827; margin: 4px 0 10px 0;">{bottleneck_info['bottleneck']}</div>
        <div style="font-size: 15px; color: #4B5563; margin-bottom: 14px; line-height: 1.5;">
            <b>Why:</b> "{bottleneck_info['why']}"
        </div>
        <div style="font-size: 14px; color: #111827; background: #FFFFFF; border: 1px solid #E5E7EB; padding: 14px 18px; border-radius: 8px;">
            <b style="color:#4F46E5;">Recommended Action:</b> {bottleneck_info['recommendation']}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_v4_learned_section(insight_text: str, confidence: str, evidence_count: int):
    """Simple V4 learned banner."""
    st.markdown(f"""
    <div style="background-color: #F8F9FA; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px 28px; margin: 32px 0; text-align: left;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="font-size: 12px; font-weight: 700; color: #4F46E5; text-transform: uppercase;">V4 INTELLIGENCE INSIGHT</div>
            <span style="font-size: 11px; font-weight: 700; color: #16A34A; background: #DCFCE7; padding: 3px 10px; border-radius: 4px;">CONFIDENCE: {confidence}</span>
        </div>
        <div style="font-size: 17px; font-weight: 700; color: #111827; margin: 8px 0; line-height: 1.5;">
            "{insight_text}"
        </div>
        <div style="font-size: 13px; color: #6B7280;">
            Evidence: <b>{evidence_count} videos</b> analyzed in database.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_section_title(title: str, subtitle: str = ""):
    """Clean section title left-aligned."""
    st.markdown(f"""
    <div style="margin: 40px 0 18px 0; text-align: left;">
        <h2 style="font-size: 24px; font-weight: 800; color: #111827; margin: 0; letter-spacing: -0.02em;">{title}</h2>
        {f'<div style="font-size: 14px; color: #4B5563; margin-top: 4px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def get_performance_badge_html(pclass: str) -> str:
    """Simple rounded pill badge."""
    if pclass == "WINNER":
        return '<span style="background-color: #DCFCE7; color: #16A34A; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 700;">WINNER</span>'
    elif pclass == "ABOVE AVERAGE":
        return '<span style="background-color: #EEF2FF; color: #4F46E5; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 700;">ABOVE AVERAGE</span>'
    elif pclass == "NORMAL":
        return '<span style="background-color: #F3F4F6; color: #4B5563; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 700;">NORMAL</span>'
    else:
        return '<span style="background-color: #FEE2E2; color: #DC2626; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 700;">UNDERPERFORMER</span>'
