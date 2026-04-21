import os
import sys

import streamlit as st

# Agrega la raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.dashboard.theme_manager import inject_theme_css
from src.dashboard.cache_manager import invalidate_all_caches
from src.dashboard.data_loader import load_scores
from src.dashboard.views import (
    alerts,
    home_legacy_operational,
    home_general,
    manual_test,
    model_view,
    premium_full_latest,
    train_details,
)


# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================

st.set_page_config(
    page_title="MonitoreoTI - Dashboard de Riesgo",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inyectar estilos UNA SOLA VEZ (NO en cada render)
inject_theme_css()


# ============================================================================
# NAVEGACIÓN
# ============================================================================

NAV_SECTIONS = {
    "primary": {
        "title": "VISTAS PRINCIPALES",
        "question": "Operacion diaria",
        "items": [
            ("system_home", "Home General"),
            ("train_operational", "Vista Tren (Operativa)"),
            ("alerts", "Alertas"),
            ("sandbox", "Prueba Manual"),
        ],
    },
    "secondary": {
        "title": "VISTAS SECUNDARIAS",
        "question": "Decision y diagnostico",
        "items": [
            ("premium_full_latest", "Resumen Ejecutivo"),
            ("detail", "Detalle de Señales"),
            ("model_view", "Modelo Predictivo"),
        ],
    },
}


def _set_nav(view_key: str) -> None:
    st.session_state["nav_view"] = view_key

with st.sidebar:
    st.markdown("## MonitoreoTI")
    st.markdown("---")

    if "nav_view" not in st.session_state:
        st.session_state["nav_view"] = "system_home"

    for section in NAV_SECTIONS.values():
        st.markdown(f"**{section['title']}**")
        st.caption(section["question"])
        for view_key_option, label in section["items"]:
            is_selected = st.session_state.get("nav_view") == view_key_option
            button_label = f"● {label}" if is_selected else f"○ {label}"
            if st.button(button_label, use_container_width=True, key=f"nav_{view_key_option}"):
                _set_nav(view_key_option)
                st.rerun()
        st.markdown("")

    view_key = st.session_state.get("nav_view", "system_home")

    st.markdown("---")
    
    # Control de sandbox
    if st.session_state.get("sandbox_active", False):
        st.warning("Sandbox activo", icon="⚠️")
        if st.button("Desactivar sandbox", use_container_width=True):
            st.session_state["sandbox_active"] = False
            st.rerun()
        st.markdown("---")

    # Controles de caché y datos
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refrescar", use_container_width=True, help="Limpia cache y recarga datos"):
            invalidate_all_caches()
            st.rerun()
    
    with col2:
        if st.button("Info", use_container_width=True, help="Informacion del sistema"):
            st.info("Sistema global, operación por tren, análisis causal y simulación técnica.")


# ============================================================================
# CARGA DE DATOS
# ============================================================================

try:
    real_df = load_scores()
    
    if st.session_state.get("sandbox_active", False) and "sandbox_df" in st.session_state:
        df = st.session_state["sandbox_df"].copy()
    else:
        df = real_df
    
    # ========================================================================
    # RENDERIZADO DE VISTAS
    # ========================================================================
    
    if view_key == "system_home":
        home_general.render(df)
    elif view_key == "train_operational":
        home_legacy_operational.render(df)
    elif view_key == "premium_full_latest":
        premium_full_latest.render(df)
    elif view_key == "detail":
        train_details.render(df)
    elif view_key == "alerts":
        alerts.render(df)
    elif view_key == "sandbox":
        manual_test.render(real_df)
    elif view_key == "model_view":
        model_view.render(df)

except Exception as e:
    st.error(f"❌ Error cargando dashboard: {str(e)}")
    st.info("Intenta refrescar los datos o revisar la conexión al pipeline")

