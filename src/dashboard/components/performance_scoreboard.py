"""
Performance Scoreboard - Panel de desempeño competitivo y visual.

Características:
- Ranking de estaciones
- Comparison tables con estilos premium
- Award badges para mejores performers
- Performance trends
"""

import streamlit as st
import pandas as pd


def render_leaderboard(data: pd.DataFrame, columns: list, title: str = "Ranking"):
    """
    Renderiza un leaderboard/ranking con estilos premium.
    
    Args:
        data: DataFrame con datos
        columns: Columnas a mostrar
        title: Título
    """
    # Ordenar por primera columna de valor
    data_sorted = data.sort_values(by=columns[1], ascending=False).reset_index(drop=True)
    
    st.markdown(f"### 🏆 {title}")
    
    for idx, row in data_sorted.head(10).iterrows():
        medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"#{idx+1}"
        
        # Color degradado según posición
        if idx == 0:
            bg_color = "linear-gradient(135deg, #ffd700 0%, #ffed4e 100%)"
            border_color = "#ffd700"
        elif idx == 1:
            bg_color = "linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%)"
            border_color = "#c0c0c0"
        elif idx == 2:
            bg_color = "linear-gradient(135deg, #cd7f32 0%, #daa520 100%)"
            border_color = "#cd7f32"
        else:
            bg_color = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
            border_color = "#667eea"
        
        col1, col2, col3 = st.columns([0.15, 0.6, 0.25])
        
        with col1:
            st.markdown(f"<div style='text-align: center; font-size: 1.8rem; font-weight: 900;'>{medal}</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<div style='font-weight: 700; font-size: 1.05rem;'>{row[columns[0]]}</div>", unsafe_allow_html=True)
        
        with col3:
            value_text = f"{row[columns[1]]:.2f}" if isinstance(row[columns[1]], float) else str(row[columns[1]])
            st.markdown(
                f"""
                <div style="
                    background: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 8px;
                    padding: 0.5rem 1rem;
                    text-align: center;
                    font-weight: 700;
                    color: {'#333' if idx <= 2 else 'white'};
                    font-size: 1.1rem;
                ">
                    {value_text}
                </div>
                """,
                unsafe_allow_html=True
            )


def render_comparison_table(data: pd.DataFrame, highlight_columns: list = None):
    """
    Renderiza una tabla de comparación con estilos premium.
    
    Args:
        data: DataFrame
        highlight_columns: Columnas a destacar
    """
    st.markdown("""
    <style>
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .comparison-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 700;
        }
        
        .comparison-table th, .comparison-table td {
            padding: 1rem;
            text-align: center;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .comparison-table tbody tr {
            transition: background-color 0.3s ease;
        }
        
        .comparison-table tbody tr:hover {
            background-color: rgba(102, 126, 234, 0.05);
        }
        
        .comparison-table tbody tr:last-child td {
            border-bottom: none;
        }
        
        .highlight-cell {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            font-weight: 700;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # HTML table
    html = '<table class="comparison-table"><thead><tr>'
    for col in data.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    
    for idx, row in data.iterrows():
        html += '<tr>'
        for col in data.columns:
            cell_class = 'highlight-cell' if highlight_columns and col in highlight_columns else ''
            html += f'<td class="{cell_class}">{row[col]}</td>'
        html += '</tr>'
    
    html += '</tbody></table>'
    
    st.markdown(html, unsafe_allow_html=True)


def render_award_badge(awarded_to: str, award_type: str, metric: str, value: str):
    """
    Renderiza un badge de premio/reconocimiento.
    
    Args:
        awarded_to: A quién se otorga
        award_type: Tipo de premio (Best Overall, Safety Champion, etc)
        metric: Métrica premiada
        value: Valor
    """
    award_config = {
        'Best Overall': {'icon': '🏆', 'color': '#ffd700', 'bg': 'rgba(255, 215, 0, 0.1)'},
        'Safety Champion': {'icon': '⭐', 'color': '#ff6b6b', 'bg': 'rgba(255, 107, 107, 0.1)'},
        'Efficiency Leader': {'icon': '⚡', 'color': '#4facfe', 'bg': 'rgba(79, 172, 254, 0.1)'},
        'Uptime Master': {'icon': '✅', 'color': '#4caf50', 'bg': 'rgba(76, 175, 80, 0.1)'},
    }
    
    config = award_config.get(award_type, award_config['Best Overall'])
    
    html = f"""
    <div style="
        background: linear-gradient(135deg, {config['bg']} 0%, rgba(0,0,0,0.02) 100%);
        border: 3px solid {config['color']};
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        color: {config['color']};
        position: relative;
        overflow: hidden;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">{config['icon']}</div>
        <div style="font-size: 1.3rem; font-weight: 900; margin-bottom: 0.5rem;">{award_type}</div>
        <div style="font-size: 1.1rem; color: #333; margin-bottom: 0.5rem;">{awarded_to}</div>
        <div style="font-size: 0.95rem; color: #666;">
            <span>{metric}: </span>
            <span style="font-weight: 700; color: {config['color']};">{value}</span>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_performance_grid(stations_data: dict):
    """
    Renderiza un grid de desempeño de estaciones.
    
    Args:
        stations_data: Dict con datos de estaciones
    """
    cols = st.columns(len(stations_data))
    
    for col, (station, metrics) in zip(cols, stations_data.items()):
        with col:
            # Calcular score
            score = metrics.get('score', 0)
            if score >= 85:
                color = '#4caf50'
                emoji = '✅'
            elif score >= 70:
                color = '#ffa500'
                emoji = '⚠️'
            else:
                color = '#ff6b6b'
                emoji = '❌'
            
            html = f"""
            <div style="
                background: linear-gradient(135deg, {color} 0%, rgba({hex_to_rgb(color)[0]}, {hex_to_rgb(color)[1]}, {hex_to_rgb(color)[2]}, 0.1) 100%);
                border: 2px solid {color};
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                color: {'white' if score < 70 else '#333'};
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{emoji}</div>
                <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">{station}</div>
                <div style="font-size: 2.2rem; font-weight: 900; margin-bottom: 0.5rem;">{score}</div>
                <div style="font-size: 0.85rem; opacity: 0.9;">
                    {metrics.get('label', 'Score')}
                </div>
            </div>
            """
            
            st.markdown(html, unsafe_allow_html=True)


def hex_to_rgb(hex_color: str):
    """Convierte hex a RGB."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
