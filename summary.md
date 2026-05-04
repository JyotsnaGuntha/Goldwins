# Microgrid Panel Designer Technical Summary

## Project Objective

The objective of Microgrid Panel Designer is to automate the design workflow for low-voltage microgrid panels. The application computes electrical ratings, sizes the main busbar, generates engineering drawings, builds a BOM, and exports production-ready documents from a single data entry flow.

The implementation keeps the engineering logic in Python and uses a `pywebview` desktop shell so the same calculations power both the interactive UI and the exported reports.

## Problem Statement

Manual panel design typically involves repeated work across spreadsheets, drawing tools, and report templates. That process is slow, error-prone, and hard to keep consistent when source ratings, breaker selections, or panel dimensions change.

This project addresses that problem by centralizing the design logic in one application that can:

- validate user input before generation
- derive electrical ratings from source data
- size the panel from actual equipment footprints and clearances
- produce SLD, GA, BOM, and report exports from the same computed design state

## Methodology

The system follows a compute, render, and export pipeline:

1. Collect design inputs in the browser UI.
2. Normalize and validate the payload in the Python bridge.
3. Run electrical calculations for incoming and outgoing sources.
4. Derive geometry, busbar sizing, and MCCB schedules from the calculated state.
5. Render SVG diagrams for SLD and GA views.
6. Build BOM records and export deliverables.

This approach ensures that the previewed design and exported documents are generated from the same data path.

## System Architecture

The project is organized into five main layers:

1. Desktop host: [main.py](main.py)
2. Bridge/API layer: [api/bridge.py](api/bridge.py)
3. Core compatibility layer: [core/](core)
4. Domain logic and generators: [src/](src)
5. Frontend UI: [ui/](ui)

### Desktop Host

[main.py](main.py) creates the `pywebview` window, selects the Qt backend, resolves packaged resources, and loads [ui/index.html](ui/index.html). The compatibility launchers [app.py](app.py) and [run_app.py](run_app.py) both forward to `main()`.

### Bridge/API Layer

[api/bridge.py](api/bridge.py) is the main runtime orchestration layer exposed to JavaScript. It holds application state such as:

- current theme
- the last submitted payload
- the active MCCB database, if one has been loaded

It exposes the actions used by the frontend:

- `get_state()`
- `set_theme(theme)`
- `generate(payload)`
- `export_pdf(payload)`
- `export_ga_pdf(payload)`
- `export_excel(payload)`

### Core Layer

The `core/` package provides compatibility wrappers and export helpers:

- [core/sld.py](core/sld.py): exposes SLD calculations, primitive drawing helpers, and SLD generation
- [core/ga.py](core/ga.py): exposes GA dimensioning, theme colors, and GA SVG generation
- [core/utils.py](core/utils.py): re-exports shared utility functions from `src/utils.py`
- [core/bom.py](core/bom.py): builds the technical report PDF, GA PDF, BOM Excel, and file-download responses
- [core/constants.py](core/constants.py): shared constants used by the legacy compatibility surface

### Domain Layer

The `src/` package contains the actual engineering logic:

- [src/utils.py](src/utils.py): MCCB database loading, standard-rating selection, current calculations, busbar sizing, and theme helpers
- [src/constants.py](src/constants.py): standards, clearances, palettes, and geometry constants
- [src/sld/](src/sld): SLD calculations, drawing primitives, and SVG generation
- [src/ga/](src/ga): panel dimensioning, theme palettes, and GA SVG generation
- [src/bom/](src/bom): BOM item modeling and export helpers

### Frontend Layer

The UI is a browser-based frontend located in `ui/`:

- [ui/index.html](ui/index.html): control layout and output containers
- [ui/style.css](ui/style.css): layout, theming, and responsive styling
- [ui/app.js](ui/app.js): event wiring, payload collection, bridge calls, and preview updates

## Tools And Technologies Used

The project uses the following technologies and libraries:

- Python: core application runtime and engineering logic
- `pywebview`: desktop host for the HTML/CSS/JS UI
- HTML, CSS, JavaScript: frontend interface and interaction layer
- `pandas`: tabular data handling and Excel export
- `openpyxl`: workbook output support
- `reportlab`: PDF generation for technical and GA reports
- `svglib`: SVG-to-ReportLab conversion for diagram embedding
- `svgwrite`: SVG construction for SLD and GA drawings
- `PyInstaller`: desktop packaging for Windows distribution
- `PySide6` and `QtPy`: Qt backend used by the desktop shell

