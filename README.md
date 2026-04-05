# ⚡ Smart Microgrid Panel Design Tool

A professional, modular, production-grade Streamlit application for generating electrical engineering diagrams and documentation for microgrid systems.

---

## 🎯 Project Overview

This application transforms user inputs (solar capacity, grid connection, diesel generators) into a complete engineering package:

- **Single Line Diagram (SLD)** - Electrical schematic showing all connections
- **General Arrangement (GA)** - Physical panel layout with component placement
- **Bill of Materials (BOM)** - Comprehensive equipment list and specifications
- **Professional PDF Report** - Complete documentation for stakeholder review

---

## 🏗️ Modular Architecture

### Directory Structure

```
project_root/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── config/
│   ├── __init__.py
│   └── constants.py               # System constants & parameters
├── models/
│   ├── __init__.py
│   └── system_model.py            # Data models (SystemInput, DesignObject)
├── engine/
│   ├── __init__.py
│   ├── calculations.py            # Electrical calculations
│   ├── mccb_selection.py          # MCCB rating selection (optional)
│   ├── sizing.py                  # Component sizing (optional)
│   └── design_builder.py          # Orchestrates design creation
├── renderers/
│   ├── __init__.py
│   ├── sld_renderer.py            # Single Line Diagram renderer
│   ├── ga_renderer.py             # General Arrangement renderer
│   └── bom_generator.py           # Bill of Materials generator
├── utils/
│   ├── __init__.py
│   ├── svg_helpers.py             # SVG to PNG conversion
│   └── pdf_helpers.py             # PDF report generation
├── ui/
│   ├── __init__.py
│   ├── sidebar.py                 # Input controls & sidebar
│   └── styles.py                  # Theming & styling
└── assets/                        # Images, logos, etc.
```

---

## 🧠 Core Concepts

### 1. **SystemInput** Model
Represents all user-provided parameters:
```python
SystemInput(
    solar_kw=100,
    grid_kw=120,
    dg_ratings_kva=[250, 250],  # Multiple DGs
    num_poles=4,
    num_outgoing_feeders=3
)
```

### 2. **DesignObject** Model
Computed output containing:
- **Incomers** - Sources with MCCB ratings
- **Outgoings** - Load feeders with MCCB values
- **Busbar** - Sizing and material specs
- **Controller** - MGC specifications
- **Total Current** - System aggregate current

### 3. **Separation of Concerns**
- **`engine/`** - Pure calculations, no UI/rendering
- **`renderers/`** - Only render from DesignObject, no calculations
- **`ui/`** - Only input collection and display

---

## 🔌 Electrical Calculations

### Current Calculation
- **Solar/Grid (kW)**: I = P / (√3 × V × PF)
  - Default PF = 0.8
- **DGs (kVA)**: I = S / (√3 × V)
  - PF = 1.0

### MCCB Selection
1. Apply 1.25× safety factor to calculated current
2. Select next standard rating from: [16, 20, 25, 32, 40, ... 1600]

### Busbar Sizing
Automatically calculated based on total system current using:
- ~60A per 50×10mm aluminium busbar
- Scale up for larger systems

---

## 🎨 UX/UI Behavior

### "Generate SLD Preview" Button
**Action:** Generates only the Single Line Diagram
```python
1. Validate SystemInput
2. Create DesignObject (calculations)
3. Render SLD from DesignObject
4. Store in session_state
5. Display on screen
```

**Output:** None downloaded - only displayed

### "Download Full Report" Button
**Action:** Generates ONE comprehensive PDF
```python
1. Reuse stored DesignObject (no recalculation)
2. Generate GA from DesignObject
3. Generate BOM from DesignObject
4. Create PDF with:
   - Title Page (System Summary)
   - Page 2: SLD as embedded image
   - Page 3: GA layout
   - Page 4: BOM table
5. Trigger single download
```

---

## 🖼️ Rendering Pipeline

### SLD Renderer (`sld_renderer.py`)
```
DesignObject → SVG String
  ├── Draw Sources (DG, Grid, Solar)
  ├── Draw MCCBs (Incomers)
  ├── Draw Main Busbar
  ├── Draw MGC Controller
  ├── Draw Communication Lines
  └── Draw Outgoing Feeders
```

**Output:** SVG as base64 string (displayed inline)

### GA Renderer (`ga_renderer.py`)
```
DesignObject → SVG String
  ├── Draw Panel Outline
  ├── Draw Busbar Runs
  ├── Draw MCCB Symbols (physical layout)
  └── Add Dimensions
```

