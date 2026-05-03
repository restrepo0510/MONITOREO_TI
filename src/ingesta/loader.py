import os
import json
from datetime import datetime
import pandas as pd


class DataLoader:
    """
    Módulo de ingesta del sistema de mantenimiento predictivo.

    Responsabilidades:
    - Leer el dataset crudo desde data/raw/.
    - Realizar limpieza mínima estructural.
    - Estandarizar nombres de columnas para coherencia interna.
    - Validar estructura básica requerida por el sistema.
    - Generar un dataset base procesado en formato Parquet.
    - Registrar cada ejecución en un log JSON estructurado.

    Este módulo no realiza análisis estadístico ni modelado.
    Solo garantiza que los datos estén listos y consistentes
    para que los siguientes módulos (preprocessing y modelo)
    trabajen sin errores estructurales.
    """
    # Importar configuración central
    from src.config import DATA_RAW_PATH, DATA_BASE_PATH, LOG_DIR

    def __init__(self,
             file_path=DATA_RAW_PATH,
             output_path=DATA_BASE_PATH,
             log_dir=LOG_DIR):
        # Ruta del archivo crudo que se desea cargar
        self.file_path = file_path

        # Ruta donde se guardará el dataset base procesado
        # Este archivo será utilizado por los módulos posteriores
        self.output_path = output_path

        # Carpeta donde se almacenarán los logs JSON
        self.log_dir = log_dir

        # Esquema interno estandarizado que utilizará todo el sistema
        # Se define explícitamente para poder validar estructura
        self.expected_columns = [
            "timestamp",
            "TP2",
            "TP3",
            "H1",
            "DV_pressure",
            "Reservoirs",
            "Oil_Temperature",
            "Motor_Current",
            "COMP",
            "DV_electric",
            "TOWERS",
            "MPG",
            "LPS",
            "Pressure_switch",
            "Oil_Level",
            "Caudal_impulses",
        ]

        # Mapeo de nombres del CSV real hacia el esquema interno
        # Sirve para corregir diferencias de mayúsculas o errores tipográficos
        self.rename_map = {
            "Oil_temperature": "Oil_Temperature",
            "Motor_current": "Motor_Current",
            "DV_eletric": "DV_electric",
            "Towers": "TOWERS",
            "Oil_level": "Oil_Level",
        }

    def load_and_validate(self):
        """
        Ejecuta el proceso completo de ingesta.

        Flujo:
        1. Verifica existencia del archivo.
        2. Carga el CSV en memoria.
        3. Aplica limpieza estructural básica.
        4. Normaliza nombres de columnas.
        5. Convierte y valida timestamp.
        6. Ordena datos temporalmente.
        7. Valida columnas esperadas.
        8. Guarda dataset base procesado en formato Parquet.
        9. Genera log estructurado con métricas.
        """

        start_time = datetime.now()
        run_id = start_time.strftime("%Y-%m-%d_%H-%M-%S")

        try:
            # Verificar que el archivo exista antes de continuar
            # Esto evita que el pipeline falle silenciosamente
            if not os.path.exists(self.file_path):
                raise FileNotFoundError("Archivo no encontrado en data/raw/")

            # Leer el dataset crudo
            # Este es el punto más costoso en tiempo si el archivo es grande
            df = pd.read_csv(self.file_path)

            # Eliminar columna índice innecesaria si el CSV fue exportado con índice
            # No aporta valor al análisis ni al modelo
            df = df.drop(columns=["Unnamed: 0"], errors="ignore")

            # Renombrar columnas al esquema interno estándar
            # Esto evita errores posteriores por diferencias de nombres
            df.rename(columns=self.rename_map, inplace=True)

            # Convertir la columna timestamp a formato datetime
            # Es fundamental para análisis temporal y ventanas de predicción
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

            # Eliminar filas con timestamp inválido
            # Filas sin tiempo no pueden participar en análisis temporal
            df = df.dropna(subset=["timestamp"])

            # Ordenar cronológicamente
            # Garantiza coherencia en cálculos por ventana y evolución temporal
            df = df.sort_values("timestamp").reset_index(drop=True)

            # Validar que estén todas las columnas necesarias
            # Si faltan columnas críticas, el sistema podría fallar más adelante
            missing_cols = [c for c in self.expected_columns if c not in df.columns]
            is_valid = len(missing_cols) == 0

            # Crear carpeta de salida si no existe
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

            # Guardar dataset base procesado
            # Se utiliza formato Parquet porque:
            # - Es más eficiente que CSV en almacenamiento.
            # - Es más rápido para lectura en análisis.
            # - Preserva correctamente tipos de datos.
            # - Evita repetir limpieza y renombrado en cada módulo.
            df.to_parquet(self.output_path, index=False)

            end_time = datetime.now()
            exec_time = round((end_time - start_time).total_seconds(), 2)

            # Construir log estructurado
            # Registra tanto métricas técnicas como estado de validación
            log_data = {
                "timestamp": start_time.isoformat(),
                "run_id": run_id,
                "operation": "ingestion_pipeline",
                "status": "SUCCESS" if is_valid else "WARNING",
                "input_file": self.file_path,
                "output_file": self.output_path,
                "metrics": {
                    "records_processed": int(len(df)),
                    "columns": int(len(df.columns)),
                    "missing_columns": missing_cols,
                    "memory_usage_mb": round(
                        df.memory_usage(deep=True).sum() / 1024**2, 2
                    ),
                    "min_timestamp": str(df["timestamp"].min()),
                    "max_timestamp": str(df["timestamp"].max()),
                },
                "execution_time_seconds": exec_time,
            }

            # Guardar log JSON
            # Se genera un archivo por ejecución para garantizar trazabilidad completa
            self._save_log(log_data, run_id)

            print("Ingesta completada correctamente")
            print(f"Registros procesados: {len(df):,}")
            print(f"Tiempo de ejecución: {exec_time} segundos")

            return df

        except Exception as e:
            # En caso de error, también se registra el evento
            # Esto garantiza que ninguna ejecución quede sin trazabilidad
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "run_id": run_id,
                "operation": "ingestion_pipeline",
                "status": "ERROR",
                "error_message": str(e),
                "input_file": self.file_path,
                "output_file": self.output_path,
            }

            self._save_log(error_log, run_id)
            print("Error en ingesta:", e)
            return None

    def _save_log(self, log_data, run_id):
        """
        Guarda un archivo JSON por ejecución.

        Esto permite:
        - Auditoría histórica.
        - Diagnóstico de errores.
        - Evidencia de cumplimiento del KR de trazabilidad.
        """

        os.makedirs(self.log_dir, exist_ok=True)
        log_path = os.path.join(self.log_dir, f"ingestion_{run_id}.json")

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    loader = DataLoader()
    loader.load_and_validate()