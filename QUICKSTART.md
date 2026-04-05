# 🚀 Quick Start Guide

## Installation & Setup

### 1. Install Dependencies
```bash
cd d:\Goldwins
pip install -r requirements.txt
```

### 2. Verify Installation
```bash
python -c "import streamlit, svgwrite, reportlab, cairosvg; print('✅ All dependencies installed')"
```

### 3. Run the Application
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📖 How to Use

### Step 1: Configure Your System
Left sidebar contains all input controls:
- **Solar Capacity** (kWp)
- **Grid Connection** (kW)
- **Number of DGs** (Diesel Generators)
  - Each DG rating in kVA
- **System Type** (3-phase or 4-pole)
- **Outgoing Feeders** (1-5 load circuits)

### Step 2: Generate SLD Preview
Click **"⚡ Generate SLD Preview"**

This will:
- Validate all inputs
- Calculate currents for each source
- Select appropriate MCCB ratings
- Draw the Single Line Diagram
- Display design metrics

**Note:** Nothing is downloaded yet - preview only on screen

### Step 3: Download Full Report
Click **"📥 Download Full Report"**

This will:
- Generate GA (physical panel layout)
- Create comprehensive PDF with:
  1. Title page + system summary
  2. SLD (as embedded image)
  3. GA (physical arrangement)
  4. BOM (bill of materials table)
- Trigger download as `Microgrid_Panel_Full_Report.pdf`

---

## 🔧 Configuration & Customization

### Edit System Constants
File: `config/constants.py`

```python
SYSTEM_VOLTAGE = 415              # Change if using 240V, 380V, etc.
POWER_FACTOR = 0.8                # Default for solar/grid
SAFETY_FACTOR = 1.25              # Adjust MCCB selection margin

STANDARD_MCCBS = [                # Add/remove available ratings
    16, 20, 25, 32, 40, ...
]
```

### Modify Calculations
File: `engine/calculations.py`

```python
def calculate_current_from_kw(power_kw, voltage_v, pf):
    # Adjust formula if needed
    return power_kw * 1000 / (math.sqrt(3) * voltage_v * pf)
```

### Change SLD Layout
File: `config/constants.py`

```python
SVG_WIDTH = 1450                  # Diagram width
Y_SOURCES = 180                   # Source symbols Y position
COMPONENT_SPACING = 280           # Horizontal spacing
```

### Customize PDF Report
File: `utils/pdf_helpers.py`

```python
def _build_title_page(self, project_name):
    # Modify title, colors, content
    story.append(Paragraph(...))
```

---

## 📊 Example Configurations

### Small Solar System
```
Solar: 50 kWp
Grid: 100 kW
DGs: 1 × 125 kVA
Outgoings: 2
System: 4-pole
```

### Medium Microgrid
```
Solar: 100 kWp
Grid: 120 kW
DGs: 2 × 250 kVA
Outgoings: 3
System: 4-pole (TYPICAL)
```

### Large Industrial
```
Solar: 500 kWp
Grid: 500 kW
DGs: 4 × 500 kVA
Outgoings: 5
System: 4-pole
```

---

## 🧠 How It Works (Technical)

### Data Flow
```
User Input (Sidebar)
    ↓
SystemInput (dataclass)
    ↓
DesignBuilder.build()
    ↓
DesignObject (complete design)
    ↓
Renderers (SLD, GA, BOM)
    ↓
Display + PDF Generation
```

### Calculation Examples

**Solar Incomer (100 kWp):**
```
Current = 100,000 / (√3 × 415 × 0.8)
        = 100,000 / 574.8
        = 173.9 A

MCCB = 173.9 × 1.25 = 217.4 A
Selected: 250A (next standard rating)
```

**DG Incomer (250 kVA):**
```
Current = 250,000 / (√3 × 415)
        = 250,000 / 719.1
        = 347.8 A

MCCB = 347.8 × 1.25 = 434.75 A
Selected: 500A (next standard rating)
```

---

## 🎨 Design Features

### SLD Rendering
- **Sources:** DG (circle), Grid (tower), Solar (panel)
- **Protection:** MCCBs with arc symbols
- **Busbar:** Red horizontal line
- **Controller:** Purple MGC box
- **Communication:** Dashed lines

### GA Rendering
- **Panel:** Black outline with dimensions
- **Busbar:** Red runs with height labels
- **MCCBs:** Stacked with terminals
- **Layout:** Two-column arrangement

### BOM Table
- Serial numbers
- Component names
- Ratings (A, kVA)
- Pole configuration
- Quantities

---

## ✅ Verification Checklist

After running, verify:
- [ ] Sidebar inputs accept values
- [ ] "Generate" button creates SLD
- [ ] SLD displays electrical diagram
- [ ] BOM preview shows all components
- [ ] "Download" button triggers PDF download
- [ ] PDF has 4 pages (Title, SLD, GA, BOM)
- [ ] All MCCBs correctly rated for current
- [ ] Calculations match expected formulas

---

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | Run `pip install -r requirements.txt` |
| PNG conversion fails | Install cairosvg: `pip install cairosvg` |
| PDF missing images | Ensure cairosvg is working |
| Streamlit freezes | Check input validation errors in terminal |
| Numbers seem wrong | Verify POWER_FACTOR in constants.py |

---

## 📞 Getting Help

1. **Check terminal output** for error messages
2. **Review README.md** for architecture details
3. **Inspect log files** in `.streamlit/` directory
4. **Test individual modules** in Python REPL

---

## 🚀 Next Steps

- [ ] Run the app and test with sample configuration
- [ ] Export a PDF report for review
- [ ] Customize colors/theme in `ui/styles.py`
- [ ] Add logo/branding in assets/
- [ ] Deploy to Streamlit Cloud or server
- [ ] Share with stakeholders

---

**Happy designing! ⚡**
