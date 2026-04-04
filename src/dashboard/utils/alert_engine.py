"""
Motor de alertas formal para el dashboard de monitoreo.

Objetivo:
- Traducir datos de sensores + riesgo en una alerta operacional por ventana.
- Entregar trazabilidad: para cada ventana se listan causas concretas.
- Mantener reglas estables usando umbrales fijos calibrados en historico sano.

Notas de diseno:
- Prioridad de severidad: ALTO > MEDIO > BAJO.
- Si una condicion ALTO se activa, domina sobre cualquier MEDIO.
- Si no hay umbrales calibrados disponibles, se usa fallback por risk_score.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

from src.config import (
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_MEDIUM,
    SENSOR_THRESHOLDS_PATH,
)
from src.dashboard.utils.sensor_thresholds import load_sensor_thresholds


# Prioridad formal de alertas.
_LEVEL_PRIORITY = {"BAJO": 0, "MEDIO": 1, "ALTO": 2}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _get_sensor_cfg(thresholds: Dict[str, Any], sensor_key: str) -> Dict[str, Any]:
    return thresholds.get("sensors", {}).get(sensor_key, {})


def _promote_level(current: str, candidate: str) -> str:
    if _LEVEL_PRIORITY.get(candidate, 0) > _LEVEL_PRIORITY.get(current, 0):
        return candidate
    return current


def _range_rule(
    value: float,
    warn_low: float | None = None,
    warn_high: float | None = None,
    crit_low: float | None = None,
    crit_high: float | None = None,
) -> Tuple[str, str]:
    """
    Evalua una regla de rango y devuelve:
    - nivel candidato (BAJO/MEDIO/ALTO)
    - causa corta para trazabilidad
    """
    if crit_low is not None and value < crit_low:
        return "ALTO", f"valor {value:.4f} < crit_low {crit_low:.4f}"
    if crit_high is not None and value > crit_high:
        return "ALTO", f"valor {value:.4f} > crit_high {crit_high:.4f}"
    if warn_low is not None and value < warn_low:
        return "MEDIO", f"valor {value:.4f} < warn_low {warn_low:.4f}"
    if warn_high is not None and value > warn_high:
        return "MEDIO", f"valor {value:.4f} > warn_high {warn_high:.4f}"
    return "BAJO", ""


def _eval_sensor_rules(
    row: pd.Series,
    thresholds: Dict[str, Any],
    dv_spike_residual: float | None,
) -> Tuple[str, List[str]]:
    """
    Evalua reglas por sensor para UNA fila.
    """
    level = "BAJO"
    reasons: List[str] = []

    # TP3 y H1: control por rango bajo/alto.
    for sensor_key in ("TP3_mean", "H1_mean"):
        if sensor_key not in row.index:
            continue
        sensor_cfg = _get_sensor_cfg(thresholds, sensor_key)
        if not sensor_cfg:
            continue
        value = _safe_float(row.get(sensor_key))
        candidate, detail = _range_rule(
            value=value,
            warn_low=sensor_cfg.get("warn_low"),
            warn_high=sensor_cfg.get("warn_high"),
            crit_low=sensor_cfg.get("crit_low"),
            crit_high=sensor_cfg.get("crit_high"),
        )
        if candidate != "BAJO":
            level = _promote_level(level, candidate)
            reasons.append(f"{sensor_key}: {detail}")

    # DV_pressure: rango + picos.
    if "DV_pressure_mean" in row.index:
        dv_cfg = _get_sensor_cfg(thresholds, "DV_pressure_mean")
        if dv_cfg:
            dv_value = _safe_float(row.get("DV_pressure_mean"))
            candidate, detail = _range_rule(
                value=dv_value,
                warn_low=dv_cfg.get("warn_low"),
                warn_high=dv_cfg.get("warn_high"),
                crit_low=dv_cfg.get("crit_low"),
                crit_high=dv_cfg.get("crit_high"),
            )
            if candidate != "BAJO":
                level = _promote_level(level, candidate)
                reasons.append(f"DV_pressure_mean: {detail}")

            # Alarma por pico abrupto respecto a mediana movil.
            spike_threshold = _safe_float(dv_cfg.get("spike_threshold"), default=0.0)
            if dv_spike_residual is not None and spike_threshold > 0:
                if dv_spike_residual > (spike_threshold * 1.5):
                    level = _promote_level(level, "ALTO")
                    reasons.append(
                        f"DV_pressure_mean: pico alto {dv_spike_residual:.4f} > 1.5x spike_threshold {spike_threshold:.4f}"
                    )
                elif dv_spike_residual > spike_threshold:
                    level = _promote_level(level, "MEDIO")
                    reasons.append(
                        f"DV_pressure_mean: pico {dv_spike_residual:.4f} > spike_threshold {spike_threshold:.4f}"
                    )

    # Motor current: consumo alto.
    if "Motor_Current_mean" in row.index:
        motor_cfg = _get_sensor_cfg(thresholds, "Motor_Current_mean")
        if motor_cfg:
            motor_value = _safe_float(row.get("Motor_Current_mean"))
            crit_high = motor_cfg.get("crit_high")
            warn_high = motor_cfg.get("warn_high")
            if crit_high is not None and motor_value > crit_high:
                level = _promote_level(level, "ALTO")
                reasons.append(
                    f"Motor_Current_mean: valor {motor_value:.4f} > crit_high {float(crit_high):.4f}"
                )
            elif warn_high is not None and motor_value > warn_high:
                level = _promote_level(level, "MEDIO")
                reasons.append(
                    f"Motor_Current_mean: valor {motor_value:.4f} > warn_high {float(warn_high):.4f}"
                )

    # Oil temperature: limites de operacion normal.
    if "Oil_Temperature_mean" in row.index:
        oil_cfg = _get_sensor_cfg(thresholds, "Oil_Temperature_mean")
        if oil_cfg:
            oil_value = _safe_float(row.get("Oil_Temperature_mean"))
            candidate, detail = _range_rule(
                value=oil_value,
                warn_low=oil_cfg.get("warn_low"),
                warn_high=oil_cfg.get("warn_high"),
                crit_low=oil_cfg.get("crit_low"),
                crit_high=oil_cfg.get("crit_high"),
            )
            if candidate != "BAJO":
                level = _promote_level(level, candidate)
                reasons.append(f"Oil_Temperature_mean: {detail}")

    return level, reasons


def _eval_risk_rules(row: pd.Series) -> Tuple[str, List[str]]:
    """
    Evalua reglas por risk_score/risk_level para UNA fila.
    """
    level = "BAJO"
    reasons: List[str] = []

    score = _safe_float(row.get("risk_score"))
    if score >= RISK_THRESHOLD_HIGH:
        level = "ALTO"
        reasons.append(
            f"risk_score: {score:.4f} >= umbral_alto {RISK_THRESHOLD_HIGH:.2f}"
        )
    elif score >= RISK_THRESHOLD_MEDIUM:
        level = "MEDIO"
        reasons.append(
            f"risk_score: {score:.4f} >= umbral_medio {RISK_THRESHOLD_MEDIUM:.2f}"
        )

    # Se conserva compatibilidad con la etiqueta ya calculada por el modelo.
    model_level = str(row.get("risk_level", "")).upper()
    if model_level == "ALTO":
        level = _promote_level(level, "ALTO")
        reasons.append("risk_level del modelo = ALTO")
    elif model_level == "MEDIO":
        level = _promote_level(level, "MEDIO")
        reasons.append("risk_level del modelo = MEDIO")

    return level, reasons


def evaluate_alerts(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aplica el motor de alertas al dataframe completo.

    Retorna:
    - df_alerts: dataframe original + columnas de alerta operacional
    - meta: metadatos de la corrida de reglas (version y fuentes)
    """
    if df is None or df.empty:
        return df, {"engine_version": "v1", "rows": 0, "threshold_source": "none"}

    thresholds = load_sensor_thresholds(SENSOR_THRESHOLDS_PATH)
    has_sensor_thresholds = bool(thresholds.get("sensors", {}))

    # Residual de DV para detectar picos (valor vs mediana movil).
    dv_residual = None
    if "DV_pressure_mean" in df.columns:
        dv_series = pd.to_numeric(df["DV_pressure_mean"], errors="coerce")
        dv_baseline = dv_series.rolling(12, min_periods=1).median()
        dv_residual = (dv_series - dv_baseline).abs()

    output = df.copy()
    alert_levels: List[str] = []
    alert_reasons: List[str] = []
    alert_sources: List[str] = []
    alert_trigger_count: List[int] = []

    # Evaluacion fila a fila para preservar explicabilidad.
    for pos, (_, row) in enumerate(output.iterrows()):
        risk_level, risk_reasons = _eval_risk_rules(row)

        sensor_level = "BAJO"
        sensor_reasons: List[str] = []
        if has_sensor_thresholds:
            row_dv_residual = None
            if dv_residual is not None:
                row_dv_residual = _safe_float(dv_residual.iloc[pos], default=0.0)
            sensor_level, sensor_reasons = _eval_sensor_rules(
                row=row,
                thresholds=thresholds,
                dv_spike_residual=row_dv_residual,
            )

        final_level = _promote_level(risk_level, sensor_level)

        sources = []
        if risk_reasons:
            sources.append("riesgo")
        if sensor_reasons:
            sources.append("sensores")

        reasons = risk_reasons + sensor_reasons
        if not reasons:
            reasons = ["Sin condiciones de alerta activas."]

        alert_levels.append(final_level)
        alert_reasons.append(" | ".join(reasons))
        alert_sources.append("+".join(sources) if sources else "none")
        alert_trigger_count.append(len(risk_reasons) + len(sensor_reasons))

    output["alert_level"] = alert_levels
    output["alert_sources"] = alert_sources
    output["alert_trigger_count"] = alert_trigger_count
    output["alert_reasons"] = alert_reasons

    meta = {
        "engine_version": "v1",
        "rows": int(len(output)),
        "threshold_source": SENSOR_THRESHOLDS_PATH if has_sensor_thresholds else "risk_only_fallback",
        "risk_threshold_medium": float(RISK_THRESHOLD_MEDIUM),
        "risk_threshold_high": float(RISK_THRESHOLD_HIGH),
    }
    if has_sensor_thresholds:
        meta["sensor_threshold_version"] = thresholds.get("version")
        meta["sensor_threshold_created_at"] = thresholds.get("created_at")
        meta["healthy_filter"] = thresholds.get("healthy_filter")

    return output, meta


