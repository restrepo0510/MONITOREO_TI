from pathlib import Path

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
    render_level_badge,
    render_section_header,
    render_view_header,
)
from src.dashboard.utils.alert_engine import (
    build_prediction_advisory,
    evaluate_alerts,
    evaluate_latest_alert,
    resolve_alert_thresholds,
)

TRAIN_ID_CANDIDATES = ["train_id", "train", "id_train", "apu_id", "engine_id"]


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
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=risk_df["timestamp"],
            y=risk_df["risk_score"],
            mode="lines",
            name="Risk Score",
            line=dict(color=PALETTE["steel_azure"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(184,219,217,0.30)",
            hovertemplate="%{x}<br>Score: %{y:.3f}<extra></extra>",
        )
    )

    high_events = risk_df[risk_df["risk_score"] >= RISK_THRESHOLDS["ALTO"]]
    if not high_events.empty:
        fig.add_trace(
            go.Scatter(
                x=high_events["timestamp"],
                y=high_events["risk_score"],
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
    chunks = [chunk.strip() for chunk in str(alert_reasons).split("|") if chunk.strip()]
    labels = []
    values = []
    for idx, chunk in enumerate(chunks[:5], start=1):
        label = chunk.split(":", 1)[0].replace("_mean", "").replace("_last", "")
        labels.append(label)
        values.append(max(1, 6 - idx))
    if not labels:
        labels = ["Estable"]
        values = [1]

    fig = go.Figure(
        go.Bar(
            x=values[::-1],
            y=labels[::-1],
            orientation="h",
            marker=dict(color=["#234B8D", "#4A76BE", "#7698D0", "#AFC4E8", "#D7E2F5"][: len(labels)][::-1]),
            hovertemplate="%{y}<extra></extra>",
        )
    )
    fig.update_layout(height=300, margin=dict(t=10, b=10, l=6, r=6), xaxis_title="Peso relativo")
    fig.update_xaxes(showgrid=True, gridcolor="rgba(35,75,141,0.08)")
    fig.update_yaxes(showgrid=False)
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


def render(df):
    _inject_css()
    working_df = df.copy().sort_values("timestamp")
    train_df, train_id, train_col = _selected_train_df(working_df)
    _render_header(train_id)
    render_view_header(
        "Vista Tren (Operativa)",
        "Monitoreo detallado del tren seleccionado: estado actual, señales clave, riesgo, finanzas y acciones.",
    )

    latest = train_df.iloc[-1]
    risk_level = str(latest["risk_level"]).upper()
    score = float(latest["risk_score"])
    thresholds, _ = resolve_alert_thresholds(train_df)
    alert_df, _meta = evaluate_alerts(train_df.tail(2400), thresholds=thresholds)
    latest_alert, _ = evaluate_latest_alert(train_df.tail(2400), thresholds=thresholds)
    prediction = build_prediction_advisory(train_df.tail(2400), thresholds=thresholds)

    render_section_header("Estado Actual del Tren", "Lectura instantánea del nivel de riesgo operacional.")
    _render_risk_banner(risk_level, score)
    render_level_badge(risk_level, score)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Score de Riesgo Actual", f"{score:.3f}")
    with m2:
        st.metric("Proyección a 2 horas", f"{float(prediction['projected_score']):.3f}", prediction["projected_level"])
    with m3:
        st.metric("Tendencia del Riesgo", prediction["trend_direction"].upper(), f"Triggers {int(latest_alert['alert_trigger_count'])}")

    render_section_header("Riesgo Operacional en el Tiempo", "Evolución temporal del riesgo con umbrales de decisión.")
    st.plotly_chart(_build_risk_chart(train_df), use_container_width=True)

    st.markdown("---")
    render_section_header("Sensores Clave del Tren", "Comportamiento de las señales críticas para diagnóstico operativo.")
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
    render_section_header("Señales Doradas del Tren", "Indicadores agregados que resumen la salud operativa del equipo.")
    render_golden_signals(train_df, thresholds)

    st.markdown("---")
    render_section_header("Impacto Financiero del Tren", "Estimación de costo evitado y valor de actuar preventivamente.")
    render_financial_section(alert_df, prediction)

    st.markdown("---")
    render_section_header("Causas Actuales del Riesgo", "Factores que están empujando el riesgo en la lectura actual.")
    st.plotly_chart(_build_drivers_chart(latest_alert["alert_reasons"]), use_container_width=True)

    st.markdown("---")
    render_section_header("Plan de Acción Recomendado", "Acciones operativas sugeridas según el estado del tren.")
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
