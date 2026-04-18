"""
EJEMPLO COMPLETO: Dashboard Premium con Todos los Componentes Nuevos

Este archivo muestra cómo integrar y usar todos os componentes premium
para crear un dashboard espectacular que impresione a ejecutivos.

Uso:
    streamlit run example_premium_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Imports de componentes
from src.dashboard.components.advanced_metrics import (
    render_gauge_metric,
    render_correlation_heatmap,
    render_sparkline_trend,
    render_comparison_chart
)

from src.dashboard.components.realtime_indicators import (
    render_status_badge,
    render_live_indicator,
    render_impact_card,
    render_threat_meter
)

from src.dashboard.components.performance_scoreboard import (
    render_leaderboard,
    render_award_badge,
    render_performance_grid
)

from src.dashboard.theme_manager import inject_theme_css


# ============================================================================
# CONFIGURACIÓN PAGE
# ============================================================================

st.set_page_config(
    page_title="📊 Dashboard Premium TI - EJEMPLO",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_theme_css()


# ============================================================================
# FUNCIONES AUXILIARES PARA GENERAR DATOS DE EJEMPLO
# ============================================================================

@st.cache_data
def generate_sensor_data():
    """Genera datos simulados de sensores para ejemplos."""
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=100, freq='h')
    return pd.DataFrame({
        'timestamp': dates,
        'temperature': np.random.normal(65, 10, 100),
        'pressure': np.random.normal(75, 8, 100),
        'current': np.random.normal(40, 12, 100),
        'voltage': np.random.normal(120, 5, 100),
        'vibration': np.random.normal(2.5, 0.8, 100),
    })


@st.cache_data
def generate_stations_comparison():
    """Genera datos de comparativa de estaciones."""
    return pd.DataFrame({
        'Estación': ['Centro', 'Norte', 'Sur', 'Este', 'Oeste'],
        'Disponibilidad': [98.5, 97.2, 95.1, 92.3, 89.7],
        'Eficiencia': [92, 88, 85, 78, 75],
        'Score': [95.3, 92.6, 90.1, 85.2, 82.4]
    })


# ============================================================================
# HEADER PREMIUM
# ============================================================================

st.markdown("""
<style>
    .premium-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .premium-header h1 {
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0;
        margin-bottom: 0.5rem;
    }
    
    .premium-header p {
        font-size: 1.1rem;
        opacity: 0.95;
        margin: 0;
    }
</style>

<div class="premium-header">
    <h1>📊 Dashboard Premium TI</h1>
    <p>Sistema Integral de Monitoreo y Análisis</p>
    <p style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">
        Última actualización: """ + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + """
    </p>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# SECCIÓN 1: ESTADO OPERACIONAL
# ============================================================================

st.markdown("## 🔴 Estado Operacional")
st.markdown("*Estado actual de sistemas e infraestructura*")

cols = st.columns(4)
with cols[0]:
    render_status_badge(status='OK', label='Sistema Eléctrico', animate=True)
with cols[1]:
    render_status_badge(status='WARNING', label='Compressor #1', animate=True)
with cols[2]:
    render_status_badge(status='OK', label='Refrigeración', animate=True)
with cols[3]:
    render_status_badge(status='MAINTENANCE', label='Revisión Mensual')

st.divider()


# ============================================================================
# SECCIÓN 2: MÉTRICAS CRÍTICAS - GAUGES
# ============================================================================

st.markdown("## 📈 Métricas Críticas (Gauges)")
st.markdown("*Indicadores principales con escala visual*")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.plotly_chart(
        render_gauge_metric("Disponibilidad", 92.5, 100, "%"),
        use_container_width=True
    )

with col2:
    st.plotly_chart(
        render_gauge_metric("Eficiencia", 78.3, 100, "%"),
        use_container_width=True
    )

with col3:
    st.plotly_chart(
        render_gauge_metric("Seguridad", 95.8, 100, "%"),
        use_container_width=True
    )

