"""
Utility functions for storing and retrieving grid occupancy data.

This module stays intentionally lightweight so it can be reused by both the
prototype editor and any downstream consumers such as the A* navigation logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import json

# Type aliases keep call sites expressive while letting mypy/pyright infer list[int].
CellRow = List[int]
Grid = List[CellRow]

# Default location for the persisted grid. Callers may override this path when needed.
DEFAULT_GRID_PATH = Path("grid.json")


def _normalise_path(path: Path | str | None) -> Path:
    """
    Convert an optional path into a `Path` object, falling back to the default file.

    Keeping this small helper private avoids repeating the same None-handling logic in
    each API function while keeping their signatures easy to read.
    """
    if path is None:
        return DEFAULT_GRID_PATH
    return Path(path)


def load_grid(path: Path | str | None = None) -> Grid:
    """
    Load a grid from JSON. Returns an empty list when the file does not exist yet.

    The empty list gives callers the opportunity to decide how to seed a new grid
    (e.g. by creating a default sized matrix) without raising an exception.
    """
    grid_file = _normalise_path(path)
    if not grid_file.exists():
        return []

    with grid_file.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    # Defensively ensure the JSON unmarshals into the expected 2D list of ints.
    if not isinstance(data, list):
        raise ValueError(f"Invalid grid format in {grid_file}: expected outer list.")

    normalised: Grid = []
    for row_idx, row in enumerate(data):
        if not isinstance(row, Iterable):
            raise ValueError(f"Invalid grid row at index {row_idx}: must be iterable.")
        normalised_row: CellRow = []
        for col_idx, cell in enumerate(row):
            try:
                normalised_row.append(int(cell))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid cell value at ({row_idx}, {col_idx}): {cell!r}"
                ) from exc
        normalised.append(normalised_row)

    return normalised


def save_grid(grid: Grid, path: Path | str | None = None) -> None:
    """
    Persist the provided grid to JSON so other tools (like A*) can consume it.

    The function ensures the directory exists before writing to keep the prototype
    resilient when run from different working directories.
    """
    grid_file = _normalise_path(path)
    grid_file.parent.mkdir(parents=True, exist_ok=True)

    with grid_file.open("w", encoding="utf-8") as fp:
        json.dump(grid, fp, indent=2)


def get_grid(path: Path | str | None = None) -> Grid:
    """
    Convenience accessor that mirrors the eventual API A* will call.

    At the moment it simply forwards to `load_grid`, but keeping the indirection lets
    us later swap in an in-memory representation without changing the consumer code.
    """
    return load_grid(path)
