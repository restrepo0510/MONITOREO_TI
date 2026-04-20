from pathlib import Path

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np

from src.dashboard.cache_manager import load_dashboard_data
from src.dashboard.theme_manager import (
    inject_theme_css,
    render_section_header,
    render_page_title,
    render_hero_alert,
    render_kpi_card_advanced,
    render_metric_row,
    render_stats_summary,
    render_premium_divider,
    COLORS,
    RISK_THEME,
)
from src.dashboard.components.alert_badge import render_alert_badge
from src.dashboard.components.financial_section import render_financial_section
from src.dashboard.components.golden_signals import render_golden_signals
from src.dashboard.components.operativity_panel import render_operativity_panel
from src.dashboard.components.postmortem_panel import render_postmortem_panel
from src.dashboard.components.station_line import render_station_line
from src.dashboard.theme import RISK_THRESHOLDS




# ============================================================================
# UTILIDADES PRIVADAS PARA GRÁFICOS
# ============================================================================

def _build_risk_chart(df, prediction):
    """Gráfico de riesgo a lo largo del tiempo."""
    risk_df = df.tail(720).copy()
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=risk_df["timestamp"],
            y=risk_df["risk_score"],
            mode="lines",
            name="Risk score",
            line=dict(color=COLORS["primary_blue"], width=2.7),
            fill="tozeroy",
            fillcolor="rgba(35, 75, 141, 0.12)",
            hovertemplate="%{x}<br>Score %{y:.3f}<extra></extra>",
        )
    )
    
    fig.add_hline(
        y=RISK_THRESHOLDS["MEDIO"],
        line_dash="dash",
        line_color=COLORS["accent_yellow"],
        annotation_text=f"MEDIO",
        annotation_position="top left",
    )
    fig.add_hline(
        y=RISK_THRESHOLDS["ALTO"],
        line_dash="dash",
        line_color=COLORS["alert_red"],
        annotation_text=f"ALTO",
        annotation_position="top left",
    )
    
    # Proyección
    fig.add_trace(
        go.Scatter(
            x=[risk_df["timestamp"].iloc[-1]],
            y=[prediction["projected_score"]],
            mode="markers",
            name="Proyeccion 2h",
            marker=dict(
                color=COLORS["accent_yellow"],
                size=12,
                line=dict(color=COLORS["text_dark"], width=1.2),
            ),
            hovertemplate="Proyeccion<br>%{y:.3f}<extra></extra>",
        )
    )
    
    fig.update_layout(
        height=360,
        margin=dict(t=20, b=10, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=COLORS["text_dark"]),
        legend=dict(orientation="h", y=1.10, x=0),
    )
    fig.update_yaxes(range=[0, 1], showgrid=True, gridcolor="rgba(35, 75, 141, 0.10)")
    fig.update_xaxes(showgrid=False)
    return fig


def _build_drivers_chart(alert_reasons):
    """Gráfico profesional de causas/drivers del riesgo."""
    chunks = [chunk.strip() for chunk in str(alert_reasons).split("|") if chunk.strip()]
    labels = []
    values = []
    
    for idx, chunk in enumerate(chunks[:5], start=1):
        label = chunk.split(":", 1)[0].replace("_mean", "").replace("_last", "")
        labels.append(label)
        values.append(max(1, 6 - idx))

    if not labels:
        labels = ["Sistema Estable"]
        values = [5]
        colors_list = ["#059669"]  # Verde para estado estable
    else:
        # Paleta de colores gradiente: Rojo → Naranja → Amarillo
        # Para mostrar severidad de cada causa
        if len(labels) == 1:
            colors_list = ["#DC1F26"]  # Rojo puro para una causa crítica
        elif len(labels) == 2:
            colors_list = ["#DC1F26", "#F97316"]  # Rojo, Naranja
        elif len(labels) == 3:
            colors_list = ["#DC1F26", "#F59E0B", "#F97316"]  # Rojo, Amarillo, Naranja
        elif len(labels) == 4:
            colors_list = ["#DC1F26", "#F59E0B", "#F97316", "#FB923C"]  # Rojo a Naranja
        else:
            colors_list = ["#DC1F26", "#F59E0B", "#F97316", "#FB923C", "#FBBF24"]  # Rojo a Amarillo

    # Invertir para que la causa más importante esté arriba
    labels = labels[::-1]
    values = values[::-1]
    colors_list = colors_list[::-1]

    # Calcular porcentajes para las etiquetas
    max_value = max(values) if values else 1
    percentages = [int((v / max_value) * 100) for v in values]

    # Crear figura con barras horizontales mejoradas
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(
                color=colors_list,
                line=dict(
                    color=[c.replace("F", "A") for c in colors_list],  # Bordes más oscuros
                    width=2
                ),
                opacity=0.95
            ),
            text=[f"{pct}%" for pct in percentages],
            textposition="outside",
            textfont=dict(size=12, color="#0F1E3C", family="Arial Black"),
            hovertemplate="<b>%{y}</b><br>Peso: %{x}<br>Severidad: %{customdata}%<extra></extra>",
            customdata=percentages,
        )
    )
    
    # Actualizar layout con diseño profesional
    fig.update_layout(
        height=320,
        margin=dict(t=30, b=30, l=150, r=80),
        paper_bgcolor="#FAFAFA",
        plot_bgcolor="white",
        font=dict(family="Arial", color="#0F1E3C", size=11),
        xaxis_title="Peso Relativo",
        xaxis_title_font=dict(size=12, family="Arial", color="#6B7280"),
        showlegend=False,
        hovermode="closest",
    )
    
    # Mejorar ejes
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(200, 200, 200, 0.2)",
        gridwidth=0.8,
        showline=True,
        linewidth=1,
        linecolor="#E5E7EB",
        zeroline=False,
        tickfont=dict(size=11, color="#6B7280"),
    )
    
    fig.update_yaxes(
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor="#E5E7EB",
        tickfont=dict(size=11, color="#0F1E3C", family="Arial"),
        automargin=True,
    )
    
    return fig


