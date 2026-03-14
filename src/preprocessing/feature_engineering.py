import pandas as pd
from pathlib import Path


# ======================================================
# CONFIGURACIÓN
# ======================================================

# Ventana temporal seleccionada en el análisis
WINDOW_SIZE = "5min"

# Dataset generado por la etapa de ingesta
INPUT_PATH = Path("data/processed/base.parquet")

# Dataset de salida con las features generadas
OUTPUT_PATH = Path("data/processed/features.parquet")


# ======================================================
# VARIABLES DEL DATASET
# ======================================================

# Sensores analógicos (valores continuos)
ANALOG_SENSORS = [
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_Temperature",
    "Motor_Current"
]

# Señales digitales (0 / 1)
DIGITAL_SIGNALS = [
    "COMP",
    "DV_eletric",
    "Towers",
    "MPG",
    "LPS",
    "Pressure_switch",
    "Oil_level",
    "Caudal_impulses"
]


# ======================================================
# GENERAR FEATURES
# ======================================================

def generate_features():

    print("Cargando dataset base...")

    df = pd.read_parquet(INPUT_PATH)

    print("Dataset cargado")
    print("Registros:", len(df))

    # ==================================================
    # convertir timestamp a datetime
    # ==================================================

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # usar timestamp como índice temporal
    df = df.set_index("timestamp")

    # ==================================================
    # definir agregaciones
    # ==================================================

    # agregaciones para sensores analógicos
    analog_aggs = ["mean", "std", "min", "max", "last"]

    # agregaciones para señales digitales
    digital_aggs = ["mean", "sum", "last"]

    agg_dict = {}

    # construir diccionario de agregaciones
    for col in ANALOG_SENSORS:
        if col in df.columns:
            agg_dict[col] = analog_aggs

    for col in DIGITAL_SIGNALS:
        if col in df.columns:
            agg_dict[col] = digital_aggs

    # ==================================================
    # crear ventanas temporales
    # ==================================================

    print("Generando features por ventana:", WINDOW_SIZE)

    # agrupar datos en ventanas de 5 minutos
    features = df.resample(WINDOW_SIZE).agg(agg_dict)

    # ==================================================
    # limpiar nombres de columnas
    # ==================================================

    # multiindex -> nombre simple
    features.columns = [
        "_".join(col) for col in features.columns
    ]

    # ==================================================
    # eliminar ventanas vacías
    # ==================================================

    # eliminar solo ventanas completamente vacías
    features = features.dropna(how="all")

    # ==================================================
    # guardar resultado
    # ==================================================

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    features.to_parquet(OUTPUT_PATH)

    print("Features guardadas en:")
    print(OUTPUT_PATH)

    print("Shape final:", features.shape)

    return features


# ======================================================
# EJECUCIÓN
# ======================================================

if __name__ == "__main__":
    generate_features()

import pandas as pd
from pathlib import Path


# ======================================================
# CONFIGURACIÓN
# ======================================================

# Ventana temporal seleccionada en el análisis
WINDOW_SIZE = "5min"

# Dataset generado por la etapa de ingesta
INPUT_PATH = Path("data/processed/base.parquet")

# Dataset de salida con las features generadas
OUTPUT_PATH = Path("data/processed/features.parquet")


# ======================================================
# VARIABLES DEL DATASET
# ======================================================

# Sensores analógicos (valores continuos)
ANALOG_SENSORS = [
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_Temperature",
    "Motor_Current"
]

# Señales digitales (0 / 1)
DIGITAL_SIGNALS = [
    "COMP",
    "DV_eletric",
    "Towers",
    "MPG",
    "LPS",
    "Pressure_switch",
    "Oil_level",
    "Caudal_impulses"
]


# ======================================================
# GENERAR FEATURES
# ======================================================

def generate_features():

    print("Cargando dataset base...")

    df = pd.read_parquet(INPUT_PATH)

    print("Dataset cargado")
    print("Registros:", len(df))

    # ==================================================
    # convertir timestamp a datetime
    # ==================================================

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # usar timestamp como índice temporal
    df = df.set_index("timestamp")

    # ==================================================
    # definir agregaciones
    # ==================================================

    # agregaciones para sensores analógicos
    analog_aggs = ["mean", "std", "min", "max", "last"]

    # agregaciones para señales digitales
    digital_aggs = ["mean", "sum", "last"]

    agg_dict = {}

    # construir diccionario de agregaciones
    for col in ANALOG_SENSORS:
        if col in df.columns:
            agg_dict[col] = analog_aggs

    for col in DIGITAL_SIGNALS:
        if col in df.columns:
            agg_dict[col] = digital_aggs

    # ==================================================
    # crear ventanas temporales
    # ==================================================

    print("Generando features por ventana:", WINDOW_SIZE)

    # agrupar datos en ventanas de 5 minutos
    features = df.resample(WINDOW_SIZE).agg(agg_dict)

    # ==================================================
    # limpiar nombres de columnas
    # ==================================================

    # multiindex -> nombre simple
    features.columns = [
        "_".join(col) for col in features.columns
    ]

    # ==================================================
    # eliminar ventanas vacías
    # ==================================================

    # eliminar solo ventanas completamente vacías
    features = features.dropna(how="all")

    # ==================================================
    # guardar resultado
    # ==================================================

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    features.to_parquet(OUTPUT_PATH)

    print("Features guardadas en:")
    print(OUTPUT_PATH)

    print("Shape final:", features.shape)

    return features


# ======================================================
# EJECUCIÓN
# ======================================================

if __name__ == "__main__":
    generate_features()