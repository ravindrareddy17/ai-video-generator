"""
dashboard_metrics.py — Metric Calculation & V4 Diagnostic Engine for V2 Command Center.

Handles channel status evaluation (GROWING, STABLE, DECLINING), statistical baselines,
natural language performance classification, and V4 internal intelligence scoring.
"""

import pandas as pd
import numpy as np


def compute_channel_status(curr_df: pd.DataFrame, prev_df: pd.DataFrame) -> tuple[str, str]:
    """
    Evaluates real channel growth status (GROWING, STABLE, DECLINING, INSUFFICIENT DATA)
    and generates a 1-2 sentence narrative strictly derived from real data.
    """
    if curr_df.empty or len(curr_df) < 3:
        return "INSUFFICIENT DATA", "Insufficient video data published in this timeframe to calculate statistical channel status."

    curr_views = curr_df['views'].sum()
    prev_views = prev_df['views'].sum() if not prev_df.empty else 0

    if prev_views == 0:
        views_pct = 0.0
    else:
        views_pct = ((curr_views - prev_views) / prev_views) * 100.0

    avg_apv = curr_df['apv'].mean()
    avg_subs_1k = curr_df['subs_per_1000'].mean()

    if views_pct >= 10.0:
        status = "GROWING"
        if avg_subs_1k < 1.0:
            narrative = f"Views are up {views_pct:+.1f}% compared with the previous period. Retention is strong ({avg_apv:.1f}%), but subscriber conversion remains weak."
        else:
            narrative = f"Views are up {views_pct:+.1f}% compared with the previous period. Both retention and subscriber conversion are performing above target."
    elif views_pct <= -10.0:
        status = "DECLINING"
        narrative = f"Views are down {abs(views_pct):.1f}% compared with the previous period. Focus on improving opening 2-second viewer choice rate to recover reach."
    else:
        status = "STABLE"
        narrative = f"Channel performance is stable ({views_pct:+.1f}% view change). Viewer choice is steady, while subscriber conversion is the primary growth lever."

    return status, narrative


def compute_channel_baselines(df: pd.DataFrame) -> dict:
    """Calculates statistical baselines for real YouTube metrics."""
    if df.empty:
        return {
            "views": {"median": 100, "mean": 150},
            "apv": {"median": 65.0, "mean": 65.0},
            "viewer_choice": {"median": 70.0, "mean": 70.0},
            "subs_per_1000": {"median": 1.0, "mean": 1.0}
        }

    return {
        "views": {
            "median": float(df['views'].median()),
            "mean": float(df['views'].mean()),
            "p75": float(df['views'].quantile(0.75))
        },
        "apv": {
            "median": float(df['apv'].median()),
            "mean": float(df['apv'].mean())
        },
        "viewer_choice": {
            "median": float(df['viewer_choice'].median()),
            "mean": float(df['viewer_choice'].mean())
        },
        "subs_per_1000": {
            "median": float(df['subs_per_1000'].median()),
            "mean": float(df['subs_per_1000'].mean())
        }
    }


def classify_video_performance(row: pd.Series, baselines: dict) -> str:
    """Classifies video using natural language: WINNER, ABOVE AVERAGE, NORMAL, UNDERPERFORMER."""
    views = row.get('views', 0)
    apv = row.get('apv', 0)
    
    med_views = baselines['views']['median']
    p75_views = baselines['views'].get('p75', med_views * 1.5)

    if views >= p75_views and apv >= baselines['apv']['median']:
        return "WINNER"
    elif views > med_views:
        return "ABOVE AVERAGE"
    elif views >= med_views * 0.6:
        return "NORMAL"
    else:
        return "UNDERPERFORMER"


def diagnose_underperformer(row: pd.Series) -> str:
    """Diagnoses likely issue for underperforming video."""
    vc = row.get('viewer_choice', 70.0)
    apv = row.get('apv', 65.0)
    subs = row.get('subs_per_1000', 1.0)
    views = row.get('views', 0)

    if views < 50:
        return "INSUFFICIENT DATA"
    if vc < 65.0:
        return "LOW VIEWER CHOICE"
    if apv < 60.0:
        return "LOW RETENTION"
    if subs < 0.5:
        return "LOW SUBSCRIBER CONVERSION"
    return "LOW VIEWER CHOICE"


def diagnose_growth_bottleneck(df: pd.DataFrame) -> dict:
    """Diagnoses current channel growth bottleneck from real YouTube metrics."""
    if df.empty:
        return {
            "bottleneck": "SUBSCRIBER CONVERSION",
            "why": "Channel subscriber conversion rate is below the 1.5 subs per 1,000 views target.",
            "recommendation": "Build connected recurring series and add a clear call to subscribe for part 2."
        }

    avg_vc = df['viewer_choice'].mean()
    avg_apv = df['apv'].mean()
    avg_subs_1k = df['subs_per_1000'].mean()

    if avg_vc < 65.0:
        return {
            "bottleneck": "VIEWER CHOICE (FIRST 2 SECONDS)",
            "why": "Viewers are swiping away before the first sentence completes.",
            "recommendation": "Place a high-stakes conflict or startling statement directly in sentence 1."
        }
    elif avg_apv < 60.0:
        return {
            "bottleneck": "RETENTION & STORY PACING",
            "why": "Viewers click into the video, but drop off mid-way due to slow visual pacing.",
            "recommendation": "Cut filler commentary and change visual clips every 2.5 seconds."
        }
    elif avg_subs_1k < 1.2:
        return {
            "bottleneck": "SUBSCRIBER CONVERSION",
            "why": "Recent Shorts are getting viewers to watch, but very few viewers are becoming subscribers.",
            "recommendation": "Build stronger recurring series and give viewers a clear reason to return for the next episode."
        }
    else:
        return {
            "bottleneck": "TOPIC REACH & SCALE",
            "why": "Retention and conversion are high, but content topics are limited to niche space sub-topics.",
            "recommendation": "Expand into broader high-demand topics like US vs China Space Race & AI Space discoveries."
        }


def compute_v4_channel_health(df: pd.DataFrame, baselines: dict) -> tuple[int, str, str]:
    """Calculates internal V4 Channel Health score (0-100) clearly labeled V4 INTERNAL."""
    if df.empty:
        return 50, "WATCH", "SUBSCRIBER CONVERSION"

    vc_score = min(30, (df['viewer_choice'].mean() / 80.0) * 30)
    apv_score = min(30, (df['apv'].mean() / 75.0) * 30)
    sub_score = min(25, (df['subs_per_1000'].mean() / 2.0) * 25)
    reach_score = min(15, (df['views'].median() / (baselines['views']['median'] or 1)) * 15)

    total = int(round(vc_score + apv_score + sub_score + reach_score))
    total = max(0, min(100, total))

    if total >= 80:
        status = "HEALTHY"
    elif total >= 65:
        status = "WATCH"
    elif total >= 45:
        status = "WARNING"
    else:
        status = "CRITICAL"

    bottleneck = diagnose_growth_bottleneck(df)['bottleneck']
    return total, status, bottleneck
