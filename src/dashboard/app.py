import os
import json
import pandas as pd
from datetime import datetime


class ModelOutputSaver:
    """
    Módulo de persistencia de salida del modelo.

    Responsabilidades:
    - Leer el archivo con risk_score y risk_level generado por RiskPredictor.
    - Seleccionar y estructurar las columnas de salida estándar.
    - Guardar el resultado final en formato Parquet y CSV.
    - Generar log JSON estructurado por ejecución.

    """

    def __init__(
        self,
        input_path="data/processed/risk_scores.parquet",
        output_parquet="data/output/model_output.parquet",
        output_csv="data/output/model_output.csv",
        log_dir="logs",
    ):
        # Archivo generado por RiskPredictor (IN-15)
        self.input_path = input_path

        # Salida en Parquet para uso interno del sistema
        self.output_parquet = output_parquet

        self.output_csv = output_csv

        # Carpeta de logs
        self.log_dir = log_dir

        # Columnas que conforman la salida estándar del modelo
        # timestamp: identifica la ventana temporal
        # risk_score: valor numérico entre 0 y 1
        # risk_level: categoría BAJO / MEDIO / ALTO
        self.output_columns = ["timestamp", "risk_score", "risk_level"]

    def run(self):
        """
        Flujo:
        1. Carga el archivo con scores y niveles de riesgo.
        2. Valida que las columnas de salida existan.
        3. Selecciona solo las columnas estándar de salida.
        4. Guarda en Parquet y CSV.
        5. Genera log estructurado.
        """

        start_time = datetime.now()
        run_id = start_time.strftime("%Y-%m-%d_%H-%M-%S")

        try:
            # Verificar que el archivo de entrada exista
            if not os.path.exists(self.input_path):
                raise FileNotFoundError(
                    f"No se encontró {self.input_path}. "
                    "Ejecuta primero src/analysis/risk_prediction.py"
                )

            # Cargar resultado del modelo
            df = pd.read_parquet(self.input_path)

            # Validar que las columnas necesarias existan
            missing = [c for c in self.output_columns if c not in df.columns]
            if missing:
                raise ValueError(
                    f"Columnas faltantes en la salida del modelo: {missing}"
                )

            # Seleccionar solo las columnas de salida estándar
            df_output = df[self.output_columns].copy()

            # Ordenar por timestamp para coherencia temporal
            df_output = df_output.sort_values("timestamp").reset_index(drop=True)

            # Crear carpeta de salida si no existe
            os.makedirs(os.path.dirname(self.output_parquet), exist_ok=True)

            # Guardar en Parquet 
            df_output.to_parquet(self.output_parquet, index=False)

            df_output.to_csv(self.output_csv, index=False)

            end_time = datetime.now()
            exec_time = round((end_time - start_time).total_seconds(), 2)

            # Distribución de niveles para el log
            dist = df_output["risk_level"].value_counts().to_dict()

            # Log estructurado
            log_data = {
                "timestamp": start_time.isoformat(),
                "run_id": run_id,
                "operation": "model_output_saver",
                "status": "SUCCESS",
                "input_file": self.input_path,
                "output_parquet": self.output_parquet,
                "output_csv": self.output_csv,
                "metrics": {
                    "records_saved": int(len(df_output)),
                    "risk_distribution": dist,
                    "score_min": round(float(df_output["risk_score"].min()), 4),
                    "score_max": round(float(df_output["risk_score"].max()), 4),
                    "score_mean": round(float(df_output["risk_score"].mean()), 4),
                    "time_range": {
                        "start": str(df_output["timestamp"].min()),
                        "end": str(df_output["timestamp"].max()),
                    },
                },
                "execution_time_seconds": exec_time,
            }

            self._save_log(log_data, run_id)

            print("Salida del modelo guardada correctamente")
            print(f"Registros guardados: {len(df_output):,}")
            print(f"Distribución de riesgo: {dist}")
            print(f"Archivos generados:")
            print(f"  → {self.output_parquet}")
            print(f"  → {self.output_csv}")
            print(f"Tiempo de ejecución: {exec_time} segundos")

            return df_output

        except Exception as e:
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "run_id": run_id,
                "operation": "model_output_saver",
                "status": "ERROR",
                "error_message": str(e),
                "input_file": self.input_path,
            }
            self._save_log(error_log, run_id)
            print("Error al guardar salida del modelo:", e)
            return None

    def _save_log(self, log_data, run_id):
        """
        Guarda un archivo JSON por ejecución para trazabilidad.
        """
        os.makedirs(self.log_dir, exist_ok=True)
        log_path = os.path.join(self.log_dir, f"model_output_{run_id}.json")

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    saver = ModelOutputSaver()
    saver.run()
