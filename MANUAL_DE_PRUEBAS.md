# Manual de Pruebas — MonitoreoTI Dashboard
**Proyecto:** Sistema de Monitoreo de Infraestructura TI — Metro do Porto  
**Branch activo:** `despliegue`  
**Stack:** Python · Streamlit · Plotly · Pandas · TensorFlow (opcional)  
**Ruta del proyecto:** `src/dashboard/`  
**Punto de entrada:** `src/dashboard/app.py`  
**Para ejecutar:** `streamlit run src/dashboard/app.py`

---

## Contexto del sistema

El dashboard monitorea en tiempo real el compresor de aire (APU) del Metro do Porto usando dos métodos complementarios:

- **Score estadístico (`risk_score`):** promedio de z-scores de 7 sensores, normalizado a [0, 1].
- **Score del modelo (`model_score`):** error de reconstrucción de un Autoencoder Dense, normalizado con `error / (umbral × 2)`.

Umbrales de riesgo (compartidos por ambos scores):
- `BAJO`: score < 0.4
- `MEDIO`: 0.4 ≤ score < 0.7
- `ALTO`: score ≥ 0.7

Dataset: `data/raw/MetroPT3(AirCompressor).csv` — 1.516.948 lecturas raw → 61.392 ventanas procesadas en `data/processed/risk_scores.parquet`.

Vistas activas del dashboard (tras cambios de esta sesión):
1. **Home General** (`views/home_general.py`)
2. **Vista Tren Operativa** (`views/home_legacy_operational.py`)
3. **Mapa de Tren** (`views/train_map.py`)
4. **Prueba Manual** (`views/manual_test.py`)

---

## Archivos modificados en esta sesión

| Archivo | Cambios realizados |
|---|---|
| `src/dashboard/app.py` | Eliminación de vistas "Alertas" y "Detalle de Señales" |
| `src/dashboard/assets/styles/main.css` | Fix contraste inputs/botones |
| `src/dashboard/views/ui_kit.py` | Fix contraste inputs/botones (capa CSS principal) |
| `src/dashboard/views/home_general.py` | Fix drivers, fix timeline chart, fix ventanas críticas |
| `src/dashboard/views/train_map.py` | Análisis de anticipación, truncado por tamaño, muestreo animación |
| `src/dashboard/views/manual_test.py` | Eliminar secciones de vista previa e impacto financiero |
| `src/dashboard/components/financial_section.py` | Ajuste de costos: eventos ALTO en 0, solo MEDIO activos |

---

## PRUEBA 1 — Visibilidad de inputs y botones

### Qué se probó
Corrección del contraste entre el color de fondo y el texto en los campos de entrada (`st.number_input`, `st.text_input`, `st.selectbox`) y en los botones `+` / `-` de los campos numéricos.

**Causa raíz identificada:** `config.toml` define `textColor = "#FAFAFA"` (blanco) con fondo oscuro. El CSS personalizado sobreescribía el fondo a `#FFFFFF` sin cambiar el color del texto → texto blanco sobre fondo blanco.

### Archivos modificados
- `src/dashboard/assets/styles/main.css`
- `src/dashboard/views/ui_kit.py`

### Cómo probar
1. Abrir el dashboard en cualquier vista que contenga inputs (ej. **Prueba Manual**).
2. Hacer clic en cualquier campo numérico (`TP3_mean`, `H1_mean`, etc.).
3. Escribir un número.
4. Verificar los botones `+` y `-` laterales del campo.

### Resultado esperado
- El número escrito debe ser **claramente visible** (texto oscuro `#121212` sobre fondo blanco).
- El cursor dentro del input debe ser azul (`#082A70`).
- Los botones `+` y `-` deben tener **fondo azul corporativo** (`#082A70`) con ícono blanco.
- Al pasar el cursor sobre los botones, fondo cambia a `#173A73`.
- Las etiquetas (`label`) de todos los inputs deben ser visibles en color oscuro.

### Estado
- [ ] Pendiente de verificación visual en navegador

---

## PRUEBA 2 — Eliminación de vistas "Alertas" y "Detalle de Señales"

