"""
Placeholder module.
Este archivo se completará en el desarrollo del dashboard.
"""

import pandas as pd
import streamlit as st

SENSOR_COLUMNS = [
    "TP3_mean",
    "H1_mean",
    "DV_pressure_mean",
    "Motor_Current_mean",
    "Oil_Temperature_mean",
    "MPG_last",
    "TOWERS_last",
]


def _pick_score_column(df: pd.DataFrame) -> str:
    if "risk_score_operational" in df.columns:
        return "risk_score_operational"
    return "risk_score"


def _sensor_key_from_reason(reason_text: str) -> list[str]:
    sensors: list[str] = []
    for chunk in str(reason_text).split("|"):
        part = chunk.strip()
        if ":" not in part:
            continue
        prefix = part.split(":", 1)[0].strip()
        if prefix in SENSOR_COLUMNS and prefix not in sensors:
            sensors.append(prefix)
    return sensors


def _format_sensor_name(sensor: str) -> str:
    return sensor.replace("_mean", "").replace("_last", "")


def _format_sensor_snapshot(row: pd.Series, sensors: list[str], max_items: int = 3) -> str:
    selected = sensors if sensors else [s for s in SENSOR_COLUMNS if s in row.index]
    selected = [s for s in selected if s in row.index][:max_items]
    if not selected:
        return "Sin sensores destacados."

    parts = []
    for sensor in selected:
        value = row.get(sensor)
        try:
            num = float(value)
            parts.append(f"{_format_sensor_name(sensor)}={num:.3f}")
        except Exception:
            parts.append(f"{_format_sensor_name(sensor)}={value}")
    return " | ".join(parts)


def build_alert_episodes(alerts_df: pd.DataFrame) -> pd.DataFrame:
    if alerts_df is None or alerts_df.empty:
        return pd.DataFrame()

    work = alerts_df.copy().sort_values("timestamp")
    work["is_alert"] = work["alert_level"].ne("BAJO")
    work = work[work["is_alert"]].copy()
    if work.empty:
        return pd.DataFrame()

    work["episode_break"] = (
        work["timestamp"].diff().dt.total_seconds().fillna(0).gt(120)
        | work["alert_level"].ne(work["alert_level"].shift(1))
    )
    work["episode_id"] = work["episode_break"].cumsum()

    score_col = _pick_score_column(work)
    episodes_rows = []
    for _, group in work.groupby("episode_id", dropna=False):
        group_sorted = group.sort_values("timestamp")
        peak_idx = group_sorted[score_col].astype(float).idxmax()
        peak_row = group_sorted.loc[peak_idx]
        reasons = str(peak_row.get("alert_reasons", "")).strip() or str(group_sorted["alert_reasons"].iloc[-1])
        active_sensors = _sensor_key_from_reason(reasons)
        event_time = pd.to_datetime(peak_row.get("sandbox_event_created_at"), errors="coerce")
        if pd.isna(event_time):
            event_time = pd.to_datetime(peak_row.get("timestamp"), errors="coerce")
        if pd.isna(event_time):
            event_time = group_sorted["timestamp"].max()

        event_note = str(peak_row.get("sandbox_event_note", "")).strip()
        if not event_note:
            event_note = f"Evento detectado por: {reasons.split('|')[0].strip()}"

        episodes_rows.append(
            {
                "start": group_sorted["timestamp"].min(),
                "end": group_sorted["timestamp"].max(),
                "peak_time": peak_row.get("timestamp"),
                "event_time": event_time,
                "level": "ALTO" if (group_sorted["alert_level"] == "ALTO").any() else "MEDIO",
                "max_score": float(group_sorted[score_col].astype(float).max()),
                "sources": ", ".join(sorted(set(group_sorted["alert_sources"].astype(str)))),
                "reasons": reasons,
                "windows": int(len(group_sorted)),
                "max_triggers": int(group_sorted["alert_trigger_count"].astype(float).max())
                if "alert_trigger_count" in group_sorted.columns
                else 0,
                "sensor_snapshot": _format_sensor_snapshot(peak_row, active_sensors, max_items=3),
                "event_note": event_note,
            }
        )

    episodes = pd.DataFrame(episodes_rows)
    episodes["duration_min"] = (
        (episodes["end"] - episodes["start"]).dt.total_seconds() / 60.0
    ).round(1)
    return episodes.sort_values("end", ascending=False)


