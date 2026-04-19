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
    return {"logo": assets_dir / "logo.png", "train": assets_dir / "train.png"}


def _inject_css():
    st.markdown(
        """
        <style>
        .legacy-premium-title {
            color: #234B8D;
            font-size: 2.3rem;
            font-weight: 850;
            line-height: 1.02;
            margin-bottom: 0.2rem;
        }
        .legacy-premium-subtitle {
            color: #445472;
            font-size: 0.95rem;
            line-height: 1.5;
            max-width: 880px;
        }
        .legacy-premium-kicker {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            color: #6A7894;
            font-weight: 800;
            margin-top: 1.2rem;
            margin-bottom: 0.25rem;
        }
        .legacy-premium-section {
            font-size: 1.45rem;
            color: #0F1E3C;
            font-weight: 850;
            margin-bottom: 0.15rem;
        }
        .legacy-premium-copy {
            font-size: 0.92rem;
            color: #53617C;
            line-height: 1.5;
            margin-bottom: 0.9rem;
        }
        .legacy-premium-shell {
            background: radial-gradient(circle at top right, rgba(255,230,0,0.16), transparent 28%),
                        linear-gradient(135deg, #FFFFFF 0%, #F6F9FF 55%, #EEF4FF 100%);
            border: 1px solid rgba(35, 75, 141, 0.10);
            border-radius: 28px;
            padding: 1.1rem 1.2rem 0.95rem 1.2rem;
            box-shadow: 0 24px 48px rgba(15, 30, 60, 0.10);
            margin-bottom: 1rem;
        }
        .legacy-premium-driver {
            background: #FFFFFF;
            border-radius: 22px;
            padding: 0.95rem;
            border: 1px solid rgba(35, 75, 141, 0.10);
            box-shadow: 0 18px 34px rgba(15, 30, 60, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header():
    paths = _image_paths()
    c1, c2, c3, c4 = st.columns([0.9, 2.2, 2.1, 1.8], gap="small", vertical_alignment="center")
    with c1:
        if paths["logo"].exists():
            st.image(str(paths["logo"]), width=145)
    with c2:
        st.markdown('<div class="legacy-premium-title">Command Center APU 001 (Legacy 2026-04-06)</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="legacy-premium-subtitle">Vista ejecutiva premium con trazabilidad de alertas, drivers y narrativa de riesgo.</div>',
            unsafe_allow_html=True,
        )
    with c3:
        render_station_line(train_id="001", cycle_seconds=5)
    with c4:
        if paths["train"].exists():
            st.image(str(paths["train"]), width=330)


def _section_header(kicker: str, title: str, copy: str):
    st.markdown(f'<div class="legacy-premium-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="legacy-premium-section">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="legacy-premium-copy">{copy}</div>', unsafe_allow_html=True)


def _build_risk_chart(df, prediction):
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
            marker=dict(color=PALETTE["yellow"], size=12, line=dict(color="#0F1E3C", width=1.2)),
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

    colors = ["#234B8D", "#4A76BE", "#7698D0", "#AFC4E8", "#D7E2F5"][: len(labels)][::-1]
    fig = go.Figure(
        go.Bar(
            x=values[::-1],
            y=labels[::-1],
            orientation="h",
            marker=dict(color=colors),
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
    _inject_css()
    _render_header()

    working_df = df.copy().sort_values("timestamp")
    thresholds, threshold_source = resolve_alert_thresholds(working_df)
    alert_df, meta = evaluate_alerts(working_df.tail(2400), thresholds=thresholds)
    latest_alert, _ = evaluate_latest_alert(working_df.tail(2400), thresholds=thresholds)
    prediction = build_prediction_advisory(working_df.tail(2400), thresholds=thresholds)
    latest = working_df.iloc[-1]

    st.markdown('<div class="legacy-premium-shell">', unsafe_allow_html=True)
    left, right = st.columns([2.2, 1.0], gap="medium")
    with left:
        _section_header(
            "Executive View",
            "Estado general del sistema",
            f"Fuente de umbrales: {threshold_source}. Vista premium historica incorporada al panel unificado.",
        )
    with right:
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
        "Cruza la trayectoria del score con los factores que mas pesan ahora mismo.",
    )
    chart_col, driver_col = st.columns([1.8, 1.0], gap="medium")
    with chart_col:
        st.plotly_chart(_build_risk_chart(working_df, prediction), use_container_width=True)
    with driver_col:
        st.markdown('<div class="legacy-premium-driver">', unsafe_allow_html=True)
        st.markdown("**Drivers criticos ahora**")
        st.plotly_chart(_build_driver_chart(latest_alert["alert_reasons"]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    _section_header(
        "Golden Signals",
        "Senales doradas de la APU",
        "Sintesis premium de disponibilidad neumatica y condicion termica.",
    )
    render_golden_signals(working_df, thresholds)

    _section_header(
        "Finance Layer",
        "Impacto financiero estimado",
        "Modelo referencial para mostrar valor de negocio.",
    )
    render_financial_section(alert_df, prediction)

    _section_header(
        "Operational Playbook",
        "Acciones recomendadas",
        "Plan accionable para operacion y mantenimiento.",
    )
    render_operativity_panel(working_df.tail(2400))
    st.caption(
        f"Motor {meta.get('engine_version', 'v2')} | Umbral medio {meta.get('risk_threshold_medium', 0.4):.2f} | Umbral alto {meta.get('risk_threshold_high', 0.7):.2f}"
    )

    _section_header(
        "Postmortem",
        "Postmortem inteligente",
        "Lectura ejecutiva de los episodios recientes.",
    )
    render_postmortem_panel(alert_df, prediction)
