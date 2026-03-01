import pandas as pd
import json
import os
from datetime import datetime

class DataLoader:
    def __init__(self, file_path="data/raw/MetroPT3(AirCompressor).csv", log_dir="logs"):
        self.file_path = file_path
        self.log_dir = log_dir
        
        # Las 20 variables esperadas según la documentación oficial del MetroPT
        self.expected_columns = [
            "TP2", "TP3", "H1", "DV_pressure", "Reservoirs", "Oil_Temperature",
            "Flowmeter", "Motor_Current", "COMP", "DV_electric", "TOWERS",
            "MPG", "LPS", "Pressure_switch", "Oil_Level", "Caudal_impulses",
            "gpsLong", "gpsLat", "gpsSpeed", "gpsQuality"
        ]

    def load_and_validate(self):
        print(f"⏳ Iniciando carga de datos desde: {self.file_path}")
        print("   Esto puede tardar un par de minutos (el archivo pesa ~1.5 GB)...")
        
        start_time = datetime.now()
        
        if not os.path.exists(self.file_path):
            print(f"\n❌ ERROR: No se encontró el archivo en {self.file_path}")
            print("   Asegúrate de guardar el CSV en 'data/raw/' con el nombre 'MetroPT3.csv'")
            return None

        try:
            df = pd.read_csv(self.file_path)
            
            records_count = len(df)
            columns_present = list(df.columns)
            
            missing_cols = [col for col in self.expected_columns if col not in columns_present]
            is_valid = len(missing_cols) == 0
            
            log_data = {
                "timestamp": start_time.isoformat(),
                "status": "SUCCESS" if is_valid else "WARNING",
                "file": self.file_path,
                "metrics": {
                    "total_records": records_count,
                    "total_columns": len(columns_present),
                    "expected_columns_found": is_valid,
                    "missing_columns": missing_cols
                },
                "execution_time_seconds": round((datetime.now() - start_time).total_seconds(), 2)
            }

            self._save_log(log_data)
            
            print(f"\n✅ Carga exitosa completada en {log_data['execution_time_seconds']} segundos.")
            print(f"📊 Registros encontrados: {records_count:,}")
            print(f"📊 Variables (columnas): {len(columns_present)}")
            print(f"📝 Log de auditoría guardado en la carpeta '{self.log_dir}'")
            
            return df
            
        except Exception as e:
            print(f"\n❌ Error inesperado al cargar los datos: {str(e)}")
            self._save_log({"timestamp": start_time.isoformat(), "status": "ERROR", "error_message": str(e)})
            return None

    def _save_log(self, log_data):
        os.makedirs(self.log_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"ingestion_{date_str}.json")
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4)

if __name__ == "__main__":
    loader = DataLoader()
    dataset = loader.load_and_validate()