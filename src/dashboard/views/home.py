from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.alert_badge import render_alert_badge
from src.dashboard.components.financial_section import render_financial_section
from src.dashboard.components.golden_signals import render_golden_signals
from src.dashboard.components.kpi_card import render_kpi_card
from src.dashboard.components.operativity_panel import render_operativity_panel
from src.dashboard.components.postmortem_panel import render_postmortem_panel
from src.dashboard.components.station_line import render_station_line
from src.dashboard.theme import PALETTE, RISK_THRESHOLDS
from src.dashboard.utils.alert_engine import (
    build_prediction_advisory,
    evaluate_alerts,
    evaluate_latest_alert,
    resolve_alert_thresholds,
)


def _image_paths():
    assets_dir = Path(__file__).resolve().parents[1] / "assets" / "images"
    return {
        "logo": assets_dir / "logo.png",
        "train": assets_dir / "train.png",
    }


def _render_header():
    paths = _image_paths()
    top_left, top_title, top_meta, top_train = st.columns(
        [0.9, 2.35, 2.25, 1.85],
        gap="small",
        vertical_alignment="center",
    )

    with top_left:
        if paths["logo"].exists():
            st.image(str(paths["logo"]), width=145)
        else:
            st.caption("Logo: src/dashboard/assets/images/logo.png")

    with top_title:
        st.markdown(
            '<div class="main-title">APU DEL TREN #001</div>',
            unsafe_allow_html=True,
        )

    with top_meta:
        render_station_line(train_id="001", cycle_seconds=5)

    with top_train:
        st.markdown('<div class="header-train-wrap">', unsafe_allow_html=True)
        if paths["train"].exists():
            st.image(str(paths["train"]), width=335)
        else:
            st.caption("Tren local: src/dashboard/assets/images/train.png")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="margin-bottom:0.1rem;"></div>', unsafe_allow_html=True)


