import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from src.dashboard.components.alert_badge import render_alert_badge
from src.dashboard.components.kpi_card import render_kpi_card
from src.dashboard.components.postmortem_panel import build_alert_episodes
from src.dashboard.theme import PALETTE
from src.dashboard.views.ui_kit import (
    inject_operational_ui,
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


def _render_current_alert_banner(latest_row):
    level = latest_row.get("alert_level", "BAJO")
    reason = latest_row.get("alert_reasons", "Sin causas registradas")

    if level == "ALTO":
        st.error(f"ALERTA ALTA ACTIVA. {reason}")
    elif level == "MEDIO":
        st.warning(f"ALERTA EN OBSERVACION. {reason}")
    else:
        st.info("Sin alerta activa en la ultima ventana.")


def _inject_alerts_premium_css():
    st.markdown(
        """
        <style>
        .jj-alerts-hero {
            background: radial-gradient(circle at top right, rgba(255,230,0,0.16), transparent 28%),
                        linear-gradient(135deg, #FFFFFF 0%, #F6F9FF 52%, #EEF4FF 100%);
            border-radius: 28px;
            border: 1px solid rgba(35, 75, 141, 0.10);
            box-shadow: 0 24px 48px rgba(15, 30, 60, 0.10);
            padding: 1.2rem 1.25rem 1rem 1.25rem;
            margin-bottom: 1rem;
        }
        .jj-alerts-copy {
            color: #4E5C76;
            font-size: 0.94rem;
            line-height: 1.52;
            margin-top: 0.25rem;
        }
        .jj-alert-panel {
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


def _build_alert_timeline(alerts_df: pd.DataFrame):
    chart_df = alerts_df.tail(720).copy()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=chart_df["timestamp"],
            y=chart_df["risk_score"],
            mode="lines",
            name="Risk score",
            line=dict(color=PALETTE["steel_azure"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(35, 75, 141, 0.10)",
            hovertemplate="%{x}<br>Score %{y:.3f}<extra></extra>",
        )
    )

    for level, color in [("MEDIO", "#D5B700"), ("ALTO", PALETTE["alert_red"])]:
        subset = chart_df[chart_df["alert_level"] == level]
        if subset.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=subset["timestamp"],
                y=subset["risk_score"],
                mode="markers",
                name=f"Alertas {level}",
                marker=dict(color=color, size=8, line=dict(color="white", width=0.8)),
                hovertemplate="%{x}<br>" + level + " %{y:.3f}<extra></extra>",
            )
        )

    fig.update_layout(
        height=360,
        margin=dict(t=18, b=10, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0F1E3C"),
        legend=dict(orientation="h", y=1.10, x=0),
    )
    fig.update_yaxes(range=[0, 1], showgrid=True, gridcolor="rgba(35, 75, 141, 0.10)")
    fig.update_xaxes(showgrid=False)
    return fig


def _build_source_mix(alerts_df: pd.DataFrame):
    exploded = (
        alerts_df[alerts_df["alert_sources"] != "none"]["alert_sources"]
        .str.split("+")
        .explode()
        .value_counts()
        .reset_index()
    )
    if exploded.empty:
        exploded = pd.DataFrame({"index": ["none"], "count": [1]})
    exploded.columns = ["source", "count"]

    fig = px.bar(
        exploded,
        x="count",
        y="source",
        orientation="h",
        color="source",
        color_discrete_map={
            "riesgo": PALETTE["steel_azure"],
            "sensores": "#4A76BE",
            "relaciones": PALETTE["yellow"],
            "none": "#AFC4E8",
        },
    )
    fig.update_layout(
        height=250,
        margin=dict(t=12, b=12, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        font=dict(color="#0F1E3C"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(35, 75, 141, 0.08)")
    fig.update_yaxes(showgrid=False)
    return fig


def _build_driver_distribution(alerts_df: pd.DataFrame):
    drivers = []
    for reason in alerts_df["alert_reasons"].tolist():
        for chunk in str(reason).split("|"):
            part = chunk.strip()
            if not part:
                continue
            label = part.split(":", 1)[0].replace("_mean", "").replace("_last", "")
            drivers.append(label)

    if not drivers:
        driver_df = pd.DataFrame({"driver": ["Sin drivers"], "count": [1]})
    else:
        driver_df = (
            pd.Series(drivers).value_counts().head(8).reset_index()
        )
        driver_df.columns = ["driver", "count"]

    fig = px.bar(
        driver_df.sort_values("count"),
        x="count",
        y="driver",
        orientation="h",
        color="count",
        color_continuous_scale=["#D7E2F5", "#4A76BE", "#173A73"],
    )
    fig.update_layout(
        height=250,
        margin=dict(t=12, b=12, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        coloraxis_showscale=False,
        font=dict(color="#0F1E3C"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(35, 75, 141, 0.08)")
    fig.update_yaxes(showgrid=False)
    return fig


def render(df):
    inject_operational_ui()
    _inject_alerts_premium_css()

    render_view_header(
        "Estado de Alertas del Sistema",
        "Seguimiento de eventos críticos, episodios y proyección de riesgo en una sola vista.",
    )
    working_df = df.copy().sort_values("timestamp")
    thresholds, threshold_source = resolve_alert_thresholds(working_df)
    alerts_df, meta = evaluate_alerts(working_df.tail(3600), thresholds=thresholds)
    if alerts_df is None or alerts_df.empty:
        st.info("No hay datos para evaluar alertas.")
        return

    latest_alert, _ = evaluate_latest_alert(working_df.tail(3600), thresholds=thresholds)
    prediction = build_prediction_advisory(working_df.tail(3600), thresholds=thresholds)
    episodes = build_alert_episodes(alerts_df)

    alto = alerts_df[alerts_df["alert_level"] == "ALTO"].copy()
    medio = alerts_df[alerts_df["alert_level"] == "MEDIO"].copy()

    st.markdown('<div class="jj-alerts-hero">', unsafe_allow_html=True)
    hero_left, hero_right = st.columns([2.1, 1.0], gap="medium")
    with hero_left:
        st.markdown("### Monitoreo formal y prediccion")
        st.markdown(
            f'<div class="jj-alerts-copy">La vista de alertas ahora distingue tres capas: riesgo global, alertas atribuibles a sensores y reglas de relacion entre sensores. Fuente de umbrales: {threshold_source}.</div>',
            unsafe_allow_html=True,
        )
        st.caption(prediction["message"])
    with hero_right:
        latest_score = float(working_df["risk_score"].iloc[-1]) if "risk_score" in working_df.columns else None
        render_level_badge(latest_alert["alert_level"], latest_score)
        render_alert_badge(
            latest_alert["alert_level"],
            label="Estado actual",
            caption=f"Triggers {latest_alert['alert_trigger_count']} | Proyeccion {prediction['projected_level']}",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        render_kpi_card(
            label="Ventanas ALTO",
            value=str(len(alto)),
            caption="Ventanas recientes con severidad alta segun el motor formal.",
            tone="red",
        )
    with c2:
        render_kpi_card(
            label="Ventanas MEDIO",
            value=str(len(medio)),
            caption="Ventanas en observacion antes de un posible escalamiento.",
            tone="yellow",
        )
    with c3:
        render_kpi_card(
            label="Episodios",
            value=str(len(episodes)),
            caption="Bloques contiguos de alertas para lectura operativa mas limpia.",
            tone="blue",
        )
    with c4:
        minutes_to_high = prediction.get("minutes_to_high")
        eta_text = f"{minutes_to_high} min" if minutes_to_high is not None else "Sin cruce"
        render_kpi_card(
            label="ETA a ALTO",
            value=eta_text,
            delta=prediction["trend_direction"].upper(),
            caption="Tiempo estimado para alcanzar ALTO si la pendiente reciente se sostiene.",
            tone="dark",
        )

    if alto.empty and medio.empty:
        st.info("Sin alertas historicas activas. Sistema operando en rango normal.")
        return

    render_section_header(
        "Riesgo Operacional y Causas",
        "Línea temporal de alertas junto a las fuentes que están explicando el comportamiento actual.",
    )
    line_col, source_col = st.columns([1.8, 1.0], gap="medium")
    with line_col:
        st.plotly_chart(_build_alert_timeline(alerts_df), use_container_width=True)
    with source_col:
        st.markdown('<div class="jj-alert-panel">', unsafe_allow_html=True)
        st.markdown("**Mix de fuentes**")
        st.plotly_chart(_build_source_mix(alerts_df), use_container_width=True)
        st.markdown("**Drivers mas repetidos**")
        st.plotly_chart(_build_driver_distribution(alerts_df[alerts_df["alert_level"] != "BAJO"]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_header(
        "Eventos Recientes con Alerta",
        "Detalle de ventanas recientes donde el sistema detectó condiciones de observación o criticidad.",
    )
    alert_table = (
        alerts_df[alerts_df["alert_level"] != "BAJO"][
            [
                "timestamp",
                "alert_level",
                "risk_score",
                "risk_level",
                "alert_sources",
                "alert_trigger_count",
                "alert_reasons",
            ]
        ]
        .sort_values("timestamp", ascending=False)
        .head(80)
        .reset_index(drop=True)
    )
    st.dataframe(alert_table, use_container_width=True, height=360)

    render_section_header(
        "Proyección de Riesgo",
        "Estimación del próximo nivel de riesgo si se mantiene la tendencia reciente.",
    )
    pred1, pred2 = st.columns([1.1, 1.2], gap="medium")
    with pred1:
        render_alert_badge(
            prediction["projected_level"],
            label="Nivel proyectado",
            caption=f"Score proyectado {prediction['projected_score']:.3f} | Confianza {prediction['confidence']}%",
        )
        st.caption(prediction["message"])
    with pred2:
        hist_df = alerts_df[alerts_df["alert_level"] != "BAJO"].copy()
        fig = px.histogram(
            hist_df,
            x="risk_score",
            color="alert_level",
            nbins=24,
            barmode="overlay",
            category_orders={"alert_level": ["ALTO", "MEDIO"]},
            color_discrete_map={"ALTO": PALETTE["alert_red"], "MEDIO": PALETTE["yellow"]},
        )
        fig.update_layout(
            height=270,
            margin=dict(t=16, b=10, l=6, r=6),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#0F1E3C"),
            legend_title_text="Nivel",
        )
        st.plotly_chart(fig, use_container_width=True)

    if not episodes.empty:
        render_section_header(
            "Resumen de Episodios",
            "Agrupación de alertas consecutivas para simplificar análisis operativo.",
        )
        episode_table = episodes[
            ["start", "end", "level", "max_score", "sources", "duration_min", "windows"]
        ].head(20)
        st.dataframe(episode_table, use_container_width=True, height=260)

    st.caption(
        f"Motor {meta.get('engine_version', 'v2')} | Fuente umbrales {meta.get('threshold_source', 'N/A')} | Riesgo medio >= {meta.get('risk_threshold_medium', 0.4):.2f} | Riesgo alto >= {meta.get('risk_threshold_high', 0.7):.2f}"
    )
