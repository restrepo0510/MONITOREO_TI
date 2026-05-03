"""Componente de impacto financiero para el dashboard."""

import streamlit as st

from src.dashboard.components.kpi_card import render_kpi_card
from src.dashboard.components.ui_kit import section_title


SCENARIO = {
    "cost_high_episode": 4_200_000,
    "cost_medium_episode": 1_250_000,
    "preventive_action_cost": 280_000,
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


def render_financial_section(alerts_df, prediction, compact_header: bool = False):
    """Renderiza la sección de impacto financiero (sin gráfica)."""
    financials = _estimate_financials(alerts_df, prediction)

    if compact_header:
        section_title("Impacto Financiero del Tren", "", extra_class="train-tight-section-head")
    else:
        section_title("Impacto Financiero del Tren", "")

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        render_kpi_card(
            label="Exposición Económica",
            value=_format_cop(financials["gross_exposure"]),
            delta=f"{financials['high_events']} eventos altos y {financials['medium_events']} medios",
            caption="Estimación del costo bruto expuesto por continuidad operativa y mantenimiento reactivo.",
            tone="red",
        )

    with c2:
        roi_value = financials["roi"]
        roi_text = f"ROI potencial {roi_value:.1f}x" if roi_value > 0 else "ROI potencial 0x"
        render_kpi_card(
            label="Mitigación Preventiva",
            value=_format_cop(financials["preventive_budget"]),
            delta=roi_text,
            caption="Presupuesto de intervención temprana para absorber backlog y evitar escalamiento.",
            tone="yellow",
        )

    with c3:
        render_kpi_card(
            label="Valor Neto Esperado",
            value=_format_cop(financials["net_value"]),
            delta=f"Ahorro potencial {_format_cop(financials['avoided_cost'])}",
            caption="Escenario de ahorro si se actúa sobre las señales tempranas y la proyección de riesgo.",
            tone="green",
        )
