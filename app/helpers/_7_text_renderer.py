# app/helpers/_7_text_renderer.py

from typing import Dict, Any
import pandas as pd

from rich.console import Console
from rich.table import Table
from rich.text import Text


# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------

def render_windows_text(
    df: pd.DataFrame,
    event_dict: Dict[int, Dict[str, Any]],
    config: Dict[str, Any],
    limit: int = 20,
    offset: int = 0,
) -> None:
    """
    Renderiza ventanas en formato texto usando rich.
    """

    console = Console()

    obs_events_col = config["columns"]["observation"]["events"]
    pred_events_col = config["columns"]["prediction"]["events"]

    total = len(df)
    df_slice = df.iloc[offset : offset + limit]

    table = Table(
        title=f"Resultados ({offset}–{min(offset+limit, total)} / {total})",
        show_lines=True,
        expand=True,
    )

    table.add_column("#", justify="right", style="bold")
    table.add_column("OBSERVATION", justify="left")
    table.add_column("PREDICTION", justify="left")

    for idx, (_, row) in enumerate(df_slice.iterrows(), start=offset):
        obs_text = _render_event_sequence(row[obs_events_col], event_dict)
        pred_text = _render_event_sequence(row[pred_events_col], event_dict)

        table.add_row(
            str(idx),
            obs_text,
            pred_text,
        )

    console.print(table)


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _render_event_sequence(events: list[int], event_dict: Dict[int, Dict[str, Any]]) -> Text:
    """
    Renderiza una secuencia de eventos como texto coloreado.
    """
    text = Text()

    for event_id in events:
        info = event_dict.get(event_id)

        if info is None:
            # Evento desconocido
            text.append(f"{event_id} ", style="dim")
            continue

        color = info["final_color"]
        text.append(f"{event_id} ", style=color)

    return text
