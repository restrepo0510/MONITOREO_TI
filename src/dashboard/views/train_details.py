import streamlit as st
import plotly.graph_objects as go
from src.dashboard.theme import PALETTE, RISK_THRESHOLDS

def render(df):
    st.title("🔍 Detalle de Señales")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        fecha_ini = st.date_input("Desde", value=df["timestamp"].min().date())
    with col2:
        fecha_fin = st.date_input("Hasta", value=df["timestamp"].max().date())

    mask = (df["timestamp"].dt.date >= fecha_ini) & \
           (df["timestamp"].dt.date <= fecha_fin)
    df_f = df[mask]

    if df_f.empty:
        st.warning("No hay datos en el rango seleccionado.")
        return

    st.subheader(f"Score de Riesgo — {len(df_f):,} ventanas")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_f["timestamp"], y=df_f["risk_score"],
        mode="lines", name="Risk Score",
        line=dict(color=PALETTE["steel_azure"], width=2),
        fill="tozeroy", fillcolor="rgba(184,219,217,0.28)"
    ))
    fig.add_hline(
        y=RISK_THRESHOLDS["MEDIO"],
        line_dash="dot",
        line_color=PALETTE["yellow"],
        annotation_text=f"Umbral MEDIO ({RISK_THRESHOLDS['MEDIO']:.1f})",
    )
    fig.add_hline(
        y=RISK_THRESHOLDS["ALTO"],
        line_dash="dot",
        line_color=PALETTE["alert_red"],
        annotation_text=f"Umbral ALTO ({RISK_THRESHOLDS['ALTO']:.1f})",
    )
    fig.update_layout(
        height=420,
        xaxis_title="Timestamp",
        yaxis_title="Risk Score",
        yaxis=dict(range=[0, 1]),
        margin=dict(t=20, b=20),
        paper_bgcolor=PALETTE["ghost_white"],
        plot_bgcolor="white",
        font=dict(color=PALETTE["black"]),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tabla de Ventanas")
    st.dataframe(
        df_f[["timestamp", "risk_score", "risk_level"]]
          .sort_values("risk_score", ascending=False)
          .reset_index(drop=True),
        use_container_width=True,
        height=300
    )
