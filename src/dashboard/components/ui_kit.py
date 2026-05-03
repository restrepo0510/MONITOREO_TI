from __future__ import annotations

import html
import re
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.icons import icon_chip, icon_svg
from src.dashboard.components.styles import inject_global_styles


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return text or "item"


def _fmt_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _state_badge(level: str) -> str:
    normalized = str(level or "BAJO").upper()
    if normalized == "ALTO":
        return '<span class="ds-badge ds-badge-high">ALTO</span>'
    if normalized == "MEDIO":
        return '<span class="ds-badge ds-badge-medium">MEDIO</span>'
    return '<span class="ds-badge ds-badge-low">BAJO</span>'


def _driver_icon(name: str) -> str:
    raw = str(name or "").lower()
    if raw in {"sin condiciones", "sin condición", "sin condicion"}:
        return icon_chip("bell", "#3B82F6")
    if "risk_score_operational" in raw:
        return icon_chip("activity", "#EF4444")
    if "tp3" in raw or "h1" in raw or "dv_pressure" in raw:
        return icon_chip("gauge", "#F59E0B")
    if "motor_current" in raw:
        return icon_chip("zap", "#22C55E")
    if "relacion_recuperacion_lenta" in raw:
        return icon_chip("refresh-cw", "#F97316")
    if "oil_temperature" in raw:
        return icon_chip("droplet", "#A855F7")
    return icon_chip("bell", "#3B82F6")


