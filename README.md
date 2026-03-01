# 🚆 Sistema de Monitoreo y Predicción de Fallas en Infraestructura de TI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> Sistema de mantenimiento predictivo basado en machine learning para la detección temprana de fallas en unidades de producción de aire (APU) del Metro de Porto, Portugal.

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Tecnologías](#️-tecnologías)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Dataset](#-dataset)
- [Resultados Esperados](#-resultados-esperados)
- [Contribuidores](#-contribuidores)
- [Roadmap](#️-roadmap)
- [Licencia](#-licencia)

---

## 🎯 Descripción

Este proyecto desarrolla un **sistema prototipo de mantenimiento predictivo** que utiliza técnicas de aprendizaje automático para anticipar fallas en equipos críticos de infraestructura ferroviaria. El sistema procesa datos de telemetría en tiempo real de 20 variables (sensores analógicos, señales digitales y GPS) para:

- 🔍 **Detectar anomalías** en el comportamiento operativo
- 📊 **Predecir riesgo de falla** con 2+ horas de anticipación
- 📈 **Monitorear degradación** progresiva de componentes
- 🚨 **Generar alertas** accionables para equipos de mantenimiento

### ¿Por qué es importante?

El mantenimiento tradicional (reactivo o preventivo) genera:
- ⏱️ Tiempos de inactividad no planificados
- 💰 Costos elevados de reparaciones de emergencia
- 🔄 Reemplazos prematuros o tardíos de componentes

Nuestro enfoque **predictivo** permite:
- ✅ Planificar mantenimientos con anticipación
- ✅ Reducir interrupciones de servicio
- ✅ Optimizar uso de recursos técnicos
- ✅ Tomar decisiones basadas en datos reales

---

## ✨ Características

### Fase 1: Monitoreo Básico
- 📊 **Dashboard de Flota**: Vista agregada de todos los trenes con ranking por riesgo
- 🔎 **Dashboard de Tren Individual**: Evolución temporal de sensores clave y health index
- 🚦 **Semaforización**: Estado visual (Normal / Observación / Riesgo Alto)
- 📥 **Exportación**: Reportes CSV de trenes en riesgo

### Fase 2: Análisis Predictivo
- 🤖 **Modelo de Machine Learning**: Predicción de riesgo a horizonte de 2 horas
- 📉 **Detección de Anomalías**: Score por ventana temporal usando desviación estadística
- 📈 **Análisis de Tendencias**: Clasificación de degradación (Estable / Leve / Acelerada)
- ⚠️ **Sistema de Alertas**: Notificaciones automáticas cuando riesgo ≥ Alto

### Fase 3: Trazabilidad
- 📝 **Logs Estructurados (JSON)**: Registro completo de eventos del sistema
- ⏱️ **Métricas de Performance**: Latencias, tasa de procesamiento, errores
- 🔍 **Auditoría**: Evidencia completa por cada predicción (sensor, ciclo, scores)

---

## 🛠️ Tecnologías

### Core
- **Python 3.10+**: Lenguaje principal
- **Pandas**: Manipulación de datos tabulares
- **NumPy**: Computación numérica
- **Scikit-learn**: Machine Learning (clasificación, regresión)

### Visualización & Dashboard
- **Streamlit**: Framework para dashboards interactivos
- **Plotly**: Gráficos interactivos
- **Matplotlib/Seaborn**: Visualizaciones estáticas

### Almacenamiento
- **SQLite** / **Parquet**: Base de datos local (decisión en Sprint 1)
- **JSON**: Logs estructurados

### Desarrollo
- **Git/GitHub**: Control de versiones
- **Jupyter**: Notebooks para EDA
- **pytest**: Testing
- **black**: Formateo de código

---

## 🚀 Instalación

### Prerrequisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Git

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/predictive-maintenance.git
cd predictive-maintenance
```

### Paso 2: Crear entorno virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Descargar el dataset

1. Visitar [MetroPT-3 Dataset en Kaggle](https://www.kaggle.com/datasets/joebeachcapital/metropt-3-dataset)
2. Descargar el archivo CSV principal
3. Colocar en `data/raw/MetroPT3.csv`

**Estructura esperada:**
```
data/raw/MetroPT3.csv    # ~1.5 GB, 10,979,547 filas × 20 columnas
```

---

## 💻 Uso

### 1. Ingesta de Datos

Cargar y validar el dataset:

```bash
python src/ingesta/loader.py
```

**Salida esperada:**
- ✅ Validación de 10,979,547 registros
- ✅ Confirmación de 20 variables
- ✅ Generación de estadísticas descriptivas
- ✅ Logs JSON en `logs/ingestion_YYYY-MM-DD.json`

### 2. Análisis Exploratorio

Abrir notebooks interactivos:

```bash
jupyter notebook notebooks/01_exploratory_analysis.ipynb
```

### 3. Preprocesamiento

Generar features y etiquetar datos:

```bash
python src/preprocessing/feature_engineering.py
```

### 4. Entrenamiento del Modelo

```bash
python src/analysis/risk_prediction.py --train
```

### 5. Lanzar Dashboard

```bash
streamlit run src/dashboard/app.py
```

El dashboard estará disponible en: `http://localhost:8501`

---

## 📊 Dataset

### MetroPT-3: Predictive Maintenance Dataset

**Fuente:** [Nature Scientific Data - The MetroPT dataset for predictive maintenance](https://www.nature.com/articles/s41597-022-01877-3)

**Descripción:**
- 🚆 Datos reales del Metro de Porto, Portugal
- 📅 Periodo: Enero - Junio 2022
- 📏 Tamaño: 10,979,547 registros × 20 variables
- ⚙️ Frecuencia: 1 Hz (1 registro por segundo)
- 🔧 Componente: Air Production Unit (APU) de tren

### Variables del Dataset

#### Sensores Analógicos (8)
1. **TP2**: Presión en compresor (bar)
2. **TP3**: Presión en panel neumático (bar)
3. **H1**: Válvula activada cuando presión > 10.2 bar (bar)
4. **DV_pressure**: Presión por descarga de torres secadoras (bar)
5. **Reservoirs**: Presión en tanques de aire (bar)
6. **Oil_Temperature**: Temperatura del aceite (°C)
7. **Flowmeter**: Flujo de aire (m³/h)
8. **Motor_Current**: Corriente del motor (A)

#### Señales Digitales (8)
9. **COMP**: Señal de válvula de admisión
10. **DV_electric**: Señal de válvula de salida del compresor
11. **TOWERS**: Indica torre activa (1 o 2)
12. **MPG**: Activación de válvula cuando presión < 8.2 bar
13. **LPS**: Señal cuando presión < 7 bar
14. **Pressure_switch**: Señal de válvula piloto
15. **Oil_Level**: Nivel de aceite bajo
16. **Caudal_impulses**: Impulsos de flujo por segundo

#### GPS (4)
17. **gpsLong**: Longitud (°)
18. **gpsLat**: Latitud (°)
19. **gpsSpeed**: Velocidad (km/h)
20. **gpsQuality**: Calidad de señal

### Fallas Documentadas

El dataset contiene **3 fallas catastróficas** con timestamps exactos:

| Falla | Tipo | Fecha | Duración | Componente Afectado |
|-------|------|-------|----------|---------------------|
| **Falla 1** | Fuga de aire (clientes) | 28 Feb - 1 Mar 2022 | ~24h | Tubería de alimentación |
| **Falla 2** | Fuga de aire (secador) | 23 Mar 2022 | ~3h | Válvula piloto neumática |
| **Falla 3** | Fuga de aceite | 30 May - 2 Jun 2022 | ~72h | Motor del compresor |

---

## 🎯 Resultados Esperados

### Key Results (OKRs)

| KR | Métrica | Meta | Estado |
|----|---------|------|--------|
| KR1 | Sensores predictivos identificados | ≥ 3 sensores | 🔄 En progreso |
| KR2 | ROC-AUC del modelo en test | ≥ 0.75 | ⏳ Pendiente |
| KR3 | Recall en clase Riesgo Alto | ≥ 60% | ⏳ Pendiente |
| KR4 | Motores Alto riesgo con alerta | ≥ 95% | ⏳ Pendiente |
| KR5 | Eventos registrados en logs | 100% | ✅ Implementado |

### Métricas de Éxito

- ✅ Detección de fallas al menos **2 horas antes** de materializarse
- ✅ Tasa de falsos positivos **< 15%**
- ✅ Sistema responde en **< 5 segundos** para consultas de dashboard
- ✅ **100% trazabilidad** de predicciones en logs

---

## 👥 Contribuidores

| Nombre | Rol | GitHub |
|--------|-----|--------|
| Juan José Álvarez | System Engineer | 
| Santiago Gómez | Data Engineer | 
| Isabella Gutiérrez | System Engineer | 
| Juan Esteban Vasco | Data Engineer | 

**Institución:** Universidad Pontificia Bolivariana (UPB)  
**Programa:** Ingeniería de Sistemas - 5to Semestre  
**Curso:** Proyecto de Ingeniería de Software  
**Periodo:** 2024-2

---

## 🗓️ Roadmap

### Sprint 1 (Semanas 1-2) ✅
- [x] Setup de repositorio
- [x] Análisis exploratorio de datos
- [x] Identificación de sensores predictivos
- [x] Sistema de logging implementado

### Sprint 2 (Semanas 3-4) 🔄
- [ ] Feature engineering completo
- [ ] Baseline de detección de anomalías
- [ ] Modelo de clasificación inicial
- [ ] Métricas de evaluación

### Sprint 3 (Semanas 5-6) ⏳
- [ ] Optimización de hiperparámetros
- [ ] Sistema de alertas
- [ ] Health index por tren
- [ ] Dashboard básico

### Sprint 4 (Semanas 7-8) ⏳
- [ ] Vista de flota completa
- [ ] Vista detallada por tren
- [ ] Integración modelo-dashboard
- [ ] Testing end-to-end

### Sprint 5 (Semanas 9-10) ⏳
- [ ] Refinamiento de UX
- [ ] Optimización de performance
- [ ] Documentación técnica
- [ ] Preparación de demo

### Sprint 6 (Semana 11) ⏳
- [ ] Testing final
- [ ] Deployment local
- [ ] Documentación de usuario
- [ ] Presentación final

---

## 📚 Referencias

### Papers Académicos
- [The MetroPT dataset for predictive maintenance](https://www.nature.com/articles/s41597-022-01877-3) - Nature Scientific Data (2022)
- [Data-driven predictive maintenance](https://ieeexplore.ieee.org/document/9923456) - IEEE Intelligent Systems (2022)

### Recursos Técnicos
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 🙏 Agradecimientos

- **Metro do Porto** por proporcionar los datos reales de operación
- **Bruno Veloso et al.** por publicar y documentar el dataset MetroPT-3
- **Universidad Pontificia Bolivariana** por el apoyo académico

---

<div align="center">

Hecho con ❤️ por estudiantes de Ingeniería de Sistemas UPB

</div>
