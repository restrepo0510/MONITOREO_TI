import pandas as pd

from src.config import DASHBOARD_SOURCE_OF_TRUTH_PATH, SENSOR_THRESHOLDS_PATH
from src.dashboard.utils.sensor_thresholds import (
    calibrate_sensor_thresholds,
    save_sensor_thresholds,
)


def run():
    print(f"[thresholds] Loading source: {DASHBOARD_SOURCE_OF_TRUTH_PATH}")
    df = pd.read_parquet(DASHBOARD_SOURCE_OF_TRUTH_PATH)

    thresholds = calibrate_sensor_thresholds(df)
    save_sensor_thresholds(thresholds, SENSOR_THRESHOLDS_PATH)

    print(f"[thresholds] Saved: {SENSOR_THRESHOLDS_PATH}")
    print(f"[thresholds] Healthy rows used: {thresholds.get('rows_healthy_used')}")
    print(f"[thresholds] Sensors calibrated: {list(thresholds.get('sensors', {}).keys())}")


if __name__ == "__main__":
    run()
