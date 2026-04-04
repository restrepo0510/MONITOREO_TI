import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

try:
    from src.config import (
        RISK_THRESHOLD_HIGH,
        RISK_THRESHOLD_MEDIUM,
        RISK_SCALER_PARAMS_PATH,
        RISK_SCALER_REUSE_PARAMS,
    )
except Exception:
    # Fallback para ejecución aislada del módulo.
    RISK_THRESHOLD_HIGH = 0.7
    RISK_THRESHOLD_MEDIUM = 0.4
    RISK_SCALER_PARAMS_PATH = "data/processed/risk_scaler_params.json"
    RISK_SCALER_REUSE_PARAMS = True


class RiskPredictor:
    """
    Módulo de detección de riesgo baseline del sistema de mantenimiento predictivo.

    Responsabilidades:
    - Leer el dataset con features procesadas.
    - Calcular un score de riesgo por ventana usando reglas estadísticas simples.
    - Asignar un nivel de riesgo: BAJO, MEDIO, ALTO.
    - Registrar cada ejecución en un log JSON estructurado.
    """

    def __init__(
        self,
        input_path="data/processed/features.parquet",
        output_path="data/processed/risk_scores.parquet",
        log_dir="logs",
        scaler_params_path=RISK_SCALER_PARAMS_PATH,
        reuse_scaler_params=RISK_SCALER_REUSE_PARAMS,
    ):
        # Ruta del dataset procesado generado por el módulo de ingesta
        self.input_path = input_path

        self.output_path = output_path

        self.log_dir = log_dir

        # Ruta donde se persisten parámetros del escalado de score.
        # Estos parámetros permiten estabilidad entre ejecuciones.
        self.scaler_params_path = scaler_params_path

        # Define si reutilizar parámetros persistidos.
        # True evita drift por recalcular min/max global en cada corrida.
        self.reuse_scaler_params = reuse_scaler_params

        # Sensores relevantes identificados en IN-3
        self.sensor_cols = [
            "TP2_mean",
            "TP3_mean",
            "H1_mean",
            "DV_pressure_mean",
            "Reservoirs_mean",
            "Oil_Temperature_mean",
            "Motor_Current_mean",
        ]

        # Umbrales para clasificar nivel de riesgo
        # Score >= 0.7 → ALTO, >= 0.4 → MEDIO, < 0.4 → BAJO
        self.threshold_high = RISK_THRESHOLD_HIGH
        self.threshold_medium = RISK_THRESHOLD_MEDIUM

    def _compute_raw_score(self, df, sensor_params):
        """
        Calcula raw_score (promedio de z-scores absolutos) usando
        parámetros explícitos por sensor (mean/std).
        """
        z_scores = pd.DataFrame(index=df.index)

        for col, stats in sensor_params.items():
            if col in df.columns:
                mean = float(stats["mean"])
                std = float(stats["std"])
                if std > 0:
                    z_scores[col] = (df[col] - mean).abs() / std
                else:
                    z_scores[col] = 0.0

        if z_scores.empty:
            return pd.Series(0.0, index=df.index)

        return z_scores.mean(axis=1)

    def _fit_scaler_params(self, df, available_sensors):
        """
        Ajusta parámetros de escalado una sola vez (calibración) y devuelve:
        - mean/std por sensor
        - min/max del raw_score de calibración
        """
        sensor_params = {}
        for col in available_sensors:
            mean = float(df[col].mean())
            std = float(df[col].std())
            if std <= 0:
                std = 1.0
            sensor_params[col] = {"mean": mean, "std": std}

        raw_score = self._compute_raw_score(df, sensor_params)
        raw_min = float(raw_score.min()) if len(raw_score) else 0.0
        raw_max = float(raw_score.max()) if len(raw_score) else 1.0
        if raw_max <= raw_min:
            raw_max = raw_min + 1.0

        return {
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "sensor_params": sensor_params,
            "raw_score_min": raw_min,
            "raw_score_max": raw_max,
        }

    def _save_scaler_params(self, params):
        """
        Persiste parámetros de escalado para reutilizarlos en corridas futuras.
        """
        os.makedirs(os.path.dirname(self.scaler_params_path), exist_ok=True)
        with open(self.scaler_params_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=4, ensure_ascii=False)

    def _load_scaler_params(self):
        """
        Carga parámetros persistidos si existen.
        """
        if not os.path.exists(self.scaler_params_path):
            return None
        with open(self.scaler_params_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _resolve_scaler_params(self, df, available_sensors):
        """
        Decide entre reutilizar parámetros guardados o recalibrar.
        Devuelve: (params, scaler_source)
        """
        if self.reuse_scaler_params:
            loaded = self._load_scaler_params()
            if loaded:
                loaded_sensors = set(loaded.get("sensor_params", {}).keys())
                required_sensors = set(available_sensors)
                if required_sensors.issubset(loaded_sensors):
                    return loaded, "reused"
                print("Advertencia: scaler guardado incompleto para sensores actuales. Recalibrando...")

        fitted = self._fit_scaler_params(df, available_sensors)
        self._save_scaler_params(fitted)
        return fitted, "fitted"

    def compute_risk_score(self, df, scaler_params=None):
        """
        Calcula un score de riesgo entre 0 y 1 por cada fila.

        Lógica baseline:
        - Para cada sensor relevante, calcula cuántas desviaciones estándar
          se aleja del promedio global (z-score).
        - El score final es el promedio normalizado de los z-scores absolutos.
        - Un score alto indica comportamiento anómalo simultáneo en varios sensores.
        """

        if scaler_params is None:
            # Compatibilidad con comportamiento previo (si no se pasa scaler).
            available_sensors = [c for c in self.sensor_cols if c in df.columns]
            scaler_params = self._fit_scaler_params(df, available_sensors)

        sensor_params = scaler_params.get("sensor_params", {})
        raw_score = self._compute_raw_score(df, sensor_params)

        min_s = float(scaler_params.get("raw_score_min", 0.0))
        max_s = float(scaler_params.get("raw_score_max", 1.0))

        # Normalización estable usando parámetros persistidos.
        if max_s > min_s:
            score = (raw_score - min_s) / (max_s - min_s)
        else:
            score = pd.Series(0.0, index=df.index)

        # Acotar a [0, 1] evita desborde cuando aparezcan valores extremos.
        return score.clip(lower=0.0, upper=1.0)

    def assign_risk_level(self, score):
        """
        Convierte el score numérico en un nivel de riesgo categórico.

        - ALTO  : score >= 0.7
        - MEDIO : score >= 0.4
        - BAJO  : score < 0.4
        """

        conditions = [
            score >= self.threshold_high,
            score >= self.threshold_medium,
        ]
        choices = ["ALTO", "MEDIO"]
        return np.select(conditions, choices, default="BAJO")

    def run(self):
        """
        Ejecuta el pipeline completo de detección de riesgo.

        Flujo:
        1. Carga dataset procesado desde Parquet.
        2. Valida que los sensores necesarios existan.
        3. Calcula score de riesgo por fila.
        4. Asigna nivel de riesgo categórico.
        5. Guarda resultado en Parquet.
        6. Genera log JSON estructurado.
        """

        start_time = datetime.now()
        run_id = start_time.strftime("%Y-%m-%d_%H-%M-%S")

        try:
            # Verificar que el archivo de entrada exista
            if not os.path.exists(self.input_path):
                raise FileNotFoundError(
                    f"No se encontró el archivo procesado en {self.input_path}. "
                    "Ejecuta primero el módulo de ingesta."
                )

            # Cargar dataset
            df = pd.read_parquet(self.input_path)
            # asegurar timestamp como columna
            if "timestamp" not in df.columns:
                df = df.reset_index()
            assert "timestamp" in df.columns, "timestamp sigue faltando"
            
            # Validar sensores disponibles
            available_sensors = [c for c in self.sensor_cols if c in df.columns]
            missing_sensors = [c for c in self.sensor_cols if c not in df.columns]

            if len(available_sensors) == 0:
                raise ValueError("Ningún sensor relevante encontrado en el dataset.")

            # Resolver parámetros de escalado (reusar o calibrar).
            scaler_params, scaler_source = self._resolve_scaler_params(df, available_sensors)

            # Calcular score de riesgo con parámetros estables.
            df["risk_score"] = self.compute_risk_score(df, scaler_params=scaler_params)

            # Asignar nivel de riesgo
            df["risk_level"] = self.assign_risk_level(df["risk_score"])

            # Crear carpeta de salida si no existe
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

            # Guardar resultado
            if "timestamp" not in df.columns:
                df = df.reset_index()

            df.to_parquet(self.output_path, index=False)

            end_time = datetime.now()
            exec_time = round((end_time - start_time).total_seconds(), 2)

            # Distribución de niveles para el log
            dist = df["risk_level"].value_counts().to_dict()

            # Log estructurado
            log_data = {
                "timestamp": start_time.isoformat(),
                "run_id": run_id,
                "operation": "risk_detection_baseline",
                "status": "SUCCESS",
                "input_file": self.input_path,
                "output_file": self.output_path,
                "scaler_params_path": self.scaler_params_path,
                "scaler_source": scaler_source,
                "metrics": {
                    "records_processed": int(len(df)),
                    "sensors_used": available_sensors,
                    "missing_sensors": missing_sensors,
                    "risk_distribution": dist,
                    "score_mean": round(float(df["risk_score"].mean()), 4),
                    "score_std": round(float(df["risk_score"].std()), 4),
                },
                "execution_time_seconds": exec_time,
            }

            self._save_log(log_data, run_id)

            print("Detección de riesgo completada correctamente")
            print(f"Registros procesados: {len(df):,}")
            print(f"Distribución de riesgo: {dist}")
            print(f"Tiempo de ejecución: {exec_time} segundos")

            return df

        except Exception as e:
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "run_id": run_id,
                "operation": "risk_detection_baseline",
                "status": "ERROR",
                "error_message": str(e),
                "input_file": self.input_path,
                "output_file": self.output_path,
            }
            self._save_log(error_log, run_id)
            print("Error en detección de riesgo:", e)
            return None

    def _save_log(self, log_data, run_id):
        """
        Guarda un archivo JSON por ejecución para trazabilidad.
        """
        os.makedirs(self.log_dir, exist_ok=True)
        log_path = os.path.join(self.log_dir, f"risk_detection_{run_id}.json")

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    predictor = RiskPredictor()
    predictor.run()
