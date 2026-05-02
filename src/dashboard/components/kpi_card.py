"""
Placeholder module.
Este archivo se completará en el desarrollo del dashboard.
"""

import streamlit as st


_TONE_STYLES = {
    "blue": {"accent": "#082A70", "bg": "#FFFFFF"},
    "yellow": {"accent": "#7E6900", "bg": "#FFFCE8"},
    "red": {"accent": "#9E1E33", "bg": "#FFF1F2"},
    "green": {"accent": "#2E8E5B", "bg": "#EAF7EE"},
    "dark": {"accent": "#121212", "bg": "#F8FAF7"},
}


def _ensure_styles():
    st.markdown(
        """
        <style>
        .jj-kpi-card {
            border-radius: 24px;
            padding: 1.05rem 1.05rem 0.95rem 1.05rem;
            border: 1px solid rgba(8, 42, 112, 0.18);
            box-shadow: 0 14px 30px rgba(16, 31, 56, 0.08);
            min-height: 162px;
        }
        .jj-kpi-label {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            opacity: 0.8;
            font-weight: 760;
            margin-bottom: 0.52rem;
            color: #5F6B7A;
        }
        .jj-kpi-value {
            font-size: 2rem;
            line-height: 1.04;
            font-weight: 820;
            margin-bottom: 0.33rem;
        }
        .jj-kpi-delta {
            font-size: 0.79rem;
            font-weight: 700;
            margin-bottom: 0.32rem;
        }
        .jj-kpi-caption {
            font-size: 0.8rem;
            line-height: 1.43;
            color: #5F6B7A;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(
    label: str,
    value: str,
    caption: str = "",
    delta: str = "",
    tone: str = "blue",
) -> None:
    _ensure_styles()
    style = _TONE_STYLES.get(tone, _TONE_STYLES["blue"])
    delta_html = f'<div class="jj-kpi-delta" style="color:{style["accent"]};">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="jj-kpi-card" style="background:{style['bg']};">
            <div class="jj-kpi-label">{label}</div>
            <div class="jj-kpi-value" style="color:{style['accent']};">{value}</div>
            {delta_html}
            <div class="jj-kpi-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
