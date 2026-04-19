"""
Motor de acciones recomendadas (backend).

Este modulo desacopla la logica operacional del frontend:
- Lee una politica editable en JSON.
- Usa el resultado del motor de alertas para identificar nivel y causas.
- Devuelve acciones recomendadas por nivel global y por sensor activado.

Soporta dos formatos de acciones:
1) Basico: lista de strings
2) Expandido: lista de objetos con metadatos
   {text, responsable, canal, sla_min, priority, direction, when, id}
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import pandas as pd

from src.config import RECOMMENDATION_POLICY_PATH
from src.dashboard.utils.alert_engine import evaluate_latest_alert


SENSOR_KEYS = {
    "TP3_mean",
    "H1_mean",
    "DV_pressure_mean",
    "Motor_Current_mean",
    "MPG_last",
    "Oil_Temperature_mean",
    "TOWERS_last",
}


def _load_policy(path: str = RECOMMENDATION_POLICY_PATH) -> Dict[str, Any]:
    """
    Carga la politica de acciones desde archivo JSON.
    Si no existe o esta malformada, retorna estructura vacia segura.
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _extract_active_sensors(alert_reasons: str) -> List[str]:
    """
    Extrae sensores activados desde texto de razones de alerta.

    Formato esperado en alert_engine:
    - "TP3_mean: ... | risk_score: ... | DV_pressure_mean: ..."
    """
    if not isinstance(alert_reasons, str) or not alert_reasons.strip():
        return []

    active: List[str] = []
    for chunk in alert_reasons.split("|"):
        part = chunk.strip()
        if ":" not in part:
            continue
        prefix = part.split(":", 1)[0].strip()
        if prefix in SENSOR_KEYS and prefix not in active:
            active.append(prefix)
    return active


def _safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except Exception:
        return default


def _as_action_object(
    raw_action: Any,
    default_priority: int,
    default_responsable: str,
    default_canal: str,
    default_sla_min: int,
    source: str,
    level: str,
    sensor: str | None,
    seq: int,
) -> Dict[str, Any]:
    """
    Normaliza una accion a formato objeto.
    """
    if isinstance(raw_action, str):
        text = raw_action.strip()
        return {
            "id": f"{source}-{level}-{seq}",
            "text": text,
            "responsable": default_responsable,
            "canal": default_canal,
            "sla_min": default_sla_min,
            "priority": default_priority,
            "direction": "any",
            "when": "inmediato" if level == "ALTO" else "proxima_ventana",
            "source": source,
            "level": level,
            "sensor": sensor,
            "_seq": seq,
        }

    if isinstance(raw_action, dict):
        text = str(raw_action.get("text") or raw_action.get("accion") or "").strip()
        if not text:
            text = "Accion sin descripcion"

        return {
            "id": str(raw_action.get("id") or f"{source}-{level}-{seq}"),
            "text": text,
            "responsable": str(raw_action.get("responsable") or default_responsable),
            "canal": str(raw_action.get("canal") or default_canal),
            "sla_min": _safe_int(raw_action.get("sla_min"), default_sla_min),
            "priority": _safe_int(raw_action.get("priority"), default_priority),
            "direction": str(raw_action.get("direction") or "any"),
            "when": str(raw_action.get("when") or ("inmediato" if level == "ALTO" else "proxima_ventana")),
            "source": source,
            "level": level,
            "sensor": sensor,
            "_seq": seq,
        }

    return {
        "id": f"{source}-{level}-{seq}",
        "text": "Accion invalida en politica",
        "responsable": default_responsable,
        "canal": default_canal,
        "sla_min": default_sla_min,
        "priority": default_priority,
        "direction": "any",
        "when": "proxima_ventana",
        "source": source,
        "level": level,
        "sensor": sensor,
        "_seq": seq,
    }


def _normalize_action_list(
    raw_actions: Any,
    default_priority: int,
    default_responsable: str,
    default_canal: str,
    default_sla_min: int,
    source: str,
    level: str,
    sensor: str | None,
) -> List[Dict[str, Any]]:
    """
    Convierte string/list/dict a lista normalizada de acciones.
    """
    if raw_actions is None:
        return []

    if isinstance(raw_actions, (str, dict)):
        raw_actions = [raw_actions]

    if not isinstance(raw_actions, list):
        return []

    actions: List[Dict[str, Any]] = []
    for idx, raw_action in enumerate(raw_actions, start=1):
        actions.append(
            _as_action_object(
                raw_action=raw_action,
                default_priority=default_priority,
                default_responsable=default_responsable,
                default_canal=default_canal,
                default_sla_min=default_sla_min,
                source=source,
                level=level,
                sensor=sensor,
                seq=idx,
            )
        )
    return actions


def _dedupe_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Elimina duplicados preservando orden relativo.
    """
    seen = set()
    unique: List[Dict[str, Any]] = []

    for action in actions:
        key = (
            action.get("text", ""),
            action.get("responsable", ""),
            action.get("canal", ""),
            action.get("sensor", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(action)

    return unique


def _sort_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ordena por prioridad y secuencia.
    Menor prioridad = mas urgente.
    """
    return sorted(
        actions,
        key=lambda a: (
            _safe_int(a.get("priority"), 999),
            0 if a.get("source") == "global" else 1,
            _safe_int(a.get("_seq"), 999),
        ),
    )


