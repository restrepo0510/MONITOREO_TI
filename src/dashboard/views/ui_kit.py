from __future__ import annotations

from urllib.parse import quote

import streamlit as st


def _metro_cursor_data_uri() -> str:
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
      <defs>
        <linearGradient id="g" x1="8" y1="4" x2="40" y2="44" gradientUnits="userSpaceOnUse">
          <stop stop-color="#FFE600"/>
          <stop offset="0.42" stop-color="#F6C50E"/>
          <stop offset="1" stop-color="#082A70"/>
        </linearGradient>
      </defs>
      <path d="M24 4C15.2 4 9 10.1 9 19v9.6C9 36.3 15.5 43 24 43s15-6.7 15-14.4V19C39 10.1 32.8 4 24 4Z" fill="url(#g)" stroke="#050505" stroke-width="2"/>
      <path d="M14 18c.7-5.1 4.4-8.2 10-8.2s9.3 3.1 10 8.2H14Z" fill="#F9F8F8" stroke="#050505" stroke-width="1.5"/>
      <path d="M14 21h20v8H14z" fill="#102A44" stroke="#050505" stroke-width="1.4"/>
      <path d="M17.2 29.5h13.6" stroke="#B8DBD9" stroke-width="1.7" stroke-linecap="round"/>
      <circle cx="17.2" cy="34.8" r="2.6" fill="#F9F8F8" stroke="#050505" stroke-width="1"/>
      <circle cx="30.8" cy="34.8" r="2.6" fill="#F9F8F8" stroke="#050505" stroke-width="1"/>
      <path d="M20.4 16.6c0-1.3.9-2.2 2.1-2.2s2.1.9 2.1 2.2v1.7c0 .9.7 1.6 1.6 1.6s1.6-.7 1.6-1.6v-3.7" fill="none" stroke="#082A70" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M7 7l9 4-7 4Z" fill="#050505"/>
    </svg>
    """
    return f"data:image/svg+xml,{quote(svg.strip())}"


def inject_custom_css(force: bool = False) -> None:
    """Inyecta el sistema visual global del dashboard."""
    cursor_uri = _metro_cursor_data_uri()
    css = """
        <style>
        :root {
            --mt-blue: #082A70;
            --mt-yellow: #F6C50E;
            --mt-bg: #F9F8F8;
            --mt-card: #FFFFFF;
            --mt-card-soft: #F8FAF7;
            --mt-text: #121212;
            --mt-muted: #5F6B7A;
            --mt-border: rgba(8, 42, 112, 0.18);
            --mt-shadow: 0 16px 34px rgba(16, 31, 56, 0.08);
            --mt-shadow-soft: 0 10px 24px rgba(16, 31, 56, 0.06);
            --mt-radius-xl: 28px;
            --mt-radius-lg: 24px;
            --mt-radius-md: 16px;
        }

        * {
            cursor: url("CURSOR_URI") 8 8, auto !important;
        }

        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 6% 0%, rgba(246, 197, 14, 0.16), transparent 24%),
                        linear-gradient(180deg, #F9F8F8 0%, var(--mt-bg) 100%);
            color: var(--mt-text);
        }

        [data-testid="stMainBlockContainer"],
        .main .block-container {
            padding-top: 1.1rem !important;
            padding-bottom: 2.8rem !important;
            max-width: 1600px !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #082A70 0%, #061F54 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.20);
        }

        [data-testid="stSidebar"] * {
            color: #F8FAF7;
        }

        [data-testid="stSidebar"] .stButton > button {
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.25);
            background: rgba(255, 255, 255, 0.10);
            color: #FFFFFF;
            box-shadow: none;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background: #FFFFFF;
            color: var(--mt-blue);
            border-color: #FFFFFF;
        }

        h1, h2, h3, h4, h5 {
            color: var(--mt-text);
            letter-spacing: 0.1px;
        }

        hr {
            border-top: 1px solid var(--mt-border);
            margin-top: 1.3rem;
            margin-bottom: 1.3rem;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, var(--mt-card) 0%, var(--mt-card-soft) 100%);
            border: 1px solid var(--mt-border);
            border-radius: var(--mt-radius-lg);
            padding: 0.85rem 0.95rem;
            box-shadow: var(--mt-shadow-soft);
            min-height: 122px;
        }

        div[data-testid="stMetricLabel"] p {
            color: var(--mt-muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            color: var(--mt-blue);
            font-size: 2rem;
            line-height: 1.02;
            font-weight: 800;
        }

        div[data-testid="stMetricDelta"] {
            color: #4A5A77;
            font-size: 0.82rem;
            font-weight: 700;
        }

        div[data-testid="stPlotlyChart"] {
            background: var(--mt-card);
            border: 1px solid var(--mt-border);
            border-radius: var(--mt-radius-lg);
            box-shadow: var(--mt-shadow-soft);
            padding: 0.45rem 0.55rem 0.25rem 0.55rem;
            margin-bottom: 0.8rem;
            overflow: hidden;
        }

        div[data-testid="stDataFrame"] {
            background: var(--mt-card);
            border: 1px solid var(--mt-border);
            border-radius: var(--mt-radius-lg);
            box-shadow: var(--mt-shadow-soft);
            padding: 0.22rem;
        }

        .stButton > button {
            border-radius: 999px;
            border: 1px solid var(--mt-border);
            background: #FFFFFF;
            color: var(--mt-blue);
            font-weight: 700;
            box-shadow: 0 6px 14px rgba(15, 30, 60, 0.05);
        }

        .stButton > button:hover {
            border-color: rgba(8, 42, 112, 0.42);
            color: #173A73;
            background: #F9FBFF;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            border-radius: 14px !important;
            border-color: var(--mt-border) !important;
            background: #FFFFFF !important;
            color: var(--mt-text) !important;
        }

        div[data-baseweb="input"] input,
        div[data-baseweb="input"] textarea,
        div[data-baseweb="select"] input,
        [data-testid="stNumberInput"] input {
            color: var(--mt-text) !important;
            background: transparent !important;
            caret-color: var(--mt-blue) !important;
        }

        div[data-baseweb="select"] [data-testid="stMarkdownContainer"],
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div[class] {
            color: var(--mt-text) !important;
        }

        [data-testid="stNumberInput"] button,
        [data-testid="stNumberInput"] [data-testid="baseButton-secondary"] {
            background: var(--mt-blue) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            min-width: 32px !important;
            min-height: 32px !important;
        }

        [data-testid="stNumberInput"] button:hover,
        [data-testid="stNumberInput"] [data-testid="baseButton-secondary"]:hover {
            background: #173A73 !important;
            color: #FFFFFF !important;
        }

        [data-testid="stNumberInput"] button svg,
        [data-testid="stNumberInput"] [data-testid="baseButton-secondary"] svg {
            fill: #FFFFFF !important;
            stroke: #FFFFFF !important;
        }

        .stTextInput > div > div,
        .stSelectbox > div > div,
        .stNumberInput > div > div {
            background: #FFFFFF !important;
            color: var(--mt-text) !important;
        }

        .stTextInput label,
        .stSelectbox label,
        .stNumberInput label,
        .stSlider label,
        .stCheckbox label,
        .stRadio label {
            color: var(--mt-text) !important;
            font-weight: 600;
        }

        .mt-main-title {
            color: var(--mt-blue);
            font-size: 2.28rem;
            font-weight: 850;
            line-height: 1.04;
            margin: 0;
            letter-spacing: 0.1px;
        }

        .mt-main-subtitle {
            color: var(--mt-muted);
            font-size: 0.97rem;
            line-height: 1.58;
            margin-top: 0.4rem;
            margin-bottom: 1.15rem;
            max-width: 980px;
        }

        .mt-section-title {
            font-size: 1.2rem;
            font-weight: 760;
            color: var(--mt-blue);
            margin-top: 1.35rem;
            margin-bottom: 0.12rem;
            display: flex;
            align-items: center;
            gap: 0.55rem;
        }

        .mt-section-title::before {
            content: "";
            width: 9px;
            height: 9px;
            border-radius: 999px;
            background: var(--mt-yellow);
            box-shadow: 0 0 0 2px rgba(8, 42, 112, 0.20);
        }

        .mt-section-subtitle {
            color: var(--mt-muted);
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 0.85rem;
        }

        .mt-panel {
            background: linear-gradient(180deg, #FFFFFF 0%, #F9FCF8 100%);
            border-radius: var(--mt-radius-xl);
            padding: 1.12rem 1.15rem;
            border: 1px solid var(--mt-border);
            box-shadow: var(--mt-shadow);
            margin-bottom: 1rem;
        }

        .mt-level {
            width: 100%;
            border-radius: 18px;
            padding: 0.9rem 1rem;
            margin: 0.2rem 0 0.6rem 0;
            border: 1px solid transparent;
            box-shadow: var(--mt-shadow-soft);
        }

        .mt-level-title {
            font-size: 1rem;
            font-weight: 820;
            line-height: 1.1;
            margin-bottom: 0.16rem;
        }

        .mt-level-copy {
            font-size: 0.88rem;
            line-height: 1.45;
            opacity: 0.96;
        }

        .mt-level-high {
            background: linear-gradient(135deg, #8E1D2B 0%, #C52F3D 100%);
            color: #F4F7F9;
            border-color: rgba(142, 29, 43, 0.32);
        }

        .mt-level-medium {
            background: linear-gradient(135deg, #F6C50E 0%, #F8D400 100%);
            color: #223047;
            border-color: rgba(212, 177, 0, 0.35);
        }

        .mt-level-low {
            background: linear-gradient(135deg, #082A70 0%, #061F54 100%);
            color: #F4F7F9;
            border-color: rgba(8, 42, 112, 0.35);
        }

        @media (max-width: 900px) {
            .mt-main-title {
                font-size: 1.72rem;
            }
            div[data-testid="stMetricValue"] {
                font-size: 1.55rem;
            }
            div[data-testid="stMetric"] {
                min-height: 110px;
            }
        }
        </style>
        """
    css = css.replace("CURSOR_URI", cursor_uri)
    st.markdown(css, unsafe_allow_html=True)


def inject_operational_ui() -> None:
    inject_custom_css()


def render_view_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="mt-main-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mt-main-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="mt-section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mt-section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_level_badge(level: str, score: float | None = None, detail: str | None = None) -> None:
    normalized = str(level).upper()
    if normalized == "ALTO":
        css = "mt-level mt-level-high"
        title = "Estado actual: Riesgo ALTO"
    elif normalized == "MEDIO":
        css = "mt-level mt-level-medium"
        title = "Estado actual: Riesgo MEDIO"
    else:
        css = "mt-level mt-level-low"
        title = "Estado actual: Riesgo BAJO"

    score_copy = f"Score de riesgo: {score:.3f}" if score is not None else ""
    extra = f" {detail}" if detail else ""
    copy = f"{score_copy}{extra}".strip()
    if not copy:
        copy = "Sin detalle adicional."

    st.markdown(
        f"""
        <div class="{css}">
            <div class="mt-level-title">{title}</div>
            <div class="mt-level-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
