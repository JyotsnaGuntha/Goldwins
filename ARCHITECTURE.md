# 🏗️ Architecture & Module Reference

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  STREAMLIT USER INTERFACE                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SIDEBAR (ui/sidebar.py)                                 │   │
│  │  ├─ Solar Input (kWp)                                    │   │
│  │  ├─ Grid Input (kW)                                      │   │
│  │  ├─ DG Count & Ratings (kVA each)                        │   │
│  │  ├─ System Poles (3 or 4)                                │   │
│  │  └─ Outgoing Feeders Count                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MAIN AREA                                               │   │
│  │  ├─ Generate Button → SLD Preview                        │   │
│  │  └─ Download Button → Full PDF Report                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MODEL LAYER (models/system_model.py)                    │   │
│  │  ├─ SystemInput (user inputs)                            │   │
│  │  └─ DesignObject (computed outputs)                      │   │
│  │     ├─ Incomers (with MCCBs)                             │   │
│  │     ├─ Outgoings (load feeders)                          │   │
│  │     ├─ Busbar Design                                     │   │
│  │     └─ Controller                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                        ↑                                         │
│                        │                                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ENGINE LAYER (engine/*)                                 │   │
│  │  ├─ DesignBuilder: Orchestrates design creation         │   │
│  │  └─ Calculations: Pure math functions                    │   │
│  │     ├─ calculate_current_from_kw()                       │   │
│  │     ├─ calculate_current_from_kva()                      │   │
│  │     ├─ select_mccb_rating()                              │   │
│  │     └─ calculate_busbar_size()                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┬──────────────┐
                    ↓                   ↓              ↓
┌──────────────────────────┐ ┌────────────────────┐ ┌──────────────┐
│   RENDERER LAYER         │ │  PDF LAYER         │ │  CONFIG      │
│ (renderers/*)            │ │ (utils/)           │ │ (config/)    │
│                          │ │                    │ │              │
│ ┌────────────────────┐   │ │ ┌────────────────┐ │ │ constants.py │
│ │ SLDRenderer        │   │ │ │ PDFGenerator   │ │ │              │
│ │ - SVG output       │   │ │ │ - 4-page PDF   │ │ │ Electrical   │
│ └────────────────────┘   │ │ │ - Title page   │ │ │ parameters   │
│                          │ │ │ - SLD page     │ │ │              │
│ ┌────────────────────┐   │ │ │ - GA page      │ │ │ SVG colors   │
│ │ GARenderer         │   │ │ │ - BOM page     │ │ │              │
│ │ - Physical layout  │   │ │ └────────────────┘ │ │ PDF settings │
│ └────────────────────┘   │ │                    │ │              │
│                          │ │ ┌────────────────┐ │ │ Panel layout │
│ ┌────────────────────┐   │ │ │ SVG Helpers    │ │ │              │
│ │ BOMGenerator       │   │ │ │ - SVG→PNG      │ │ │ MCCB ratings │
│ │ - Data tables      │   │ │ │ - Cleanup      │ │ │              │
│ │ - HTML/Text       │   │ │ └────────────────┘ │ │              │
│ └────────────────────┘   │ │                    │ │              │
└──────────────────────────┘ └────────────────────┘ └──────────────┘
           │
           └──────────────────────────────────────┐
                                                  ↓
                                    ┌─────────────────────┐
                                    │  OUTPUT             │
                                    ├─────────────────────┤
                                    │ • SLD (SVG)         │
                                    │ • GA (SVG)          │
                                    │ • BOM (HTML/PDF)    │
                                    │ • PDF Report (4pp)  │
                                    └─────────────────────┘
```

---

## Module Dependency Graph

```
app.py (Main)
  │
  ├─→ config/constants.py
  ├─→ models/system_model.py
  ├─→ engine/
  │    ├─ design_builder.py
  │    │   └─ calculations.py
  │    └─ calculations.py
  ├─→ renderers/
  │    ├─ sld_renderer.py
  │    ├─ ga_renderer.py
  │    └─ bom_generator.py
  ├─→ utils/
  │    ├─ svg_helpers.py
  │    └─ pdf_helpers.py
  │         └─ bom_generator.py
  └─→ ui/
       ├─ sidebar.py
       └─ styles.py
```

---

## Data Flow - Generate Button

```
User clicks "Generate"
    ↓
ui/sidebar.render_sidebar()
    ↓ (returns)
SystemInput object
    ↓
validate()
    ↓
engine/DesignBuilder(SystemInput).build()
    ├─→ _build_incomers()
    │    └─ calculations.select_mccb_rating()
    ├─→ _build_outgoings()
    │    └─ calculations.select_mccb_rating()
    └─→ _size_busbar()
         └─ calculations.calculate_busbar_size()
    ↓
DesignObject (complete with all computed values)
    ↓
renderers/SLDRenderer(design).render()
    ↓
SVG String
    ↓
svg_helpers.svg_to_png()
    ↓ (optional)
PNG file (temp)
    ↓
st.session_state["design"] = design
st.session_state["sld_svg"] = sld_svg
st.session_state["sld_png_path"] = png_path
    ↓
Display on screen with metrics
```

---

## Data Flow - Download Button

```
User clicks "Download"
    ↓
Check st.session_state["design"]
    ├─ If None: Show warning
    └─ If exists: Continue
    ↓
renderers/GARenderer(design).render()
    ↓
GA SVG String
    ↓
svg_helpers.svg_to_png(ga_svg)
    ↓
GA PNG file (temp)
    ↓
utils/PDFReportGenerator(design).generate_full_report()
    ├─→ _build_title_page()
    │    └─ design.total_current_a, etc.
    ├─→ _build_sld_page(sld_png_path)
    ├─→ _build_ga_page(ga_png_path)
    └─→ _build_bom_page()
         └─ BOMGenerator(design).generate_bom_data()
    ↓
PDF bytes (in BytesIO buffer)
    ↓
Cleanup temp PNG files
    ↓
st.download_button() → PDF download
```

---

## Class Hierarchy

### Models
```
SystemInput (dataclass)
├─ solar_kw: float
├─ grid_kw: float
├─ dg_ratings_kva: List[float]
├─ num_poles: int
└─ Methods:
   ├─ validate()
   ├─ has_solar()
   ├─ has_grid()
   └─ has_dgs()

DesignObject (dataclass)
├─ incomers: List[Incomer]
├─ outgoings: List[Outgoing]
├─ busbar: BusbarDesign
├─ controller: MicrogridController
├─ system_voltage_v: int
├─ num_poles: int
├─ total_current_a: float
└─ Methods:
   ├─ num_incomers()
   ├─ num_outgoings()
   └─ get_all_mccbs()

Incomer (dataclass)
├─ name: str
├─ source_type: str (DG|Grid|Solar)
├─ rating_kw_or_kva: float
├─ current_a: float
└─ mccb_rating_a: int

Outgoing (dataclass)
├─ name: str
└─ mccb_rating_a: int

BusbarDesign (dataclass)
├─ num_runs: int
├─ width_mm: int
├─ thickness_mm: int
├─ length_mm: int
└─ material: str

MicrogridController (dataclass)
├─ name: str
└─ type: str
```

### Engines
```
DesignBuilder
├─ __init__(system_input: SystemInput)
├─ build() → DesignObject
├─ _build_incomers() → List[Incomer]
├─ _build_outgoings() → List[Outgoing]
└─ _size_busbar() → BusbarDesign
```

### Renderers
```
SLDRenderer
├─ __init__(design: DesignObject)
├─ render() → str (SVG)
└─ Helper methods (_draw_*, etc.)

GARenderer
├─ __init__(design: DesignObject)
├─ render() → str (SVG)
└─ Helper methods (_draw_*, etc.)

BOMGenerator
├─ __init__(design: DesignObject)
├─ generate_bom_data() → List[List[str]]
└─ generate_bom_summary() → str
```

---

## Constants Reference

### Electrical
```python
SYSTEM_VOLTAGE = 415              # V (3-phase nominal)
POWER_FACTOR = 0.8                # Default for solar/grid
DG_POWER_FACTOR = 1.0             # DGs rated in kVA
SAFETY_FACTOR = 1.25              # For MCCB selection
```

### SVG Rendering
```python
SVG_WIDTH = 1450                  # pixels
SVG_HEIGHT = 850                  # pixels
Y_SOURCES = 180                   # Top section
Y_DIVISION = 380                  # Customer/Scope line
Y_BUSBAR = 600                    # Main busbar
IC_START_X = 220                  # First incomer X
COMPONENT_SPACING = 280           # Between incomers
```

### Colors
```python
COLOR_WHITE = "white"
COLOR_GRID = "#60a5fa"             # Light blue
COLOR_SOLAR = "#fbbf24"            # Amber
COLOR_MCCB = "#10b981"             # Emerald
COLOR_BUSBAR = "#ef4444"           # Red
COLOR_MGC = "#a78bfa"              # Purple
```

---

## Session State Variables

```python
st.session_state["design"]        # DesignObject (main computed output)
st.session_state["sld_svg"]       # SVG string (for display)
st.session_state["sld_png_path"]  # Temp PNG path (for PDF)
st.session_state["ga_png_path"]   # Temp PNG path (for PDF)
```

**Lifecycle:**
- Initialized to None on first run
- Populated on "Generate" click
- Reused on "Download" click
- Reset only on sidebar parameter change

---

## Error Handling Strategy

1. **Input Validation**
   ```python
   SystemInput.validate()  # Checks all constraints
   → ValueError if invalid
   ```

2. **Rendering Errors**
   ```python
   try:
       sld_svg = SLDRenderer(design).render()
   except Exception as e:
       st.error(f"Rendering failed: {e}")
   ```

3. **PDF Generation**
   ```python
   try:
       pdf_buffer = PDFReportGenerator(design).generate_full_report()
   except Exception as e:
       st.error(f"PDF generation failed: {e}")
   ```

4. **Resource Cleanup**
   ```python
   finally:
       cleanup_temp_file(png_path)  # Always clean up temps
   ```

---

## Performance Considerations

| Operation | Time | Notes |
|-----------|------|-------|
| Load inputs | Instant | Sidebar rendering |
| Validate & calculate | <100ms | Pure Python math |
| Render SLD | 200-500ms | SVG drawing (~50 elements) |
| Render GA | 100-300ms | SVG drawing (~30 elements) |
| Convert SVG→PNG | 1-3s | Requires cairo/cairosvg |
| Generate PDF | 2-5s | Image embedding + table layout |
| **Total (Generate)** | **~1 second** | Cached in session_state |
| **Total (Download)** | **~6 seconds** | GA + PNG conversion + PDF build |

---

## Thread Safety

- Streamlit is **single-threaded per session**
- Each user has isolated session_state
- No concurrent access to DesignObject
- Safe for multi-user deployment

---

## Testing Points

```
1. Unit Tests (engine/calculations.py)
   - Test current calculations
   - Test MCCB selection
   - Test busbar sizing

2. Integration Tests (engine/design_builder.py)
   - Test complete design creation
   - Test with various configurations

3. UI Tests (Manual)
   - Test sidebar input validation
   - Test button interactions
   - Test session state persistence

4. Rendering Tests (Manual)
   - Verify SLD layout matches spec
   - Verify GA physical dimensions
   - Verify PDF page layout
```

---

**Architecture Last Updated:** April 2026
**Status:** Production-Ready ✅
