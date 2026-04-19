from __future__ import annotations

import pandas as pd

from src.dashboard.views.premium_full_latest import render as render_executive


def render(df: pd.DataFrame) -> None:
    """
    Compatibilidad retroactiva:
    - Esta vista delega al Resumen Ejecutivo real.
    - Evita mantener duplicados con datos simulados.
    """
    render_executive(df)
