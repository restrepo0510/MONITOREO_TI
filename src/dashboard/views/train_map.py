"""
Vista de Mapa de Tren en Tiempo Real - Línea A del Metro.

Permite subir un CSV con mediciones de sensores y visualizar el tren
moviéndose entre las 23 estaciones de la Línea A, con código de color
según el nivel de riesgo activo.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.views.ui_kit import render_section_header, render_view_header

# ---------------------------------------------------------------------------
# Configuración de la línea
# ---------------------------------------------------------------------------

NUM_STATIONS = 23

STATION_NAMES: list[str] = [f"Est. {i + 1}" for i in range(NUM_STATIONS)]

# Colores por nivel de riesgo
LEVEL_COLORS = {
    "BAJO": "#22C55E",   # verde
    "MEDIO": "#F97316",  # naranja
    "ALTO": "#EF4444",   # rojo
}

LEVEL_LABELS = {
    "BAJO": "Normal",
    "MEDIO": "Alerta Media",
    "ALTO": "Alerta Alta",
}

RENAME_MAP = {
    "Oil_temperature": "Oil_Temperature",
    "Motor_current": "Motor_Current",
    "DV_eletric": "DV_electric",
    "Towers": "TOWERS",
    "Oil_level": "Oil_Level",
}

ANALOG_SENSORS = [
    "TP2", "TP3", "H1", "DV_pressure",
    "Reservoirs", "Oil_Temperature", "Motor_Current",
]

RISK_THRESHOLD_ALTO = 0.7
RISK_THRESHOLD_MEDIO = 0.4


# ---------------------------------------------------------------------------
# Procesamiento de datos
# ---------------------------------------------------------------------------

def _risk_level(score: float) -> str:
    if score >= RISK_THRESHOLD_ALTO:
        return "ALTO"
    if score >= RISK_THRESHOLD_MEDIO:
        return "MEDIO"
    return "BAJO"


def _compute_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula risk_score y risk_level mediante z-scores sobre los sensores
    analógicos disponibles. Sólo se invoca cuando el CSV no trae estas columnas.
    """
    sensors = [s for s in ANALOG_SENSORS if s in df.columns]

    if not sensors:
        df["risk_score"] = 0.1
        df["risk_level"] = "BAJO"
        return df

    z_df = pd.DataFrame(index=df.index)
    for s in sensors:
        col = pd.to_numeric(df[s], errors="coerce").fillna(0.0)
        std = col.std()
        if std > 0:
            z_df[s] = ((col - col.mean()) / std).abs()
        else:
            z_df[s] = 0.0

    avg_z = z_df.mean(axis=1)
    # z > 3 se considera muy anómalo → clip a [0, 1]
    df["risk_score"] = (avg_z / 3.0).clip(0.0, 1.0)
    df["risk_level"] = df["risk_score"].apply(_risk_level)
    return df


_RAW_COLUMNS = [
    "row_id", "timestamp",
    "TP2", "TP3", "H1", "DV_pressure", "Reservoirs", "Oil_Temperature", "Motor_Current",
    "COMP", "DV_electric", "TOWERS", "MPG", "LPS", "Pressure_switch", "Oil_Level", "Caudal_impulses",
]


def _process_uploaded_csv(uploaded_file) -> pd.DataFrame:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    except Exception:
        try:
            df = pd.read_csv(uploaded_file, encoding="latin-1")
        except Exception as e:
            st.error(f"Error leyendo el CSV: {e}")
            return pd.DataFrame()

    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    df.rename(columns=RENAME_MAP, inplace=True)

    # Detectar si el CSV no tiene cabeceras (ningún sensor analógico reconocido)
    has_headers = any(s in df.columns for s in ANALOG_SENSORS)
    if not has_headers:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        try:
            df = pd.read_csv(uploaded_file, header=None, encoding="utf-8-sig")
        except Exception:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, header=None, encoding="latin-1")
            except Exception:
                pass
        # Asignar nombres según el esquema del DataLoader (17 cols con índice, 16 sin)
        if df.shape[1] == len(_RAW_COLUMNS):
            df.columns = _RAW_COLUMNS
        elif df.shape[1] == len(_RAW_COLUMNS) - 1:
            df.columns = _RAW_COLUMNS[1:]  # sin row_id
        df = df.drop(columns=["row_id"], errors="ignore")
        df.rename(columns=RENAME_MAP, inplace=True)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
    else:
        df["timestamp"] = pd.date_range("2024-01-01", periods=len(df), freq="10s")

    if "risk_level" in df.columns:
        df["risk_level"] = df["risk_level"].astype(str).str.upper()
        if "risk_score" not in df.columns:
            mapping = {"BAJO": 0.2, "MEDIO": 0.55, "ALTO": 0.85}
            df["risk_score"] = df["risk_level"].map(mapping).fillna(0.2)
    elif "risk_score" in df.columns:
        df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(0.1)
        df["risk_level"] = df["risk_score"].apply(_risk_level)
    else:
        df = _compute_risk(df)

    return df


