"""
Autoencoder-based anomaly detector for train sensor data.

Loads the trained Keras model once (cached) and returns per-row
reconstruction error normalized to [0, 1].
"""

from __future__ import annotations

import json
import pickle
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[2] / "model"

# Feature order expected by the model (original dataset column names)
MODEL_FEATURES: list[str] = [
    "TP2", "TP3", "H1", "DV_pressure", "Reservoirs",
    "Oil_temperature", "Motor_current", "COMP", "DV_eletric",
    "Towers", "MPG", "LPS", "Oil_level", "Caudal_impulses",
]

# After train_map.py's RENAME_MAP some columns get new names.
# This maps them back to what the model expects.
_POST_RENAME_TO_MODEL: dict[str, str] = {
    "Oil_Temperature": "Oil_temperature",
    "Motor_Current":   "Motor_current",
    "DV_electric":     "DV_eletric",
    "TOWERS":          "Towers",
    "Oil_Level":       "Oil_level",
}


@lru_cache(maxsize=1)
def _load_artifacts():
    try:
        from tensorflow import keras  # noqa: F401 – lazy import so TF is optional
    except ImportError as exc:
        raise ImportError(
            "TensorFlow is required for model inference. "
            "Install it with: pip install tensorflow"
        ) from exc

    try:
        import joblib
        _pkl = joblib.load
    except ImportError:
        def _pkl(path):
            with open(path, "rb") as f:
                return pickle.load(f)

    model = keras.models.load_model(str(MODEL_DIR / "autoencoder_dense (1).keras"))
    scaler = _pkl(str(MODEL_DIR / "scaler (1).pkl"))
    threshold = float(np.load(str(MODEL_DIR / "threshold (1).npy")))

    with open(MODEL_DIR / "feature_names (1).json", encoding="utf-8") as fh:
        features: list[str] = json.load(fh)

    return model, scaler, threshold, features


def predict(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return df with three new columns:
    - model_score    : reconstruction error normalised to [0, 1]
    - model_anomaly  : True when raw error >= stored threshold
    - _model_raw_err : raw MSE (kept for debugging)

    If TensorFlow is unavailable or any artifact is missing, the columns
    are added with NaN / False so callers don't need to special-case.
    """
    out = df.copy()
    out["model_score"] = np.nan
    out["model_anomaly"] = False
    out["_model_raw_err"] = np.nan

    try:
        model, scaler, threshold, features = _load_artifacts()
    except Exception:
        return out

    # Map post-rename column names → model feature names
    col_lookup: dict[str, str] = {}
    for col in df.columns:
        model_name = _POST_RENAME_TO_MODEL.get(col, col)
        if model_name in features:
            col_lookup[model_name] = col

    # Build input matrix in model feature order; missing features filled with 0
    X = np.zeros((len(df), len(features)), dtype=np.float32)
    for i, fname in enumerate(features):
        if fname in col_lookup:
            X[:, i] = (
                pd.to_numeric(df[col_lookup[fname]], errors="coerce")
                .fillna(0.0)
                .values
            )

    X_scaled = scaler.transform(X)
    X_rec = model.predict(X_scaled, verbose=0)
    errors = np.mean(np.square(X_scaled - X_rec), axis=1)

    # Normalise so that threshold maps to ~0.5; clip to [0, 1]
    out["model_score"] = np.clip(errors / (threshold * 2.0), 0.0, 1.0)
    out["model_anomaly"] = errors >= threshold
    out["_model_raw_err"] = errors

    return out
