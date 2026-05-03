# 📊 Guía de Componentes Premium - Dashboard TI

## Descripción General

Se han añadido 3 nuevas librerías de componentes para expandir las capacidades visuales del dashboard:

1. **`advanced_metrics.py`** - Métricas avanzadas y análisis
2. **`realtime_indicators.py`** - Indicadores en tiempo real con animaciones
3. **`performance_scoreboard.py`** - Rankings competitivos y scoreboards

---

## 🔧 Instalación & Imports

```python
# En tu archivo de vista (ej: home.py)
from src.dashboard.components.advanced_metrics import (
    render_gauge_metric,
    render_correlation_heatmap,
    render_sparkline_trend,
    render_comparison_chart,
    render_metric_card_with_history
)

from src.dashboard.components.realtime_indicators import (
    render_status_badge,
    render_live_indicator,
    render_impact_card,
    render_threat_meter
)

from src.dashboard.components.performance_scoreboard import (
    render_leaderboard,
    render_comparison_table,
    render_award_badge,
    render_performance_grid
)
```

---

## 📈 Componentes - Advanced Metrics

### 1. **Gauge Metric** (Medidor)
Renderiza un medidor visual con rango y umbrales.

```python
import streamlit as st
from src.dashboard.components.advanced_metrics import render_gauge_metric

# Uso básico
fig = render_gauge_metric(
    title="Disponibilidad",
    value=85,
    max_value=100,
    unit="%"
)
st.plotly_chart(fig, use_container_width=True)
```

**Características:**
- ✅ Colores automáticos por rango (azul ≤33%, naranja 33-66%, rojo >66%)
- ✅ Umbrales visuales
- ✅ Indicadores de peligro
- ✅ Responsive

---

### 2. **Correlation Heatmap** (Mapa de Calor)
Muestra correlaciones entre sensores.

```python
import pandas as pd
from src.dashboard.components.advanced_metrics import render_correlation_heatmap

# Tus datos
df = load_sensor_data()

# Métodos
fig = render_correlation_heatmap(df)  # Auto-detecta sensores
fig = render_correlation_heatmap(df, sensor_columns=['temp', 'pressure'])  # Específico

st.plotly_chart(fig, use_container_width=True)
```

**Características:**
- ✅ Auto-detección de columnas de sensores
- ✅ Escala de color RdBu
- ✅ Valores de correlación mostrados
- ✅ 400px de altura

---

### 3. **Sparkline Trend** (Mini Gráfico de Tendencia)
Gráfico mini de últimos 50 valores.

```python
from src.dashboard.components.advanced_metrics import render_sparkline_trend

fig = render_sparkline_trend(
    df=data,
    column='temperature',
    title='Temperatura Últimas 50 lecturas'
)
st.plotly_chart(fig, use_container_width=True)
```

**Características:**
- ✅ Altura compacta (120px) - ideal para sidebars
- ✅ Área rellena bajo la línea
- ✅ Hover interactivo
- ✅ Línea suave

---

### 4. **Comparison Chart** (Gráfico Comparativo)
Compara valor anterior vs actual vs objetivo.

```python
from src.dashboard.components.advanced_metrics import render_comparison_chart

fig = render_comparison_chart(
    current=92,
    previous=87,
    benchmark=95,
    label="Eficiencia Sistema"
)
st.plotly_chart(fig, use_container_width=True)
```

**Características:**
- ✅ Comparación de 2 o 3 valores
- ✅ Colores diferenciados
- ✅ Etiquetas automáticas
- ✅ Altura: 300px

---

### 5. **Metric Card with History** (Tarjeta con Historia)
Tarjeta degradada con estadísticas históricas.

```python
from src.dashboard.components.advanced_metrics import render_metric_card_with_history

render_metric_card_with_history(
    label="CPU Promedio",
    current=65.5,
    history=[45, 50, 55, 60, 62, 65.5],
    unit="%"
)
```

