from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from src.dashboard.theme import RISK_THRESHOLDS


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


def render(base_df: pd.DataFrame) -> None:
    st.title("Prueba Manual (Sandbox)")
    st.markdown("---")
    st.info("Modo temporal para demo: no escribe en base de datos ni modifica archivos.")

    _ensure_sandbox(base_df)
    _init_inputs_from_reference(st.session_state["sandbox_df"])

    sandbox_df = st.session_state["sandbox_df"]
    base_len = int(st.session_state.get("sandbox_base_len", len(base_df)))

    enabled = st.toggle(
        "Usar sandbox en todo el dashboard",
        value=bool(st.session_state.get("sandbox_active", False)),
    )
    st.session_state["sandbox_active"] = enabled

    if enabled:
        st.success("Sandbox activado: el dashboard usa la tabla simulada.")
    else:
        st.warning("Sandbox desactivado: el dashboard usa datos reales.")

    st.markdown("### Entrada Manual")
    st.caption("Edita valores, luego pulsa 'Agregar entrada simulada' para acumular filas.")

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
        st.markdown(f"**Nivel calculado:** {_risk_level_from_score(score)}")

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
        if st.button("Quitar ultima simulada", use_container_width=True):
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
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Filas reales", len(base_df))
    with c2:
        st.metric("Filas sandbox", len(sandbox_df))
    with c3:
        st.metric("Filas simuladas", len(simulated_df))
    with c4:
        st.metric("Sandbox activo", "SI" if st.session_state.get("sandbox_active", False) else "NO")

    st.subheader("Vista previa de nueva fila (sin guardar)")
    preview = _build_manual_row(sandbox_df)
    show_cols = ["timestamp", "risk_score", "risk_level"] + [c for c in SENSOR_COLUMNS if c in sandbox_df.columns]
    st.dataframe(pd.DataFrame([preview])[show_cols], use_container_width=True)

    st.subheader("Tabla de entradas simuladas")
    if simulated_df.empty:
        st.info("Aun no hay entradas simuladas. Usa 'Agregar entrada simulada'.")
    else:
        st.dataframe(simulated_df[show_cols].tail(30).reset_index(drop=True), use_container_width=True)
