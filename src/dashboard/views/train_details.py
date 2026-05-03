import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.dashboard.theme import PALETTE, RISK_THRESHOLDS
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
    "MPG_last",
    "Oil_Temperature_mean",
    "TOWERS_last",
]


def _available_sensors(df: pd.DataFrame) -> list[str]:
    return [c for c in SENSOR_COLUMNS if c in df.columns]


def _correlation_heatmap(df_f: pd.DataFrame, sensors: list[str]):
    if len(sensors) < 2:
        return None
    corr = df_f[sensors].apply(pd.to_numeric, errors="coerce").corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale=["#1E3A8A", "#E0E7FF", "#DC1F26"],
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig.update_layout(
        height=420,
        margin=dict(t=30, b=30, l=120, r=30),
        paper_bgcolor="#FAFAFA",
        plot_bgcolor="#FAFAFA",
        title_text="Matriz de Correlación de Sensores",
        title_font=dict(size=14, color="#1F2937", family="Arial Black"),
        coloraxis_colorbar=dict(
            title="Correlación",
            thicknessmode="pixels", thickness=20,
            lenmode="pixels", len=300,
        ),
        font=dict(family="Arial, sans-serif", size=11, color="#374151"),
    )
    return fig


def _pre_alert_pattern(df_f: pd.DataFrame, sensors: list[str]) -> pd.DataFrame:
    thresholds, _ = resolve_alert_thresholds(df_f)
    alerts_df, _ = evaluate_alerts(df_f.tail(3600), thresholds=thresholds)
    if alerts_df is None or alerts_df.empty or "alert_level" not in alerts_df.columns:
        return pd.DataFrame(columns=["Sensor", "Promedio base", "Promedio en ALTO", "Variacion %"])

    base_df = alerts_df[alerts_df["alert_level"] == "BAJO"]
    high_df = alerts_df[alerts_df["alert_level"] == "ALTO"]
    if base_df.empty or high_df.empty:
        return pd.DataFrame(columns=["Sensor", "Promedio base", "Promedio en ALTO", "Variacion %"])

    rows = []
    for s in sensors:
        base_val = pd.to_numeric(base_df[s], errors="coerce").mean()
        high_val = pd.to_numeric(high_df[s], errors="coerce").mean()
        if pd.isna(base_val) or pd.isna(high_val):
            continue
        var_pct = ((high_val - base_val) / base_val * 100) if base_val != 0 else 0.0
        rows.append(
            {
                "Sensor": s,
                "Promedio base": float(base_val),
                "Promedio en ALTO": float(high_val),
                "Variacion %": float(var_pct),
            }
        )
    return pd.DataFrame(rows).sort_values("Variacion %", ascending=False)


