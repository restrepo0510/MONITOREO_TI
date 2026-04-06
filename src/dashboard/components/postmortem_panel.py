"""
Placeholder module.
Este archivo se completará en el desarrollo del dashboard.
"""

import pandas as pd
import streamlit as st


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

    episodes = (
        work.groupby("episode_id", dropna=False)
        .agg(
            start=("timestamp", "min"),
            end=("timestamp", "max"),
            level=("alert_level", lambda s: "ALTO" if (s == "ALTO").any() else "MEDIO"),
            max_score=("risk_score", "max"),
            sources=("alert_sources", lambda s: ", ".join(sorted(set(s)))),
            reasons=("alert_reasons", "last"),
            windows=("alert_level", "size"),
        )
        .reset_index(drop=True)
    )
    episodes["duration_min"] = (
        (episodes["end"] - episodes["start"]).dt.total_seconds() / 60.0
    ).round(1)
    return episodes.sort_values("end", ascending=False)


def _ensure_styles():
    st.markdown(
        """
        <style>
        .jj-postmortem-card {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFF 100%);
            border-radius: 22px;
            padding: 1rem 1rem 0.95rem 1rem;
            border: 1px solid rgba(35, 75, 141, 0.10);
            box-shadow: 0 18px 34px rgba(15, 30, 60, 0.08);
            min-height: 250px;
        }
        .jj-postmortem-label {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            color: #6C7A95;
            font-weight: 700;
            margin-bottom: 0.42rem;
        }
        .jj-postmortem-title {
            font-size: 1.04rem;
            color: #0F1E3C;
            font-weight: 800;
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
            font-size: 0.86rem;
            line-height: 1.5;
            color: #4F5D78;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _chip(level: str):
    if str(level).upper() == "ALTO":
        return ("#FFF1F1", "#A61E2E")
    return ("#FFFCE0", "#8D7300")


def render_postmortem_panel(alerts_df: pd.DataFrame, prediction: dict) -> None:
    _ensure_styles()
    episodes = build_alert_episodes(alerts_df)
    if episodes.empty:
        st.info("No hay episodios recientes para construir el postmortem.")
        return

    cols = st.columns(min(3, len(episodes)), gap="medium")
    for idx, (_, row) in enumerate(episodes.head(3).iterrows()):
        bg, fg = _chip(row["level"])
        cause = str(row["reasons"]).split("|")[0].strip()
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
                        Duracion: {row['duration_min']:.1f} min<br>
                        Ventanas afectadas: {int(row['windows'])}<br>
                        Score maximo: {float(row['max_score']):.3f}<br>
                        Origenes: {row['sources']}<br><br>
                        Driver principal: {cause}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption(
        f"Lectura ejecutiva: {prediction.get('message', 'Sin proyeccion activa')}."
    )
