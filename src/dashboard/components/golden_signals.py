"""
Placeholder module.
Este archivo se completará en el desarrollo del dashboard.
"""

import plotly.graph_objects as go
import streamlit as st

from src.dashboard.theme import PALETTE


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


def _range_status(value, cfg):
    if not cfg:
        return "BAJO"
    crit_low = cfg.get("crit_low")
    crit_high = cfg.get("crit_high")
    warn_low = cfg.get("warn_low")
    warn_high = cfg.get("warn_high")
    if crit_low is not None and value < float(crit_low):
        return "ALTO"
    if crit_high is not None and value > float(crit_high):
        return "ALTO"
    if warn_low is not None and value < float(warn_low):
        return "MEDIO"
    if warn_high is not None and value > float(warn_high):
        return "MEDIO"
    return "BAJO"


def _signal_palette(level):
    if level == "ALTO":
        return {"line": PALETTE["alert_red"], "fill": "rgba(211, 47, 47, 0.12)"}
    if level == "MEDIO":
        return {"line": "#D5B700", "fill": "rgba(255, 230, 0, 0.18)"}
    return {"line": PALETTE["steel_azure"], "fill": "rgba(35, 75, 141, 0.10)"}


def _sparkline(series, line_color, fill_color):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=series.index,
            y=series.values,
            mode="lines",
            line=dict(color=line_color, width=2.3),
            fill="tozeroy",
            fillcolor=fill_color,
            hovertemplate="%{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=132,
        margin=dict(t=6, b=6, l=6, r=6),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(35, 75, 141, 0.10)")
    return fig


def _ensure_styles():
    st.markdown(
        """
        <style>
        .jj-signal-card {
            background: #FFFFFF;
            border-radius: 22px;
            padding: 0.9rem 0.9rem 0.7rem 0.9rem;
            border: 1px solid rgba(35, 75, 141, 0.10);
            box-shadow: 0 20px 34px rgba(15, 30, 60, 0.08);
        }
        .jj-signal-topline {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            color: #60708D;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .jj-signal-title {
            font-size: 1rem;
            color: #0F1E3C;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }
        .jj-signal-value {
            font-size: 1.65rem;
            line-height: 1.02;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }
        .jj-signal-caption {
            font-size: 0.84rem;
            line-height: 1.42;
            color: #55617D;
            min-height: 48px;
        }
        .jj-signal-status {
            display: inline-block;
            padding: 0.22rem 0.56rem;
            border-radius: 999px;
            font-size: 0.73rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            margin-top: 0.42rem;
            margin-bottom: 0.42rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _status_chip(level):
    if level == "ALTO":
        return ("#FFF1F1", "#A61E2E")
    if level == "MEDIO":
        return ("#FFFCE0", "#8D7300")
    return ("#EEF4FF", "#234B8D")


def _render_signal_card(title, topline, value, caption, level, fig):
    chip_bg, chip_fg = _status_chip(level)
    st.markdown(
        f"""
        <div class="jj-signal-card">
            <div class="jj-signal-topline">{topline}</div>
            <div class="jj-signal-title">{title}</div>
            <div class="jj-signal-value" style="color:{chip_fg};">{value}</div>
            <div class="jj-signal-caption">{caption}</div>
            <div class="jj-signal-status" style="background:{chip_bg}; color:{chip_fg};">{level}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"golden-{title}")


def render_golden_signals(df, thresholds):
    _ensure_styles()
    if df is None or df.empty:
        st.info("No hay datos para construir senales doradas.")
        return

    recent = df.tail(180).copy()
    sensors = thresholds.get("sensors", {}) if thresholds else {}

    tp3_level = _range_status(
        _safe_float(recent["TP3_mean"].iloc[-1], default=0.0),
        sensors.get("TP3_mean", {}),
    )
    motor_level = _range_status(
        _safe_float(recent["Motor_Current_mean"].iloc[-1], default=0.0),
        sensors.get("Motor_Current_mean", {}),
    )
    dv_level = _range_status(
        _safe_float(recent["DV_pressure_mean"].iloc[-1], default=0.0),
        sensors.get("DV_pressure_mean", {}),
    )
    oil_level = _range_status(
        _safe_float(recent["Oil_Temperature_mean"].iloc[-1], default=0.0),
        sensors.get("Oil_Temperature_mean", {}),
    )

    mpg_active = float((recent["MPG_last"] > 0.5).astype(float).mean() * 100.0)
    tower_switches = int(recent["TOWERS_last"].diff().abs().fillna(0).sum())
    pneu_balance = _safe_float(recent["TP3_mean"].iloc[-1]) - _safe_float(recent["H1_mean"].iloc[-1])

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        palette = _signal_palette(tp3_level)
        fig = _sparkline(recent["TP3_mean"], palette["line"], palette["fill"])
        _render_signal_card(
            title="Disponibilidad neumatica",
            topline="Golden Signal 01",
            value=f"{recent['TP3_mean'].iloc[-1]:.2f} bar",
            caption=f"Balance TP3-H1: {pneu_balance:+.2f} bar. Resume la capacidad de sostener presion de servicio.",
            level=tp3_level,
            fig=fig,
        )

    with col2:
        palette = _signal_palette(motor_level)
        fig = _sparkline(recent["Motor_Current_mean"], palette["line"], palette["fill"])
        _render_signal_card(
            title="Carga del compresor",
            topline="Golden Signal 02",
            value=f"{recent['Motor_Current_mean'].iloc[-1]:.2f} A",
            caption=f"MPG activo {mpg_active:.0f}% del tiempo reciente. Mide cuanto esfuerzo esta absorbiendo el sistema.",
            level=motor_level,
            fig=fig,
        )

    with col3:
        palette = _signal_palette(dv_level)
        fig = _sparkline(recent["DV_pressure_mean"], palette["line"], palette["fill"])
        _render_signal_card(
            title="Descarga y secado",
            topline="Golden Signal 03",
            value=f"{recent['DV_pressure_mean'].iloc[-1]:.3f}",
            caption=f"Conmutaciones de torres en la ventana reciente: {tower_switches}. Detecta estabilidad de descarga y secado.",
            level=dv_level,
            fig=fig,
        )

    with col4:
        palette = _signal_palette(oil_level)
        fig = _sparkline(recent["Oil_Temperature_mean"], palette["line"], palette["fill"])
        _render_signal_card(
            title="Condicion termica",
            topline="Golden Signal 04",
            value=f"{recent['Oil_Temperature_mean'].iloc[-1]:.1f} C",
            caption="Condensa la carga termica del aceite y su deriva reciente para anticipar desgaste.",
            level=oil_level,
            fig=fig,
        )