with col4:
    st.plotly_chart(
        render_gauge_metric("Energía", 68.5, 100, "%"),
        use_container_width=True
    )

st.divider()


# ============================================================================
# SECCIÓN 3: INDICADORES EN TIEMPO REAL
# ============================================================================

st.markdown("## 🎯 Indicadores Críticos en Tiempo Real")
st.markdown("*Valores actuales con codificación de color por umbral*")

col1, col2, col3 = st.columns(3)

with col1:
    render_live_indicator(
        value=78.5,
        label="Temperatura Compressor",
        threshold_warning=70,
        threshold_critical=85
    )

with col2:
    render_live_indicator(
        value=92.3,
        label="Presión Sistema",
        threshold_warning=80,
        threshold_critical=95
    )

with col3:
    render_live_indicator(
        value=45.2,
        label="Consumo Energético",
        threshold_warning=70,
        threshold_critical=85
    )

st.divider()


# ============================================================================
# SECCIÓN 4: IMPACTO FINANCIERO
# ============================================================================

st.markdown("## 💰 Impacto Operativo & Financiero")
st.markdown("*Visualización del impacto en el negocio*")

col1, col2 = st.columns(2)

with col1:
    col1a, col1b = st.columns(2, gap="small")
    with col1a:
        render_impact_card(
            title="Pérdidas Acumuladas",
            impact_value="$18,500",
            impact_unit="USD",
            description="Inactividad no programada en 30 días",
            icon="💸"
        )
    with col1b:
        render_impact_card(
            title="Tiempo Medio Reparación",
            impact_value="4.2",
            impact_unit="hrs",
            description="Promedio cuando hay incidentes",
            icon="⏱️"
        )

with col2:
    col2a, col2b = st.columns(2, gap="small")
    with col2a:
        render_impact_card(
            title="Oportunidad de Ahorro",
            impact_value="$42,000",
            impact_unit="USD",
            description="Implementando mejoras preventivas",
            icon="📈"
        )
    with col2b:
        render_impact_card(
            title="ROI Potencial",
            impact_value="156%",
            impact_unit="anual",
            description="Con nuevo plan de mantenimiento",
            icon="🚀"
        )

st.divider()


# ============================================================================
# SECCIÓN 5: ANÁLISIS DE SENSORES
# ============================================================================

st.markdown("## 🔬 Análisis de Sensores")
st.markdown("*Correlaciones y tendencias de datos*")

# Generar datos
sensor_data = generate_sensor_data()

tabs = st.tabs(["Mapa de Correlación", "Tendencias", "Comparativa"])