**Características:**
- ✅ Gradiente morado-azul
- ✅ Indicador de tendencia (📈/📉)
- ✅ Rango min-max
- ✅ Animación de entrada

---

## 🎯 Componentes - Real-Time Indicators

### 1. **Status Badge** (Badge de Estado)
Badge animado con estado.

```python
from src.dashboard.components.realtime_indicators import render_status_badge

# Estados disponibles: 'OK', 'WARNING', 'CRITICAL', 'MAINTENANCE'
render_status_badge(status='OK', label='Sistema Principal', animate=True)
render_status_badge(status='WARNING', label='Compressor 2')
render_status_badge(status='CRITICAL', animate=False)
render_status_badge(status='MAINTENANCE', label='Revisión Mensual')
```

**Características:**
- ✅ 4 estados predefinidos con colores
- ✅ Animación de pulso adaptada al estado
- ✅ Icono + texto + etiqueta
- ✅ Control de animación

---

### 2. **Live Indicator** (Indicador en Vivo)
Valor con color dinámico según umbral.

```python
from src.dashboard.components.realtime_indicators import render_live_indicator

render_live_indicator(
    value=85.5,
    label="Temperatura Compressor",
    threshold_warning=70,
    threshold_critical=85
)
```

**Características:**
- ✅ Colores automáticos por umbral
- ✅ Gradiente de fondo
- ✅ Estados: OK (verde), WARNING (naranja), CRITICAL (rojo)
- ✅ Sombra y borde

---

### 3. **Impact Card** (Tarjeta de Impacto)
Tarjeta grande para mostrar impactos importantes.

```python
from src.dashboard.components.realtime_indicators import render_impact_card

render_impact_card(
    title="Pérdidas por Inactividad",
    impact_value="$12,500",
    impact_unit="USD",
    description="Tiempo de inactividad del compressor en últimas 24hrs",
    icon="💰"
)

render_impact_card(
    title="Reducción de Eficiencia",
    impact_value="15",
    impact_unit="%",
    description="Disminución de rendimiento vs línea base",
    icon="⚡"
)
```

**Características:**
- ✅ Gradiente morado-azul premium
- ✅ Sombra significativa
- ✅ Emoji customizable
- ✅ Descripción contextual

---

### 4. **Threat Meter** (Medidor de Amenaza)
Barra de progreso para nivel de riesgo.

```python
from src.dashboard.components.realtime_indicators import render_threat_meter

render_threat_meter(threat_level=3)   # Verde - BAJO
render_threat_meter(threat_level=5)   # Naranja - MEDIO
render_threat_meter(threat_level=7)   # Naranja oscuro - ALTO
render_threat_meter(threat_level=9)   # Rojo - CRÍTICO
```

**Características:**
- ✅ Escala 0-10
- ✅ 4 niveles: BAJO, MEDIO, ALTO, CRÍTICO
- ✅ Color y etiqueta automática
- ✅ Barra animada

---

## 🏆 Componentes - Performance Scoreboard

### 1. **Leaderboard** (Ranking)
Ranking visual con medallas.

```python
from src.dashboard.components.performance_scoreboard import render_leaderboard
import pandas as pd

# Preparar datos
ranking_data = pd.DataFrame({
    'Estación': ['Norte', 'Sur', 'Este', 'Oeste'],
    'Upt ime': [98.5, 97.2, 95.1, 92.3]
})

render_leaderboard(
    data=ranking_data,
    columns=['Estación', 'Uptime'],
    title="Ranking de Disponibilidad"
)
```

**Características:**
- ✅ Medallas automáticas: 🥇🥈🥉
- ✅ Top 10 mostrados
- ✅ Colores degradados: Oro, Plata, Bronce, Morado
- ✅ Animaciones suaves

---

### 2. **Comparison Table** (Tabla Comparativa)
Tabla con estilos premium y resaltados.

