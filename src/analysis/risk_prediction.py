import os
import json
import pandas as pd
import numpy as np
from datetime import datetime


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
        input_path="data/processed/base.parquet",
        output_path="data/processed/risk_scores.parquet",
        log_dir="logs",
    ):
        # Ruta del dataset procesado generado por el módulo de ingesta
        self.input_path = input_path

        self.output_path = output_path

        self.log_dir = log_dir

        # Sensores relevantes identificados en IN-3
        self.sensor_cols = [
            "TP2",
            "TP3",
            "H1",
            "DV_pressure",
            "Reservoirs",
            "Oil_Temperature",
            "Motor_Current",
        ]

        # Umbrales para clasificar nivel de riesgo
        # Score >= 0.7 → ALTO, >= 0.4 → MEDIO, < 0.4 → BAJO
        self.threshold_high = 0.7
        self.threshold_medium = 0.4

    def compute_risk_score(self, df):
        """
        Calcula un score de riesgo entre 0 y 1 por cada fila.

        Lógica baseline:
        - Para cada sensor relevante, calcula cuántas desviaciones estándar
          se aleja del promedio global (z-score).
        - El score final es el promedio normalizado de los z-scores absolutos.
        - Un score alto indica comportamiento anómalo simultáneo en varios sensores.
        """

        z_scores = pd.DataFrame(index=df.index)

        for col in self.sensor_cols:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    z_scores[col] = (df[col] - mean).abs() / std
                else:
                    z_scores[col] = 0.0

        # Promedio de z-scores por fila
        raw_score = z_scores.mean(axis=1)

        # Normalizar entre 0 y 1 usando min-max
        min_s = raw_score.min()
        max_s = raw_score.max()
        if max_s > min_s:
            score = (raw_score - min_s) / (max_s - min_s)
        else:
            score = pd.Series(0.0, index=df.index)

        return score

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

            # Validar sensores disponibles
            available_sensors = [c for c in self.sensor_cols if c in df.columns]
            missing_sensors = [c for c in self.sensor_cols if c not in df.columns]

            if len(available_sensors) == 0:
                raise ValueError("Ningún sensor relevante encontrado en el dataset.")

            # Calcular score de riesgo
            df["risk_score"] = self.compute_risk_score(df)

            # Asignar nivel de riesgo
            df["risk_level"] = self.assign_risk_level(df["risk_score"])

            # Crear carpeta de salida si no existe
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

            # Guardar resultado
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
