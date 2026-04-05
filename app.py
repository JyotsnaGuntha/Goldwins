"""
Streamlit Microgrid Design Tool - Main Application
Professional, modular, production-grade application
"""

import streamlit as st
import base64
from pathlib import Path

# ==================== LOCAL IMPORTS ====================
from config.constants import SVG_WIDTH, SVG_HEIGHT
from models.system_model import SystemInput, DesignObject
from engine.design_builder import DesignBuilder
from renderers.sld_renderer import SLDRenderer
from renderers.ga_renderer import GARenderer
from renderers.bom_generator import BOMGenerator
from utils.pdf_helpers import PDFReportGenerator
from utils.svg_helpers import svg_to_png, cleanup_temp_file
from ui.styles import apply_theme
from ui.sidebar import render_sidebar, render_control_buttons, render_system_summary


# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="Smart Microgrid Panel Design Tool",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SESSION STATE INITIALIZATION ====================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "design" not in st.session_state:
    st.session_state.design = None

if "sld_svg" not in st.session_state:
    st.session_state.sld_svg = None

if "ga_svg" not in st.session_state:
    st.session_state.ga_svg = None

if "sld_png_path" not in st.session_state:
    st.session_state.sld_png_path = None

if "ga_png_path" not in st.session_state:
    st.session_state.ga_png_path = None


# ==================== THEME TOGGLE CALLBACK ====================
def toggle_theme():
    """Toggle theme state - callback triggered on button click"""
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"


# ==================== APPLY THEME - FIRST (before rendering any content) ====================
apply_theme()


# ==================== THEME TOGGLE BUTTON ====================
# Create a container for the theme toggle button
col1, col2 = st.columns([0.95, 0.05])
with col2:
    theme_emoji = "🌙" if st.session_state.theme == "dark" else "☀️"
    st.button(theme_emoji, on_click=toggle_theme, key="theme_toggle", help="Toggle Dark/Light Theme")


# ==================== TITLE SECTION ====================
st.markdown(
    '<div class="main-title">Microgrid Panel Design Tool</div>',
    unsafe_allow_html=True
)
st.markdown(
    "Generate professional Single Line Diagrams, General Arrangements, and Bills of Materials for your microgrid system.",
    unsafe_allow_html=False
)


# ==================== SIDEBAR - INPUT COLLECTION ====================
system_input = render_sidebar()


# ==================== MAIN CONTENT AREA ====================
def display_sld_preview(design: DesignObject, sld_svg: str):
    """Display SLD preview on screen"""
    from ui.styles import get_theme_colors
    
    st.subheader("📋 Single Line Diagram (SLD) Preview")
    
    # Encode SVG to base64 for display
    b64_sld = base64.b64encode(sld_svg.encode('utf-8')).decode('utf-8')
    
    # Get theme-aware colors
    colors = get_theme_colors()
    
    # Display with styling
    st.markdown(
        f'''
        <div style="background:{colors['bg']}; padding:20px; border-radius:15px; border:1px solid {colors['border']};">
            <img src="data:image/svg+xml;base64,{b64_sld}" style="width:100%; max-width:1400px;">
        </div>
        ''',
        unsafe_allow_html=True
    )
    
    # Display design summary
    st.markdown("### Design Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Current", f"{design.total_current_a:.2f}A")
    
    with col2:
        st.metric("Incomers", design.num_incomers())
    
    with col3:
        st.metric("Outgoings", design.num_outgoings())
    
    with col4:
        st.metric("Busbar Runs", design.busbar.num_runs)


def display_bom_preview(design: DesignObject):
    """Display BOM preview in expander"""
    with st.expander("📄 Bill of Materials Preview"):
        bom_gen = BOMGenerator(design)
        bom_summary = bom_gen.generate_bom_summary()
        st.code(bom_summary, language="text")


# ==================== CONTROL BUTTONS ====================
generate_clicked, download_clicked = render_control_buttons()


