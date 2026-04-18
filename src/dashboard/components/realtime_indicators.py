"""
Real-Time Indicators - Indicadores en tiempo real con animaciones premium.

Características:
- Status badges animados
- Indicadores de estado con colores dinámicos
- Métricas de impacto en tiempo real
- Paneles de monitoreo activo
"""

import streamlit as st


def render_status_badge(status: str, label: str = "", animate: bool = True):
    """
    Renderiza un badge de estado con animación.
    
    Args:
        status: 'OK', 'WARNING', 'CRITICAL', 'MAINTENANCE'
        label: Etiqueta del badge
        animate: Si debe animar con pulse
    """
    status_config = {
        'OK': {
            'color': '#4caf50',
            'bg': 'rgba(76, 175, 80, 0.1)',
            'text': '✓ Normal',
            'animation': 'opacity 2s ease-in-out infinite' if animate else 'none'
        },
        'WARNING': {
            'color': '#ffa500',
            'bg': 'rgba(255, 165, 0, 0.1)',
            'text': '⚠ Advertencia',
            'animation': 'opacity 1.5s ease-in-out infinite' if animate else 'none'
        },
        'CRITICAL': {
            'color': '#ff6b6b',
            'bg': 'rgba(255, 107, 107, 0.1)',
            'text': '🚨 Crítico',
            'animation': 'opacity 1s ease-in-out infinite' if animate else 'none'
        },
        'MAINTENANCE': {
            'color': '#667eea',
            'bg': 'rgba(102, 126, 234, 0.1)',
            'text': '🔧 Mantenimiento',
            'animation': 'none'
        }
    }
    
    config = status_config.get(status, status_config['OK'])
    
    html = f"""
    <style>
        @keyframes pulse-badge {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
        
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 50px;
            background: {config['bg']};
            border: 2px solid {config['color']};
            color: {config['color']};
            font-weight: 700;
            font-size: 0.95rem;
            animation: {config['animation']};
        }}
        
        .status-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: {config['color']};
            animation: {config['animation']};
        }}
    </style>
    
    <div class="status-badge">
        <div class="status-dot"></div>
        <span>{config['text']}</span>
        {f'<small style="opacity: 0.7; margin-left: 0.3rem;">({label})</small>' if label else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_live_indicator(value: float, label: str, threshold_warning: float = 70, threshold_critical: float = 85):
    """
    Renderiza un indicador de valor en vivo con cambio de color.
    
    Args:
        value: Valor actual
        label: Etiqueta
        threshold_warning: Umbral de advertencia
        threshold_critical: Umbral crítico
    """
    if value >= threshold_critical:
        color = '#ff6b6b'
        status = 'CRITICAL'
    elif value >= threshold_warning:
        color = '#ffa500'
        status = 'WARNING'
    else:
        color = '#4caf50'
        status = 'OK'
    
    html = f"""
    <div style="
        background: linear-gradient(135deg, {color} 0%, rgba({hex_to_rgb(color)[0]}, {hex_to_rgb(color)[1]}, {hex_to_rgb(color)[2]}, 0.1) 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border: 2px solid {color};
        position: relative;
        overflow: hidden;
    ">
        <div style="position: relative; z-index: 1;">
            <div style="font-size: 0.9rem; opacity: 0.95; margin-bottom: 0.5rem; font-weight: 600;">{label}</div>
            <div style="font-size: 2.5rem; font-weight: 900;">{value:.1f}</div>
            <div style="font-size: 0.85rem; opacity: 0.9; margin-top: 0.5rem;">{status}</div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def hex_to_rgb(hex_color: str):
    """Convierte hex a RGB."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def render_impact_card(title: str, impact_value: str, impact_unit: str, description: str, icon: str = ""):
    """
    Renderiza una tarjeta de impacto/métrica importante.
    
    Args:
        title: Título del impacto
        impact_value: Valor del impacto
        impact_unit: Unidad (USD, hrs, %)
        description: Descripción
        icon: Emoji o icono
    """
    # Construir HTML de forma limpia
    card_html = '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; padding: 2rem; color: white; box-shadow: 0 12px 24px rgba(102, 126, 234, 0.3); border: 1px solid rgba(255,255,255,0.1);">'
    card_html += '  <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">'
    card_html += f'    <span style="font-size: 2.5rem;">{icon}</span>'
    card_html += '    <div>'
    card_html += f'      <div style="font-size: 0.95rem; opacity: 0.9; margin-bottom: 0.25rem;">{title}</div>'
    card_html += f'      <div style="font-size: 2rem; font-weight: 900; line-height: 1;">{impact_value}<span style="font-size: 1.2rem; margin-left: 0.25rem;">{impact_unit}</span></div>'
    card_html += '    </div>'
    card_html += '  </div>'
    card_html += f'  <div style="font-size: 0.9rem; opacity: 0.85; line-height: 1.5;">{description}</div>'
    card_html += '</div>'
    
    st.markdown(card_html, unsafe_allow_html=True)


def render_monitoring_panel():
    """
    Renderiza un panel de monitoreo activo con múltiples indicadores.
    """
    st.markdown("""
    <style>
        @keyframes blink {
            0%, 49%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        
        .monitoring-indicator {
            animation: blink 1.5s ease-in-out infinite;
        }
        
        @keyframes slide-right {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(0); }
        }
        
        .progress-bar {
            animation: slide-right 2s ease-in-out;
        }
    </style>
    """, unsafe_allow_html=True)


def render_threat_meter(threat_level: int):
    """
    Renderiza un medidor de amenaza/riesgo.
    
    Args:
        threat_level: Nivel de 0-10
    """
    if threat_level <= 3:
        color = '#4caf50'
        label = 'BAJO'
    elif threat_level <= 6:
        color = '#ffa500'
        label = 'MEDIO'
    elif threat_level <= 8:
        color = '#ff9800'
        label = 'ALTO'
    else:
        color = '#ff6b6b'
        label = 'CRÍTICO'
    
    percentage = (threat_level / 10) * 100
    
    html = f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; font-size: 0.95rem;">Nivel de Amenaza</span>
            <span style="font-weight: 700; color: {color};">{threat_level}/10 - {label}</span>
        </div>
        <div style="
            width: 100%;
            height: 24px;
            background: rgba(0,0,0,0.1);
            border-radius: 12px;
            overflow: hidden;
            border: 2px solid {color};
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: linear-gradient(90deg, {color} 0%, rgba({hex_to_rgb(color)[0]}, {hex_to_rgb(color)[1]}, {hex_to_rgb(color)[2]}, 0.5) 100%);
                transition: width 0.5s ease;
            "></div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)
