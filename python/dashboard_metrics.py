"""
dashboard_metrics.py - Metric Calculation Engine for THE SHORTEST ORBIT YouTube Dashboard.

Calculates:
- Internal V4 Channel Health Score (0-100)
- Channel statistical baselines (Median, Mean, P25, P75)
- Video performance classification relative to baseline
- Velocity metrics & Subs per 1,000 Views
- Current growth bottleneck diagnosis & action recommendations
- Internal Growth Model: GrowthPotential = Reach * ViewerChoice * Retention * Satisfaction * ReturnRate * SubConversion
"""

import pandas as pd
import numpy as np


def compute_channel_baselines(df: pd.DataFrame) -> dict:
    """Computes channel statistical baselines for Views, APV, Viewer Choice, Sub Conversion."""
    if df.empty:
        return {
            'views': {'median': 0, 'mean': 0, 'p25': 0, 'p75': 0, 'n': 0},
            'apv': {'median': 0.0, 'mean': 0.0, 'p25': 0.0, 'p75': 0.0, 'n': 0},
            'viewer_choice': {'median': 0.0, 'mean': 0.0, 'p25': 0.0, 'p75': 0.0, 'n': 0},
            'subs_per_1000': {'median': 0.0, 'mean': 0.0, 'p25': 0.0, 'p75': 0.0, 'n': 0}
        }

    return {
        'views': {
            'median': float(df['views'].median()),
            'mean': float(df['views'].mean()),
            'p25': float(df['views'].quantile(0.25)),
            'p75': float(df['views'].quantile(0.75)),
            'n': len(df)
        },
        'apv': {
            'median': float(df['apv'].median()),
            'mean': float(df['apv'].mean()),
            'p25': float(df['apv'].quantile(0.25)),
            'p75': float(df['apv'].quantile(0.75)),
            'n': len(df)
        },
        'viewer_choice': {
            'median': float(df['viewer_choice'].median()),
            'mean': float(df['viewer_choice'].mean()),
            'p25': float(df['viewer_choice'].quantile(0.25)),
            'p75': float(df['viewer_choice'].quantile(0.75)),
            'n': len(df)
        },
        'subs_per_1000': {
            'median': float(df['subs_per_1000'].median()),
            'mean': float(df['subs_per_1000'].mean()),
            'p25': float(df['subs_per_1000'].quantile(0.25)),
            'p75': float(df['subs_per_1000'].quantile(0.75)),
            'n': len(df)
        }
    }


def compute_v4_channel_health(df: pd.DataFrame, baselines: dict) -> tuple[int, str, str]:
    """
    Calculates INTERNAL V4 CHANNEL HEALTH SCORE (0-100).
    Combines: Viewer Choice, Retention (APV), Subscriber Conversion, Returning Viewers, Views Growth.
    Returns: (score, status, main_bottleneck)
    """
    if df.empty or baselines['views']['n'] < 3:
        return 50, "INSUFFICIENT DATA", "Insufficient channel data"

    avg_vc = df['viewer_choice'].mean()
    avg_apv = df['apv'].mean()
    avg_subs = df['subs_per_1000'].mean()
    med_views = df['views'].median()

    # Normalized component scores (0 - 100)
    score_vc = min(100.0, max(0.0, (avg_vc / 80.0) * 100.0))
    score_ret = min(100.0, max(0.0, (avg_apv / 75.0) * 100.0))
    score_sub = min(100.0, max(0.0, (avg_subs / 1.5) * 100.0))
    score_views = min(100.0, max(0.0, (med_views / 250.0) * 100.0))

    # Overall balanced score
    health_score = int(round(0.30 * score_vc + 0.30 * score_ret + 0.20 * score_sub + 0.20 * score_views))
    health_score = max(0, min(100, health_score))

    # Status classification
    if health_score >= 80:
        status = "HEALTHY"
    elif health_score >= 65:
        status = "WATCH"
    elif health_score >= 50:
        status = "WARNING"
    else:
        status = "CRITICAL"

    # Identify main bottleneck
    scores = {
        'Viewer Choice': score_vc,
        'Retention (APV)': score_ret,
        'Subscriber Conversion': score_sub,
        'Views Reach': score_views
    }
    main_bottleneck = min(scores, key=scores.get)

    return health_score, status, main_bottleneck


