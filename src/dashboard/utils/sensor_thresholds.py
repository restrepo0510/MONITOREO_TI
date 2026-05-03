import json
import os
from datetime import datetime

import pandas as pd


SENSOR_KEYS = [
    "TP3_mean",
    "H1_mean",
    "DV_pressure_mean",
    "Motor_Current_mean",
    "MPG_last",
    "Oil_Temperature_mean",
    "TOWERS_last",
]


def _safe_quantile(series, q, fallback=0.0):
    if series is None or len(series) == 0:
        return float(fallback)
    return float(series.quantile(q))


def _series(df, col):
    if col not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").dropna()


def calibrate_sensor_thresholds(df):
    """
    Calibra umbrales fijos por sensor usando histórico sano.

    Regla de histórico sano:
    - Si existe columna risk_level, usa sólo filas BAJO.
    - Si no existe o queda vacío, usa todo el dataset.
    """
    if "risk_level" in df.columns:
        healthy_df = df[df["risk_level"] == "BAJO"].copy()
        healthy_source = "risk_level == BAJO"
    else:
        healthy_df = df.copy()
        healthy_source = "all_rows_no_risk_level"

    if healthy_df.empty:
        healthy_df = df.copy()
        healthy_source = "fallback_all_rows_empty_healthy"

    thresholds = {
        "version": 1,
        "created_at": datetime.now().isoformat(),
        "healthy_filter": healthy_source,
        "rows_total": int(len(df)),
        "rows_healthy_used": int(len(healthy_df)),
        "sensors": {},
    }

    tp3 = _series(healthy_df, "TP3_mean")
    h1 = _series(healthy_df, "H1_mean")
    dv = _series(healthy_df, "DV_pressure_mean")
    motor = _series(healthy_df, "Motor_Current_mean")
    mpg = _series(healthy_df, "MPG_last")
    oil = _series(healthy_df, "Oil_Temperature_mean")
    towers = _series(healthy_df, "TOWERS_last")

    thresholds["sensors"]["TP3_mean"] = {
        "min_expected": _safe_quantile(tp3, 0.10),
        "warn_low": _safe_quantile(tp3, 0.05),
        "warn_high": _safe_quantile(tp3, 0.95),
        "crit_low": _safe_quantile(tp3, 0.01),
        "crit_high": _safe_quantile(tp3, 0.99),
    }
    thresholds["sensors"]["H1_mean"] = {
        "min_expected": _safe_quantile(h1, 0.10),
        "warn_low": _safe_quantile(h1, 0.05),
        "warn_high": _safe_quantile(h1, 0.95),
        "crit_low": _safe_quantile(h1, 0.01),
        "crit_high": _safe_quantile(h1, 0.99),
    }

    if len(dv) > 0:
        dv_baseline = dv.rolling(12, min_periods=1).median()
        dv_residual = (dv - dv_baseline).abs()
        spike_threshold = _safe_quantile(dv_residual.dropna(), 0.99)
    else:
        spike_threshold = 0.0
    thresholds["sensors"]["DV_pressure_mean"] = {
        "warn_low": _safe_quantile(dv, 0.05),
        "warn_high": _safe_quantile(dv, 0.95),
        "crit_low": _safe_quantile(dv, 0.01),
        "crit_high": _safe_quantile(dv, 0.99),
        "spike_threshold": spike_threshold,
    }

    thresholds["sensors"]["Motor_Current_mean"] = {
        "on_threshold": _safe_quantile(motor, 0.60),
        "warn_high": _safe_quantile(motor, 0.95),
        "crit_high": _safe_quantile(motor, 0.99),
    }

    thresholds["sensors"]["MPG_last"] = {
        "on_threshold": 0.5,
        "min_active_pct_warn": _safe_quantile((mpg > 0.5).astype(float), 0.10, fallback=0.0) * 100,
    }

    thresholds["sensors"]["Oil_Temperature_mean"] = {
        "normal_low": _safe_quantile(oil, 0.10),
        "normal_high": _safe_quantile(oil, 0.90),
        "warn_low": _safe_quantile(oil, 0.05),
        "warn_high": _safe_quantile(oil, 0.95),
        "crit_low": _safe_quantile(oil, 0.01),
        "crit_high": _safe_quantile(oil, 0.99),
    }

    thresholds["sensors"]["TOWERS_last"] = {
        "on_threshold": 0.5,
    }

    return thresholds


def save_sensor_thresholds(thresholds, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=4, ensure_ascii=False)


def load_sensor_thresholds(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
