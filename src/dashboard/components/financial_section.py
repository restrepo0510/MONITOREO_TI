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


def _build_financial_chart(financials):
    """Gráfica de barras comparativa mejorada para impacto financiero"""
    
    fig = go.Figure(data=[
        go.Bar(
            x=["Exposición\nEconómica", "Mitigación\nPreventiva", "Valor Neto\nEsperado"],
            y=[
                financials["gross_exposure"],
                financials["preventive_budget"],
                financials["net_value"],
            ],
            marker=dict(
                color=["#DC1F26", "#F59E0B", "#059669"],
                line=dict(color=["#A01520", "#D97706", "#047857"], width=2),
                opacity=0.9
            ),
            text=[
                _format_cop(financials["gross_exposure"]),
                _format_cop(financials["preventive_budget"]),
                _format_cop(financials["net_value"]),
            ],
            textposition="outside",
            textfont=dict(size=12, color="#0F1E3C", family="Arial Black"),
            hovertemplate="<b>%{x}</b><br>Valor: %{customdata}<extra></extra>",
            customdata=[
                _format_cop(financials["gross_exposure"]),
                _format_cop(financials["preventive_budget"]),
                _format_cop(financials["net_value"]),
            ]
        )
    ])
    
    fig.update_layout(
        height=380,
        margin=dict(t=30, b=30, l=60, r=30),
        paper_bgcolor="#FAFAFA",
        plot_bgcolor="white",
        font=dict(family="Arial", color="#0F1E3C"),
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor="#E5E7EB",
            tickfont=dict(size=11, family="Arial"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.2)",
            gridwidth=0.8,
            showline=True,
            linewidth=1,
            linecolor="#E5E7EB",
            tickformat="$,.0f",
        ),
    )
    
    return fig