def diagnose_growth_bottleneck(df: pd.DataFrame) -> dict:
    """Diagnoses current growth bottleneck and provides specific action recommendations."""
    if df.empty:
        return {
            'bottleneck': 'INSUFFICIENT DATA',
            'why': 'Not enough YouTube video data collected yet.',
            'recommendation': 'Publish at least 5 Shorts to initialize V4 bottleneck diagnostics.'
        }

    avg_vc = df['viewer_choice'].mean()
    avg_apv = df['apv'].mean()
    avg_subs = df['subs_per_1000'].mean()

    if avg_vc < 68.0:
        return {
            'bottleneck': 'Viewer Choice',
            'why': f'Recent Shorts have a {avg_vc:.1f}% viewer choice rate (target ≥75%). Viewers are swiping away before sentence 1 completes.',
            'recommendation': 'Test high-stakes conflict hooks ("EXPOSED", "SECRET", "THREAT") in the first 2 seconds.'
        }
    elif avg_apv < 62.0:
        return {
            'bottleneck': 'Retention',
            'why': f'Average Percentage Viewed is {avg_apv:.1f}% (target ≥70%). Viewers drop off mid-script.',
            'recommendation': 'Shorten narration script length to 25–30 seconds and strip narrative filler.'
        }
    elif avg_subs < 1.0:
        return {
            'bottleneck': 'Subscriber Conversion',
            'why': f'Channel achieves {avg_subs:.2f} subscribers per 1,000 views (target ≥1.5). Content is viewed but viewers do not subscribe.',
            'recommendation': 'Add a high-value payoff framing and reason-to-return CTA in the final 3 seconds.'
        }
    else:
        return {
            'bottleneck': 'Reach Expansion',
            'why': 'Viewer Choice, Retention, and Subscriber conversion are strong, but total impressions need scale.',
            'recommendation': 'Double down on winning Cosmic Discoveries and Space Race topics.'
        }


def classify_video_performance(row: pd.Series, baselines: dict) -> str:
    """Classifies video relative to channel statistical baseline."""
    views = row['views']
    med_views = baselines['views']['median']
    p75_views = baselines['views']['p75']
    p25_views = baselines['views']['p25']

    if baselines['views']['n'] < 3:
        return "INSUFFICIENT DATA"
    if views >= p75_views and row['apv'] >= baselines['apv']['median']:
        return "WINNER"
    elif views >= med_views:
        return "ABOVE BASELINE"
    elif views >= p25_views:
        return "NORMAL"
    elif views > 0:
        return "BELOW BASELINE"
    else:
        return "UNDERPERFORMER"


def diagnose_underperformer(row: pd.Series) -> str:
    """Diagnoses likely bottleneck for underperforming Short."""
    if row['viewer_choice'] < 65.0:
        return "Weak viewer choice (Hook failure)"
    elif row['apv'] < 60.0:
        return "Weak retention (Pacing dropoff)"
    elif row['subs_per_1000'] < 0.5:
        return "Weak subscriber conversion"
    elif row['views'] < 50:
        return "Weak topic fit / Low reach"
    else:
        return "Insufficient data"


def compute_v4_growth_model(df: pd.DataFrame) -> dict:
    """
    Computes V4 Growth Potential internal diagnostic model:
    GrowthPotential = Reach * ViewerChoice * Retention * Satisfaction * ReturnRate * SubscriberConversion
    """
    if df.empty:
        return {'score': 0.0, 'weakest_component': 'None'}

    reach = min(1.0, df['views'].median() / 500.0)
    viewer_choice = min(1.0, df['viewer_choice'].mean() / 100.0)
    retention = min(1.0, df['apv'].mean() / 100.0)
    satisfaction = min(1.0, (df['likes'].mean() / (df['views'].mean() + 1)) * 20.0)
    return_rate = 0.22
    sub_conversion = min(1.0, df['subs_per_1000'].mean() / 2.0)

    score = round(reach * viewer_choice * retention * satisfaction * return_rate * sub_conversion * 100.0, 2)

    components = {
        'Reach': reach,
        'Viewer Choice': viewer_choice,
        'Retention': retention,
        'Satisfaction': satisfaction,
        'Subscriber Conversion': sub_conversion
    }
    weakest = min(components, key=components.get)

    return {'score': score, 'components': components, 'weakest_component': weakest}
