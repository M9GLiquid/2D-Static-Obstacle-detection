"""
Lightweight persistence helpers for the occupancy grid.

The functions defined here provide a stable contract for any tool that needs to read
or write the arena layout (prototype editor, A*, Unity integration, automated tests).
Grids are stored as JSON, using human-friendly symbols so designers can review or edit
files directly when needed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import json

# 2D grids are represented as lists of rows, each row containing integer cell states.
CellRow = List[int]
Grid = List[CellRow]

# Default location for the persisted grid. Callers may override this path when needed.
DEFAULT_GRID_PATH = Path("grid.json")

# Shared cell semantics so every subsystem interprets the same numeric values. The
# symbolic mapping keeps saved files easy to read while allowing consumers to work
# with integers in memory.
FREE = 0
OBSTACLE = 1
HOME = 2

SYMBOL_TO_CELL = {"O": FREE, "X": OBSTACLE, "H": HOME}
CELL_TO_SYMBOL = {value: key for key, value in SYMBOL_TO_CELL.items()}


def _normalise_path(path: Path | str | None) -> Path:
    """
    Convert an optional path into a `Path` object, falling back to the default file.

    Normalising paths in one place keeps the public functions concise and guarantees
    consistent behaviour when callers pass strings, `Path` objects, or nothing at all.
    """
    if path is None:
        return DEFAULT_GRID_PATH
    return Path(path)


def load_grid(path: Path | str | None = None) -> Grid:
    """
    Load a grid from JSON and return it as a matrix of integers.

    * Each cell letter is translated back into the canonical integer value.
    * Unknown or malformed data raises a descriptive `ValueError`.
    * When the file does not exist yet, an empty list is returned so the caller can
      decide how to initialise a fresh grid.
    """
    grid_file = _normalise_path(path)
    if not grid_file.exists():
        return []

    with grid_file.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    # Ensure the JSON structure is a list of rows.
    if not isinstance(data, list):
        raise ValueError(f"Invalid grid format in {grid_file}: expected outer list.")

    normalised: Grid = []
    for row_idx, row in enumerate(data):
        if not isinstance(row, Iterable):
            raise ValueError(f"Invalid grid row at index {row_idx}: must be iterable.")
        normalised_row: CellRow = []
        for col_idx, cell in enumerate(row):
            try:
                if isinstance(cell, str):
                    normalised_value = SYMBOL_TO_CELL[cell.upper()]
                else:
                    normalised_value = int(cell)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid cell value at ({row_idx}, {col_idx}): {cell!r}"
                ) from exc
            normalised_row.append(normalised_value)
        normalised.append(normalised_row)

    return normalised


def save_grid(grid: Grid, path: Path | str | None = None) -> None:
    """
    Persist the provided grid to JSON using human-readable cell symbols.

    Directories are created on demand so the call succeeds even when the chosen path
    does not exist yet.
    """
    grid_file = _normalise_path(path)
    grid_file.parent.mkdir(parents=True, exist_ok=True)

    serialisable = [
        [CELL_TO_SYMBOL.get(int(cell), "O") for cell in row] for row in grid
    ]

    with grid_file.open("w", encoding="utf-8") as fp:
        json.dump(serialisable, fp, indent=2)


def get_grid(path: Path | str | None = None) -> Grid:
    """
    Convenience accessor that returns the current grid using the default storage path.

    The indirection allows future implementations to swap the backing store without
    touching consumer code (e.g. in-memory cache, network source, Unity bridge).
    """
    return load_grid(path)
