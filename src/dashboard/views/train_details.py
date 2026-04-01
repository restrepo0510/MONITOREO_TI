import streamlit as st
import plotly.graph_objects as go

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

    color_map = {"ALTO": "#e74c3c", "MEDIO": "#f39c12", "BAJO": "#2ecc71"}

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_f["timestamp"], y=df_f["risk_score"],
        mode="lines", name="Risk Score",
        line=dict(color="#01696f", width=1.5),
        fill="tozeroy", fillcolor="rgba(1,105,111,0.08)"
    ))
    fig.add_hline(y=0.6, line_dash="dot", line_color="#f39c12",
                  annotation_text="Umbral MEDIO (0.6)")
    fig.add_hline(y=0.8, line_dash="dot", line_color="#e74c3c",
                  annotation_text="Umbral ALTO (0.8)")
    fig.update_layout(
        height=420,
        xaxis_title="Timestamp",
        yaxis_title="Risk Score",
        yaxis=dict(range=[0, 1]),
        margin=dict(t=20, b=20)
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