## Data Extraction And Validation Logic

The application accepts design inputs from the UI and normalizes them before any engineering output is generated.

### Input Normalization

In [api/bridge.py](api/bridge.py), the payload is sanitized using small conversion helpers that coerce values into integers or floats and fill missing list values with defaults. The bridge validates the key design constraints before generation:

- busbar material must be `Copper` or `Aluminium`
- system poles must be `3` or `4`
- outgoing feeder count must be at least one

### MCCB Data Extraction

The project supports loading an MCCB dimension database from Excel. That logic lives in [src/utils.py](src/utils.py) and reads the workbook with dynamic header detection. It looks for rating, height, width, and depth columns, then builds a rating-indexed lookup table.

If no external database is available, the application falls back to the built-in MCCB dimension set in `src/constants.py`.

The loaded or fallback database is used to:

- resolve MCCB footprint dimensions
- compute row widths and panel geometry
- generate schedule rows in reports
- size the GA drawing around the actual equipment footprint

### Rating Selection

Outgoing feeders are normalized to standard MCCB ratings using `get_standard_rating()`. Incoming equipment uses a 1.25x safety margin through `get_mccb_rating()` so the selected breaker rating is always at or above the calculated current.

## Implementation Details

### Source Handling

[src/utils.py](src/utils.py) contains the reusable electrical helpers that support the rest of the application. It calculates current from power or kVA, determines recommended MCCB ratings, and provides theme and busbar helpers used by both drawing and export code.

### SLD Implementation

[src/sld/calculations.py](src/sld/calculations.py) computes the source currents and breaker ratings. [src/sld/components.py](src/sld/components.py) draws the electrical primitives, and [src/sld/generator.py](src/sld/generator.py) lays them out into a single-line diagram SVG.

### GA Implementation

[src/ga/dimensions.py](src/ga/dimensions.py) calculates panel size from actual MCCB dimensions, busbar chamber height, and spacing rules. [src/ga/styles.py](src/ga/styles.py) provides theme-aware color palettes, and [src/ga/generator.py](src/ga/generator.py) renders the front and side GA views.

### BOM and Export Implementation

[src/bom/generator.py](src/bom/generator.py) converts the computed design into BOM line items. [src/bom/exports.py](src/bom/exports.py) contains the report-generation helpers, and [core/bom.py](core/bom.py) adapts those helpers for the desktop runtime, adds safe logo handling, and prepares final PDF and Excel output.

### UI and Bridge Implementation

[api/bridge.py](api/bridge.py) acts as the controller between the frontend and the engineering engine. It validates input, stores state, coordinates diagram generation, and triggers exports. The UI in [ui/app.js](ui/app.js) sends payloads to the bridge and updates the preview areas with returned SVG and summary data.

## Processing Workflow

The main workflow is centered in [api/bridge.py](api/bridge.py):

1. The UI submits a payload through the JS bridge.
2. The bridge validates and normalizes the input values.
3. `SystemCalculations` computes source currents and incomer MCCB ratings.
4. Busbar sizing is derived from total current and busbar material.
5. GA panel dimensions are computed from MCCB footprints and clearances.
6. SLD and GA SVGs are generated.
7. BOM rows are assembled.
8. The bridge returns the full design payload to the UI.

Export follows the same design path, but the bridge regenerates light-themed SVG output for document readability and hands the results to the export helpers in [core/bom.py](core/bom.py).

## Engineering Logic

### SLD Generation

The SLD pipeline is implemented under [src/sld/](src/sld):

- [src/sld/calculations.py](src/sld/calculations.py) defines `SystemCalculations`, which computes:
  - solar current from kW
  - grid current from kW
  - DG currents from kVA
  - DG MCCB ratings
  - solar and grid MCCB ratings
  - total busbar current
- [src/sld/components.py](src/sld/components.py) draws the primitive electrical symbols:
  - MCCB
  - transmission tower
  - solar array
  - microgrid controller
- [src/sld/generator.py](src/sld/generator.py) lays out the full SLD SVG, including source branches, busbar, outgoing feeders, and communication lines

### GA Generation

The GA pipeline is implemented under [src/ga/](src/ga):

