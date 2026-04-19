"""
General Arrangement helpers used by the desktop application.
"""

from src.ga.dimensions import compute_panel_dimensions
from src.ga.styles import get_ga_colors, get_color
from src.ga.generator import generate_ga_svg

__all__ = [
    "compute_panel_dimensions",
    "get_ga_colors",
    "get_color",
    "generate_ga_svg",
]
