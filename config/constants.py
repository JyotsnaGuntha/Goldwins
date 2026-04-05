"""
Configuration and constants for Microgrid Design Tool
"""

# ==================== ELECTRICAL CONSTANTS ====================
SYSTEM_VOLTAGE = 415  # V (3-phase)
POWER_FACTOR = 0.8  # Default PF for calculations
DG_POWER_FACTOR = 1.0  # DGs are rated in kVA, so PF = 1.0
SAFETY_FACTOR = 1.25  # 25% safety margin for MCCB selection

# ==================== STANDARD MCCB RATINGS ====================
STANDARD_MCCBS = [
    16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200,
    250, 315, 400, 500, 630, 800, 1000, 1250, 1600
]

# ==================== SVG DRAWING CONSTANTS ====================
SVG_WIDTH = 1450
SVG_HEIGHT = 850
SVG_BORDER_COLOR = "#334155"
SVG_BACKGROUND_COLOR = "#020617"

# Component spacing
COMPONENT_SPACING = 280  # Horizontal spacing between incomers
IC_START_X = 220  # Starting X position for incomers
Y_SOURCES = 180  # Y position for source symbols
Y_DIVISION = 380  # Division line between customer and scope
Y_BUSBAR = 600  # Y position for main busbar
OUTGOING_SPACING = 300  # Spacing for output feeders

# Colors for SVG
COLOR_WHITE = "white"
COLOR_GRID = "#60a5fa"  # Light blue
COLOR_SOLAR = "#fbbf24"  # Amber
COLOR_DG = "#60a5fa"  # Blue
COLOR_MCCB = "#10b981"  # Emerald (MCCB arc)
COLOR_BUSBAR = "#ef4444"  # Red
COLOR_MGC = "#a78bfa"  # Purple
COLOR_COMM = "#c4b5fd"  # Light purple

# ==================== PDF REPORT CONSTANTS ====================
PDF_MARGIN = 40
PDF_TITLE_FONTSIZE = 24
PDF_SECTION_FONTSIZE = 16
PDF_NORMAL_FONTSIZE = 10

# ==================== UI COLORS (Dark Theme) ====================
THEME_PRIMARY = "#7c3aed"  # Purple
THEME_PRIMARY_DARK = "#6d28d9"
THEME_SECONDARY = "#a78bfa"
THEME_TEXT_PRIMARY = "#f1f5f9"
THEME_TEXT_SECONDARY = "#cbd5e1"
THEME_BG_DARK = "#020617"
THEME_BG_CARD = "rgba(15, 23, 42, 0.8)"

# ==================== PANEL LAYOUT (GA) ====================
GA_PANEL_WIDTH = 600  # mm (physical panel width)
GA_PANEL_HEIGHT = 1200  # mm (physical panel height)
GA_MCCB_HEIGHT = 90  # mm (height of single MCCB pole)
GA_MCCB_WIDTH = 55  # mm (width of MCCB)
GA_COLUMN_GAP = 30  # Gap between MCCB columns
GA_BUSBAR_WIDTH = 50  # mm (busbar width)
GA_BUSBAR_THICKNESS = 10  # mm
