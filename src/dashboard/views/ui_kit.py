from __future__ import annotations

import streamlit as st


def inject_operational_ui() -> None:
    """
    Base visual compartida para TODAS las vistas.
    Replica el estilo principal de "Vista Tren (Operativa)" para mantener consistencia.
    """
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 1.1rem;
            padding-bottom: 2.2rem;
        }
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #FFFFFF 0%, #F7FAFF 100%);
            border: 1px solid rgba(35, 75, 141, 0.10);
            border-radius: 14px;
            padding: 0.4rem 0.65rem;
            box-shadow: 0 10px 22px rgba(15, 30, 60, 0.06);
        }
        div[data-testid="stMetricLabel"] {
            color: #234B8D;
            font-weight: 700;
        }
        .mt-main-title {
            color: #234B8D;
            font-size: 2.12rem;
            font-weight: 860;
            line-height: 1.1;
            margin: 0;
            letter-spacing: 0.2px;
        }
        .mt-main-subtitle {
            color: #4E5C76;
            font-size: 0.95rem;
            line-height: 1.55;
            margin-top: 0.35rem;
            margin-bottom: 0.9rem;
            max-width: 980px;
        }
        .mt-section-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #234B8D;
            margin-top: 1.35rem;
            margin-bottom: 0.2rem;
        }
        .mt-section-subtitle {
            color: #4E5C76;
            font-size: 0.92rem;
            line-height: 1.45;
            margin-bottom: 0.65rem;
        }
        .mt-panel {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
            border-radius: 22px;
            padding: 1rem;
            border: 1px solid rgba(35, 75, 141, 0.10);
            box-shadow: 0 18px 34px rgba(15, 30, 60, 0.09);
        }
        .mt-level {
            width: 100%;
            border-radius: 12px;
            padding: 0.8rem 1rem;
            margin: 0.25rem 0 0.5rem 0;
            border: 1px solid transparent;
        }
        .mt-level-title {
            font-size: 1.05rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 0.12rem;
        }
        .mt-level-copy {
            font-size: 0.92rem;
            line-height: 1.35;
            opacity: 0.95;
        }
        .mt-level-high {
            background: #D32F2F;
            color: #F4F4F9;
            border-color: #B71C1C;
        }
        .mt-level-medium {
            background: #F6E8AE;
            color: #3C3A28;
            border-color: #D5B700;
        }
        .mt-level-low {
            background: #E4F5ED;
            color: #1D4B36;
            border-color: #9AD2B8;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
