from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.ui_kit import (
    chart_card,
    finance_card,
    kpi_card,
    page_header,
    section_title,
    status_card,
    table_card,
)
from src.dashboard.theme import RISK_THRESHOLDS
from src.dashboard.utils.alert_engine import evaluate_alerts, resolve_alert_thresholds

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

    color_map = {"ALTO": "#e74c3c", "MEDIO": "#f39c12", "BAJO": "#2ecc71"}
    fig = px.pie(
        dist,
        names="Nivel",
        values="Cantidad",
        color="Nivel",
        color_discrete_map=color_map,
        hole=0.48,
    )
    fig.update_traces(textinfo="none", hovertemplate="%{label}: %{value}<extra></extra>", sort=False)
    fig.update_traces(domain=dict(x=[0.12, 0.88], y=[0.12, 0.88]))
    fig.update_layout(
        height=200,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="white",
        showlegend=False,
    )
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
            line=dict(color="#234B8D", width=2.4),
            fill="tozeroy",
            fillcolor="rgba(35, 75, 141, 0.12)",
            hovertemplate="%{x}<br>Score: %{y:.3f}<extra></extra>",
        )
    )
    fig.add_hline(y=RISK_THRESHOLDS["MEDIO"], line_dash="dash", line_color="#f39c12")
    fig.add_hline(y=RISK_THRESHOLDS["ALTO"], line_dash="dash", line_color="#e74c3c")
    fig.update_layout(
        height=220,
        margin=dict(t=8, b=8, l=10, r=80),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(orientation="h", y=1.05, x=0),
    )
    fig.add_annotation(xref="paper", yref="y", x=1.10, y=RISK_THRESHOLDS["ALTO"], text="<b>ALTO</b>", showarrow=False, font=dict(color="#e74c3c", size=11))
    fig.add_annotation(xref="paper", yref="y", x=1.10, y=RISK_THRESHOLDS["MEDIO"], text="<b>MEDIO</b>", showarrow=False, font=dict(color="#f39c12", size=11))
    fig.add_annotation(xref="paper", yref="y", x=1.10, y=0.15, text="<b>BAJO</b>", showarrow=False, font=dict(color="#2ecc71", size=11))
    fig.update_yaxes(range=[0, 1], title_text="Risk score")
    fig.update_xaxes(showgrid=False)
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
    df = _df.copy().sort_values("timestamp")
    thresholds, _ = resolve_alert_thresholds(df)
    alert_df, _meta = evaluate_alerts(df.tail(2400), thresholds=thresholds)
    if alert_df is None:
        alert_df = pd.DataFrame()
    df, train_col = _with_train_id(df)
    latest_trains = _latest_per_train(df, train_col)

    latest_ts = pd.to_datetime(df["timestamp"].iloc[-1]) if "timestamp" in df.columns and not df.empty else None
    updated_label = latest_ts.strftime("Última actualización: %H:%M:%S") if latest_ts is not None else "Sin timestamp"
    page_header(
        "Estado General del Sistema",
        "Resumen actual de toda la operación: estado de trenes, riesgo global, impacto financiero y causas principales.",
        updated_text=updated_label,
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

    top_cols = st.columns([1.7, 0.9, 0.9, 0.9, 1.0], gap="medium")
    with top_cols[0]:
        status_card(
            "Estado actual",
            f"Riesgo {dominant_level}",
            dominant_level,
            metadata=f"Score de riesgo: {mean_risk:.3f} | Trenes analizados: {total_trains}",
        )
    with top_cols[1]:
        kpi_card("Trenes en Riesgo Alto", f"{high}/{total_trains}", f"{high_pct:.1f}%", icon="alert-circle", color="#e74c3c")
    with top_cols[2]:
        kpi_card("Trenes en Riesgo Medio", f"{medium}/{total_trains}", f"{medium_pct:.1f}%", icon="alert-triangle", color="#f39c12")
    with top_cols[3]:
        kpi_card("Trenes en Riesgo Bajo", f"{low}/{total_trains}", f"{low_pct:.1f}%", icon="check-circle", color="#2ecc71")
    with top_cols[4]:
        kpi_card("Salud Operativa Global", f"{health:.1f}/100", f"Disponibilidad {uptime:.1f}%", icon="activity", color="#234B8D")

    section_title(
        "Señales Clave del Sistema",
        "Promedios globales para evaluar disponibilidad, carga, temperatura y consumo.",
    )
    sensor_cols = [c for c in SENSOR_COLUMNS if c in df.columns]
    if sensor_cols:
        g1, g2, g3, g4 = st.columns(4, gap="medium")
        mean_vals = {c: float(pd.to_numeric(df[c], errors="coerce").mean()) for c in sensor_cols}
        with g1:
            kpi_card("Disponibilidad neumática", f"{mean_vals.get('TP3_mean', 0):.2f}", icon="gauge", color="#234B8D")
        with g2:
            kpi_card("Carga del sistema", f"{mean_vals.get('Motor_Current_mean', 0):.2f}", icon="cpu", color="#2ecc71")
        with g3:
            kpi_card("Condición térmica", f"{mean_vals.get('Oil_Temperature_mean', 0):.2f}", icon="thermometer", color="#f39c12")
        with g4:
            kpi_card("Consumo energético", f"{mean_vals.get('Motor_Current_mean', 0):.2f}", icon="zap", color="#FFE600")
    else:
        st.info("No hay columnas de sensores globales para mostrar señales doradas.")

    section_title(
        "Riesgo Operacional Global",
        "Comportamiento del riesgo agregado y cantidad de ventanas cr?ticas.",
    )
    c1, c2 = st.columns([1, 2], gap="medium")
    critical_windows = int((alert_df["alert_level"] == "ALTO").sum()) if "alert_level" in alert_df.columns else 0
    risk_level_text = "BAJO" if critical_windows == 0 else "MEDIO" if critical_windows < 10 else "ALTO"
    risk_level_color = "#2ecc71" if risk_level_text == "BAJO" else "#f39c12" if risk_level_text == "MEDIO" else "#e74c3c"

    with c1:
        pie = _risk_distribution_chart(df, train_col)
        if pie:
            center_color = "#2ecc71" if risk_level_text == "BAJO" else "#f39c12" if risk_level_text == "MEDIO" else "#e74c3c"
            pie.add_annotation(
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                text=f"<span style='font-size:20px;'><b>100%</b></span><br><span style='color:{center_color};font-size:12px;'>{risk_level_text}</span>",
                showarrow=False,
                font=dict(color="#121212", size=20),
                align="center",
            )
            with st.container(key="risk-left-card"):
                d1, d2 = st.columns([2, 1], gap="small")
                with d1:
                    st.markdown('<div style="display:flex;justify-content:center;align-items:center;height:100%;">', unsafe_allow_html=True)
                    st.plotly_chart(pie, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                with d2:
                    st.markdown(
                        f"""
                        <div style="height:200px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;">
                            <div style="font-size:13px;color:#7A8797;margin-bottom:6px;">Ventanas críticas</div>
                            <div style="font-size:32px;font-weight:700;line-height:1;color:#121212;margin-bottom:10px;">{critical_windows}</div>
                            <div style="display:flex;align-items:center;justify-content:center;gap:8px;">
                                <span style="width:10px;height:10px;border-radius:50%;background:{risk_level_color};display:inline-block;"></span>
                                <span style="font-size:14px;font-weight:600;color:#121212;">{risk_level_text.title()}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with c2:
        line = _risk_timeline_chart(df)
        if line:
            with st.container(key="risk-right-card"):
                st.markdown(
                    '<div style="font-size:13px;font-weight:600;color:#121212;margin:0 0 6px 0;">Evolución del Riesgo (últimos 10 días)</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(line, use_container_width=True)

    section_title("Impacto Financiero Global")
    fin = _global_financial(alert_df)
    f1, f2, f3 = st.columns(3, gap="medium")
    with f1:
        finance_card(
            title="Costo Reactivo",
            value=_money(fin["reactive_cost"]),
            description="Si no se actúa de forma preventiva",
            type="reactive",
        )
    with f2:
        finance_card(
            title="Costo Preventivo",
            value=_money(fin["preventive_cost"]),
            description="Escenario de mantenimiento planificado",
            type="preventive",
        )
    with f3:
        finance_card(
            title="Ahorro Estimado",
            value=_money(fin["savings"]),
            description="Beneficio de anticipar fallas",
            type="savings",
        )

    section_title(
        "Causas Recurrentes del Riesgo",
        "Sensores o factores que más activan alertas en toda la flota.",
    )
    drivers_df = _drivers_summary(alert_df)
    if not drivers_df.empty:
        table_card("Drivers de riesgo", drivers_df)
    else:
        st.info("No hay drivers globales disponibles aún.")

    section_title(
        "Estado por Tren",
        "Tabla resumida por tren para navegar al detalle operativo.",
    )
    train_table = latest_trains.copy()
    train_table["Estado"] = train_table["risk_level"]
    if "timestamp" in train_table.columns:
        train_table["Última alerta"] = pd.to_datetime(train_table["timestamp"]).astype(str)
    else:
        train_table["Última alerta"] = "-"
    train_table["Accion"] = "Abrir vista tren"
    view_cols = [train_col, "risk_score", "Estado", "Última alerta", "Accion"]
    rename_map = {train_col: "Tren", "risk_score": "Riesgo"}
    table_card("Estado actual de la flota", train_table[view_cols].rename(columns=rename_map))

    available = train_table[train_col].astype(str).tolist()
    selected = st.selectbox("Seleccionar tren para abrir vista detallada", available, index=0)
    if st.button("Abrir Vista Tren Operativa", use_container_width=False):
        st.session_state["selected_train_id"] = selected
        st.session_state["nav_view"] = "train_operational"
        st.rerun()
