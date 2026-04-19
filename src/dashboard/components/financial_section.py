"""
Placeholder module.
Este archivo se completará en el desarrollo del dashboard.
"""

import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.kpi_card import render_kpi_card
from src.dashboard.theme import PALETTE


SCENARIO = {
    "cost_high_episode": 4200000,
    "cost_medium_episode": 1250000,
    "preventive_action_cost": 280000,
    "avoidance_ratio": 0.34,
}


def _format_cop(value: float) -> str:
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"COP {value / 1_000_000:.2f} M"
    if abs(value) >= 1_000:
        return f"COP {value / 1_000:.0f} K"
    return f"COP {value:.0f}"


def _estimate_financials(alerts_df, prediction):
    if alerts_df is None or alerts_df.empty:
        return {
            "high_events": 0,
            "medium_events": 0,
            "gross_exposure": 0.0,
            "preventive_budget": 0.0,
            "avoided_cost": 0.0,
            "net_value": 0.0,
            "roi": 0.0,
        }

    levels = alerts_df["alert_level"].fillna("BAJO")
    high_events = int(((levels == "ALTO") & (levels.shift(1) != "ALTO")).sum())
    medium_events = int(((levels == "MEDIO") & (levels.shift(1) != "MEDIO")).sum())
    projected_multiplier = 1.0
    if prediction.get("projected_level") == "ALTO":
        projected_multiplier = 1.35
    elif prediction.get("projected_level") == "MEDIO":
        projected_multiplier = 1.15

    gross_exposure = (
        (high_events * SCENARIO["cost_high_episode"])
        + (medium_events * SCENARIO["cost_medium_episode"])
    ) * projected_multiplier
    prioritized_actions = max(1, min(high_events + medium_events, 12))
    preventive_budget = prioritized_actions * SCENARIO["preventive_action_cost"]
    avoided_cost = gross_exposure * SCENARIO["avoidance_ratio"]
    net_value = avoided_cost - preventive_budget
    roi = (avoided_cost / preventive_budget) if preventive_budget > 0 else 0.0

    return {
        "high_events": high_events,
        "medium_events": medium_events,
        "gross_exposure": gross_exposure,
        "preventive_budget": preventive_budget,
        "avoided_cost": avoided_cost,
        "net_value": net_value,
        "roi": roi,
    }


def _build_waterfall(financials):
    fig = go.Figure(
        go.Waterfall(
            name="Impacto",
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Exposicion", "Mitigacion", "Valor neto"],
            y=[
                financials["gross_exposure"],
                -financials["preventive_budget"],
                financials["net_value"],
            ],
            connector={"line": {"color": "rgba(15, 30, 60, 0.18)"}},
            increasing={"marker": {"color": PALETTE["steel_azure"]}},
            decreasing={"marker": {"color": PALETTE["alert_red"]}},
            totals={"marker": {"color": "#173A73"}},
            hovertemplate="%{x}: COP %{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=290,
        margin=dict(t=18, b=12, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0F1E3C"),
    )
    fig.update_yaxes(showgrid=True, gridcolor="rgba(35, 75, 141, 0.10)")
    return fig


def render_financial_section(alerts_df, prediction):
    financials = _estimate_financials(alerts_df, prediction)

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        render_kpi_card(
            label="Exposicion economica",
            value=_format_cop(financials["gross_exposure"]),
            delta=f"{financials['high_events']} eventos altos y {financials['medium_events']} medios",
            caption="Estimacion demo del costo bruto expuesto por continuidad operativa y mantenimiento reactivo.",
            tone="red",
        )
    with c2:
        render_kpi_card(
            label="Mitigacion preventiva",
            value=_format_cop(financials["preventive_budget"]),
            delta=f"ROI potencial {financials['roi']:.1f}x",
            caption="Presupuesto de intervencion temprana para absorber backlog y evitar escalamiento.",
            tone="yellow",
        )
    with c3:
        render_kpi_card(
            label="Valor neto esperado",
            value=_format_cop(financials["net_value"]),
            delta=f"Ahorro potencial {_format_cop(financials['avoided_cost'])}",
            caption="Escenario de ahorro si se actua sobre las senales tempranas y la proyeccion del riesgo.",
            tone="blue",
        )

    st.plotly_chart(_build_waterfall(financials), use_container_width=True)
    st.caption(
        "Modelo financiero referencial para demo. Sustituible por costos reales del cliente sin tocar la experiencia visual."
    )
