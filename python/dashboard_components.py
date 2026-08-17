"""
dashboard_components.py - Visual UI Component Library for THE SHORTEST ORBIT Dashboard.

Provides pixel-perfect, dark cinematic space/technology UI components with
clear visual separation, distinct containers, and crimson accents.
"""

import streamlit as st
import pandas as pd


def render_header_component(analyzed_count: int, last_update_str: str):
    """Renders top header banner with distinct styling and clear metadata."""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #161B22 0%, #0E1117 100%);
                border: 1px solid #30363D; border-left: 6px solid #C1121F;
                border-radius: 10px; padding: 22px 28px; margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(193, 18, 31, 0.12);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h1 style="font-size:30px; font-weight:800; color:#FFFFFF; margin:0; letter-spacing:-0.5px;">
                    🚀 THE SHORTEST ORBIT
                </h1>
                <div style="font-size:13px; color:#C1121F; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; margin-top:4px;">
                    YouTube Analytics Command Center
                </div>
            </div>
            <div style="text-align:right;">
                <span style="background-color:rgba(255, 215, 0, 0.15); color:#FFD700; border:1px solid #FFD700; padding:4px 12px; border-radius:20px; font-size:11px; font-weight:700;">
                    STORED SNAPSHOT DATA
                </span>
                <div style="font-size:12px; color:#8B949E; margin-top:6px;">Last update: <b style="color:#F0F6FC;">{last_update_str}</b></div>
                <div style="font-size:12px; color:#8B949E;">Analyzed Shorts: <b style="color:#FFFFFF;">{analyzed_count}</b></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_card(title: str, value: str, subtext: str, sub_color: str = "#3FB950", icon: str = "📊"):
    """Renders a single KPI card container with visual border separation."""
    return f"""
    <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 18px 20px; height: 100%;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size: 12px; font-weight: 700; color: #8B949E; text-transform: uppercase;">{title}</div>
            <div style="font-size: 18px;">{icon}</div>
        </div>
        <div style="font-size: 30px; font-weight: 800; color: #FFFFFF; margin: 8px 0;">{value}</div>
        <div style="font-size: 12px; font-weight: 700; color: {sub_color};">{subtext}</div>
    </div>
    """


def render_insight_banner(health_score: int, health_status: str, top_pillar: str, bottleneck_name: str):
    """Renders clean insight banner with visual border separation."""
    st.markdown(f"""
    <div style="background-color: rgba(193, 18, 31, 0.08); border-left: 4px solid #C1121F; border: 1px solid rgba(193, 18, 31, 0.3); border-radius: 8px; padding: 16px 22px; margin-bottom: 24px;">
        <div style="font-size: 12px; font-weight: 800; color: #C1121F; text-transform: uppercase; letter-spacing: 1px;">💡 KEY CHANNEL PERFORMANCE INSIGHT</div>
        <div style="font-size: 15px; color: #F0F6FC; margin-top: 6px; line-height: 1.5;">
            Your YouTube channel is operating with a <b>V4 Channel Health Score of {health_score}/100 ({health_status})</b>. 
            Top content pillar is <b>{top_pillar}</b>. 
            Main growth bottleneck identified on <b>{bottleneck_name}</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_bottleneck_card(bottleneck_info: dict):
    """Renders prominent bottleneck card with visual red accent border."""
    st.markdown(f"""
    <div style="background-color: #161B22; border: 1px solid #C1121F; border-left: 6px solid #C1121F; border-radius: 10px; padding: 20px 24px; margin-bottom: 24px;">
        <div style="font-size: 12px; font-weight: 800; color: #C1121F; text-transform: uppercase; letter-spacing: 1px;">
            ⚠️ CURRENT GROWTH BOTTLENECK: {bottleneck_info['bottleneck']}
        </div>
        <div style="font-size: 15px; font-weight: 700; color: #FFFFFF; margin: 8px 0;">
            Why: {bottleneck_info['why']}
        </div>
        <div style="font-size: 14px; color: #3FB950;">
            💡 <b>Recommended Action:</b> {bottleneck_info['recommendation']}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str = ""):
    """Renders a section header with clean underline separation."""
    st.markdown(f"""
    <div style="margin: 28px 0 16px 0; border-bottom: 1px solid #30363D; padding-bottom: 8px;">
        <h2 style="font-size: 22px; font-weight: 800; color: #FFFFFF; margin: 0;">{title}</h2>
        {f'<div style="font-size: 13px; color: #8B949E; margin-top: 2px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)
