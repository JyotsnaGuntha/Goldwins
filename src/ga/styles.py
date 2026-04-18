"""
GA Drawing Styles & Color Themes
Provides responsive color palettes for GA drawing based on theme.
"""

from ..constants import GA_COLORS_DARK, GA_COLORS_LIGHT


def get_ga_colors(theme="dark"):
    """
    Get GA drawing color palette based on theme.
    
    Args:
        theme: "dark" or "light"
    
    Returns:
        dict with all GA drawing colors
    """
    return GA_COLORS_DARK if theme == "dark" else GA_COLORS_LIGHT


def get_color(color_key, theme="dark"):
    """
    Convenience function to get single color by key.
    
    Args:
        color_key: Color key name (e.g., "bg", "shell", "text")
        theme: "dark" or "light"
    
    Returns:
        Color hex string
    """
    colors = get_ga_colors(theme)
    return colors.get(color_key, "#000000")
