from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.cache_manager import load_dashboard_data
from src.dashboard.views.ui_kit import inject_operational_ui, render_section_header, render_view_header

TRAIN_ID_CANDIDATES = ["train_id", "train", "id_train", "apu_id", "engine_id"]


def _find_train_col(df: pd.DataFrame) -> Optional[str]:
    for c in TRAIN_ID_CANDIDATES:
        if c in df.columns:
            return c
    return None


def _with_train_id(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    col = _find_train_col(df)
    work = df.copy()
    if col is None:
        col = "train_id"
        work[col] = "001"
    work[col] = work[col].astype(str)
    return work, col


def _latest_per_train(df: pd.DataFrame, train_col: str) -> pd.DataFrame:
    return (
        df.sort_values("timestamp")
        .groupby(train_col, as_index=False)
        .tail(1)
        .sort_values("risk_score", ascending=False)
        .reset_index(drop=True)
    )


def _money(v: float) -> str:
    return f"COP {v:,.0f}"


def _financial(alert_df: pd.DataFrame) -> dict:
    if alert_df is None or alert_df.empty or "alert_level" not in alert_df.columns:
        return {"reactive_cost": 0.0, "preventive_cost": 0.0, "savings": 0.0}

    high = float((alert_df["alert_level"] == "ALTO").sum())
    medium = float((alert_df["alert_level"] == "MEDIO").sum())

    reactive = high * 8_000_000 + medium * 2_200_000
    preventive = high * 2_900_000 + medium * 1_100_000
    savings = max(0.0, reactive - preventive)
    return {"reactive_cost": reactive, "preventive_cost": preventive, "savings": savings}


def _risk_trend(df: pd.DataFrame):
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
            line=dict(color="#234B8D", width=2.7),
            fill="tozeroy",
            fillcolor="rgba(35,75,141,0.12)",
        )
    )
    fig.add_hline(y=0.4, line_dash="dash", line_color="#D5B700")
    fig.add_hline(y=0.7, line_dash="dash", line_color="#D32F2F")
    fig.update_layout(height=330, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="white", plot_bgcolor="white")
    fig.update_yaxes(range=[0, 1], title_text="Risk score")
    return fig


def _financial_chart(fin: dict):
    bars = pd.DataFrame(
        {
            "Concepto": ["Costo reactivo", "Costo preventivo", "Ahorro estimado"],
            "Valor": [fin["reactive_cost"], fin["preventive_cost"], fin["savings"]],
        }
    )
    fig = px.bar(
        bars,
        x="Concepto",
        y="Valor",
        color="Concepto",
        color_discrete_map={
            "Costo reactivo": "#D32F2F",
            "Costo preventivo": "#234B8D",
            "Ahorro estimado": "#D5B700",
        },
    )
    fig.update_layout(height=330, margin=dict(t=10, b=10, l=10, r=10), showlegend=False, paper_bgcolor="white", plot_bgcolor="white")
    return fig


def _drivers_table(alert_df: pd.DataFrame) -> pd.DataFrame:
    if alert_df is None or alert_df.empty or "alert_reasons" not in alert_df.columns:
        return pd.DataFrame(columns=["Causa", "Frecuencia"])

    counts: dict[str, int] = {}
    for raw in alert_df["alert_reasons"].astype(str).tolist():
        for part in [p.strip() for p in raw.split("|") if p.strip()]:
            key = part.split(":", 1)[0].replace("_mean", "").replace("_last", "")
            counts[key] = counts.get(key, 0) + 1

    rows = [{"Causa": k, "Frecuencia": v} for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)]
    return pd.DataFrame(rows).head(8)


def render(_df: pd.DataFrame) -> None:
    inject_operational_ui()
    data = load_dashboard_data()
    df = data["df"].copy().sort_values("timestamp")
    alert_df = data["alert_df"]

    df, train_col = _with_train_id(df)
    latest = _latest_per_train(df, train_col)

    total_trains = max(1, len(latest))
    high = int((latest["risk_level"] == "ALTO").sum())
    medium = int((latest["risk_level"] == "MEDIO").sum())
    low = int((latest["risk_level"] == "BAJO").sum())

    mean_risk = float(pd.to_numeric(latest["risk_score"], errors="coerce").fillna(0).mean())
    uptime = max(0.0, 100 - (high / total_trains) * 100 * 0.95)
    efficiency = max(0.0, 100 - mean_risk * 100)
    health = max(0.0, 100 - mean_risk * 80)

    fin = _financial(alert_df)

    render_view_header(
        "Resumen Ejecutivo",
        "Visión consolidada para toma de decisiones: estado de flota, impacto financiero y valor operativo del sistema.",
    )

    render_section_header("Estado Ejecutivo de la Flota", "Lectura rápida para liderazgo de operación y mantenimiento.")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Trenes monitoreados", f"{total_trains}")
    with k2:
        st.metric("Trenes en riesgo alto", f"{high}", f"{(high/max(1,total_trains))*100:.1f}%")
    with k3:
        st.metric("Disponibilidad global", f"{uptime:.1f}%")
    with k4:
        st.metric("Salud operativa", f"{health:.1f}/100", f"Eficiencia {efficiency:.1f}%")

    render_section_header("Impacto Financiero Consolidado", "Comparación entre escenario reactivo y preventivo en la flota.")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.metric("Costo reactivo estimado", _money(fin["reactive_cost"]))
    with f2:
        st.metric("Costo preventivo estimado", _money(fin["preventive_cost"]))
    with f3:
        st.metric("Ahorro total estimado", _money(fin["savings"]))

    c1, c2 = st.columns([1.3, 1.0], gap="medium")
    with c1:
        fig = _financial_chart(fin)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        trend = _risk_trend(df)
        if trend:
            st.plotly_chart(trend, use_container_width=True)

    render_section_header("Valor Operativo del Sistema", "Efecto directo en continuidad operativa y reducción de exposición al riesgo.")
    st.markdown(
        """
        - Menor exposición a fallas no planificadas gracias a alertamiento temprano.
        - Priorización de mantenimiento según severidad y tendencia de riesgo.
        - Mejor asignación de recursos al enfocarse en trenes con mayor criticidad.
        """
    )

    render_section_header("Causas Recurrentes de Riesgo", "Principales factores que explican la mayoría de alertas en la flota.")
    drivers = _drivers_table(alert_df)
    if drivers.empty:
        st.info("Aún no hay causas recurrentes para mostrar.")
    else:
        st.dataframe(drivers, use_container_width=True, hide_index=True)