- [src/ga/dimensions.py](src/ga/dimensions.py) computes physical panel dimensions from actual MCCB footprints, busbar chamber height, clearances, and duct space
- [src/ga/styles.py](src/ga/styles.py) provides theme-aware GA colors
- [src/ga/generator.py](src/ga/generator.py) builds the full front and side elevation SVG with dimension arrows, mounting plate, plinth, and spec rendering

### BOM Generation

The BOM pipeline is implemented under [src/bom/](src/bom):

- [src/bom/generator.py](src/bom/generator.py) builds `BOMItem` objects and groups repeated MCCB items with `Counter`
- [src/bom/exports.py](src/bom/exports.py) provides PDF and Excel export helpers

The BOM includes:

- incomer MCCBs
- outgoing feeder MCCBs
- main busbar
- microgrid controller
- control cable
- power/consumable cable allowance
- control panel enclosure

## Export And Reporting

[core/bom.py](core/bom.py) is responsible for producing the user-facing deliverables:

- technical report PDF
- standalone GA PDF
- BOM Excel workbook
- file-download payloads for the frontend

It also contains runtime-safe logo resolution so the report footer works both from source and from a frozen PyInstaller build.

Export output is intentionally normalized to light colors even when the UI theme is dark, which avoids unreadable diagrams in printed documents.

## Results

The implemented system produces the following outputs from one design workflow:

- validated microgrid design inputs
- calculated incomer and outgoing MCCB ratings
- SLD SVG for electrical topology review
- GA SVG for internal layout review
- technical report PDF with diagrams, schedules, and notes
- standalone GA PDF
- BOM Excel workbook

The current implementation also improves consistency by ensuring that the same source data drives calculations, drawings, schedules, and exported files.

## Conclusions

The project successfully consolidates panel design tasks into a single desktop application. It reduces manual duplication, makes breaker and busbar sizing reproducible, and keeps design output synchronized across preview and export modes.

The architecture is modular enough to support ongoing refinement of the electrical rules, UI workflow, or export formatting without rewriting the entire system.

## Implemented Components To Date

### Runtime And Packaging

- [main.py](main.py): desktop application entrypoint
- [app.py](app.py): legacy compatibility launcher
- [run_app.py](run_app.py): compatibility launcher
- [main.spec](main.spec): PyInstaller packaging configuration
- [assets/](assets): application icon and other packaged resources
- `build/`: generated PyInstaller build output

### Application Logic

- [api/bridge.py](api/bridge.py): orchestration, validation, state, export coordination
- [core/bom.py](core/bom.py): report generation and file export
- [core/ga.py](core/ga.py): GA compatibility wrapper
- [core/sld.py](core/sld.py): SLD compatibility wrapper
- [core/utils.py](core/utils.py): shared utility compatibility wrapper

### Engineering Modules

- [src/utils.py](src/utils.py): calculations, ratings, database loading, theme helpers
- [src/constants.py](src/constants.py): shared constants and palettes
- [src/sld/calculations.py](src/sld/calculations.py): electrical calculations
- [src/sld/components.py](src/sld/components.py): SLD primitives
- [src/sld/generator.py](src/sld/generator.py): SLD SVG generation
- [src/ga/dimensions.py](src/ga/dimensions.py): panel geometry
- [src/ga/styles.py](src/ga/styles.py): GA color themes
- [src/ga/generator.py](src/ga/generator.py): GA SVG generation
- [src/bom/generator.py](src/bom/generator.py): BOM item modeling
- [src/bom/exports.py](src/bom/exports.py): PDF and Excel export support

### Frontend

- [ui/index.html](ui/index.html): layout and controls
- [ui/style.css](ui/style.css): visual styling and responsiveness
- [ui/app.js](ui/app.js): bridge integration and preview handling

### Data And Legacy Files

- `BusBar_dimensions.xlsx`: sizing data source
- `Pole_modification.xlsx`: supporting engineering data
- [Electricpanel.py](Electricpanel.py): legacy monolithic implementation retained for reference
- [app.py.backup](app.py.backup): backup launcher file

## Operational Notes

- The desktop app is started from [main.py](main.py) in normal source runs.
- `pywebview` uses the Qt backend and the frontend is loaded from the local `ui/` folder.
- PDF generation depends on `reportlab` and SVG-to-drawing conversion through `svglib`.
- Excel export depends on `pandas` and `openpyxl`.
- The current architecture keeps calculations in Python so the same data drives UI previews and exported documents.
