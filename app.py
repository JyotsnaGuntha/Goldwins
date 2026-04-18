"""
Microgrid Panel SLD/GA/BOM Generator - Main Application
Refactored into modular components with clean separation of concerns.

Module Architecture:
  src/
  ├── constants.py          - All electrical standards & design constants
  ├── utils.py              - Shared utilities (MCCB loading, calculations)
  ├── sld/                  - Single Line Diagram
  │   ├── components.py     - MCCB, tower, solar drawing functions
  │   ├── calculations.py   - Electrical calculations
  │   └── generator.py      - Main SLD generation
  ├── ga/                   - General Arrangement
  │   ├── dimensions.py     - Panel sizing logic (IEC 61439)
  │   ├── styles.py         - Color themes for GA drawing
  │   └── generator.py      - Main GA generation
  └── bom/                  - Bill of Materials
      ├── generator.py      - BOM generation logic
      └── exports.py        - PDF and Excel export functions
"""

import streamlit as st
import pandas as pd
import math
import datetime
import io
import svgwrite as svg
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from svglib.svglib import svg2rlg

# Import from modular structure
from src.constants import (
    THEME_DARK, THEME_LIGHT, FALLBACK_MCCB_DB, STANDARD_MCCBS,
    PLINTH_H, PANEL_D, CABLE_DUCT_H, TOP_MARGIN_H, CLEARANCE_PP, CLEARANCE_PE,
    MCCB_COL_GAP, ROW_GAP_MM, SIDE_MARGIN, MIN_PANEL_WIDTH, MIN_PANEL_HEIGHT,
)
from src.utils import (
    load_mccb_dimensions_from_file,
    get_standard_rating,
    generate_busbar_spec,
    get_mccb_dims,
    get_busbar_chamber_height,
    get_busbar_thickness,
)
from src.sld.generator import generate_sld
from src.sld.calculations import SystemCalculations
from src.ga.generator import generate_ga_svg as generate_ga_svg_modular
from src.ga.dimensions import compute_panel_dimensions
from src.bom.generator import generate_bom_items
from src.bom.exports import (
    generate_pdf_report,
    generate_ga_pdf,
    generate_excel_bom,
)

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(page_title="Professional Microgrid SLD Generator", layout="wide")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "mccb_db" not in st.session_state:
    st.session_state.mccb_db = {}

# ============================================================================
# THEME SETUP (CSS & STYLING)
# ============================================================================
theme_colors = THEME_DARK if st.session_state.theme == "dark" else THEME_LIGHT
theme_bg = theme_colors["bg"]
theme_card = theme_colors["card"]
theme_text = theme_colors["text"]
theme_sub = theme_colors["subtitle"]
theme_border = theme_colors["border"]
theme_title = theme_colors["title"]
theme_svg_bg = theme_colors["svg_bg"]
theme_svg_stroke = theme_colors["svg_stroke"]

