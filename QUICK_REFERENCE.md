# Quick Reference - Module Imports & Functions

## Imports by Module

### Constants & Configuration
```python
from src.constants import (
    STANDARD_MCCBS,              # List of standard MCCB ratings
    NOMINAL_VOLTAGE,             # 415V (3-phase)
    POWER_FACTOR,                # 0.8 (solar/grid)
    DG_POWER_FACTOR,             # 1.0 (diesel generators)
    PLINTH_H,                    # Plinth height (100mm)
    PANEL_D,                     # Standard panel depth (600mm)
    CLEARANCE_PP, CLEARANCE_PE,  # IEC 61439 clearances
    BUSBAR_CHAMBER_HEIGHTS,      # {400: 100mm, 800: 150mm, ∞: 200mm}
    BUSBAR_THICKNESS,            # {400: 5mm, 800: 10mm, ∞: 12mm}
    FALLBACK_MCCB_DB,           # Fallback MCCB dimensions
    THEME_DARK, THEME_LIGHT,    # Theme definitions
    GA_COLORS_DARK, GA_COLORS_LIGHT  # GA drawing colors
)
```

### Utilities
```python
from src.utils import (
    # Excel/Database functions
    load_mccb_dimensions_from_file,   # Load MCCB data from uploaded Excel
    get_mccb_dims,                    # Get MCCB dimensions with fallback
    get_standard_rating,              # Round to nearest standard rating
    
    # Calculation functions
    calculate_current_from_power,     # P(kW) → I(A)
    calculate_current_from_kva,       # S(kVA) → I(A)
    get_mccb_rating,                  # Apply 1.25× safety margin
    get_busbar_chamber_height,        # IEC 61439 → chamber height (mm)
    get_busbar_thickness,             # Get busbar thickness (mm)
    
    # Specification generation
    calculate_row_width,              # Width of MCCB row + gaps
    generate_busbar_spec,             # → "1 Set (40 x 20 mm Copper)"
    get_theme_colors,                 # Get color palette by theme
)
```

### SLD (Single Line Diagram)
```python
from src.sld.calculations import SystemCalculations

# Usage
calcs = SystemCalculations(
    solar_kw=100,              # Solar generation (kW)
    grid_kw=120,               # Grid capacity (kW)
    dg_ratings_kva=[250, 250]  # DG ratings (kVA list)
)

# Properties
calcs.i_solar          # Solar current (A)
calcs.i_grid           # Grid current (A)
calcs.dg_currents      # List of DG currents (A)
calcs.dg_mccbs         # List of DG MCCB ratings (A)
calcs.mccb_solar       # Solar MCCB rating (A)
calcs.mccb_grid        # Grid MCCB rating (A)
calcs.total_busbar_current  # Total current on busbar (A)
calcs.get_all_incomers()    # All incomer MCCB ratings [DGs, Grid, Solar]

from src.sld.generator import generate_sld

# Usage
svg_str, width, height = generate_sld(
    system_calcs=calcs,
    num_outputs=4,              # Number of output feeders
    mccb_outputs=[400, 250],   # Output MCCB ratings
    mccb_db=mccb_database,     # MCCB dimensions dictionary
    theme="dark"               # "dark" or "light"
)
# Returns: SLD SVG string, canvas width, canvas height
```

### GA (General Arrangement)
```python
from src.ga.generator import generate_ga_svg
from src.ga.dimensions import compute_panel_dimensions

# Panel sizing
panel_dims = compute_panel_dimensions(
    incomer_mccbs=[250, 400, 160],     # All incomer MCCB ratings
    outgoing_mccbs=[400, 250, 200],    # All output MCCB ratings
    mccb_db=mccb_database,             # MCCB dimensions dict
    busbar_current_A=1200              # Total busbar current (A)
)

# Extract dimensions
print(panel_dims["PANEL_W"])    # Panel width (mm)
print(panel_dims["PANEL_H"])    # Panel height (mm)
print(panel_dims["PANEL_D"])    # Panel depth (mm)
print(panel_dims["BUSBAR_CH_MM"])  # Busbar chamber height (mm)

# GA drawing
svg_str, svg_w, svg_h, panel_w, panel_h, panel_d = generate_ga_svg(
    incomer_mccbs=[250, 400, 160],
    outgoing_mccbs=[400, 250, 200],
    mccb_db=mccb_database,
    busbar_current=1200,
    busbar_spec="1 Set (40 x 20 mm Copper)",
    mccb_solar=160,
    mccb_grid=400,
    num_dg=2,
    num_outputs=4,
    theme="dark"
)
# Returns: SVG string, width, height, panel_w mm, panel_h mm, panel_d mm
```

