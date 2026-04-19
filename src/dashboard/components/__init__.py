"""
Dashboard Components Package

Importa los componentes premium para uso fácil en vistas.

IMPORTACIÓN RÁPIDA:
    from src.dashboard.components import (
        render_gauge_metric,
        render_status_badge,
        render_leaderboard
    )
"""

# ============================================================================
# ADVANCED METRICS
# ============================================================================

try:
    from .advanced_metrics import (
        render_gauge_metric,
        render_correlation_heatmap,
        render_sparkline_trend,
        render_comparison_chart,
        render_metric_card_with_history,
        render_metrics_dashboard
    )
except ImportError:
    pass

# ============================================================================
# REAL-TIME INDICATORS
# ============================================================================

try:
    from .realtime_indicators import (
        render_status_badge,
        render_live_indicator,
        render_impact_card,
        render_threat_meter,
        render_monitoring_panel
    )
except ImportError:
    pass

# ============================================================================
# PERFORMANCE SCOREBOARD
# ============================================================================

try:
    from .performance_scoreboard import (
        render_leaderboard,
        render_comparison_table,
        render_award_badge,
        render_performance_grid
    )
except ImportError:
    pass

# ============================================================================
# EXISTING COMPONENTS (si existen)
# ============================================================================

try:
    from .alert_badge import render_alert_badge
except ImportError:
    pass

try:
    from .kpi_card import render_kpi_card
except ImportError:
    pass

try:
    from .sensor_chart import render_sensor_chart
except ImportError:
    pass

try:
    from .golden_signals import render_golden_signals
except ImportError:
    pass

try:
    from .financial_section import render_financial_section
except ImportError:
    pass

try:
    from .operativity_panel import render_operativity_panel
except ImportError:
    pass

try:
    from .postmortem_panel import render_postmortem_panel
except ImportError:
    pass

try:
    from .station_line import render_station_line
except ImportError:
    pass


__all__ = [
    # Advanced Metrics
    'render_gauge_metric',
    'render_correlation_heatmap',
    'render_sparkline_trend',
    'render_comparison_chart',
    'render_metric_card_with_history',
    'render_metrics_dashboard',
    
    # Real-Time Indicators
    'render_status_badge',
    'render_live_indicator',
    'render_impact_card',
    'render_threat_meter',
    'render_monitoring_panel',
    
    # Performance Scoreboard
    'render_leaderboard',
    'render_comparison_table',
    'render_award_badge',
    'render_performance_grid',
    
    # Existing Components
    'render_alert_badge',
    'render_kpi_card',
    'render_sensor_chart',
    'render_golden_signals',
    'render_financial_section',
    'render_operativity_panel',
    'render_postmortem_panel',
    'render_station_line',
]
