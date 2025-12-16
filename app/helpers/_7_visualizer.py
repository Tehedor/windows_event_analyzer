# app/helpers/_7_visualizer.py
from pathlib import Path
from typing import Dict, Any
import re

import plotly.graph_objects as go
import yaml


# -------------------------------------------------------------------------
# Carga de metadatos
# -------------------------------------------------------------------------

def load_components(components_path: Path) -> dict:
    with components_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# -------------------------------------------------------------------------
# Utilidades de color
# -------------------------------------------------------------------------

def adjust_color_intensity(hex_color: str, percentile: int) -> str:
    """
    Ajusta la intensidad del color según el percentil destino.
    Q05 -> muy claro
    Q95 -> muy intenso
    """
    factor = percentile / 100.0

    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)

    return f"rgb({r},{g},{b})"


def parse_event_name(event_name: str) -> tuple[str, int]:
    """
    Devuelve:
    - componente base
    - percentil destino (Qxx)
    """

    # Caso transición: *_Qxx_to_Qyy
    if "_to_Q" in event_name:
        base, to_part = event_name.rsplit("_to_Q", 1)
        percentile = int(to_part)
        component = base.rsplit("_Q", 1)[0]
        return component, percentile

    # Caso simple: *_Qxx
    if "_Q" in event_name:
        component, q = event_name.rsplit("_Q", 1)
        percentile = int(q)
        return component, percentile

    raise ValueError(f"Formato de evento no reconocido: {event_name}")



# -------------------------------------------------------------------------
# Gráfico principal
# -------------------------------------------------------------------------

def plot_windows(
    df,
    event_id_map: Dict[int, str],
    components_cfg: Dict[str, Any],
    output_path: Path
):
    """
    Genera una imagen con las ventanas de observación/predicción.
    """

    fig = go.Figure()
    y = 0

    for _, row in df.iterrows():
        x = 0

        # --- OBSERVATION WINDOW ---
        for event_id in row["observation_events"]:
            event_name = event_id_map[event_id]
            component, percentile = parse_event_name(event_name)

            base_color = components_cfg["components"][component]["color"]
            color = adjust_color_intensity(base_color, percentile)

            fig.add_shape(
                type="rect",
                x0=x,
                x1=x + 1,
                y0=y,
                y1=y + 0.4,
                fillcolor=color,
                line=dict(width=0)
            )
            x += 1

        # Separador visual
        x += 0.5

        # --- PREDICTION WINDOW ---
        for event_id in row["prediction_events"]:
            event_name = event_id_map[event_id]
            component, percentile = parse_event_name(event_name)

            base_color = components_cfg["components"][component]["color"]
            color = adjust_color_intensity(base_color, percentile)

            fig.add_shape(
                type="rect",
                x0=x,
                x1=x + 1,
                y0=y,
                y1=y + 0.4,
                fillcolor=color,
                line=dict(width=0)
            )
            x += 1

        y += 1

    fig.update_layout(
        height=max(300, y * 80),
        width=1200,
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="white"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(output_path))
