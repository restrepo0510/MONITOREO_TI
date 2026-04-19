"""
Componente visual de estaciones para el header.

Muestra:
- estacion anterior
- estacion actual
- estacion siguiente

La estacion actual rota automaticamente cada N segundos.
"""

from __future__ import annotations

import time

import streamlit as st

from src.dashboard.utils.station_mapper import get_station_triplet


@st.fragment(run_every="5s")
def render_station_line(train_id: str = "001", cycle_seconds: int = 5) -> None:
    """
    Renderiza una mini linea de metro compacta y auto-rotativa.
    """
    # Tick temporal para rotar estaciones sin estado persistente.
    tick = int(time.time() // max(cycle_seconds, 1))
    triplet = get_station_triplet(tick)

    st.markdown(
        f"""
        <div class="station-strip">
          <div class="station-train-id">Train ID: {train_id}</div>
          <div class="station-line-row">
            <span class="station-node station-prev">{triplet['previous']}</span>
            <span class="station-connector"></span>
            <span class="station-node station-current">{triplet['current']}</span>
            <span class="station-connector"></span>
            <span class="station-node station-next">{triplet['next']}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
