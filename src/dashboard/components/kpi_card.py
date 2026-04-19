"""
Placeholder module.
Este archivo se completará en el desarrollo del dashboard.
"""

import streamlit as st


_TONE_STYLES = {
    "blue": {"accent": "#234B8D", "bg": "#FFFFFF"},
    "yellow": {"accent": "#D5B700", "bg": "#FFFCE0"},
    "red": {"accent": "#C0392B", "bg": "#FFF1F1"},
    "dark": {"accent": "#0F1E3C", "bg": "#F4F4F9"},
}


def _ensure_styles():
    st.markdown(
        """
        <style>
        .jj-kpi-card {
            border-radius: 18px;
            padding: 1rem 1rem 0.95rem 1rem;
            border: 1px solid rgba(35, 75, 141, 0.08);
            box-shadow: 0 18px 34px rgba(15, 30, 60, 0.08);
            min-height: 152px;
        }
        .jj-kpi-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            opacity: 0.72;
            font-weight: 700;
            margin-bottom: 0.6rem;
        }
        .jj-kpi-value {
            font-size: 1.65rem;
            line-height: 1.04;
            font-weight: 800;
            margin-bottom: 0.4rem;
        }
        .jj-kpi-delta {
            font-size: 0.84rem;
            font-weight: 700;
            margin-bottom: 0.32rem;
        }
        .jj-kpi-caption {
            font-size: 0.86rem;
            line-height: 1.42;
            color: #4A5672;
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
