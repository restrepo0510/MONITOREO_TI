"""
Placeholder module.
Este archivo se completará en el desarrollo del dashboard.
"""

import streamlit as st


_LEVEL_STYLES = {
    "ALTO": {
        "bg": "linear-gradient(135deg, #A61E2E 0%, #D32F2F 100%)",
        "text": "#F4F4F9",
        "border": "rgba(166, 30, 46, 0.24)",
    },
    "MEDIO": {
        "bg": "linear-gradient(135deg, #FFE600 0%, #FFD000 100%)",
        "text": "#0F1E3C",
        "border": "rgba(255, 208, 0, 0.24)",
    },
    "BAJO": {
        "bg": "linear-gradient(135deg, #234B8D 0%, #173A73 100%)",
        "text": "#F4F4F9",
        "border": "rgba(35, 75, 141, 0.22)",
    },
}


def _ensure_styles():
    st.markdown(
        """
        <style>
        .jj-alert-badge {
            border-radius: 18px;
            padding: 0.95rem 1rem;
            box-shadow: 0 18px 32px rgba(15, 30, 60, 0.10);
            border: 1px solid transparent;
        }
        .jj-alert-badge-label {
            font-size: 0.78rem;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            opacity: 0.85;
            margin-bottom: 0.3rem;
            font-weight: 700;
        }
        .jj-alert-badge-value {
            font-size: 1.48rem;
            line-height: 1.05;
            font-weight: 800;
            margin-bottom: 0.22rem;
        }
        .jj-alert-badge-caption {
            font-size: 0.88rem;
            line-height: 1.4;
            opacity: 0.94;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_alert_badge(
    level: str,
    label: str = "Nivel actual",
    caption: str = "",
) -> None:
    _ensure_styles()
    normalized_level = str(level or "BAJO").upper()
    style = _LEVEL_STYLES.get(normalized_level, _LEVEL_STYLES["BAJO"])
    st.markdown(
        f"""
        <div class="jj-alert-badge"
             style="background:{style['bg']}; color:{style['text']}; border-color:{style['border']};">
            <div class="jj-alert-badge-label">{label}</div>
            <div class="jj-alert-badge-value">{normalized_level}</div>
            <div class="jj-alert-badge-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