def render(df):
    inject_operational_ui()
    render_view_header(
        "Detalle de Señales del Sistema",
        "Análisis temporal del riesgo con filtros por fecha para revisión operacional.",
    )
    latest = df.sort_values("timestamp").iloc[-1]
    render_level_badge(str(latest["risk_level"]).upper(), float(latest["risk_score"]))

    render_section_header("Rango de Análisis", "Selecciona el periodo de tiempo que deseas revisar.")
    col1, col2 = st.columns(2)
    with col1:
        fecha_ini = st.date_input("Desde", value=df["timestamp"].min().date())
    with col2:
        fecha_fin = st.date_input("Hasta", value=df["timestamp"].max().date())

    mask = (df["timestamp"].dt.date >= fecha_ini) & \
           (df["timestamp"].dt.date <= fecha_fin)
    df_f = df[mask]

    if df_f.empty:
        st.warning("No hay datos en el rango seleccionado.")
        return

    render_section_header(
        "Riesgo Operacional en el Tiempo",
        f"Visualización del score de riesgo para {len(df_f):,} ventanas dentro del rango seleccionado.",
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_f["timestamp"], 
        y=df_f["risk_score"],
        mode="lines", 
        name="Risk Score",
        line=dict(color="#1E3A8A", width=3),
        fill="tozeroy", 
        fillcolor="rgba(30, 58, 138, 0.15)",
        hovertemplate="<b>Tiempo:</b> %{x}<br><b>Risk Score:</b> %{y:.2%}<extra></extra>",
    ))
    fig.add_hline(
        y=RISK_THRESHOLDS["MEDIO"],
        line_dash="dash",
        line_color="#F59E0B",
        line_width=2.2,
        annotation_text=f"Umbral MEDIO: {RISK_THRESHOLDS['MEDIO']:.0%}",
        annotation_position="right",
        annotation_font=dict(size=11, color="#D97706", family="Arial Black"),
    )
    fig.add_hline(
        y=RISK_THRESHOLDS["ALTO"],
        line_dash="dot",
        line_color="#DC1F26",
        line_width=2.4,
        annotation_text=f"Umbral ALTO: {RISK_THRESHOLDS['ALTO']:.0%}",
        annotation_position="right",
        annotation_font=dict(size=11, color="#7F1D1D", family="Arial Black"),
    )
    fig.update_layout(
        height=420,
        margin=dict(t=30, b=30, l=20, r=150),
        paper_bgcolor="#FAFAFA",
        plot_bgcolor="#FAFAFA",
        xaxis_title="Timestamp",
        yaxis_title="Risk Score (%)",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="#E5E7EB",
            tickfont=dict(size=10, color="#6B7280"),
        ),
        yaxis=dict(
            range=[0, 1],
            showgrid=True,
            gridwidth=0.8,
            gridcolor="rgba(209, 213, 219, 0.5)",
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="#E5E7EB",
            tickfont=dict(size=10, color="#6B7280"),
            tickformat=".0%",
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial",
        ),
        font=dict(family="Arial, sans-serif", color="#374151"),
    )
    st.plotly_chart(fig, use_container_width=True)

    render_section_header("Detalle de Ventanas Analizadas", "Listado ordenado para inspección y trazabilidad de eventos.")
    st.dataframe(
        df_f[["timestamp", "risk_score", "risk_level"]]
          .sort_values("risk_score", ascending=False)
          .reset_index(drop=True),
        use_container_width=True,
        height=300
    )

    sensors = _available_sensors(df_f)
    render_section_header(
        "Correlaciones Relevantes de Señales",
        "Relación entre sensores clave para identificar comportamientos conjuntos previos a degradación.",
    )
    if len(sensors) < 2:
        st.info("No hay suficientes sensores disponibles para calcular correlaciones.")
    else:
        heat = _correlation_heatmap(df_f, sensors)
        if heat:
            st.plotly_chart(heat, use_container_width=True)

    render_section_header(
        "Patrones Previos a Riesgo Alto",
        "Comparación de comportamiento promedio en estado base versus ventanas de riesgo ALTO.",
    )
    pattern_df = _pre_alert_pattern(df_f, sensors)
    if pattern_df.empty:
        st.info("No hay suficientes eventos ALTO/BAJO en este rango para estimar patrones previos.")
    else:
        st.dataframe(pattern_df, use_container_width=True, hide_index=True)

    render_section_header(
        "Comparación de Sensores Clave",
        "Tendencia reciente de sensores seleccionados para análisis técnico puntual.",
    )
    if sensors:
        selected = st.multiselect("Sensores a comparar", options=sensors, default=sensors[: min(3, len(sensors))])
        if selected:
            compare_df = df_f[["timestamp"] + selected].copy().tail(720)
            long_df = compare_df.melt(id_vars=["timestamp"], var_name="Sensor", value_name="Valor")
            
            color_palette = {
                "TP3_mean": "#1E3A8A",
                "H1_mean": "#0891B2",
                "DV_pressure_mean": "#059669",
                "Motor_Current_mean": "#DC1F26",
                "MPG_last": "#F59E0B",
                "Oil_Temperature_mean": "#8B5CF6",
                "TOWERS_last": "#EC4899",
            }
            
            fig_cmp = px.line(long_df, x="timestamp", y="Valor", color="Sensor", color_discrete_map=color_palette)
            fig_cmp.update_traces(line=dict(width=2.5))
            fig_cmp.update_layout(
                height=400,
                margin=dict(t=30, b=30, l=60, r=30),
                paper_bgcolor="#FAFAFA",
                plot_bgcolor="#FAFAFA",
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showline=True,
                    linewidth=1,
                    linecolor="#E5E7EB",
                    tickfont=dict(size=10, color="#6B7280"),
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=0.8,
                    gridcolor="rgba(209, 213, 219, 0.5)",
                    zeroline=False,
                    showline=True,
                    linewidth=1,
                    linecolor="#E5E7EB",
                    tickfont=dict(size=10, color="#6B7280"),
                ),
                hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
                legend=dict(
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="#E5E7EB",
                    borderwidth=1,
                    font=dict(size=11, family="Arial"),
                ),
                font=dict(family="Arial, sans-serif", color="#374151"),
            )
            st.plotly_chart(fig_cmp, use_container_width=True)