# ---------------------------------------------------------------------------
# Cálculo de posición
# ---------------------------------------------------------------------------

def _train_position(record_idx: int, total: int) -> float:
    """
    Devuelve la posición continua del tren [0, NUM_STATIONS - 1].
    El tren recorre todas las estaciones a lo largo del dataset completo.
    """
    if total <= 1:
        return 0.0
    return (record_idx / (total - 1)) * (NUM_STATIONS - 1)


def _current_station_idx(position: float) -> int:
    return min(int(position), NUM_STATIONS - 1)


# ---------------------------------------------------------------------------
# Figuras Plotly
# ---------------------------------------------------------------------------

def _build_metro_figure(df: pd.DataFrame, record_idx: int) -> go.Figure:
    row = df.iloc[record_idx]
    total = len(df)
    position = _train_position(record_idx, total)

    risk_level = str(row.get("risk_level", "BAJO")).upper()
    if risk_level not in LEVEL_COLORS:
        risk_level = "BAJO"
    train_color = LEVEL_COLORS[risk_level]
    glow = train_color + "66"

    station_x = list(range(NUM_STATIONS))
    station_y = [0] * NUM_STATIONS

    fig = go.Figure()

    # --- Línea de vía ---
    fig.add_trace(go.Scatter(
        x=station_x,
        y=station_y,
        mode="lines",
        line=dict(color="#6B7280", width=5),
        hoverinfo="none",
        showlegend=False,
    ))

    # --- Estaciones (etiquetas alternadas arriba/abajo) ---
    text_positions = [
        "top center" if i % 2 == 0 else "bottom center"
        for i in range(NUM_STATIONS)
    ]
    label_y_offsets = [0.12 if i % 2 == 0 else -0.12 for i in range(NUM_STATIONS)]
    station_label_y = [offset for offset in label_y_offsets]

    # Puntos de las estaciones
    fig.add_trace(go.Scatter(
        x=station_x,
        y=station_y,
        mode="markers",
        marker=dict(
            size=13,
            color="#374151",
            line=dict(color="#FFFFFF", width=2),
        ),
        hovertemplate=[f"<b>{n}</b><extra></extra>" for n in STATION_NAMES],
        showlegend=False,
        name="Estaciones",
    ))

    # Etiquetas alternadas como puntos invisibles con texto
    for i, name in enumerate(STATION_NAMES):
        y_off = 0.22 if i % 2 == 0 else -0.22
        fig.add_annotation(
            x=i,
            y=y_off,
            text=name,
            showarrow=False,
            font=dict(size=9, color="#374151"),
            xanchor="center",
            yanchor="middle",
        )

    # --- Tren (marcador animado) ---
    station_idx = _current_station_idx(position)
    station_name = STATION_NAMES[station_idx]
    risk_score = float(row.get("risk_score", 0.0))
    timestamp_val = row.get("timestamp", "")

    fig.add_trace(go.Scatter(
        x=[position],
        y=[0],
        mode="markers+text",
        marker=dict(
            size=26,
            color=train_color,
            line=dict(color="#FFFFFF", width=3),
            symbol="circle",
        ),
        text=["🚇"],
        textposition="top center",
        textfont=dict(size=14),
        hovertemplate=(
            f"<b>Tren 001</b><br>"
            f"Estación: {station_name}<br>"
            f"Riesgo: <b>{risk_level}</b><br>"
            f"Score: {risk_score:.3f}<br>"
            f"Registro: {record_idx + 1}/{total}<br>"
            f"Tiempo: {timestamp_val}"
            "<extra></extra>"
        ),
        showlegend=False,
        name="Tren 001",
    ))

    # --- Leyenda manual de colores ---
    for level, color in LEVEL_COLORS.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=11, color=color, line=dict(color="#FFFFFF", width=1.5)),
            name=f"{LEVEL_LABELS[level]}",
            showlegend=True,
        ))

    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            range=[-0.8, NUM_STATIONS - 0.2],
            fixedrange=True,
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            range=[-0.55, 0.6],
            fixedrange=True,
            zeroline=False,
        ),
        plot_bgcolor="rgba(248, 250, 252, 1)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        height=220,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.18,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
    )

    return fig


