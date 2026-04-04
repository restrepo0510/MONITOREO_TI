"""
Componente de operatividad: Acciones recomendadas.

Este componente solo renderiza.
La logica de decision viene del backend en recommendation_engine.
"""

import streamlit as st

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
    active_sensors = rec.get("active_sensors", [])

    if level == "ALTO":
        st.error("PROTOCOLO ACTIVO: ALERTA ALTA")
    elif level == "MEDIO":
        st.warning("PROTOCOLO ACTIVO: ALERTA MEDIA")
    else:
        st.info("PROTOCOLO ACTIVO: OPERACION NORMAL")

    if actions:
        action_lines = "\n".join([_render_action_line(a) for a in actions])
        st.markdown(action_lines)
    else:
        st.markdown("- Sin acciones registradas en la politica actual.")
