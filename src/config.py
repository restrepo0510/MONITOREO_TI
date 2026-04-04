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

# Scores generados por el modelo (archivo completo con sensores + riesgo)
# NOTA: este es el archivo que conserva TODAS las columnas necesarias
# para el dashboard de monitoreo (incluye señales por sensor).
DATA_RISK_SCORES_PATH = "data/processed/risk_scores.parquet"

# Compatibilidad retroactiva:
# algunos módulos antiguos referencian DATA_SCORES_PATH.
DATA_SCORES_PATH = DATA_RISK_SCORES_PATH

# Exportes de salida para integración (resumen liviano de riesgo)
DATA_MODEL_OUTPUT_PARQUET_PATH = "data/output/model_output.parquet"
DATA_MODEL_OUTPUT_CSV_PATH = "data/output/model_output.csv"
DATA_MODEL_OUTPUT_SQLITE_PATH = "data/output/model_output.db"

# Fuente oficial del dashboard:
# - Debe incluir columnas de sensores para visualización detallada.
# - Por eso NO se usa model_output.* como fuente principal del front.
DASHBOARD_SOURCE_OF_TRUTH_PATH = DATA_RISK_SCORES_PATH

# Umbrales fijos por sensor calibrados con histórico sano.
# Este artefacto permite alertamiento formal estable y trazable.
SENSOR_THRESHOLDS_PATH = "data/processed/sensor_thresholds.json"

# Politica operacional para acciones recomendadas.
# Define acciones por nivel de alerta y por sensor.
RECOMMENDATION_POLICY_PATH = "src/dashboard/config/recommended_actions.json"

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

# Ruta de persistencia de parámetros de escalado del risk_score.
# Este archivo evita recalcular min/max global en cada corrida y
# ayuda a mantener estabilidad de score en operación continua.
RISK_SCALER_PARAMS_PATH = "data/processed/risk_scaler_params.json"

# Si es True, se reutilizan parámetros guardados cuando existan.
# Si es False, se recalibran en cada ejecución (modo experimental).
RISK_SCALER_REUSE_PARAMS = True

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
# ============================================================