with tabs[0]:
    st.markdown("### Matriz de Correlación entre Sensores")
    fig = render_correlation_heatmap(sensor_data)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.markdown("### Mini Gráficos de Tendencia (Últimas 50 lecturas)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = render_sparkline_trend(sensor_data, 'temperature', 'Temperatura')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = render_sparkline_trend(sensor_data, 'pressure', 'Presión')
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        fig = render_sparkline_trend(sensor_data, 'current', 'Corriente')
        st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.markdown("### Comparison: Actual vs Anterior vs Objetivo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = render_comparison_chart(
            current=92.5,
            previous=87.3,
            benchmark=95,
            label="Disponibilidad"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = render_comparison_chart(
            current=78.3,
            previous=75.1,
            benchmark=85,
            label="Eficiencia"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        fig = render_comparison_chart(
            current=150,
            previous=165,
            benchmark=120,
            label="Consumo Energético (kWh)"
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()


# ============================================================================
# SECCIÓN 6: THREAT METER (MEDIDOR DE RIESGO)
# ============================================================================

st.markdown("## ⚠️ Evaluación de Riesgo")
st.markdown("*Nivel de amenaza acumulativo del sistema*")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### Amenaza Crítica (Sistema)")
    render_threat_meter(threat_level=7)

with col2:
    st.markdown("### Riesgo Eléctrico")
    render_threat_meter(threat_level=3)

with col3:
    st.markdown("### Riesgo de Fallos")
    render_threat_meter(threat_level=5)

with col4:
    st.markdown("### Degradación Equipos")
    render_threat_meter(threat_level=6)

st.divider()


# ============================================================================
# SECCIÓN 7: RANKING DE ESTACIONES
# ============================================================================

st.markdown("## 🥇 Ranking de Estaciones por Disponibilidad")
st.markdown("*Competencia sana entre ubicaciones*")

stations_data = generate_stations_comparison()
render_leaderboard(
    data=stations_data,
    columns=['Estación', 'Disponibilidad'],
    title="Disponibilidad por Estación"
)

st.divider()


# ============================================================================
# SECCIÓN 8: GRID DE DESEMPEÑO
# ============================================================================

st.markdown("## 📊 Score de Desempeño General")
st.markdown("*Calificación general por estación*")

performance_data = {
    'Centro': {'score': 95, 'label': 'Excelente'},
    'Norte': {'score': 87, 'label': 'Muy Bueno'},
    'Sur': {'score': 78, 'label': 'Bueno'},
    'Este': {'score': 68, 'label': 'Requiere Atención'}
}

render_performance_grid(performance_data)

st.divider()


# ============================================================================
# SECCIÓN 9: RECONOCIMIENTOS Y PREMIOS
# ============================================================================

st.markdown("## 🏆 Desempeño Destacado & Reconocimientos")
st.markdown("*Felicitación a los mejores performers del mes*")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Best Overall")
    render_award_badge(
        awarded_to="Estación Centro",
        award_type="Best Overall",
        metric="Score Operativo",
        value="95.3"
    )

with col2:
    st.subheader("Safety Champion")
    render_award_badge(
        awarded_to="Equipo de Mantenimiento Sur",
        award_type="Safety Champion",
        metric="Días sin incidentes",
        value="180"
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("Efficiency Leader")
    render_award_badge(
        awarded_to="Línea Express Centro",
        award_type="Efficiency Leader",
        metric="Consumo energético",
        value="-18% vs baseline"
    )

with col2:
    st.subheader("Uptime Master")
    render_award_badge(
        awarded_to="Compressor #3",
        award_type="Uptime Master",
        metric="Disponibilidad",
        value="99.7%"
    )

st.divider()


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<style>
    .premium-footer {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-top: 3px solid #667eea;
        padding: 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-top: 2rem;
    }
    
    .premium-footer p {
        margin: 0.25rem 0;
        opacity: 0.95;
    }
</style>

<div class="premium-footer">
    <p><strong>Sistema de Monitoreo Premium TI</strong></p>
    <p>Desarrollado para optimizar desempeño operacional</p>
    <p style="font-size: 0.9rem; opacity: 0.8;">
        © 2024 | Todos los datos son simulados para demostración
    </p>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# SIDEBAR CON CONTROLES
# ============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Controles")
    
    refresh_rate = st.select_slider(
        "Frecuencia de actualización:",
        options=[5, 10, 15, 30],
        value=10
    )
    
    st.markdown(f"*Datos se actualizan cada {refresh_rate} segundos*")
    
    st.divider()
    
    st.markdown("## 📋 Información")
    
    st.info(
        """
        **Este es un dashboard de ejemplo** que muestra todos los 
        componentes premium disponibles.
        
        Componentes incluidos:
        - ✅ Gauges (medidores)
        - ✅ Status badges (estados)
        - ✅ Indicadores en vivo
        - ✅ Impact cards
        - ✅ Threat meters
        - ✅ Heatmaps de correlación
        - ✅ Sparklines de tendencia
        - ✅ Gráficos comparativos
        - ✅ Leaderboards
        - ✅ Award badges
        - ✅ Performance grids
        """
    )
    
    st.divider()
    
    st.markdown("## 📚 Documentación")
    st.markdown(
        "[👉 Ver Guía Completa de Componentes](../COMPONENTES_PREMIUM.md)"
    )
