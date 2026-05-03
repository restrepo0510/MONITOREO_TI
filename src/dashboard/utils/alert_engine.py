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

import numpy as np
import pandas as pd

from src.config import (
    PREDICTION_HORIZON_MINUTES,
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_MEDIUM,
    SENSOR_THRESHOLDS_PATH,
)
from src.dashboard.utils.sensor_thresholds import (
    calibrate_sensor_thresholds,
    load_sensor_thresholds,
)


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


def _calibration_sample(df: pd.DataFrame, max_rows: int = 50000) -> pd.DataFrame:
    if df is None or df.empty or len(df) <= max_rows:
        return df.copy()
    step = max(len(df) // max_rows, 1)
    return df.iloc[::step].copy()


def resolve_alert_thresholds(
    df: pd.DataFrame,
    thresholds: Dict[str, Any] | None = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Resuelve umbrales para el motor:
    - usa los provistos si llegan desde el caller
    - intenta cargar el JSON persistido
    - si no existe, calibra en runtime sobre una muestra del dataset
    """
    if thresholds and thresholds.get("sensors"):
        return thresholds, str(thresholds.get("_source", "provided"))

    persisted = load_sensor_thresholds(SENSOR_THRESHOLDS_PATH)
    if persisted.get("sensors"):
        persisted["_source"] = SENSOR_THRESHOLDS_PATH
        return persisted, SENSOR_THRESHOLDS_PATH

    if df is None or df.empty:
        return {}, "none"

    sample_df = _calibration_sample(df)
    runtime_thresholds = calibrate_sensor_thresholds(sample_df)
    runtime_thresholds["runtime_calibration"] = True
    runtime_thresholds["calibration_sample_rows"] = int(len(sample_df))
    runtime_thresholds["_source"] = "runtime_calibration"
    return runtime_thresholds, "runtime_calibration"


def _build_context_series(
    df: pd.DataFrame,
    thresholds: Dict[str, Any],
) -> Dict[str, pd.Series | None]:
    context: Dict[str, pd.Series | None] = {
        "dv_residual": None,
        "mpg_active_pct": None,
        "tower_switches": None,
    }

    if "DV_pressure_mean" in df.columns:
        dv_series = pd.to_numeric(df["DV_pressure_mean"], errors="coerce")
        dv_baseline = dv_series.rolling(12, min_periods=1).median()
        context["dv_residual"] = (dv_series - dv_baseline).abs()

    if "MPG_last" in df.columns:
        mpg_cfg = _get_sensor_cfg(thresholds, "MPG_last")
        on_threshold = _safe_float(mpg_cfg.get("on_threshold"), default=0.5)
        mpg_series = pd.to_numeric(df["MPG_last"], errors="coerce").fillna(0.0)
        context["mpg_active_pct"] = (
            (mpg_series > on_threshold).astype(float).rolling(24, min_periods=1).mean()
            * 100.0
        )

    if "TOWERS_last" in df.columns:
        towers_series = pd.to_numeric(df["TOWERS_last"], errors="coerce").fillna(0.0)
        context["tower_switches"] = (
            towers_series.diff().abs().fillna(0.0).rolling(24, min_periods=1).sum()
        )

    return context


def _context_value(series: pd.Series | None, pos: int, default: float | None = None):
    if series is None or len(series) <= pos:
        return default
    return _safe_float(series.iloc[pos], default=default or 0.0)


def _score_to_level(score: float) -> str:
    if score >= RISK_THRESHOLD_HIGH:
        return "ALTO"
    if score >= RISK_THRESHOLD_MEDIUM:
        return "MEDIO"
    return "BAJO"


def _compute_operational_risk_score(
    base_score: float,
    sensor_level: str,
    relation_level: str,
    sensor_trigger_count: int,
    relation_trigger_count: int,
) -> float:
    """
    Ajusta el score general cuando hay evidencia fuerte en sensores/relaciones.
    Objetivo: evitar que una anomalia severa quede solo en tarjeta de sensor.
    """
    score = float(np.clip(base_score, 0.0, 1.0))

    floor = 0.0
    if sensor_level == "ALTO" or relation_level == "ALTO":
        floor = max(floor, float(RISK_THRESHOLD_HIGH + 0.02))
    elif sensor_level == "MEDIO" or relation_level == "MEDIO":
        floor = max(floor, float(RISK_THRESHOLD_MEDIUM + 0.03))

    trigger_boost = min(
        0.12,
        (max(sensor_trigger_count, 0) * 0.02)
        + (max(relation_trigger_count, 0) * 0.025),
    )

    adjusted = max(score, floor)
    if adjusted >= RISK_THRESHOLD_HIGH:
        adjusted = min(1.0, adjusted + min(trigger_boost, 0.06))
    else:
        adjusted = min(1.0, adjusted + trigger_boost)

    return float(np.clip(adjusted, 0.0, 1.0))


def _eval_sensor_rules(
    row: pd.Series,
    thresholds: Dict[str, Any],
    context_row: Dict[str, float | None],
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
            dv_spike_residual = context_row.get("dv_residual")
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

    mpg_cfg = _get_sensor_cfg(thresholds, "MPG_last")
    mpg_active_pct = context_row.get("mpg_active_pct")
    if mpg_cfg and mpg_active_pct is not None:
        risk_score = _safe_float(row.get("risk_score"), default=0.0)
        min_active_pct_warn = _safe_float(
            mpg_cfg.get("min_active_pct_warn"), default=55.0
        )
        if (
            mpg_active_pct >= max(min_active_pct_warn + 25.0, 90.0)
            and risk_score >= RISK_THRESHOLD_MEDIUM
        ):
            level = _promote_level(level, "MEDIO")
            reasons.append(
                f"MPG_last: actividad reciente {mpg_active_pct:.1f}% supera patron saludable bajo riesgo elevado"
            )

    towers_switches = context_row.get("tower_switches")
    dv_cfg = _get_sensor_cfg(thresholds, "DV_pressure_mean")
    dv_spike_threshold = _safe_float(dv_cfg.get("spike_threshold"), default=0.0)
    dv_residual = context_row.get("dv_residual")
    if towers_switches is not None and dv_residual is not None and dv_spike_threshold > 0:
        if towers_switches <= 0.0 and dv_residual > (dv_spike_threshold * 1.25):
            level = _promote_level(level, "MEDIO")
            reasons.append(
                "TOWERS_last: sin conmutacion reciente mientras DV_pressure muestra descarga anomala"
            )

    return level, reasons


def _eval_relation_rules(
    row: pd.Series,
    thresholds: Dict[str, Any],
    context_row: Dict[str, float | None],
) -> Tuple[str, List[str]]:
    """
    Reglas para patrones cruzados entre sensores.
    Permiten distinguir alertas globales vs alertas atribuibles a relaciones.
    """
    level = "BAJO"
    reasons: List[str] = []

    tp3_cfg = _get_sensor_cfg(thresholds, "TP3_mean")
    h1_cfg = _get_sensor_cfg(thresholds, "H1_mean")
    dv_cfg = _get_sensor_cfg(thresholds, "DV_pressure_mean")
    motor_cfg = _get_sensor_cfg(thresholds, "Motor_Current_mean")
    oil_cfg = _get_sensor_cfg(thresholds, "Oil_Temperature_mean")

    tp3 = _safe_float(row.get("TP3_mean"), default=np.nan)
    h1 = _safe_float(row.get("H1_mean"), default=np.nan)
    motor = _safe_float(row.get("Motor_Current_mean"), default=np.nan)
    oil = _safe_float(row.get("Oil_Temperature_mean"), default=np.nan)
    score = _safe_float(row.get("risk_score"), default=0.0)

    tp3_warn_low = tp3_cfg.get("warn_low")
    tp3_crit_low = tp3_cfg.get("crit_low")
    h1_warn_low = h1_cfg.get("warn_low")
    h1_crit_low = h1_cfg.get("crit_low")
    motor_warn_high = motor_cfg.get("warn_high")
    motor_crit_high = motor_cfg.get("crit_high")
    oil_warn_high = oil_cfg.get("warn_high")
    oil_crit_high = oil_cfg.get("crit_high")
    dv_spike_threshold = _safe_float(dv_cfg.get("spike_threshold"), default=0.0)

    dv_residual = context_row.get("dv_residual")
    mpg_active_pct = context_row.get("mpg_active_pct")
    tower_switches = context_row.get("tower_switches")

    if (
        tp3_warn_low is not None
        and motor_warn_high is not None
        and tp3 < float(tp3_warn_low)
        and motor > float(motor_warn_high)
    ):
        candidate = "MEDIO"
        if (
            tp3_crit_low is not None
            and motor_crit_high is not None
            and tp3 < float(tp3_crit_low)
            and motor > float(motor_crit_high)
        ):
            candidate = "ALTO"
        level = _promote_level(level, candidate)
        reasons.append(
            "relacion_presion_carga: TP3 bajo con Motor_Current alto sugiere esfuerzo del compresor sin recuperar presion"
        )

    if (
        h1_warn_low is not None
        and mpg_active_pct is not None
        and h1 < float(h1_warn_low)
        and mpg_active_pct >= 65.0
    ):
        candidate = "ALTO" if h1_crit_low is not None and h1 < float(h1_crit_low) else "MEDIO"
        level = _promote_level(level, candidate)
        reasons.append(
            "relacion_recuperacion_lenta: H1 bajo con MPG activo de forma persistente indica recuperacion ineficiente"
        )

    if (
        dv_residual is not None
        and dv_spike_threshold > 0
        and oil_warn_high is not None
        and oil > float(oil_warn_high)
        and dv_residual > dv_spike_threshold
    ):
        candidate = (
            "ALTO"
            if oil_crit_high is not None and oil > float(oil_crit_high)
            else "MEDIO"
        )
        level = _promote_level(level, candidate)
        reasons.append(
            "relacion_secado_termico: descargas anormales con temperatura de aceite elevada elevan la degradacion"
        )

    if (
        tower_switches is not None
        and dv_residual is not None
        and tower_switches <= 0.0
        and dv_residual > max(dv_spike_threshold, 0.05)
        and score >= RISK_THRESHOLD_MEDIUM
    ):
        candidate = "ALTO" if score >= RISK_THRESHOLD_HIGH else "MEDIO"
        level = _promote_level(level, candidate)
        reasons.append(
            "relacion_torres_secado: ausencia de conmutacion en torres mientras la descarga permanece inestable"
        )

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


def evaluate_alerts(
    df: pd.DataFrame,
    thresholds: Dict[str, Any] | None = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aplica el motor de alertas al dataframe completo.

    Retorna:
    - df_alerts: dataframe original + columnas de alerta operacional
    - meta: metadatos de la corrida de reglas (version y fuentes)
    """
    if df is None or df.empty:
        return df, {"engine_version": "v1", "rows": 0, "threshold_source": "none"}

    thresholds, threshold_source = resolve_alert_thresholds(df, thresholds)
    has_sensor_thresholds = bool(thresholds.get("sensors", {}))
    context_series = _build_context_series(df, thresholds)

    output = df.copy()
    alert_levels: List[str] = []
    alert_reasons: List[str] = []
    alert_sources: List[str] = []
    alert_trigger_count: List[int] = []
    risk_scores_operational: List[float] = []
    risk_levels_operational: List[str] = []
    risk_score_deltas: List[float] = []

    # Evaluacion fila a fila para preservar explicabilidad.
    for pos, (_, row) in enumerate(output.iterrows()):
        risk_level, risk_reasons = _eval_risk_rules(row)

        sensor_level = "BAJO"
        sensor_reasons: List[str] = []
        relation_level = "BAJO"
        relation_reasons: List[str] = []
        if has_sensor_thresholds:
            context_row = {
                "dv_residual": _context_value(
                    context_series["dv_residual"], pos, default=None
                ),
                "mpg_active_pct": _context_value(
                    context_series["mpg_active_pct"], pos, default=None
                ),
                "tower_switches": _context_value(
                    context_series["tower_switches"], pos, default=None
                ),
            }
            sensor_level, sensor_reasons = _eval_sensor_rules(
                row=row,
                thresholds=thresholds,
                context_row=context_row,
            )
            relation_level, relation_reasons = _eval_relation_rules(
                row=row,
                thresholds=thresholds,
                context_row=context_row,
            )

        base_score = _safe_float(row.get("risk_score"), default=0.0)
        operational_score = _compute_operational_risk_score(
            base_score=base_score,
            sensor_level=sensor_level,
            relation_level=relation_level,
            sensor_trigger_count=len(sensor_reasons),
            relation_trigger_count=len(relation_reasons),
        )
        operational_level = _score_to_level(operational_score)

        final_level = _promote_level(risk_level, sensor_level)
        final_level = _promote_level(final_level, relation_level)
        final_level = _promote_level(final_level, operational_level)

        sources = []
        if risk_reasons:
            sources.append("riesgo")
        if sensor_reasons:
            sources.append("sensores")
        if relation_reasons:
            sources.append("relaciones")

        reasons = risk_reasons + sensor_reasons + relation_reasons
        if operational_score > (base_score + 0.02):
            reasons.append(
                f"risk_score_operational: ajuste de severidad eleva score de {base_score:.3f} a {operational_score:.3f}"
            )
        if not reasons:
            reasons = ["Sin condiciones de alerta activas."]

        alert_levels.append(final_level)
        alert_reasons.append(" | ".join(reasons))
        alert_sources.append("+".join(sources) if sources else "none")
        alert_trigger_count.append(
            len(risk_reasons) + len(sensor_reasons) + len(relation_reasons)
        )
        risk_scores_operational.append(operational_score)
        risk_levels_operational.append(operational_level)
        risk_score_deltas.append(float(operational_score - base_score))

    output["alert_level"] = alert_levels
    output["alert_sources"] = alert_sources
    output["alert_trigger_count"] = alert_trigger_count
    output["alert_reasons"] = alert_reasons
    output["risk_score_operational"] = risk_scores_operational
    output["risk_level_operational"] = risk_levels_operational
    output["risk_score_delta"] = risk_score_deltas

    meta = {
        "engine_version": "v2",
        "rows": int(len(output)),
        "threshold_source": threshold_source,
        "risk_threshold_medium": float(RISK_THRESHOLD_MEDIUM),
        "risk_threshold_high": float(RISK_THRESHOLD_HIGH),
        "uses_relation_rules": True,
        "uses_operational_score_adjustment": True,
    }
    if has_sensor_thresholds:
        meta["sensor_threshold_version"] = thresholds.get("version")
        meta["sensor_threshold_created_at"] = thresholds.get("created_at")
        meta["healthy_filter"] = thresholds.get("healthy_filter")
        meta["runtime_calibration"] = bool(thresholds.get("runtime_calibration"))
        meta["calibration_sample_rows"] = thresholds.get("calibration_sample_rows")

    return output, meta


def evaluate_latest_alert(
    df: pd.DataFrame,
    thresholds: Dict[str, Any] | None = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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
            {"engine_version": "v2-latest", "rows": 0, "threshold_source": "none"},
        )

    recent_df = df.tail(240).copy()
    latest = recent_df.iloc[-1]
    thresholds, threshold_source = resolve_alert_thresholds(df, thresholds)
    has_sensor_thresholds = bool(thresholds.get("sensors", {}))
    context_series = _build_context_series(recent_df, thresholds)

    risk_level, risk_reasons = _eval_risk_rules(latest)

    sensor_level = "BAJO"
    sensor_reasons: List[str] = []
    relation_level = "BAJO"
    relation_reasons: List[str] = []
    if has_sensor_thresholds:
        pos = len(recent_df) - 1
        context_row = {
            "dv_residual": _context_value(
                context_series["dv_residual"], pos, default=None
            ),
            "mpg_active_pct": _context_value(
                context_series["mpg_active_pct"], pos, default=None
            ),
            "tower_switches": _context_value(
                context_series["tower_switches"], pos, default=None
            ),
        }

        sensor_level, sensor_reasons = _eval_sensor_rules(
            row=latest,
            thresholds=thresholds,
            context_row=context_row,
        )
        relation_level, relation_reasons = _eval_relation_rules(
            row=latest,
            thresholds=thresholds,
            context_row=context_row,
        )

    final_level = _promote_level(risk_level, sensor_level)
    final_level = _promote_level(final_level, relation_level)

    base_score = _safe_float(latest.get("risk_score"), default=0.0)
    operational_score = _compute_operational_risk_score(
        base_score=base_score,
        sensor_level=sensor_level,
        relation_level=relation_level,
        sensor_trigger_count=len(sensor_reasons),
        relation_trigger_count=len(relation_reasons),
    )
    operational_level = _score_to_level(operational_score)
    final_level = _promote_level(final_level, operational_level)

    sources = []
    if risk_reasons:
        sources.append("riesgo")
    if sensor_reasons:
        sources.append("sensores")
    if relation_reasons:
        sources.append("relaciones")

    reasons = risk_reasons + sensor_reasons + relation_reasons
    if operational_score > (base_score + 0.02):
        reasons.append(
            f"risk_score_operational: ajuste de severidad eleva score de {base_score:.3f} a {operational_score:.3f}"
        )
    if not reasons:
        reasons = ["Sin condiciones de alerta activas."]

    latest_alert = {
        "alert_level": final_level,
        "alert_sources": "+".join(sources) if sources else "none",
        "alert_trigger_count": len(risk_reasons) + len(sensor_reasons) + len(relation_reasons),
        "alert_reasons": " | ".join(reasons),
        "risk_level": latest.get("risk_level"),
        "risk_score": latest.get("risk_score"),
        "risk_level_operational": operational_level,
        "risk_score_operational": operational_score,
        "risk_score_delta": float(operational_score - base_score),
        "timestamp": latest.get("timestamp"),
    }

    meta = {
        "engine_version": "v2-latest",
        "rows": int(len(df)),
        "threshold_source": threshold_source,
        "risk_threshold_medium": float(RISK_THRESHOLD_MEDIUM),
        "risk_threshold_high": float(RISK_THRESHOLD_HIGH),
        "uses_operational_score_adjustment": True,
    }
    if has_sensor_thresholds:
        meta["sensor_threshold_version"] = thresholds.get("version")
        meta["sensor_threshold_created_at"] = thresholds.get("created_at")
        meta["healthy_filter"] = thresholds.get("healthy_filter")
        meta["runtime_calibration"] = bool(thresholds.get("runtime_calibration"))
        meta["calibration_sample_rows"] = thresholds.get("calibration_sample_rows")

    return latest_alert, meta


def build_prediction_advisory(
    df: pd.DataFrame,
    thresholds: Dict[str, Any] | None = None,
    horizon_minutes: int = PREDICTION_HORIZON_MINUTES,
) -> Dict[str, Any]:
    """
    Proyeccion ligera de riesgo para avisos predictivos.
    Usa la pendiente reciente del risk_score y resume drivers activos.
    """
    if df is None or df.empty:
        return {
            "status": "sin_datos",
            "current_score": 0.0,
            "projected_score": 0.0,
            "projected_level": "BAJO",
            "minutes_to_medium": None,
            "minutes_to_high": None,
            "trend_direction": "estable",
            "confidence": 0,
            "message": "No hay datos suficientes para proyectar riesgo.",
            "drivers": [],
            "horizon_minutes": int(horizon_minutes),
        }

    recent = (
        df.dropna(subset=["timestamp", "risk_score"])
        .tail(180)
        .copy()
        .sort_values("timestamp")
    )
    score_col = "risk_score_operational" if "risk_score_operational" in recent.columns else "risk_score"
    if len(recent) < 5:
        current_score = _safe_float(df.iloc[-1].get(score_col), default=0.0)
        return {
            "status": "insuficiente",
            "current_score": current_score,
            "projected_score": current_score,
            "projected_level": str(df.iloc[-1].get("risk_level", "BAJO")).upper(),
            "minutes_to_medium": None,
            "minutes_to_high": None,
            "trend_direction": "estable",
            "confidence": 5,
            "message": "Se requieren mas puntos para generar una proyeccion confiable.",
            "drivers": [],
            "horizon_minutes": int(horizon_minutes),
        }

    elapsed_min = (
        (recent["timestamp"] - recent["timestamp"].iloc[0]).dt.total_seconds() / 60.0
    ).astype(float)
    current_score = _safe_float(recent[score_col].iloc[-1], default=0.0)

    if elapsed_min.max() <= 0:
        slope_per_min = 0.0
        projected_score = current_score
        r2 = 0.0
    else:
        slope_per_min, intercept = np.polyfit(elapsed_min, recent[score_col], 1)
        fitted = (slope_per_min * elapsed_min) + intercept
        residual = recent[score_col] - fitted
        ss_res = float((residual**2).sum())
        ss_tot = float(((recent[score_col] - recent[score_col].mean()) ** 2).sum())
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        projected_score = float(
            np.clip(current_score + (slope_per_min * horizon_minutes), 0.0, 1.0)
        )

    if projected_score >= RISK_THRESHOLD_HIGH:
        projected_level = "ALTO"
    elif projected_score >= RISK_THRESHOLD_MEDIUM:
        projected_level = "MEDIO"
    else:
        projected_level = "BAJO"

    delta_projection = projected_score - current_score
    if delta_projection > 0.03:
        trend_direction = "subiendo"
    elif delta_projection < -0.03:
        trend_direction = "bajando"
    else:
        trend_direction = "estable"

    minutes_to_medium = None
    minutes_to_high = None
    if slope_per_min > 0:
        if current_score < RISK_THRESHOLD_MEDIUM:
            minutes_to_medium = max(
                0, int(round((RISK_THRESHOLD_MEDIUM - current_score) / slope_per_min))
            )
        if current_score < RISK_THRESHOLD_HIGH:
            minutes_to_high = max(
                0, int(round((RISK_THRESHOLD_HIGH - current_score) / slope_per_min))
            )

    confidence = int(
        np.clip((abs(delta_projection) * 140.0) + (max(r2, 0.0) * 45.0), 8, 96)
    )
    latest_alert, _ = evaluate_latest_alert(recent, thresholds=thresholds)
    drivers = [
        chunk.strip()
        for chunk in str(latest_alert.get("alert_reasons", "")).split("|")
        if chunk.strip()
    ][:4]

    if projected_level == "ALTO":
        message = (
            f"Si la pendiente reciente se mantiene, el sistema podria entrar en ALTO "
            f"dentro del horizonte de {horizon_minutes} minutos."
        )
    elif projected_level == "MEDIO":
        message = (
            f"La tendencia reciente apunta a una ventana de observacion dentro del "
            f"horizonte de {horizon_minutes} minutos."
        )
    else:
        message = (
            f"La proyeccion a {horizon_minutes} minutos permanece en rango bajo, "
            f"con vigilancia sobre los drivers actuales."
        )

    return {
        "status": "ok",
        "current_score": current_score,
        "projected_score": projected_score,
        "projected_level": projected_level,
        "minutes_to_medium": minutes_to_medium,
        "minutes_to_high": minutes_to_high,
        "trend_direction": trend_direction,
        "confidence": confidence,
        "message": message,
        "drivers": drivers,
        "horizon_minutes": int(horizon_minutes),
        "slope_per_min": float(slope_per_min),
        "r2": float(r2),
        "projection_score_source": score_col,
        "alert_snapshot": latest_alert,
    }
