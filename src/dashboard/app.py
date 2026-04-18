import os
import sys
from pathlib import Path

import streamlit as st

# Agrega la raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.dashboard.theme_manager import inject_theme_css
from src.dashboard.cache_manager import invalidate_all_caches
from src.dashboard.data_loader import load_scores
from src.dashboard.views import alerts, home, manual_test, train_details


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

NAV_OPTIONS = {
    "home": "🏠 Resumen General",
    "detail": "📊 Detalle de Señales",
    "alerts": "🚨 Alertas",
    "sandbox": "🧪 Prueba Manual",
}

with st.sidebar:
    st.markdown("## ⚙️ MonitoreoTI")
    st.markdown("---")

    view_key = st.radio(
        "Navegación",
        options=list(NAV_OPTIONS.keys()),
        format_func=lambda k: NAV_OPTIONS[k],
        index=0,
    )

    st.markdown("---")
    
    # Control de sandbox
    if st.session_state.get("sandbox_active", False):
        st.warning("🧪 Sandbox activo", icon="⚠️")
        if st.button("Desactivar sandbox", use_container_width=True):
            st.session_state["sandbox_active"] = False
            st.rerun()
        st.markdown("---")

    # Controles de caché y datos
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refrescar", use_container_width=True, help="Limpia caché y recarga datos"):
            invalidate_all_caches()
            st.rerun()
    
    with col2:
        if st.button("📋 Info", use_container_width=True, help="Información del sistema"):
            st.info("Dashboard optimizado con caching inteligente y renderizado eficiente")


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
    
    if view_key == "home":
        home.render(df)
    elif view_key == "detail":
        train_details.render(df)
    elif view_key == "alerts":
        alerts.render(df)
    elif view_key == "sandbox":
        manual_test.render(real_df)

except Exception as e:
    st.error(f"❌ Error cargando dashboard: {str(e)}")
    st.info("Intenta refrescar los datos o revisar la conexión al pipeline")

