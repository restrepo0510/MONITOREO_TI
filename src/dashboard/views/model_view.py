"""
Vista del Modelo Predictivo — Autoencoder de Detección de Anomalías.

Muestra:
- KPIs de anomalía detectada por el modelo
- Línea temporal de error de reconstrucción vs umbral
- Error medio por sensor (diagnóstico de causa)
- Comparación entre ae_anomaly y risk_level del pipeline
- Distribución del error de reconstrucción
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.theme import PALETTE
from src.dashboard.views.ui_kit import (
    inject_operational_ui,
    render_section_header,
    render_view_header,
)

_AE_SENSOR_COLS_MAP = {
    "TP2": "TP2",
    "TP3": "TP3",
    "H1": "H1",
    "DV_pressure": "DV_pressure",
    "Reservoirs": "Reservoirs",
    "Oil_temperature": "Aceite Temp",
    "Motor_current": "Motor Corr",
    "COMP": "COMP",
    "DV_eletric": "DV Elec",
    "Towers": "Torres",
    "MPG": "MPG",
    "LPS": "LPS",
    "Oil_level": "Nivel Aceite",
    "Caudal_impulses": "Caudal",
}


def _has_ae_data(df: pd.DataFrame) -> bool:
    return "ae_reconstruction_error" in df.columns


def _sensor_error_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("ae_err_")]


def _build_error_timeline(df: pd.DataFrame) -> go.Figure:
    work = df.tail(1440).copy().sort_values("timestamp")
    threshold = float(work["ae_threshold"].iloc[-1]) if "ae_threshold" in work.columns else None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=work["timestamp"],
            y=work["ae_reconstruction_error"],
            mode="lines",
            name="Error de reconstrucción",
            line=dict(color=PALETTE["steel_azure"], width=2.2),
            fill="tozeroy",
            fillcolor="rgba(35, 75, 141, 0.10)",
            hovertemplate="%{x}<br>Error %{y:.6f}<extra></extra>",
        )
    )

    if threshold is not None:
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color=PALETTE["alert_red"],
            annotation_text=f"Umbral ({threshold:.6f})",
            annotation_position="top right",
        )

    anomaly_mask = work.get("ae_anomaly", pd.Series(False, index=work.index))
    anomalies = work[anomaly_mask]
    if not anomalies.empty:
        fig.add_trace(
            go.Scatter(
                x=anomalies["timestamp"],
                y=anomalies["ae_reconstruction_error"],
                mode="markers",
                name="Anomalía detectada",
                marker=dict(color=PALETTE["alert_red"], size=7, line=dict(color="white", width=0.8)),
                hovertemplate="%{x}<br>Error %{y:.6f}<extra></extra>",
            )
        )

    fig.update_layout(
        height=340,
        margin=dict(t=18, b=10, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0F1E3C"),
        legend=dict(orientation="h", y=1.10, x=0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(35, 75, 141, 0.09)")
    return fig


def _build_sensor_error_bar(df: pd.DataFrame) -> go.Figure | None:
    err_cols = _sensor_error_cols(df)
    if not err_cols:
        return None

    means = df[err_cols].mean().sort_values(ascending=True)
    labels = [
        _AE_SENSOR_COLS_MAP.get(c.replace("ae_err_", ""), c.replace("ae_err_", ""))
        for c in means.index
    ]

    fig = px.bar(
        x=means.values,
        y=labels,
        orientation="h",
        color=means.values,
        color_continuous_scale=["#D7E2F5", "#4A76BE", "#173A73"],
        labels={"x": "Error medio", "y": "Sensor"},
    )
    fig.update_layout(
        height=340,
        margin=dict(t=12, b=12, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        coloraxis_showscale=False,
        font=dict(color="#0F1E3C"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(35, 75, 141, 0.08)")
    fig.update_yaxes(showgrid=False)
    return fig


def _build_ae_vs_risk(df: pd.DataFrame) -> go.Figure | None:
    if "risk_score" not in df.columns or "ae_score" not in df.columns:
        return None
    work = df.tail(1440).copy().sort_values("timestamp")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=work["timestamp"],
            y=work["risk_score"],
            mode="lines",
            name="Risk score (pipeline)",
            line=dict(color=PALETTE["steel_azure"], width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=work["timestamp"],
            y=work["ae_score"],
            mode="lines",
            name="Score autoencoder",
            line=dict(color="#D5B700", width=2, dash="dot"),
        )
    )
    fig.update_layout(
        height=280,
        margin=dict(t=18, b=10, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0F1E3C"),
        legend=dict(orientation="h", y=1.12, x=0),
    )
    fig.update_yaxes(range=[0, 1], showgrid=True, gridcolor="rgba(35, 75, 141, 0.09)")
    fig.update_xaxes(showgrid=False)
    return fig


def _build_error_histogram(df: pd.DataFrame) -> go.Figure:
    threshold = float(df["ae_threshold"].iloc[-1]) if "ae_threshold" in df.columns else None
    fig = px.histogram(
        df,
        x="ae_reconstruction_error",
        nbins=60,
        color_discrete_sequence=[PALETTE["steel_azure"]],
        labels={"ae_reconstruction_error": "Error de reconstrucción"},
    )
    if threshold is not None:
        fig.add_vline(
            x=threshold,
            line_dash="dash",
            line_color=PALETTE["alert_red"],
            annotation_text="Umbral",
            annotation_position="top right",
        )
    fig.update_layout(
        height=260,
        margin=dict(t=12, b=10, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0F1E3C"),
    )
    return fig


def render(df: pd.DataFrame) -> None:
    inject_operational_ui()
    render_view_header(
        "Modelo Predictivo — Autoencoder",
        "Detección de anomalías mediante error de reconstrucción. ROC-AUC 0.87 | F1 0.71 | Precision media 0.94",
    )

    if not _has_ae_data(df):
        st.warning(
            "No hay datos del autoencoder disponibles. "
            "Ejecuta el pipeline completo para generar autoencoder_scores.parquet."
        )
        st.code("python -m src.pipeline.run_pipeline", language="bash")
        return

    work = df.dropna(subset=["ae_reconstruction_error"]).copy()
    threshold = float(work["ae_threshold"].iloc[-1]) if "ae_threshold" in work.columns else 0.0
    anomaly_count = int(work["ae_anomaly"].sum()) if "ae_anomaly" in work.columns else 0
    total = len(work)
    anomaly_pct = (anomaly_count / total * 100) if total > 0 else 0.0
    mean_error = float(work["ae_reconstruction_error"].mean())
    top_sensor = (
        work["ae_top_sensor"].value_counts().index[0]
        if "ae_top_sensor" in work.columns and not work["ae_top_sensor"].empty
        else "N/A"
    )
    top_sensor_label = _AE_SENSOR_COLS_MAP.get(top_sensor, top_sensor)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Ventanas analizadas", f"{total:,}")
    with k2:
        st.metric("Anomalías detectadas", f"{anomaly_count:,}", f"{anomaly_pct:.1f}% del total")
    with k3:
        st.metric("Error medio reconstrucción", f"{mean_error:.6f}", f"Umbral {threshold:.6f}")
    with k4:
        st.metric("Sensor más anómalo", top_sensor_label)

    render_section_header(
        "Error de Reconstrucción en el Tiempo",
        "Línea temporal del error del autoencoder. Las marcas rojas superan el umbral de anomalía.",
    )
    st.plotly_chart(_build_error_timeline(work), use_container_width=True)

    render_section_header(
        "Diagnóstico por Sensor",
        "Error medio de reconstrucción por sensor. Permite identificar qué variable genera más anomalía.",
    )
    col_bar, col_hist = st.columns([1.3, 1.0], gap="medium")
    with col_bar:
        bar_fig = _build_sensor_error_bar(work)
        if bar_fig:
            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.info("No hay columnas de error por sensor disponibles.")
    with col_hist:
        st.plotly_chart(_build_error_histogram(work), use_container_width=True)

    render_section_header(
        "Comparación: Autoencoder vs Pipeline",
        "Score del autoencoder (amarillo) vs risk_score del pipeline estadístico (azul). Valores altos en ambos indican mayor certeza.",
    )
    cmp_fig = _build_ae_vs_risk(work)
    if cmp_fig:
        st.plotly_chart(cmp_fig, use_container_width=True)
    else:
        st.info("Datos de risk_score o ae_score no disponibles para comparación.")

    render_section_header(
        "Ventanas con Anomalía Detectada",
        "Detalle de ventanas donde el error supera el umbral del modelo.",
    )
    if "ae_anomaly" in work.columns:
        anomaly_df = work[work["ae_anomaly"]].sort_values("timestamp", ascending=False)
        show_cols = ["timestamp", "ae_reconstruction_error", "ae_score", "ae_top_sensor"]
        if "risk_score" in anomaly_df.columns:
            show_cols.append("risk_score")
        if "risk_level" in anomaly_df.columns:
            show_cols.append("risk_level")
        show_cols = [c for c in show_cols if c in anomaly_df.columns]
        if anomaly_df.empty:
            st.success("No se detectaron anomalías en el rango de datos disponible.")
        else:
            st.dataframe(anomaly_df[show_cols].head(80).reset_index(drop=True), use_container_width=True, height=320)

    st.caption(
        f"Modelo: Dense Autoencoder | Arquitectura: Input(14)→64→32→8→32→64→Output(14) | "
        f"Umbral: {threshold:.8f} | Entrenado con LOFO 4-fold | "
        f"ROC-AUC: 0.87 ± 0.16 | F1: 0.71 ± 0.33"
    )
