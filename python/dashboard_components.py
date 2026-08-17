"""
dashboard_components.py — White/Purple Editorial SaaS UI Components for V2 Command Center.

Reproduces the premium visual design language:
- Pure white background (#FFFFFF)
- Bold black typography (#0A0A0A)
- Brand Purple accent (#5B21F5)
- Secondary Purple (#7C3AED) & Light Purple (#F1EDFF)
- Large editorial headings & generous whitespace
- Rounded cards (16px) & subtle borders (#E8E8E8)
"""

import streamlit as st


def render_purple_top_announcement_bar(data_source: str = "STORED YOUTUBE DATA", last_update_str: str = ""):
    """Thin purple announcement bar (#5B21F5) at the very top."""
    st.markdown(f"""
    <div style="background-color: #5B21F5; color: #FFFFFF; padding: 14px 28px; margin: -6rem -6rem 24px -6rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(91, 33, 245, 0.2);">
        <div style="font-size: 14px; font-weight: 700; letter-spacing: 0.5px;">
            THE SHORTEST ORBIT &nbsp; | &nbsp; <span style="font-weight: 400; opacity: 0.9;">YouTube Growth Command Center</span>
        </div>
        <div style="font-size: 13px; font-weight: 600;">
            YouTube Data: <span style="background: rgba(255,255,255,0.2); padding: 3px 10px; border-radius: 999px; font-size: 11px;">● {data_source}</span>
            &nbsp; <span style="opacity: 0.8;">Synced: {last_update_str}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hero_section():
    """Large editorial hero section with generous vertical whitespace."""
    st.markdown("""
    <div style="margin: 40px 0 48px 0; text-align: left;">
        <h1 style="font-size: 58px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.04em; margin: 0; line-height: 1.05;">
            THE SHORTEST ORBIT
        </h1>
        <h2 style="font-size: 26px; font-weight: 700; color: #5B21F5; margin: 6px 0 16px 0; text-transform: uppercase; letter-spacing: 0.05em;">
            YOUTUBE GROWTH COMMAND CENTER
        </h2>
        <p style="font-size: 19px; color: #555555; line-height: 1.6; max-width: 780px; margin: 0;">
            Understand what is working, what is failing, and what your channel should create next.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_channel_status_panel(status: str, narrative: str):
    """Large rounded Channel Status panel on light purple background (#F1EDFF)."""
    status_color = "#5B21F5" if status in ["GROWING", "STABLE"] else ("#DC2626" if status == "DECLINING" else "#888888")

    st.markdown(f"""
    <div style="background-color: #F1EDFF; border: 1px solid #E8E8E8; border-radius: 20px; padding: 32px 36px; margin-bottom: 48px;">
        <div style="font-size: 12px; font-weight: 700; color: #5B21F5; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">CHANNEL STATUS</div>
        <div style="font-size: 44px; font-weight: 800; color: {status_color}; letter-spacing: -0.03em; margin: 4px 0 12px 0;">{status}</div>
        <div style="font-size: 18px; color: #0A0A0A; line-height: 1.6; max-width: 900px; font-weight: 500;">
            {narrative}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_editorial_kpi_card(title: str, value: str, change_str: str, prev_val: str, tooltip: str = ""):
    """Clean white editorial KPI card (#FFFFFF, 16px radius, 1px solid #E8E8E8)."""
    is_pos = "+" in change_str or change_str.startswith("+")
    is_neg = "-" in change_str and not change_str.startswith("0")
    change_color = "#16A34A" if is_pos else ("#DC2626" if is_neg else "#888888")

    return f"""
    <div style="background-color: #FFFFFF; border: 1px solid #E8E8E8; border-radius: 16px; padding: 28px 24px; height: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.02);" title="{tooltip}">
        <div style="font-size: 12px; font-weight: 700; color: #888888; text-transform: uppercase; letter-spacing: 0.08em;">{title}</div>
        <div style="font-size: 38px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em; margin: 8px 0 6px 0;">{value}</div>
        <div style="font-size: 14px; font-weight: 700; color: {change_color};">{change_str}</div>
        <div style="font-size: 12px; color: #888888; margin-top: 6px;">Previous: {prev_val}</div>
    </div>
    """


def render_bottleneck_section(bottleneck_info: dict):
    """Full-width rounded #F1EDFF current bottleneck section."""
    st.markdown(f"""
    <div style="background-color: #F1EDFF; border: 1px solid #E8E8E8; border-radius: 20px; padding: 36px 40px; margin: 48px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-size: 12px; font-weight: 800; color: #5B21F5; text-transform: uppercase; letter-spacing: 0.08em;">CURRENT BOTTLENECK</div>
            <span style="font-size: 11px; font-weight: 700; color: #5B21F5; background: #FFFFFF; padding: 4px 12px; border-radius: 999px; border: 1px solid #E8E8E8;">V4 DIAGNOSTIC</span>
        </div>
        <div style="font-size: 36px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em; margin: 6px 0 12px 0;">{bottleneck_info['bottleneck']}</div>
        <div style="font-size: 17px; color: #555555; margin-bottom: 16px; line-height: 1.6;">
            <b>WHY?</b> "{bottleneck_info['why']}"
        </div>
        <div style="font-size: 16px; color: #0A0A0A; background: #FFFFFF; border: 1px solid #E8E8E8; padding: 16px 20px; border-radius: 12px; font-weight: 600;">
            <span style="color:#5B21F5; font-weight:800;">WHAT TO DO NEXT →</span> {bottleneck_info['recommendation']}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_v4_learned_section(insight_text: str, confidence: str, evidence_count: int):
    """V4 Intelligence brief summary panel with light purple background (#F1EDFF)."""
    st.markdown(f"""
    <div style="background-color: #F1EDFF; border: 1px solid #E8E8E8; border-radius: 20px; padding: 32px 36px; margin: 48px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-size: 12px; font-weight: 800; color: #5B21F5; text-transform: uppercase; letter-spacing: 0.08em;">V4 LEARNED</div>
            <span style="font-size: 11px; font-weight: 700; color: #16A34A; background: #DCFCE7; padding: 4px 12px; border-radius: 999px;">CONFIDENCE: {confidence}</span>
        </div>
        <div style="font-size: 20px; font-weight: 700; color: #0A0A0A; margin: 10px 0; line-height: 1.5;">
            "{insight_text}"
        </div>
        <div style="font-size: 14px; color: #555555; margin-top: 6px;">
            Evidence: <b>{evidence_count} videos</b> analyzed.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_section_title(title: str, subtitle: str = ""):
    """Large modern editorial section title (32-42px)."""
    st.markdown(f"""
    <div style="margin: 56px 0 24px 0; text-align: left;">
        <h2 style="font-size: 34px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.03em; margin: 0;">{title}</h2>
        {f'<div style="font-size: 16px; color: #555555; margin-top: 4px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def get_performance_badge_html(pclass: str) -> str:
    """Returns rounded pill badge for video classifications."""
    if pclass == "WINNER":
        return '<span style="background-color: #DCFCE7; color: #16A34A; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;">WINNER</span>'
    elif pclass == "ABOVE AVERAGE":
        return '<span style="background-color: #F1EDFF; color: #5B21F5; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;">ABOVE AVERAGE</span>'
    elif pclass == "NORMAL":
        return '<span style="background-color: #F3F4F6; color: #555555; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;">NORMAL</span>'
    else:
        return '<span style="background-color: #FEE2E2; color: #DC2626; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;">UNDERPERFORMER</span>'
