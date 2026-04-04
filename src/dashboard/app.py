import os
import sys
from pathlib import Path

import streamlit as st

# agrega la raiz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.dashboard.data_loader import load_scores
from src.dashboard.views import alerts, home, manual_test, train_details


def _load_global_css():
    css_path = Path(__file__).resolve().parent / "assets" / "styles" / "main.css"
    if not css_path.exists():
        return
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


st.set_page_config(
    page_title="MonitoreoTI - Dashboard de Riesgo",
    page_icon="??",
    layout="wide",
    initial_sidebar_state="expanded",
)

_load_global_css()

NAV_OPTIONS = {
    "home": "?? Resumen General",
    "detail": "?? Detalle de Senales",
    "alerts": "?? Alertas",
    "sandbox": "?? Prueba Manual",
}

with st.sidebar:
    st.markdown("## ?? MonitoreoTI")
    st.markdown("---")

    view_key = st.radio(
        "Navegacion",
        options=list(NAV_OPTIONS.keys()),
        format_func=lambda k: NAV_OPTIONS[k],
        index=0,
    )

    st.markdown("---")
    if st.session_state.get("sandbox_active", False):
        st.warning("Sandbox activo")
        if st.button("Desactivar sandbox", use_container_width=True):
            st.session_state["sandbox_active"] = False
            st.rerun()
        st.markdown("---")

    if st.button("?? Refrescar datos"):
        st.cache_data.clear()
        st.rerun()


real_df = load_scores()
if st.session_state.get("sandbox_active", False) and "sandbox_df" in st.session_state:
    df = st.session_state["sandbox_df"].copy()
else:
    df = real_df


if view_key == "home":
    home.render(df)
elif view_key == "detail":
    train_details.render(df)
elif view_key == "alerts":
    alerts.render(df)
elif view_key == "sandbox":
    manual_test.render(real_df)