**Output:** SVG with physical measurements

### BOM Generator (`bom_generator.py`)
```
DesignObject → List of Data Rows
  ├── Incomer MCCBs
  ├── Outgoing MCCBs
  ├── Busbar Details
  ├── Controller Info
  └── System Summary
```

**Output:** Data table (for PDF and display)

---

## 📊 Session State Management

```python
st.session_state["design"]        # DesignObject - persists between reruns
st.session_state["sld_svg"]       # SVG string
st.session_state["sld_png_path"]  # Path to converted PNG
st.session_state["ga_png_path"]   # Path to converted GA PNG
```

**Purpose:** Avoid recalculation on Download button click

---

## 🚀 Running the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Streamlit
```bash
streamlit run app.py
```

### 3. Access
Open browser to `http://localhost:8501`

---

## 🔧 Customization

### Modify Constants
Edit `config/constants.py`:
```python
SYSTEM_VOLTAGE = 415          # Change system voltage
STANDARD_MCCBS = [...]        # Add/remove MCCB ratings
SAFETY_FACTOR = 1.25          # Adjust safety margin
```

### Add New Source Types
Modify `engine/design_builder.py`:
```python
def _build_incomers(self):
    # Add logic for new sources (Wind, Battery, etc.)
```

### Change SLD Layout
Edit `renderers/sld_renderer.py`:
```python
# Adjust Y_SOURCES, Y_DIVISION, COMPONENT_SPACING in constants.py
```

### Customize PDF Report
Edit `utils/pdf_helpers.py`:
```python
def _build_title_page(self):
    # Modify title page content and styling
```

---

## 📚 Key Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web UI framework |
| `svgwrite` | SVG diagram creation |
| `reportlab` | PDF generation |
| `cairosvg` | SVG → PNG conversion |
| `Pillow` | Image handling |

---

## 🎓 Design Patterns Used

1. **Separation of Concerns**
   - Models: Data structures only
   - Engines: Calculations only
   - Renderers: Rendering only

2. **Builder Pattern**
   - `DesignBuilder` constructs complex `DesignObject`
   - Encapsulates calculation logic

3. **Factory Pattern**
   - `SLDRenderer`, `GARenderer` create appropriate outputs

4. **Session State Pattern**
   - Persist computed design across Streamlit reruns

---

## ✅ Best Practices Implemented

- ✅ **No Duplicate Logic** - Single calculation source
- ✅ **Clean Imports** - Modular package structure
- ✅ **Type Hints** - Full type annotations
- ✅ **Error Handling** - Input validation and error messages
- ✅ **Documentation** - Docstrings for all functions
- ✅ **Constants** - Centralized configuration
- ✅ **Session Management** - Efficient state handling
- ✅ **Professional Styling** - Dark theme with gradients

---

## 🐛 Troubleshooting

### SVG Not Converting to PNG
- Ensure `cairosvg` is installed: `pip install cairosvg`
- Check system has cairo libraries installed
- On Windows, use pre-built wheels: `pip install cairosvg==2.7.0`

### PDF Generation Fails
- Verify `reportlab` is installed
- Check PNG files exist before PDF creation
- Review error logs in terminal

### Streamlit Cache Issues
- Clear cache: `streamlit cache clear`
- Restart Streamlit server

---

## 📝 Example Usage Flow

1. **User opens app**
   - Sidebar loads with default values
   - App shows welcome screen

2. **User configures system**
   - Sets Solar: 100 kWp
   - Sets Grid: 120 kW
   - Adds 2 DGs (250 kVA each)
   - Selects 3 outgoing feeders

3. **User clicks "Generate SLD Preview"**
   - App creates DesignObject with all calculations
   - SLD rendered and displayed on screen
   - BOM preview shown in expander

4. **User clicks "Download Full Report"**
   - GA rendered
   - PDF created with 4 pages:
     - Title/Summary
     - SLD
     - GA
     - BOM
   - PDF downloaded

---

## 🔐 Security Considerations

- Input validation prevents injection attacks
- No database/external API calls (local processing)
- Temporary PNG files cleaned up after PDF generation
- Session state is user/browser-local (no cross-user data leaks)

---

## 📄 License & Credits

Professional electrical engineering tool for microgrid design.
Built with Streamlit for rapid prototyping and deployment.

---

## 📧 Support

For issues, feature requests, or custom configurations, contact the engineering team.

---

**Last Updated:** April 2026
**Version:** 2.0 (Refactored, Production-Ready)
