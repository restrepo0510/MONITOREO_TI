"""
Advanced Metrics Display - Componentes visuales premium y sofisticados.

Características:
- Gauge charts para métricas
- Heatmaps de correlaciones
- Spark lines para tendencias
- Métricas comparativas
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def render_gauge_metric(title: str, value: float, max_value: float = 100, unit: str = "%"):
    """
    Renderiza un medidor/gauge visual premium.
    
    Args:
        title: Título de la métrica
        value: Valor actual (0-max_value)
        max_value: Valor máximo de la escala
        unit: Unidad a mostrar
    """
    percentage = (value / max_value) * 100
    
    # Determinar color por rango
    if percentage <= 33:
        color = "#4facfe"  # Azul
    elif percentage <= 66:
        color = "#ffa500"  # Naranja
    else:
        color = "#ff6b6b"  # Rojo
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        number={'suffix': unit, 'font': {'size': 24, 'color': color}},
        gauge={
            'axis': {'range': [0, max_value]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, max_value * 0.33], 'color': 'rgba(79, 172, 254, 0.2)'},
                {'range': [max_value * 0.33, max_value * 0.66], 'color': 'rgba(255, 165, 0, 0.2)'},
                {'range': [max_value * 0.66, max_value], 'color': 'rgba(255, 107, 107, 0.2)'},
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.7
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#0F1E3C", size=12),
    )
    
    return fig


def render_correlation_heatmap(df, sensor_columns=None):
    """
    Renderiza un mapa de calor de correlaciones entre sensores.
    
    Args:
        df: DataFrame con datos
        sensor_columns: Columnas de sensores a analizar
    """
    if sensor_columns is None:
        # Detectar columnas de sensores automáticamente
        sensor_cols = [col for col in df.columns if any(x in col.lower() for x in ['temp', 'pressure', 'current', 'voltage'])]
        if not sensor_cols:
            sensor_cols = df.select_dtypes(include=[np.number]).columns.tolist()[1:5]
    else:
        sensor_cols = sensor_columns
    
    if len(sensor_cols) < 2:
        st.info("No hay suficientes sensores para mostrar correlación")
        return None
    
    correlation = df[sensor_cols].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation.values,
        x=correlation.columns,
        y=correlation.index,
        colorscale='RdBu_r',
        zmid=0,
        text=correlation.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlación")
    ))
    
    fig.update_layout(
        height=400,
        title="Correlación entre Sensores",
        xaxis_title="",
        yaxis_title="",
        margin=dict(l=100, r=50, t=80, b=80),
    )
    
    return fig


def render_sparkline_trend(df, column: str, title: str):
    """
    Renderiza una línea de tendencia mini (sparkline).
    
    Args:
        df: DataFrame con datos
        column: Columna a graficar
        title: Título
    """
    recent_data = df[column].tail(50)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=recent_data.values,
        mode='lines',
        fill='tozeroy',
        line=dict(color='#667eea', width=2),
        fillcolor='rgba(102, 126, 234, 0.2)',
        hovertemplate='%{y:.2f}<extra></extra>',
    ))
    
    fig.update_layout(
        height=120,
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=True, zeroline=False, tickfont=dict(size=10)),
        hovermode='x unified',
        title=title,
    )
    
    return fig


def render_comparison_chart(current: float, previous: float, benchmark: float = None, label: str = "Métrica"):
    """
    Renderiza un gráfico comparativo de valores.
    
    Args:
        current: Valor actual
        previous: Valor anterior (para comparación)
        benchmark: Valor benchmark/objetivo
        label: Etiqueta
    """
    categories = ['Anterior', 'Actual']
    
    if benchmark:
        categories.append('Objetivo')
        values = [previous, current, benchmark]
    else:
        values = [previous, current]
    
    colors = ['#a0aec0', '#4facfe']
    if benchmark:
        colors.append('#4caf50')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker=dict(color=colors),
        text=values,
        textposition='outside',
        hovertemplate='%{x}: %{y:.2f}<extra></extra>',
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
        title=label,
        yaxis_title="Valor",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
    )
    
    return fig


def render_metric_card_with_history(label: str, current: float, history: list, unit: str = ""):
    """
    Renderiza una tarjeta de métrica con historia sparkline.
    
    Args:
        label: Etiqueta de la métrica
        current: Valor actual
        history: Lista de valores históricos
        unit: Unidad
    """
    if not history or len(history) == 0:
        history = [current]
    
    min_val = min(history)
    max_val = max(history)
    trend = "📈" if (len(history) > 1 and current >= history[-2]) else "📉"
    
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        border-radius: 12px; padding: 1.2rem; color: white; position: relative; overflow: hidden;">
            <div style="position: relative; z-index: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 700; opacity: 0.95;">{label}</span>
                    <span style="font-size: 1.3rem;">{trend}</span>
                </div>
                <div style="font-size: 2rem; font-weight: 900; margin-bottom: 0.5rem;">
                    {current:.2f}{unit}
                </div>
                <div style="font-size: 0.85rem; opacity: 0.9;">
                    Rango: {min_val:.2f} - {max_val:.2f}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics_dashboard(data: dict):
    """
    Renderiza un dashboard completo de métricas avanzadas.
    
    Args:
        data: Dict con métricas y datos
    """
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.plotly_chart(
            render_gauge_metric("Disponibilidad", 85, 100, "%"),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            render_gauge_metric("Eficiencia", 78, 100, "%"),
            use_container_width=True
        )