def _build_risk_timeline(df: pd.DataFrame, record_idx: int) -> go.Figure:
    total = len(df)
    indices = list(range(total))
    scores = df["risk_score"].tolist()
    risk_levels = df["risk_level"].tolist()

    fig = go.Figure()

    # Bandas de fondo por nivel
    fig.add_hrect(y0=0, y1=RISK_THRESHOLD_MEDIO, fillcolor="rgba(34,197,94,0.07)", line_width=0)
    fig.add_hrect(y0=RISK_THRESHOLD_MEDIO, y1=RISK_THRESHOLD_ALTO, fillcolor="rgba(249,115,22,0.07)", line_width=0)
    fig.add_hrect(y0=RISK_THRESHOLD_ALTO, y1=1.0, fillcolor="rgba(239,68,68,0.07)", line_width=0)

    # Línea de riesgo coloreada por nivel
    for level, color in LEVEL_COLORS.items():
        mask = [l == level for l in risk_levels]
        x_seg = [i for i, m in zip(indices, mask) if m]
        y_seg = [scores[i] for i in x_seg]
        if x_seg:
            fig.add_trace(go.Scatter(
                x=x_seg,
                y=y_seg,
                mode="markers",
                marker=dict(size=3, color=color),
                name=f"Riesgo {level}",
                showlegend=False,
                hoverinfo="skip",
            ))

    # Línea continua sobre todas
    fig.add_trace(go.Scatter(
        x=indices,
        y=scores,
        mode="lines",
        line=dict(color="#234B8D", width=2),
        fill="tozeroy",
        fillcolor="rgba(35,75,141,0.07)",
        name="Risk Score",
        hovertemplate="Registro %{x}<br>Score: %{y:.3f}<extra></extra>",
        showlegend=False,
    ))

    # Marcador de posición actual
    current_score = scores[record_idx] if record_idx < total else 0.0
    fig.add_vline(
        x=record_idx,
        line_color="#F97316",
        line_width=2,
        line_dash="dot",
    )
    fig.add_trace(go.Scatter(
        x=[record_idx],
        y=[current_score],
        mode="markers",
        marker=dict(size=12, color="#F97316", line=dict(color="#FFFFFF", width=2)),
        name="Posición actual",
        hovertemplate=f"Score actual: {current_score:.3f}<extra></extra>",
        showlegend=False,
    ))

    # Líneas de umbral
    fig.add_hline(
        y=RISK_THRESHOLD_MEDIO,
        line_dash="dash",
        line_color="rgba(249,115,22,0.6)",
        annotation_text="MEDIO",
        annotation_font=dict(size=10, color="rgba(249,115,22,0.9)"),
    )
    fig.add_hline(
        y=RISK_THRESHOLD_ALTO,
        line_dash="dash",
        line_color="rgba(239,68,68,0.6)",
        annotation_text="ALTO",
        annotation_font=dict(size=10, color="rgba(239,68,68,0.9)"),
    )

    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            title="Registro (nº)",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            title="Risk Score",
            range=[0, 1.02],
            tickfont=dict(size=10),
        ),
        plot_bgcolor="rgba(248,250,252,1)",
        paper_bgcolor="rgba(255,255,255,0)",
        height=200,
        margin=dict(l=60, r=20, t=10, b=40),
    )

    return fig


# ---------------------------------------------------------------------------
# Estado vacío (sin datos cargados)
# ---------------------------------------------------------------------------

