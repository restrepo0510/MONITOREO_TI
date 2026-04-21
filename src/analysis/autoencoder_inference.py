"""
Módulo de inferencia del autoencoder de detección de anomalías.

Responsabilidades:
- Cargar el modelo Keras entrenado desde Models/
- Recalibrar el StandardScaler desde los datos históricos (base.parquet)
- Ejecutar inferencia sobre los datos crudos por lotes
- Agregar resultados a ventanas de 5 minutos para alinear con el dashboard
- Guardar autoencoder_scores.parquet con métricas por ventana
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

os.environ.setdefault("KERAS_BACKEND", "torch")
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

# Mapa de columnas base.parquet → nombres esperados por el modelo
_COL_MAP: dict[str, str] = {
    "TP2": "TP2",
    "TP3": "TP3",
    "H1": "H1",
    "DV_pressure": "DV_pressure",
    "Reservoirs": "Reservoirs",
    "Oil_Temperature": "Oil_temperature",
    "Motor_Current": "Motor_current",
    "COMP": "COMP",
    "DV_electric": "DV_eletric",
    "TOWERS": "Towers",
    "MPG": "MPG",
    "LPS": "LPS",
    "Oil_Level": "Oil_level",
    "Caudal_impulses": "Caudal_impulses",
}

MODEL_DIR = "Models"
FEATURE_NAMES_PATH = os.path.join(MODEL_DIR, "feature_names.json")
MODEL_PATH = os.path.join(MODEL_DIR, "autoencoder_dense.keras")
THRESHOLD_PATH = os.path.join(MODEL_DIR, "threshold.npy")

BASE_PATH = "data/processed/base.parquet"
OUTPUT_PATH = "data/processed/autoencoder_scores.parquet"

BATCH_SIZE = 32768
WINDOW = "5min"


def _load_feature_names() -> list[str]:
    with open(FEATURE_NAMES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _prepare_features(df: pd.DataFrame, feature_names: list[str]) -> np.ndarray:
    renamed = df.rename(columns=_COL_MAP)
    missing = [c for c in feature_names if c not in renamed.columns]
    if missing:
        raise ValueError(f"Columnas faltantes en datos crudos: {missing}")
    return renamed[feature_names].astype("float32").values


def _fit_scaler(X: np.ndarray) -> StandardScaler:
    scaler = StandardScaler()
    sample_size = min(200_000, len(X))
    idx = np.random.default_rng(42).choice(len(X), sample_size, replace=False)
    scaler.fit(X[idx])
    return scaler


def _infer_batched(model, X_scaled: np.ndarray, batch_size: int = BATCH_SIZE) -> np.ndarray:
    preds = []
    n = len(X_scaled)
    for start in range(0, n, batch_size):
        batch = X_scaled[start : start + batch_size]
        pred = model.predict(batch, verbose=0)
        preds.append(pred)
    return np.vstack(preds)


def run_autoencoder_inference(
    base_path: str = BASE_PATH,
    output_path: str = OUTPUT_PATH,
) -> pd.DataFrame | None:
    print("Cargando modelo autoencoder...")
    import torch
    torch._dynamo.disable()
    import keras  # importar después de setear KERAS_BACKEND

    model = keras.models.load_model(MODEL_PATH)
    threshold = float(np.load(THRESHOLD_PATH))
    feature_names = _load_feature_names()

    print(f"Cargando datos base desde {base_path}...")
    base_df = pd.read_parquet(base_path)
    base_df["timestamp"] = pd.to_datetime(base_df["timestamp"])

    print("Preparando features...")
    X_raw = _prepare_features(base_df, feature_names)

    print("Calibrando StandardScaler desde datos históricos...")
    scaler = _fit_scaler(X_raw)
    X_scaled = scaler.transform(X_raw).astype("float32")

    print(f"Corriendo inferencia sobre {len(X_scaled):,} muestras...")
    X_reconstructed = _infer_batched(model, X_scaled)

    # Error de reconstrucción total (MSE por fila)
    errors = np.mean((X_scaled - X_reconstructed) ** 2, axis=1)

    # Recalibrar umbral: el umbral original fue calibrado con el scaler de entrenamiento.
    # Al refitear el scaler desde los datos históricos, el espacio escalado cambia.
    # Usamos el percentil 95 de la distribución de errores como umbral operativo.
    recalibrated_threshold = float(np.percentile(errors, 95))
    print(f"Umbral recalibrado (p95): {recalibrated_threshold:.8f} (original: {threshold:.8f})")
    threshold = recalibrated_threshold

    # Error por sensor (permite diagnóstico de causa)
    per_sensor_errors = (X_scaled - X_reconstructed) ** 2

    result_df = pd.DataFrame({"timestamp": base_df["timestamp"].values})
    result_df["ae_reconstruction_error"] = errors
    result_df["ae_anomaly_raw"] = errors > threshold

    for i, name in enumerate(feature_names):
        result_df[f"ae_err_{name}"] = per_sensor_errors[:, i]

    # Agregar a ventanas de 5 minutos para alinear con risk_scores.parquet
    print(f"Agregando a ventanas de {WINDOW}...")
    result_df = result_df.set_index("timestamp")

    agg_dict: dict[str, str | list] = {
        "ae_reconstruction_error": "mean",
        "ae_anomaly_raw": "any",
    }
    for name in feature_names:
        agg_dict[f"ae_err_{name}"] = "mean"

    windowed = result_df.resample(WINDOW).agg(agg_dict)
    windowed = windowed.reset_index()
    windowed.rename(columns={"ae_anomaly_raw": "ae_anomaly"}, inplace=True)
    windowed["ae_anomaly"] = windowed["ae_anomaly"].astype(bool)

    # Sensor con mayor error por ventana (skipna para ventanas con NaN)
    sensor_err_cols = [f"ae_err_{n}" for n in feature_names]
    valid_mask = windowed[sensor_err_cols].notna().any(axis=1)
    windowed["ae_top_sensor"] = ""
    if valid_mask.any():
        windowed.loc[valid_mask, "ae_top_sensor"] = (
            windowed.loc[valid_mask, sensor_err_cols]
            .idxmax(axis=1, skipna=True)
            .str.replace("ae_err_", "", regex=False)
        )

    # Score normalizado [0-1] para display en dashboard
    err_max = float(windowed["ae_reconstruction_error"].quantile(0.999))
    err_max = err_max if err_max > 0 else 1.0
    windowed["ae_score"] = (windowed["ae_reconstruction_error"] / err_max).clip(0.0, 1.0)

    windowed["ae_threshold"] = threshold

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    windowed.to_parquet(output_path, index=False)

    anomaly_count = int(windowed["ae_anomaly"].sum())
    print(f"Inferencia completada. Ventanas: {len(windowed):,} | Anomalías detectadas: {anomaly_count:,}")
    print(f"Guardado en: {output_path}")

    return windowed


if __name__ == "__main__":
    run_autoencoder_inference()
