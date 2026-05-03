from pathlib import Path
import html
import base64

import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.icons import icon_chip
from src.dashboard.components.financial_section import render_financial_section
from src.dashboard.components.golden_signals import render_golden_signals
from src.dashboard.components.operativity_panel import render_operativity_panel
from src.dashboard.components.postmortem_panel import render_postmortem_panel
from src.dashboard.components.sensor_chart import ensure_sensor_chart_styles, render_sensor_card
from src.dashboard.components.styles import inject_global_styles
from src.dashboard.components.ui_kit import chart_card, kpi_card, section_title
from src.dashboard.theme import PALETTE, RISK_THRESHOLDS
from src.dashboard.views.ui_kit import (
    inject_operational_ui,
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
        
        .train-hero {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAF7 100%);
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 24px;
            box-shadow: 0 12px 28px rgba(16, 24, 40, 0.07);
            padding: 1.05rem 1.05rem 0.95rem 1.05rem;
            margin-bottom: 0.8rem;
        }
        .train-hero-title {
            color: #082A70;
            font-size: 2.6rem;
            line-height: 1.05;
            font-weight: 700;
            margin: 0;
            letter-spacing: 0.15px;
            white-space: nowrap;
        }
        .train-hero-status {
            color: #2ecc71;
            font-size: 2rem;
            line-height: 1.02;
            font-weight: 600;
            margin-top: 4px;
        }
        .train-hero-copy {
            color: #6b7280;
            font-size: 14px;
            margin-top: 6px;
        }
        .train-hero-desc {
            color: #6b7280;
            font-size: 14px;
            line-height: 1.4;
            margin-top: 6px;
        }
        .train-hero-heading {
            display: block;
        }
        .train-header-icon {
            width: 72px;
            height: 72px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #082A70;
            color: #FFFFFF;
        }
        .train-header-icon svg {
            width: 36px;
            height: 36px;
        }
        .train-route-shell {
            margin-top: 0;
            background: #F6F8FC;
            border: 1px solid rgba(8, 42, 112, 0.12);
            border-radius: 16px;
            padding: 14px 16px;
            width: min(100%, 460px);
            max-width: 100%;
        }
        .train-route-wrap {

            width: 100%;
            display: flex;
            justify-content: flex-end;
            align-items: flex-start;
            margin-top: 10px;
            padding-right: 28px;
        }
        .train-route-track {
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: nowrap;
            white-space: nowrap;
        }
        .train-route-stop {
            background: #EAF0FB;
            color: #4A5B7C;
            font-size: 12px;
            font-weight: 600;
            border-radius: 12px;
            padding: 7px 12px;
            line-height: 1.15;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0;
            position: relative;
            text-align: center;
            white-space: normal;
            max-width: 128px;
        }
        .train-route-stop.active {
            background: #082A70;
            color: #FFFFFF;
            padding: 8px 14px;
            max-width: 160px;
        }
        .train-route-stop.active::after {
            content: "";
            position: absolute;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #F6C50E;
            top: -5px;
            right: -5px;
        }
        .train-route-arrow {
            color: #6E84AB;
            font-weight: 700;
            font-size: 14px;
            line-height: 1;
        }
        .train-header-right {
            display: flex;
            justify-content: flex-end;
            align-items: flex-start;
            width: 100%;
            margin-top: -110px;
        }
        .train-header-image {
            width: 400px !important;
            max-width: none !important;
            display: block;
        }
        .train-status-strip {
            border-radius: 16px;
            border: 1px solid rgba(8, 42, 112, 0.14);
            padding: 0.7rem 0.86rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.8rem;
            box-shadow: 0 6px 16px rgba(16, 24, 40, 0.05);
        }
        .train-status-strip-left {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            min-width: 0;
        }
        .train-status-text {
            color: #1d2b44;
            font-size: 0.95rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .train-status-score {
            color: #5F6B7A;
            font-size: 0.9rem;
            font-weight: 620;
        }
        .train-status-bullet {
            margin: 0 8px 0 6px;
            color: #1d2b44;
            font-weight: 700;
        }
        .train-state-heading {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 0.5rem;
            margin-bottom: 0.65rem;
        }
        .train-state-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #F6C50E;
            flex-shrink: 0;
        }
        .train-state-title {
            color: #1F3D8A;
            font-size: 36px;
            font-weight: 800;
            line-height: 1.1;
            margin: 0;
            letter-spacing: 0.1px;
        }
        .train-strip-low {
            background: linear-gradient(180deg, #F3FBF5 0%, #EEF8F1 100%);
        }
        .train-strip-medium {
            background: linear-gradient(180deg, #FFFBEF 0%, #FFF7E4 100%);
        }
        .train-strip-high {
            background: linear-gradient(180deg, #FFF4F4 0%, #FFEEEE 100%);
        }
        .train-section-spacer {
            margin-top: 0.55rem;
        }
        .train-tight-divider {
            border-top: 1px solid rgba(8, 42, 112, 0.18);
            margin: 0.12rem 0 0.08rem 0;
        }
        .train-tight-section-head {
            margin-top: 0.06rem !important;
            margin-bottom: 0.05rem !important;
        }
        .train-tight-section-head .ds-section-title {
            font-size: 2rem !important;
            line-height: 1.2 !important;
        }
        .train-tight-section-head .ds-section-subtitle {
            margin-top: 0.04rem !important;
            font-size: 0.78rem !important;
            line-height: 1.2 !important;
        }
        .train-plan-history-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.85rem;
        }
        @media (max-width: 900px) {
            .train-plan-history-grid {
                grid-template-columns: 1fr;
            }
            .train-header-icon {
                width: 68px;
                height: 68px;
            }
            .train-header-icon svg {
                width: 34px;
                height: 34px;
            }
            .train-hero-title {
                font-size: 1.9rem;
            }
            .train-hero-status {
                font-size: 1.35rem;
            }
            .train-route-shell {
                width: 100%;
                max-width: 100%;
            }
            .train-header-right {
                margin-top: 0;
            }
            .train-header-image {
                width: 280px !important;
                max-width: 100% !important;
            }
            .train-route-wrap {
                justify-content: flex-start;
                margin-top: 0;
                padding-right: 0;
            }
            .train-route-track {
                flex-wrap: wrap;
                white-space: normal;
            }
            .train-hero-heading {
                display: block;
            }
            .train-state-title {
                font-size: 30px;
            }
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
    c1, c2, c3 = st.columns([3.8, 3.2, 3.0], gap="medium", vertical_alignment="top")

    with c1:
        safe_train_id = html.escape(str(train_id))
        st.markdown(
            f"""
            <div class="train-hero-heading">
                <div class="train-hero-title">APU DEL TREN #{safe_train_id}</div>
                <div class="train-hero-status">(Operativo)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="train-route-wrap">
                <div class="train-route-shell">
                    <div class="train-route-track">
                        <span class="train-route-stop">Parque inicial</span>
                        <span class="train-route-arrow">&rarr;</span>
                        <span class="train-route-stop active">Camino de mantenimiento</span>
                        <span class="train-route-arrow">&rarr;</span>
                        <span class="train-route-stop">Mantenimiento salida</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        if paths["train"].exists():
            encoded_train = base64.b64encode(paths["train"].read_bytes()).decode("ascii")
            st.markdown(
                f'''
                <div class="train-header-right">
                    <img class="train-header-image" src="data:image/png;base64,{encoded_train}" alt="Tren APU {safe_train_id}" />
                </div>
                ''',
                unsafe_allow_html=True,
            )
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
        height=362,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=20, b=12, l=8, r=8),
        legend=dict(orientation="h", y=1.1, x=0),
    )
    fig.update_yaxes(range=[0, 1], showgrid=True, gridcolor="rgba(35,75,141,0.12)")
    fig.update_xaxes(showgrid=False)
    return fig


def _build_drivers_chart(alert_reasons):
    """Grafico profesional de causas/drivers del riesgo con colores degradados."""
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
        # Paleta de colores degradada: Rojo -> Naranja -> Amarillo
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

    # Invertir para que la causa mas importante este arriba
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
    level = str(risk_level).upper()
    strip_class = "train-strip-low"
    icon_color = "#2ecc71"
    label = "RIESGO BAJO"
    if level == "MEDIO":
        strip_class = "train-strip-medium"
        icon_color = "#f39c12"
        label = "RIESGO MEDIO"
    elif level == "ALTO":
        strip_class = "train-strip-high"
        icon_color = "#e74c3c"
        label = "RIESGO ALTO"

    st.markdown(
        f"""
        <div class="train-status-strip {strip_class}">
            <div class="train-status-strip-left">
                {icon_chip("activity", icon_color, size=16, chip_size=30)}
                <div class="train-status-text">{label}</div>
                <div class="train-status-score"><span class="train-status-bullet">&bull;</span>Score: {float(score):.2f}</div>
            </div>
            <div style="color:#6A7891;font-size:16px;font-weight:700;line-height:1;">&#709;</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
            <label class="sensor-popup-close" for="{popup_id}">&times;</label>
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
    inject_global_styles()
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

    st.markdown(
        """
        <div class="train-state-heading">
            <span class="train-state-dot"></span>
            <h3 class="train-state-title">Estado Actual</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_risk_banner(risk_level_display, score_operational)
    if score_delta >= 0.03:
        st.warning(
            f"AVISO OPERATIVO: el riesgo general subió de {score:.3f} a {score_operational:.3f} por severidad detectada en sensores/relaciones."
        )

    m1, m2, m3 = st.columns(3, gap="medium")
    with m1:
        kpi_card(
            "Score de Riesgo Actual",
            f"{score_operational:.3f}",
            f"Ajuste {score_delta:+.3f}",
            icon="bar-chart",
            color="#082A70",
        )
    with m2:
        kpi_card(
            "Proyección a 2 horas",
            f"{float(prediction['projected_score']):.3f}",
            prediction["projected_level"],
            icon="clock",
            color="#8e44ad",
        )
    with m3:
        kpi_card(
            "Tendencia del Riesgo",
            trend_direction_display,
            trend_detail,
            icon="activity",
            color="#2ecc71",
        )

    section_title("Riesgo Operacional en el Tiempo", "")
    chart_card("Evolución de riesgo operacional", _build_risk_chart(alert_df))

    st.markdown('<div class="train-tight-divider"></div>', unsafe_allow_html=True)
    section_title("Sensores Clave del Tren", "", extra_class="train-tight-section-head")
    ensure_sensor_chart_styles()

    row1 = st.columns(4, gap="medium")
    with row1[0]:
        render_sensor_card("TP3_mean", train_df)
    with row1[1]:
        render_sensor_card("H1_mean", train_df)
    with row1[2]:
        render_sensor_card("DV_pressure_mean", train_df)
    with row1[3]:
        render_sensor_card("Motor_Current_mean", train_df)

    row2 = st.columns(3, gap="medium")
    with row2[0]:
        render_sensor_card("MPG_last", train_df)
    with row2[1]:
        render_sensor_card("Oil_Temperature_mean", train_df)
    with row2[2]:
        render_sensor_card("TOWERS_last", train_df)

    st.markdown('<div class="train-tight-divider"></div>', unsafe_allow_html=True)
    section_title("Señales Doradas del Tren", "", extra_class="train-tight-section-head")
    render_golden_signals(train_df, thresholds)

    st.markdown('<div class="train-tight-divider"></div>', unsafe_allow_html=True)
    render_financial_section(alert_df, prediction, compact_header=True)

    st.markdown("---")
    plan_col, history_col = st.columns([1, 1], gap="medium")
    with plan_col:
        section_title("Plan de Acción Recomendado", "")
        render_operativity_panel(train_df)
    with history_col:
        section_title("Historial de Eventos (Postmortem)", "Resumen de episodios relevantes para trazabilidad técnica.")
        render_postmortem_panel(alert_df, prediction, max_columns=1)

    if train_col:
        st.markdown("---")
        back_col1, back_col2 = st.columns([1, 3])
        with back_col1:
            if st.button("Volver al Home General"):
                st.session_state["nav_view"] = "system_home"
                st.rerun()


