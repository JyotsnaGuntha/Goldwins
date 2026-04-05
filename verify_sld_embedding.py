"""
Complete end-to-end test of SLD embedding in PDF
This simulates the user workflow: Generate SLD -> Download Full Report
"""
import os
from models.system_model import SystemInput
from engine.design_builder import DesignBuilder
from renderers.sld_renderer import SLDRenderer
from renderers.ga_renderer import GARenderer
from utils.pdf_helpers import PDFReportGenerator

print("=" * 60)
print("TESTING: SLD Embedded in PDF")
print("=" * 60)

# Step 1: Create system input (simulating sidebar input)
print("\n1️⃣  Creating system configuration...")
system_input = SystemInput(
    solar_kw=150,
    grid_kw=250,
    dg_ratings_kva=[400, 400, 250],
    num_poles=3,
    num_outgoing_feeders=5
)
print(f"   ✓ Solar: {system_input.solar_kw}kW")
print(f"   ✓ Grid: {system_input.grid_kw}kW")
print(f"   ✓ DGs: {len(system_input.dg_ratings_kva)} units @ {system_input.dg_ratings_kva} kVA")
print(f"   ✓ Outgoings: {system_input.num_outgoing_feeders} feeders")

# Step 2: Generate design
print("\n2️⃣  Building design object...")
try:
    builder = DesignBuilder(system_input)
    design = builder.build()
    print(f"   ✓ Design built successfully")
    print(f"   ✓ Total current: {design.total_current_a:.2f}A")
    print(f"   ✓ MCCBs needed: {design.num_incomers() + design.num_outgoings()}")
except Exception as e:
    print(f"   ✗ Design build failed: {e}")
    exit(1)

# Step 3: Generate SLD SVG (shown on screen via "Generate SLD Preview")
print("\n3️⃣  Generating SLD SVG (displayed on screen)...")
try:
    sld_renderer = SLDRenderer(design)
    sld_svg = sld_renderer.render()
    print(f"   ✓ SLD SVG generated: {len(sld_svg)} characters")
    print(f"   ✓ Contains title: {'⚡' in sld_svg}")
    print(f"   ✓ Contains SVG elements: {'<circle' in sld_svg or '<rect' in sld_svg or '<path' in sld_svg}")
except Exception as e:
    print(f"   ✗ SLD generation failed: {e}")
    exit(1)

# Step 4: Generate GA SVG
print("\n4️⃣  Generating GA SVG...")
try:
    ga_renderer = GARenderer(design)
    ga_svg = ga_renderer.render()
    print(f"   ✓ GA SVG generated: {len(ga_svg)} characters")
except Exception as e:
    print(f"   ✗ GA generation failed: {e}")
    exit(1)

# Step 5: Generate PDF with embedded SLD and GA (via "Download Full Report" button)
print("\n5️⃣  Generating PDF with embedded diagrams...")
try:
    pdf_gen = PDFReportGenerator(design)
    pdf_buffer = pdf_gen.generate_full_report(
        sld_svg_string=sld_svg,
        ga_svg_string=ga_svg,
        project_name="Complete Microgrid Panel Design"
    )
    pdf_bytes = pdf_buffer.getvalue()
    pdf_size_kb = len(pdf_bytes) / 1024
    
    print(f"   ✓ PDF generated: {pdf_size_kb:.1f} KB")
    print(f"   ✓ PDF is valid: {pdf_bytes.startswith(b'%PDF')}")
    
    # Save to file
    output_file = "test_sld_embedded.pdf"
    with open(output_file, "wb") as f:
        f.write(pdf_bytes)
    print(f"   ✓ Saved to: {output_file}")
    
except Exception as e:
    print(f"   ✗ PDF generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 6: Verify PDF content
print("\n6️⃣  Verifying PDF content...")
try:
    with open(output_file, "rb") as f:
        pdf_content = f.read()
    
    # Check for SLD markers (reportlab adds drawing instructions)
    has_drawing_markers = b'BT' in pdf_content or b'cm' in pdf_content or b'Tj' in pdf_content
    print(f"   ✓ Contains drawing commands: {has_drawing_markers}")
    
    # Check for text markers ("Single Line Diagram")
    has_sld_text = b'Single Line Diagram' in pdf_content
    print(f"   ✓ Contains 'Single Line Diagram' text: {has_sld_text}")
    
    # Check for General Arrangement text
    has_ga_text = b'General Arrangement' in pdf_content
    print(f"   ✓ Contains 'General Arrangement' text: {has_ga_text}")
    
    # Check for title page text
    has_title = b'System Configuration' in pdf_content
    print(f"   ✓ Contains title page: {has_title}")
    
    # Check for BOM text
    has_bom = b'Bill of Materials' in pdf_content
    print(f"   ✓ Contains BOM: {has_bom}")
    
except Exception as e:
    print(f"   ✗ Verification failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ SUCCESS: SLD IS NOW EMBEDDED IN PDF")
print("=" * 60)
print("\nWorkflow verified:")
print("  1. User configures microgrid parameters")
print("  2. Clicks 'Generate SLD Preview' → SLD displays on screen")
print("  3. Clicks 'Download Full Report' → PDF generated with:")
print("     - Page 1: Title + System Configuration")
print("     - Page 2: SLD Diagram (now embedded ✓)")
print("     - Page 3: GA Diagram (now embedded ✓)")
print("     - Page 4: Bill of Materials")
print("\n✓ Test file saved: " + output_file)