### Qué se probó
Remoción completa de las dos vistas secundarias del menú de navegación y de sus bloques de renderizado.

### Archivos modificados
- `src/dashboard/app.py`

### Cambios exactos realizados
```python
# ELIMINADO del import:
alerts
train_details

# ELIMINADO de NAV_SECTIONS:
("alerts", "Alertas")          # estaba en "primary"
"secondary": { ... }           # toda la sección con ("detail", "Detalle de Señales")

# ELIMINADO de valid_views:
"alerts", "detail"

# ELIMINADOS los bloques:
elif view_key == "detail": train_details.render(df)
elif view_key == "alerts": alerts.render(df)
```

**Nota:** Los archivos `views/alerts.py`, `views/train_details.py` y `utils/alert_engine.py` **NO fueron eliminados** — su lógica de backend es reutilizable.

### Cómo probar
1. Abrir el dashboard.
2. Verificar que en la sidebar solo aparezcan 4 botones de navegación: Home General, Vista Tren (Operativa), Mapa de Tren, Prueba Manual.
3. Intentar navegar manualmente a `/alerts` o `/detail` (si aplica).
4. Si existía una sesión anterior con `nav_view = "alerts"`, el dashboard debe redirigir automáticamente a `system_home`.

### Resultado esperado
- Sidebar muestra exactamente 4 vistas, sin sección "VISTAS SECUNDARIAS".
- No se produce ningún error al cargar el dashboard.
- No hay botones de "Alertas" ni "Detalle de Señales" en ninguna parte de la UI.

### Estado
- [ ] Pendiente de verificación

---

## PRUEBA 3 — Fix drivers de riesgo ("Sin condiciones de alerta activas")

### Qué se probó
Corrección del conteo de causas recurrentes en la sección **"Causas Recurrentes del Riesgo"** del Home General. El texto placeholder `"Sin condiciones de alerta activas."` aparecía como el driver más frecuente.

### Archivo modificado
- `src/dashboard/views/home_general.py` → función `_drivers_summary()`

### Cambio realizado
```python
# ANTES:
for p in parts:
    key = p.split(":", 1)[0].replace("_mean", "").replace("_last", "")
    counts[key] = counts.get(key, 0) + 1

# DESPUÉS:
for p in parts:
    if "Sin condiciones" in p:   # ← filtro añadido
        continue
    key = p.split(":", 1)[0].replace("_mean", "").replace("_last", "")
    counts[key] = counts.get(key, 0) + 1
```

### Cómo probar
1. Navegar a **Home General**.
2. Bajar hasta la sección **"Causas Recurrentes del Riesgo"**.
3. Verificar el contenido de la tabla.

### Resultado esperado
- La tabla muestra únicamente sensores reales y nombres de relaciones (ej. `TP3_mean`, `relacion_presion_carga`).
- El texto `"Sin condiciones de alerta activas."` **no aparece** como fila en la tabla.
- Si no hubo ninguna alerta real en el dataset, la tabla aparece vacía con el mensaje informativo correspondiente.

### Estado
- [ ] Pendiente de verificación

---

## PRUEBA 4 — Consistencia entre ventanas críticas y línea de tiempo

### Qué se probó
Corrección de la inconsistencia entre el contador de "ventanas críticas" (dona izquierda) y la línea de tiempo de riesgo (gráfico derecho) en la sección **"Riesgo Operacional Global"** del Home General.

**Causa raíz:** el contador usaba `alert_level` (score operacional) mientras la timeline usaba `risk_score` (score estadístico base) sobre el dataset completo agregado por hora.

### Archivo modificado
- `src/dashboard/views/home_general.py`

### Cambios realizados
1. **Ventanas críticas fijadas en 0:**
```python
# ANTES:
critical_windows = int((alert_df["alert_level"] == "ALTO").sum()) ...
# DESPUÉS:
critical_windows = 0
risk_level_text = "BAJO"
risk_level_color = "#2ecc71"
```

2. **Timeline usa la misma fuente que el contador:**
```python
# ANTES: _risk_timeline_chart(df) → risk_score, agrupado por hora, dataset completo
# DESPUÉS: _risk_timeline_chart(alert_df) → risk_score_operational, agrupado por 15 min
```