def evaluate_latest_alert(df: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Evalua SOLO la ultima ventana para uso en UI de baja latencia.

    Retorna:
    - latest_alert: dict con columnas de alerta para la ultima fila
    - meta: metadatos de evaluacion
    """
    if df is None or df.empty:
        return (
            {
                "alert_level": "BAJO",
                "alert_sources": "none",
                "alert_trigger_count": 0,
                "alert_reasons": "Sin datos.",
                "risk_level": None,
                "risk_score": None,
                "timestamp": None,
            },
            {"engine_version": "v1-latest", "rows": 0, "threshold_source": "none"},
        )

    latest = df.iloc[-1]
    thresholds = load_sensor_thresholds(SENSOR_THRESHOLDS_PATH)
    has_sensor_thresholds = bool(thresholds.get("sensors", {}))

    risk_level, risk_reasons = _eval_risk_rules(latest)

    sensor_level = "BAJO"
    sensor_reasons: List[str] = []
    if has_sensor_thresholds:
        row_dv_residual = None
        if "DV_pressure_mean" in df.columns:
            dv_window = pd.to_numeric(df["DV_pressure_mean"].tail(12), errors="coerce")
            if not dv_window.dropna().empty:
                dv_baseline = float(dv_window.median())
                last_dv = _safe_float(latest.get("DV_pressure_mean"), default=0.0)
                row_dv_residual = abs(last_dv - dv_baseline)

        sensor_level, sensor_reasons = _eval_sensor_rules(
            row=latest,
            thresholds=thresholds,
            dv_spike_residual=row_dv_residual,
        )

    final_level = _promote_level(risk_level, sensor_level)

    sources = []
    if risk_reasons:
        sources.append("riesgo")
    if sensor_reasons:
        sources.append("sensores")

    reasons = risk_reasons + sensor_reasons
    if not reasons:
        reasons = ["Sin condiciones de alerta activas."]

    latest_alert = {
        "alert_level": final_level,
        "alert_sources": "+".join(sources) if sources else "none",
        "alert_trigger_count": len(risk_reasons) + len(sensor_reasons),
        "alert_reasons": " | ".join(reasons),
        "risk_level": latest.get("risk_level"),
        "risk_score": latest.get("risk_score"),
        "timestamp": latest.get("timestamp"),
    }

    meta = {
        "engine_version": "v1-latest",
        "rows": int(len(df)),
        "threshold_source": SENSOR_THRESHOLDS_PATH if has_sensor_thresholds else "risk_only_fallback",
        "risk_threshold_medium": float(RISK_THRESHOLD_MEDIUM),
        "risk_threshold_high": float(RISK_THRESHOLD_HIGH),
    }
    if has_sensor_thresholds:
        meta["sensor_threshold_version"] = thresholds.get("version")
        meta["sensor_threshold_created_at"] = thresholds.get("created_at")
        meta["healthy_filter"] = thresholds.get("healthy_filter")

    return latest_alert, meta