```python
from src.dashboard.components.performance_scoreboard import render_comparison_table

comparison_df = pd.DataFrame({
    'Métrica': ['Disponibilidad', 'Eficiencia', 'Seguridad'],
    'Objetivo': ['95%', '90%', '100%'],
    'Actual': ['98%', '87%', '99%'],
    'Diferencia': ['+3%', '-3%', '-1%']
})

render_comparison_table(
    data=comparison_df,
    highlight_columns=['Diferencia']  # Columnas a destacar
)
```

**Características:**
- ✅ Encabezado degradado morado-azul
- ✅ Filas hover interactivas
- ✅ Columnas destacables con celdas cyan
- ✅ Responsive y con sombra

---

### 3. **Award Badge** (Badge de Premio)
Reconocimiento visual por desempeño.

```python
from src.dashboard.components.performance_scoreboard import render_award_badge

render_award_badge(
    awarded_to="Estación Centro",
    award_type="Best Overall",
    metric="Score Operativo",
    value="98.5"
)

render_award_badge(
    awarded_to="Compressor 3",
    award_type="Safety Champion",
    metric="Tiempo sin incidentes",
    value="245 días"
)

render_award_badge(
    awarded_to="Línea Express",
    award_type="Efficiency Leader",
    metric="Consumo energético",
    value="-12% vs baseline"
)

render_award_badge(
    awarded_to="Zona Periférica",
    award_type="Uptime Master",
    metric="Disponibilidad",
    value="99.8%"
)
```

**Características:**
- ✅ Tipos predefinidos con emojis
- ✅ 4 tipos: Best Overall, Safety Champion, Efficiency Leader, Uptime Master
- ✅ Borde de color temático
- ✅ Formato profesional

---

### 4. **Performance Grid** (Grid de Desempeño)
Grid 2-4 columnas con cards de estaciones.

```python
from src.dashboard.components.performance_scoreboard import render_performance_grid

stations = {
    'Norte': {'score': 98, 'label': 'Excelente'},
    'Sur': {'score': 85, 'label': 'Bueno'},
    'Este': {'score': 72, 'label': 'Aceptable'},
    'Oeste': {'score': 65, 'label': 'Requiere atención'}
}

render_performance_grid(stations)
```

**Características:**
- ✅ Automático (2-4 columnas según espacios)
- ✅ Color por score (Verde ≥85, Naranja 70-85, Rojo <70)
- ✅ Emoji emoji indicador visual
- ✅ Responsive

---

## 📖 Ejemplos de Integración Completa

### Ejemplo 1: Dashboard de Monitoreo Operativo

```python
import streamlit as st
from src.dashboard.components.realtime_indicators import render_status_badge, render_impact_card
from src.dashboard.components.advanced_metrics import render_gauge_metric
from src.dashboard.components.performance_scoreboard import render_award_badge

st.set_page_config(page_title="Dashboard Operativo", layout="wide")

# Sección 1: Estado General
st.markdown("## 🏢 Estado de Sistemas")
cols = st.columns(3)
with cols[0]:
    render_status_badge('OK', 'Sistema Eléctrico', animate=True)
with cols[1]:
    render_status_badge('WARNING', 'Compressor', animate=True)
with cols[2]:
    render_status_badge('CRITICAL', 'Refrigeración', animate=False)

# Sección 2: Métricas Críticas
st.markdown("## 📊 Métricas Críticas")
cols = st.columns(2)
with cols[0]:
    st.plotly_chart(render_gauge_metric("Disponibilidad", 92, 100, "%"), use_container_width=True)
with cols[1]:
    st.plotly_chart(render_gauge_metric("Eficiencia", 78, 100, "%"), use_container_width=True)

# Sección 3: Impacto Operativo
st.markdown("## 💰 Impacto Operativo")
col1, col2, col3 = st.columns(3)
with col1:
    render_impact_card("Pérdidas Acumuladas", "$8,500", "USD", "Última semana", "💸")
with col2:
    render_impact_card("Tiempo Recuperación", "4.2", "horas", "Promedio últimas paradas", "⏱️")
with col3:
    render_impact_card("Mejora Potencial", "22%", "ROI", "Si se implementan mejoras", "📈")

# Sección 4: Premios/Reconocimientos
st.markdown("## 🏆 Desempeño Destacado")
col1, col2 = st.columns(2)
with col1:
    render_award_badge("Estación Centro", "Best Overall", "Score Operativo", "98.5")
with col2:
    render_award_badge("Línea Express", "Efficiency Leader", "Consumo energético", "-12%")
```

