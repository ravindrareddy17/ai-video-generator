"""
dashboard_components.py — UI Component Library for V2 Command Center.

Enforces strict separation between TYPE 1 (Real YouTube Performance) and TYPE 2 (Internal V4 Intelligence).
Clean styling: #0B0F14 bg, #11161D panel, #171D25 secondary panel, #C1121F accent.
"""

import streamlit as st
import pandas as pd


def render_top_header(data_source: str = "STORED YOUTUBE DATA", last_update_str: str = ""):
    """Extremely simple top header with title and data status."""
    st.markdown(f"""
    <div style="background-color: #11161D; border: 1px solid #171D25; border-radius: 8px; padding: 20px 24px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 28px; font-weight: 800; color: #F5F7FA; margin: 0; letter-spacing: -0.5px;">THE SHORTEST ORBIT</div>
            <div style="font-size: 13px; color: #9AA4B2; font-weight: 600; text-transform: uppercase; margin-top: 2px;">YouTube Growth Command Center</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 12px; font-weight: 700; color: #D29922; background: rgba(210, 153, 34, 0.12); padding: 4px 12px; border-radius: 4px; display: inline-block;">
                {data_source}
            </div>
            <div style="font-size: 12px; color: #9AA4B2; margin-top: 6px;">Last updated: <span style="color: #F5F7FA;">{last_update_str}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_channel_status_panel(status: str, narrative: str):
    """Section 1 — Channel Status Panel."""
    color_map = {
        "GROWING": "#2EA043",
        "STABLE": "#58A6FF",
        "DECLINING": "#F85149",
        "INSUFFICIENT DATA": "#9AA4B2"
    }
    status_color = color_map.get(status, "#58A6FF")

    st.markdown(f"""
    <div style="background-color: #11161D; border: 1px solid #171D25; border-left: 6px solid {status_color}; border-radius: 8px; padding: 20px 24px; margin-bottom: 24px;">
        <div style="font-size: 12px; font-weight: 700; color: #9AA4B2; text-transform: uppercase; letter-spacing: 1px;">CHANNEL STATUS</div>
        <div style="font-size: 32px; font-weight: 900; color: {status_color}; margin: 4px 0;">{status}</div>
        <div style="font-size: 15px; color: #F5F7FA; line-height: 1.5;">{narrative}</div>
    </div>
    """, unsafe_allow_html=True)


def render_youtube_metric_card(title: str, value: str, change_str: str, prev_val: str, tooltip: str = ""):
    """
    Section 2 — Real YouTube Metric Card (TYPE 1).
    Displays current value, change vs previous period, and previous baseline.
    NO V4 SCORES IN THIS ROW.
    """
    is_pos = "+" in change_str or change_str.startswith("+")
    is_neg = "-" in change_str and not change_str.startswith("0")
    change_color = "#2EA043" if is_pos else ("#F85149" if is_neg else "#9AA4B2")

    return f"""
    <div style="background-color: #11161D; border: 1px solid #171D25; border-radius: 8px; padding: 16px 18px; height: 100%;" title="{tooltip}">
        <div style="font-size: 12px; font-weight: 700; color: #9AA4B2; text-transform: uppercase; letter-spacing: 0.5px;">{title}</div>
        <div style="font-size: 26px; font-weight: 800; color: #F5F7FA; margin: 6px 0;">{value}</div>
        <div style="font-size: 13px; font-weight: 700; color: {change_color};">{change_str}</div>
        <div style="font-size: 12px; color: #9AA4B2; margin-top: 4px;">Previous: {prev_val}</div>
    </div>
    """


def render_bottleneck_section(bottleneck_info: dict):
    """Section 6 — Current Bottleneck Card (V4 Diagnostic)."""
    st.markdown(f"""
    <div style="background-color: #11161D; border: 1px solid #C1121F; border-left: 6px solid #C1121F; border-radius: 8px; padding: 22px 26px; margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size: 12px; font-weight: 800; color: #C1121F; text-transform: uppercase; letter-spacing: 1px;">CURRENT BOTTLENECK</div>
            <span style="font-size: 11px; font-weight: 700; color: #D29922; background: rgba(210, 153, 34, 0.15); padding: 2px 8px; border-radius: 4px;">V4 DIAGNOSTIC</span>
        </div>
        <div style="font-size: 22px; font-weight: 800; color: #F5F7FA; margin: 6px 0;">{bottleneck_info['bottleneck']}</div>
        <div style="font-size: 14px; color: #9AA4B2; margin-bottom: 12px;"><b>Why?</b> "{bottleneck_info['why']}"</div>
        <div style="font-size: 14px; color: #2EA043; background: rgba(46, 160, 67, 0.1); padding: 10px 14px; border-radius: 6px;">
            <b>WHAT TO DO:</b> {bottleneck_info['recommendation']}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_next_recommendations_section(recommendations: list):
    """Section 7 — What Should I Make Next? Panel."""
    st.markdown("""
    <div style="margin: 28px 0 16px 0; border-bottom: 1px solid #171D25; padding-bottom: 8px;">
        <h3 style="font-size: 20px; font-weight: 800; color: #F5F7FA; margin: 0;">NEXT CONTENT RECOMMENDATION</h3>
    </div>
    """, unsafe_allow_html=True)

    rcol1, rcol2, rcol3 = st.columns(3)
    for col, rec in zip([rcol1, rcol2, rcol3], recommendations):
        with col:
            st.markdown(f"""
            <div style="background-color: #11161D; border: 1px solid #171D25; border-radius: 8px; padding: 18px 20px; height: 100%;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size: 12px; font-weight: 800; color: #C1121F;">#{rec['rank']} TOPIC</div>
                    <span style="font-size: 10px; font-weight: 700; color: #D29922; background: rgba(210, 153, 34, 0.15); padding: 2px 6px; border-radius: 3px;">V4 INTERNAL</span>
                </div>
                <div style="font-size: 16px; font-weight: 700; color: #F5F7FA; margin: 8px 0;">{rec['topic']}</div>
                <div style="font-size: 13px; color: #9AA4B2; margin-bottom: 8px;">"{rec['why']}"</div>
                <div style="font-size: 13px; color: #D29922; font-weight: 700;">V4 Opportunity: {rec['opportunity']}</div>
                <div style="font-size: 12px; color: #9AA4B2; margin-top: 4px;">Angle: <b style="color:#F5F7FA;">{rec['angle']}</b> | Series: <b style="color:#F5F7FA;">{rec['series']}</b></div>
            </div>
            """, unsafe_allow_html=True)


def render_v4_learned_section(insight_text: str, confidence: str, evidence_count: int):
    """Section 8 — V4 Learned Brief Summary Banner."""
    st.markdown(f"""
    <div style="background-color: #11161D; border: 1px solid #171D25; border-left: 4px solid #58A6FF; border-radius: 8px; padding: 18px 22px; margin-top: 24px; margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size: 12px; font-weight: 800; color: #58A6FF; text-transform: uppercase;">V4 LEARNED</div>
            <span style="font-size: 11px; font-weight: 700; color: #2EA043; background: rgba(46, 160, 67, 0.15); padding: 2px 8px; border-radius: 4px;">CONFIDENCE: {confidence}</span>
        </div>
        <div style="font-size: 15px; color: #F5F7FA; margin: 8px 0; font-weight: 600;">"{insight_text}"</div>
        <div style="font-size: 12px; color: #9AA4B2;">Evidence: <b style="color:#F5F7FA;">{evidence_count} videos</b> analyzed.</div>
    </div>
    """, unsafe_allow_html=True)
