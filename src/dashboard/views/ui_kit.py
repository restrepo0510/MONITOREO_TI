from __future__ import annotations

import streamlit as st


def inject_operational_ui() -> None:
    st.markdown(
        """
        <style>
        .main .block-container { padding-top:1.1rem; padding-bottom:2.2rem; }
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg,#FFFFFF 0%,#F7FAFF 100%);
            border: 1px solid rgba(35,75,141,0.10);
            border-radius: 14px;
            padding: 0.4rem 0.65rem;
            box-shadow: 0 10px 22px rgba(15,30,60,0.06);
        }
        div[data-testid="stMetricLabel"] { color:#234B8D; font-weight:700; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_view_header(title: str, subtitle: str) -> None:
    st.html(f"""
        <div style="margin-bottom:0.2rem;">
            <div style="color:#234B8D;font-size:2.12rem;font-weight:860;
                        line-height:1.1;letter-spacing:0.2px;font-family:inherit;">
                {title}
            </div>
            <div style="color:#4E5C76;font-size:0.95rem;line-height:1.55;
                        margin-top:0.35rem;margin-bottom:0.4rem;max-width:980px;font-family:inherit;">
                {subtitle}
            </div>
        </div>
    """)


def render_section_header(title: str, subtitle: str) -> None:
    st.html(f"""
        <div style="margin-top:1.1rem;margin-bottom:0.1rem;font-family:inherit;">
            <div style="font-size:1.3rem;font-weight:700;color:#234B8D;margin-bottom:0.18rem;">
                {title}
            </div>
            <div style="color:#4E5C76;font-size:0.92rem;line-height:1.45;margin-bottom:0.5rem;">
                {subtitle}
            </div>
        </div>
    """)


def render_level_badge(level: str, score: float | None = None, detail: str | None = None) -> None:
    normalized = str(level).upper()
    if normalized == "ALTO":
        bg, fg, border = "#D32F2F", "#F4F4F9", "#B71C1C"
        label = "Estado actual: Riesgo ALTO"
    elif normalized == "MEDIO":
        bg, fg, border = "#F6E8AE", "#3C3A28", "#D5B700"
        label = "Estado actual: Riesgo MEDIO"
    else:
        bg, fg, border = "#E4F5ED", "#1D4B36", "#9AD2B8"
        label = "Estado actual: Riesgo BAJO"

    score_text = f"Score de riesgo: {score:.3f}" if score is not None else ""
    extra = f" {detail}" if detail else ""
    copy = f"{score_text}{extra}".strip() or "Sin detalle adicional."

    st.html(f"""
        <div style="
            background:{bg};color:{fg};border:1px solid {border};
            border-radius:12px;padding:0.8rem 1rem;margin:0.25rem 0 0.5rem 0;
            font-family:inherit;
        ">
            <div style="font-size:1.05rem;font-weight:800;line-height:1.1;margin-bottom:0.12rem;">
                {label}
            </div>
            <div style="font-size:0.92rem;line-height:1.35;opacity:0.95;">
                {copy}
            </div>
        </div>
    """)
