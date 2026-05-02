"""
Placeholder module.
Este archivo se completará en el desarrollo del dashboard.
"""

import streamlit as st


_LEVEL_STYLES = {
    "ALTO": {
        "bg": "linear-gradient(135deg, #8E1D2B 0%, #C52F3D 100%)",
        "text": "#F4F7F9",
        "border": "rgba(142, 29, 43, 0.35)",
    },
    "MEDIO": {
        "bg": "linear-gradient(135deg, #FFE600 0%, #FFD000 100%)",
        "text": "#223047",
        "border": "rgba(126, 105, 0, 0.30)",
    },
    "BAJO": {
        "bg": "linear-gradient(135deg, #234B8D 0%, #173A73 100%)",
        "text": "#F4F7F9",
        "border": "rgba(35, 75, 141, 0.34)",
    },
}


def _ensure_styles():
    st.markdown(
        """
        <style>
        .jj-alert-badge {
            border-radius: 24px;
            padding: 1rem 1.05rem;
            box-shadow: 0 14px 30px rgba(16, 31, 56, 0.10);
            border: 1px solid transparent;
        }
        .jj-alert-badge-label {
            font-size: 0.72rem;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            opacity: 0.85;
            margin-bottom: 0.24rem;
            font-weight: 760;
        }
        .jj-alert-badge-value {
            font-size: 1.65rem;
            line-height: 1.05;
            font-weight: 820;
            margin-bottom: 0.22rem;
        }
        .jj-alert-badge-caption {
            font-size: 0.82rem;
            line-height: 1.45;
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
