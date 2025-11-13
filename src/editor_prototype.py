"""
Phase 1 prototype editor that overlays an editable occupancy grid on top of a webcam.

Keeping this prototype self-contained lets us validate the UX and data flow before
hooking it into the Unity overlay (Phase 2). The heavy lifting lives in `run_editor`
so that `main` can stay as a thin entrypoint for hardcoded prototype settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence
import cv2  # type: ignore

from grid_api import Grid, load_grid, save_grid, DEFAULT_GRID_PATH


@dataclass
class EditorState:
    """Simple container that shares context between the render loop and mouse handler."""

    grid: Grid
    rows: int
    cols: int
    cell_width: float = 1.0
    cell_height: float = 1.0
    auto_save: bool = True
    grid_path: Path = DEFAULT_GRID_PATH


def _seed_grid(rows: int, cols: int, persisted: Sequence[Sequence[int]]) -> Grid:
    """
    Build a grid with the requested dimensions, copying any persisted values that fit.

    The helper ensures that mismatched dimensions from older saves do not break the
    prototype; extra cells default back to FREE (0).
    """
    seeded = [[0 for _ in range(cols)] for _ in range(rows)]
    max_row = min(rows, len(persisted))
    for row_idx in range(max_row):
        row = persisted[row_idx]
        max_col = min(cols, len(row))
        for col_idx in range(max_col):
            seeded[row_idx][col_idx] = int(row[col_idx])
    return seeded


def _draw_grid_overlay(frame, state: EditorState) -> None:
    """
    Mutate the frame in-place so the user can see grid lines and obstacle highlights.
    """
    rows, cols = state.rows, state.cols
    height, width = frame.shape[:2]

    # Cache cell dimensions for the mouse handler (converted to floats for precision).
    state.cell_width = width / cols
    state.cell_height = height / rows

    tinted = frame.copy()
    for row_idx in range(rows):
        for col_idx in range(cols):
            if state.grid[row_idx][col_idx] != 1:
                continue
            top_left = (int(col_idx * state.cell_width), int(row_idx * state.cell_height))
            bottom_right = (
                int((col_idx + 1) * state.cell_width),
                int((row_idx + 1) * state.cell_height),
            )
            # Draw a semi-transparent rectangle for obstacles so the camera feed stays visible.
            cv2.rectangle(
                tinted,
                top_left,
                bottom_right,
                color=(30, 30, 30),  # Dark grey tint
                thickness=-1,  # Filled rectangle
            )

    # Blend tinted overlay back on top to keep the underlying video visible.
    cv2.addWeighted(tinted, 0.4, frame, 0.6, 0, dst=frame)

    # Draw grid lines on top to help with precise clicks.
    for col_idx in range(cols + 1):
        x = int(col_idx * state.cell_width)
        cv2.line(frame, (x, 0), (x, height), color=(255, 255, 255), thickness=1)
    for row_idx in range(rows + 1):
        y = int(row_idx * state.cell_height)
        cv2.line(frame, (0, y), (width, y), color=(255, 255, 255), thickness=1)


def _handle_mouse(event, x, y, _flags, state: EditorState) -> None:
    """Toggle the clicked cell and optionally write it back to disk immediately."""
    if event != cv2.EVENT_LBUTTONDOWN:
        return

    col = int(x // state.cell_width)
    row = int(y // state.cell_height)

    if not (0 <= row < state.rows and 0 <= col < state.cols):
        return

    # Simple toggle between FREE (0) and OBSTACLE (1).
    state.grid[row][col] = 1 - state.grid[row][col]

    if state.auto_save:
        save_grid(state.grid, state.grid_path)
        print(f"[auto-save] Updated cell ({row}, {col}) -> {state.grid[row][col]}")


def run_editor(rows: int, cols: int, *, grid_path: Path | str = DEFAULT_GRID_PATH) -> None:
    """
    Launch the Phase 1 webcam-based editor for the specified grid dimensions.

    This function owns the OpenCV lifecycle so the eventual Unity integration can reuse
    the grid logic without inheriting webcam setup code.
    """
    persisted = load_grid(grid_path)
    grid = _seed_grid(rows, cols, persisted)

    state = EditorState(
        grid=grid,
        rows=rows,
        cols=cols,
        grid_path=Path(grid_path),
    )

    window_name = "Mermaid AI Grid Editor"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, _handle_mouse, state)

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not access webcam. Check that a camera is connected.")

    print("Controls: left click to toggle, 's' to save, 'q' to quit.")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Failed to read frame from webcam. Exiting editor.")
                break

            _draw_grid_overlay(frame, state)
            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Quitting editor. Goodbye!")
                break
            if key == ord("s"):
                save_grid(state.grid, state.grid_path)
                print(f"Grid saved to {state.grid_path.resolve()}")
    finally:
        # Always release hardware and window resources, even when an exception bubbles up.
        camera.release()
        cv2.destroyWindow(window_name)


def main() -> None:
    """
    Hardcoded entry for the prototype stage.

    The constants can later be replaced with dimensions provided by the overlay module.
    """
    prototype_rows = 12
    prototype_cols = 16

    run_editor(prototype_rows, prototype_cols)


if __name__ == "__main__":
    main()