# ============================================================================
# HEADER
# ============================================================================

def _render_header():
    """Renderiza header premium con logo y estación."""
    assets_dir = Path(__file__).resolve().parents[1] / "assets" / "images"
    logo_path = assets_dir / "logo.png"
    train_path = assets_dir / "train.png"
    
    cols = st.columns([0.9, 2.2, 2.1, 1.8], gap="small", vertical_alignment="center")
    
    with cols[0]:
        if logo_path.exists():
            st.image(str(logo_path), width=145)
    
    with cols[1]:
        render_page_title("Command Center APU 001", 
                         "Vista ejecutiva para monitoreo, continuidad operativa y priorizacion de mantenimiento.")
    
    with cols[2]:
        render_station_line(train_id="001", cycle_seconds=5)
    
    with cols[3]:
        if train_path.exists():
            st.image(str(train_path), width=330)


# ============================================================================
# SECCIÓN PRINCIPAL
# ============================================================================

def render(df):
    """
    Dashboard ejecutivo premium - Diseño impactante para impresionar.
    """
    # CSS premium
    inject_theme_css()
    
    # Datos optimizados
    data = load_dashboard_data()
    latest = data['latest']
    prediction = data['prediction']
    alert_df = data['alert_df']
    latest_alert = data['latest_alert']
    threshold_source = data['threshold_source']
    
    # ========================================================================
    # 1. HEADER ESPECTACULAR
    # ========================================================================
    
    col_logo, col_title, col_station, col_train = st.columns(
        [0.8, 2.2, 2.1, 1.9], gap="medium", vertical_alignment="center"
    )
    
    assets_dir = Path(__file__).resolve().parents[1] / "assets" / "images"
    
    with col_logo:
        logo_path = assets_dir / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=145)
    
    with col_title:
        st.markdown(
            "<h1 class='title-main'>MonitoreoTI 🚀</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p class='subtitle-main'>Centro de Control Ejecutivo - Sistema de Monitoreo Predictivo Avanzado</p>",
            unsafe_allow_html=True,
        )
    
    with col_station:
        render_station_line(train_id="001", cycle_seconds=5)
    
    with col_train:
        train_path = assets_dir / "train.png"
        if train_path.exists():
            st.image(str(train_path), width=330)
    
    st.markdown("")
    
    # ========================================================================
    # 2. ALERTA PRINCIPAL IMPACTANTE
    # ========================================================================
    
    render_hero_alert(
        alert_level=latest_alert["alert_level"],
        score=float(latest['risk_score']),
        trend=prediction['projected_level']
    )
    
    st.markdown("")
    
    # ========================================================================
    # 3. MÉTRICAS KPI PREMIUM EN GRID
    # ========================================================================
    
    st.markdown(
        '<div class="section-kicker">INDICADORES CLAVE</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h2 class="section-title">Estado Operacional Actual</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="section-copy">Métricas en tiempo real del estado del equipo APU #001</p>',
        unsafe_allow_html=True,
    )
    
    # Preparar datos de KPI
    high_alerts = int((alert_df["alert_level"] == "ALTO").sum())
    medium_alerts = int((alert_df["alert_level"] == "MEDIO").sum())
    
    kpi_metrics = [
        {
            "label": "Riesgo Actual",
            "value": f"{float(latest['risk_score']):.3f}",
            "delta": f"Estado: {str(latest['risk_level']).upper()}",
            "caption": "Puntuación de riesgo del motor",
            "progress": float(latest['risk_score']) * 100,
            "color": "red" if float(latest['risk_score']) > 0.7 else "yellow" if float(latest['risk_score']) > 0.4 else "cyan",
            "icon": ""
        },
        {
            "label": "Proyección 2H",
            "value": f"{prediction['projected_score']:.3f}",
            "delta": f"{prediction['trend_direction'].upper()}",
            "caption": "Trayectoria esperada",
            "progress": prediction['projected_score'] * 100,
            "color": "blue",
            "icon": ""
        },
        {
            "label": "Alertas Críticas",
            "value": str(high_alerts),
            "delta": f"+{medium_alerts} en observación",
            "caption": "Ventanas que requieren acción",
            "progress": min((high_alerts / max(1, high_alerts + medium_alerts)) * 100, 100),
            "color": "red" if high_alerts > 0 else "cyan",
            "icon": ""
        },
        {
            "label": "Triggers Activos",
            "value": str(int(latest_alert["alert_trigger_count"])),
            "delta": latest_alert["alert_sources"].replace("+", " +").upper()[:30],
            "caption": "Causas raíz identificadas",
            "progress": min(latest_alert["alert_trigger_count"] * 25, 100),
            "color": "pink",
            "icon": ""
        }
    ]
    
    render_metric_row(kpi_metrics)
    
    st.markdown("")
    
    # ========================================================================
    # 4. RESUMEN ESTADÍSTICO PREMIUM
    # ========================================================================
    
    render_premium_divider()
    
    render_stats_summary(
        "Estadísticas de Desempeño",
        {
            "Uptime": f"{(1 - high_alerts / max(1, len(alert_df))) * 100:.1f}%",
            "Eficiencia": f"{100 - float(latest['risk_score']) * 100:.1f}%",
            "Salud General": f"{100 - float(latest['risk_score']) * 80:.0f}/100",
            "Status": "OPERATIVO" if float(latest['risk_score']) < 0.7 else "ALERTA",
        }
    )
    
    st.markdown("")
    
    # ========================================================================
    # 5. GRÁFICOS PRINCIPALES OPTIMIZADOS
    # ========================================================================
    
    render_section_header(
        "ANÁLISIS DE RIESGO",
        "Comportamiento Temporal y Predicciones",
        "Trayectoria del score de riesgo a lo largo del tiempo con proyecciones"
    )
    
    col_chart, col_drivers = st.columns([2, 1], gap="medium")
    
    with col_chart:
        st.markdown(
            '<div class="chart-container">',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            _build_risk_chart(data["df"], prediction),
            use_container_width=True,
            key="risk_chart"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_drivers:
        st.markdown(
            '<div class="chart-container">',
            unsafe_allow_html=True,
        )
        st.markdown("**🔍 Drivers Críticos**")
        st.plotly_chart(
            _build_drivers_chart(latest_alert['alert_reasons']),
            use_container_width=True,
            key="drivers_chart"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("")
    
    # ========================================================================
    # 6. GOLDEN SIGNALS
    # ========================================================================
    
    render_premium_divider()
    
    render_section_header(
        "⭐ SEÑALES CRÍTICAS",
        "Indicadores de Salud del Sistema",
        "Monitoreo de parámetros clave que indican la salud operativa"
    )
    render_golden_signals(data["df"], data["thresholds"])
    
    st.markdown("")
    
    # ========================================================================
    # 7. ANÁLISIS FINANCIERO
    # ========================================================================
    
    render_premium_divider()
    
    render_section_header(
        " IMPACTO FINANCIERO",
        "ROI y Ahorros Proyectados",
        "Estimación de valor generado por el sistema de monitoreo"
    )
    render_financial_section(alert_df, prediction)
    
    st.markdown("")
    
    # ========================================================================
    # 8. PLAYBOOK OPERATIVO
    # ========================================================================
    
    render_premium_divider()
    
    render_section_header(
        "PLAN DE ACCIÓN",
        "Recomendaciones Operativas",
        "Pasos concretos para mantener el equipo en óptimas condiciones"
    )
    render_operativity_panel(data["df"].tail(2400))
    
    st.caption(
        f"Motor {data['meta'].get('engine_version', 'v2')} · "
        f"Umbral Medio {data['meta'].get('risk_threshold_medium', 0.4):.2f} · "
        f"Umbral Alto {data['meta'].get('risk_threshold_high', 0.7):.2f}"
    )
    
    st.markdown("")
    
    # ========================================================================
    # 9. ANÁLISIS HISTÓRICO
    # ========================================================================
    
    render_premium_divider()
    
    render_section_header(
        "POSTMORTEM",
        "Análisis de Episodios Recientes",
        "Desagregación ejecutiva de eventos críticos para toma de decisiones"
    )
    render_postmortem_panel(alert_df, prediction)
    
    st.markdown("")
    
    # ========================================================================
    # 10. FOOTER PROFESIONAL
    # ========================================================================
    
    st.markdown(
        """
        <div style="text-align: center; margin-top: 3rem; padding: 2rem; 
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
        border-radius: 16px; border-top: 2px solid #667eea;">
            <p style="color: #718096; margin: 0;">Dashboard MonitoreoTI v2.0 • Powered by Streamlit & Python</p>
            <p style="color: #a0aec0; font-size: 0.85rem; margin-top: 0.5rem;">
                Última actualización: Ahora • Estado: OPERATIVO ✓
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