def _fallback_global_actions(level: str) -> List[Dict[str, Any]]:
    if level == "ALTO":
        return [
            {
                "id": "fallback-alto-1",
                "text": "Detener operacion del tren.",
                "responsable": "Centro de control",
                "canal": "radio",
                "sla_min": 2,
                "priority": 1,
                "direction": "any",
                "when": "inmediato",
                "source": "global",
                "level": "ALTO",
                "sensor": None,
                "_seq": 1,
            },
            {
                "id": "fallback-alto-2",
                "text": "Notificar al equipo tecnico.",
                "responsable": "Mantenimiento",
                "canal": "correo",
                "sla_min": 5,
                "priority": 2,
                "direction": "any",
                "when": "inmediato",
                "source": "global",
                "level": "ALTO",
                "sensor": None,
                "_seq": 2,
            },
        ]

    if level == "MEDIO":
        return [
            {
                "id": "fallback-medio-1",
                "text": "Monitorear comportamiento y preparar mantenimiento preventivo.",
                "responsable": "Operacion",
                "canal": "panel",
                "sla_min": 30,
                "priority": 20,
                "direction": "any",
                "when": "proxima_ventana",
                "source": "global",
                "level": "MEDIO",
                "sensor": None,
                "_seq": 1,
            }
        ]

    return [
        {
            "id": "fallback-bajo-1",
            "text": "Operacion normal. Continuar monitoreo.",
            "responsable": "Operacion",
            "canal": "panel",
            "sla_min": 60,
            "priority": 100,
            "direction": "any",
            "when": "rutina",
            "source": "global",
            "level": "BAJO",
            "sensor": None,
            "_seq": 1,
        }
    ]


def get_latest_recommendations(
    df: pd.DataFrame,
    policy_path: str = RECOMMENDATION_POLICY_PATH,
) -> Dict[str, Any]:
    """
    Evalua alertas y construye recomendaciones para la ULTIMA ventana.

    Retorna:
    - level: ALTO/MEDIO/BAJO
    - timestamp
    - global_actions (lista de objetos)
    - sensor_actions (dict por sensor -> lista de objetos)
    - combined_actions (lista final ordenada)
    - active_sensors (sensores detectados en razones)
    - reasons
    - policy_loaded (bool)
    """
    if df is None or df.empty:
        return {
            "level": "BAJO",
            "timestamp": None,
            "global_actions": [],
            "sensor_actions": {},
            "combined_actions": [],
            "active_sensors": [],
            "reasons": "Sin datos.",
            "policy_loaded": False,
        }

    latest, _meta = evaluate_latest_alert(df)
    level = str(latest.get("alert_level", "BAJO")).upper()
    reasons = str(latest.get("alert_reasons", ""))
    active_sensors = _extract_active_sensors(reasons)

    policy = _load_policy(policy_path)
    policy_loaded = bool(policy)

    default_responsable = str(policy.get("default_responsable", "Operacion")) if policy_loaded else "Operacion"
    default_canal = str(policy.get("default_canal", "panel")) if policy_loaded else "panel"
    default_sla_min = _safe_int(policy.get("default_sla_min"), 30) if policy_loaded else 30

    global_actions_cfg = policy.get("global_actions", {}) if policy_loaded else {}
    sensor_actions_cfg = policy.get("sensor_actions", {}) if policy_loaded else {}

    raw_global_actions = global_actions_cfg.get(level)
    if raw_global_actions:
        global_actions = _normalize_action_list(
            raw_actions=raw_global_actions,
            default_priority=10,
            default_responsable=default_responsable,
            default_canal=default_canal,
            default_sla_min=default_sla_min,
            source="global",
            level=level,
            sensor=None,
        )
    else:
        global_actions = _fallback_global_actions(level)

    sensor_actions: Dict[str, List[Dict[str, Any]]] = {}
    for sensor in active_sensors:
        raw_sensor_actions = sensor_actions_cfg.get(sensor, {}).get(level, [])
        normalized_sensor_actions = _normalize_action_list(
            raw_actions=raw_sensor_actions,
            default_priority=25,
            default_responsable=default_responsable,
            default_canal=default_canal,
            default_sla_min=default_sla_min,
            source="sensor",
            level=level,
            sensor=sensor,
        )
        if normalized_sensor_actions:
            sensor_actions[sensor] = normalized_sensor_actions

    combined_actions: List[Dict[str, Any]] = []
    combined_actions.extend(global_actions)
    for sensor in active_sensors:
        combined_actions.extend(sensor_actions.get(sensor, []))

    combined_actions = _dedupe_actions(combined_actions)
    combined_actions = _sort_actions(combined_actions)

    # Limpieza de campo interno de orden.
    for action in combined_actions:
        action.pop("_seq", None)
    for action in global_actions:
        action.pop("_seq", None)
    for _sensor, actions in sensor_actions.items():
        for action in actions:
            action.pop("_seq", None)

    return {
        "level": level,
        "timestamp": latest.get("timestamp"),
        "global_actions": global_actions,
        "sensor_actions": sensor_actions,
        "combined_actions": combined_actions,
        "active_sensors": active_sensors,
        "reasons": reasons,
        "policy_loaded": policy_loaded,
        "policy_path": policy_path,
        "policy_version": policy.get("version") if policy_loaded else None,
    }