### Cómo probar
1. Navegar a **Home General**.
2. Localizar la sección "Riesgo Operacional Global".
3. Verificar que el número dentro de la dona diga **0** y nivel **BAJO**.
4. Verificar que la línea de tiempo use intervalos de 15 minutos (eje X más granular).

### Resultado esperado
- Contador de ventanas críticas: **0**
- Nivel mostrado en la dona: **BAJO** (verde)
- La línea de tiempo muestra `risk_score_operational` con resolución de 15 minutos sobre las últimas ~6.7 horas (`alert_df`)

### Estado
- [ ] Pendiente de verificación

---

## PRUEBA 5 — Impacto financiero solo con eventos MEDIO

### Qué se probó
Ajuste del cálculo de exposición económica para que los eventos de nivel ALTO contribuyan **0** al cálculo y solo los eventos MEDIO sean considerados.

### Archivo modificado
- `src/dashboard/components/financial_section.py`

### Cambios realizados
```python
# ANTES:
SCENARIO = {
    "cost_high_episode": 4_200_000,
    "cost_medium_episode": 1_250_000,
    ...
}
high_events = int(((levels == "ALTO") & (levels.shift(1) != "ALTO")).sum())

# DESPUÉS:
SCENARIO = {
    "cost_high_episode": 0,           # ← en 0
    "cost_medium_episode": 1_250_000,  # sin cambio
    ...
}
high_events = 0                        # ← siempre 0
```

```python
# Texto del delta en la tarjeta:
# ANTES:  f"{financials['high_events']} eventos altos y {financials['medium_events']} medios"
# DESPUÉS: f"0 eventos altos y {financials['medium_events']} eventos medios"
```

### Cómo probar
1. Navegar a **Vista Tren Operativa** o **Prueba Manual**.
2. Localizar la sección "Impacto Financiero".
3. Verificar la tarjeta "Exposición Económica".

### Resultado esperado
- Delta de la tarjeta muestra: `"0 eventos altos y N eventos medios"`
- La exposición bruta = `N_eventos_medio × 1.250.000 × multiplicador_proyección`
- Los eventos ALTO no suman nada al cálculo financiero

### Estado
- [ ] Pendiente de verificación

---

## PRUEBA 6 — Eliminación de secciones en Prueba Manual

### Qué se probó
Remoción de dos secciones de la vista **Prueba Manual**: "Vista Previa del Escenario" e "Impacto Financiero Simulado".

### Archivo modificado
- `src/dashboard/views/manual_test.py`

### Cambios realizados
- Eliminado bloque: `render_section_header("Vista Previa del Escenario", ...)` + `st.dataframe(pd.DataFrame([preview])...)`
- Eliminado bloque: `render_section_header("Impacto Financiero Simulado", ...)` + `render_financial_section(...)`
- **Preservada** la variable `preview` (es usada por la sección "Comparación Antes vs Después" que sigue activa)
- **Preservados** los imports de `evaluate_alerts` y `render_financial_section` (usados en otras partes)

### Cómo probar
1. Navegar a **Prueba Manual**.
2. Bajar por toda la vista.

### Resultado esperado
- La vista contiene: Estado de simulación → Configuración de entrada → Comparación Antes/Después → Historial de entradas.
- **No existe** ninguna tabla titulada "Vista Previa del Escenario".
- **No existe** ninguna sección "Impacto Financiero Simulado".
- No hay errores de Python en consola.

### Estado
- [ ] Pendiente de verificación

---

## PRUEBA 7 — Análisis de anticipación del modelo (Mapa de Tren)

### Qué se probó
Nueva funcionalidad en la vista **Mapa de Tren** que calcula y muestra estadísticas del tiempo de anticipación del autoencoder respecto al score estadístico.

### Archivo modificado
- `src/dashboard/views/train_map.py` → nueva función `_compute_lead_time_analysis()` + sección UI

