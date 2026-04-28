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


@st.fragment(run_every="1s")
def render_station_line(train_id: str = "001", cycle_seconds: int = 5) -> None:
    """
    Renderiza una mini linea de metro compacta y auto-rotativa.
    """
    cycle = max(int(cycle_seconds), 1)
    # Offset por tren para que cada unidad no quede sincronizada en la misma estacion.
    train_offset = sum(ord(ch) for ch in str(train_id))
    tick = int(time.time() // cycle) + train_offset
    triplet = get_station_triplet(tick)

    st.markdown(
        f"""
        <style>
        .station-strip {{
          border: 1px solid rgba(35, 75, 141, 0.20);
          border-radius: 14px;
          background: linear-gradient(180deg, #FFFFFF 0%, #F7FAFF 100%);
          padding: 0.5rem 0.65rem;
        }}
        .station-train-id {{
          font-size: 0.72rem;
          font-weight: 700;
          color: #4B5563;
          margin-bottom: 0.28rem;
          letter-spacing: 0.02em;
        }}
        .station-line-row {{
          display: grid;
          grid-template-columns: 1fr auto 1fr auto 1fr;
          align-items: center;
          gap: 0.3rem;
        }}
        .station-node {{
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          font-size: 0.69rem;
          line-height: 1.1;
          text-align: center;
          min-height: 2.05rem;
          padding: 0.22rem 0.55rem;
        }}
        .station-prev, .station-next {{
          background: #EEF2FF;
          color: #1F2937;
          border: 1px solid #D1D5DB;
          opacity: 0.88;
        }}
        .station-current {{
          background: #234B8D;
          color: #FFFFFF;
          border: 1px solid #173A73;
          font-weight: 800;
          box-shadow: 0 0 0 3px rgba(35, 75, 141, 0.18);
          position: relative;
        }}
        .station-current::after {{
          content: "●";
          color: #FFE600;
          position: absolute;
          top: -0.55rem;
          right: 0.32rem;
          font-size: 0.72rem;
        }}
        .station-connector {{
          height: 2px;
          width: 1.15rem;
          border-radius: 999px;
          background: linear-gradient(90deg, #93C5FD 0%, #1D4ED8 100%);
        }}
        </style>
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
