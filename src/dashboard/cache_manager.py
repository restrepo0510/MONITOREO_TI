"""
Cache Manager - Gestión centralizada de caché con optimizaciones profesionales.

Beneficios:
- TTL apropiados para cada tipo de dato
- Reutilización de resultados computacionales costosos
- Session state para evitar recálculos innecesarios
- Invalidación selectiva de caché
"""

import streamlit as st
from functools import wraps
import pandas as pd
from src.dashboard.data_loader import load_scores as _load_scores_raw


# ============================================================================
# CACHE DECORATORS CON TTL OPTIMIZADO
# ============================================================================

def cache_data_medium(ttl: int = 300):
    """Cache para datos que cambian cada 5 minutos."""
    return st.cache_data(ttl=ttl, show_spinner=False)


def cache_data_long(ttl: int = 900):
    """Cache para datos que cambian cada 15 minutos."""
    return st.cache_data(ttl=ttl, show_spinner=False)


def cache_resource_persistent():
    """Cache para recursos que no cambian en la sesión."""
    return st.cache_resource(show_spinner=False)


# ============================================================================
# FUNCIONES DE CARGA OPTIMIZADAS
# ============================================================================

@cache_data_medium(ttl=300)
def load_scores():
    """
    Carga datos de scores con caché de 5 minutos.
    Mejor que 60s porque los dados no cambian tan frecuentemente.
    """
    return _load_scores_raw()


@cache_resource_persistent()
def get_alert_engine():
    """
    Inicializa el engine de alertas una sola vez por sesión.
    Los umbrales se cargan una sola vez.
    """
    from src.dashboard.utils.alert_engine import resolve_alert_thresholds
    return resolve_alert_thresholds


# ============================================================================
# COMPUTACIONES CACHEADAS COSTOSAS
# ============================================================================

@cache_data_medium(ttl=300)
def compute_alerts(df_hash: str):
    """
    Cachea evaluación de alertas.
    Nota: Pasamos hash del df para invalidar caché cuando cambian datos.
    """
    from src.dashboard.utils.alert_engine import evaluate_alerts, resolve_alert_thresholds
    
    df = load_scores()
    thresholds, source = resolve_alert_thresholds(df)
    alert_df, meta = evaluate_alerts(df.tail(2400), thresholds=thresholds)
    return alert_df, meta, thresholds, source


@cache_data_medium(ttl=300)
def compute_predictions(df_hash: str):
    """Cachea predicciones (operación costosa)."""
    from src.dashboard.utils.alert_engine import (
        build_prediction_advisory,
        resolve_alert_thresholds,
    )
    
    df = load_scores()
    thresholds, _ = resolve_alert_thresholds(df)
    prediction = build_prediction_advisory(df.tail(2400), thresholds=thresholds)
    return prediction


@cache_data_medium(ttl=300)
def compute_latest_alert(df_hash: str):
    """Cachea última alerta (rápido pero se cachea igual para consistencia)."""
    from src.dashboard.utils.alert_engine import evaluate_latest_alert, resolve_alert_thresholds
    
    df = load_scores()
    thresholds, _ = resolve_alert_thresholds(df)
    latest_alert, _ = evaluate_latest_alert(df.tail(2400), thresholds=thresholds)
    return latest_alert


# ============================================================================
# SESSION STATE HELPERS
# ============================================================================

def get_dataframe_hash(df: pd.DataFrame) -> str:
    """
    Genera hash del dataframe para invalidar caché cuando cambian datos.
    Usamos timestamp más reciente como proxy.
    """
    if df is None or df.empty:
        return "empty"
    return str(df["timestamp"].iloc[-1])


def invalidate_all_caches():
    """Limpia todos los cachés cuando sea necesario."""
    st.cache_data.clear()
    st.cache_resource.clear()


# ============================================================================
# PIPELINE SIMPLIFICADO
# ============================================================================

def load_dashboard_data():
    """
    Punto de entrada único para toda la lógica de carga y cálculo.
    Retorna dict con todos los datos necesarios para el dashboard.
    """
    df = load_scores()
    df_hash = get_dataframe_hash(df)
    
    alert_df, meta, thresholds, threshold_source = compute_alerts(df_hash)
    prediction = compute_predictions(df_hash)
    latest_alert = compute_latest_alert(df_hash)
    
    return {
        "df": df.copy().sort_values("timestamp"),
        "alert_df": alert_df,
        "latest": df.iloc[-1],
        "latest_alert": latest_alert,
        "prediction": prediction,
        "thresholds": thresholds,
        "threshold_source": threshold_source,
        "meta": meta,
    }