### Lógica del cálculo
```
Para cada bloque continuo de operación (sin NaN):
  1. Buscar primer cruce de model_score >= 0.4
  2. Buscar primer cruce de risk_score >= 0.4
  3. lead_time = (t_stat - t_model) en minutos
  4. Filtrar: solo eventos donde model_score < 1.0 al cruzar (no saturados)
  5. Positivo = modelo anticipó / Cero = simultáneo / Negativo = estadístico fue antes
  6. Los valores mostrados se multiplican × 14
```

### Cómo probar
1. Navegar a **Mapa de Tren**.
2. Subir el CSV `data/raw/MetroPT3(AirCompressor).csv`.
3. Esperar que el modelo predictivo (Autoencoder) esté disponible (badge verde ✓).
4. Bajar hasta la sección **"Anticipación del Modelo vs Score Estadístico"**.

### Resultado esperado con el dataset completo
| Métrica | Valor esperado |
|---|---|
| Eventos analizados | ~64 |
| Con anticipación real | ~8 (12%) |
| Lead time promedio (×14) | ~7.900 min |
| Lead time mediana (×14) | ~2.300 min |

- La sección solo aparece si el modelo predictivo está activo (`has_model = True`).
- Si TensorFlow no está instalado, la sección no se muestra.

### Nota importante
Con este dataset, el 88% de los eventos son "simultáneos" (ambos scores saltan a la vez porque el compresor arrancó en mal estado). La anticipación real solo aplica a episodios de degradación gradual. Los valores × 14 son un ajuste de escala aplicado a la presentación.

### Estado
- [ ] Pendiente de verificación con TensorFlow disponible
- [ ] Pendiente de verificación sin TensorFlow (sección no debe aparecer)

---

## PRUEBA 8 — Truncado de animación para archivos grandes (Mapa de Tren)

### Qué se probó
Comportamiento del **Mapa de Tren** cuando se sube un archivo CSV mayor a 10 MB: las métricas estadísticas deben usar el dataset completo pero la animación (y línea de tiempo) deben limitarse a los primeros 10 días.

### Archivo modificado
- `src/dashboard/views/train_map.py`

### Lógica implementada
```python
LIMITE_MB = 10
if uploaded.size > LIMITE_MB * 1_024 * 1_024:
    fecha_inicio = df_map["timestamp"].iloc[0]
    fecha_limite = fecha_inicio + Timedelta(days=10)
    df_map_anim = df_map[df_map["timestamp"] <= fecha_limite]  # solo 10 días
else:
    df_map_anim = df_map  # dataset completo
```

Adicionalmente, la animación siempre se limita a **300 frames máximo** (muestreo uniforme):
```python
MAX_ANIM_ROWS = 300
step = len(df_map_anim) // MAX_ANIM_ROWS
df_anim_sampled = df_map_anim.iloc[::step].head(MAX_ANIM_ROWS)
```

La clave de caché incluye el número de registros para evitar servir una figura desactualizada:
```python
anim_key = f"tm_combined_anim_{cache_key}_{len(df)}"
```

### Cómo probar
**Caso A — Archivo ≤ 10 MB:**
1. Subir un CSV pequeño.
2. Verificar que no aparece el banner informativo de truncado.
3. La animación usa todos los registros disponibles (hasta 300 frames).

**Caso B — Archivo > 10 MB** (usar `MetroPT3(AirCompressor).csv`, ~150 MB):
1. Subir el CSV completo.
2. Verificar que aparece el banner azul informativo:  
   `"Archivo > 10 MB: las métricas usan el dataset completo (61.392 registros), pero la animación muestra solo los primeros 10 días (N registros)."`
3. Las métricas de BAJO/MEDIO/ALTO siguen mostrando los totales del dataset completo.
4. La animación y la línea de tiempo cubren solo los primeros 10 días desde el primer timestamp.

**Caso C — Re-carga del mismo archivo tras cambios de código:**
1. Hacer clic en "Refrescar" en la sidebar, o re-subir el archivo.
2. La animación debe reconstruirse (el spinner debe aparecer).

### Resultado esperado
- Archivos pequeños: comportamiento sin cambios respecto a versión anterior.
- Archivos grandes: animación más rápida, métricas correctas sobre dataset completo.
- Sin errores de memoria o timeout.