def section_title(title: str, subtitle: str | None = None, extra_class: str | None = None) -> None:
    inject_global_styles()
    safe_title = html.escape(str(title or ""))
    safe_subtitle = html.escape(str(subtitle or "")) if subtitle else ""
    extra = str(extra_class or "").strip()
    class_name = f"ds-section-head {html.escape(extra)}".strip() if extra else "ds-section-head"
    st.markdown(
        f"""
        <div class="{class_name}">
            <h3 class="ds-section-title">{safe_title}</h3>
            {f'<div class="ds-section-subtitle">{safe_subtitle}</div>' if safe_subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(
    title: str,
    value: Any,
    delta: str | None = None,
    icon: str | None = None,
    color: str | None = None,
    metadata: str | None = None,
) -> None:
    inject_global_styles()
    tone = color or "#234B8D"
    safe_title = html.escape(str(title or ""))
    safe_value = html.escape(_fmt_value(value))
    safe_delta = html.escape(str(delta or "")) if delta else ""
    safe_metadata = html.escape(str(metadata or "")) if metadata else ""
    safe_icon = icon_chip(icon or "bar-chart", tone)
    meta_block = ""
    if safe_metadata:
        meta_block = f'<div class="ds-kpi-meta">{safe_metadata}</div>'
    elif safe_delta:
        meta_block = '<div class="ds-kpi-meta">&nbsp;</div>'

    st.markdown(
        f"""
        <div class="ds-card ds-kpi-card">
            <div class="ds-kpi-title">{safe_title}</div>
            <div class="ds-kpi-main-row">
                {safe_icon}
                <div class="ds-kpi-value">{safe_value}</div>
            </div>
            {meta_block}
            {f'<div class="ds-kpi-delta">{safe_delta}</div>' if safe_delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_card(label: str, value: str, state: str, metadata: str | None = None) -> None:
    inject_global_styles()
    normalized = str(state or "BAJO").upper()
    state_class = "ds-status-value-low"
    icon_name = "shield-check"
    icon_color = "#37B26C"
    if normalized == "MEDIO":
        state_class = "ds-status-value-medium"
        icon_name = "alert-circle"
        icon_color = "#f39c12"
    elif normalized == "ALTO":
        state_class = "ds-status-value-high"
        icon_name = "alert-circle"
        icon_color = "#e74c3c"

    safe_label = html.escape(str(label or ""))
    raw_value = str(value or "").strip()
    safe_value = html.escape(raw_value if raw_value else f"Riesgo {normalized}")
    safe_meta = html.escape(str(metadata or "")) if metadata else "&nbsp;"

    st.markdown(
        f"""
        <div class="ds-card ds-status-card">
            <div class="ds-status-main-row">
                {icon_chip(icon_name, icon_color, size=80, chip_size=56)}
                <div class="ds-status-text-block">
                    <div class="ds-status-inline">
                        <span class="ds-status-inline-text ds-status-title">{safe_label}:</span>
                        <span class="ds-status-inline-text ds-status-value {state_class}">{safe_value}</span>
                    </div>
                    <div class="ds-status-secondary">{safe_meta}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sensor_card(name: str, value: Any, metadata: str, fig: go.Figure, color: str) -> None:
    inject_global_styles()
    key = f"ds-sensor-card-{_slug(name)}"
    with st.container(key=key):
        st.markdown(
            f"""
            <div class="ds-kpi-main-row">
                {icon_chip("gauge", color, size=19, chip_size=41)}
                <div class="ds-status-text-block">
                    <div class="ds-chart-title">{html.escape(str(name or ''))}</div>
                    <div class="ds-kpi-value">{html.escape(_fmt_value(value))}</div>
                </div>
            </div>
            <div class="ds-chart-subtitle">{html.escape(str(metadata or ''))}</div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig, use_container_width=True)


def golden_card(title: str, value: Any, description: str, fig: go.Figure, color: str) -> None:
    inject_global_styles()
    key = f"ds-golden-card-{_slug(title)}"
    with st.container(key=key):
        st.markdown(
            f"""
            <div class="ds-kpi-main-row">
                {icon_chip("activity", color, size=19, chip_size=41)}
                <div class="ds-status-text-block">
                    <div class="ds-chart-title">{html.escape(str(title or ''))}</div>
                    <div class="ds-kpi-value">{html.escape(_fmt_value(value))}</div>
                </div>
            </div>
            <div class="ds-chart-subtitle">{html.escape(str(description or ''))}</div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig, use_container_width=True)


def finance_card(title: str, value: Any, description: str, type: str) -> None:
    inject_global_styles()
    tone = str(type or "").strip().lower()
    css_tone = "ds-finance-preventive"
    icon = icon_chip("wrench", "#f39c12")
    if tone in {"reactive", "red", "high"}:
        css_tone = "ds-finance-reactive"
        icon = icon_chip("alert-circle", "#e74c3c")
    elif tone in {"savings", "green", "low"}:
        css_tone = "ds-finance-savings"
        icon = icon_chip("trending-up", "#2ecc71")

    st.markdown(
        f"""
        <div class="ds-card ds-finance-card {css_tone}">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:0.7rem;">
                <div class="ds-finance-title">{html.escape(str(title or ''))}</div>
                {icon}
            </div>
            <div class="ds-finance-value">{html.escape(_fmt_value(value))}</div>
            <div class="ds-finance-desc">{html.escape(str(description or ''))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_card(title: str, fig: go.Figure) -> None:
    inject_global_styles()
    key = f"ds-chart-card-{_slug(title)}"
    with st.container(key=key):
        st.markdown(f'<div class="ds-chart-title">{html.escape(str(title or ""))}</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)


def _table_cell_html(column: str, value: Any, row: pd.Series, max_freq: float) -> str:
    col = str(column or "")
    if col.lower() == "frecuencia":
        try:
            freq = float(value)
        except Exception:
            freq = 0.0
        pct = 0.0 if max_freq <= 0 else max(0.0, min(100.0, (freq / max_freq) * 100.0))
        bar = (
            f'<div class="ds-progress-cell"><div class="ds-progress"><div class="ds-progress-fill" style="width:{pct:.2f}%"></div></div>'
            f'<span>{int(freq)}</span></div>'
        )
        return bar

    if col.lower() == "driver":
        return f'<div style="display:flex;align-items:center;gap:0.72rem;">{_driver_icon(str(value))}<span>{html.escape(str(value))}</span></div>'

    if col.lower() == "estado":
        return _state_badge(str(value))

    if col.lower() == "accion":
        return f'<span class="ds-pill-action">{html.escape(str(value))}</span>'

    if col.lower() == "riesgo":
        try:
            risk = float(value)
            return f"{risk:.4f}"
        except Exception:
            return html.escape(str(value))

    return html.escape(str(value))


def table_card(title: str, dataframe: pd.DataFrame) -> None:
    inject_global_styles()
    safe_title = html.escape(str(title or ""))
    if dataframe is None or dataframe.empty:
        st.markdown(
            f"""
            <div class="ds-action-card">
                <div class="ds-action-title">{safe_title}</div>
                <div class="ds-action-content">Sin datos disponibles.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    table_df = dataframe.copy()
    max_freq = 0.0
    if "Frecuencia" in table_df.columns:
        try:
            max_freq = float(pd.to_numeric(table_df["Frecuencia"], errors="coerce").fillna(0).max())
        except Exception:
            max_freq = 0.0

    headers = "".join([f"<th>{html.escape(str(c))}</th>" for c in table_df.columns])
    rows = []
    for _, row in table_df.iterrows():
        cells = []
        for column in table_df.columns:
            cells.append(f"<td>{_table_cell_html(str(column), row[column], row, max_freq)}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")

    st.markdown(
        f"""
        <div class="ds-chart-title" style="margin-bottom:0.55rem;">{safe_title}</div>
        <div class="ds-table-wrap">
            <table class="ds-table">
                <thead><tr>{headers}</tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def action_card(title: str, content: str) -> None:
    inject_global_styles()
    st.markdown(
        f"""
        <div class="ds-action-card">
            <div class="ds-action-title">{html.escape(str(title or ''))}</div>
            <div class="ds-action-content">{html.escape(str(content or ''))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def event_card(event_data: dict[str, Any]) -> None:
    inject_global_styles()
    name = html.escape(str(event_data.get("title", "Evento")))
    content = html.escape(str(event_data.get("content", "")))
    st.markdown(
        f"""
        <div class="ds-event-card">
            <div class="ds-event-title">{name}</div>
            <div class="ds-event-content">{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, updated_text: str = "") -> None:
    inject_global_styles()
    cols = st.columns([5, 1.3], gap="large")
    with cols[0]:
        st.markdown(
            f"""
            <div class="ds-page-header">
                <span class="ds-page-dot"></span>
                <h1 class="ds-page-title">{html.escape(str(title or ''))}</h1>
            </div>
            <p class="ds-page-subtitle">{html.escape(str(subtitle or ''))}</p>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        txt = html.escape(str(updated_text or "-"))
        clock = icon_svg("clock", size=16, stroke="#7b879b", stroke_width=2)
        st.markdown(
            f'<div class="ds-clock-chip">{clock}<span>{txt}</span></div>',
            unsafe_allow_html=True,
        )
