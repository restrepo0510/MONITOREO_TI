import pandas as pd
import sqlite3
import os
import streamlit as st
from src.config import (
    DASHBOARD_SOURCE_OF_TRUTH_PATH,
    DATA_MODEL_OUTPUT_SQLITE_PATH,
)

# ----------------------------------------------------------
# Contrato de datos para dashboard:
# 1) Fuente oficial: DASHBOARD_SOURCE_OF_TRUTH_PATH (completa)
# 2) Fallback legado: SQLite de model_output (resumen)
# ----------------------------------------------------------
PARQUET_PATH = DASHBOARD_SOURCE_OF_TRUTH_PATH
SQLITE_PATH = DATA_MODEL_OUTPUT_SQLITE_PATH

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
    return df
