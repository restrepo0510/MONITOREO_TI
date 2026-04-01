import streamlit as st
from data_loader import load_scores
from views import home, train_details, alerts

st.set_page_config(
    page_title="MonitoreoTI — Dashboard de Riesgo",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Sidebar navegación ──────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚦 MonitoreoTI")
    st.markdown("---")
    vista = st.radio(
        "Navegación",
        options=["🏠 Resumen General", "🔍 Detalle de Señales", "🔔 Alertas"],
        index=0
    )
    st.markdown("---")
    if st.button("🔄 Refrescar datos"):
        st.cache_data.clear()
        st.rerun()

# ── Carga de datos ──────────────────────────────────────────
df = load_scores()

# ── Enrutamiento de vistas ──────────────────────────────────
if vista == "🏠 Resumen General":
    home.render(df)
elif vista == "🔍 Detalle de Señales":
    train_details.render(df)
elif vista == "🔔 Alertas":
    alerts.render(df)