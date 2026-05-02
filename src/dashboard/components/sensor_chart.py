import html

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.config import SENSOR_THRESHOLDS_PATH
from src.dashboard.theme import PALETTE, risk_palette
from src.dashboard.utils.sensor_thresholds import load_sensor_thresholds


SENSOR_DESCRIPTIONS = {
    "TP3_mean": "Presion en una parte clave del sistema neumatico (salida del compresor o linea principal).",
    "H1_mean": "Presion en un punto intermedio del sistema neumatico.",
    "DV_pressure_mean": "Presion en la valvula de descarga o control.",
    "Motor_Current_mean": "Corriente del motor: cuanta energia esta consumiendo el motor del compresor.",
    "MPG_last": "MPG corresponde a una senal digital que representa el estado operativo de un componente del sistema de compresion, indicando si se encuentra activo o inactivo.",
    "Oil_Temperature_mean": "Temperatura del aceite del sistema de compresion.",
    "TOWERS_last": "TOWERS corresponde a una senal digital que indica el estado de operacion de las torres del sistema de secado de aire del compresor.",
}


def _inject_sensor_chart_css():
    st.markdown(
        """
        <style>
        .sensor-card {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAF7 100%);
            border: 1px solid rgba(8, 42, 112, 0.18);
            border-radius: 26px;
            padding: 1rem 1rem 0.86rem 1rem;
            margin-bottom: 0.36rem;
            box-shadow: 0 14px 30px rgba(16, 31, 56, 0.08);
            position: relative;
        }
        .sensor-card::before {
            content: "";
            position: absolute;
            top: 0.85rem;
            left: 0.85rem;
            width: 7px;
            height: 48px;
            border-radius: 999px;
            background: var(--sensor-accent, #082A70);
            opacity: 0.95;
        }
        .sensor-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.8rem;
            padding-left: 1rem;
        }
        .sensor-title {
            font-size: 0.92rem;
            font-weight: 750;
            color: #082A70;
            margin-bottom: 0.26rem;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }
        .sensor-title-wrap {
            display: inline-block;
            position: relative;
            cursor: help;
        }
        .sensor-tooltip {
            visibility: hidden;
            opacity: 0;
            width: max-content;
            max-width: min(420px, 90vw);
            background: #082A70;
            color: #FFFFFF;
            text-align: left;
            border-radius: 10px;
            padding: 10px 12px;
            position: absolute;
            z-index: 999;
            top: 120%;
            left: 0;
            line-height: 1.35;
            font-size: 0.82rem;
            text-transform: lowercase;
            white-space: normal;
            overflow-wrap: anywhere;
            word-break: break-word;
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.22);
            transition: opacity 0.18s ease;
        }
        .sensor-title-wrap:hover .sensor-tooltip {
            visibility: visible;
            opacity: 1;
        }
        .sensor-status-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            padding: 0.26rem 0.65rem;
            font-size: 0.67rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .sensor-status-alto {
            background: #FFF0F2;
            color: #9E1E33;
            border-color: rgba(158, 30, 51, 0.24);
        }
        .sensor-status-medio {
            background: #FFFCE0;
            color: #7E6900;
            border-color: rgba(126, 105, 0, 0.26);
        }
        .sensor-status-bajo {
            background: #EDF3FF;
            color: #082A70;
            border-color: rgba(8, 42, 112, 0.26);
        }
        .sensor-status-missing {
            background: #F2F4F7;
            color: #5F6B7A;
            border-color: rgba(95, 107, 122, 0.24);
        }
        .sensor-value {
            padding-left: 1rem;
            font-size: 2rem;
            font-weight: 800;
            color: #121212;
            line-height: 1.1;
            margin-bottom: 0.18rem;
        }
        .sensor-meta {
            padding-left: 1rem;
            font-size: 0.76rem;
            color: #5F6B7A;
            margin-bottom: 0.2rem;
            letter-spacing: 0.01em;
        }
        .sensor-meta-secondary {
            padding-left: 1rem;
            font-size: 0.73rem;
            color: #5F6B7A;
            line-height: 1.25;
        }
        [class*="st-key-sensor-panel-"] {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAF7 100%);
            border-radius: 28px;
            padding: 0.62rem 0.62rem 0.55rem 0.62rem;
            border: 1px solid rgba(8, 42, 112, 0.20);
            margin-bottom: 1.25rem;
            overflow: visible;
            box-shadow: 0 15px 32px rgba(16, 31, 56, 0.08);
        }
        [class*="st-key-sensor-panel-"] div[data-testid="stPlotlyChart"] {
            border-top: 1px solid rgba(8, 42, 112, 0.18);
            border-radius: 18px;
            padding-top: 0.55rem;
            margin-top: 0.25rem;
        }
        [class*="st-key-sensor-panel-"] div[data-testid="stPlotlyChart"] > div {
            border: none;
            border-radius: 16px;
            overflow: hidden;
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_sensor_chart_styles():
    """
    Carga estilos de sensores antes de renderizar la grilla.
    Esto evita desfase vertical en la primera tarjeta.
    """
    _inject_sensor_chart_css()


def _load_thresholds_once():
    """
    Carga umbrales fijos por sensor una sola vez por sesión de Streamlit.
    """
    key = "_sensor_thresholds_loaded"
    if key not in st.session_state:
        st.session_state[key] = load_sensor_thresholds(SENSOR_THRESHOLDS_PATH)
    return st.session_state[key]


def _sensor_threshold(thresholds, sensor, field, fallback):
    sensor_cfg = thresholds.get("sensors", {}).get(sensor, {})
    value = sensor_cfg.get(field, fallback)
    try:
        return float(value)
    except Exception:
        return float(fallback)


_LEVEL_PRIORITY = {"BAJO": 0, "MEDIO": 1, "ALTO": 2, "MISSING": -1}


def _promote_level(current, candidate):
    if _LEVEL_PRIORITY.get(candidate, -1) > _LEVEL_PRIORITY.get(current, -1):
        return candidate
    return current


def _range_level(value, warn_low=None, warn_high=None, crit_low=None, crit_high=None):
    if crit_low is not None and value < float(crit_low):
        return "ALTO"
    if crit_high is not None and value > float(crit_high):
        return "ALTO"
    if warn_low is not None and value < float(warn_low):
        return "MEDIO"
    if warn_high is not None and value > float(warn_high):
        return "MEDIO"
    return "BAJO"


def _sensor_alert_level(sensor, sensor_df, thresholds):
    if sensor not in sensor_df.columns or sensor_df.empty:
        return "MISSING"

    latest_val = float(sensor_df[sensor].iloc[-1])
    sensor_cfg = thresholds.get("sensors", {}).get(sensor, {})

    if sensor in ("TP3_mean", "H1_mean"):
        return _range_level(
            latest_val,
            warn_low=sensor_cfg.get("warn_low"),
            warn_high=sensor_cfg.get("warn_high"),
            crit_low=sensor_cfg.get("crit_low"),
            crit_high=sensor_cfg.get("crit_high"),
        )

    if sensor == "DV_pressure_mean":
        level = _range_level(
            latest_val,
            warn_low=sensor_cfg.get("warn_low"),
            warn_high=sensor_cfg.get("warn_high"),
            crit_low=sensor_cfg.get("crit_low"),
            crit_high=sensor_cfg.get("crit_high"),
        )
        spike_threshold = sensor_cfg.get("spike_threshold")
        if spike_threshold is not None:
            baseline = sensor_df[sensor].rolling(12, min_periods=1).median().iloc[-1]
            residual = abs(latest_val - float(baseline))
            if residual > float(spike_threshold) * 1.5:
                level = _promote_level(level, "ALTO")
            elif residual > float(spike_threshold):
                level = _promote_level(level, "MEDIO")
        return level

    if sensor == "Motor_Current_mean":
        warn_high = sensor_cfg.get("warn_high")
        crit_high = sensor_cfg.get("crit_high")
        if crit_high is not None and latest_val > float(crit_high):
            return "ALTO"
        if warn_high is not None and latest_val > float(warn_high):
            return "MEDIO"
        return "BAJO"

    if sensor == "Oil_Temperature_mean":
        return _range_level(
            latest_val,
            warn_low=sensor_cfg.get("warn_low"),
            warn_high=sensor_cfg.get("warn_high"),
            crit_low=sensor_cfg.get("crit_low"),
            crit_high=sensor_cfg.get("crit_high"),
        )

    # Senales digitales: estado binario no implica por si solo alerta.
    if sensor in ("MPG_last", "TOWERS_last"):
        return "BAJO"

    return "BAJO"


def _format_value(value):
    if abs(value) < 1:
        return f"{value:.3f}"
    if abs(value) < 100:
        return f"{value:.2f}"
    return f"{value:.1f}"


def _hex_to_rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _base_chart_layout(fig, show_legend=False):
    fig.update_layout(
        height=182,
        margin=dict(t=8, b=8, l=8, r=8),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=PALETTE["black"], size=11),
        showlegend=bool(show_legend),
    )
    fig.update_xaxes(
        showgrid=False,
        tickfont=dict(size=9, color="#4d5875"),
        tickformat="%H:%M",
        nticks=4,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(8, 42, 112, 0.12)",
        zeroline=False,
        tickfont=dict(size=9, color="#4d5875"),
    )


def _build_trend_figure(sensor_df, sensor, palette, min_expected):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sensor_df["timestamp"],
            y=sensor_df[sensor],
            mode="lines",
            line=dict(width=2.2, color=palette["bg"]),
            hovertemplate="%{x}<br>%{y:.3f}<extra></extra>",
            name="Serie",
        )
    )
    rolling = sensor_df[sensor].rolling(8, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=sensor_df["timestamp"],
            y=rolling,
            mode="lines",
            line=dict(width=1.8, color=PALETTE["light_blue"], dash="dot"),
            hovertemplate="%{x}<br>Tendencia: %{y:.3f}<extra></extra>",
            name="Tendencia",
        )
    )
    fig.add_hline(
        y=min_expected,
        line_dash="dash",
        line_color=PALETTE["yellow"],
    )
    _base_chart_layout(fig)
    return fig


def _build_dv_pressure_figure(sensor_df, sensor, palette, spike_threshold):
    series = sensor_df[sensor]
    baseline = series.rolling(12, min_periods=1).median()
    residual = (series - baseline).abs()
    spike_mask = residual >= spike_threshold

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sensor_df["timestamp"],
            y=series,
            mode="lines",
            line=dict(width=2.1, color=palette["bg"]),
            hovertemplate="%{x}<br>Presion: %{y:.4f}<extra></extra>",
            name="DV pressure",
        )
    )
    if spike_mask.any():
        fig.add_trace(
            go.Scatter(
                x=sensor_df.loc[spike_mask, "timestamp"],
                y=series[spike_mask],
                mode="markers",
                marker=dict(size=7, color=PALETTE["alert_red"], symbol="diamond"),
                hovertemplate="%{x}<br>Pico: %{y:.4f}<extra></extra>",
                name="Picos",
            )
        )
    _base_chart_layout(fig, show_legend=bool(spike_mask.any()))
    return fig, int(spike_mask.sum()), float(spike_mask.mean() * 100)


def _build_motor_current_figure(sensor_df, sensor, palette, on_threshold, warn_high, crit_high):
    series = sensor_df[sensor]
    recent = sensor_df.tail(20).copy()
    recent_state = recent[sensor] >= on_threshold
    colors = [palette["bg"] if state else PALETTE["light_blue"] for state in recent_state]

    full_state = (series >= on_threshold).astype(int)
    transitions = int(full_state.diff().abs().fillna(0).sum())
    avg_recent = float(series.tail(12).mean())
    peak = float(series.max())

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=recent["timestamp"],
            y=recent[sensor],
            marker_color=colors,
            hovertemplate="%{x}<br>Corriente: %{y:.4f}<extra></extra>",
            name="Actividad",
        )
    )
    fig.add_hline(y=avg_recent, line_dash="dot", line_color=PALETTE["steel_azure"])
    fig.add_hline(y=warn_high, line_dash="dot", line_color=PALETTE["yellow"])
    fig.add_hline(y=crit_high, line_dash="dash", line_color=PALETTE["alert_red"])
    _base_chart_layout(fig)
    return fig, transitions, avg_recent, peak


def _build_donut_figure(sensor_df, sensor, palette, on_threshold):
    state = (sensor_df[sensor] > on_threshold).astype(int)
    active = int(state.sum())
    inactive = int(len(state) - active)
    active_pct = float((active / max(len(state), 1)) * 100)

    change_mask = state.ne(state.shift(1))
    if not change_mask.empty:
        change_mask.iloc[0] = False
    last_change_str = "sin cambios"
    if change_mask.any():
        ts = sensor_df.loc[change_mask, "timestamp"].iloc[-1]
        last_change_str = ts.strftime("%d/%m %H:%M")

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Activo", "Inactivo"],
                values=[active, inactive],
                hole=0.72,
                marker=dict(
                    colors=[palette["bg"], _hex_to_rgba(PALETTE["light_blue"], 0.75)],
                    line=dict(color="white", width=1),
                ),
                textinfo="none",
                hovertemplate="%{label}: %{value}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        height=182,
        margin=dict(t=8, b=8, l=8, r=8),
        paper_bgcolor="white",
        showlegend=True,
        legend=dict(orientation="h", y=-0.11, x=0.12, font=dict(size=9)),
        annotations=[
            dict(
                text=f"{active_pct:.0f}%<br>activo",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=13, color=PALETTE["black"]),
            )
        ],
    )
    return fig, active_pct, last_change_str


def _build_oil_temperature_figure(sensor_df, sensor, palette, normal_low, normal_high, crit_low, crit_high):
    series = sensor_df[sensor]
    mean_val = float(series.mean())
    outlier_mask = (series < crit_low) | (series > crit_high)
    outlier_count = int(outlier_mask.sum())

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.35, 0.65],
        horizontal_spacing=0.10,
        specs=[[{"type": "box"}, {"type": "xy"}]],
    )
    fig.add_trace(
        go.Box(
            y=series,
            name="Distribucion",
            marker_color=PALETTE["steel_azure"],
            line=dict(color=PALETTE["steel_azure"]),
            fillcolor=_hex_to_rgba(PALETTE["light_blue"], 0.35),
            boxmean=True,
            hovertemplate="%{y:.3f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=sensor_df["timestamp"],
            y=series,
            mode="lines",
            line=dict(width=2.0, color=palette["bg"]),
            hovertemplate="%{x}<br>Temp: %{y:.3f}<extra></extra>",
            name="Evolucion",
        ),
        row=1,
        col=2,
    )
    if outlier_count > 0:
        fig.add_trace(
            go.Scatter(
                x=sensor_df.loc[outlier_mask, "timestamp"],
                y=series[outlier_mask],
                mode="markers",
                marker=dict(size=6, color=PALETTE["alert_red"]),
                hovertemplate="%{x}<br>Outlier: %{y:.3f}<extra></extra>",
                name="Outliers",
            ),
            row=1,
            col=2,
        )
    fig.add_hrect(
        y0=normal_low,
        y1=normal_high,
        fillcolor=_hex_to_rgba(PALETTE["light_blue"], 0.20),
        line_width=0,
        row=1,
        col=2,
    )
    fig.update_layout(
        height=182,
        margin=dict(t=8, b=8, l=8, r=8),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=PALETTE["black"], size=11),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(size=9, color="#4d5875"), row=1, col=2)
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(8, 42, 112, 0.12)",
        zeroline=False,
        tickfont=dict(size=9, color="#4d5875"),
        row=1,
        col=2,
    )
    fig.update_xaxes(showgrid=False, row=1, col=1)
    fig.update_yaxes(showgrid=False, row=1, col=1)
    return fig, mean_val, normal_low, normal_high, outlier_count


def _build_towers_figure(sensor_df, sensor, palette, on_threshold):
    series = sensor_df[sensor].tail(24).copy()
    state = (series > on_threshold).astype(int)
    colors = [palette["bg"] if value == 1 else PALETTE["light_blue"] for value in state]
    transitions = int(state.diff().abs().fillna(0).sum())
    active_pct = float(state.mean() * 100)
    inactive_pct = 100.0 - active_pct

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=sensor_df.tail(24)["timestamp"],
            y=state,
            marker_color=colors,
            hovertemplate="%{x}<br>Estado: %{y}<extra></extra>",
            name="Estado",
        )
    )
    _base_chart_layout(fig)
    fig.update_yaxes(
        range=[-0.1, 1.1],
        tickvals=[0, 1],
        ticktext=["Inactivo", "Activo"],
        showgrid=True,
        gridcolor="rgba(8, 42, 112, 0.12)",
    )
    return fig, transitions, active_pct, inactive_pct


def _build_missing_figure():
    fig = go.Figure()
    fig.update_layout(
        height=182,
        margin=dict(t=8, b=8, l=8, r=8),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text="Sin datos disponibles para este sensor",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=12, color="#606b85"),
            )
        ],
    )
    return fig


def _render_header(
    display_name,
    value_text,
    delta_text,
    sensor_key,
    risk_label,
    accent_color,
    extra_text="",
):
    description = SENSOR_DESCRIPTIONS.get(sensor_key, "")
    safe_title = html.escape(display_name)
    safe_description = html.escape(description)
    safe_extra = html.escape(extra_text)
    normalized_risk = str(risk_label).strip().upper()
    risk_css = {
        "ALTO": "sensor-status-alto",
        "MEDIO": "sensor-status-medio",
        "BAJO": "sensor-status-bajo",
    }.get(normalized_risk, "sensor-status-missing")

    if description:
        title_html = (
            f'<div class="sensor-title"><span class="sensor-title-wrap">{safe_title}'
            f'<span class="sensor-tooltip">{safe_description}</span></span></div>'
        )
    else:
        title_html = f'<div class="sensor-title">{safe_title}</div>'

    extra_html = ""
    if extra_text:
        extra_html = f'<div class="sensor-meta-secondary">{safe_extra}</div>'

    st.markdown(
        f"""
        <div class="sensor-card" style="--sensor-accent:{accent_color};">
            <div class="sensor-head">
                {title_html}
                <span class="sensor-status-badge {risk_css}">{normalized_risk}</span>
            </div>
            <div class="sensor-value">{value_text}</div>
            <div class="sensor-meta">Delta reciente: {delta_text}</div>
            {extra_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sensor_card(sensor, df):
    _inject_sensor_chart_css()
    thresholds = _load_thresholds_once()

    latest = df.iloc[-1]
    display_name = sensor.replace("_mean", "").replace("_last", "")

    with st.container(key=f"sensor-panel-{sensor}"):
        if sensor not in df.columns:
            _render_header(
                display_name=display_name,
                value_text="N/A",
                delta_text="N/A",
                sensor_key=sensor,
                risk_label="SIN DATOS",
                accent_color=risk_palette("MISSING")["bg"],
            )
            st.plotly_chart(_build_missing_figure(), use_container_width=True, key=f"sensor_{sensor}")
            return

        sensor_df = df.tail(64).copy()
        sensor_level = _sensor_alert_level(sensor, sensor_df, thresholds)
        palette = risk_palette(sensor_level)
        value = float(latest[sensor])
        prev_mean = float(sensor_df[sensor].iloc[:-1].tail(12).mean()) if len(sensor_df) > 1 else value
        delta = value - prev_mean
        delta_text = f"{delta:+.3f}"
        value_text = _format_value(value)
        extra_text = ""

        if sensor in ("TP3_mean", "H1_mean"):
            min_expected = _sensor_threshold(
                thresholds,
                sensor,
                "min_expected",
                float(sensor_df[sensor].quantile(0.10)),
            )
            fig = _build_trend_figure(sensor_df, sensor, palette, min_expected)
            extra_text = f"Umbral min (P10): {min_expected:.3f}"
        elif sensor == "DV_pressure_mean":
            spike_threshold = _sensor_threshold(
                thresholds,
                sensor,
                "spike_threshold",
                float((sensor_df[sensor] - sensor_df[sensor].rolling(12, min_periods=1).median()).abs().quantile(0.90)),
            )
            fig, peaks, activation_freq = _build_dv_pressure_figure(sensor_df, sensor, palette, spike_threshold)
            extra_text = f"Picos detectados: {peaks} | Frec. activacion: {activation_freq:.1f}%"
        elif sensor == "Motor_Current_mean":
            on_threshold = _sensor_threshold(
                thresholds,
                sensor,
                "on_threshold",
                float(sensor_df[sensor].quantile(0.60)),
            )
            warn_high = _sensor_threshold(
                thresholds,
                sensor,
                "warn_high",
                float(sensor_df[sensor].quantile(0.95)),
            )
            crit_high = _sensor_threshold(
                thresholds,
                sensor,
                "crit_high",
                float(sensor_df[sensor].quantile(0.99)),
            )
            fig, transitions, avg_recent, peak_max = _build_motor_current_figure(
                sensor_df, sensor, palette, on_threshold, warn_high, crit_high
            )
            extra_text = f"Cambios ON/OFF: {transitions} | Prom(12): {avg_recent:.4f} | Pico max: {peak_max:.4f}"
        elif sensor == "MPG_last":
            on_threshold = _sensor_threshold(thresholds, sensor, "on_threshold", 0.5)
            fig, active_pct, last_change = _build_donut_figure(sensor_df, sensor, palette, on_threshold)
            extra_text = f"% tiempo activo: {active_pct:.1f}% | Ultimo cambio: {last_change}"
        elif sensor == "Oil_Temperature_mean":
            normal_low = _sensor_threshold(
                thresholds,
                sensor,
                "normal_low",
                float(sensor_df[sensor].quantile(0.10)),
            )
            normal_high = _sensor_threshold(
                thresholds,
                sensor,
                "normal_high",
                float(sensor_df[sensor].quantile(0.90)),
            )
            crit_low = _sensor_threshold(
                thresholds,
                sensor,
                "crit_low",
                float(sensor_df[sensor].quantile(0.01)),
            )
            crit_high = _sensor_threshold(
                thresholds,
                sensor,
                "crit_high",
                float(sensor_df[sensor].quantile(0.99)),
            )
            fig, mean_val, p10, p90, outliers = _build_oil_temperature_figure(
                sensor_df, sensor, palette, normal_low, normal_high, crit_low, crit_high
            )
            extra_text = f"Media: {mean_val:.2f} | Rango normal: {p10:.2f}-{p90:.2f} | Outliers: {outliers}"
        elif sensor == "TOWERS_last":
            on_threshold = _sensor_threshold(thresholds, sensor, "on_threshold", 0.5)
            fig, transitions, active_pct, inactive_pct = _build_towers_figure(sensor_df, sensor, palette, on_threshold)
            extra_text = f"Frecuencia de cambio: {transitions} | Activo: {active_pct:.1f}% | Inactivo: {inactive_pct:.1f}%"
        else:
            min_expected = float(sensor_df[sensor].quantile(0.10))
            fig = _build_trend_figure(sensor_df, sensor, palette, min_expected)
            extra_text = f"Umbral min (P10): {min_expected:.3f}"

        _render_header(
            display_name=display_name,
            value_text=value_text,
            delta_text=delta_text,
            sensor_key=sensor,
            risk_label=sensor_level,
            accent_color=palette["bg"],
            extra_text=extra_text,
        )

        st.plotly_chart(fig, use_container_width=True, key=f"sensor_{sensor}")
    
