## Overlay Integration Checklist

This project already ships with a Python webcam prototype. The notes below list only
the changes needed to hook the same grid logic into the Unity overlay backed by the
GPS ortho camera.

### Provide the Overlay Frame
- Substitute the prototype’s `cv2.VideoCapture(0)` with the overlay render texture or
  camera output.
- Maintain a stable frame resolution; the grid sizing math expects consistent width ×
  height measurements each update.

### Align Grid Dimensions
- Let the overlay decide the authoritative `rows` and `cols`, then pass those into the
  editor logic so the JSON grid and the Unity visual grid align.
- Keep the `(row, col)` → world coordinate mapping fixed. Every index must correspond to
  the same arena tile across overlay, Python helpers, and A*.

### Forward Click Events
- Route overlay click callbacks to a handler that calls `grid[row][col] =
  1 - grid[row][col]`.
- Apply obstacle tinting through the overlay (FREE = baseline look, OBSTACLE =
  highlighted). The Python prototype’s draw routine shows the intended styling.

### Persist and Share the Grid
- Continue saving after edits with `save_grid(grid)`. The default location is
  `grid.json`, but you can override the path if needed.
- Consumers (A*) should call `get_grid()`; keep that as the public API even if you move
  the backing store into DOTS data.

### ECS / DOTS Considerations
- If toggles trigger structural ECS changes, enqueue them through an
  `EntityCommandBuffer` (or ParallelWriter) rather than mutating during query
  iteration.
- Cache any entity queries inside `OnCreate` and reuse them in `OnUpdate` to avoid
  per-frame allocations.

### Validation Before Shipping
- Overlay edits update the JSON grid and the live display in lockstep.
- A* reads the latest grid and correctly avoids OBSTACLE cells.
- Camera alignment is verified so a clicked cell always matches the expected arena
  region.

## Reusable Modules

- `src/grid_api.py` — production ready. Provides `load_grid`, `save_grid`, and
  `get_grid`. Works headless; can be called from Unity via Python bindings or reworked
  as a C# layer that honours the same JSON contract.
- `src/editor_prototype.py` — prototype only. Source of ideas for Unity integration, but
  the final overlay should implement its own rendering and input while reusing the grid
  persistence helpers.
