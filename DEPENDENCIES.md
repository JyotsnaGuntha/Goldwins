# Module Dependencies Map

## Dependency Graph

```
app.py (Main Streamlit Application)
├── src.constants
│   └── (No internal dependencies)
│
├── src.utils
│   ├── pandas
│   ├── math
│   └── src.constants
│
├── src.sld.calculations
│   ├── src.utils
│   ├── src.constants
│   └── math
│
├── src.sld.generator
│   ├── src.sld.components
│   ├── src.sld.calculations
│   ├── src.constants
│   ├── svgwrite
│   └── math
│
├── src.sld.components
│   ├── svgwrite
│   ├── math
│   └── src.constants
│
├── src.ga.generator
│   ├── src.ga.dimensions
│   ├── src.ga.styles
│   ├── src.utils
│   ├── src.constants
│   ├── svgwrite
│   └── datetime
│
├── src.ga.dimensions
│   ├── src.utils
│   ├── src.constants
│   └── math
│
├── src.ga.styles
│   └── src.constants
│
├── src.bom.generator
│   ├── src.utils
│   ├── src.constants
│   └── collections
│
└── src.bom.exports
    ├── src.bom.generator
    ├── reportlab (Canvas, SimpleDocTemplate, Paragraph, Table, TableStyle, colors, A4, landscape)
    ├── svglib (svg2rlg)
    ├── pandas
    ├── datetime
    ├── tempfile
    ├── os
    ├── io
    └── src.constants
```

---

## Import Chain Analysis

### Tier 1: Base Dependencies (No Internal Dependencies)
**These can be used standalone:**

```python
from src.constants import *
```

- No Python imports from src/
- Pure constants and configuration
- Safe to use in isolation

---

### Tier 2: Utility Layer (Depends on Tier 1)
**These depend only on constants:**

```python
from src.utils import load_mccb_dimensions_from_file, get_mccb_dims, ...
```

**Dependencies:**
- pandas (Excel reading)
- math (calculations)
- src.constants (standard values)

**Can be used independently** - excellent for unit testing

---

### Tier 3: Domain Modules (Depend on Tier 1 & 2)

#### SLD Package
```python
from src.sld.calculations import SystemCalculations
from src.sld.generator import generate_sld
```

**Dependencies:**
- src.utils (utility functions)
- src.constants (electrical standards)
- src.sld.components (drawing functions)
- svgwrite (SVG generation)
- math (calculations)

**Code Flow:**
1. `SystemCalculations` uses utils for current/MCCB calculations
2. `generate_sld()` calls SystemCalculations
3. `generate_sld()` calls components.py for drawing

#### GA Package
```python
from src.ga.generator import generate_ga_svg
from src.ga.dimensions import compute_panel_dimensions
```

**Dependencies:**
- src.utils (MCCB dimensions, busbar specs)
- src.constants (colors, sizes, standards)
- src.ga.dimensions (panel sizing)
- src.ga.styles (color management)
- svgwrite (SVG generation)
- datetime (timestamp)

**Code Flow:**
1. `generate_ga_svg()` calls `compute_panel_dimensions()`
2. `compute_panel_dimensions()` uses utils for lookups
3. Drawing uses `get_ga_colors()` from styles

#### BOM Package
```python
from src.bom.generator import generate_bom_items
from src.bom.exports import generate_pdf_report, generate_excel_bom
```

**Dependencies:**
- src.utils (MCCB lookups)
- src.constants (materials, standards)
- reportlab (PDF generation)
- svglib (SVG embedding in PDF)
- pandas (Excel export)
- io, tempfile, os (file handling)

**Code Flow:**
1. `generate_bom_items()` is pure data generation
2. `generate_pdf_report()` accepts pre-generated data
3. `generate_excel_bom()` converts BOM items to Excel

---

### Tier 4: Application Layer (Depends on Tier 1-3)
**Main Streamlit app:**

```python
import app
# or
from run_app import launch_streamlit
```

**Import Order in app.py:**
1. Streamlit basics
2. src.constants (for theme values)
3. src.utils (for utilities)
4. src.sld (for SLD generation)
5. src.ga (for GA generation)
6. src.bom (for BOM + exports)

**Dependencies:**
- All of src/ packages
- streamlit (UI framework)
- pandas (data display)
- io (file buffers)

---

## Circular Dependency Analysis ✅

**Status: NONE DETECTED**

This is a **clean dependency hierarchy** with no circular dependencies:

```
Tier 1 (Base) ← Only external packages
    ↓
Tier 2 (Utils) ← Only Tier 1
    ↓
Tier 3 (Domains) ← Only Tier 1 & 2
    ↓
Tier 4 (App) ← Only Tier 1-3
```

Each higher tier can depend on lower tiers, but not vice versa.

---

## External Package Dependencies