def _ensure_styles():
    st.markdown(
        """
        <style>
        .jj-postmortem-card {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAF7 100%);
            border-radius: 24px;
            padding: 1rem 1rem 0.95rem 1rem;
            border: 1px solid rgba(35, 75, 141, 0.18);
            box-shadow: 0 14px 30px rgba(16, 31, 56, 0.08);
            min-height: 250px;
        }
        .jj-postmortem-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            color: #5F6B7A;
            font-weight: 760;
            margin-bottom: 0.42rem;
        }
        .jj-postmortem-title {
            font-size: 1.04rem;
            color: #234B8D;
            font-weight: 810;
            margin-bottom: 0.4rem;
        }
        .jj-postmortem-chip {
            display: inline-block;
            padding: 0.24rem 0.56rem;
            border-radius: 999px;
            font-size: 0.73rem;
            font-weight: 800;
            margin-bottom: 0.6rem;
        }
        .jj-postmortem-copy {
            font-size: 0.82rem;
            line-height: 1.5;
            color: #5F6B7A;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _chip(level: str):
    if str(level).upper() == "ALTO":
        return ("#FFF1F1", "#A61E2E")
    return ("#FFFCE0", "#8D7300")


def render_postmortem_panel(alerts_df: pd.DataFrame, prediction: dict, max_columns: int = 3) -> None:
    _ensure_styles()
    episodes = build_alert_episodes(alerts_df)
    if episodes.empty:
        st.info("No hay episodios recientes para construir el postmortem.")
        return

    card_count = min(3, len(episodes))
    column_count = max(1, min(int(max_columns), card_count))

    if column_count == 1:
        for idx, (_, row) in enumerate(episodes.head(card_count).iterrows()):
            bg, fg = _chip(row["level"])
            cause = str(row["reasons"]).split("|")[0].strip()
            event_time = pd.to_datetime(row.get("event_time", row.get("peak_time")), errors="coerce")
            if pd.isna(event_time):
                event_time = pd.to_datetime(row.get("peak_time"), errors="coerce")
            event_time_txt = event_time.strftime("%d/%m %H:%M:%S") if pd.notna(event_time) else "-"
            event_note = str(row.get("event_note", "")).strip() or "Sin descripcion de evento."
            st.markdown(
                f"""
                <div class="jj-postmortem-card" style="margin-bottom:0.75rem;">
                    <div class="jj-postmortem-label">Postmortem {idx + 1}</div>
                    <div class="jj-postmortem-title">
                        {row['start'].strftime('%d/%m %H:%M')} - {row['end'].strftime('%H:%M')}
                    </div>
                    <div class="jj-postmortem-chip" style="background:{bg}; color:{fg};">{row['level']}</div>
                    <div class="jj-postmortem-copy">
                        Hora del evento: {event_time_txt}<br>
                        Duracion: {row['duration_min']:.1f} min<br>
                        Ventanas afectadas: {int(row['windows'])}<br>
                        Triggers maximos: {int(row.get('max_triggers', 0))}<br>
                        Score maximo: {float(row['max_score']):.3f}<br>
                        Origenes: {row['sources']}<br><br>
                        Sensores clave: {row.get('sensor_snapshot', 'Sin sensores destacados.')}<br>
                        Evento: {event_note}<br>
                        <br>
                        Driver principal: {cause}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        return

    cols = st.columns(column_count, gap="medium")
    for idx, (_, row) in enumerate(episodes.head(card_count).iterrows()):
        bg, fg = _chip(row["level"])
        cause = str(row["reasons"]).split("|")[0].strip()
        event_time = pd.to_datetime(row.get("event_time", row.get("peak_time")), errors="coerce")
        if pd.isna(event_time):
            event_time = pd.to_datetime(row.get("peak_time"), errors="coerce")
        event_time_txt = event_time.strftime("%d/%m %H:%M:%S") if pd.notna(event_time) else "-"
        event_note = str(row.get("event_note", "")).strip() or "Sin descripcion de evento."
        with cols[idx]:
            st.markdown(
                f"""
                <div class="jj-postmortem-card">
                    <div class="jj-postmortem-label">Postmortem {idx + 1}</div>
                    <div class="jj-postmortem-title">
                        {row['start'].strftime('%d/%m %H:%M')} - {row['end'].strftime('%H:%M')}
                    </div>
                    <div class="jj-postmortem-chip" style="background:{bg}; color:{fg};">{row['level']}</div>
                    <div class="jj-postmortem-copy">
                        Hora del evento: {event_time_txt}<br>
                        Duracion: {row['duration_min']:.1f} min<br>
                        Ventanas afectadas: {int(row['windows'])}<br>
                        Triggers maximos: {int(row.get('max_triggers', 0))}<br>
                        Score maximo: {float(row['max_score']):.3f}<br>
                        Origenes: {row['sources']}<br><br>
                        Sensores clave: {row.get('sensor_snapshot', 'Sin sensores destacados.')}<br>
                        Evento: {event_note}<br>
                        <br>
                        Driver principal: {cause}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

