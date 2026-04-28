from pathlib import Path
import html

import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.financial_section import render_financial_section
from src.dashboard.components.golden_signals import render_golden_signals
from src.dashboard.components.operativity_panel import render_operativity_panel
from src.dashboard.components.postmortem_panel import render_postmortem_panel
from src.dashboard.components.sensor_chart import ensure_sensor_chart_styles, render_sensor_card
from src.dashboard.components.station_line import render_station_line
from src.dashboard.theme import PALETTE, RISK_THRESHOLDS
from src.dashboard.views.ui_kit import (
    inject_operational_ui,
    render_section_header,
)
from src.dashboard.utils.alert_engine import (
    build_prediction_advisory,
    evaluate_alerts,
    evaluate_latest_alert,
    resolve_alert_thresholds,
)

TRAIN_ID_CANDIDATES = ["train_id", "train", "id_train", "apu_id", "engine_id"]
SENSOR_REASON_KEYS = {
    "TP3_mean",
    "H1_mean",
    "DV_pressure_mean",
    "Motor_Current_mean",
    "MPG_last",
    "Oil_Temperature_mean",
    "TOWERS_last",
}


def _image_paths():
    assets_dir = Path(__file__).resolve().parents[1] / "assets" / "images"
    return {"logo": assets_dir / "logo.png", "train": assets_dir / "train.png"}


