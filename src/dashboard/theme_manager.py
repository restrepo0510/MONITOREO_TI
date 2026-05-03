"""
Theme Manager PREMIUM - Sistema de estilos modernos y sofisticados.

Características:
- Diseño ejecutivo de nivel Fortune 500
- Animaciones suaves y transiciones
- Gradientes y efectos visuales premium
- Componentes responsive y accesibles
- CSS inyectado UNA SOLA VEZ al cargar
"""

import streamlit as st
from pathlib import Path
import time

# ============================================================================
# INYECCIÓN DE CSS (UNA SOLA VEZ)
# ============================================================================

def inject_theme_css():
    """
    Inyecta CSS premium con diseño moderno y ejecutivo.
    Diseñado para impresionar.
    """
    st.markdown(
        """
        <style>
        /* ===== RESET Y BASE ===== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; }
        
        /* ===== COLORES PREMIUM ===== */
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --accent-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            --danger-gradient: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            
            --primary-blue: #667eea;
            --secondary-purple: #764ba2;
            --accent-pink: #f093fb;
            --alert-red: #ff6b6b;
            --success-cyan: #00f2fe;
            --warning-yellow: #fee140;
            
            --text-dark: #1a202c;
            --text-medium: #2d3748;
            --text-light: #718096;
            
            --shadow-sm: 0 4px 6px rgba(0, 0, 0, 0.07);
            --shadow-md: 0 10px 25px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 20px 40px rgba(0, 0, 0, 0.15);
            --shadow-xl: 0 30px 50px rgba(0, 0, 0, 0.2);
        }
        
        /* ===== TIPOGRAFÍA PREMIUM ===== */
        .title-main {
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3.2rem;
            font-weight: 900;
            line-height: 1;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            letter-spacing: -1px;
        }
        
        .subtitle-main {
            color: var(--text-light);
            font-size: 1.1rem;
            font-weight: 500;
            line-height: 1.6;
            margin-bottom: 0;
        }
        
        .section-kicker {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: var(--primary-blue);
            font-weight: 800;
            margin-top: 2rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .section-kicker::before {
            content: '';
            width: 3px;
            height: 20px;
            background: var(--accent-gradient);
            border-radius: 2px;
        }
        
        .section-title {
            font-size: 1.85rem;
            color: var(--text-dark);
            font-weight: 800;
            margin-bottom: 0.75rem;
            letter-spacing: -0.5px;
        }
        
        .section-copy {
            font-size: 1rem;
            color: var(--text-light);
            line-height: 1.6;
            margin-bottom: 1.5rem;
            max-width: 900px;
        }
        
        /* ===== HEADER HERO ===== */
        .header-hero {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
            border-top: 3px solid var(--primary-blue);
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }
        
        .header-hero::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(240, 147, 251, 0.1), transparent);
            border-radius: 50%;
            animation: float 8s ease-in-out infinite;
        }
        
        .header-hero::after {
            content: '';
            position: absolute;
            bottom: -50%;
            left: -5%;
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, rgba(79, 172, 254, 0.1), transparent);
            border-radius: 50%;
            animation: float-reverse 8s ease-in-out infinite;
        }
        
        /* ===== ANIMACIONES ===== */
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(20px); }
        }
        
        @keyframes float-reverse {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4); }
            50% { box-shadow: 0 0 0 15px rgba(102, 126, 234, 0); }
        }
        
        @keyframes slide-in {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* ===== KPI CARDS PREMIUM ===== */
        .kpi-card-premium {
            border-radius: 20px;
            padding: 1.8rem;
            border: 1px solid rgba(102, 126, 234, 0.1);
            box-shadow: var(--shadow-md);
            background: linear-gradient(135deg, #ffffff 0%, #f7f9ff 100%);
            min-height: 180px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            animation: slide-in 0.6s ease-out;
        }
        
        .kpi-card-premium::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 100px;
            height: 100px;
            background: var(--primary-gradient);
            opacity: 0.05;
            border-radius: 50%;
            transform: translate(30%, -30%);
        }
        
        .kpi-card-premium:hover {
            transform: translateY(-8px);
            box-shadow: var(--shadow-lg);
            background: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%);
        }
        
        .kpi-label {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            opacity: 0.7;
            font-weight: 700;
            margin-bottom: 0.8rem;
            color: var(--text-medium);
        }
        
        .kpi-value {
            font-size: 2.4rem;
            line-height: 1;
            font-weight: 900;
            margin-bottom: 0.5rem;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .kpi-delta {
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
            padding: 0.4rem 0.8rem;
            border-radius: 10px;
            display: inline-block;
            background: rgba(79, 172, 254, 0.1);
            color: var(--primary-blue);
        }
        
        .kpi-delta.positive {
            background: rgba(79, 172, 254, 0.15);
            color: #0066cc;
        }
        
        .kpi-delta.negative {
            background: rgba(255, 107, 107, 0.15);
            color: #cc0000;
        }
        
        .kpi-caption {
            font-size: 0.9rem;
            line-height: 1.5;
            color: var(--text-light);
        }
        
        /* ===== PROGRESS BAR ===== */
        .kpi-progress {
            width: 100%;
            height: 4px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 1rem;
        }
        
        .kpi-progress-bar {
            height: 100%;
            background: var(--success-gradient);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        /* ===== ALERT BADGE PREMIUM ===== */
        .alert-badge {
            border-radius: 16px;
            padding: 1.2rem 1.5rem;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
            border: 1px solid transparent;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 1rem;
            animation: slide-in 0.6s ease-out;
        }
        
        .alert-badge::before {
            content: '';
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse-glow 2s infinite;
        }
        
        .alert-badge-high {
            background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(238, 90, 111, 0.05));
            color: #cc0000;
            border-color: rgba(255, 107, 107, 0.2);
        }
        
        .alert-badge-high::before {
            background: #ff6b6b;
        }
        
        .alert-badge-medium {
            background: linear-gradient(135deg, rgba(254, 225, 64, 0.1), rgba(250, 112, 154, 0.05));
            color: #d4a400;
            border-color: rgba(250, 112, 154, 0.2);
        }
        
        .alert-badge-medium::before {
            background: #ffd700;
        }
        
        .alert-badge-low {
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.1), rgba(0, 242, 254, 0.05));
            color: #0066cc;
            border-color: rgba(79, 172, 254, 0.2);
        }
        
        .alert-badge-low::before {
            background: #4facfe;
        }
        
        /* ===== HERO CONTAINER ===== */
        .hero-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            padding: 2.5rem;
            color: white;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
            box-shadow: var(--shadow-lg);
        }
        
        .hero-container::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.1), transparent);
            border-radius: 50%;
        }
        
        .hero-container::after {
            content: '';
            position: absolute;
            bottom: -50%;
            left: -5%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.05), transparent);
            border-radius: 50%;
        }
        
        /* ===== CHART CONTAINER ===== */
        .chart-container {
            background: linear-gradient(135deg, #ffffff 0%, #f7f9ff 100%);
            border-radius: 20px;
            padding: 1.5rem;
            border: 1px solid rgba(102, 126, 234, 0.1);
            box-shadow: var(--shadow-md);
            margin-bottom: 1.5rem;
        }
        
        .chart-container .plotly-chart {
            border-radius: 16px;
            overflow: hidden;
        }
        
        /* ===== STATS GRID ===== */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        /* ===== METRIC GAUGE ===== */
        .metric-gauge {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 0 auto;
            margin-bottom: 1rem;
        }
        
        .gauge-canvas {
            width: 100%;
            height: 100%;
        }
        
        /* ===== RESPONSIVE ===== */
        @media (max-width: 768px) {
            .title-main { font-size: 2.2rem; }
            .section-title { font-size: 1.4rem; }
            .kpi-value { font-size: 1.8rem; }
            .kpi-card-premium { min-height: 140px; padding: 1.2rem; }
            .stats-grid { grid-template-columns: 1fr; }
        }
        
        /* ===== SCROLLBAR CUSTOM ===== */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-blue);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--secondary-purple);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# COMPONENTES MODERNOS Y SOFISTICADOS
# ============================================================================

def render_page_title(title: str, subtitle: str):
    """Renderiza el título principal de la página con diseño premium."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 2rem 0; position: relative;">
            <h1 class="title-main">{title}</h1>
            <p class="subtitle-main">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(kicker: str, title: str, description: str):
    """Renderiza un header de sección premium con animación."""
    st.markdown(
        f"""
        <div class="section-header" style="margin: 2rem 0;">
            <div class="section-kicker">{kicker}</div>
            <div class="section-title">{title}</div>
            <div class="section-copy">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero_alert(alert_level: str, score: float, trend: str):
    """Renderiza una alerta tipo hero con diseño impactante."""
    colors = {
        "ALTO": "linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)",
        "MEDIO": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "BAJO": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    }
    
    gradient = colors.get(alert_level, colors["BAJO"])
    icon = {"ALTO": "🚨", "MEDIO": "⚠️", "BAJO": "✅"}.get(alert_level, "ℹ️")
    
    st.markdown(
        f"""
        <div class="hero-container">
            <div style="position: relative; z-index: 1;">
                <div style="font-size: 3.5rem; margin-bottom: 1rem;">{icon}</div>
                <h2 style="font-size: 2rem; font-weight: 900; margin-bottom: 0.5rem;">
                    ALERTA OPERACIONAL
                </h2>
                <p style="font-size: 1.2rem; opacity: 0.95; margin-bottom: 1rem;">
                    Risk Score: <strong>{score:.3f}</strong> | Tendencia: <strong>{trend}</strong>
                </p>
                <p style="font-size: 0.95rem; opacity: 0.9;">
                    Estado: <strong>{alert_level}</strong> • Tiempo Real
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card_advanced(label: str, value: str, delta: str = "", caption: str = "", 
                             progress: float = 0, color: str = "blue", icon: str = ""):
    """
    Renderiza una tarjeta KPI premium con barra de progreso y animación.
    
    Args:
        label: Etiqueta de la métrica
        value: Valor principal
        delta: Cambio/tendencia
        caption: Descripción
        progress: Porcentaje de progreso (0-100)
        color: blue, cyan, pink, yellow, red
        icon: Emoji o icono
    """
    # Mapeo de colores
    color_map = {
        "blue": ("var(--primary-gradient)", "rgba(102, 126, 234, 0.1)"),
        "cyan": ("var(--success-gradient)", "rgba(79, 172, 254, 0.1)"),
        "pink": ("var(--accent-gradient)", "rgba(240, 147, 251, 0.1)"),
        "yellow": ("var(--warning-gradient)", "rgba(254, 225, 64, 0.1)"),
        "red": ("var(--danger-gradient)", "rgba(255, 107, 107, 0.1)"),
    }
    
    gradient, bg = color_map.get(color, color_map["blue"])
    delta_class = "positive" if "↑" in delta else "negative" if "↓" in delta else ""
    
    progress_bar = f"""
        <div class="kpi-progress">
            <div class="kpi-progress-bar" style="width: {min(progress, 100)}%; background: {gradient.replace('linear-gradient', 'linear-gradient')}"></div>
        </div>
    """ if progress > 0 else ""
    
    st.markdown(
        f"""
        <div class="kpi-card-premium">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                <div class="kpi-label">{icon} {label}</div>
            </div>
            <div class="kpi-value">{value}</div>
            {f'<div class="kpi-delta {delta_class}">{delta}</div>' if delta else ''}
            <p class="kpi-caption">{caption}</p>
            {progress_bar}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_row(metrics: list):
    """
    Renderiza una fila de métricas KPI.
    
    Args:
        metrics: Lista de dicts con {label, value, delta, caption, color, icon}
    """
    cols = st.columns(len(metrics), gap="medium")
    for col, metric in zip(cols, metrics):
        with col:
            render_kpi_card_advanced(**metric)


def render_trend_indicator(label: str, current: float, previous: float = None, unit: str = ""):
    """Renderiza un indicador de tendencia visual."""
    if previous is not None:
        change = current - previous
        change_pct = (change / previous * 100) if previous != 0 else 0
        trend = "📈" if change >= 0 else "📉"
        delta = f"{trend} {change_pct:+.1f}%"
    else:
        delta = ""
    
    render_kpi_card_advanced(
        label=label,
        value=f"{current:.2f}{unit}",
        delta=delta,
        progress=min(current * 100 / 100, 100) if current > 0 else 0
    )


def render_stats_summary(title: str, stats: dict):
    """
    Renderiza un resumen de estadísticas en formato grid.
    
    Args:
        title: Título de la sección
        stats: Dict con {stat_name: value}
    """
    st.markdown(f'<h3 class="section-title">{title}</h3>', unsafe_allow_html=True)
    
    cols = st.columns(len(stats), gap="small")
    for col, (stat_name, stat_value) in zip(cols, stats.items()):
        with col:
            st.markdown(
                f"""
                <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 12px; color: white;">
                    <div style="font-size: 1.8rem; font-weight: 900;">{stat_value}</div>
                    <div style="font-size: 0.85rem; opacity: 0.9; margin-top: 0.5rem;">{stat_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_premium_divider():
    """Renderiza un divisor premium entre secciones."""
    st.markdown(
        """
        <div style="height: 2px; background: linear-gradient(90deg, transparent, #667eea, transparent); 
        margin: 2rem 0; border-radius: 10px;"></div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# COLORES Y PALETA
# ============================================================================

COLORS = {
    "primary-blue": "#667eea",
    "secondary-purple": "#764ba2",
    "accent-pink": "#f093fb",
    "alert-red": "#ff6b6b",
    "success-cyan": "#00f2fe",
    "warning-yellow": "#fee140",
}

RISK_THEME = {
    "ALTO": {
        "color": "#ff6b6b",
        "bg": "#fff0f0",
        "gradient": "linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)",
    },
    "MEDIO": {
        "color": "#ffa500",
        "bg": "#fff8f0",
        "gradient": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    },
    "BAJO": {
        "color": "#4facfe",
        "bg": "#f0f8ff",
        "gradient": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    },
}
