from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from src.dashboard.components.financial_section import render_financial_section
from src.dashboard.theme import RISK_THRESHOLDS
from src.dashboard.utils.alert_engine import (
    build_prediction_advisory,
    evaluate_alerts,
    evaluate_latest_alert,
    resolve_alert_thresholds,
)
from src.dashboard.utils.recommendation_engine import get_latest_recommendations
from src.dashboard.views.ui_kit import (
    inject_operational_ui,
    render_level_badge,
    render_section_header,
    render_view_header,
)


SENSOR_COLUMNS = [
    "TP3_mean",
    "H1_mean",
    "DV_pressure_mean",
    "Motor_Current_mean",
    "MPG_last",
    "Oil_Temperature_mean",
    "TOWERS_last",
]

INPUT_KEYS = {
    "risk_score": "mt_risk_score",
    "TP3_mean": "mt_tp3",
    "H1_mean": "mt_h1",
    "DV_pressure_mean": "mt_dv",
    "Motor_Current_mean": "mt_motor",
    "MPG_last": "mt_mpg",
    "Oil_Temperature_mean": "mt_oil",
    "TOWERS_last": "mt_towers",
}


def _risk_level_from_score(score: float) -> str:
    if score >= RISK_THRESHOLDS["ALTO"]:
        return "ALTO"
    if score >= RISK_THRESHOLDS["MEDIO"]:
        return "MEDIO"
    return "BAJO"