# ==================== GENERATE BUTTON LOGIC ====================
if generate_clicked:
    try:
        # Validate input
        system_input.validate()
        
        # Show status
        with st.spinner("🔧 Generating design..."):
            # Build design object
            builder = DesignBuilder(system_input)
            design = builder.build()
            
            # Store in session state
            st.session_state.design = design
            
            # Generate SLD
            sld_renderer = SLDRenderer(design)
            sld_svg = sld_renderer.render()
            st.session_state.sld_svg = sld_svg
            
            # Convert to PNG for PDF (optional)
            sld_png_path = svg_to_png(sld_svg, width=int(SVG_WIDTH * 0.8), height=int(SVG_HEIGHT * 0.8))
            st.session_state.sld_png_path = sld_png_path
        
        # Display SLD
        st.success("✅ Design generated successfully!")
        display_sld_preview(design, sld_svg)
        
        # Display BOM preview
        display_bom_preview(design)
        
    except ValueError as e:
        st.error(f"❌ Input Validation Error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error generating design: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


# ==================== DOWNLOAD BUTTON LOGIC ====================
if download_clicked:
    if st.session_state.design is None:
        st.warning("⚠️ Please click 'Generate SLD Preview' first to create a design.")
    else:
        try:
            design = st.session_state.design
            sld_svg = st.session_state.sld_svg
            sld_png_path = st.session_state.sld_png_path
            
            with st.spinner("📝 Generating comprehensive PDF report..."):
                # Generate GA
                ga_renderer = GARenderer(design)
                ga_svg = ga_renderer.render()
                
                # Convert GA to PNG
                ga_png_path = svg_to_png(ga_svg, width=600, height=1200)
                
                # Generate PDF report
                pdf_gen = PDFReportGenerator(design)
                pdf_buffer = pdf_gen.generate_full_report(
                    sld_svg_string=sld_svg,
                    ga_svg_string=ga_svg,
                    sld_png_path=sld_png_path,
                    ga_png_path=ga_png_path,
                    project_name="Smart Microgrid Panel Design"
                )
                
                # Cleanup temporary PNG files
                if sld_png_path:
                    cleanup_temp_file(sld_png_path)
                if ga_png_path:
                    cleanup_temp_file(ga_png_path)
            
            # Offer download
            st.download_button(
                label="📥 Download Full PDF Report",
                data=pdf_buffer.getvalue(),
                file_name="Microgrid_Panel_Full_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            st.success("✅ PDF Report generated and ready for download!")
            
        except Exception as e:
            st.error(f"❌ Error generating PDF report: {str(e)}")
            import traceback
            st.error(traceback.format_exc())


# ==================== DISPLAY CACHED SLD (persists across theme changes) ====================
# If SLD was previously generated and cached in session state, display it
# This ensures the SLD persists when theme toggles without re-rendering
# Only display if we didn't just generate (to avoid duplicates)
if not generate_clicked and st.session_state.sld_svg is not None and st.session_state.design is not None:
    display_sld_preview(st.session_state.design, st.session_state.sld_svg)
    display_bom_preview(st.session_state.design)


# ==================== IDLE STATE ====================
if st.session_state.design is None:
    st.info(
        "👈 **Getting Started:**\n\n"
        "1. Configure your microgrid parameters in the left sidebar\n"
        "2. Click '⚡ Generate SLD Preview' to create the design and view the diagram\n"
        "3. Click '📥 Download Full Report' to generate a professional PDF with SLD, GA, and BOM"
    )
    
    # Show example/info
    st.markdown("### What This Tool Does")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            **📊 SLD Generation**
            - Sources (DG, Grid, Solar)
            - MCCB protection
            - Busbar routing
            - Load distribution
            """
        )
    
    with col2:
        st.markdown(
            """
            **📐 GA Layout**
            - Physical panel arrangement
            - Component spacing
            - Busbar positioning
            - Professional dimensions
            """
        )
    
    with col3:
        st.markdown(
            """
            **📄 Complete BOM**
            - All MCCBs listed
            - Busbar specifications
            - System summary
            - Equipment details
            """
        )


# ==================== FOOTER ====================
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #94a3b8; font-size: 12px; padding: 20px;">
        <p> Kirloskar Oil Engines Limited</p>
    </div>
    """,
    unsafe_allow_html=True
)