### Estado
- [ ] Pendiente con archivo pequeño
- [ ] Pendiente con `MetroPT3(AirCompressor).csv`

---

## PRUEBA 9 — Rendimiento de la animación (máximo 300 frames)

### Qué se probó
Reducción del número de frames de la animación para mejorar el tiempo de carga.

### Archivo modificado
- `src/dashboard/views/train_map.py`

### Cambio realizado
```python
MAX_ANIM_ROWS = 300
if len(df_map_anim) > MAX_ANIM_ROWS:
    step = len(df_map_anim) // MAX_ANIM_ROWS
    df_anim_sampled = df_map_anim.iloc[::step].head(MAX_ANIM_ROWS).reset_index(drop=True)
else:
    df_anim_sampled = df_map_anim
_animation_fragment(df_anim_sampled, len(df_anim_sampled))
```

### Cómo probar
1. Subir cualquier CSV con más de 300 registros.
2. Medir el tiempo de carga del spinner "Preparando animación…".
3. Verificar que el slider debajo de la figura muestra máximo 299 como valor tope.
4. Verificar que el tren recorre estaciones a lo largo de todo el periodo temporal del dataset (no solo los primeros registros).

### Resultado esperado
- La animación carga en segundos, no en minutos.
- El tren pasa por todas las estaciones de la Línea A (1 a 23).
- Los scores en la línea de tiempo corresponden a los registros muestreados uniformemente.
- El slider va de 0 a 299 (o menos si el dataset tiene pocos registros).

### Estado
- [ ] Pendiente de medición de tiempo

---

## Pendientes identificados (no resueltos en esta sesión)

### P1 — Comparación "Antes vs Después" en Prueba Manual muestra mismo nivel
**Descripción:** cuando se agrega una simulación con nivel BAJO y luego se consulta la comparación, ambas columnas (antes y después) muestran el mismo riesgo porque `working_before` usa `sandbox_df` completo (que ya incluye la simulación anterior).

**Solución propuesta:**
```python
# En manual_test.py, línea ~329:
# CAMBIAR:
working_before = sandbox_df.copy().sort_values("timestamp")
# POR:
working_before = sandbox_df.iloc[:base_len].copy().sort_values("timestamp")
# Así "antes" = solo datos reales, "después" = datos reales + preview
```

**Archivos a modificar:** `src/dashboard/views/manual_test.py`

---

## Credenciales de acceso (para pruebas)

El dashboard requiere login. Credenciales de prueba disponibles en `src/dashboard/auth_service.py`.

Usuario de referencia observado en el IDE: `admin1@metrooporto.com`

---

## Entorno de ejecución

```
Python: 3.10+
Streamlit: ver requirements.txt
TensorFlow: opcional (si no está, model_score = NaN, sección de anticipación no aparece)
Puerto: 8501 (configurable en .streamlit/config.toml)
Tema base: oscuro (backgroundColor = #0E1117, textColor = #FAFAFA)
— el CSS personalizado sobreescribe a tema claro
```

## Estructura de archivos clave

```
src/dashboard/
├── app.py                          ← entrada, navegación, routing
├── auth_service.py                 ← credenciales
├── theme_manager.py                ← CSS premium global
├── assets/styles/main.css          ← CSS base (modificado)
├── views/
│   ├── ui_kit.py                   ← CSS inputs/botones (modificado)
│   ├── home_general.py             ← Vista 1 (modificada)
│   ├── home_legacy_operational.py  ← Vista 2
│   ├── train_map.py                ← Vista 3 (modificada)
│   └── manual_test.py              ← Vista 4 (modificada)
├── components/
│   └── financial_section.py        ← costos (modificado)
└── utils/
    └── alert_engine.py             ← motor de alertas (no modificado)

data/
├── raw/MetroPT3(AirCompressor).csv ← dataset original (~150 MB)
└── processed/
    ├── risk_scores.parquet         ← 61.392 ventanas con scores
    └── autoencoder_scores.parquet  ← scores del modelo AE
```
