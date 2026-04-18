"""
Panel Dimensioning Logic
Computes dynamic panel sizes based on MCCB database and clearances.
"""

import math
from ..constants import (
    PLINTH_H,
    PANEL_D,
    CABLE_DUCT_H,
    TOP_MARGIN_H,
    CLEARANCE_PP,
    CLEARANCE_PE,
    MCCB_COL_GAP,
    ROW_GAP_MM,
    SIDE_MARGIN,
    MIN_PANEL_WIDTH,
    MIN_PANEL_HEIGHT,
    DIMENSION_ROUNDING,
)
from ..utils import get_mccb_dims, get_busbar_chamber_height, get_busbar_thickness


def compute_panel_dimensions(incomer_mccbs, outgoing_mccbs, db, busbar_current_A):
    """
    Compute panel W × H (mm, real-world) from:
      • Actual MCCB footprints read from DB
      • Standard busbar chamber height (IEC 61439)
      • Minimum clearances and wiring duct

    Vertical stack on mounting plate (top → bottom):
      TOP_MARGIN_H        (clearance above incomers)
      Incomer MCCB height (tallest incomer)
      ROW_GAP_MM          (inter-row clearance)
      Busbar chamber      (get_busbar_chamber_height)
      ROW_GAP_MM
      Outgoing MCCB height (tallest outgoing, × rows if wrap)
      CABLE_DUCT_H        (wiring duct / gland plate zone)

    Returns:
        dict with all panel geometry values (all in mm)
    """
    busbar_ch_mm = get_busbar_chamber_height(busbar_current_A)

    # ── 1. Width calculation ──────────────────────────────────────────────────
    def row_width(ratings):
        if not ratings:
            return 0
        total = sum(get_mccb_dims(r, db)['w'] for r in ratings)
        total += MCCB_COL_GAP * (len(ratings) - 1)
        return total

    inc_row_w = row_width(incomer_mccbs)
    out_row_w = row_width(outgoing_mccbs)
    mount_w = max(inc_row_w, out_row_w) + SIDE_MARGIN * 2
    PANEL_W = math.ceil(max(MIN_PANEL_WIDTH, mount_w + 100) / DIMENSION_ROUNDING) * DIMENSION_ROUNDING

    # ── 2. Height calculation ─────────────────────────────────────────────────
    max_inc_h = max((get_mccb_dims(r, db)['h'] for r in incomer_mccbs), default=200)
    max_out_h = max((get_mccb_dims(r, db)['h'] for r in outgoing_mccbs), default=200)

    # Determine how many rows outgoing needs
    avail_w = PANEL_W - 100 - SIDE_MARGIN * 2
    out_rows = 1
    running = 0
    for r in outgoing_mccbs:
        w = get_mccb_dims(r, db)['w'] + MCCB_COL_GAP
        running += w
        if running > avail_w:
            out_rows += 1
            running = w

    mount_h = (
        TOP_MARGIN_H +
        max_inc_h +
        ROW_GAP_MM +
        busbar_ch_mm +
        ROW_GAP_MM +
        out_rows * (max_out_h + ROW_GAP_MM) +
        CABLE_DUCT_H
    )
    PANEL_H = math.ceil(max(MIN_PANEL_HEIGHT, mount_h + 200) / DIMENSION_ROUNDING) * DIMENSION_ROUNDING

    MOUNT_W = PANEL_W - 100
    MOUNT_H = PANEL_H - 100

    return {
        "PANEL_W":        PANEL_W,
        "PANEL_H":        PANEL_H,
        "PANEL_D":        PANEL_D,
        "MOUNT_W":        MOUNT_W,
        "MOUNT_H":        MOUNT_H,
        "PLINTH_H":       PLINTH_H,
        "BUSBAR_CH_MM":   busbar_ch_mm,
        "MAX_INC_H":      max_inc_h,
        "MAX_OUT_H":      max_out_h,
        "OUT_ROWS":       out_rows,
        "INC_ROW_W":      inc_row_w,
        "OUT_ROW_W":      out_row_w,
    }
