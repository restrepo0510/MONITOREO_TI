import streamlit as st
import plotly.express as px

def render(df):
    st.title("🏠 Resumen General del Sistema")
    st.markdown("---")

    total = len(df)
    alto  = int((df["risk_level"] == "ALTO").sum())
    medio = int((df["risk_level"] == "MEDIO").sum())
    bajo  = int((df["risk_level"] == "BAJO").sum())

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total ventanas", f"{total:,}")
    c2.metric("🔴 Alto riesgo",  f"{alto:,}",  delta=f"{alto/total*100:.1f}%")
    c3.metric("🟡 Medio riesgo", f"{medio:,}", delta=f"{medio/total*100:.1f}%")
    c4.metric("🟢 Bajo riesgo",  f"{bajo:,}",  delta=f"{bajo/total*100:.1f}%")

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Evolución del Score de Riesgo")
        fig = px.line(df, x="timestamp", y="risk_score",
                      color_discrete_sequence=["#01696f"],
                      labels={"risk_score": "Score", "timestamp": "Tiempo"})
        fig.add_hline(y=0.6, line_dash="dash", line_color="orange",
                      annotation_text="Umbral MEDIO")
        fig.add_hline(y=0.8, line_dash="dash", line_color="red",
                      annotation_text="Umbral ALTO")
        fig.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Distribución de Niveles")
        dist = df["risk_level"].value_counts().reset_index()
        dist.columns = ["Nivel", "Cantidad"]
        color_map = {"ALTO": "#e74c3c", "MEDIO": "#f39c12", "BAJO": "#2ecc71"}
        fig2 = px.pie(dist, names="Nivel", values="Cantidad",
                      color="Nivel", color_discrete_map=color_map,
                      hole=0.45)
        fig2.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)