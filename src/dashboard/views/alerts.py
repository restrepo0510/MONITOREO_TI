import streamlit as st
import plotly.express as px

def render(df):
    st.title("🔔 Panel de Alertas")
    st.markdown("---")

    alto  = df[df["risk_level"] == "ALTO"].copy()
    medio = df[df["risk_level"] == "MEDIO"].copy()

    if alto.empty and medio.empty:
        st.success("✅ Sin alertas activas. Sistema operando en rango normal.")
        return

    st.error(f"🔴 **{len(alto)} ventanas en nivel ALTO**")
    st.warning(f"🟡 **{len(medio)} ventanas en nivel MEDIO**")

    st.markdown("---")
    st.subheader("Ventanas críticas (ALTO riesgo)")
    if not alto.empty:
        st.dataframe(
            alto[["timestamp", "risk_score"]]
              .sort_values("risk_score", ascending=False)
              .head(50)
              .reset_index(drop=True),
            use_container_width=True
        )

        fig = px.histogram(alto, x="risk_score", nbins=20,
                           color_discrete_sequence=["#e74c3c"],
                           labels={"risk_score": "Score", "count": "Ventanas"},
                           title="Distribución de scores en zona ALTO")
        fig.update_layout(height=300, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin ventanas en nivel ALTO.")