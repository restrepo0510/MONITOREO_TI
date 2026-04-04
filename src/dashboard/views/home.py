from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.operativity_panel import render_operativity_panel
from src.dashboard.components.sensor_chart import ensure_sensor_chart_styles, render_sensor_card
from src.dashboard.components.station_line import render_station_line
from src.dashboard.theme import PALETTE, RISK_THRESHOLDS


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
            font-size: 1.55rem;
            font-weight: 700;
            color: #000000;
            margin-top: 1.7rem;
            margin-bottom: 0.95rem;
        }
        .section-subtitle {
            font-size: 1.25rem;
            font-weight: 700;
            color: #000000;
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
        .header-meta-wrap {
            text-align: left;
            margin-top: 2.1rem;
        }
        .header-train-wrap {
            text-align: right;
            margin-top: 0.35rem;
        }
        .header-train-meta {
            font-size: 1.22rem;
            font-weight: 700;
            color: #234B8D;
            line-height: 1.18;
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
            text-overflow: clip;
            scrollbar-width: none;
            width: 100%;
        }
        .station-line-row::-webkit-scrollbar {
            display: none;
        }
        .station-node {
            border-radius: 999px;
            padding: 0.22rem 0.58rem;
            font-size: 0.84rem;
            font-weight: 650;
            max-width: none;
            overflow: visible;
            text-overflow: clip;
            white-space: nowrap;
            line-height: 1.2;
            flex: 0 0 auto;
        }
        .station-prev, .station-next {
            background: rgba(184, 219, 217, 0.58);
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
            background: rgba(35, 75, 141, 0.45);
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
        css_class = "risk-banner risk-banner-high"
        title = "RIESGO ALTO"
        st.markdown(
            f"""
            <div class="{css_class}">
                <div class="risk-banner-title">{title}</div>
                <div class="risk-banner-score">Score: {score:.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif risk == "MEDIO":
        st.warning(f"RIESGO MEDIO - Score: {score:.2f}")
    else:
        st.info(f"RIESGO BAJO - Score: {score:.2f}")


def render(df):
    _inject_home_css()
    _render_header()

    # ULTIMO ESTADO
    latest = df.iloc[-1]
    risk = latest["risk_level"]
    score = latest["risk_score"]

    # ESTADO + RIESGO
    st.subheader("Estado actual del sistema")
    _render_risk_banner(risk, score)

    _subsection_title("Comportamiento del riesgo")
    st.plotly_chart(_build_risk_behavior_chart(df), use_container_width=True)

    st.markdown("---")

    # SENSORES
    ensure_sensor_chart_styles()
    _section_title("Sensores")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_sensor_card("TP3_mean", df)

    with c2:
        render_sensor_card("H1_mean", df)

    with c3:
        render_sensor_card("DV_pressure_mean", df)

    with c4:
        render_sensor_card("Motor_Current_mean", df)

    c5, c6, c7 = st.columns(3)

    with c5:
        render_sensor_card("MPG_last", df)

    with c6:
        render_sensor_card("Oil_Temperature_mean", df)

    with c7:
        render_sensor_card("TOWERS_last", df)

    st.markdown("---")

    # OPERATIVIDAD
    _subsection_title("Acciones recomendadas")
    render_operativity_panel(df)

    st.markdown("---")

    # POSTMORTEM
    _subsection_title("Postmortem / Registro")

    st.text_area(
        "Resumen del sistema",
        f"""
        Ultimo estado detectado: {risk}
        Score: {score:.3f}
        Timestamp: {latest["timestamp"]}
        """,
        height=150,
    )