# Apply CSS styling
st.markdown(f"""
<style>
    .stApp {{ background: {theme_bg}; font-family: 'Inter', sans-serif; }}
    .main-title {{ text-align: center; font-size: 42px; font-weight: 800; color: {theme_title}; margin-bottom: 30px; }}
    .section-title {{ font-size: 22px; font-weight: 600; color: #19988b; margin-top: 25px; margin-bottom: 12px; border-bottom: 1px solid rgba(25,152,139,0.2); padding-bottom: 5px; }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color: #062a30 !important; font-weight: 800 !important; }}
    .stButton>button, [data-testid="stDownloadButton"]>button {{ background: linear-gradient(90deg,#19988b,#15803d) !important; color: white !important; border: none !important; padding: 12px 30px !important; border-radius: 8px !important; font-weight: 700 !important; }}
    .info-card {{ background: rgba(25,152,139,0.15); border-left: 4px solid #19988b; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: {theme_text}; }}
    .warning-card {{ background: rgba(239,68,68,0.1); border-left: 4px solid #ef4444; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #fca5a5; }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER & THEME TOGGLE
# ============================================================================
col_header, col_toggle = st.columns([0.9, 0.1])
with col_header:
    st.markdown(f'<div class="main-title">Microgrid Panel SLD Generator</div>', unsafe_allow_html=True)
with col_toggle:
    theme_icon = "🌞" if st.session_state.theme == "dark" else "🌙"
    if st.button(theme_icon, help="Toggle Light/Dark Theme", key="theme_toggle_btn"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

# SIDEBAR INPUTS
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Design Parameters")

    # ── MCCB Dimensions File Upload ────────────────────────────────────────
    with st.expander("📂 MCCB Dimensions (Excel)", expanded=True):
        st.markdown(
            "<div style='font-size:12px;color:#475569;margin-bottom:8px;'>"
            "Upload <b>Circuit_Breaker_Dimensions.xlsx</b>.<br>"
            "Expected columns: Frame | Rating | Poles | Height(mm) | Width(mm) | Depth(mm)<br>"
            "Data rows starting at row 5 (row 4 = header).</div>",
            unsafe_allow_html=True,
        )
        uploaded_mccb_xl = st.file_uploader(
            "MCCB Dimensions (.xlsx)",
            type=["xlsx"],
            key="mccb_xl_uploader",
            help="Circuit Breaker Dimensions Excel sheet"
        )
        if uploaded_mccb_xl is not None:
            db_loaded = load_mccb_dimensions_from_file(uploaded_file=uploaded_mccb_xl)
            if db_loaded:
                st.session_state.mccb_db = db_loaded
                st.success(f"✅ Loaded {len(db_loaded)} MCCB entries.")
                # Show preview table
                preview = [(k, v['h'], v['w'], v['d'], v['frame'])
                           for k, v in sorted(db_loaded.items())]
                df_prev = pd.DataFrame(preview, columns=["Rating(A)", "H(mm)", "W(mm)", "D(mm)", "Frame"])
                st.dataframe(df_prev, use_container_width=True, height=160)
            else:
                st.warning("⚠️ Could not parse file. Check format.")
        elif not st.session_state.mccb_db:
            st.info("ℹ️ No file — using built-in fallback dimensions.")

    # ── Busbar sizing info (auto-calculated per IEC 61439) ─────────────────
    with st.expander("ℹ️ Busbar Chamber (Auto-Calculated)", expanded=False):
        st.markdown(
            "<div style='font-size:12px;color:#475569;'>"
            "Busbar chamber height is automatically determined from total busbar current "
            "per IEC 61439 / OEM standards:<br>"
            "• ≤ 400 A → <b>100 mm</b><br>"
            "• 401–800 A → <b>150 mm</b><br>"
            "• &gt; 800 A → <b>200 mm</b><br><br>"
            "Busbar thickness:<br>"
            "• ≤ 400 A → 5 mm<br>"
            "• 401–800 A → 10 mm<br>"
            "• &gt; 800 A → 12 mm<br><br>"
            "Min clearances (IEC 61439):<br>"
            "• Phase–Phase ≥ 25 mm<br>"
            "• Phase–Earth ≥ 20 mm"
            "</div>",
            unsafe_allow_html=True,
        )

    with st.expander("Capacity Inputs", expanded=True):
        solar_kw   = st.number_input("Solar (kWp)",    value=100, min_value=0)
        grid_kw    = st.number_input("Grid (kW)",       value=120, min_value=0)
        num_dg     = st.number_input("Number of DGs",   value=2,   min_value=0, max_value=4)
        dg_ratings = []
        if num_dg > 0:
            st.markdown("<div style='font-size:13px;color:#64748b;margin-top:5px;margin-bottom:5px;'>DG Specifications</div>", unsafe_allow_html=True)
            for i in range(int(num_dg)):
                dg = st.number_input(f"DG {i+1} Rating (kVA)", value=250, key=f"dg_in_{i}")
                dg_ratings.append(dg)

        num_outputs = st.number_input("Outgoing Feeders", value=3, min_value=1, max_value=10)
        mccb_outputs = []
        if num_outputs > 0:
            st.markdown("<div style='font-size:13px;color:#64748b;margin-top:5px;margin-bottom:5px;'>Outgoing Feeder Specifications (Amperes)</div>", unsafe_allow_html=True)
            for i in range(int(num_outputs)):
                default_val = 400 if i < 2 else 250
                out_r = st.number_input(f"O/G {i+1} Rating (Amp)", value=default_val, key=f"og_in_{i}", min_value=0)
                mccb_outputs.append(get_standard_rating(out_r))

        busbar_material = st.selectbox("Busbar Material", ["Copper", "Aluminium"], index=1)
        num_poles       = st.selectbox("System Phases/Poles", [3, 4], index=1)

    st.divider()
    if st.button("Generate Final SLD & BOM", use_container_width=True, type="primary"):
        st.session_state.submitted = True

# ──────────────────────────────────────────────────────────────────────────────
# CORE CALCULATIONS
# ──────────────────────────────────────────────────────────────────────────────

def get_mccb_rating(current):
    required = current * 1.25
    for rating in STANDARD_MCCBS:
        if rating >= required:
            return rating
    return STANDARD_MCCBS[-1]

V  = 415
PF = 0.8

i_solar    = (solar_kw * 1000) / (math.sqrt(3) * V * PF) if solar_kw > 0 else 0
mccb_solar = get_mccb_rating(i_solar) if solar_kw > 0 else 0

i_grid    = (grid_kw * 1000) / (math.sqrt(3) * V * PF) if grid_kw > 0 else 0
mccb_grid = get_mccb_rating(i_grid) if grid_kw > 0 else 0

dg_mccbs    = []
dg_currents = []
for dg in dg_ratings:
    i = (dg * 1000) / (math.sqrt(3) * V)
    dg_currents.append(i)
    dg_mccbs.append(get_mccb_rating(i))

total_busbar_current  = i_solar + i_grid + sum(dg_currents)
total_outgoing_rating = sum(mccb_outputs)

density     = 1.6 if busbar_material == "Copper" else 1.0
busbar_area = total_busbar_current / density
suggested_width = math.ceil(busbar_area / 10 / 5) * 5
if suggested_width < 20:
    suggested_width = 20
busbar_spec = f"1 Set ({suggested_width} x 20 mm {busbar_material})"

# ──────────────────────────────────────────────────────────────────────────────
# DRAWING HELPERS (SLD)
# ──────────────────────────────────────────────────────────────────────────────

def draw_mccb(dwg, x, y, rating, poles, label, side="left"):
    dwg.add(dwg.line(start=(x, y - 50), end=(x, y - 18), stroke=theme_text, stroke_width=2))
    dwg.add(dwg.line(start=(x, y + 12), end=(x, y + 50), stroke=theme_text, stroke_width=2))
    dwg.add(dwg.path(d=f"M{x},{y-18} A14,14 0 0,0 {x+2},{y+12}", stroke="#10b981", fill="none", stroke_width=2.5))
    if side == "left":
        info_x, anchor        = x - 25, "end"
        label_x, label_anchor = x + 35, "start"
    else:
        info_x, anchor        = x + 25, "start"
        label_x, label_anchor = x - 35, "end"
    dwg.add(dwg.text(f"{rating} A, {poles}pole,", insert=(info_x, y - 5),    font_size=12, fill=theme_text, text_anchor=anchor, font_family="Arial"))
    dwg.add(dwg.text("Motorised MCCB",            insert=(info_x, y + 12),   font_size=11, fill=theme_sub,  text_anchor=anchor, font_family="Arial"))
    dwg.add(dwg.text(label,                        insert=(label_x, y + 5),  font_size=14, font_weight="bold", fill=theme_text, text_anchor=label_anchor, font_family="Arial"))

def draw_tower(dwg, x, y):
    h = 90; w = 25
    dwg.add(dwg.line((x, y-5), (x-w, y+h), stroke=theme_text, stroke_width=2))
    dwg.add(dwg.line((x, y-5), (x+w, y+h), stroke=theme_text, stroke_width=2))
    dwg.add(dwg.line((x-w, y+h), (x+w, y+h), stroke=theme_text, stroke_width=2))
    arm_y = [y+15, y+40, y+65]; arm_w = [18, 28, 24]
    for i in range(3):
        dwg.add(dwg.line((x-arm_w[i], arm_y[i]), (x+arm_w[i], arm_y[i]), stroke=theme_text, stroke_width=2))
        dwg.add(dwg.line((x-arm_w[i], arm_y[i]), (x-arm_w[i], arm_y[i]+8), stroke=theme_text, stroke_width=1.2))
        dwg.add(dwg.line((x+arm_w[i], arm_y[i]), (x+arm_w[i], arm_y[i]+8), stroke=theme_text, stroke_width=1.2))
    for i in range(len(arm_y)-1):
        y1,y2 = arm_y[i],arm_y[i+1]; w1,w2 = arm_w[i],arm_w[i+1]
        dwg.add(dwg.line((x-w1,y1),(x+w2,y2), stroke=theme_text, stroke_width=0.8, stroke_opacity=0.4))
        dwg.add(dwg.line((x+w1,y1),(x-w2,y2), stroke=theme_text, stroke_width=0.8, stroke_opacity=0.4))

def draw_solar(dwg, x, y):
    dwg.add(dwg.path(d=f"M{x-20},{y+55} L{x+20},{y+55} L{x+30},{y+20} L{x-30},{y+20} Z", fill="#1e293b", stroke=theme_text, stroke_width=2))
    for i in range(1,4):
        h_y = y+20+i*(35/4)
        dwg.add(dwg.line((x-30+i*2.5, h_y),(x+30-i*2.5,h_y), stroke=theme_text, stroke_opacity=0.4))
    dwg.add(dwg.line((x, y+20),(x, y+55), stroke=theme_text, stroke_opacity=0.4))
    dwg.add(dwg.line((x-10,y+20),(x-8,y+55), stroke=theme_text, stroke_opacity=0.4))
    dwg.add(dwg.line((x+10,y+20),(x+8,y+55), stroke=theme_text, stroke_opacity=0.4))
    cx,cy = x-25, y-5
    dwg.add(dwg.circle(center=(cx,cy), r=10, stroke="#fbbf24", fill="none", stroke_width=2.5))
    for i in range(8):
        angle = i*45; r1,r2 = 12,17
        x1=cx+r1*math.cos(math.radians(angle)); y1=cy+r1*math.sin(math.radians(angle))
        x2=cx+r2*math.cos(math.radians(angle)); y2=cy+r2*math.sin(math.radians(angle))
        dwg.add(dwg.line((x1,y1),(x2,y2), stroke="#fbbf24", stroke_width=1.5))

def draw_mgc(dwg, x, y):
    size=100
    dwg.add(dwg.rect(insert=(x,y), size=(size,size), fill="#1e1b4b", stroke="#a78bfa", stroke_width=3, rx=8))
    dwg.add(dwg.rect(insert=(x+15,y+15), size=(70,70), fill="none", stroke="#a78bfa", stroke_width=2))
    pin_len=12; spacing=size/7
    for i in range(1,7):
        pos=i*spacing
        dwg.add(dwg.line((x+pos,y-pin_len),(x+pos,y), stroke="#a78bfa", stroke_width=2.5))
        dwg.add(dwg.line((x+pos,y+size),(x+pos,y+size+pin_len), stroke="#a78bfa", stroke_width=2.5))
        dwg.add(dwg.line((x-pin_len,y+pos),(x,y+pos), stroke="#a78bfa", stroke_width=2.5))
        dwg.add(dwg.line((x+size,y+pos),(x+size+pin_len,y+pos), stroke="#a78bfa", stroke_width=2.5))
    dwg.add(dwg.text("MGC", insert=(x+size/2,y+size/2+8), font_size=20, fill="white", font_weight="bold", text_anchor="middle"))

# ──────────────────────────────────────────────────────────────────────────────
# GA DRAWING GENERATOR  (dynamic panel size + dynamic MCCB dims from DB)
# ──────────────────────────────────────────────────────────────────────────────

def generate_ga_svg(incomer_mccbs, outgoing_mccbs, busbar_current, busbar_spec_text,
                    num_poles_val, busbar_material, mccb_db):
    """
    Engineering GA drawing (clean shell, dimension arrows, spec box).
    Panel geometry computed entirely from:
      - MCCB dimensions read from Excel (mccb_db)
      - Busbar chamber height per IEC 61439 (get_busbar_chamber_height)
      - Standard clearance/margin constants
    No hardcoded dimensions anywhere.
    """
    # ────────────────────────────────────────────────────────────────────────
    # 1. Compute all real-world mm dimensions
    # ────────────────────────────────────────────────────────────────────────
    pd_info      = compute_panel_dimensions(incomer_mccbs, outgoing_mccbs,
                                            mccb_db, busbar_current)
    PANEL_W      = pd_info["PANEL_W"]
    PANEL_H      = pd_info["PANEL_H"]
    PANEL_D_     = pd_info["PANEL_D"]
    MOUNT_W      = pd_info["MOUNT_W"]
    MOUNT_H      = pd_info["MOUNT_H"]
    BUSBAR_CH    = pd_info["BUSBAR_CH_MM"]      # busbar chamber height  (mm)
    MAX_INC_H    = pd_info["MAX_INC_H"]         # tallest incomer MCCB   (mm)
    MAX_OUT_H    = pd_info["MAX_OUT_H"]         # tallest outgoing MCCB  (mm)
    OUT_ROWS     = pd_info["OUT_ROWS"]
    busbar_thick = get_busbar_thickness(busbar_current)

    # Mounting-plate internal zones (all in mm, top-to-bottom):
    #   TOP_MARGIN_H  →  incomer MCCBs  →  ROW_GAP_MM
    #   →  busbar chamber  →  ROW_GAP_MM
    #   →  outgoing MCCBs (× OUT_ROWS)  →  CABLE_DUCT_H
    zone_top_margin   = TOP_MARGIN_H
    zone_incomer      = MAX_INC_H
    zone_gap1         = ROW_GAP_MM
    zone_busbar       = BUSBAR_CH
    zone_gap2         = ROW_GAP_MM
    zone_outgoing     = OUT_ROWS * (MAX_OUT_H + ROW_GAP_MM)
    zone_cable_duct   = CABLE_DUCT_H

    # ────────────────────────────────────────────────────────────────────────
    # 2. SVG canvas & scale factors
    # ────────────────────────────────────────────────────────────────────────
    SVG_W = 1500
    SVG_H = 940

    # Drawing areas (px):  LEFT_MARGIN | FRONT | GAP | SIDE | RIGHT
    LEFT_MARGIN  = 120   # room for vertical dim arrows
    FRONT_MAX_W  = 680   # max px width for front elevation
    ELEV_GAP     = 70    # gap between front and side elevation
    SIDE_MAX_W   = 140   # max px width for side elevation
    BOTTOM_STRIP = 46    # title strip height at bottom

    # Scale: fit front view into FRONT_MAX_W × (SVG_H – top/bottom space)
    AVAIL_H   = SVG_H - 100 - BOTTOM_STRIP   # leave 100 px top for dim lines
    SCALE     = min(FRONT_MAX_W / PANEL_W, AVAIL_H / (PANEL_H + PLINTH_H))
    # Side uses same vertical scale but independent horizontal scale
    SCALE_S   = min(SIDE_MAX_W / PANEL_D_, SCALE)

    # Pixel sizes
    def mm(val):    return val * SCALE          # real mm → px
    def mm_s(val):  return val * SCALE_S        # side depth → px

    pF_W  = mm(PANEL_W)
    pF_H  = mm(PANEL_H)
    pF_PL = mm(PLINTH_H)
    pF_D  = mm_s(PANEL_D_)

    mF_W  = mm(MOUNT_W)
    mF_H  = mm(MOUNT_H)

    # Zone heights in pixels (front view)
    z_top  = mm(zone_top_margin)
    z_inc  = mm(zone_incomer)
    z_gap1 = mm(zone_gap1)
    z_bb   = mm(zone_busbar)
    z_gap2 = mm(zone_gap2)
    z_out  = mm(zone_outgoing)
    z_cd   = mm(zone_cable_duct)

    # Positioning
    TOP_Y   = 90         # px from top where panel body starts
    FRONT_X = LEFT_MARGIN
    SIDE_X  = FRONT_X + pF_W + ELEV_GAP

    # Mounting plate top-left inside front view
    mp_x = FRONT_X + (pF_W - mF_W) / 2
    mp_y = TOP_Y   + (pF_H - mF_H) / 2

    # ────────────────────────────────────────────────────────────────────────
    # 3. Colours (Responsive to Theme)
    # ────────────────────────────────────────────────────────────────────────
    if st.session_state.get('theme', 'dark') == 'dark':
        BG       = "#0a0f1e"
        SHELL    = "#1a2e4a"
        STROKE   = "#4a9eca"
        DIM_C    = "#f59e0b"
        TEXT_C   = "#e2e8f0"
        HATCH_C  = "#1e4080"
        MP_C     = "#0d1f36"
        BB_C     = "#7f1d1d"       # busbar chamber fill
        BB_ST    = "#ef4444"       # busbar chamber stroke
        ZONE_ST  = "#2563eb"       # zone separator dashes
        SPEC_BG  = "#0b1929"
        SPEC_BD  = "#2dd4bf"
        HEAD_C   = "#2dd4bf"
        SUB_C    = "#94a3b8"
        GRID_C   = "#1e3252"
    else:
        BG       = "#ffffff"
        SHELL    = "#e2e8f0"
        STROKE   = "#64748b"
        DIM_C    = "#d97706"
        TEXT_C   = "#0f172a"
        HATCH_C  = "#cbd5e1"
        MP_C     = "#f1f5f9"
        BB_C     = "#fee2e2"
        BB_ST    = "#f87171"
        ZONE_ST  = "#94a3b8"
        SPEC_BG  = "#ffffff"
        SPEC_BD  = "#19988b"
        HEAD_C   = "#19988b"
        SUB_C    = "#64748b"
        GRID_C   = "#cbd5e1"

    dwg = svg.Drawing(size=(SVG_W, SVG_H), profile="full")
    dwg.viewbox(0, 0, SVG_W, SVG_H)
    dwg.add(dwg.rect((0, 0), (SVG_W, SVG_H), fill=BG))

    # ────────────────────────────────────────────────────────────────────────
    # 4. Helper functions
    # ────────────────────────────────────────────────────────────────────────
    def arr_h(x1, x2, y, label, above=True):
        """Horizontal dim arrow with ticked ends."""
        sign = -1 if above else 1
        lbl_y = y + sign * 14
        dwg.add(dwg.line((x1, y), (x2, y), stroke=DIM_C, stroke_width=1.3))
        for (tx, flip) in [(x1, 1), (x2, -1)]:
            dwg.add(dwg.line((tx, y-5), (tx, y+5), stroke=DIM_C, stroke_width=1.3))
            dwg.add(dwg.polygon([(tx, y), (tx+flip*10, y-4), (tx+flip*10, y+4)], fill=DIM_C))
        dwg.add(dwg.text(label, insert=((x1+x2)/2, lbl_y),
                         font_size=11, fill=DIM_C, text_anchor="middle",
                         font_family="Arial", font_weight="bold"))

    def arr_v(x, y1, y2, label, right=True):
        """Vertical dim arrow with ticked ends + rotated label."""
        sign = 1 if right else -1
        lbl_x = x + sign * 18
        mid_y = (y1 + y2) / 2
        dwg.add(dwg.line((x, y1), (x, y2), stroke=DIM_C, stroke_width=1.3))
        for (ty, flip) in [(y1, 1), (y2, -1)]:
            dwg.add(dwg.line((x-5, ty), (x+5, ty), stroke=DIM_C, stroke_width=1.3))
            dwg.add(dwg.polygon([(x, ty), (x-4, ty+flip*10), (x+4, ty+flip*10)], fill=DIM_C))
        g = dwg.g(transform=f"rotate(-90,{lbl_x},{mid_y})")
        g.add(dwg.text(label, insert=(lbl_x, mid_y + 4),
                       font_size=11, fill=DIM_C, text_anchor="middle",
                       font_family="Arial", font_weight="bold"))
        dwg.add(g)

    def ext_h(x, y_from, y_to):
        """Horizontal witness/extension line (dashed, vertical)."""
        dwg.add(dwg.line((x, y_from), (x, y_to),
                         stroke=DIM_C, stroke_width=0.6, stroke_dasharray="4,3"))

    def ext_v(y, x_from, x_to):
        """Vertical witness line (dashed, horizontal)."""
        dwg.add(dwg.line((x_from, y), (x_to, y),
                         stroke=DIM_C, stroke_width=0.6, stroke_dasharray="4,3"))

    def hatch(rx, ry, rw, rh, step=10):
        """Diagonal hatch fill clipped to rect."""
        cid = f"cl_{int(rx)}_{int(ry)}_{int(rw)}"
        clip = dwg.defs.add(dwg.clipPath(id=cid))
        clip.add(dwg.rect(insert=(rx, ry), size=(rw, rh)))
        g = dwg.g(clip_path=f"url(#{cid})")
        span = rw + rh
        for d in range(-int(span), int(span), step):
            g.add(dwg.line((rx+d, ry), (rx+d+rh, ry+rh),
                           stroke=HATCH_C, stroke_width=0.7, stroke_opacity="0.4"))
        dwg.add(g)

    def zone_label(label, x, y, w, h, fill=TEXT_C, fs=9):
        """Centred text in a zone."""
        dwg.add(dwg.text(label, insert=(x + w/2, y + h/2 + fs/3),
                         font_size=fs, fill=fill, text_anchor="middle",
                         font_family="Arial", font_style="italic"))

    # ────────────────────────────────────────────────────────────────────────
    # 5. Grid columns (across front view, based on max MCCBs per row)
    # ────────────────────────────────────────────────────────────────────────
    n_cols = max(len(incomer_mccbs), len(outgoing_mccbs), 4)
    col_px = pF_W / n_cols
    for i in range(n_cols + 1):
        gx = FRONT_X + i * col_px
        dwg.add(dwg.line((gx, TOP_Y - 28), (gx, TOP_Y + pF_H + pF_PL + 8),
                         stroke=GRID_C, stroke_width=0.4, stroke_dasharray="3,5"))
    for i in range(n_cols):
        gx = FRONT_X + (i + 0.5) * col_px
        dwg.add(dwg.text(str(i), insert=(gx, TOP_Y - 32),
                         font_size=9, fill=SUB_C, text_anchor="middle", font_family="Arial"))

    # ────────────────────────────────────────────────────────────────────────
    # 6. FRONT ELEVATION — outer shell + plinth
    # ────────────────────────────────────────────────────────────────────────
    plinth_y = TOP_Y + pF_H
    # Plinth
    dwg.add(dwg.rect(insert=(FRONT_X, plinth_y), size=(pF_W, pF_PL),
                     fill="#08121f", stroke=STROKE, stroke_width=1.5))
    hatch(FRONT_X, plinth_y, pF_W, pF_PL, step=12)
    # Panel body
    dwg.add(dwg.rect(insert=(FRONT_X, TOP_Y), size=(pF_W, pF_H),
                     fill=SHELL, stroke=STROKE, stroke_width=2.5))
    # Door bezel
    bz = 10
    dwg.add(dwg.rect(insert=(FRONT_X+bz, TOP_Y+bz), size=(pF_W-2*bz, pF_H-2*bz),
                     fill="none", stroke="#2563eb", stroke_width=0.9, stroke_dasharray="8,5"))
    # Mounting plate outline (dashed, no content inside)
    dwg.add(dwg.rect(insert=(mp_x, mp_y), size=(mF_W, mF_H),
                     fill=MP_C, stroke="#3b82f6", stroke_width=1.1, stroke_dasharray="6,4"))

    # ── Internal zone dividers (dashed lines showing internal layout zones) ──
    # These are drawn inside the mounting plate to show the zones without labelling contents
    cur_y = mp_y

    # Zone 1: top margin
    cur_y += z_top
    # Zone 2: incomer row top
    inc_top = cur_y
    cur_y += z_inc
    inc_bot = cur_y
    # separator after incomers
    dwg.add(dwg.line((mp_x+5, inc_bot), (mp_x+mF_W-5, inc_bot),
                     stroke=ZONE_ST, stroke_width=0.7, stroke_dasharray="5,3"))

    cur_y += z_gap1
    # Zone 3: busbar chamber
    bb_top = cur_y
    bb_bot = cur_y + z_bb
    # Busbar chamber — distinct fill
    dwg.add(dwg.rect(insert=(mp_x+5, bb_top), size=(mF_W-10, z_bb),
                     fill=BB_C, stroke=BB_ST, stroke_width=1.2, rx=2))
    # Busbar label (inside chamber, centred)
    bb_label = f"Busbar Chamber — {BUSBAR_CH} mm"
    dwg.add(dwg.text(bb_label,
                     insert=(mp_x + mF_W/2, bb_top + z_bb/2 + 4),
                     font_size=min(10, max(8, z_bb * 0.35)),
                     fill="#fca5a5", text_anchor="middle",
                     font_family="Arial", font_weight="bold"))
    cur_y = bb_bot

    # separator after busbar
    dwg.add(dwg.line((mp_x+5, bb_bot), (mp_x+mF_W-5, bb_bot),
                     stroke=ZONE_ST, stroke_width=0.7, stroke_dasharray="5,3"))
    cur_y += z_gap2

    # Zone 4: outgoing row(s)
    out_top = cur_y
    cur_y += z_out
    out_bot = cur_y
    dwg.add(dwg.line((mp_x+5, out_bot), (mp_x+mF_W-5, out_bot),
                     stroke=ZONE_ST, stroke_width=0.7, stroke_dasharray="5,3"))

    # Zone 5: cable duct — hatched
    duct_y = out_bot
    hatch(mp_x+5, duct_y, mF_W-10, z_cd, step=8)
    dwg.add(dwg.rect(insert=(mp_x+5, duct_y), size=(mF_W-10, z_cd),
                     fill="none", stroke=ZONE_ST, stroke_width=0.7, stroke_dasharray="5,3"))
    zone_label("Cable Duct / Gland Plate", mp_x, duct_y, mF_W, z_cd, fill=SUB_C, fs=9)

    # Large HMI / Display (Centered with margins, constrained to avoid bottom overlap)
    hmi_m = 35
    hmi_x = FRONT_X + pF_W/2 + hmi_m
    hmi_w = (pF_W/2 - bz) - 2 * hmi_m
    hmi_y = TOP_Y + bz + hmi_m
    # Use inc_bot (calculated line 711) to define the bottom limit with a margin
    hmi_h = inc_bot - hmi_y - hmi_m
    
    dwg.add(dwg.rect(insert=(hmi_x, hmi_y), size=(hmi_w, hmi_h),
                     fill="#0a1a2e", stroke="#3b82f6", stroke_width=1.8, rx=8))
    dwg.add(dwg.text("HMI / DISPLAY",
                     insert=(hmi_x + hmi_w/2, hmi_y + hmi_h/2 + 6),
                     font_size=13, fill="#60a5fa", text_anchor="middle",
                     font_family="Arial", font_weight="bold"))

    # Labels
    dwg.add(dwg.text("FRONT ELEVATION",
                     insert=(FRONT_X + pF_W/2, TOP_Y + pF_H + pF_PL + 20),
                     font_size=12, fill=TEXT_C, text_anchor="middle",
                     font_family="Arial", font_weight="bold"))

    # ────────────────────────────────────────────────────────────────────────
    # 7. SIDE ELEVATION
    # ────────────────────────────────────────────────────────────────────────
    dwg.add(dwg.rect(insert=(SIDE_X, plinth_y), size=(pF_D, pF_PL),
                     fill="#08121f", stroke=STROKE, stroke_width=1.5))
    hatch(SIDE_X, plinth_y, pF_D, pF_PL, step=12)
    dwg.add(dwg.rect(insert=(SIDE_X, TOP_Y), size=(pF_D, pF_H),
                     fill=SHELL, stroke=STROKE, stroke_width=2.5))
    dwg.add(dwg.rect(insert=(SIDE_X+bz, TOP_Y+bz), size=(pF_D-2*bz, pF_H-2*bz),
                     fill="none", stroke="#2563eb", stroke_width=0.9, stroke_dasharray="8,5"))
    dwg.add(dwg.text("SIDE ELEVATION",
                     insert=(SIDE_X + pF_D/2, TOP_Y + pF_H + pF_PL + 20),
                     font_size=12, fill=TEXT_C, text_anchor="middle",
                     font_family="Arial", font_weight="bold"))

    # ────────────────────────────────────────────────────────────────────────
    # 8. Dimension arrows — all tied to real mm values
    # ────────────────────────────────────────────────────────────────────────

    # ── Panel width (above front view) ──
    dim_y_top = TOP_Y - 44
    ext_h(FRONT_X,        TOP_Y - 5, dim_y_top + 2)
    ext_h(FRONT_X + pF_W, TOP_Y - 5, dim_y_top + 2)
    arr_h(FRONT_X, FRONT_X + pF_W, dim_y_top, f"{PANEL_W} mm")

    # ── Panel height (left of front view, body only) ──
    dim_x_H = FRONT_X - 60
    ext_v(TOP_Y,          FRONT_X - 5, dim_x_H + 2)
    ext_v(TOP_Y + pF_H,   FRONT_X - 5, dim_x_H + 2)
    arr_v(dim_x_H, TOP_Y, TOP_Y + pF_H, f"{PANEL_H} mm", right=False)

    # ── Plinth height (left, immediately below body) ──
    dim_x_PL = FRONT_X - 35
    ext_v(TOP_Y + pF_H,        FRONT_X - 5, dim_x_PL + 2)
    ext_v(TOP_Y + pF_H + pF_PL, FRONT_X - 5, dim_x_PL + 2)
    arr_v(dim_x_PL, TOP_Y + pF_H, TOP_Y + pF_H + pF_PL, f"{PLINTH_H} mm", right=False)

    # ── Depth (above side view) ──
    ext_h(SIDE_X,        TOP_Y - 5, dim_y_top + 2)
    ext_h(SIDE_X + pF_D, TOP_Y - 5, dim_y_top + 2)
    arr_h(SIDE_X, SIDE_X + pF_D, dim_y_top, f"{PANEL_D_} mm")

    # ── Mounting plate width (below mounting plate) ──
    mp_dim_y = mp_y + mF_H + 18
    if mp_dim_y < TOP_Y + pF_H - 10:   # only draw if fits inside panel
        ext_h(mp_x,        mp_y + mF_H + 3, mp_dim_y + 2)
        ext_h(mp_x + mF_W, mp_y + mF_H + 3, mp_dim_y + 2)
        arr_h(mp_x, mp_x + mF_W, mp_dim_y, f"MP: {MOUNT_W} mm", above=False)

    # ── Mounting plate height (right of mounting plate) ──
    mp_dim_x = mp_x + mF_W + 30
    if mp_dim_x < FRONT_X + pF_W - 5:
        ext_v(mp_y,        mp_x + mF_W + 3, mp_dim_x - 2)
        ext_v(mp_y + mF_H, mp_x + mF_W + 3, mp_dim_x - 2)
        arr_v(mp_dim_x, mp_y, mp_y + mF_H, f"MP: {MOUNT_H} mm", right=True)

    # ── Busbar chamber height (right side, inside panel) ──
    bb_dim_x = FRONT_X + pF_W + 12
    ext_v(bb_top, FRONT_X + pF_W, bb_dim_x - 2)
    ext_v(bb_bot, FRONT_X + pF_W, bb_dim_x - 2)
    arr_v(bb_dim_x, bb_top, bb_bot, f"BB: {BUSBAR_CH} mm", right=True)

    # ── Incomer zone height ──
    inc_dim_x = FRONT_X + pF_W + 32
    ext_v(inc_top, FRONT_X + pF_W, inc_dim_x - 2)
    ext_v(inc_bot, FRONT_X + pF_W, inc_dim_x - 2)
    arr_v(inc_dim_x, inc_top, inc_bot, f"I/C: {MAX_INC_H} mm", right=True)

    # ────────────────────────────────────────────────────────────────────────
    # 9. SPEC BOX — bottom-right corner
    # ────────────────────────────────────────────────────────────────────────
    SB_W = 345
    SB_H = 240
    SB_X = SVG_W - SB_W - 16
    SB_Y = SVG_H - SB_H - BOTTOM_STRIP - 10

    dwg.add(dwg.rect(insert=(SB_X, SB_Y), size=(SB_W, SB_H),
                     fill=SPEC_BG, stroke=SPEC_BD, stroke_width=1.8, rx=4))
    # Header
    hdr_h = 26
    dwg.add(dwg.rect(insert=(SB_X, SB_Y), size=(SB_W, hdr_h),
                     fill="#0d3a4a", stroke="none", rx=4))
    dwg.add(dwg.line((SB_X, SB_Y+hdr_h), (SB_X+SB_W, SB_Y+hdr_h),
                     stroke=SPEC_BD, stroke_width=0.8))
    dwg.add(dwg.text("PANEL GA DRAWING — SPECIFICATIONS",
                     insert=(SB_X+SB_W/2, SB_Y+hdr_h/2+5),
                     font_size=11, fill=SPEC_BD, text_anchor="middle",
                     font_family="Arial", font_weight="bold"))

    specs = [
        ("Panel Size  W × H × D",      f"{PANEL_W} × {PANEL_H} × {PANEL_D_} mm"),
        ("Mounting Plate  W × H",       f"{MOUNT_W} × {MOUNT_H} mm"),
        ("Plinth Height",               f"{PLINTH_H} mm"),
        ("Panel Colour",                "RAL 7035 (Light Grey)"),
        ("Mounting Plate Finish",       "Chrome Plating / Zinc Passivated"),
        ("Busbar Chamber Height",       f"{BUSBAR_CH} mm  (IEC 61439)"),
        ("Busbar Thickness",            f"{busbar_thick} mm"),
        (f"{busbar_material} Busbar",   busbar_spec_text),
        ("Total Busbar Current",        f"{busbar_current:.1f} A"),
        ("Incomers / Outgoing",         f"{len(incomer_mccbs)} / {len(outgoing_mccbs)}"),
        ("Phase–Phase Clearance",       f"≥ {CLEARANCE_PP} mm"),
        ("Phase–Earth Clearance",       f"≥ {CLEARANCE_PE} mm"),
    ]

    row_h   = (SB_H - hdr_h) / len(specs)
    DIV_X   = SB_X + 170

    for i, (key, val) in enumerate(specs):
        ry = SB_Y + hdr_h + i * row_h
        if i % 2 == 1:
            dwg.add(dwg.rect(insert=(SB_X+1, ry), size=(SB_W-2, row_h), fill="#0b2035"))
        dwg.add(dwg.line((SB_X, ry), (SB_X+SB_W, ry), stroke="#1e3a5f", stroke_width=0.4))
        dwg.add(dwg.line((DIV_X, ry), (DIV_X, ry+row_h), stroke="#1e3a5f", stroke_width=0.4))
        ty = ry + row_h/2 + 3.5
        dwg.add(dwg.text(key, insert=(SB_X+6, ty),
                         font_size=8.5, fill=SUB_C, font_family="Arial"))
        dwg.add(dwg.text(val, insert=(SB_X+SB_W-6, ty),
                         font_size=8.5, fill=TEXT_C, text_anchor="end",
                         font_family="Arial", font_weight="bold"))
    # Re-draw border on top
    dwg.add(dwg.rect(insert=(SB_X, SB_Y), size=(SB_W, SB_H),
                     fill="none", stroke=SPEC_BD, stroke_width=1.8, rx=4))

    # ────────────────────────────────────────────────────────────────────────
    # 10. Title strip at very bottom
    # ────────────────────────────────────────────────────────────────────────
    strip_y = SVG_H - BOTTOM_STRIP
    dwg.add(dwg.rect(insert=(0, strip_y), size=(SVG_W - SB_W - 28, BOTTOM_STRIP),
                     fill="#060d1a", stroke="#1e3a5f", stroke_width=1))
    dwg.add(dwg.text("MICROGRID PANEL  —  GENERAL ARRANGEMENT (GA)",
                     insert=(18, strip_y + BOTTOM_STRIP/2 + 5),
                     font_size=13, fill=HEAD_C, font_family="Arial", font_weight="bold"))
    now_str = datetime.datetime.now().strftime("%d-%b-%Y")
    dwg.add(dwg.text(f"Date: {now_str}  |  Scale: NTS  |  IEC 61439 compliant",
                     insert=(SVG_W - SB_W - 45, strip_y + BOTTOM_STRIP/2 + 5),
                     font_size=9, fill=SUB_C, text_anchor="end", font_family="Arial"))

    return dwg.tostring(), SVG_W, SVG_H, PANEL_W, PANEL_H, PANEL_D_


# ──────────────────────────────────────────────────────────────────────────────
# DEAD CODE REMOVED — old GA body cleaned up
_SENTINEL_ = None
# ──────────────────────────────────────────────────────────────────────────────
# DYNAMIC CANVAS SIZING (SLD)
# ──────────────────────────────────────────────────────────────────────────────
def compute_canvas(n_dg, g_kw, s_kw, n_out):
    n_incomers = int(n_dg) + (1 if g_kw > 0 else 0) + (1 if s_kw > 0 else 0)
    n_incomers = max(n_incomers, 1)
    n_out      = max(int(n_out), 1)
    MIN_COL    = 250; MARGIN_L = 100; MARGIN_R = 120
    width = MARGIN_L + max(n_incomers, n_out + 0.5) * MIN_COL + MARGIN_R
    width = max(width, 950)
    return int(width), 950, MIN_COL, MIN_COL, int(MARGIN_L + 60)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN UI
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.submitted:

    mccb_db = st.session_state.mccb_db if st.session_state.mccb_db else FALLBACK_MCCB_DB

    total_busbar_current  = i_solar + i_grid + sum(dg_currents)
    total_outgoing_rating = sum(mccb_outputs)
    warning_flag = total_busbar_current > total_outgoing_rating

    st.markdown(f"""
    <div class="info-card">
        <strong>📊 Busbar Calculation Summary</strong><br>
        Total Busbar Current: <strong>{total_busbar_current:.2f}A</strong><br>
        Total Outgoing Rating: <strong>{total_outgoing_rating:.0f}A</strong><br>
        Recommended Busbar Size: <strong>{busbar_spec}</strong>
    </div>
    """, unsafe_allow_html=True)

    if warning_flag:
        st.markdown(f"""
        <div class="warning-card">
            <strong>⚠️ WARNING: Insufficient Outgoing Capacity</strong><br>
            Total busbar current (<strong>{total_busbar_current:.2f}A</strong>) exceeds total outgoing
            breaker rating (<strong>{total_outgoing_rating:.0f}A</strong>).<br>
            Please increase outgoing feeder ratings or review your system configuration.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-card">✅ System is properly sized. Outgoing feeders match source capacity.</div>', unsafe_allow_html=True)

    # ── 1. SLD ────────────────────────────────────────────────────────────────

    st.markdown('<div class="section-title">📋 Professional Single Line Diagram</div>', unsafe_allow_html=True)
    system_calcs = SystemCalculations(solar_kw=solar_kw, grid_kw=grid_kw, dg_ratings_kva=dg_ratings)
    sld_svg, svg_width, svg_height = generate_sld(
        system_calcs,
        num_outputs,
        mccb_outputs,
        num_poles,
        num_dg,
        grid_kw,
        solar_kw,
        total_busbar_current,
        theme_svg_bg,
        theme_text,
        theme_svg_stroke,
        theme_sub
    )
    with st.container(border=True):
        st.image(sld_svg, use_container_width=True, caption="Microgrid SLD – click the expand icon to maximise")

    # ── 2. GA ─────────────────────────────────────────────────────────────────
    incomer_list = list(dg_mccbs)
    if grid_kw  > 0: incomer_list.append(mccb_grid)
    if solar_kw > 0: incomer_list.append(mccb_solar)

    ga_svg_str, ga_svg_w, ga_svg_h, PANEL_W_calc, PANEL_H_calc, PANEL_D_calc = generate_ga_svg(
        incomer_list, mccb_outputs, total_busbar_current, busbar_spec,
        num_poles, busbar_material, mccb_db
    )

    st.markdown('<div class="section-title">📐 General Arrangement (GA) Drawing</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.image(ga_svg_str, use_container_width=True, caption="Panel GA Drawing – click the expand icon to maximise")

    # Panel size info
    st.markdown(f"""
    <div class="info-card">
        <strong>📦 Computed Panel Dimensions (based on MCCB database)</strong><br>
        Panel W × H × D: <strong>{PANEL_W_calc} × {PANEL_H_calc} × {PANEL_D_calc} mm</strong><br>
        Incomers: <strong>{len(incomer_list)}</strong> &nbsp;|&nbsp;
        Outgoing Feeders: <strong>{len(mccb_outputs)}</strong> &nbsp;|&nbsp;
        Busbar: <strong>{busbar_spec}</strong>
    </div>
    """, unsafe_allow_html=True)

    # ── PDF UTILITIES ─────────────────────────────────────────────────────────
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []
        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()
        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_footer(num_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)
        def draw_footer(self, page_count):
            self.saveState()
            logo_path = "Kirloskar Oil Engine Logo.png"
            logo_w, logo_h = 100, 35
            try:
                self.drawImage(logo_path, A4[0]-45-logo_w, A4[1]-30-logo_h,
                               width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
            self.setFont("Helvetica", 8)
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(45, 50, A4[0]-45, 50)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawString(45, 35, "Kirloskar Oil Engines Ltd.")
            now = datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")
            self.drawCentredString(A4[0]/2.0, 35, f"Report Generated: {now}")
            pg = self.getPageNumber()
            self.drawRightString(A4[0]-45, 35, f"Page {pg} of {page_count}")
            self.restoreState()

    # ── 3. PDF Technical Report (SLD + BOM) ───────────────────────────────────
    def generate_pdf_report():
        buffer = io.BytesIO()
        doc    = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style           = styles["Title"];  title_style.fontSize = 22; title_style.textColor = colors.HexColor("#c37c5a"); title_style.alignment = 1
        h2_style              = styles["Heading2"]; h2_style.fontSize = 16; h2_style.textColor = colors.HexColor("#19988b"); h2_style.spaceBefore = 12; h2_style.spaceAfter = 8
        normal_style          = styles["Normal"]; normal_style.fontSize = 10; normal_style.leading = 13; normal_style.alignment = 4

        story = []
        story.append(Paragraph("Microgrid Panel Technical Report", title_style))
        story.append(Spacer(1, 8))
        story.append(Paragraph("1. System Overview", h2_style))
        grid_txt  = f"<b>{grid_kw} kW</b> Grid supply, " if grid_kw  > 0 else ""
        solar_txt = f"and <b>{solar_kw} kWp</b> Solar PV"   if solar_kw > 0 else ""
        story.append(Paragraph(
            f"This report details the configuration and material requirements for a customized Microgrid Panel. "
            f"The system handles <b>{int(num_dg)} DG(s)</b>, {grid_txt}{solar_txt}. "
            f"Managed via a centralized Microgrid Controller (MGC).", normal_style))
        story.append(Spacer(1, 8))

        story.append(Paragraph("2. System Specifications", h2_style))
        specs = (
            f"<b>Total Busbar Current Rating:</b> {total_busbar_current:.2f}A<br/>"
            f"<b>Total Outgoing Capacity:</b> {total_outgoing_rating:.0f}A<br/>"
            f"<b>Recommended Busbar:</b> {busbar_spec}<br/>"
            f"<b>Panel Dimensions (Computed):</b> {PANEL_W_calc}W × {PANEL_H_calc}H × {PANEL_D_calc}D mm<br/>"
            f"<b>System Configuration:</b> {int(num_poles)}-Phase, {int(num_outputs)} Outgoing Feeders<br/>"
        )
        if warning_flag:
            specs += "<br/><font color='red'><b>WARNING:</b> Total busbar current exceeds total outgoing rating. Review configuration.</font>"
        story.append(Paragraph(specs, normal_style))
        story.append(Spacer(1, 8))

        story.append(Paragraph("3. Single Line Diagram (SLD)", h2_style))
        with open("temp_sld.svg", "w", encoding="utf-8") as f:
            f.write(sld_svg)
        try:
            drawing = svg2rlg("temp_sld.svg")
            scale   = 505.0 / svg_width
            drawing.scale(scale, scale)
            drawing.width  = svg_width  * scale
            drawing.height = svg_height * scale
            sld_table = Table([[drawing]], colWidths=[505])
            sld_table.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER")]))
            story.append(sld_table)
        except Exception as e:
            story.append(Paragraph(f"[Error rendering SLD: {e}]", normal_style))

        story.append(Spacer(1, 10))
        story.append(Paragraph("<i>Note: Diagram illustrates electrical topology and power flow.</i>", normal_style))
        story.append(Spacer(1, 20))

        # ── GA Drawing in Main Report ──
        story.append(Paragraph("4. General Arrangement (GA) Drawing", h2_style))
        with open("temp_ga.svg", "w", encoding="utf-8") as f:
            f.write(ga_svg_str)
        try:
            ga_rlg = svg2rlg("temp_ga.svg")
            scale_ga = 505.0 / ga_svg_w
            ga_rlg.scale(scale_ga, scale_ga)
            ga_rlg.width = ga_svg_w * scale_ga
            ga_rlg.height = ga_svg_h * scale_ga
            ga_table = Table([[ga_rlg]], colWidths=[505])
            ga_table.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER")]))
            story.append(ga_table)
        except Exception as e:
            story.append(Paragraph(f"[Error rendering GA: {e}]", normal_style))

        story.append(Spacer(1, 10))
        story.append(Paragraph("<i>Internal layout and dimensional overview.</i>", normal_style))
        story.append(Spacer(1, 15))

        # ── MCCB Schedule Table (Integrated into Main Report) ──
        story.append(Paragraph("4.1 MCCB Schedule (from Database)", h2_style))
        sched_data = [["Tag", "Description", "Rating (A)", "Poles", "H × W × D (mm)", "Frame"]]
        for i, r in enumerate(incomer_list):
            d = get_mccb_dims(r, mccb_db)
            sched_data.append([f"I/C {i+1}", "Incomer MCCB", f"{r}A", f"{int(num_poles)}P",
                                f"{d['h']}×{d['w']}×{d['d']}", d['frame']])
        for i, r in enumerate(mccb_outputs):
            d = get_mccb_dims(r, mccb_db)
            sched_data.append([f"O/G {i+1}", "Outgoing MCCB", f"{r}A", f"{int(num_poles)}P",
                                f"{d['h']}×{d['w']}×{d['d']}", d['frame']])

        sched_table = Table(sched_data, colWidths=[40, 130, 60, 40, 115, 120])
        sched_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor("#19988b")),
            ("TEXTCOLOR",     (0,0),(-1,0),  colors.whitesmoke),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
            ("GRID",          (0,0),(-1,-1), 0.5, colors.grey),
            ("FONTSIZE",      (0,0),(-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#f1f5f9")]),
        ]))
        story.append(sched_table)
        story.append(PageBreak())

        story.append(Paragraph("5. Bill Of Material (BOM)", h2_style))
        story.append(Spacer(1, 8))

        bom_items = []
        if solar_kw > 0:
            bom_items.append({"desc": f"Solar Incomer MCCB {mccb_solar}A, {num_poles}P, 36kA BREAKING CAPACITY", "rating": "36kA", "qty": "1", "uom": "Nos"})
        if grid_kw > 0:
            bom_items.append({"desc": f"Grid Incomer MCCB {mccb_grid}A, {num_poles}P, 36kA BREAKING CAPACITY", "rating": "36kA", "qty": "1", "uom": "Nos"})
        if num_dg > 0:
            from collections import Counter
            for r, count in Counter(dg_mccbs).items():
                bom_items.append({"desc": f"DG Incomer MCCB {r}A, {num_poles}P, 36kA BREAKING CAPACITY", "rating": "36kA", "qty": str(count), "uom": "Nos"})
        if num_outputs > 0:
            from collections import Counter
            for r, count in Counter(mccb_outputs).items():
                bom_items.append({"desc": f"Outgoing Feeder MCCB {int(r)}A, {num_poles}P, 36kA BREAKING CAPACITY", "rating": "36kA", "qty": str(count), "uom": "Nos"})

        # Extract dimensions from busbar_spec for a cleaner table
        busbar_details = busbar_spec.split('(')[1].replace(')', '') if '(' in busbar_spec else busbar_spec
        bom_items.append({"desc": f"{busbar_material} Main Busbar ({busbar_details})", "rating": f"{total_busbar_current:.1f}A", "qty": "1", "uom": "Set"})
        bom_items.append({"desc": "Microgrid Controller (MGC)", "rating": "Standard", "qty": "1", "uom": "Nos"})
        bom_items.append({"desc": "Control Cable 1.5 sqmm", "rating": "-", "qty": "100", "uom": "Meters"})
        bom_items.append({"desc": "Power/Consumable Cable Varied", "rating": "-", "qty": "50", "uom": "Meters"})
        bom_items.append({"desc": f"Control Panel, {PANEL_H_calc}H x {PANEL_W_calc} W x {PANEL_D_calc} D mm with stand", "rating": "-", "qty": "1", "uom": "Set"})

        table_data = [["Sr", "Component / Description", "Rating", "Qty", "UOM"]]
        for i, item in enumerate(bom_items):
            table_data.append([str(i+1), item["desc"], item["rating"], item["qty"], item["uom"]])

        table = Table(table_data, colWidths=[25, 305, 75, 55, 55])
        table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor("#19988b")),
            ("TEXTCOLOR",     (0,0),(-1,0),  colors.whitesmoke),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
            ("BOTTOMPADDING", (0,0),(-1,0),  10),
            ("BACKGROUND",    (0,1),(-1,-1), colors.HexColor("#f8fafc")),
            ("GRID",          (0,0),(-1,-1), 0.5, colors.grey),
            ("FONTSIZE",      (0,0),(-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#f1f5f9")]),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

        story.append(Paragraph("6. Notes & Remarks", h2_style))
        story.append(Paragraph(
            "• This BOM is subject to final design review.<br/>"
            "• All MCCB ratings include a 1.25× safety factor.<br/>"
            "• Busbar sizing considers thermal conductivity and current density limits.<br/>"
            "• Panel dimensions are computed dynamically from MCCB database.<br/>"
            "• All components per relevant Indian Standards and IEC guidelines.", normal_style))

        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer

    # ── 4. GA PDF (Landscape, standalone) ─────────────────────────────────────
    def generate_ga_pdf():
        buffer    = io.BytesIO()
        page_size = landscape(A4)
        doc       = SimpleDocTemplate(buffer, pagesize=page_size,
                                      rightMargin=30, leftMargin=30, topMargin=35, bottomMargin=40)
        styles = getSampleStyleSheet()
        title_style = styles["Title"]; title_style.fontSize = 18; title_style.textColor = colors.HexColor("#c37c5a"); title_style.alignment = 1
        h2_style    = styles["Heading2"]; h2_style.fontSize = 13; h2_style.textColor = colors.HexColor("#19988b")
        normal_style = styles["Normal"]; normal_style.fontSize = 9; normal_style.leading = 12

        story = []
        story.append(Paragraph("Microgrid Panel — Internal General Arrangement (GA)", title_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"<b>Panel Dimensions (Computed):</b> {PANEL_W_calc}W × {PANEL_H_calc}H × {PANEL_D_calc}D mm &nbsp;|&nbsp; "
            f"<b>Busbar:</b> {busbar_spec} &nbsp;|&nbsp; <b>Busbar Current:</b> {total_busbar_current:.1f}A",
            normal_style))
        story.append(Spacer(1, 8))

        with open("temp_ga.svg", "w", encoding="utf-8") as f:
            f.write(ga_svg_str)
        try:
            ga_drw  = svg2rlg("temp_ga.svg")
            avail_w = page_size[0] - 60
            avail_h = page_size[1] - 160
            scale_g = min(avail_w / ga_svg_w, avail_h / ga_svg_h)
            ga_drw.scale(scale_g, scale_g)
            ga_drw.width  = ga_svg_w * scale_g
            ga_drw.height = ga_svg_h * scale_g
            ga_table = Table([[ga_drw]], colWidths=[avail_w])
            ga_table.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER")]))
            story.append(ga_table)
        except Exception as e:
            story.append(Paragraph(f"[Error rendering GA: {e}]", normal_style))

        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"<i>Panel dims auto-calculated from MCCB dimensions database. "
            f"{len(incomer_list)} incomer(s) | {len(mccb_outputs)} outgoing feeder(s). "
            f"All dimensions in mm. Drawing is schematic, not to scale.</i>", normal_style))

        # MCCB schedule table
        story.append(Spacer(1, 8))
        story.append(Paragraph("MCCB Schedule (from Database)", h2_style))
        sched_data = [["Tag", "Description", "Rating (A)", "Poles", "H × W × D (mm)", "Frame"]]
        for i, r in enumerate(incomer_list):
            d = get_mccb_dims(r, mccb_db)
            sched_data.append([f"I/C {i+1}", "Incomer MCCB", f"{r}A", f"{num_poles}P",
                                f"{d['h']}×{d['w']}×{d['d']}", d['frame']])
        for i, r in enumerate(mccb_outputs):
            d = get_mccb_dims(r, mccb_db)
            sched_data.append([f"O/G {i+1}", "Outgoing MCCB", f"{r}A", f"{num_poles}P",
                                f"{d['h']}×{d['w']}×{d['d']}", d['frame']])

        sched_table = Table(sched_data, colWidths=[50, 130, 70, 45, 120, 90])
        sched_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor("#19988b")),
            ("TEXTCOLOR",     (0,0),(-1,0),  colors.whitesmoke),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
            ("GRID",          (0,0),(-1,-1), 0.5, colors.grey),
            ("FONTSIZE",      (0,0),(-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#f1f5f9")]),
        ]))
        story.append(sched_table)

        class GACanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                canvas.Canvas.__init__(self, *args, **kwargs); self._saved_page_states = []
            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__)); self._startPage()
            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state); self._draw_footer(num_pages); canvas.Canvas.showPage(self)
                canvas.Canvas.save(self)
            def _draw_footer(self, page_count):
                self.saveState()
                logo_path = "Kirloskar Oil Engine Logo.png"
                try:
                    self.drawImage(logo_path, page_size[0]-40-90, page_size[1]-25-32, width=90, height=32, preserveAspectRatio=True, mask='auto')
                except Exception: pass
                self.setFont("Helvetica", 8); self.setStrokeColor(colors.HexColor("#cbd5e1")); self.setLineWidth(0.5)
                self.line(30, 45, page_size[0]-30, 45); self.setFillColor(colors.HexColor("#475569"))
                self.drawString(30, 32, "Kirloskar Oil Engines Ltd.")
                now = datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")
                self.drawCentredString(page_size[0]/2.0, 32, f"Report Generated: {now}")
                self.drawRightString(page_size[0]-30, 32, f"Page {self.getPageNumber()} of {page_count}")
                self.restoreState()

        doc.build(story, canvasmaker=GACanvas)
        buffer.seek(0)
        return buffer

    # ── 5. Excel BOM ──────────────────────────────────────────────────────────
    def generate_excel_bom():
        bom_items = []
        if solar_kw > 0:
            bom_items.append({"Description": f"Solar Incomer MCCB {mccb_solar}A, {num_poles}P, 36kA BREAKING CAPACITY", "Rating": "36kA", "Qty": 1, "UOM": "Nos"})
        if grid_kw > 0:
            bom_items.append({"Description": f"Grid Incomer MCCB {mccb_grid}A, {num_poles}P, 36kA BREAKING CAPACITY", "Rating": "36kA", "Qty": 1, "UOM": "Nos"})
        if num_dg > 0:
            from collections import Counter
            for r, count in Counter(dg_mccbs).items():
                bom_items.append({"Description": f"DG Incomer MCCB {r}A, {num_poles}P, 36kA BREAKING CAPACITY", "Rating": "36kA", "Qty": count, "UOM": "Nos"})
        if num_outputs > 0:
            from collections import Counter
            for r, count in Counter(mccb_outputs).items():
                bom_items.append({"Description": f"Outgoing Feeder MCCB {int(r)}A, {num_poles}P, 36kA BREAKING CAPACITY", "Rating": "36kA", "Qty": count, "UOM": "Nos"})
        busbar_details = busbar_spec.split('(')[1].replace(')', '') if '(' in busbar_spec else busbar_spec
        bom_items.append({"Description": f"{busbar_material} Main Busbar ({busbar_details})", "Rating": f"{total_busbar_current:.1f}A", "Qty": 1, "UOM": "Set"})
        bom_items.append({"Description": "Microgrid Controller (MGC)", "Rating": "Standard", "Qty": 1, "UOM": "Nos"})
        bom_items.append({"Description": "Control Cable 1.5 sqmm", "Rating": "-", "Qty": 100, "UOM": "Meters"})
        bom_items.append({"Description": "Power/Consumable Cable Varied", "Rating": "-", "Qty": 50, "UOM": "Meters"})
        bom_items.append({"Description": f"Control Panel, {PANEL_H_calc}H x {PANEL_W_calc} W x {PANEL_D_calc} D mm with stand", "Rating": "-", "Qty": 1, "UOM": "Set"})

        df = pd.DataFrame(bom_items)
        df.insert(0, "Sr No", range(1, len(df)+1))
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="BOM")
        return output.getvalue()

    pdf_buffer    = generate_pdf_report()
    ga_pdf_buffer = generate_ga_pdf()
    excel_data    = generate_excel_bom()

    # ── Download buttons ───────────────────────────────────────────────────────
    st.divider()
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        st.download_button("📄 Download Technical Report (PDF)", data=pdf_buffer,
                           file_name="Microgrid_Panel_Technical_Report.pdf", mime="application/pdf", use_container_width=True)
    with col_dl2:
        st.download_button("📐 Download GA Drawing (PDF)", data=ga_pdf_buffer,
                           file_name="Microgrid_Panel_GA_Drawing.pdf", mime="application/pdf", use_container_width=True)
    with col_dl3:
        st.download_button("📊 Download BOM (Excel)", data=excel_data,
                           file_name="Microgrid_Panel_BOM.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # ── Summary metrics ────────────────────────────────────────────────────────
    st.divider()
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1: st.metric("Total Busbar Current",  f"{total_busbar_current:.2f}A")
    with col2: st.metric("Total Outgoing Rating", f"{total_outgoing_rating:.0f}A")
    with col3: st.metric("System Voltage",        "415V, 3Φ")
    with col4: st.metric("Busbar Size",           busbar_spec)
    with col5: st.metric("Panel W×H (mm)",        f"{PANEL_W_calc}×{PANEL_H_calc}")
    with col6: st.metric("Canvas Size",           f"{svg_width}×{svg_height} px")