def render_financial_section(alerts_df, prediction):
    """Renderiza la sección de Impacto Financiero con diseño profesional premium"""
    
    financials = _estimate_financials(alerts_df, prediction)

    # ===== ENCABEZADO DE SECCIÓN =====
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="color: #0F1E3C; font-family: Arial; font-size: 28px; margin: 0; font-weight: bold;">
            Impacto Financiero del Tren
        </h2>
        <p style="color: #6B7280; font-family: Arial; font-size: 14px; margin-top: 8px; margin-bottom: 0;">
            Estimación de costo evitado y valor de actuar preventivamente
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ===== TARJETAS KPI CON DISEÑO MEJORADO =====
    c1, c2, c3 = st.columns(3, gap="medium")
    
    with c1:
        render_kpi_card(
            label="Exposición Económica",
            value=_format_cop(financials["gross_exposure"]),
            delta=f"{financials['high_events']} eventos altos y {financials['medium_events']} medios",
            caption="Estimación demo del costo bruto expuesto por continuidad operativa y mantenimiento reactivo.",
            tone="red",
        )
    
    with c2:
        roi_value = financials['roi']
        roi_text = f"✨ ROI potencial {roi_value:.1f}x" if roi_value > 0 else "✨ ROI potencial 0x"
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
            delta=f"💚 Ahorro potencial {_format_cop(financials['avoided_cost'])}",
            caption="Escenario de ahorro si se actúa sobre las señales tempranas y la proyección del riesgo.",
            tone="blue",
        )

    # ===== GRÁFICA FINANCIERA MEJORADA =====
    st.plotly_chart(
        _build_financial_chart(financials), 
        use_container_width=True,
        config={"displayModeBar": False}
    )
    
    # ===== INFORMACIÓN REFERENCIAL =====
    st.markdown("""
    <p style="color: #9CA3AF; font-size: 12px; font-family: Arial; margin-top: 12px; margin-bottom: 24px; font-style: italic;">
        📋 Modelo financiero referencial para demo. Sustituible por costos reales del cliente sin tocar la experiencia visual.
    </p>
    """, unsafe_allow_html=True)

    # ===== SECCIÓN: CAUSAS ACTUALES DEL RIESGO =====
    st.markdown("""
    <div style="margin-top: 32px; padding-top: 24px; border-top: 2px solid #E5E7EB;">
        <h3 style="color: #0F1E3C; font-family: Arial; font-size: 18px; margin: 0 0 16px 0; font-weight: bold;">
            Causas Actuales del Riesgo
        </h3>
        <p style="color: #6B7280; font-family: Arial; font-size: 14px; margin: 0;">
            Factores que están empujando el riesgo en la lectura actual.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Renderizar causas de riesgo
    _render_risk_causes()

    # ===== SECCIÓN: PLAN DE ACCIÓN RECOMENDADO =====
    st.markdown("""
    <div style="margin-top: 32px; padding-top: 24px; border-top: 2px solid #E5E7EB;">
        <h3 style="color: #0F1E3C; font-family: Arial; font-size: 18px; margin: 0 0 16px 0; font-weight: bold;">
            Plan de Acción Recomendado
        </h3>
        <p style="color: #6B7280; font-family: Arial; font-size: 14px; margin: 0;">
            Acciones operativas sugeridas según el estado del tren.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Renderizar plan de acción
    _render_action_plan(prediction)


def _render_risk_causes():
    """Renderiza las causas actuales del riesgo con tarjetas visuales"""
    
    causes = [
        {
            "icon": "",
            "title": "Mantenimiento Reactivo",
            "description": "Intervenciones no programadas aumentan riesgo de fallos en cascada",
            "color": "#DC1F26"
        },
        {
            "icon": "",
            "title": "Variabilidad de Sensores",
            "description": "Fluctuaciones anómalas en lecturas de correlación y presión",
            "color": "#F59E0B"
        },
        {
            "icon": "",
            "title": "Ventanas de Riesgo",
            "description": "Periodos de operación con carga elevada sin intervención preventiva",
            "color": "#F97316"
        }
    ]
    
    cols = st.columns(3, gap="medium")
    for idx, cause in enumerate(causes):
        with cols[idx]:
            st.markdown(f"""
            <div style="
                background: white;
                border: 2px solid {cause['color']};
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 12px;
                transition: all 0.3s ease;
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">{cause['icon']}</div>
                <h4 style="color: {cause['color']}; font-family: Arial; font-size: 14px; font-weight: bold; margin: 0 0 8px 0;">
                    {cause['title']}
                </h4>
                <p style="color: #6B7280; font-family: Arial; font-size: 13px; margin: 0; line-height: 1.5;">
                    {cause['description']}
                </p>
            </div>
            """, unsafe_allow_html=True)


def _render_action_plan(prediction):
    """Renderiza el plan de acción recomendado"""
    
    # Determinar estado del protocolo
    current_level = prediction.get("projected_level", "BAJO")
    if current_level == "ALTO":
        protocol_status = "PROTOCOLO CRÍTICO: INTERVENCIÓN INMEDIATA"
        protocol_color = "#DC1F26"
        status_icon = ""
        actions = [
            ("Parar equipo de compresión", "Revisar manómetros y presión de aire"),
            ("Inspeccionar motor", "Revisar corriente, temperatura y aislamiento"),
            ("Limpiar filtros", "Cambiar si es necesario; verificar flujo"),
        ]
    elif current_level == "MEDIO":
        protocol_status = "PROTOCOLO ACTIVO: MONITOREO INTENSIVO"
        protocol_color = "#F59E0B"
        status_icon = ""
        actions = [
            ("Incrementar frecuencia de monitoreo", "Revisar cada 2 horas en lugar de cada 4"),
            ("Revisar presión de aire", "Mantener dentro de rangos óptimos"),
            ("Lubricación preventiva", "Aplicar según calendario acelelerado"),
        ]
    else:
        protocol_status = "PROTOCOLO ACTIVO: OPERACIÓN NORMAL"
        protocol_color = "#059669"
        status_icon = "🟢"
        actions = [
            ("Mantener monitoreo en panel", "Consolidar tendencia para análisis de rutina"),
            ("Registrar lecturas", "Documentar para la siguiente inspección programada"),
            ("Validar umbrales", "Asegurar que sensores estén dentro de rangos normales"),
        ]
    
    # Mostrar estado del protocolo
    st.markdown(f"""
    <div style="
        background: {protocol_color}20;
        border-left: 5px solid {protocol_color};
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 24px;
    ">
        <div style="font-size: 18px; color: {protocol_color}; font-weight: bold; margin-bottom: 4px;">
            {status_icon} {protocol_status}
        </div>
        <p style="color: #6B7280; font-family: Arial; font-size: 13px; margin: 0; margin-top: 8px;">
            Estado actual del protocolo operativo según proyección de riesgo.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar acciones
    st.markdown("<h4 style='color: #0F1E3C; font-family: Arial; font-size: 14px; margin: 0 0 16px 0; font-weight: bold;'>Acciones Prioritarias:</h4>", unsafe_allow_html=True)
    
    cols = st.columns(3, gap="medium")
    for idx, (action, detail) in enumerate(actions):
        with cols[idx % 3]:
            st.markdown(f"""
            <div style="
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 14px;
                margin-bottom: 8px;
            ">
                <div style="background: #F3F4F6; border-radius: 6px; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: {protocol_color}; margin-bottom: 8px;">
                    {idx + 1}
                </div>
                <h5 style="color: #0F1E3C; font-family: Arial; font-size: 13px; margin: 0 0 6px 0; font-weight: bold;">
                    {action}
                </h5>
                <p style="color: #9CA3AF; font-family: Arial; font-size: 12px; margin: 0; line-height: 1.4;">
                    {detail}
                </p>
            </div>
            """, unsafe_allow_html=True)
