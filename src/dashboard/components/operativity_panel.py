"""
Componente de operatividad: Acciones recomendadas.

Este componente solo renderiza.
La logica de decision viene del backend en recommendation_engine.
"""

import streamlit as st

from src.dashboard.components.icons import icon_chip
from src.dashboard.components.ui_kit import action_card
from src.dashboard.utils.recommendation_engine import get_latest_recommendations


def _render_action_line(action):
    text = action.get("text", "Accion sin descripcion")
    return f"- {text}"


def render_operativity_panel(df):
    """
    Muestra acciones recomendadas para la ultima ventana evaluada.
    """
    rec = get_latest_recommendations(df)
    level = rec.get("level", "BAJO")
    actions = rec.get("combined_actions", [])
    if level == "ALTO":
        protocol_title = "PROTOCOLO ACTIVO: ALERTA ALTA"
        tone_color = "#e74c3c"
    elif level == "MEDIO":
        protocol_title = "PROTOCOLO ACTIVO: ALERTA MEDIA"
        tone_color = "#f39c12"
    else:
        protocol_title = "PROTOCOLO ACTIVO: OPERACION NORMAL"
        tone_color = "#2ecc71"

    st.markdown(
        f"""
        <div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.06);border-radius:20px;padding:0.9rem 0.95rem;box-shadow:0 8px 24px rgba(16,24,40,0.06);margin-bottom:0.7rem;">
          <div style="display:flex;align-items:center;gap:0.6rem;">
            {icon_chip("settings", tone_color, 16, chip_size=34)}
            <div style="font-size:0.94rem;font-weight:760;color:#1f2b45;">{protocol_title}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if actions:
        for idx, action in enumerate(actions, start=1):
            action_card(f"Accion {idx}", action.get("text", "Accion sin descripcion"))
    else:
        action_card("Accion", "Sin acciones registradas en la politica actual.")