def _safe_float(value, fallback=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(fallback)


def _next_timestamp(df: pd.DataFrame) -> pd.Timestamp:
    if "timestamp" in df.columns and not df.empty:
        return pd.to_datetime(df["timestamp"].iloc[-1]) + timedelta(minutes=5)
    return pd.Timestamp.now()


def _ensure_sandbox(base_df: pd.DataFrame) -> None:
    if "sandbox_df" not in st.session_state:
        st.session_state["sandbox_df"] = base_df.copy()
    if "sandbox_base_len" not in st.session_state:
        st.session_state["sandbox_base_len"] = int(len(base_df))
    if "sandbox_active" not in st.session_state:
        st.session_state["sandbox_active"] = False


def _init_inputs_from_reference(ref_df: pd.DataFrame) -> None:
    latest = ref_df.iloc[-1] if not ref_df.empty else pd.Series(dtype="object")

    defaults = {
        "risk_score": _safe_float(latest.get("risk_score", 0.20), 0.20),
        "TP3_mean": _safe_float(latest.get("TP3_mean", 9.0), 9.0),
        "H1_mean": _safe_float(latest.get("H1_mean", 9.0), 9.0),
        "DV_pressure_mean": _safe_float(latest.get("DV_pressure_mean", 0.0), 0.0),
        "Motor_Current_mean": _safe_float(latest.get("Motor_Current_mean", 0.1), 0.1),
        "MPG_last": _safe_float(latest.get("MPG_last", 0.0), 0.0),
        "Oil_Temperature_mean": _safe_float(latest.get("Oil_Temperature_mean", 60.0), 60.0),
        "TOWERS_last": _safe_float(latest.get("TOWERS_last", 0.0), 0.0),
    }

    for field, key in INPUT_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = defaults[field]


def _build_manual_row(sandbox_df: pd.DataFrame) -> pd.Series:
    latest = sandbox_df.iloc[-1].copy() if not sandbox_df.empty else pd.Series(dtype="object")

    score = _safe_float(st.session_state[INPUT_KEYS["risk_score"]], 0.20)
    latest["timestamp"] = _next_timestamp(sandbox_df)
    latest["risk_score"] = score
    latest["risk_level"] = _risk_level_from_score(score)

    for sensor in SENSOR_COLUMNS:
        latest[sensor] = _safe_float(st.session_state[INPUT_KEYS[sensor]], 0.0)

    return latest


def _append_manual_row() -> None:
    sandbox_df = st.session_state["sandbox_df"]
    row = _build_manual_row(sandbox_df)
    st.session_state["sandbox_df"] = pd.concat(
        [sandbox_df, pd.DataFrame([row])],
        ignore_index=True,
    )
    st.session_state["sandbox_active"] = True


def _remove_last_simulated_row() -> bool:
    sandbox_df = st.session_state["sandbox_df"]
    base_len = int(st.session_state.get("sandbox_base_len", 0))
    if len(sandbox_df) <= base_len:
        return False
    st.session_state["sandbox_df"] = sandbox_df.iloc[:-1].reset_index(drop=True)
    return True


def _reset_sandbox(base_df: pd.DataFrame) -> None:
    st.session_state["sandbox_df"] = base_df.copy()
    st.session_state["sandbox_base_len"] = int(len(base_df))
    st.session_state["sandbox_active"] = False


def _split_reasons(reason_text: str) -> list[str]:
    if not reason_text:
        return []
    reasons = []
    for part in str(reason_text).split("|"):
        clean = part.strip()
        if clean:
            reasons.append(clean)
    return reasons


def render(base_df: pd.DataFrame) -> None:
    inject_operational_ui()
    render_view_header(
        "Simulación Manual de Escenarios",
        "Prueba controlada sin afectar archivos ni base de datos. Ideal para validar respuestas del sistema.",
    )
    st.info("Modo de simulación seguro: no escribe en base de datos ni modifica archivos.")

    _ensure_sandbox(base_df)
    _init_inputs_from_reference(st.session_state["sandbox_df"])

    sandbox_df = st.session_state["sandbox_df"]
    base_len = int(st.session_state.get("sandbox_base_len", len(base_df)))

    enabled = st.toggle(
        "Usar sandbox en todo el dashboard",
        value=bool(st.session_state.get("sandbox_active", False)),
    )
    st.session_state["sandbox_active"] = enabled

    current_level = _risk_level_from_score(_safe_float(st.session_state[INPUT_KEYS["risk_score"]], 0.20))
    render_section_header("Estado Actual de Simulación", "Confirma si el dashboard está usando datos reales o simulados.")
    render_level_badge(current_level, _safe_float(st.session_state[INPUT_KEYS["risk_score"]], 0.20))

    if enabled:
        st.success("Sandbox activado: el dashboard usa la tabla simulada.")
    else:
        st.warning("Sandbox desactivado: el dashboard usa datos reales.")

    render_section_header("Configuración de Entrada Manual", "Edita variables operativas y agrega nuevas filas simuladas.")

    col1, col2 = st.columns(2)
    with col1:
        st.slider(
            "Risk Score",
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            key=INPUT_KEYS["risk_score"],
        )
    with col2:
        score = _safe_float(st.session_state[INPUT_KEYS["risk_score"]], 0.20)
        st.markdown(f"**Nivel calculado del escenario:** {_risk_level_from_score(score)}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("TP3_mean", format="%.4f", key=INPUT_KEYS["TP3_mean"])
    with c2:
        st.number_input("H1_mean", format="%.4f", key=INPUT_KEYS["H1_mean"])
    with c3:
        st.number_input("DV_pressure_mean", format="%.4f", key=INPUT_KEYS["DV_pressure_mean"])
    with c4:
        st.number_input("Motor_Current_mean", format="%.4f", key=INPUT_KEYS["Motor_Current_mean"])

    c5, c6, c7 = st.columns(3)
    with c5:
        st.number_input("MPG_last", format="%.4f", key=INPUT_KEYS["MPG_last"])
    with c6:
        st.number_input("Oil_Temperature_mean", format="%.4f", key=INPUT_KEYS["Oil_Temperature_mean"])
    with c7:
        st.number_input("TOWERS_last", format="%.4f", key=INPUT_KEYS["TOWERS_last"])

    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("Agregar entrada simulada", use_container_width=True):
            _append_manual_row()
            st.success("Entrada agregada al sandbox.")
            st.rerun()
    with a2:
        if st.button("Quitar última simulada", use_container_width=True):
            ok = _remove_last_simulated_row()
            if ok:
                st.success("Ultima entrada simulada removida.")
            else:
                st.info("No hay entradas simuladas para quitar.")
            st.rerun()
    with a3:
        if st.button("Reiniciar sandbox", use_container_width=True):
            _reset_sandbox(base_df)
            st.success("Sandbox reiniciado con datos reales.")
            st.rerun()

    sandbox_df = st.session_state["sandbox_df"]
    simulated_df = sandbox_df.iloc[base_len:].copy() if len(sandbox_df) > base_len else pd.DataFrame(columns=sandbox_df.columns)

    st.markdown("---")
    render_section_header("Métricas Clave de Simulación", "Resumen rápido del volumen de datos reales y simulados.")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Filas reales", len(base_df))
    with c2:
        st.metric("Filas sandbox", len(sandbox_df))
    with c3:
        st.metric("Filas simuladas", len(simulated_df))
    with c4:
        st.metric("Sandbox activo", "SI" if st.session_state.get("sandbox_active", False) else "NO")

    render_section_header("Vista Previa del Escenario", "Fila que se agregaría con la configuración actual (sin guardar).")
    preview = _build_manual_row(sandbox_df)
    show_cols = ["timestamp", "risk_score", "risk_level"] + [c for c in SENSOR_COLUMNS if c in sandbox_df.columns]
    st.dataframe(pd.DataFrame([preview])[show_cols], use_container_width=True)

    render_section_header(
        "Comparación Antes vs Después",
        "Impacto esperado del nuevo escenario sobre nivel de riesgo, causas activas y recomendación operativa.",
    )
    working_before = sandbox_df.copy().sort_values("timestamp")
    working_after = pd.concat([working_before, pd.DataFrame([preview])], ignore_index=True).sort_values("timestamp")

    thresholds_before, _ = resolve_alert_thresholds(working_before)
    latest_before, _ = evaluate_latest_alert(working_before.tail(2400), thresholds=thresholds_before)

    thresholds_after, _ = resolve_alert_thresholds(working_after)
    latest_after, _ = evaluate_latest_alert(working_after.tail(2400), thresholds=thresholds_after)
    pred_after = build_prediction_advisory(working_after.tail(2400), thresholds=thresholds_after)
    rec_after = get_latest_recommendations(working_after.tail(2400))

    before_level = str(latest_before.get("alert_level", "BAJO"))
    after_level = str(latest_after.get("alert_level", "BAJO"))
    before_score = float(working_before["risk_score"].iloc[-1]) if not working_before.empty else 0.0
    after_score = float(working_after["risk_score"].iloc[-1]) if not working_after.empty else before_score

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown("**Estado actual (antes)**")
        render_level_badge(before_level, before_score)
    with c2:
        st.markdown("**Estado simulado (después)**")
        render_level_badge(after_level, after_score)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Nivel de riesgo", f"{before_level} -> {after_level}")
    with m2:
        st.metric("Score de riesgo", f"{after_score:.3f}", f"{after_score - before_score:+.3f}")
    with m3:
        st.metric("Proyección 2h", pred_after["projected_level"], pred_after["trend_direction"].upper())

    before_reasons = set(_split_reasons(str(latest_before.get("alert_reasons", ""))))
    after_reasons = set(_split_reasons(str(latest_after.get("alert_reasons", ""))))
    activated = sorted([r for r in after_reasons if r not in before_reasons])

    d1, d2 = st.columns([1.1, 1.2], gap="medium")
    with d1:
        st.markdown("**Drivers activados por la simulación**")
        if activated:
            for item in activated[:8]:
                st.markdown(f"- {item}")
        else:
            st.caption("No se activaron drivers nuevos respecto al estado anterior.")
    with d2:
        st.markdown("**Recomendación resultante**")
        if rec_after["combined_actions"]:
            top_action = rec_after["combined_actions"][0]
            st.info(top_action.get("text", "Sin acción priorizada."))
        else:
            st.caption("No hay recomendaciones disponibles para el escenario actual.")

    render_section_header(
        "Impacto Financiero Simulado",
        "Estimación financiera para el escenario resultante usando el mismo motor del dashboard operativo.",
    )
    alerts_after_df, _ = evaluate_alerts(working_after.tail(2400), thresholds=thresholds_after)
    render_financial_section(alerts_after_df, pred_after)

    render_section_header("Historial de Entradas Simuladas", "Registro de los escenarios agregados en esta sesión.")
    if simulated_df.empty:
        st.info("Aun no hay entradas simuladas. Usa 'Agregar entrada simulada'.")
    else:
        st.dataframe(simulated_df[show_cols].tail(30).reset_index(drop=True), use_container_width=True)