def _inject_css():
    st.markdown(
        """
        <style>
        .home-legacy-title {
            color: #234B8D;
            font-size: 2.0rem;
            font-weight: 800;
            line-height: 1.1;
            margin: 0;
        }
        .home-legacy-section {
            font-size: 1.3rem;
            font-weight: 700;
            color: #234B8D;
            margin-top: 1.2rem;
            margin-bottom: 0.6rem;
        }
        .home-legacy-risk-high {
            background: #D32F2F;
            color: #F4F4F9;
            border: 1px solid #B71C1C;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin: 0.25rem 0 0.5rem 0;
        }
        /* Compactar metricas en vista tren */
        div[data-testid="stMetric"] {
            border-radius: 10px !important;
            padding: 0.18rem 0.42rem !important;
        }
        div[data-testid="stMetricLabel"] p {
            font-size: 0.78rem !important;
            line-height: 1.1 !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.45rem !important;
            line-height: 1.05 !important;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 0.78rem !important;
            line-height: 1.1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _find_train_col(df):
    for c in TRAIN_ID_CANDIDATES:
        if c in df.columns:
            return c
    return None


def _selected_train_df(df):
    train_col = _find_train_col(df)
    if not train_col:
        return df.copy(), "001", None

    train_id = str(st.session_state.get("selected_train_id", "")).strip()
    candidates = df[train_col].astype(str).unique().tolist()
    if not train_id or train_id not in candidates:
        train_id = str(candidates[0]) if candidates else "001"
    st.session_state["selected_train_id"] = train_id
    filtered = df[df[train_col].astype(str) == train_id].copy()
    if filtered.empty:
        filtered = df.copy()
    return filtered, train_id, train_col


def _render_header(train_id: str):
    paths = _image_paths()
    c1, c2, c3, c4 = st.columns([0.9, 2.35, 2.25, 1.85], gap="small", vertical_alignment="center")

    with c1:
        if paths["logo"].exists():
            st.image(str(paths["logo"]), width=145)
        else:
            st.caption("Logo no encontrado")

    with c2:
        st.markdown(f'<div class="home-legacy-title">APU DEL TREN #{train_id} (Operativo)</div>', unsafe_allow_html=True)

    with c3:
        render_station_line(train_id=train_id, cycle_seconds=5)

    with c4:
        if paths["train"].exists():
            st.image(str(paths["train"]), width=335)
        else:
            st.caption("Imagen de tren no encontrada")


def _build_risk_chart(df):
    risk_df = df.tail(500).copy()
    score_col = "risk_score_operational" if "risk_score_operational" in risk_df.columns else "risk_score"
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=risk_df["timestamp"],
            y=risk_df[score_col],
            mode="lines",
            name="Risk Score",
            line=dict(color=PALETTE["steel_azure"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(184,219,217,0.30)",
            hovertemplate="%{x}<br>Score: %{y:.3f}<extra></extra>",
        )
    )

    high_events = risk_df[risk_df[score_col] >= RISK_THRESHOLDS["ALTO"]]
    if not high_events.empty:
        fig.add_trace(
            go.Scatter(
                x=high_events["timestamp"],
                y=high_events[score_col],
                mode="markers",
                name="Eventos ALTO",
                marker=dict(color=PALETTE["alert_red"], size=7, symbol="diamond"),
                hovertemplate="%{x}<br>Evento ALTO: %{y:.3f}<extra></extra>",
            )
        )

    fig.add_hline(
        y=RISK_THRESHOLDS["MEDIO"],
        line_dash="dash",
        line_color=PALETTE["yellow"],
        annotation_text=f"MEDIO ({RISK_THRESHOLDS['MEDIO']:.1f})",
        annotation_position="top left",
    )
    fig.add_hline(
        y=RISK_THRESHOLDS["ALTO"],
        line_dash="dash",
        line_color=PALETTE["alert_red"],
        annotation_text=f"ALTO ({RISK_THRESHOLDS['ALTO']:.1f})",
        annotation_position="top left",
    )
    fig.update_layout(
        height=320,
        paper_bgcolor=PALETTE["ghost_white"],
        plot_bgcolor="white",
        margin=dict(t=20, b=10, l=8, r=8),
        legend=dict(orientation="h", y=1.1, x=0),
    )
    fig.update_yaxes(range=[0, 1], showgrid=True, gridcolor="rgba(35,75,141,0.12)")
    fig.update_xaxes(showgrid=False)
    return fig


def _build_drivers_chart(alert_reasons):
    """Gráfico profesional de causas/drivers del riesgo con colores degradados."""
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
        # Paleta de colores degradada: Rojo → Naranja → Amarillo
        if len(labels) == 1:
            colors_list = ["#DC1F26"]  # Rojo puro
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

    # Calcular porcentajes
    max_value = max(values) if values else 1
    percentages = [int((v / max_value) * 100) for v in values]

    # Crear figura
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(
                color=colors_list,
                line=dict(
                    color=[c.replace("F", "A") for c in colors_list],
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
    
    fig.update_layout(
        height=340,
        margin=dict(t=30, b=30, l=180, r=100),
        paper_bgcolor="#FAFAFA",
        plot_bgcolor="white",
        font=dict(family="Arial", color="#0F1E3C", size=11),
        xaxis_title="Peso Relativo",
        xaxis_title_font=dict(size=12, family="Arial", color="#6B7280"),
        showlegend=False,
        hovermode="closest",
    )
    
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


def _render_risk_banner(risk_level, score):
    if risk_level == "ALTO":
        st.markdown(
            f"""
            <div class="home-legacy-risk-high">
                <div><b>RIESGO ALTO</b></div>
                <div>Score: {float(score):.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif risk_level == "MEDIO":
        st.warning(f"RIESGO MEDIO - Score: {float(score):.2f}")
    else:
        st.info(f"RIESGO BAJO - Score: {float(score):.2f}")


def _extract_triggered_sensors(alert_reasons: str) -> list[str]:
    sensors = []
    for chunk in str(alert_reasons).split("|"):
        part = chunk.strip()
        if ":" not in part:
            continue
        prefix = part.split(":", 1)[0].strip()
        if prefix in SENSOR_REASON_KEYS and prefix not in sensors:
            sensors.append(prefix)
    return sensors


def _render_sensor_popup_red(latest_alert: dict, score_operational: float) -> None:
    sensors = _extract_triggered_sensors(str(latest_alert.get("alert_reasons", "")))
    if not sensors:
        return

    level = str(latest_alert.get("alert_level", "MEDIO")).upper()
    triggers = int(latest_alert.get("alert_trigger_count", 0))
    ts = latest_alert.get("timestamp")
    time_text = str(ts)[:19] if ts is not None else "-"
    sensor_text = ", ".join([s.replace("_mean", "").replace("_last", "") for s in sensors[:3]])
    if len(sensors) > 3:
        sensor_text += f" +{len(sensors) - 3}"
    popup_id = f"sensor-popup-close-{abs(hash((level, time_text, sensor_text, triggers)))}"
    safe_sensor_text = html.escape(sensor_text)
    safe_time_text = html.escape(time_text)

    st.markdown(
        f"""
        <style>
        .sensor-popup-toggle {{
          display: none;
        }}
        .sensor-popup-overlay {{
          position: fixed;
          inset: 0;
          z-index: 99990;
          background: rgba(10, 20, 40, 0.42);
        }}
        .sensor-popup-card {{
          position: fixed;
          left: 50%;
          top: 50%;
          transform: translate(-50%, -50%);
          z-index: 99991;
          width: min(560px, 92vw);
          background: linear-gradient(180deg, #D32F2F 0%, #B71C1C 100%);
          color: #FFF5F5;
          border: 1px solid #F5B4B4;
          border-radius: 14px;
          box-shadow: 0 18px 40px rgba(120, 16, 22, 0.50);
          padding: 1rem 1.05rem 0.95rem 1.05rem;
        }}
        .sensor-popup-title {{
          font-weight: 900;
          font-size: 1.00rem;
          letter-spacing: 0.02em;
          margin-bottom: 0.35rem;
          padding-right: 1.5rem;
        }}
        .sensor-popup-copy {{
          font-size: 0.88rem;
          line-height: 1.35;
          opacity: 0.98;
        }}
        .sensor-popup-close {{
          position: absolute;
          top: 0.42rem;
          right: 0.62rem;
          width: 1.35rem;
          height: 1.35rem;
          border-radius: 999px;
          border: 1px solid rgba(255, 255, 255, 0.72);
          background: rgba(255, 255, 255, 0.14);
          color: #FFFFFF;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-weight: 900;
          font-size: 0.95rem;
          line-height: 1;
          cursor: pointer;
          user-select: none;
        }}
        .sensor-popup-toggle:checked ~ .sensor-popup-overlay,
        .sensor-popup-toggle:checked ~ .sensor-popup-card {{
          display: none;
        }}
        </style>
        <div class="sensor-popup-wrap">
          <input id="{popup_id}" type="checkbox" class="sensor-popup-toggle" />
          <div class="sensor-popup-overlay"></div>
          <div class="sensor-popup-card">
            <label class="sensor-popup-close" for="{popup_id}">×</label>
            <div class="sensor-popup-title">ALERTA SENSOR ACTIVA ({level})</div>
            <div class="sensor-popup-copy">
              Sensores disparados: {safe_sensor_text}<br>
              Score operativo: {score_operational:.3f} | Triggers: {triggers}<br>
              Hora del evento: {safe_time_text}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(df):
    _inject_css()
    inject_operational_ui()
    working_df = df.copy().sort_values("timestamp")
    train_df, train_id, train_col = _selected_train_df(working_df)
    _render_header(train_id)
    latest = train_df.iloc[-1]
    risk_level = str(latest["risk_level"]).upper()
    score = float(latest["risk_score"])
    thresholds, _ = resolve_alert_thresholds(train_df)
    alert_df, _meta = evaluate_alerts(train_df.tail(2400), thresholds=thresholds)
    latest_alert, _ = evaluate_latest_alert(train_df.tail(2400), thresholds=thresholds)
    prediction = build_prediction_advisory(alert_df.tail(2400), thresholds=thresholds)
    score_operational = float(latest_alert.get("risk_score_operational", score))
    score_delta = float(latest_alert.get("risk_score_delta", score_operational - score))
    risk_level_display = str(latest_alert.get("alert_level", risk_level)).upper()
    _render_sensor_popup_red(latest_alert, score_operational)
    trend_direction_display = prediction["trend_direction"].upper()
    trend_detail = f"Triggers {int(latest_alert['alert_trigger_count'])}"
    if trend_direction_display == "ESTABLE" and risk_level_display == "ALTO":
        trend_direction_display = "ALTO SOSTENIDO"
        trend_detail = f"Triggers {int(latest_alert['alert_trigger_count'])} | Score {score_operational:.3f}"
    elif trend_direction_display == "ESTABLE" and score_delta >= 0.03:
        trend_direction_display = "SUBIENDO"
        trend_detail = f"Ajuste sensores {score_delta:+.3f}"

    render_section_header("Estado Actual", "")
    _render_risk_banner(risk_level_display, score_operational)
    if score_delta >= 0.03:
        st.warning(
            f"AVISO OPERATIVO: el riesgo general subio de {score:.3f} a {score_operational:.3f} por severidad detectada en sensores/relaciones."
        )
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Score de Riesgo Actual", f"{score_operational:.3f}", f"Ajuste {score_delta:+.3f}")
    with m2:
        st.metric("Proyección a 2 horas", f"{float(prediction['projected_score']):.3f}", prediction["projected_level"])
    with m3:
        st.metric("Tendencia del Riesgo", trend_direction_display, trend_detail)

    render_section_header("Riesgo Operacional en el Tiempo", "")
    st.plotly_chart(_build_risk_chart(alert_df), use_container_width=True)

    st.markdown("---")
    render_section_header("Sensores Clave del Tren", "")
    ensure_sensor_chart_styles()

    row1 = st.columns(4)
    with row1[0]:
        render_sensor_card("TP3_mean", train_df)
    with row1[1]:
        render_sensor_card("H1_mean", train_df)
    with row1[2]:
        render_sensor_card("DV_pressure_mean", train_df)
    with row1[3]:
        render_sensor_card("Motor_Current_mean", train_df)

    row2 = st.columns(3)
    with row2[0]:
        render_sensor_card("MPG_last", train_df)
    with row2[1]:
        render_sensor_card("Oil_Temperature_mean", train_df)
    with row2[2]:
        render_sensor_card("TOWERS_last", train_df)

    st.markdown("---")
    render_section_header("Señales Doradas del Tren", "")
    render_golden_signals(train_df, thresholds)

    st.markdown("---")
    render_financial_section(alert_df, prediction)

    st.markdown("---")
    render_section_header("Plan de Acción Recomendado", "")
    render_operativity_panel(train_df)

    st.markdown("---")
    render_section_header("Historial de Eventos (Postmortem)", "Resumen de episodios relevantes para trazabilidad técnica.")
    render_postmortem_panel(alert_df, prediction)

    if train_col:
        st.markdown("---")
        back_col1, back_col2 = st.columns([1, 3])
        with back_col1:
            if st.button("Volver al Home General"):
                st.session_state["nav_view"] = "system_home"
                st.rerun()
