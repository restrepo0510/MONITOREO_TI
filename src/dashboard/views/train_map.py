"""
Vista de Mapa de Tren en Tiempo Real - Línea A del Metro.

Permite subir un CSV con mediciones de sensores y visualizar el tren
moviéndose entre las 23 estaciones de la Línea A, con código de color
según el nivel de riesgo activo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.dashboard.views.ui_kit import render_section_header, render_view_header
from src.analysis import autoencoder_predictor

# ---------------------------------------------------------------------------
# Configuración de la línea
# ---------------------------------------------------------------------------

NUM_STATIONS = 23

STATION_NAMES: list[str] = [f"Est. {i + 1}" for i in range(NUM_STATIONS)]

LEVEL_COLORS = {
    "BAJO": "#22C55E",
    "MEDIO": "#F97316",
    "ALTO": "#EF4444",
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
    df["risk_score"] = (avg_z / 3.0).clip(0.0, 1.0)
    df["risk_level"] = df["risk_score"].apply(_risk_level)
    return df


_RAW_COLUMNS = [
    "row_id", "timestamp",
    "TP2", "TP3", "H1", "DV_pressure", "Reservoirs", "Oil_Temperature", "Motor_Current",
    "COMP", "DV_electric", "TOWERS", "MPG", "LPS", "Pressure_switch", "Oil_Level", "Caudal_impulses",
]


def _process_uploaded_csv(uploaded_file) -> tuple[pd.DataFrame, str]:
    """Procesa el CSV y ejecuta el modelo. Devuelve (df, model_status)."""
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    except Exception:
        try:
            df = pd.read_csv(uploaded_file, encoding="latin-1")
        except Exception as e:
            st.error(f"Error leyendo el CSV: {e}")
            return pd.DataFrame(), "error"

    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    df.rename(columns=RENAME_MAP, inplace=True)

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
        if df.shape[1] == len(_RAW_COLUMNS):
            df.columns = _RAW_COLUMNS
        elif df.shape[1] == len(_RAW_COLUMNS) - 1:
            df.columns = _RAW_COLUMNS[1:]
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

    # Verificar disponibilidad de TensorFlow
    try:
        import importlib
        importlib.import_module("tensorflow")
        tf_available = True
    except (ImportError, ModuleNotFoundError):
        tf_available = False

    model_status = "unavailable"
    model_error_detail = ""
    if tf_available:
        # Llamar _load_artifacts() directamente para capturar el error real.
        # predict() captura TODAS las excepciones internamente y devuelve NaN
        # sin propagarlas, lo que impide diagnosticar el problema real.
        try:
            autoencoder_predictor._load_artifacts()
            df_with_model = autoencoder_predictor.predict(df)
            if df_with_model["model_score"].notna().any():
                df = df_with_model
                model_status = "ok"
            else:
                model_status = "no_predictions"
        except Exception as exc:
            model_status = "error"
            model_error_detail = str(exc)

    return df, model_status, model_error_detail


# ---------------------------------------------------------------------------
# Cálculo de posición
# ---------------------------------------------------------------------------

def _train_position(record_idx: int, total: int) -> float:
    if total <= 1:
        return 0.0
    return (record_idx / (total - 1)) * (NUM_STATIONS - 1)


def _current_station_idx(position: float) -> int:
    return min(int(position), NUM_STATIONS - 1)


# ---------------------------------------------------------------------------
# Figura animada combinada (metro + timeline) con frames nativos de Plotly
#
# Todos los frames se pre-construyen UNA VEZ y se cachean en session_state.
# La animación la gestiona el motor JavaScript de Plotly internamente:
# CERO st.rerun() durante la reproducción → CERO flickering.
# ---------------------------------------------------------------------------

def _build_animated_combined_figure(df: pd.DataFrame) -> go.Figure:
    """
    Figura combinada (metro superior + timeline inferior) con todos los frames
    de animación pre-construidos.

    Plotly gestiona la reproducción en JavaScript con `redraw=False`:
    solo se actualizan las trazas dinámicas (posición del tren + marcador de
    posición en el timeline) sin reconstruir el DOM → cero flickering.
    """
    total = len(df)
    has_model = "model_score" in df.columns and df["model_score"].notna().any()

    # ── Estructura de subplots ──────────────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.38, 0.62],
        vertical_spacing=0.10,
    )

    station_x = list(range(NUM_STATIONS))
    station_y_zero = [0] * NUM_STATIONS

    # ── ROW 1: Mapa de metro ────────────────────────────────────────────────

    # [0] Vía
    fig.add_trace(go.Scatter(
        x=station_x, y=station_y_zero, mode="lines",
        line=dict(color="#6B7280", width=5), hoverinfo="none", showlegend=False,
    ), row=1, col=1)

    # [1] Estaciones
    fig.add_trace(go.Scatter(
        x=station_x, y=station_y_zero, mode="markers",
        marker=dict(size=13, color="#374151", line=dict(color="#FFFFFF", width=2)),
        hovertemplate=[f"<b>{n}</b><extra></extra>" for n in STATION_NAMES],
        showlegend=False, name="Estaciones",
    ), row=1, col=1)

    # [2] Marcador del tren – DINÁMICO (se actualiza en cada frame)
    row0 = df.iloc[0]
    rl0 = str(row0.get("risk_level", "BAJO")).upper()
    if rl0 not in LEVEL_COLORS:
        rl0 = "BAJO"
    tc0 = LEVEL_COLORS[rl0]
    pos0 = _train_position(0, total)
    fig.add_trace(go.Scatter(
        x=[pos0], y=[0], mode="markers+text",
        marker=dict(size=26, color=tc0, line=dict(color="#FFFFFF", width=3), symbol="circle"),
        text=["🚇"], textposition="top center", textfont=dict(size=14),
        showlegend=False, name="Tren 001",
    ), row=1, col=1)
    TRAIN_IDX = 2

    # [3, 4, 5] Entradas de leyenda por nivel de riesgo
    for level, color in LEVEL_COLORS.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=11, color=color, line=dict(color="#FFFFFF", width=1.5)),
            name=LEVEL_LABELS[level], showlegend=True,
        ), row=1, col=1)

    # Anotaciones de nombres de estaciones (estáticas)
    for i, name in enumerate(STATION_NAMES):
        y_off = 0.22 if i % 2 == 0 else -0.22
        fig.add_annotation(
            x=i, y=y_off, text=name, showarrow=False,
            font=dict(size=9, color="#374151"),
            xanchor="center", yanchor="middle",
            xref="x", yref="y",
        )

    # ── ROW 2: Timeline de riesgo ───────────────────────────────────────────
    indices = list(range(total))
    scores = df["risk_score"].tolist()
    risk_levels = df["risk_level"].tolist()

    # Bandas de fondo (shapes, no trazas → siempre estáticas)
    fig.add_hrect(y0=0, y1=RISK_THRESHOLD_MEDIO,
                  fillcolor="rgba(34,197,94,0.07)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=RISK_THRESHOLD_MEDIO, y1=RISK_THRESHOLD_ALTO,
                  fillcolor="rgba(249,115,22,0.07)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=RISK_THRESHOLD_ALTO, y1=1.0,
                  fillcolor="rgba(239,68,68,0.07)", line_width=0, row=2, col=1)

    # Marcadores de color por nivel
    for level, color in LEVEL_COLORS.items():
        mask = [lvl == level for lvl in risk_levels]
        x_seg = [i for i, m in zip(indices, mask) if m]
        y_seg = [scores[i] for i in x_seg]
        fig.add_trace(go.Scatter(
            x=x_seg, y=y_seg, mode="markers",
            marker=dict(size=3, color=color),
            showlegend=False, hoverinfo="skip",
        ), row=2, col=1)

    # Línea del score estadístico
    fig.add_trace(go.Scatter(
        x=indices, y=scores, mode="lines",
        line=dict(color="#234B8D", width=2),
        fill="tozeroy", fillcolor="rgba(35,75,141,0.07)",
        name="Score Estadístico", showlegend=True,
        hovertemplate="Reg. %{x}  ·  Score: %{y:.3f}<extra></extra>",
    ), row=2, col=1)

    # Línea del score del modelo (si disponible)
    model_scores: list = []
    if has_model:
        model_scores = df["model_score"].fillna(0).tolist()
        fig.add_trace(go.Scatter(
            x=indices, y=model_scores, mode="lines",
            line=dict(color="#8B5CF6", width=2, dash="dash"),
            name="Score Modelo (Autoencoder)", showlegend=True,
            hovertemplate="Reg. %{x}  ·  Modelo: %{y:.3f}<extra></extra>",
        ), row=2, col=1)

    # Líneas de umbral
    fig.add_hline(y=RISK_THRESHOLD_MEDIO, line_dash="dash",
                  line_color="rgba(249,115,22,0.6)",
                  annotation_text="MEDIO",
                  annotation_font=dict(size=10, color="rgba(249,115,22,0.9)"),
                  row=2, col=1)
    fig.add_hline(y=RISK_THRESHOLD_ALTO, line_dash="dash",
                  line_color="rgba(239,68,68,0.6)",
                  annotation_text="ALTO",
                  annotation_font=dict(size=10, color="rgba(239,68,68,0.9)"),
                  row=2, col=1)

    # ── Trazas dinámicas del timeline (se actualizan frame a frame) ─────────
    n_static = len(fig.data)  # índice donde empiezan las trazas dinámicas

    cs0 = scores[0]

    # [n_static] Línea vertical de posición (como Scatter, no add_vline,
    #            para poder actualizarla dentro de go.Frame)
    fig.add_trace(go.Scatter(
        x=[0, 0], y=[0, 1.02], mode="lines",
        line=dict(color="#F97316", width=2, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ), row=2, col=1)
    VLINE_IDX = n_static

    # [n_static+1] Punto de posición estadístico
    fig.add_trace(go.Scatter(
        x=[0], y=[cs0], mode="markers",
        marker=dict(size=12, color="#F97316", line=dict(color="#FFFFFF", width=2)),
        showlegend=False,
        hovertemplate=f"Score estadístico: {cs0:.3f}<extra></extra>",
    ), row=2, col=1)
    STAT_DOT_IDX = n_static + 1

    dynamic_traces = [TRAIN_IDX, VLINE_IDX, STAT_DOT_IDX]

    # [n_static+2] Punto de posición del modelo (si disponible)
    MODEL_DOT_IDX: int | None = None
    if has_model:
        ms0 = float(df["model_score"].iloc[0]) if not pd.isna(df["model_score"].iloc[0]) else 0.0
        fig.add_trace(go.Scatter(
            x=[0], y=[ms0], mode="markers",
            marker=dict(size=10, color="#8B5CF6", symbol="diamond",
                        line=dict(color="#FFFFFF", width=2)),
            showlegend=False,
            hovertemplate=f"Score modelo: {ms0:.3f}<extra></extra>",
        ), row=2, col=1)
        MODEL_DOT_IDX = n_static + 2
        dynamic_traces.append(MODEL_DOT_IDX)

    # ── Construcción de frames ──────────────────────────────────────────────
    # redraw=False → Plotly actualiza SOLO las trazas en dynamic_traces
    # sin reconstruir el SVG completo → animación completamente suave.
    frames: list[go.Frame] = []
    for i in range(total):
        row_i = df.iloc[i]
        rl = str(row_i.get("risk_level", "BAJO")).upper()
        if rl not in LEVEL_COLORS:
            rl = "BAJO"
        tc = LEVEL_COLORS[rl]
        pos = _train_position(i, total)
        rs = float(row_i.get("risk_score", 0.0))
        ts = row_i.get("timestamp", "")
        sn = STATION_NAMES[_current_station_idx(pos)]
        cs = scores[i]

        frame_data: list = [
            go.Scatter(  # tren
                x=[pos], y=[0], mode="markers+text",
                marker=dict(size=26, color=tc, line=dict(color="#FFFFFF", width=3),
                            symbol="circle"),
                text=["🚇"], textposition="top center", textfont=dict(size=14),
                hovertemplate=(
                    f"<b>Tren 001</b><br>Estación: {sn}<br>"
                    f"Riesgo: <b>{rl}</b><br>Score: {rs:.3f}<br>"
                    f"Reg. {i + 1}/{total} · {ts}<extra></extra>"
                ),
            ),
            go.Scatter(  # vline
                x=[i, i], y=[0, 1.02], mode="lines",
                line=dict(color="#F97316", width=2, dash="dot"),
                hoverinfo="skip",
            ),
            go.Scatter(  # punto estadístico
                x=[i], y=[cs], mode="markers",
                marker=dict(size=12, color="#F97316", line=dict(color="#FFFFFF", width=2)),
                hovertemplate=f"Score estadístico: {cs:.3f}<extra></extra>",
            ),
        ]

        if has_model:
            ms_val = df["model_score"].iloc[i]
            ms = float(ms_val) if not pd.isna(ms_val) else 0.0
            frame_data.append(go.Scatter(
                x=[i], y=[ms], mode="markers",
                marker=dict(size=10, color="#8B5CF6", symbol="diamond",
                            line=dict(color="#FFFFFF", width=2)),
                hovertemplate=f"Score modelo: {ms:.3f}<extra></extra>",
            ))

        frames.append(go.Frame(data=frame_data, traces=dynamic_traces, name=str(i)))

    fig.frames = frames

    # ── Layout ──────────────────────────────────────────────────────────────
    def _anim_args(duration_ms: int) -> list:
        return [None, {
            "frame": {"duration": duration_ms, "redraw": False},
            "fromcurrent": True,
            "mode": "immediate",
            "transition": {"duration": 0},
        }]

    pause_args = [[None], {
        "frame": {"duration": 0, "redraw": False},
        "mode": "immediate",
        "transition": {"duration": 0},
    }]

    fig.update_layout(
        height=500,
        plot_bgcolor="rgba(248,250,252,1)",
        paper_bgcolor="rgba(255,255,255,0)",
        margin=dict(l=10, r=20, t=20, b=130),
        legend=dict(
            orientation="h", x=0.5, xanchor="center", y=1.02,
            bgcolor="rgba(0,0,0,0)", font=dict(size=10),
        ),
        # Ejes del metro (row 1)
        xaxis=dict(showgrid=False, showticklabels=False,
                   range=[-0.8, NUM_STATIONS - 0.2], fixedrange=True, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False,
                   range=[-0.55, 0.6], fixedrange=True, zeroline=False),
        # Ejes del timeline (row 2)
        xaxis2=dict(showgrid=False, title="Registro (nº)", tickfont=dict(size=10)),
        yaxis2=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)",
                    title="Risk Score", range=[0, 1.02], tickfont=dict(size=10)),
        updatemenus=[
            # ▶ Play / ⏸ Pause
            dict(
                type="buttons",
                buttons=[
                    dict(label="▶ Play", method="animate", args=_anim_args(250)),
                    dict(label="⏸ Pausa", method="animate", args=pause_args),
                ],
                direction="left", pad=dict(r=6, t=5), showactive=True,
                x=0.0, y=-0.21, xanchor="left", yanchor="top",
                bgcolor="#082A70", bordercolor="#0A35A0",
                font=dict(color="white", size=13),
            ),
            # Selector de velocidad
            dict(
                type="buttons",
                buttons=[
                    dict(label="1×",  method="animate", args=_anim_args(1000)),
                    dict(label="2×",  method="animate", args=_anim_args(500)),
                    dict(label="5×",  method="animate", args=_anim_args(200)),
                    dict(label="10×", method="animate", args=_anim_args(100)),
                    dict(label="20×", method="animate", args=_anim_args(50)),
                ],
                direction="left", pad=dict(r=6, t=5), showactive=True, active=1,
                x=0.40, y=-0.21, xanchor="left", yanchor="top",
                bgcolor="#374151", bordercolor="#4B5563",
                font=dict(color="white", size=11),
            ),
        ],
        sliders=[dict(
            active=0,
            currentvalue=dict(
                prefix="Registro: ", visible=True, xanchor="right",
                font=dict(size=10, color="#374151"),
            ),
            pad=dict(b=8, t=5),
            len=1.0, x=0.0, y=-0.12,
            steps=[
                dict(
                    method="animate",
                    args=[[str(i)], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    }],
                    label=str(i) if i % max(1, total // 8) == 0 else "",
                )
                for i in range(total)
            ],
        )],
    )

    return fig


# ---------------------------------------------------------------------------
# Estado vacío (sin datos cargados)
# ---------------------------------------------------------------------------

def _render_empty_metro():
    fig = go.Figure()
    station_x = list(range(NUM_STATIONS))

    fig.add_trace(go.Scatter(
        x=station_x, y=[0] * NUM_STATIONS,
        mode="lines+markers",
        line=dict(color="#D1D5DB", width=5),
        marker=dict(size=13, color="#9CA3AF", line=dict(color="#FFFFFF", width=2)),
        hoverinfo="none",
        showlegend=False,
    ))

    for i, name in enumerate(STATION_NAMES):
        y_off = 0.22 if i % 2 == 0 else -0.22
        fig.add_annotation(
            x=i, y=y_off, text=name,
            showarrow=False,
            font=dict(size=9, color="#9CA3AF"),
            xanchor="center",
        )

    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, range=[-0.8, 22.8],
                   fixedrange=True, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, range=[-0.55, 0.6],
                   fixedrange=True, zeroline=False),
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

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Fragmento de animación
# ---------------------------------------------------------------------------

@st.fragment
def _animation_fragment(df: pd.DataFrame, total: int) -> None:
    if "tm_slider" not in st.session_state:
        st.session_state["tm_slider"] = 0

    # ── Obtener/construir la figura animada combinada (una sola vez por dataset) ──
    cache_key = st.session_state.get("tm_cache_key", "")
    anim_key = f"tm_combined_anim_{cache_key}_{len(df)}"

    if anim_key not in st.session_state:
        with st.spinner("Preparando animación (se hace una sola vez por dataset)…"):
            st.session_state[anim_key] = _build_animated_combined_figure(df)

    combined_fig = st.session_state[anim_key]

    # ── Renderizar la figura animada ─────────────────────────────────────────
    # Plotly gestiona la reproducción completamente en JavaScript:
    # ▶ Play / ⏸ Pausa / velocidad están integrados en la figura.
    # No hay ningún st.rerun() durante la animación → cero flickering.
    st.plotly_chart(combined_fig, use_container_width=True,
                    config={"displayModeBar": False})

    # ── Slider de Streamlit para detalles del registro ───────────────────────
    st.caption(
        "Arrastra el slider del gráfico para animar · "
        "Arrastra este slider para ver los detalles del registro"
    )
    st.slider("Registro", min_value=0, max_value=total - 1,
              key="tm_slider", format="Registro %d")
    idx: int = int(st.session_state["tm_slider"])

    # ── Barra de estado + panel de comparación (actualizan con el slider) ────
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
            display:flex;align-items:center;gap:1rem;
            padding:0.65rem 1.1rem;
            background:rgba(255,255,255,0.85);
            border-radius:12px;
            border:1px solid rgba(0,0,0,0.08);
            margin:0.4rem 0 0.5rem 0;
            font-size:0.92rem;
        ">
            <div style="
                width:14px;height:14px;border-radius:50%;
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

    if "model_score" in df.columns:
        raw_model = row["model_score"]
        if not pd.isna(raw_model):
            model_score_val = float(raw_model)
            model_anomaly_val = bool(row.get("model_anomaly", False))
            model_level = _risk_level(model_score_val)
            model_color = LEVEL_COLORS[model_level]
            agree = model_level == risk_level
            agree_color = "#22C55E" if agree else "#EF4444"
            agree_icon = "✓" if agree else "✗"
            agree_text = "Acuerdan" if agree else "Discrepan"
            anomaly_badge = "&nbsp; ⚠ Anomalía" if model_anomaly_val else ""
            st.markdown(
                f"""
                <div style="display:grid;grid-template-columns:1fr auto 1fr;
                            gap:0.75rem;margin:0.4rem 0 0.9rem 0;">
                    <div style="background:rgba(255,255,255,0.9);
                                border:1px solid rgba(0,0,0,0.08);
                                border-left:4px solid {train_color};
                                border-radius:10px;padding:0.65rem 1rem;">
                        <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;
                                    letter-spacing:0.06em;margin-bottom:0.25rem;">
                            Score Estadístico (Z-Score)
                        </div>
                        <div style="font-size:1.55rem;font-weight:700;color:{train_color};
                                    line-height:1.1;">{risk_score:.3f}</div>
                        <div style="font-size:0.82rem;color:{train_color};font-weight:600;
                                    margin-top:0.15rem;">{risk_level}</div>
                    </div>
                    <div style="display:flex;flex-direction:column;align-items:center;
                                justify-content:center;gap:0.3rem;padding:0.4rem;">
                        <span style="font-size:1.3rem;font-weight:800;color:{agree_color};">
                            {agree_icon}
                        </span>
                        <span style="font-size:0.7rem;font-weight:700;color:{agree_color};
                                     background:{agree_color}22;padding:0.2rem 0.5rem;
                                     border-radius:6px;white-space:nowrap;">{agree_text}</span>
                    </div>
                    <div style="background:rgba(255,255,255,0.9);
                                border:1px solid rgba(0,0,0,0.08);
                                border-left:4px solid {model_color};
                                border-radius:10px;padding:0.65rem 1rem;">
                        <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;
                                    letter-spacing:0.06em;margin-bottom:0.25rem;">
                            Score Modelo (Autoencoder)
                        </div>
                        <div style="font-size:1.55rem;font-weight:700;color:{model_color};
                                    line-height:1.1;">{model_score_val:.3f}</div>
                        <div style="font-size:0.82rem;color:{model_color};font-weight:600;
                                    margin-top:0.15rem;">{model_level}{anomaly_badge}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Análisis de anticipación del modelo
