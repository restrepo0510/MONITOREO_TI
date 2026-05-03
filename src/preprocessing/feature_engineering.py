import pandas as pd
from pathlib import Path


WINDOW_SIZE = "5min"
INPUT_PATH = Path("data/processed/base.parquet")
OUTPUT_PATH = Path("data/processed/features.parquet")

ANALOG_SENSORS = [
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_Temperature",
    "Motor_Current",
]

DIGITAL_SIGNALS = [
    "COMP",
    "DV_electric",
    "TOWERS",
    "MPG",
    "LPS",
    "Pressure_switch",
    "Oil_Level",
    "Caudal_impulses",
]


def _flatten_columns(columns):
    flat = []
    for col in columns:
        if isinstance(col, tuple):
            flat.append("_".join(str(part) for part in col if part))
        else:
            flat.append(str(col))
    return flat


def generate_features():
    print("Loading base dataset...")
    df = pd.read_parquet(INPUT_PATH)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).set_index("timestamp").sort_index()

    analog_aggs = ["mean", "std", "min", "max", "last"]
    digital_aggs = ["mean", "sum", "last"]

    agg_dict = {}

    for col in ANALOG_SENSORS:
        if col in df.columns:
            agg_dict[col] = analog_aggs

    for col in DIGITAL_SIGNALS:
        if col in df.columns:
            agg_dict[col] = digital_aggs

    missing_analog = [c for c in ANALOG_SENSORS if c not in df.columns]
    missing_digital = [c for c in DIGITAL_SIGNALS if c not in df.columns]
    if missing_analog:
        print("Missing analog sensors:", missing_analog)
    if missing_digital:
        print("Missing digital signals:", missing_digital)

    if not agg_dict:
        raise ValueError("No valid sensors found to aggregate.")

    print(f"Generating features with window: {WINDOW_SIZE}")
    features = df.resample(WINDOW_SIZE).agg(agg_dict).reset_index()

    features.columns = _flatten_columns(features.columns)

    value_cols = [c for c in features.columns if c != "timestamp"]
    features = features.dropna(subset=value_cols, how="all")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(OUTPUT_PATH, index=False)

    print(f"Features saved to: {OUTPUT_PATH}")
    print(f"Final shape: {features.shape}")

    return features


if __name__ == "__main__":
    generate_features()