def _inject_home_css():
    st.markdown(
        """
        <style>
        .section-title {
            font-size: 1.45rem;
            font-weight: 700;
            color: #234B8D;
            margin-top: 1.7rem;
            margin-bottom: 0.95rem;
            border-bottom: 2px solid #234B8D;
            padding-bottom: 0.3rem;
        }
        .section-subtitle {
            font-size: 1.2rem;
            font-weight: 700;
            color: #234B8D;
            margin-top: 1.35rem;
            margin-bottom: 0.75rem;
        }
        .main-title {
            color: #234B8D;
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: 0.3px;
            margin-top: 0;
            margin-bottom: 0;
            line-height: 1.1;
        }
        .header-train-wrap {
            text-align: right;
            margin-top: 0.35rem;
        }
        .station-strip {
            margin-top: 0.85rem;
            margin-left: -0.65rem;
        }
        .station-train-id {
            font-size: 1.02rem;
            font-weight: 700;
            color: #234B8D;
            margin-bottom: 0.34rem;
        }
        .station-line-row {
            display: flex;
            align-items: center;
            gap: 0.48rem;
            flex-wrap: nowrap;
            white-space: nowrap;
            overflow-x: auto;
            overflow-y: hidden;
            scrollbar-width: none;
            width: 100%;
        }
        .station-line-row::-webkit-scrollbar { display: none; }
        .station-node {
            border-radius: 999px;
            padding: 0.22rem 0.58rem;
            font-size: 0.84rem;
            font-weight: 650;
            white-space: nowrap;
            line-height: 1.2;
            flex: 0 0 auto;
        }
        .station-prev, .station-next {
            background: rgba(184,219,217,0.58);
            color: #234B8D;
        }
        .station-current {
            background: #234B8D;
            color: #F4F4F9;
            font-size: 0.88rem;
            font-weight: 760;
        }
        .station-connector {
            height: 2px;
            width: 22px;
            background: rgba(35,75,141,0.45);
            border-radius: 999px;
            flex: 0 0 auto;
        }
        .risk-banner {
            width: 100%;
            border-radius: 12px;
            padding: 0.9rem 1rem;
            margin-top: 0.25rem;
            margin-bottom: 0.25rem;
            border: 1px solid transparent;
        }
        .risk-banner-title {
            font-size: 1.15rem;
            font-weight: 850;
            line-height: 1.1;
            margin-bottom: 0.15rem;
            letter-spacing: 0.2px;
        }
        .risk-banner-score {
            font-size: 0.96rem;
            font-weight: 650;
            opacity: 0.95;
        }
        .risk-banner-high {
            background: #D32F2F;
            color: #F4F4F9;
            border-color: #B71C1C;
        }
        .stTextArea textarea {
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section_title(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def _subsection_title(text):
    st.markdown(f'<div class="section-subtitle">{text}</div>', unsafe_allow_html=True)


def _build_risk_behavior_chart(df):
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
        height=310,
        paper_bgcolor=PALETTE["ghost_white"],
        plot_bgcolor="white",
        font=dict(color=PALETTE["black"]),
        margin=dict(t=24, b=12, l=8, r=8),
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis_title="Tiempo",
        yaxis_title="Risk Score",
    )
    fig.update_yaxes(range=[0, 1], showgrid=True, gridcolor="rgba(35,75,141,0.12)")
    fig.update_xaxes(showgrid=False)
    return fig


def _render_risk_banner(risk, score):
    if risk == "ALTO":
        st.markdown(
            f"""
            <div class="risk-banner risk-banner-high">
                <div class="risk-banner-title">RIESGO ALTO</div>
                <div class="risk-banner-score">Score: {score:.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif risk == "MEDIO":
        st.warning(f"RIESGO MEDIO — Score: {score:.2f}")
    else:
        st.info(f"RIESGO BAJO — Score: {score:.2f}")


def _inject_home_premium_css():
    st.markdown(
        """
        <style>
        .jj-home-title {
            color: #234B8D;
            font-size: 2.45rem;
            font-weight: 850;
            line-height: 1.02;
            margin-bottom: 0.25rem;
        }
        .jj-home-subtitle {
            color: #445472;
            font-size: 0.96rem;
            line-height: 1.55;
            max-width: 880px;
        }
        .jj-section-kicker {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #6A7894;
            font-weight: 800;
            margin-top: 1.3rem;
            margin-bottom: 0.28rem;
        }
        .jj-section-title {
            font-size: 1.55rem;
            color: #0F1E3C;
            font-weight: 850;
            margin-bottom: 0.15rem;
        }
        .jj-section-copy {
            font-size: 0.93rem;
            color: #53617C;
            line-height: 1.5;
            margin-bottom: 0.95rem;
        }
        .jj-hero-shell {
            background: radial-gradient(circle at top right, rgba(255,230,0,0.16), transparent 28%),
                        linear-gradient(135deg, #FFFFFF 0%, #F6F9FF 55%, #EEF4FF 100%);
            border: 1px solid rgba(35, 75, 141, 0.10);
            border-radius: 28px;
            padding: 1.2rem 1.25rem 1rem 1.25rem;
            box-shadow: 0 24px 48px rgba(15, 30, 60, 0.10);
            margin-bottom: 1rem;
        }
        .jj-header-train-wrap {
            text-align: right;
            margin-top: 0.25rem;
        }
        .jj-driver-card {
            background: #FFFFFF;
            border-radius: 22px;
            padding: 1rem;
            border: 1px solid rgba(35, 75, 141, 0.10);
            box-shadow: 0 18px 34px rgba(15, 30, 60, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section_header(kicker, title, copy):
    st.markdown(f'<div class="jj-section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="jj-section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="jj-section-copy">{copy}</div>', unsafe_allow_html=True)


def _render_premium_header():
    paths = _image_paths()
    left, title_col, meta_col, train_col = st.columns(
        [0.9, 2.2, 2.1, 1.8], gap="small", vertical_alignment="center"
    )

    with left:
        if paths["logo"].exists():
            st.image(str(paths["logo"]), width=145)

    with title_col:
        st.markdown(
            '<div class="jj-home-title">Command Center APU 001</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="jj-home-subtitle">Vista ejecutiva para monitoreo, continuidad operativa y priorizacion de mantenimiento con lectura explicable del riesgo.</div>',
            unsafe_allow_html=True,
        )

    with meta_col:
        render_station_line(train_id="001", cycle_seconds=5)

    with train_col:
        st.markdown('<div class="jj-header-train-wrap">', unsafe_allow_html=True)
        if paths["train"].exists():
            st.image(str(paths["train"]), width=330)
        st.markdown("</div>", unsafe_allow_html=True)


def _build_premium_risk_chart(df, prediction):
    risk_df = df.tail(720).copy()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=risk_df["timestamp"],
            y=risk_df["risk_score"],
            mode="lines",
            name="Risk score",
            line=dict(color=PALETTE["steel_azure"], width=2.7),
            fill="tozeroy",
            fillcolor="rgba(35, 75, 141, 0.12)",
            hovertemplate="%{x}<br>Score %{y:.3f}<extra></extra>",
        )
    )
    fig.add_hline(y=RISK_THRESHOLDS["MEDIO"], line_dash="dash", line_color="#D5B700")
    fig.add_hline(y=RISK_THRESHOLDS["ALTO"], line_dash="dash", line_color=PALETTE["alert_red"])
    fig.add_trace(
        go.Scatter(
            x=[risk_df["timestamp"].iloc[-1]],
            y=[prediction["projected_score"]],
            mode="markers",
            name="Proyeccion 2h",
            marker=dict(
                color=PALETTE["yellow"],
                size=12,
                line=dict(color="#0F1E3C", width=1.2),
            ),
            hovertemplate="Proyeccion 2h<br>%{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=360,
        margin=dict(t=20, b=10, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0F1E3C"),
        legend=dict(orientation="h", y=1.10, x=0),
    )
    fig.update_yaxes(range=[0, 1], showgrid=True, gridcolor="rgba(35, 75, 141, 0.10)")
    fig.update_xaxes(showgrid=False)
    return fig


def _build_driver_chart(alert_reasons):
    chunks = [chunk.strip() for chunk in str(alert_reasons).split("|") if chunk.strip()]
    labels = []
    values = []
    for idx, chunk in enumerate(chunks[:5], start=1):
        label = chunk.split(":", 1)[0].replace("_mean", "").replace("_last", "")
        labels.append(label)
        values.append(max(1, 6 - idx))

    if not labels:
        labels = ["Operacion estable"]
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
    fig.update_layout(
        height=360,
        margin=dict(t=20, b=12, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0F1E3C"),
        xaxis_title="Peso relativo",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(35, 75, 141, 0.08)")
    fig.update_yaxes(showgrid=False)
    return fig


def render(df):
    _inject_home_css()
    _inject_home_premium_css()
    _render_premium_header()

    working_df = df.copy().sort_values("timestamp")
    thresholds, threshold_source = resolve_alert_thresholds(working_df)
    alert_df, meta = evaluate_alerts(working_df.tail(2400), thresholds=thresholds)
    latest_alert, _ = evaluate_latest_alert(working_df.tail(2400), thresholds=thresholds)
    prediction = build_prediction_advisory(working_df.tail(2400), thresholds=thresholds)
    latest = working_df.iloc[-1]

    st.markdown('<div class="jj-hero-shell">', unsafe_allow_html=True)
    hero_left, hero_right = st.columns([2.2, 1.0], gap="medium")
    with hero_left:
        _section_header(
            "Executive View",
            "Estado general del sistema",
            f"Fuente de umbrales: {threshold_source}. Esta vista mezcla riesgo global, comportamiento por sensor y relaciones entre sensores para explicar mejor cada alerta.",
        )
    with hero_right:
        render_alert_badge(
            latest_alert["alert_level"],
            label="Alerta operacional",
            caption=f"Score {float(latest['risk_score']):.3f} | Proyeccion {prediction['projected_level']}",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        render_kpi_card(
            label="Riesgo actual",
            value=f"{float(latest['risk_score']):.3f}",
            delta=str(latest["risk_level"]).upper(),
            caption="Lectura actual del score entregado por el pipeline.",
            tone="blue",
        )
    with k2:
        render_kpi_card(
            label="Proyeccion 2 horas",
            value=f"{prediction['projected_score']:.3f}",
            delta=prediction["trend_direction"].upper(),
            caption="Trayectoria esperada si la pendiente reciente se mantiene.",
            tone="yellow" if prediction["projected_level"] != "BAJO" else "dark",
        )
    with k3:
        render_kpi_card(
            label="Ventanas criticas",
            value=str(int((alert_df["alert_level"] == "ALTO").sum())),
            delta=f"{int((alert_df['alert_level'] == 'MEDIO').sum())} en observacion",
            caption="Carga de ventanas que ya merecen accion operativa.",
            tone="red",
        )
    with k4:
        render_kpi_card(
            label="Triggers activos",
            value=str(int(latest_alert["alert_trigger_count"])),
            delta=latest_alert["alert_sources"].replace("+", " + ").upper(),
            caption="Cantidad de causas encendidas en la lectura actual.",
            tone="dark",
        )

    _section_header(
        "Risk Story",
        "Comportamiento del riesgo y drivers activos",
        "Cruza la trayectoria del score con los factores que mas pesan ahora mismo para que el dashboard no solo se vea premium, sino tambien explicable.",
    )
    chart_col, driver_col = st.columns([1.8, 1.0], gap="medium")
    with chart_col:
        st.plotly_chart(_build_premium_risk_chart(working_df, prediction), use_container_width=True)
    with driver_col:
        st.markdown('<div class="jj-driver-card">', unsafe_allow_html=True)
        st.markdown("**Drivers criticos ahora**")
        st.plotly_chart(_build_driver_chart(latest_alert["alert_reasons"]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    _section_header(
        "Golden Signals",
        "Senales doradas de la APU",
        "Sintesis premium de disponibilidad neumatica, esfuerzo del compresor, estabilidad de descarga y condicion termica.",
    )
    render_golden_signals(working_df, thresholds)

    _section_header(
        "Finance Layer",
        "Impacto financiero estimado",
        "Modelo referencial para mostrar valor de negocio desde la primera vista, listo para adaptarse luego a costos reales del cliente.",
    )
    render_financial_section(alert_df, prediction)

    _section_header(
        "Operational Playbook",
        "Acciones recomendadas",
        "Plan accionable para operacion y mantenimiento a partir del ultimo estado consolidado por el motor de alertas.",
    )
    render_operativity_panel(working_df.tail(2400))
    st.caption(
        f"Motor {meta.get('engine_version', 'v2')} | Umbral medio {meta.get('risk_threshold_medium', 0.4):.2f} | Umbral alto {meta.get('risk_threshold_high', 0.7):.2f}"
    )

    _section_header(
        "Postmortem",
        "Postmortem inteligente",
        "Lectura ejecutiva de los episodios recientes para convertir telemetria en historia operativa y decisiones concretas.",
    )
    render_postmortem_panel(alert_df, prediction)
