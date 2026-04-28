from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.realtime_indicators import render_impact_card
from src.dashboard.theme import RISK_THRESHOLDS
from src.dashboard.utils.alert_engine import evaluate_alerts, resolve_alert_thresholds
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
    "Oil_Temperature_mean",
    "TOWERS_last",
]

TRAIN_ID_CANDIDATES = ["train_id", "train", "id_train", "apu_id", "engine_id"]


def _find_train_col(df: pd.DataFrame) -> Optional[str]:
    for c in TRAIN_ID_CANDIDATES:
        if c in df.columns:
            return c
    return None


def _with_train_id(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    train_col = _find_train_col(df)
    work = df.copy()
    if train_col is None:
        train_col = "train_id"
        work[train_col] = "001"
    work[train_col] = work[train_col].astype(str)
    return work, train_col


def _latest_per_train(df: pd.DataFrame, train_col: str) -> pd.DataFrame:
    return (
        df.sort_values("timestamp")
        .groupby(train_col, as_index=False)
        .tail(1)
        .sort_values("risk_score", ascending=False)
        .reset_index(drop=True)
    )


def _global_financial(alert_df: pd.DataFrame) -> dict:
    if alert_df is None or alert_df.empty or "alert_level" not in alert_df.columns:
        return {"reactive_cost": 0.0, "preventive_cost": 0.0, "savings": 0.0}

    high = float((alert_df["alert_level"] == "ALTO").sum())
    medium = float((alert_df["alert_level"] == "MEDIO").sum())

    reactive_cost = high * 8_000_000 + medium * 2_200_000
    preventive_cost = high * 2_900_000 + medium * 1_100_000
    savings = max(0.0, reactive_cost - preventive_cost)
    return {
        "reactive_cost": reactive_cost,
        "preventive_cost": preventive_cost,
        "savings": savings,
    }


def _money(v: float) -> str:
    return f"COP {v:,.0f}"


def _risk_distribution_chart(df: pd.DataFrame, train_col: str):
    dist = (
        _latest_per_train(df, train_col)["risk_level"]
        .value_counts()
        .rename_axis("Nivel")
        .reset_index(name="Cantidad")
    )
    if dist.empty:
        return None
    color_map = {"ALTO": "#D32F2F", "MEDIO": "#F39C12", "BAJO": "#2ECC71"}
    fig = px.pie(
        dist,
        names="Nivel",
        values="Cantidad",
        color="Nivel",
        color_discrete_map=color_map,
        hole=0.48,
    )
    fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
    return fig


def _risk_timeline_chart(df: pd.DataFrame):
    work = df.copy().sort_values("timestamp")
    work["timestamp_hour"] = pd.to_datetime(work["timestamp"]).dt.floor("h")
    series = work.groupby("timestamp_hour", as_index=False)["risk_score"].mean().tail(240)
    if series.empty:
        return None
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=series["timestamp_hour"],
            y=series["risk_score"],
            mode="lines",
            name="Riesgo global",
            line=dict(color="#234B8D", width=2.6),
            fill="tozeroy",
            fillcolor="rgba(35,75,141,0.12)",
        )
    )
    fig.add_hline(y=RISK_THRESHOLDS["MEDIO"], line_dash="dash", line_color="#F1C40F")
    fig.add_hline(y=RISK_THRESHOLDS["ALTO"], line_dash="dash", line_color="#E74C3C")
    fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
    fig.update_yaxes(range=[0, 1], title_text="Risk score")
    return fig


def _drivers_summary(alert_df: pd.DataFrame) -> pd.DataFrame:
    if alert_df is None or alert_df.empty or "alert_reasons" not in alert_df.columns:
        return pd.DataFrame(columns=["Driver", "Frecuencia"])

    counts: dict[str, int] = {}
    for raw in alert_df["alert_reasons"].astype(str).tolist():
        parts = [p.strip() for p in raw.split("|") if p.strip()]
        for p in parts:
            key = p.split(":", 1)[0].replace("_mean", "").replace("_last", "")
            counts[key] = counts.get(key, 0) + 1

    rows = [{"Driver": k, "Frecuencia": v} for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)]
    return pd.DataFrame(rows).head(8)


