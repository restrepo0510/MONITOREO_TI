"""
Configuración central del sistema de monitoreo y predicción.

Este archivo centraliza:
- Rutas del proyecto
- Parámetros temporales
- Parámetros del modelo
- Umbrales de decisión
- Configuración de logging

Permite modificar comportamiento del sistema sin tocar los módulos.
"""

# =========================
# RUTAS DEL SISTEMA
# =========================

# Datos crudos
DATA_RAW_PATH = "data/raw/MetroPT3(AirCompressor).csv"

# Dataset base procesado por ingesta
DATA_BASE_PATH = "data/processed/base.parquet"

# Features generadas por preprocessing
DATA_FEATURES_PATH = "data/processed/features.parquet"

# Scores generados por el modelo
DATA_SCORES_PATH = "data/processed/scores.parquet"

# Carpeta de logs
LOG_DIR = "logs"


# =========================
# PARÁMETROS TEMPORALES
# =========================

# Tamaño de ventana para cálculo de features (en segundos)
WINDOW_SIZE_SECONDS = 120

# Horizonte de predicción (anticipación mínima prometida)
PREDICTION_HORIZON_MINUTES = 120


# =========================
# PARÁMETROS DEL MODELO
# =========================

# Umbral para clasificar riesgo alto
RISK_THRESHOLD_HIGH = 0.7

# Umbral para clasificar riesgo medio
RISK_THRESHOLD_MEDIUM = 0.4

# Número mínimo de sensores relevantes requeridos
MIN_REQUIRED_SENSORS = 3


# =========================
# CONFIGURACIÓN DE LOGS
# =========================

# Activar logging estructurado
ENABLE_STRUCTURED_LOGGING = True

# Nivel mínimo de severidad
LOG_LEVEL = "INFO"


# =========================
# CONFIGURACIÓN DE DASHBOARD
# =========================

# Número máximo de registros mostrados por defecto
MAX_ROWS_DASHBOARD = 500

# Activar visualización de estado del sistema
SHOW_SYSTEM_STATUS = True

# ============================================================
# RELACIÓN DIRECTA CON EL PROYECTO
# ============================================================
#
# Esta configuración central está alineada con los objetivos
# definidos en el documento técnico del proyecto:
#
# - Anticipación mínima de 2 horas:
#   Se implementa mediante PREDICTION_HORIZON_MINUTES,
#   que define el horizonte de predicción del modelo.
#
# - Ventanas temporales de análisis:
#   Se controlan con WINDOW_SIZE_SECONDS, que determina
#   el tamaño de las ventanas para cálculo de features.
#
# - Umbrales de clasificación de riesgo:
#   Se definen con RISK_THRESHOLD_HIGH y RISK_THRESHOLD_MEDIUM,
#   coherentes con la estrategia de reducción de falsas alarmas.
#
# - Monitoreo y trazabilidad:
#   LOG_DIR centraliza la ubicación de los logs estructurados,
#   cumpliendo el KR de registrar el 100% de eventos clave.
#
# - Dashboard operativo:
#   MAX_ROWS_DASHBOARD y SHOW_SYSTEM_STATUS permiten
#   controlar visualización y estado del sistema en monitoreo.
#
# Esta sección garantiza coherencia entre diseño conceptual
# (documento) y configuración técnica (implementación).
# ============================================================