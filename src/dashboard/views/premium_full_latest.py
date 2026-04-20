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


def _money(v: float) -> str:
    return f"COP {v/1_000_000:,.1f}M"


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


def _kpi_card(label: str, value: str, delta: str = "", icon: str = "📊", color: str = "#1E3A8A"):
    """
    Renderiza una tarjeta KPI hermosa con HTML/CSS.
    """
    delta_html = ""
    if delta:
        delta_html = f'<div style="font-size: 13px; color: #6B7280; margin-top: 4px;">{delta}</div>'
    
    card_html = f"""
    <div style="
        background: linear-gradient(135deg, {color}08 0%, {color}04 100%);
        border: 2px solid {color}25;
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    ">
        <div style="font-size: 28px; margin-bottom: 6px;">{icon}</div>
        <div style="font-size: 11px; color: #6B7280; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">{label}</div>
        <div style="font-size: 24px; color: {color}; font-weight: 700; margin-top: 8px; font-family: 'Arial Black';">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


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
    
    # Área degradada de fondo para zona de riesgo
    fig.add_trace(
        go.Scatter(
            x=series["timestamp_hour"],
            y=[1] * len(series),
            fill=None,
            showlegend=False,
            hoverinfo="skip",
        )
    )
    
    # Línea principal de riesgo con estilo mejorado
    fig.add_trace(
        go.Scatter(
            x=series["timestamp_hour"],
            y=series["risk_score"],
            mode="lines",
            name="Tendencia de Riesgo",
            line=dict(color="#1E3A8A", width=3.2),
            fill="tozeroy",
            fillcolor="rgba(30, 58, 138, 0.18)",
            hovertemplate="<b>Riesgo Global</b><br>%{x|%H:%M}<br>Score: %{y:.2%}<extra></extra>",
        )
    )
    
    # Umbrales visuales mejorados
    fig.add_hline(
        y=0.4, 
        line_dash="dash", 
        line_color="#F59E0B",
        line_width=2,
        annotation_text="Riesgo MEDIO (40%)",
        annotation_position="right",
        annotation_font=dict(size=11, color="#D97706"),
    )
    fig.add_hline(
        y=0.7, 
        line_dash="dot", 
        line_color="#DC1F26",
        line_width=2.2,
        annotation_text="Riesgo ALTO (70%)",
        annotation_position="right",
        annotation_font=dict(size=11, color="#991B1B"),
    )
    
    fig.update_layout(
        height=380,
        margin=dict(t=30, b=30, l=20, r=120),
        paper_bgcolor="#FAFAFA",
        plot_bgcolor="#FAFAFA",
        showlegend=False,
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
            title_text="Risk Score",
            title_font=dict(size=12, color="#374151"),
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial",
        ),
        font=dict(family="Arial, sans-serif"),
    )
    
    fig.update_yaxes(range=[0, 1])
    return fig


def _financial_chart(fin: dict):
    bars = pd.DataFrame(
        {
            "Concepto": ["Exposición\nEconómica", "Mitigación\nPreventiva", "Valor Neto\nEsperado"],
            "Valor": [fin["reactive_cost"], fin["preventive_cost"], fin["savings"]],
        }
    )
    
    # Colores mejorados: Rojo profundo, Azul premium, Oro/Amarillo
    colors = ["#DC1F26", "#1E3A8A", "#F59E0B"]
    
    fig = go.Figure()
    
    for idx, (concepto, valor, color) in enumerate(zip(bars["Concepto"], bars["Valor"], colors)):
        fig.add_trace(
            go.Bar(
                x=[concepto],
                y=[valor],
                name=concepto,
                marker=dict(
                    color=color,
                    line=dict(color="rgba(0,0,0,0.15)", width=1.5),
                    opacity=0.92
                ),
                text=f"COP {valor/1_000_000:.1f}M",
                textposition="outside",
                textfont=dict(size=13, color="#1F2937", family="Arial Black"),
                hovertemplate=f"<b>{concepto}</b><br>COP {valor:,.0f}<extra></extra>",
                showlegend=False,
            )
        )
    
    fig.update_layout(
        height=380,
        margin=dict(t=30, b=30, l=20, r=20),
        paper_bgcolor="#FAFAFA",
        plot_bgcolor="#FAFAFA",
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(size=12, color="#374151", family="Arial"),
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=0.8,
            gridcolor="rgba(209, 213, 219, 0.5)",
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color="#6B7280"),
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Arial",
        ),
        font=dict(family="Arial, sans-serif"),
    )
    
    fig.update_yaxes(range=[0, max(bars["Valor"]) * 1.15])
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


def _drivers_chart(drivers_df: pd.DataFrame):
    """
    Visualización profesional de causas recurrentes con gráfico de barras horizontal.
    Diseño premium con colores degradados, bordes definidos y tipografía mejorada.
    """
    if drivers_df is None or drivers_df.empty:
        return None
    
    # Reordenar para que el más alto esté al topo
    drivers_sorted = drivers_df.sort_values("Frecuencia", ascending=True)
    
    # Paleta de colores: Rojo (crítico) → Naranja → Amarillo
    # Degradado profesional que indica severidad
    max_freq = drivers_sorted["Frecuencia"].max()
    min_freq = drivers_sorted["Frecuencia"].min()
    freq_range = max_freq - min_freq if max_freq > min_freq else 1
    
    # Colores en RGB: Rojo (#DC1F26) → Naranja (#F97316) → Amarillo (#F59E0B)
    colors = []
    for v in drivers_sorted["Frecuencia"]:
        normalized = (v - min_freq) / freq_range if freq_range > 0 else 0.5
        
        if normalized < 0.5:
            # Rojo a Naranja
            r = 220
            g = int(31 + (115 * (normalized * 2)))
            b = int(38 + (27 * (normalized * 2)))
        else:
            # Naranja a Amarillo
            r = int(220 - (30 * ((normalized - 0.5) * 2)))
            g = int(146 + (58 * ((normalized - 0.5) * 2)))
            b = int(22 - (22 * ((normalized - 0.5) * 2)))
        
        colors.append(f"rgba({r}, {g}, {b}, 0.92)")
    
    # Calcular porcentajes para contexto
    percentages = [(v / max_freq * 100) for v in drivers_sorted["Frecuencia"]]
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            y=drivers_sorted["Causa"],
            x=drivers_sorted["Frecuencia"],
            orientation="h",
            marker=dict(
                color=colors,
                line=dict(
                    color="rgba(0, 0, 0, 0.15)",
                    width=2
                ),
                opacity=0.95
            ),
            text=[f"{int(v)} eventos" for v in drivers_sorted["Frecuencia"]],
            textposition="outside",
            textfont=dict(size=12, color="#0F1E3C", family="Arial Black"),
            hovertemplate="<b>%{y}</b><br>" +
                         "Frecuencia: %{x} eventos<br>" +
                         "Severidad: %{customdata:.0f}%<extra></extra>",
            customdata=percentages,
            showlegend=False,
        )
    )
    
    fig.update_layout(
        height=380,
        margin=dict(t=30, b=30, l=180, r=100),
        paper_bgcolor="#FAFAFA",
        plot_bgcolor="white",
        xaxis=dict(
            showgrid=True,
            gridwidth=0.8,
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="#E5E7EB",
            tickfont=dict(size=11, color="#6B7280", family="Arial"),
            title_text="Frecuencia de Ocurrencia",
            title_font=dict(size=12, color="#6B7280", family="Arial"),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="#E5E7EB",
            tickfont=dict(size=11, color="#0F1E3C", family="Arial"),
            automargin=True,
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial",
            bordercolor="#E5E7EB",
        ),
        font=dict(family="Arial, sans-serif", color="#0F1E3C"),
    )
    
    # Ajustar rango del eje X para mejor visualización
    fig.update_xaxes(range=[0, max_freq * 1.25])
    
    return fig


def render(_df: pd.DataFrame) -> None:
    # Inyectar estilos CSS mejorados
    st.markdown("""
    <style>
    /* Mejoras visuales generales */
    [data-testid="column"] {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    [data-testid="column"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
    }
    
    /* Estilos para headers */
    h1, h2, h3 {
        font-family: 'Arial Black', Arial, sans-serif;
        letter-spacing: -0.5px;
    }
    
    /* Mejorar legibilidad */
    body {
        font-family: 'Arial', sans-serif;
        background-color: #FAFAFA;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
        _kpi_card("Trenes Monitoreados", str(total_trains), icon="🚂", color="#1E3A8A")
    with k2:
        _kpi_card("En Riesgo Alto", str(high), f"({(high/max(1,total_trains))*100:.0f}%)", icon="⚠️", color="#DC1F26")
    with k3:
        _kpi_card("Disponibilidad Global", f"{uptime:.1f}%", icon="✅", color="#059669")
    with k4:
        _kpi_card("Salud Operativa", f"{health:.0f}/100", f"Eficiencia {efficiency:.0f}%", icon="💚", color="#F59E0B")

    render_section_header("Impacto Financiero Consolidado", "Comparación entre escenario reactivo y preventivo en la flota.")
    f1, f2, f3 = st.columns(3)
    with f1:
        _kpi_card("Exposición\nEconómica", _money(fin["reactive_cost"]), icon="📊", color="#DC1F26")
    with f2:
        _kpi_card("Mitigación\nPreventiva", _money(fin["preventive_cost"]), icon="🛡️", color="#1E3A8A")
    with f3:
        _kpi_card("Valor Neto\nEsperado", _money(fin["savings"]), color="#F59E0B")

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

    render_section_header("Causas Recurrentes de Riesgo", "Principales factores que explican la mayoría de alertas en la flota - Factores con mayor impacto operacional.")
    drivers = _drivers_table(alert_df)
    if drivers.empty:
        st.info("🔍 Aún no hay suficientes datos de alertas para identificar causas recurrentes.")
    else:
        chart = _drivers_chart(drivers)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