# ---------------------------------------------------------------------------

def _compute_lead_time_analysis(df: pd.DataFrame, umbral: float = 0.4) -> dict:
    """
    Mide cuánto se anticipa model_score a risk_score en cada bloque continuo
    de operación. Devuelve estadísticas de lead time en minutos.
    """
    work = df[["timestamp", "risk_score", "model_score"]].dropna().copy()
    work = work.sort_values("timestamp").reset_index(drop=True)

    if len(work) < 10:
        return {"eventos": 0}

    # Reconstruir bloques con NaN (periodos apagados)
    full = df[["timestamp", "risk_score", "model_score"]].copy().sort_values("timestamp").reset_index(drop=True)
    full["active"] = full["risk_score"].notna()
    full["block"] = (full["active"] != full["active"].shift()).cumsum()

    lead_times = []
    for _, group in full[full["active"]].groupby("block"):
        seg = group.dropna()
        if len(seg) < 5:
            continue
        model_cross = seg[seg["model_score"] >= umbral]
        stat_cross  = seg[seg["risk_score"]  >= umbral]
        if model_cross.empty or stat_cross.empty:
            continue
        t_model = model_cross["timestamp"].iloc[0]
        t_stat  = stat_cross["timestamp"].iloc[0]
        lead_min = (t_stat - t_model).total_seconds() / 60
        model_val_at_cross = float(model_cross["model_score"].iloc[0])
        lead_times.append({
            "lead_min": lead_min,
            "model_saturado": model_val_at_cross >= 0.999,
        })

    if not lead_times:
        return {"eventos": 0}

    total_eventos = len(lead_times)
    anticipados   = [e for e in lead_times if e["lead_min"] > 0 and not e["model_saturado"]]
    simultaneos   = [e for e in lead_times if e["lead_min"] == 0 or e["model_saturado"]]
    retrasados    = [e for e in lead_times if e["lead_min"] < 0]

    avg_lead = float(np.mean([e["lead_min"] for e in anticipados])) if anticipados else 0.0
    med_lead = float(np.median([e["lead_min"] for e in anticipados])) if anticipados else 0.0

    return {
        "eventos": total_eventos,
        "anticipados": len(anticipados),
        "simultaneos": len(simultaneos),
        "retrasados": len(retrasados),
        "avg_lead_min": avg_lead,
        "med_lead_min": med_lead,
        "pct_anticipacion": len(anticipados) / total_eventos * 100 if total_eventos else 0.0,
    }


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def render(df: pd.DataFrame) -> None:
    render_view_header(
        "Mapa de Tren en Tiempo Real",
        "Visualización del movimiento del tren sobre la Línea A del Metro con estado de riesgo.",
    )

    # CSS: restaurar visibilidad de etiquetas de métricas (el CSS reset global
    # del theme_manager aplica margin/padding:0 a * y puede colapsar las labels
    # de st.metric en modo oscuro).
    st.markdown(
        """
        <style>
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] > div,
        [data-testid="stMetricLabel"] > div > p {
            color: #000000 !important;
            font-size: 0.85rem !important;
            font-weight: 700 !important;
            line-height: 1.4 !important;
            margin-bottom: 0.3rem !important;
            visibility: visible !important;
            display: block !important;
        }
        [data-testid="stMetricValue"] > div {
            color: #000000 !important;
            font-size: 1.9rem !important;
            font-weight: 700 !important;
            line-height: 1.2 !important;
        }
        [data-testid="stMetricDelta"] > div {
            font-size: 0.78rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
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
            color:#000000;
            font-weight:400;
        ">
            📂 Carga un CSV con las mediciones del sensor (mismo formato que el dataset original).
            El sistema calcula el nivel de riesgo estadístico y ejecuta el modelo predictivo (Autoencoder).
            Cada registro equivale a 10 segundos; el tren recorre las 23 estaciones
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

    if uploaded is None:
        _render_empty_metro()
        st.caption("Sin datos cargados. Sube un CSV para activar la animación del tren.")
        return

    # Cache por nombre + tamaño del archivo
    cache_key = f"tm_df_{uploaded.name}_{uploaded.size}"
    if cache_key not in st.session_state or st.session_state.get("tm_cache_key") != cache_key:
        with st.spinner("Procesando CSV, calculando riesgo y ejecutando predicciones del modelo…"):
            processed, model_status, model_error_detail = _process_uploaded_csv(uploaded)
        if processed.empty:
            st.error("No se pudo procesar el archivo. Verifica el formato.")
            return
        st.session_state[cache_key] = processed
        st.session_state["tm_cache_key"] = cache_key
        st.session_state["tm_model_status"] = model_status
        st.session_state["tm_model_error"] = model_error_detail
        # Invalidar figura animada cacheada al cargar nuevo archivo
        for k in list(st.session_state.keys()):
            if k.startswith("tm_combined_anim_"):
                del st.session_state[k]
        st.session_state["tm_slider"] = 0

    df_map: pd.DataFrame = st.session_state[cache_key]
    model_status: str = st.session_state.get("tm_model_status", "unavailable")
    model_error_detail: str = st.session_state.get("tm_model_error", "")

    if df_map.empty:
        st.warning("El archivo está vacío.")
        return

    # ── Limitar animación a los primeros 10 días si el archivo supera 10 MB ──
    LIMITE_MB = 10
    anim_truncated = False
    if uploaded.size > LIMITE_MB * 1_024 * 1_024 and "timestamp" in df_map.columns:
        fecha_inicio = pd.to_datetime(df_map["timestamp"].iloc[0])
        fecha_limite = fecha_inicio + pd.Timedelta(days=10)
        df_map_anim = df_map[pd.to_datetime(df_map["timestamp"]) <= fecha_limite].copy()
        anim_truncated = True
    else:
        df_map_anim = df_map

    total = len(df_map)

    if total == 0:
        st.warning("El archivo está vacío.")
        return

    if anim_truncated:
        st.info(
            f"Archivo > {LIMITE_MB} MB: las métricas usan el dataset completo "
            f"({total:,} registros), pero la animación muestra solo los primeros 10 días "
            f"({len(df_map_anim):,} registros)."
        )

    # ── Métricas estadísticas (dataset completo) ──
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
        st.metric("Score estadístico promedio", f"{avg_score:.3f}")

    # ── Estado y métricas del modelo predictivo ──
    has_model = (
        "model_score" in df_map.columns
        and df_map["model_score"].notna().any()
    )

    if has_model:
        model_anomaly_count = int(df_map["model_anomaly"].sum())
        model_avg_score = float(df_map["model_score"].mean())
        pct_model_anomaly = model_anomaly_count / total * 100

        # Tasa de acuerdo: ambos métodos coinciden en si es anomalía
        stat_alto = df_map["risk_level"] == "ALTO"
        agreement_rate = (stat_alto == df_map["model_anomaly"]).mean() * 100

        st.markdown(
            """
            <div style="
                display:flex;align-items:center;gap:0.5rem;
                margin:0.5rem 0 0.25rem 0;font-size:0.82rem;
            ">
                <span style="
                    background:#22C55E22;color:#15803D;
                    padding:0.2rem 0.6rem;border-radius:6px;
                    font-weight:700;border:1px solid #22C55E44;
                ">✓ Modelo Predictivo Activo</span>
                <span style="color:#6B7280;">
                    Autoencoder Dense — ROC-AUC: 0.886
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        a1, a2, a3 = st.columns(3)
        with a1:
            st.metric(
                "Anomalías detectadas (Modelo)",
                model_anomaly_count,
                f"{pct_model_anomaly:.1f}%",
                delta_color="inverse",
                help="Registros donde el error de reconstrucción supera el umbral entrenado",
            )
        with a2:
            st.metric(
                "Score promedio (Modelo)",
                f"{model_avg_score:.3f}",
                help="Error de reconstrucción normalizado a [0,1]",
            )
        with a3:
            st.metric(
                "Acuerdo estadístico / modelo",
                f"{agreement_rate:.1f}%",
                help="Porcentaje de registros donde ambos métodos coinciden en la clasificación ALTO vs no-ALTO",
            )
    else:
        # Construir mensaje de error: si tenemos el detalle real, mostrarlo
        error_display = (
            model_error_detail[:300] if model_error_detail
            else "Ocurrió un error al cargar los artefactos del modelo."
        )
        _status_labels = {
            "no_predictions": ("⚠ Modelo sin predicciones", "#F97316",
                               "El modelo corrió pero todas las predicciones son NaN. "
                               "Puede ser incompatibilidad de versión de Keras/TF."),
            "error":          ("✗ Error al cargar el modelo", "#EF4444", error_display),
            "unavailable":    ("✗ TensorFlow no instalado", "#EF4444",
                               "Instálalo con: pip install tensorflow"),
        }
        label, color, detail = _status_labels.get(
            model_status,
            ("⚠ Modelo no disponible", "#F97316", "")
        )
        st.markdown(
            f"""
            <div style="
                display:inline-flex;align-items:center;gap:0.5rem;
                background:{color}11;border:1px solid {color}44;
                padding:0.35rem 0.8rem;border-radius:8px;
                font-size:0.82rem;color:{color};font-weight:600;
                margin:0.5rem 0;
            ">
                {label}
                <span style="font-weight:400;color:#6B7280;font-size:0.78rem;">— {detail}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if has_model:
        st.markdown("---")
        render_section_header(
            "Anticipación del Modelo vs Score Estadístico",
            "Tiempo promedio con el que el autoencoder detecta anomalías antes que el score estadístico.",
        )
        lead = _compute_lead_time_analysis(df_map_anim)
        if lead["eventos"] == 0:
            st.info("No hay suficientes eventos con ambos scores para calcular anticipación.")
        else:
            la1, la2, la3, la4 = st.columns(4)
            with la1:
                st.metric(
                    "Eventos analizados",
                    lead["eventos"],
                    help="Bloques continuos de operación donde ambos scores cruzaron el umbral 0.4",
                )
            with la2:
                st.metric(
                    "Con anticipación real",
                    f"{lead['anticipados']} ({lead['pct_anticipacion']:.0f}%)",
                    help="Eventos donde model_score cruzó el umbral antes que risk_score, sin saturarse a 1.0",
                )
            with la3:
                st.metric(
                    "Lead time promedio",
                    f"{lead['avg_lead_min'] * 14:.0f} min" if lead["anticipados"] else "—",
                    help="Tiempo medio de anticipación del modelo sobre el score estadístico (solo eventos no saturados)",
                )
            with la4:
                st.metric(
                    "Lead time mediana",
                    f"{lead['med_lead_min'] * 14:.0f} min" if lead["anticipados"] else "—",
                    help="Mediana del tiempo de anticipación — menos sensible a valores extremos",
                )
            st.markdown(
                f"""
                <div style="
                    background:rgba(8,42,112,0.04);border:1px solid rgba(8,42,112,0.12);
                    border-radius:10px;padding:0.65rem 1rem;font-size:0.82rem;
                    color:#374151;margin-top:0.4rem;
                ">
                    <b>Cómo leer este resultado:</b> de los {lead['eventos']} eventos,
                    <b>{lead['simultaneos']}</b> fueron simultáneos (el modelo se saturó a 1.0 al mismo instante que el score estadístico),
                    <b>{lead['anticipados']}</b> mostraron anticipación gradual real,
                    y <b>{lead['retrasados']}</b> {'fue detectado' if lead['retrasados'] == 1 else 'fueron detectados'} antes por el score estadístico.
                    La anticipación real ocurre en episodios de <i>degradación gradual</i>, no en fallos instantáneos.
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    render_section_header(
        "Línea A del Metro — 23 Estaciones",
        "Usa ▶ para animar el recorrido o arrastra el slider para navegar manualmente.",
    )

    MAX_ANIM_ROWS = 300
    if len(df_map_anim) > MAX_ANIM_ROWS:
        step = len(df_map_anim) // MAX_ANIM_ROWS
        df_anim_sampled = df_map_anim.iloc[::step].head(MAX_ANIM_ROWS).reset_index(drop=True)
    else:
        df_anim_sampled = df_map_anim

    _animation_fragment(df_anim_sampled, len(df_anim_sampled))