### BOM (Bill of Materials)
```python
from src.bom.generator import generate_bom_items, BOMItem

# Generate BOM
bom_items = generate_bom_items(
    solar_kw=100,              # Solar capacity (kW)
    grid_kw=120,               # Grid capacity (kW)
    num_dg=2,                  # Number of DGs
    dg_ratings_kva=[250, 250], # DG ratings (kVA)
    mccb_solar=160,            # Solar MCCB rating (A)
    mccb_grid=400,             # Grid MCCB rating (A)
    mccb_outputs=[400, 250, 200],  # Output MCCB ratings
    num_outputs=4,             # Number of outputs
    busbar_spec="1 Set (40 x 20 mm Copper)",
    panel_h=2400,              # Panel height (mm)
    panel_w=1200,              # Panel width (mm)
    panel_d=600                # Panel depth (mm)
)

# Iterate BOM
for item in bom_items:
    print(f"{item.description} - Rating: {item.rating}, Qty: {item.qty}, UOM: {item.uom}")

# Convert to dict for export
bom_dicts = [item.to_dict() for item in bom_items]

from src.bom.exports import generate_pdf_report, generate_ga_pdf, generate_excel_bom

# Export as PDF
pdf_bytes = generate_pdf_report(
    sld_svg=sld_string,
    ga_svg=ga_string,
    bom_items=bom_items,
    system_kw=100 + 120,       # Total system capacity
    incomer_mccbs=[250, 400, 160],
    mccb_solar=160,
    mccb_grid=400,
    busbar_current=1200,
    busbar_spec="1 Set (40 x 20 mm Copper)",
    panel_h=2400,
    panel_w=1200,
    panel_d=600,
    theme="dark",
    mccb_db=mccb_database
)

# Export standalone GA PDF (landscape A4)
ga_pdf_bytes = generate_ga_pdf(
    ga_svg=ga_string,
    incomer_mccbs=[250, 400, 160],
    mccb_db=mccb_database,
    theme="dark"
)

# Export as Excel
excel_bytes = generate_excel_bom(bom_items)

# Save to file
with open("report.pdf", "wb") as f:
    f.write(pdf_bytes)
with open("bom.xlsx", "wb") as f:
    f.write(excel_bytes)
```

---

## Common Workflows

### 1. Complete System Generation (like app.py does)
```python
from src.sld.calculations import SystemCalculations
from src.sld.generator import generate_sld
from src.ga.generator import generate_ga_svg
from src.bom.generator import generate_bom_items
from src.bom.exports import generate_pdf_report
from src.utils import generate_busbar_spec, load_mccb_dimensions_from_file

# Load MCCB database
mccb_db = load_mccb_dimensions_from_file("mccb_ratings.xlsx")

# Get user inputs
solar_kw = 100
grid_kw = 120
dg_ratings_kva = [250, 250]
num_outputs = 4
mccb_outputs = [400, 250, 200, 160]

# Calculate electrical
calcs = SystemCalculations(solar_kw, grid_kw, dg_ratings_kva)

# Generate specifications
busbar_spec = generate_busbar_spec(calcs.total_busbar_current, "Copper")

# Generate diagrams
sld_svg, sld_w, sld_h = generate_sld(calcs, num_outputs, mccb_outputs, mccb_db)
ga_svg, ga_w, ga_h, pw, ph, pd = generate_ga_svg(
    calcs.get_all_incomers(), mccb_outputs, mccb_db,
    calcs.total_busbar_current, busbar_spec, calcs.mccb_solar,
    calcs.mccb_grid, len(dg_ratings_kva), num_outputs
)

# Generate BOM
bom = generate_bom_items(
    solar_kw, grid_kw, len(dg_ratings_kva), dg_ratings_kva,
    calcs.mccb_solar, calcs.mccb_grid, mccb_outputs, num_outputs,
    busbar_spec, ph, pw, pd
)

# Export
pdf = generate_pdf_report(sld_svg, ga_svg, bom, solar_kw + grid_kw, 
                         calcs.get_all_incomers(), calcs.mccb_solar,
                         calcs.mccb_grid, calcs.total_busbar_current,
                         busbar_spec, ph, pw, pd, "dark", mccb_db)
```

### 2. Just Calculate Electrical
```python
from src.sld.calculations import SystemCalculations

calcs = SystemCalculations(100, 120, [250, 250])
print(f"Solar: {calcs.i_solar:.1f}A → MCCB {calcs.mccb_solar}A")
print(f"Grid: {calcs.i_grid:.1f}A → MCCB {calcs.mccb_grid}A")
print(f"DGs: {calcs.dg_currents} → MCCBs {calcs.dg_mccbs}")
print(f"Busbar: {calcs.total_busbar_current:.1f}A")
```

### 3. Just Generate GA Drawing
```python
from src.ga.generator import generate_ga_svg

svg, w, h, pw, ph, pd = generate_ga_svg(
    incomer_mccbs=[250, 400],
    outgoing_mccbs=[400, 250],
    mccb_db=mccb_database,
    busbar_current=1000,
    busbar_spec="1 Set (40 x 20 mm Copper)",
    theme="dark"
)

# Display or save
with open("panel_layout.svg", "w") as f:
    f.write(svg)
```

### 4. Just Generate BOM
```python
from src.bom.generator import generate_bom_items
from src.bom.exports import generate_excel_bom

bom = generate_bom_items(100, 120, 2, [250, 250], 160, 400, [400, 250], 2, ...)
excel = generate_excel_bom(bom)

with open("bom.xlsx", "wb") as f:
    f.write(excel)
```