def render(_df: pd.DataFrame) -> None:
    inject_operational_ui()
    df = _df.copy().sort_values("timestamp")
    thresholds, _ = resolve_alert_thresholds(df)
    alert_df, _meta = evaluate_alerts(df.tail(2400), thresholds=thresholds)
    if alert_df is None:
        alert_df = pd.DataFrame()
    df, train_col = _with_train_id(df)
    latest_trains = _latest_per_train(df, train_col)

    render_view_header(
        "Estado General del Sistema",
        "Resumen actual de toda la operacion: estado de trenes, riesgo global, impacto financiero y causas principales.",
    )

    total_trains = max(1, len(latest_trains))
    high = int((latest_trains["risk_level"] == "ALTO").sum())
    medium = int((latest_trains["risk_level"] == "MEDIO").sum())
    low = int((latest_trains["risk_level"] == "BAJO").sum())
    high_pct = (high / total_trains) * 100
    medium_pct = (medium / total_trains) * 100
    low_pct = (low / total_trains) * 100

    mean_risk = float(pd.to_numeric(latest_trains["risk_score"], errors="coerce").fillna(0).mean())
    uptime = float(max(0.0, 100 - high_pct * 0.95))
    health = float(max(0.0, 100 - mean_risk * 80))
    dominant_level = "ALTO" if high > 0 else "MEDIO" if medium > 0 else "BAJO"

    render_section_header("Estado Actual del Sistema", "Distribucion de severidad por tren en este momento.")
    render_level_badge(dominant_level, mean_risk, f"| Trenes analizados: {total_trains}")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Trenes en Riesgo Alto", f"{high}/{total_trains}", f"{high_pct:.1f}%")
    with k2:
        st.metric("Trenes en Riesgo Medio", f"{medium}/{total_trains}", f"{medium_pct:.1f}%")
    with k3:
        st.metric("Trenes en Riesgo Bajo", f"{low}/{total_trains}", f"{low_pct:.1f}%")
    with k4:
        st.metric("Salud Operativa Global", f"{health:.1f}/100", f"Disponibilidad {uptime:.1f}%")

    render_section_header("Señales Clave del Sistema", "Promedios globales para evaluar disponibilidad, carga, temperatura y consumo.")
    cols = [c for c in SENSOR_COLUMNS if c in df.columns]
    if cols:
        g1, g2, g3, g4 = st.columns(4)
        mean_vals = {c: float(pd.to_numeric(df[c], errors="coerce").mean()) for c in cols}
        with g1:
            st.metric("Disponibilidad neumática", f"{mean_vals.get('TP3_mean', 0):.2f}")
        with g2:
            st.metric("Carga del sistema", f"{mean_vals.get('Motor_Current_mean', 0):.2f}")
        with g3:
            st.metric("Condición térmica", f"{mean_vals.get('Oil_Temperature_mean', 0):.2f}")
        with g4:
            st.metric("Consumo energético", f"{mean_vals.get('Motor_Current_mean', 0):.2f}")
    else:
        st.info("No hay columnas de sensores globales para mostrar senales doradas.")

    render_section_header("Riesgo Operacional Global", "Comportamiento del riesgo agregado y cantidad de ventanas críticas.")
    c1, c2 = st.columns([1, 2], gap="medium")
    with c1:
        pie = _risk_distribution_chart(df, train_col)
        if pie:
            st.plotly_chart(pie, use_container_width=True)
    with c2:
        line = _risk_timeline_chart(df)
        if line:
            st.plotly_chart(line, use_container_width=True)
        critical_windows = int((alert_df["alert_level"] == "ALTO").sum()) if "alert_level" in alert_df.columns else 0
        st.caption(f"Ventanas criticas totales: {critical_windows}")

    render_section_header("Impacto Financiero Global", "Comparación entre costo reactivo, costo preventivo y ahorro estimado.")
    fin = _global_financial(alert_df)
    f1, f2, f3 = st.columns(3)
    with f1:
        render_impact_card(
            title="Costo reactivo",
            impact_value=_money(fin["reactive_cost"]),
            impact_unit="",
            description="Si no se actua de forma preventiva",
            icon="",
        )
    with f2:
        render_impact_card(
            title="Costo preventivo",
            impact_value=_money(fin["preventive_cost"]),
            impact_unit="",
            description="Escenario de mantenimiento planificado",
            icon="",
        )
    with f3:
        render_impact_card(
            title="Ahorro estimado",
            impact_value=_money(fin["savings"]),
            impact_unit="",
            description="Beneficio de anticipar fallas",
            icon="",
        )

    render_section_header("Causas Recurrentes del Riesgo", "Sensores o factores que más activan alertas en toda la flota.")
    drivers_df = _drivers_summary(alert_df)
    if not drivers_df.empty:
        st.dataframe(drivers_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay drivers globales disponibles aun.")

    render_section_header("Estado por Tren", "Tabla resumida por tren para navegar al detalle operativo.")
    train_table = latest_trains.copy()
    train_table["Estado"] = train_table["risk_level"]
    if "timestamp" in train_table.columns:
        train_table["Ultima alerta"] = pd.to_datetime(train_table["timestamp"]).astype(str)
    else:
        train_table["Ultima alerta"] = "-"
    train_table["Accion"] = "Abrir vista tren"
    view_cols = [train_col, "risk_score", "Estado", "Ultima alerta", "Accion"]
    rename_map = {train_col: "Tren", "risk_score": "Riesgo"}
    st.dataframe(train_table[view_cols].rename(columns=rename_map), use_container_width=True, hide_index=True)

    available = train_table[train_col].astype(str).tolist()
    selected = st.selectbox("Seleccionar tren para abrir vista detallada", available, index=0)
    if st.button("Abrir Vista Tren Operativa", use_container_width=False):
        st.session_state["selected_train_id"] = selected
        st.session_state["nav_view"] = "train_operational"
        st.rerun()
