import pandas as pd
import sqlite3
import os
import streamlit as st

PARQUET_PATH = "data/output/model_output.parquet"
SQLITE_PATH  = "data/output/model_output.db"

@st.cache_data(ttl=60)
def load_scores() -> pd.DataFrame:
    if os.path.exists(PARQUET_PATH):
        df = pd.read_parquet(PARQUET_PATH)
    elif os.path.exists(SQLITE_PATH):
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
                        bins=[0, 0.3, 0.6, 1.0],
                        labels=["BAJO", "MEDIO", "ALTO"])
        df = pd.DataFrame({
            "timestamp": timestamps,
            "risk_score": scores,
            "risk_level": levels.astype(str)
        })
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df