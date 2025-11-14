"""
Simple API for accessing the occupancy grid map with customizable symbols.

This API provides easy access to the grid map data stored in grid.json (located
in the same directory as this API), allowing users to retrieve the map with 
custom symbol representations.

The grid.json file is included in the api folder for easy distribution - just
copy the entire api folder to use this API.

Example:
    from map_api import get_map
    
    # Get map with default symbols (O, X, H)
    map_data = get_map()
    
    # Get map with custom symbols
    map_data = get_map(symbols={'FREE': '.', 'OBSTACLE': '#', 'HOME': '1'})
    
    # Get raw JSON data
    json_data = get_map_json()
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import json
import sys

# Add src directory to path to import grid_api
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.grid_api import load_grid, FREE, OBSTACLE, HOME

# Default path to grid.json (in the same directory as this API)
DEFAULT_MAP_PATH = Path(__file__).parent / "grid.json"

# Default symbol mapping
DEFAULT_SYMBOLS = {
    'FREE': 'O',
    'OBSTACLE': 'X', 
    'HOME': 'H'
}


def get_map_json(path: Path | str | None = None) -> Dict:
    """
    Get the raw JSON data from the grid file.
    
    Args:
        path: Optional path to grid.json. Defaults to "grid.json" in the api folder.
        
    Returns:
        Dictionary containing the raw JSON data, or empty dict if file doesn't exist.
        
    Example:
        json_data = get_map_json()
        print(json_data)  # Raw JSON structure
    """
    grid_path = Path(path) if path else DEFAULT_MAP_PATH
    
    if not grid_path.exists():
        return {}
    
    with grid_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def get_map(
    path: Path | str | None = None,
    symbols: Optional[Dict[str, str]] = None
) -> List[List[str]]:
    """
    Get the grid map as a 2D list with customizable symbols.
    
    Args:
        path: Optional path to grid.json. Defaults to "grid.json" in the api folder.
        symbols: Optional dictionary to customize symbols. Keys: 'FREE', 'OBSTACLE', 'HOME'
                 Defaults to {'FREE': 'O', 'OBSTACLE': 'X', 'HOME': 'H'}
                 
    Returns:
        2D list (rows x cols) where each cell is represented by the specified symbol.
        Returns empty list if grid file doesn't exist.
        
    Example:
        # Default symbols
        map_data = get_map()
        # Returns: [['O', 'O', 'X'], ['O', 'H', 'O'], ...]
        
        # Custom symbols
        map_data = get_map(symbols={'FREE': '.', 'OBSTACLE': '#', 'HOME': '1'})
        # Returns: [['.', '.', '#'], ['.', '1', '.'], ...]
    """
    grid = load_grid(path)
    
    if not grid:
        return []
    
    # Use custom symbols or defaults
    symbol_map = symbols if symbols else DEFAULT_SYMBOLS
    
    # Map cell values to symbols
    cell_to_symbol = {
        FREE: symbol_map.get('FREE', 'O'),
        OBSTACLE: symbol_map.get('OBSTACLE', 'X'),
        HOME: symbol_map.get('HOME', 'H')
    }
    
    # Convert grid to symbol representation
    return [
        [cell_to_symbol.get(cell, '?') for cell in row]
        for row in grid
    ]


def get_map_as_string(
    path: Path | str | None = None,
    symbols: Optional[Dict[str, str]] = None,
    separator: str = " "
) -> str:
    """
    Get the grid map as a formatted string.
    
    Args:
        path: Optional path to grid.json. Defaults to "grid.json" in the api folder.
        symbols: Optional dictionary to customize symbols. Keys: 'FREE', 'OBSTACLE', 'HOME'
        separator: String to separate cells in each row. Defaults to " ".
        
    Returns:
        Formatted string representation of the grid, one row per line.
        
    Example:
        map_str = get_map_as_string()
        print(map_str)
        # Output:
        # O O X O
        # O H O O
        # X X O O
        
        map_str = get_map_as_string(symbols={'HOME': '1'}, separator='')
        # Output:
        # OOXO
        # O1OO
        # XXOO
    """
    map_data = get_map(path, symbols)
    
    return "\n".join(
        separator.join(row) for row in map_data
    )


def get_map_info(path: Path | str | None = None) -> Dict:
    """
    Get information about the grid map (dimensions, cell counts, etc.).
    
    Args:
        path: Optional path to grid.json. Defaults to "grid.json" in the api folder.
        
    Returns:
        Dictionary with map information:
        {
            'rows': int,
            'cols': int,
            'total_cells': int,
            'free_count': int,
            'obstacle_count': int,
            'home_count': int,
            'exists': bool
        }
        
    Example:
        info = get_map_info()
        print(f"Map size: {info['rows']}x{info['cols']}")
        print(f"Obstacles: {info['obstacle_count']}")
    """
    grid = load_grid(path)
    
    if not grid:
        return {
            'rows': 0,
            'cols': 0,
            'total_cells': 0,
            'free_count': 0,
            'obstacle_count': 0,
            'home_count': 0,
            'exists': False
        }
    
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    
    free_count = sum(1 for row in grid for cell in row if cell == FREE)
    obstacle_count = sum(1 for row in grid for cell in row if cell == OBSTACLE)
    home_count = sum(1 for row in grid for cell in row if cell == HOME)
    
    return {
        'rows': rows,
        'cols': cols,
        'total_cells': rows * cols,
        'free_count': free_count,
        'obstacle_count': obstacle_count,
        'home_count': home_count,
        'exists': True
    }
