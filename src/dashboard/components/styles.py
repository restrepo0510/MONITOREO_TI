from __future__ import annotations

import streamlit as st


COLOR_TOKENS = {
    "bg": "#EEF2EC",
    "card": "#FFFFFF",
    "text": "#121212",
    "muted": "#5F6B7A",
    "border": "rgba(0,0,0,0.06)",
    "blue": "#234B8D",
    "yellow": "#FFE600",
    "low": "#2ecc71",
    "medium": "#f39c12",
    "high": "#e74c3c",
    "sensor": "#234B8D",
    "temperature": "#f39c12",
    "pressure": "#2ecc71",
    "energy": "#FFE600",
    "prediction": "#8e44ad",
    "alerts": "#e74c3c",
}


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ds-bg: #EEF2EC;
            --ds-card: #FFFFFF;
            --ds-text: #121212;
            --ds-muted: #5F6B7A;
            --ds-border: rgba(0,0,0,0.06);
            --ds-blue: #234B8D;
            --ds-yellow: #FFE600;
            --ds-low: #2ecc71;
            --ds-medium: #f39c12;
            --ds-high: #e74c3c;
            --ds-shadow-soft: 0 8px 24px rgba(16, 24, 40, 0.06);
            --ds-shadow-card: 0 14px 32px rgba(16, 24, 40, 0.08);
        }

        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 7% 0%, rgba(255, 230, 0, 0.12), transparent 24%),
                        linear-gradient(180deg, #F4F6F3 0%, var(--ds-bg) 100%);
        }

        [data-testid="stMainBlockContainer"], .main .block-container {
            max-width: 1540px !important;
            padding-top: 1.1rem !important;
            padding-bottom: 2.6rem !important;
        }

        .ds-page-header {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin-bottom: 0.15rem;
        }

        .ds-page-dot {
            width: 16px;
            height: 16px;
            border-radius: 999px;
            background: var(--ds-yellow);
            box-shadow: 0 0 0 3px rgba(255, 230, 0, 0.35);
            flex-shrink: 0;
        }

        .ds-page-title {
            color: #1b2949;
            font-size: 3rem;
            font-weight: 800;
            line-height: 1.05;
            margin: 0;
            letter-spacing: 0.2px;
        }

        .ds-page-subtitle {
            color: var(--ds-muted);
            font-size: 1rem;
            line-height: 1.48;
            margin-top: 0.2rem;
            margin-bottom: 0;
        }

        .ds-clock-chip {
            background: #F7F9FC;
            border: 1px solid var(--ds-border);
            border-radius: 16px;
            padding: 0.85rem 1rem;
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            color: #67748a;
            font-size: 0.95rem;
            font-weight: 600;
            justify-content: center;
            width: 100%;
            box-shadow: var(--ds-shadow-soft);
        }

        .ds-section-head {
            margin-top: 1.1rem;
            margin-bottom: 0.7rem;
        }

        .ds-section-title {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-size: 2rem;
            color: #1f2a44;
            font-weight: 780;
            line-height: 1.2;
            margin: 0;
        }

        .ds-section-title::before {
            content: "";
            width: 12px;
            height: 12px;
            border-radius: 999px;
            background: var(--ds-yellow);
            box-shadow: 0 0 0 2px rgba(255, 230, 0, 0.25);
            flex-shrink: 0;
        }

        .ds-section-subtitle {
            color: var(--ds-muted);
            font-size: 0.93rem;
            line-height: 1.48;
            margin-top: 0.25rem;
        }

        .ds-card {
            background: var(--ds-card);
            border: 1px solid var(--ds-border);
            border-radius: 24px;
            box-shadow: var(--ds-shadow-soft);
            transition: transform 140ms ease, box-shadow 140ms ease;
        }

        .ds-card:hover {
            transform: translateY(-1px);
            box-shadow: var(--ds-shadow-card);
        }

        .ds-kpi-card {
            padding: 17px;
            min-height: 132px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            gap: 6px;
        }

        .ds-kpi-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }

        .ds-kpi-title {
            color: #121212;
            font-size: 13px;
            line-height: 1.2;
            font-weight: 500;
            margin-bottom: 6px;
        }

        .ds-kpi-main-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .ds-kpi-value {
            color: #121212;
            font-size: 30px;
            font-weight: 700;
            line-height: 1;
        }

        .ds-kpi-delta {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            width: fit-content;
            padding: 2px 10px;
            font-size: 13px;
            font-weight: 650;
            margin-top: 0;
            color: #2f6c45;
            background: rgba(46, 204, 113, 0.16);
        }

        .ds-kpi-meta {
            color: var(--ds-muted);
            font-size: 12px;
            line-height: 1.32;
            margin-top: 0;
            min-height: 16px;
        }

        .ds-status-card {
            padding: 17px;
            min-height: 132px;
            border-left: 4px solid var(--ds-blue);
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            gap: 6px;
        }

        .ds-status-main-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .ds-status-text-block {
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 6px;
            min-width: 0;
        }

        .ds-status-inline {
            display: flex;
            align-items: baseline;
            gap: 6px;
            flex-wrap: wrap;
        }

        .ds-status-inline-text {
            font-size: 30px;
            font-weight: 600;
            line-height: 1;
        }

        .ds-status-title {
            color: #121212;
            font-size: inherit;
            font-weight: 600;
            line-height: 1.2;
            margin-bottom: 0;
        }

        .ds-status-value {
            font-size: inherit;
            font-weight: 700;
            line-height: 1;
        }

        .ds-status-value-low { color: #37B26C; }
        .ds-status-value-medium { color: #C9881C; }
        .ds-status-value-high { color: #D9534F; }

        .ds-status-primary {
            color: #2a364f;
            font-size: 38px;
            font-weight: 760;
            line-height: 1.1;
        }

        .ds-status-meta {
            margin-top: 0;
        }

        .ds-status-secondary {
            color: var(--ds-muted);
            font-size: 12px;
            margin-top: 0;
            margin-left: 54px;
            line-height: 1.3;
        }

        .ds-icon-chip {
            width: 41px;
            height: 41px;
            border-radius: 11px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--icon-bg, rgba(35, 75, 141, 0.10));
            color: var(--icon-color, var(--ds-blue));
            border: 1px solid rgba(35, 75, 141, 0.10);
            flex-shrink: 0;
        }

        .ds-icon-chip svg {
            width: 19px;
            height: 19px;
        }

        [class*="st-key-ds-chart-card-"], [class*="st-key-ds-sensor-card-"], [class*="st-key-ds-golden-card-"] {
            background: var(--ds-card);
            border: 1px solid var(--ds-border);
            border-radius: 24px;
            box-shadow: var(--ds-shadow-soft);
            padding: 17px;
            margin-bottom: 0.8rem;
        }

        [class*="st-key-ds-chart-card-"] [data-testid="stPlotlyChart"],
        [class*="st-key-ds-sensor-card-"] [data-testid="stPlotlyChart"],
        [class*="st-key-ds-golden-card-"] [data-testid="stPlotlyChart"] {
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            background: transparent !important;
            margin-top: 0.4rem !important;
            margin-bottom: 0 !important;
        }

        .ds-chart-title {
            color: #121212;
            font-size: 13px;
            font-weight: 500;
            margin: 0 0 6px 0;
        }

        .ds-chart-subtitle {
            color: var(--ds-muted);
            font-size: 12px;
            margin: 0 0 0.25rem 0;
        }

        .ds-finance-card {
            padding: 1.05rem 1rem;
            min-height: 142px;
        }

        .ds-finance-title {
            color: #354562;
            font-size: 0.84rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 680;
        }

        .ds-finance-value {
            font-size: 2rem;
            line-height: 1.08;
            font-weight: 800;
            margin-top: 0.44rem;
            margin-bottom: 0.24rem;
        }

        .ds-finance-desc {
            color: #5F6B7A;
            font-size: 0.86rem;
        }

        .ds-finance-reactive { background: linear-gradient(180deg, #FFF8F8 0%, #FFF1F1 100%); }
        .ds-finance-reactive .ds-finance-value { color: #D84040; }

        .ds-finance-preventive { background: linear-gradient(180deg, #FFFDF4 0%, #FFF9E7 100%); }
        .ds-finance-preventive .ds-finance-value { color: #B78000; }

        .ds-finance-savings { background: linear-gradient(180deg, #F7FCF8 0%, #EDF9EF 100%); }
        .ds-finance-savings .ds-finance-value { color: #1F8A42; }

        .ds-table-wrap {
            overflow-x: auto;
            border: 1px solid var(--ds-border);
            border-radius: 20px;
            background: #FFFFFF;
            box-shadow: var(--ds-shadow-soft);
        }

        .ds-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 680px;
        }

        .ds-table th {
            text-align: left;
            font-size: 0.88rem;
            color: #60708b;
            font-weight: 640;
            background: #F8FAFD;
            padding: 0.82rem 0.9rem;
            border-bottom: 1px solid var(--ds-border);
        }

        .ds-table td {
            font-size: 0.93rem;
            color: #24324d;
            padding: 0.86rem 0.9rem;
            border-bottom: 1px solid rgba(0,0,0,0.04);
            vertical-align: middle;
        }

        .ds-table tbody tr:nth-child(even) td {
            background: #FCFDFF;
        }

        .ds-table tbody tr:hover td {
            background: #F6F9FF;
        }

        .ds-progress {
            width: 100%;
            background: rgba(35, 75, 141, 0.08);
            border-radius: 999px;
            height: 9px;
            position: relative;
            overflow: hidden;
            margin-right: 0.6rem;
        }

        .ds-progress-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #2F5FA8 0%, #234B8D 100%);
        }

        .ds-progress-cell {
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: center;
            gap: 0.6rem;
        }

        .ds-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.2rem 0.58rem;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.03em;
        }

        .ds-badge-low { background: rgba(55,178,108,0.16); color: #2C8D59; }
        .ds-badge-medium { background: rgba(243,156,18,0.2); color: #99600c; }
        .ds-badge-high { background: rgba(231,76,60,0.16); color: #c0392b; }

        .ds-pill-action {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.28rem 0.75rem;
            color: #234B8D;
            background: rgba(35, 75, 141, 0.08);
            font-size: 0.82rem;
            font-weight: 700;
            border: 1px solid rgba(35, 75, 141, 0.16);
        }

        .ds-action-card, .ds-event-card {
            background: #FFFFFF;
            border: 1px solid var(--ds-border);
            border-radius: 20px;
            box-shadow: var(--ds-shadow-soft);
            padding: 0.9rem 0.95rem;
        }

        .ds-action-title, .ds-event-title {
            color: #1e2b45;
            font-size: 0.96rem;
            font-weight: 740;
            margin-bottom: 0.42rem;
        }

        .ds-action-content, .ds-event-content {
            color: var(--ds-muted);
            font-size: 0.86rem;
            line-height: 1.48;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
