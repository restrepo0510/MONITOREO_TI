import plotly.express as px
import streamlit as st


def render(df):
    st.title("Resumen General (Legacy 2026-04-01)")
    st.markdown("---")

    total = len(df)
    high = int((df["risk_level"] == "ALTO").sum())
    medium = int((df["risk_level"] == "MEDIO").sum())
    low = int((df["risk_level"] == "BAJO").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total ventanas", f"{total:,}")
    c2.metric("Alto riesgo", f"{high:,}", delta=f"{(high / max(1, total)) * 100:.1f}%")
    c3.metric("Medio riesgo", f"{medium:,}", delta=f"{(medium / max(1, total)) * 100:.1f}%")
    c4.metric("Bajo riesgo", f"{low:,}", delta=f"{(low / max(1, total)) * 100:.1f}%")

    st.markdown("---")

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Evolucion del Score de Riesgo")
        fig = px.line(
            df,
            x="timestamp",
            y="risk_score",
            color_discrete_sequence=["#01696F"],
            labels={"risk_score": "Score", "timestamp": "Tiempo"},
        )
        fig.add_hline(y=0.6, line_dash="dash", line_color="orange", annotation_text="Umbral MEDIO")
        fig.add_hline(y=0.8, line_dash="dash", line_color="red", annotation_text="Umbral ALTO")
        fig.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Distribucion de Niveles")
        dist = df["risk_level"].value_counts().reset_index()
        dist.columns = ["Nivel", "Cantidad"]
        color_map = {"ALTO": "#E74C3C", "MEDIO": "#F39C12", "BAJO": "#2ECC71"}
        fig2 = px.pie(
            dist,
            names="Nivel",
            values="Cantidad",
            color="Nivel",
            color_discrete_map=color_map,
            hole=0.45,
        )
        fig2.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)
