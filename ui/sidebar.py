"""
Sidebar UI Component - Input collection
"""
import streamlit as st
from models.system_model import SystemInput


def render_sidebar() -> SystemInput:
    """
    Render sidebar with input controls
    
    Returns:
        SystemInput object with all user parameters
    """
    with st.sidebar:
        st.header("⚙️ Design Parameters")
        
        # ==================== POWER INPUTS ====================
        with st.expander("📊 Capacity Inputs", expanded=True):
            solar_kw = st.number_input(
                "Solar (kWp)",
                value=100,
                min_value=0,
                step=10,
                help="Peak power capacity of solar system"
            )
            
            grid_kw = st.number_input(
                "Grid (kW)",
                value=120,
                min_value=0,
                step=10,
                help="Grid connection capacity"
            )
            
            num_poles = st.selectbox(
                "System Phases/Poles",
                [3, 4],
                index=1,
                help="3-phase or 4-pole (include neutral)"
            )
            
            num_dg = st.number_input(
                "Number of DGs",
                value=2,
                min_value=0,
                max_value=4,
                step=1,
                help="Add multiple diesel generators"
            )
        
        st.divider()
        
        # ==================== NUMBER OF OUTPUTS ====================
        num_outgoing_feeders = st.number_input(
            "Number of Outputs",
            value=3,
            min_value=1,
            max_value=5,
            step=1,
            help="Number of separate load circuits"
        )
        
        st.divider()
        
        # ==================== DG SPECIFICATIONS ====================
        dg_ratings = []
        if num_dg > 0:
            st.subheader("🔌 DG Specifications")
            for i in range(int(num_dg)):
                dg_rating = st.number_input(
                    f"DG {i+1} Rating (kVA)",
                    value=250,
                    min_value=10,
                    max_value=2000,
                    step=50,
                    key=f"dg_input_{i}",
                    help="Generator power rating in kVA"
                )
                dg_ratings.append(dg_rating)
        
        st.divider()
        
        # ==================== INFO & GUIDELINES ====================
        st.info(
            ""
        )
        
        # Create and return SystemInput object
        system_input = SystemInput(
            solar_kw=float(solar_kw),
            grid_kw=float(grid_kw),
            dg_ratings_kva=dg_ratings,
            num_poles=int(num_poles),
            num_outgoing_feeders=int(num_outgoing_feeders)
        )
        
        return system_input


def render_control_buttons() -> tuple[bool, bool]:
    """
    Render main control buttons
    
    Returns:
        Tuple of (generate_button_clicked, download_button_clicked)
    """
    col1, col2 = st.columns(2)
    
    with col1:
        generate_clicked = st.button(
            "⚡ Generate SLD Preview",
            use_container_width=True,
            key="generate_btn"
        )
    
    with col2:
        download_clicked = st.button(
            "📥 Download Full Report",
            use_container_width=True,
            key="download_btn"
        )
    
    return generate_clicked, download_clicked


def render_system_summary(system_input: SystemInput):
    """
    Display system input summary
    
    Args:
        system_input: SystemInput object to display
    """
    st.subheader("📋 Input Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Solar", f"{system_input.solar_kw:.0f} kWp")
    
    with col2:
        st.metric("Grid", f"{system_input.grid_kw:.0f} kW")
    
    with col3:
        st.metric("DGs", f"{system_input.num_dgs} units")
    
    if system_input.num_dgs > 0:
        with st.expander("DG Details"):
            for i, rating in enumerate(system_input.dg_ratings_kva):
                st.write(f"  DG {i+1}: {rating:.0f} kVA")