def _render_empty_metro():
    fig = go.Figure()
    station_x = list(range(NUM_STATIONS))

    fig.add_trace(go.Scatter(
        x=station_x,
        y=[0] * NUM_STATIONS,
        mode="lines+markers",
        line=dict(color="#D1D5DB", width=5),
        marker=dict(size=13, color="#9CA3AF", line=dict(color="#FFFFFF", width=2)),
        hoverinfo="none",
        showlegend=False,
    ))

    for i, name in enumerate(STATION_NAMES):
        y_off = 0.22 if i % 2 == 0 else -0.22
        fig.add_annotation(
            x=i, y=y_off,
            text=name,
            showarrow=False,
            font=dict(size=9, color="#9CA3AF"),
            xanchor="center",
        )

    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, range=[-0.8, 22.8], fixedrange=True, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, range=[-0.55, 0.6], fixedrange=True, zeroline=False),
        plot_bgcolor="rgba(248,250,252,1)",
        paper_bgcolor="rgba(255,255,255,0)",
        height=220,
        margin=dict(l=10, r=10, t=40, b=10),
        title=dict(
            text="Carga un CSV para activar la visualización del tren",
            font=dict(size=13, color="#9CA3AF"),
            x=0.5,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Fragmento de animación
# ---------------------------------------------------------------------------

@st.fragment
def _animation_fragment(df: pd.DataFrame, total: int) -> None:
    if "tm_slider" not in st.session_state:
        st.session_state["tm_slider"] = 0
    if "tm_playing" not in st.session_state:
        st.session_state["tm_playing"] = False

    playing: bool = bool(st.session_state["tm_playing"])

    # --- Auto-avance: escribir en tm_slider ANTES de que se instancie el widget ---
    # Streamlit prohíbe modificar session_state de un widget después de crearlo.
    if playing:
        speed_map = {"1×": 1, "2×": 2, "5×": 5, "10×": 10, "20×": 20}
        speed_str_pre = st.session_state.get("tm_speed", "2×")
        step = speed_map.get(speed_str_pre, 2)
        current_idx = int(st.session_state["tm_slider"])
        next_idx = current_idx + step
        if next_idx >= total:
            next_idx = total - 1
            st.session_state["tm_playing"] = False
            playing = False
        st.session_state["tm_slider"] = next_idx

    # --- Controles de reproducción ---
    ctrl_col, speed_col, _ = st.columns([2, 1, 5])

    with ctrl_col:
        btn_cols = st.columns(3)
        with btn_cols[0]:
            if st.button("▶" if not playing else "⏸", key="tm_play", use_container_width=True,
                         help="Reproducir / Pausar"):
                st.session_state["tm_playing"] = not playing
                st.rerun(scope="fragment")
        with btn_cols[1]:
            if st.button("⏹", key="tm_stop", use_container_width=True, help="Detener y volver al inicio"):
                st.session_state["tm_playing"] = False
                st.session_state["tm_slider"] = 0
                st.rerun(scope="fragment")
        with btn_cols[2]:
            if st.button("⏭", key="tm_end", use_container_width=True, help="Ir al último registro"):
                st.session_state["tm_playing"] = False
                st.session_state["tm_slider"] = total - 1
                st.rerun(scope="fragment")

    with speed_col:
        speed_str = st.selectbox(
            "Velocidad",
            options=["1×", "2×", "5×", "10×", "20×"],
            index=1,
            key="tm_speed",
            label_visibility="collapsed",
        )

    # --- Slider de navegación ---
    # Sin value=: Streamlit lee st.session_state["tm_slider"] directamente.
    st.slider(
        "Registro",
        min_value=0,
        max_value=total - 1,
        key="tm_slider",
        format="Registro %d",
    )
    idx: int = int(st.session_state["tm_slider"])

    # --- Diagrama del metro ---
    metro_fig = _build_metro_figure(df, idx)
    st.plotly_chart(metro_fig, use_container_width=True, key="tm_metro_fig")

    # --- Barra de estado del tren ---
    row = df.iloc[idx]
    risk_level = str(row.get("risk_level", "BAJO")).upper()
    if risk_level not in LEVEL_COLORS:
        risk_level = "BAJO"
    risk_score = float(row.get("risk_score", 0.0))
    timestamp_val = row.get("timestamp", "")
    train_color = LEVEL_COLORS[risk_level]
    position = _train_position(idx, total)
    station_name = STATION_NAMES[_current_station_idx(position)]

    st.markdown(
        f"""
        <div style="
            display:flex; align-items:center; gap:1rem;
            padding:0.65rem 1.1rem;
            background:rgba(255,255,255,0.85);
            border-radius:12px;
            border:1px solid rgba(0,0,0,0.08);
            margin:0.4rem 0 0.8rem 0;
            font-size:0.92rem;
        ">
            <div style="
                width:14px; height:14px; border-radius:50%;
                background:{train_color};
                box-shadow:0 0 10px {train_color}AA;
                flex-shrink:0;
            "></div>
            <span>
                <strong>Tren 001</strong>
                &nbsp;·&nbsp; {station_name}
                &nbsp;·&nbsp; Riesgo: <strong style="color:{train_color}">{risk_level}</strong>
                &nbsp;·&nbsp; Score: <strong>{risk_score:.3f}</strong>
                &nbsp;·&nbsp; Registro <strong>{idx + 1}</strong> / {total}
                &nbsp;·&nbsp; {timestamp_val}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Línea de tiempo de riesgo ---
    render_section_header("Evolución del Riesgo", "Score de riesgo a lo largo de todos los registros.")
    timeline_fig = _build_risk_timeline(df, idx)
    st.plotly_chart(timeline_fig, use_container_width=True, key="tm_timeline_fig")

    # --- Continuar animación: sólo sleep + rerun, sin tocar session_state ---
    if playing:
        time.sleep(0.25)
        st.rerun(scope="fragment")


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def render(df: pd.DataFrame) -> None:
    render_view_header(
        "Mapa de Tren en Tiempo Real",
        "Visualización del movimiento del tren sobre la Línea A del Metro con estado de riesgo.",
    )

    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,rgba(8,42,112,0.06),rgba(8,42,112,0.02));
            border:1px solid rgba(8,42,112,0.12);
            border-radius:12px;
            padding:0.75rem 1.1rem;
            margin-bottom:1rem;
            font-size:0.9rem;
            color:#374151;
        ">
            📂 <strong>Carga un CSV</strong> con las mediciones del sensor (mismo formato que el dataset original).
            El sistema calcula automáticamente el nivel de riesgo si el archivo no lo incluye.
            Cada registro equivale a <strong>10 segundos</strong>; el tren recorre las 23 estaciones
            a lo largo de todo el dataset.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Subir CSV de mediciones",
        type=["csv"],
        key="train_map_upload",
        help="Columnas esperadas: timestamp, TP2, TP3, H1, DV_pressure, Reservoirs, Oil_Temperature, Motor_Current, …",
    )

    # Si no se sube CSV, mostrar el estado vacío de la línea
    if uploaded is None:
        _render_empty_metro()
        st.caption(
            "Sin datos cargados. Sube un CSV para activar la animación del tren."
        )
        return

    # Cache por nombre + tamaño del archivo (evita reprocesar en cada render)
    cache_key = f"tm_df_{uploaded.name}_{uploaded.size}"
    if cache_key not in st.session_state or st.session_state.get("tm_cache_key") != cache_key:
        with st.spinner("Procesando CSV y calculando nivel de riesgo…"):
            processed = _process_uploaded_csv(uploaded)
        if processed.empty:
            st.error("No se pudo procesar el archivo. Verifica el formato.")
            return
        st.session_state[cache_key] = processed
        st.session_state["tm_cache_key"] = cache_key
        # Resetear slider y reproducción al cargar nuevo archivo
        st.session_state["tm_slider"] = 0
        st.session_state["tm_playing"] = False

    df_map: pd.DataFrame = st.session_state[cache_key]
    total = len(df_map)

    if total == 0:
        st.warning("El archivo está vacío.")
        return

    # --- Métricas de resumen ---
    risk_counts = df_map["risk_level"].value_counts()
    pct_alto = risk_counts.get("ALTO", 0) / total * 100
    pct_medio = risk_counts.get("MEDIO", 0) / total * 100

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total registros", f"{total:,}")
    with m2:
        st.metric("Normal (BAJO)", risk_counts.get("BAJO", 0))
    with m3:
        st.metric("Alerta media (MEDIO)", risk_counts.get("MEDIO", 0), f"{pct_medio:.1f}%")
    with m4:
        st.metric("Alerta alta (ALTO)", risk_counts.get("ALTO", 0), f"{pct_alto:.1f}%",
                  delta_color="inverse")
    with m5:
        avg_score = df_map["risk_score"].mean()
        st.metric("Score promedio", f"{avg_score:.3f}")

    st.markdown("---")
    render_section_header(
        "Línea A del Metro — 23 Estaciones",
        "Usa ▶ para animar el recorrido o arrastra el slider para navegar manualmente.",
    )

    _animation_fragment(df_map, total)