### Required Packages

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| streamlit | 1.56.0+ | app.py | Web UI framework |
| pandas | 3.0.0+ | utils, bom/exports | Data manipulation & Excel |
| svgwrite | 1.4.3+ | sld/components, sld/generator, ga/generator | SVG generation |
| reportlab | 4.0.0+ | bom/exports | PDF generation |
| svglib | 1.4.1+ | bom/exports | SVG to ReportLab conversion |
| openpyxl | 3.0.0+ | pandas (for Excel) | Excel workbook handling |
| math | (stdlib) | utils, sld, ga | Mathematical functions |
| io | (stdlib) | bom/exports | BytesIO buffers |
| tempfile | (stdlib) | bom/exports | Temporary file handling |
| os | (stdlib) | bom/exports | File operations |
| datetime | (stdlib) | ga/generator, bom/exports | Timestamps |
| collections | (stdlib) | bom/generator | Counter for grouping |

### Installation
```bash
pip install streamlit pandas svgwrite reportlab svglib openpyxl
```

---

## Module Import Examples

### Using Just Constants
```python
from src.constants import NOMINAL_VOLTAGE, CLEARANCE_PP, FALLBACK_MCCB_DB
```
✅ **No dependencies** - safe for config management

### Using Utils
```python
from src.utils import get_standard_rating, calculate_current_from_power
rating = get_standard_rating(350)  # Depends on: constants
current = calculate_current_from_power(100)  # Depends on: constants
```
✅ **Only depends on Tier 1**

### Using SLD
```python
from src.sld.calculations import SystemCalculations
from src.sld.generator import generate_sld

calcs = SystemCalculations(100, 120, [250])  # Uses: utils, constants
svg = generate_sld(calcs, ...)  # Uses: components, utils, constants
```
✅ **Depends on Tier 1 & 2**

### Using GA
```python
from src.ga.generator import generate_ga_svg
from src.ga.dimensions import compute_panel_dimensions

dims = compute_panel_dimensions(...)  # Uses: utils, constants
svg = generate_ga_svg(...)  # Uses: dimensions, styles, utils, constants
```
✅ **Depends on Tier 1 & 2**

### Using BOM
```python
from src.bom.generator import generate_bom_items
from src.bom.exports import generate_pdf_report, generate_excel_bom

bom = generate_bom_items(...)  # Uses: utils, constants
pdf = generate_pdf_report(...)  # Uses: reportlab, svglib, pandas
excel = generate_excel_bom(...)  # Uses: pandas
```
✅ **Depends on Tier 1, 2, and external packages**

### Complete System (like in app.py)
```python
# All imports together create the complete application
from src.constants import THEME_DARK, THEME_LIGHT
from src.utils import load_mccb_dimensions_from_file, generate_busbar_spec
from src.sld.calculations import SystemCalculations
from src.sld.generator import generate_sld
from src.ga.generator import generate_ga_svg
from src.bom.generator import generate_bom_items
from src.bom.exports import generate_pdf_report, generate_excel_bom
```
✅ **All tiers integrated**

---

## Test Isolation

Because of the clean dependency hierarchy, you can test modules in isolation:

### Testing Isolated Modules

```python
# Test constants (no setup)
from src.constants import NOMINAL_VOLTAGE
assert NOMINAL_VOLTAGE == 415

# Test utilities (only needs constants)
from src.utils import get_standard_rating
assert get_standard_rating(350) == 400

# Test calculations (create instance with known values)
from src.sld.calculations import SystemCalculations
calcs = SystemCalculations(100, 120, [250])
assert calcs.mccb_solar > 0
assert calcs.mccb_grid > 0

# Test panel sizing (independent of UI)
from src.ga.dimensions import compute_panel_dimensions
dims = compute_panel_dimensions([250, 400], [200, 250], {}, 1200)
assert dims['PANEL_W'] > 0
assert dims['PANEL_H'] > 0

# Test BOM generation (independent of graphics)
from src.bom.generator import generate_bom_items
bom = generate_bom_items(100, 120, 2, [250, 250], ...)
assert len(bom) > 0
assert bom[0].qty > 0
```

Each test is isolated and doesn't require the full application to be running!

---

## Dependency Resolution Order

When starting the application:

1. **First**: Load constants (configs any module might use)
2. **Second**: Load utils (used by all domain modules)
3. **Third**: Load SLD module (sld/calculations → sld/components → sld/generator)
4. **Fourth**: Load GA module (ga/dimensions → ga/styles → ga/generator)
5. **Fifth**: Load BOM module (bom/generator → bom/exports)
6. **Finally**: Initialize Streamlit app with UI logic

This order ensures all dependencies are available when needed.

---

## Refactoring Benefits Enabled by Clean Dependencies

✅ **Easy Testing** - Mock dependencies clearly defined
✅ **Easy Reuse** - Use individual modules in other projects
✅ **Easy Extension** - Add new modules without breaking existing ones
✅ **Easy Debugging** - Trace issues through clear dependency chains
✅ **Easy Documentation** - Dependency graph shows relationships
✅ **Easy Performance Tuning** - Profile individual tiers
✅ **Easy Parallelization** - Independent modules can run in separate processes
