import plotly.express as px
import streamlit as st

from src.dashboard.theme import PALETTE
from src.dashboard.utils.alert_engine import evaluate_alerts


def _render_current_alert_banner(latest_row):
    level = latest_row.get("alert_level", "BAJO")
    reason = latest_row.get("alert_reasons", "Sin causas registradas")

    if level == "ALTO":
        st.error(f"ALERTA ALTA ACTIVA. {reason}")
    elif level == "MEDIO":
        st.warning(f"ALERTA EN OBSERVACION. {reason}")
    else:
        st.info("Sin alerta activa en la ultima ventana.")


def render(df):
    st.title("Panel de Alertas")
    st.markdown("---")

    alerts_df, meta = evaluate_alerts(df)
    if alerts_df is None or alerts_df.empty:
        st.info("No hay datos para evaluar alertas.")
        return

    latest = alerts_df.iloc[-1]
    _render_current_alert_banner(latest)

    st.caption(
        f"Motor: {meta.get('engine_version', 'v1')} | "
        f"Fuente umbrales: {meta.get('threshold_source', 'N/A')} | "
        f"Regla riesgo: medio>={meta.get('risk_threshold_medium', 0.4):.2f}, "
        f"alto>={meta.get('risk_threshold_high', 0.7):.2f}"
    )

    alto = alerts_df[alerts_df["alert_level"] == "ALTO"].copy()
    medio = alerts_df[alerts_df["alert_level"] == "MEDIO"].copy()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Ventanas ALTO", len(alto))
    with c2:
        st.metric("Ventanas MEDIO", len(medio))
    with c3:
        st.metric("Total evaluadas", len(alerts_df))

    if alto.empty and medio.empty:
        st.info("Sin alertas historicas activas. Sistema operando en rango normal.")
        return

    st.markdown("---")
    st.subheader("Ultimas ventanas con alerta")

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

    st.markdown("---")
    st.subheader("Distribucion de alertas por score")

    alert_hist_df = alerts_df[alerts_df["alert_level"] != "BAJO"].copy()
    fig = px.histogram(
        alert_hist_df,
        x="risk_score",
        color="alert_level",
        nbins=24,
        barmode="overlay",
        category_orders={"alert_level": ["ALTO", "MEDIO"]},
        color_discrete_map={"ALTO": PALETTE["alert_red"], "MEDIO": PALETTE["yellow"]},
        labels={"risk_score": "Risk Score", "count": "Ventanas"},
        title="Scores asociados a ventanas con alerta",
    )
    fig.update_layout(
        height=320,
        margin=dict(t=42, b=16, l=8, r=8),
        paper_bgcolor=PALETTE["ghost_white"],
        plot_bgcolor="white",
        font=dict(color=PALETTE["black"]),
        legend_title_text="Nivel",
    )
    st.plotly_chart(fig, use_container_width=True)