---

### Ejemplo 2: Dashboard de Comparativa Estaciones

```python
import pandas as pd
from src.dashboard.components.performance_scoreboard import (
    render_leaderboard, 
    render_performance_grid,
    render_comparison_table
)

# Datos
stations_data = pd.DataFrame({
    'Estación': ['Centro', 'Norte', 'Sur', 'Este'],
    'Uptime': [98.5, 97.2, 95.1, 92.3]
})

# Ranking
st.markdown("## 🥇 Ranking de Disponibilidad")
render_leaderboard(stations_data, columns=['Estación', 'Uptime'])

# Grid
st.markdown("## 📊 Scores de Desempeño")
performance = {
    'Centro': {'score': 98, 'label': 'Excelente'},
    'Norte': {'score': 87, 'label': 'Muy Bueno'},
    'Sur': {'score': 74, 'label': 'Aceptable'},
    'Este': {'score': 68, 'label': 'Mejorar'}
}
render_performance_grid(performance)

# Tabla comparativa
st.markdown("## 📋 Comparativa Detallada")
comparison = pd.DataFrame({
    'Estación': ['Centro', 'Norte', 'Sur', 'Este'],
    'Objetivo': ['95%', '95%', '95%', '95%'],
    'Actual': ['98.5%', '97.2%', '95.1%', '92.3%'],
    'Diferencia': ['+3.5%', '+2.2%', '+0.1%', '-2.7%']
})
render_comparison_table(comparison, highlight_columns=['Diferencia'])
```

---

## 🎨 Guía de Colores

### Paleta Premium
- **Primario**: `#667eea` → `#764ba2` (Morado-Azul)
- **Éxito**: `#4caf50` (Verde)
- **Advertencia**: `#ffa500` (Naranja)
- **Crítico**: `#ff6b6b` (Rojo)
- **Info**: `#4facfe` → `#00f2fe` (Cyan)
- **Oro**: `#ffd700` (Medalla)
- **Plata**: `#c0c0c0` (Medalla)
- **Bronce**: `#cd7f32` (Medalla)

---

## 💡 Mejores Prácticas

1. **Usa Gauge Metrics** para KPIs principales (disponibilidad, eficiencia)
2. **Usa Threat Meter** para alertas de riesgo acumulativo
3. **Usa Award Badges** para reconocer desempeño excepcional
4. **Usa Leaderboards** para crear competencia sana
5. **Usa Impact Cards** para mostrar impacto financiero
6. **Combina indicadores** en la misma fila para comparación visual

---

## 🐛 Troubleshooting

### "Error: hex_to_rgb no está definido"
✅ La función está duplicada en cada módulo, copia-pégala si falta

### "Gráfico Plotly no carga"
✅ Asegúrate de: `st.plotly_chart(figura, use_container_width=True)`

### "Estilos HTML no aplican"
✅ Verifica: `st.markdown(html, unsafe_allow_html=True)`

---

## 📞 Soporte

Para preguntas o mejoras, revisa la estructura modular:
- `advanced_metrics.py` - Gráficos avanzados (Plotly-based)
- `realtime_indicators.py` - Indicadores HTML/CSS (Streamlit natives)
- `performance_scoreboard.py` - Tables y rankings (HTML-based)

¡Disfruta del dashboard premium! 🚀
