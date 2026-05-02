"""Componente de señales doradas con estilo visual por tarjeta."""

import plotly.graph_objects as go
import streamlit as st

from src.dashboard.theme import PALETTE


SIGNAL_THEMES = {
    1: {
        "bg_top": "#F2FAF4",
        "bg_bottom": "#EAF6EE",
        "border": "#D4EADB",
        "accent": "#3D9B67",
        "title": "#1B2F57",
        "value": "#102A60",
        "caption": "#4F6179",
        "line": "#3B5EA8",
        "fill": "rgba(59, 94, 168, 0.08)",
        "chip_bg": "#DFF2E6",
        "chip_fg": "#2E8E5B",
    },
    2: {
        "bg_top": "#FFF9EE",
        "bg_bottom": "#FDF4E3",
        "border": "#F0E2C6",
        "accent": "#C98A17",
        "title": "#1B2F57",
        "value": "#102A60",
        "caption": "#4F6179",
        "line": "#3E5EA7",
        "fill": "rgba(62, 94, 167, 0.08)",
        "chip_bg": "#FCEBCF",
        "chip_fg": "#B8790E",
    },
    3: {
        "bg_top": "#F8F2FC",
        "bg_bottom": "#F1E9F8",
        "border": "#E7D9F4",
        "accent": "#9B5ADC",
        "title": "#1B2F57",
        "value": "#102A60",
        "caption": "#4F6179",
        "line": "#3C5EA8",
        "fill": "rgba(60, 94, 168, 0.08)",
        "chip_bg": "#E9DDF8",
        "chip_fg": "#8548C6",
    },
    4: {
        "bg_top": "#F2F6FF",
        "bg_bottom": "#EAF1FF",
        "border": "#DCE7FE",
        "accent": "#4F78D6",
        "title": "#1B2F57",
        "value": "#102A60",
        "caption": "#4F6179",
        "line": "#3C5EA8",
        "fill": "rgba(60, 94, 168, 0.08)",
        "chip_bg": "#DCE8FF",
        "chip_fg": "#3F67C2",
    },
}


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


def _theme(signal_id: int):
    return SIGNAL_THEMES.get(signal_id, SIGNAL_THEMES[1])


def _sparkline(series, line_color, fill_color, bg_color):
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
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(35, 75, 141, 0.08)")
    return fig


def _ensure_styles():
    st.markdown(
        """
        <style>
        .jj-signal-card {
            border-radius: 24px;
            padding: 0.95rem 0.95rem 0.78rem 0.95rem;
            border: 1px solid rgba(35, 75, 141, 0.14);
            box-shadow: 0 14px 30px rgba(16, 31, 56, 0.08);
        }
        .jj-signal-topline {
            font-size: 0.71rem;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            font-weight: 760;
            margin-bottom: 0.35rem;
        }
        .jj-signal-title {
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.38rem;
        }
        .jj-signal-value {
            font-size: 1.8rem;
            line-height: 1.02;
            font-weight: 820;
            margin-bottom: 0.24rem;
        }
        .jj-signal-caption {
            font-size: 0.79rem;
            line-height: 1.42;
            min-height: 48px;
        }
        .jj-signal-status {
            display: inline-block;
            padding: 0.22rem 0.56rem;
            border-radius: 999px;
            font-size: 0.69rem;
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


def _render_signal_card(title, topline, value, caption, level, fig, signal_id: int):
    theme = _theme(signal_id)
    if level == "BAJO":
        chip_bg, chip_fg = theme["chip_bg"], theme["chip_fg"]
    else:
        chip_bg, chip_fg = _status_chip(level)

    st.markdown(
        f"""
        <div class="jj-signal-card" style="background: linear-gradient(180deg, {theme['bg_top']} 0%, {theme['bg_bottom']} 100%); border-color: {theme['border']};">
            <div class="jj-signal-topline" style="color:{theme['accent']};">{topline}</div>
            <div class="jj-signal-title" style="color:{theme['title']};">{title}</div>
            <div class="jj-signal-value" style="color:{theme['value']};">{value}</div>
            <div class="jj-signal-caption" style="color:{theme['caption']};">{caption}</div>
            <div class="jj-signal-status" style="background:{chip_bg}; color:{chip_fg};">{level}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"golden-{title}")


def render_golden_signals(df, thresholds):
    _ensure_styles()
    if df is None or df.empty:
        st.info("No hay datos para construir señales doradas.")
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
        theme = _theme(1)
        palette = _signal_palette(tp3_level)
        line_color = theme["line"] if tp3_level == "BAJO" else palette["line"]
        fill_color = theme["fill"] if tp3_level == "BAJO" else palette["fill"]
        fig = _sparkline(recent["TP3_mean"], line_color, fill_color, theme["bg_bottom"])
        _render_signal_card(
            title="Disponibilidad neumática",
            topline="Golden Signal 01",
            value=f"{recent['TP3_mean'].iloc[-1]:.2f} bar",
            caption=f"Balance TP3-H1: {pneu_balance:+.2f} bar. Resume la capacidad de sostener presión de servicio.",
            level=tp3_level,
            fig=fig,
            signal_id=1,
        )

    with col2:
        theme = _theme(2)
        palette = _signal_palette(motor_level)
        line_color = theme["line"] if motor_level == "BAJO" else palette["line"]
        fill_color = theme["fill"] if motor_level == "BAJO" else palette["fill"]
        fig = _sparkline(recent["Motor_Current_mean"], line_color, fill_color, theme["bg_bottom"])
        _render_signal_card(
            title="Carga del compresor",
            topline="Golden Signal 02",
            value=f"{recent['Motor_Current_mean'].iloc[-1]:.2f} A",
            caption=f"MPG activo {mpg_active:.0f}% del tiempo reciente. Mide cuánto esfuerzo está absorbiendo el sistema.",
            level=motor_level,
            fig=fig,
            signal_id=2,
        )

    with col3:
        theme = _theme(3)
        palette = _signal_palette(dv_level)
        line_color = theme["line"] if dv_level == "BAJO" else palette["line"]
        fill_color = theme["fill"] if dv_level == "BAJO" else palette["fill"]
        fig = _sparkline(recent["DV_pressure_mean"], line_color, fill_color, theme["bg_bottom"])
        _render_signal_card(
            title="Descarga y secado",
            topline="Golden Signal 03",
            value=f"{recent['DV_pressure_mean'].iloc[-1]:.3f}",
            caption=f"Conmutaciones de torres en la ventana reciente: {tower_switches}. Detecta estabilidad de descarga y secado.",
            level=dv_level,
            fig=fig,
            signal_id=3,
        )

    with col4:
        theme = _theme(4)
        palette = _signal_palette(oil_level)
        line_color = theme["line"] if oil_level == "BAJO" else palette["line"]
        fill_color = theme["fill"] if oil_level == "BAJO" else palette["fill"]
        fig = _sparkline(recent["Oil_Temperature_mean"], line_color, fill_color, theme["bg_bottom"])
        _render_signal_card(
            title="Condición térmica",
            topline="Golden Signal 04",
            value=f"{recent['Oil_Temperature_mean'].iloc[-1]:.1f} C",
            caption="Condensa la carga térmica del aceite y su deriva reciente para anticipar desgaste.",
            level=oil_level,
            fig=fig,
            signal_id=4,
        )
