import os
import sys
import importlib

import streamlit as st

# Agrega la raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.dashboard.theme_manager import inject_theme_css
from src.dashboard.cache_manager import invalidate_all_caches
from src.dashboard.data_loader import load_scores
from src.dashboard.views.ui_kit import inject_custom_css
from src.dashboard.views import (
    alerts,
    home_legacy_operational,
    home_general,
    manual_test,
    train_details,
    train_map,
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
inject_custom_css()


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
            ("train_map", "Mapa de Tren"),
            ("alerts", "Alertas"),
            ("sandbox", "Prueba Manual"),
        ],
    },
    "secondary": {
        "title": "VISTAS SECUNDARIAS",
        "question": "Decision y diagnostico",
        "items": [
            ("detail", "Detalle de Señales"),
        ],
    },
}

TRAIN_ID_CANDIDATES = ["train_id", "train", "id_train", "apu_id", "engine_id"]


def _find_train_col(df):
    for c in TRAIN_ID_CANDIDATES:
        if c in df.columns:
            return c
    return None


def _force_single_train(df):
    """
    Modo temporal: forzar que TODAS las vistas trabajen con un solo tren.
    Usa selected_train_id si existe; si no, toma el primer tren disponible.
    """
    if df is None or df.empty:
        st.session_state["selected_train_id"] = "001"
        return df

    train_col = _find_train_col(df)
    if not train_col:
        work = df.copy()
        work["train_id"] = "001"
        st.session_state["selected_train_id"] = "001"
        return work

    work = df.copy()
    work[train_col] = work[train_col].astype(str)
    candidates = work[train_col].dropna().astype(str).unique().tolist()
    selected = str(st.session_state.get("selected_train_id", "")).strip()

    if not selected or selected not in candidates:
        selected = str(candidates[0]) if candidates else "001"
    st.session_state["selected_train_id"] = selected

    filtered = work[work[train_col] == selected].copy()
    if filtered.empty:
        return work
    return filtered


def _set_nav(view_key: str) -> None:
    st.session_state["nav_view"] = view_key

with st.sidebar:
    st.markdown(
        """
        <style>
        .sb-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }
        .sb-logo {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #0C3A90, #082A70);
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 20px;
            line-height: 1;
            box-shadow: 0 6px 16px rgba(0,0,0,0.15);
            flex-shrink: 0;
        }
        .sb-brand-title {
            margin: 0;
            font-size: 35px;
            font-weight: 700;
            color: #FFFFFF;
            line-height: 1.1;
        }
        .sb-brand-sub {
            margin: 2px 0 0 0;
            font-size: 12px;
            color: rgba(255,255,255,0.78);
            line-height: 1.35;
        }
        </style>
        <div class="sb-brand">
            <div class="sb-logo">M</div>
            <div>
                <p class="sb-brand-title">MonitoreoTI</p>
                <p class="sb-brand-sub">Sistema de Monitoreo de Infraestructura TI</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
    valid_views = {"system_home", "train_operational", "train_map", "alerts", "sandbox", "detail"}
    if view_key not in valid_views:
        st.session_state["nav_view"] = "system_home"
        st.rerun()

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

    # Modo temporal solicitado por usuario: operar TODO el dashboard sobre un solo tren.
    df = _force_single_train(df)
    real_df = _force_single_train(real_df)

    # ========================================================================
    # RENDERIZADO DE VISTAS
    # ========================================================================

    if view_key == "system_home":
        # Recarga explícita para reflejar cambios visuales en navegación interna.
        hg_module = importlib.import_module("src.dashboard.views.home_general")
        importlib.reload(hg_module)
        hg_module.render(df)
    elif view_key == "train_operational":
        # Recarga explícita para reflejar cambios visuales en navegación interna.
        train_module = importlib.import_module("src.dashboard.views.home_legacy_operational")
        importlib.reload(train_module)
        train_module.render(df)
    elif view_key == "train_map":
        train_map.render(df)
    elif view_key == "detail":
        train_details.render(df)
    elif view_key == "alerts":
        alerts.render(df)
    elif view_key == "sandbox":
        manual_test.render(real_df)

except Exception as e:
    st.error(f"❌ Error cargando dashboard: {str(e)}")
    st.info("Intenta refrescar los datos o revisar la conexión al pipeline")
