import pandas as pd
import sqlite3
import os
import streamlit as st
from src.config import (
    DASHBOARD_SOURCE_OF_TRUTH_PATH,
    DATA_MODEL_OUTPUT_SQLITE_PATH,
    AUTOENCODER_SCORES_PATH,
)

# ----------------------------------------------------------
# Contrato de datos para dashboard:
# 1) Fuente oficial: DASHBOARD_SOURCE_OF_TRUTH_PATH (completa)
# 2) Fallback legado: SQLite de model_output (resumen)
# ----------------------------------------------------------
PARQUET_PATH = DASHBOARD_SOURCE_OF_TRUTH_PATH
SQLITE_PATH = DATA_MODEL_OUTPUT_SQLITE_PATH

CANONICAL_SENSOR_ALIASES = {
    "TP2": "TP2_mean",
    "TP3": "TP3_mean",
    "H1": "H1_mean",
    "DV_pressure": "DV_pressure_mean",
    "Reservoirs": "Reservoirs_mean",
    "Oil_Temperature": "Oil_Temperature_mean",
    "Motor_Current": "Motor_Current_mean",
    "MPG": "MPG_last",
    "TOWERS": "TOWERS_last",
}


def _apply_dashboard_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza nombres de columnas para que el front y el motor de alertas
    puedan consumir tanto datos crudos como columnas agregadas.
    """
    if df is None or df.empty:
        return df

    normalized = df.copy()

    for raw_name, canonical_name in CANONICAL_SENSOR_ALIASES.items():
        if raw_name in normalized.columns and canonical_name not in normalized.columns:
            normalized[canonical_name] = pd.to_numeric(
                normalized[raw_name], errors="coerce"
            )

    if "risk_score" in normalized.columns:
        normalized["risk_score"] = pd.to_numeric(
            normalized["risk_score"], errors="coerce"
        ).fillna(0.0)

    if "risk_level" in normalized.columns:
        normalized["risk_level"] = (
            normalized["risk_level"].astype(str).str.upper().fillna("BAJO")
        )

    return normalized

@st.cache_data(ttl=60)
def load_scores() -> pd.DataFrame:
    if os.path.exists(PARQUET_PATH):
        df = pd.read_parquet(PARQUET_PATH)
        # Se imprime para diagnóstico rápido al ejecutar localmente.
        print(f"[data_loader] Source of truth: {PARQUET_PATH}")
        print(df.columns)
    elif os.path.exists(SQLITE_PATH):
        # Fallback sólo para continuidad operativa.
        # Esta fuente puede no incluir todas las columnas de sensores.
        print(f"[data_loader] Legacy fallback source: {SQLITE_PATH}")
        conn = sqlite3.connect(SQLITE_PATH)
        df = pd.read_sql("SELECT * FROM risk_output ORDER BY timestamp", conn)
        conn.close()
    else:
        # datos demo para desarrollo sin pipeline corriendo
        import numpy as np
        np.random.seed(42)
        n = 500
        timestamps = pd.date_range("2024-01-01", periods=n, freq="10min")
        scores = np.clip(np.random.beta(2, 5, n), 0, 1)
        levels = pd.cut(scores,
                        bins=[0, 0.4, 0.7, 1.0],
                        labels=["BAJO", "MEDIO", "ALTO"])
        df = pd.DataFrame({
            "timestamp": timestamps,
            "risk_score": scores,
            "risk_level": levels.astype(str)
        })
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = _apply_dashboard_aliases(df)
    df = _merge_autoencoder_scores(df)
    return df


@st.cache_data(ttl=60)
def _load_ae_scores() -> pd.DataFrame | None:
    if not os.path.exists(AUTOENCODER_SCORES_PATH):
        return None
    ae = pd.read_parquet(AUTOENCODER_SCORES_PATH)
    ae["timestamp"] = pd.to_datetime(ae["timestamp"])
    return ae


def _merge_autoencoder_scores(df: pd.DataFrame) -> pd.DataFrame:
    ae = _load_ae_scores()
    if ae is None or ae.empty:
        return df
    # Merge por timestamp más cercano (tolerancia 5 min) para cubrir leves desajustes
    df_sorted = df.sort_values("timestamp")
    ae_sorted = ae.sort_values("timestamp")
    merged = pd.merge_asof(
        df_sorted,
        ae_sorted,
        on="timestamp",
        tolerance=pd.Timedelta("5min"),
        direction="nearest",
        suffixes=("", "_ae"),
    )
    return merged
