"""
UI Styling - Dual theme (Dark & Light) with dynamic switching
"""

import streamlit as st


DARK_THEME_CSS = """
<style>
    .stApp {
        background: linear-gradient(135deg, #020617, #0f172a);
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }
    
    /* Main Text Colors - Dark Theme */
    body, p, span, div {
        color: #e2e8f0 !important;
    }
    
    /* Main Title */
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        color: #a78bfa;
        margin-bottom: 30px;
        text-shadow: 0 0 20px rgba(167, 139, 250, 0.3);
    }
    
    /* Section Titles */
    .section-title {
        font-size: 22px;
        font-weight: 600;
        color: #c4b5fd;
        margin-top: 25px;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(196, 181, 253, 0.2);
        padding-bottom: 5px;
    }
    
    /* Sidebar Styling - Complete Dark Theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #1e293b) !important;
        border-right: 1px solid rgba(124, 58, 237, 0.2) !important;
    }
    
    /* Sidebar text colors */
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #e2e8f0 !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
    }
    
    /* Sidebar inputs styling */
    [data-testid="stSidebar"] .stNumberInput input,
    [data-testid="stSidebar"] .stSelectbox select,
    [data-testid="stSidebar"] input {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-color: #475569 !important;
    }
    
    /* Expander Styling - Dark Theme */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary p,
    [data-testid="stSidebar"] .streamlit-expanderHeader p {
        color: #e2e8f0 !important;
        font-weight: 800 !important;
        font-size: 16px !important;
    }
    
    /* Labels - Dark Theme */
    [data-testid="stSidebar"] .stNumberInput label, 
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stNumberInput label p, 
    [data-testid="stSidebar"] .stSelectbox label p {
        color: #cbd5e1 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        opacity: 1 !important;
    }
    
    /* Main content expanders - Dark Theme */
    [data-testid="stExpander"] summary p,
    .streamlit-expanderHeader p {
        color: #e2e8f0 !important;
        font-weight: 800 !important;
        font-size: 16px !important;
    }
    
    /* Main content labels - Dark Theme */
    .stNumberInput label, 
    .stSelectbox label,
    .stNumberInput label p, 
    .stSelectbox label p {
        color: #e2e8f0 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        opacity: 1 !important;
    }
    
    /* Main content inputs styling - Dark Theme */
    .stNumberInput input,
    .stSelectbox select,
    input[type="number"],
    input[type="text"] {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-color: #475569 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #7c3aed, #6d28d9);
        color: white;
        border: none;
        padding: 12px 30px;
        font-size: 16px;
        border-radius: 8px;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5);
        background: linear-gradient(90deg, #8b5cf6, #7c3aed);
    }
    
    /* Increment/Decrement Buttons - Dark Theme */
    [data-testid="stNumberInput"] button {
        color: #e2e8f0 !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-color: #475569 !important;
    }
    
    [data-testid="stNumberInput"] button:hover {
        background-color: #475569 !important;
        color: #ffffff !important;
    }
    
    /* Help Icon Tooltip - Dark Theme */
    [data-testid="stTooltipIcon"] {
        color: #a78bfa !important;
    }
    
    /* Help text and tooltip - Dark Theme */
    [data-testid="stTooltipHoverTarget"] {
        color: #a78bfa !important;
    }
    
    /* Info/Success boxes */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Result cards */
    .result-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(124, 58, 237, 0.3);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        backdrop-filter: blur(10px);
    }
    
    /* Dividers */
    hr {
        border-color: rgba(124, 58, 237, 0.2);
    }
    
    /* Metric displays */
    [data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(124, 58, 237, 0.3);
        padding: 15px;
        border-radius: 12px;
    }
    
    /* Theme Toggle Button */
    .theme-toggle {
        position: fixed;
        top: 70px;
        right: 20px;
        z-index: 999;
        background: linear-gradient(90deg, #7c3aed, #6d28d9);
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
        transition: all 0.3s ease;
    }
    
    .theme-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5);
    }
</style>
"""

LIGHT_THEME_CSS = """
<style>
    .stApp {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9) !important;
        font-family: 'Inter', sans-serif;
        color: #1e293b !important;
    }
    
    /* Comprehensive text color coverage - Light Theme */
    * {
        color: #1e293b !important;
    }
    
    body, p, span, div, h1, h2, h3, h4, h5, h6, li, a, label {
        color: #1e293b !important;
    }
    
    /* Main Title */
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        color: #6d28d9 !important;
        margin-bottom: 30px;
        text-shadow: 0 0 10px rgba(109, 40, 217, 0.15);
    }
    
    /* Section Titles */
    .section-title {
        font-size: 22px;
        font-weight: 600;
        color: #7c3aed !important;
        margin-top: 25px;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(124, 58, 237, 0.3);
        padding-bottom: 5px;
    }
    
    /* Streamlit markdown text */
    .stMarkdown {
        color: #1e293b !important;
    }
    
    .stMarkdown p {
        color: #1e293b !important;
    }
    
    /* Headings throughout */
    h1, h2, h3, h4, h5, h6 {
        color: #1e293b !important;
    }
    
    /* Metric text */
    [data-testid="stMetricLabel"] {
        color: #475569 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #1e293b !important;
    }
    
    /* Sidebar Styling - Complete Light Theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8ecf1, #dce4ed) !important;
        border-right: 1px solid rgba(124, 58, 237, 0.1) !important;
    }
    
    /* Sidebar text colors - comprehensive */
    [data-testid="stSidebar"] * {
        color: #1e293b !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {
        color: #1e293b !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #1e293b !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #1e293b !important;
    }
    
    /* Sidebar inputs styling */
    [data-testid="stSidebar"] .stNumberInput input,
    [data-testid="stSidebar"] .stSelectbox select,
    [data-testid="stSidebar"] input {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border-color: #cbd5e1 !important;
    }
    
    /* Expander Styling - Light Theme */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary p,
    [data-testid="stSidebar"] .streamlit-expanderHeader p {
        color: #1e293b !important;
        font-weight: 800 !important;
        font-size: 16px !important;
    }
    
    /* Labels - Light Theme */
    [data-testid="stSidebar"] .stNumberInput label, 
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stNumberInput label p, 
    [data-testid="stSidebar"] .stSelectbox label p {
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        opacity: 1 !important;
    }
    
    /* Main content expanders - Light Theme */
    [data-testid="stExpander"] summary p,
    .streamlit-expanderHeader p {
        color: #1e293b !important;
        font-weight: 800 !important;
        font-size: 16px !important;
    }
    
    /* Main content labels - Light Theme */
    .stNumberInput label, 
    .stSelectbox label,
    .stNumberInput label p, 
    .stSelectbox label p {
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        opacity: 1 !important;
    }
    
    /* Main content inputs styling - Light Theme */
    .stNumberInput input,
    .stSelectbox select,
    input[type="number"],
    input[type="text"] {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border-color: #cbd5e1 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #7c3aed, #6d28d9);
        color: white;
        border: none;
        padding: 12px 30px;
        font-size: 16px;
        border-radius: 8px;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
        background: linear-gradient(90deg, #8b5cf6, #7c3aed);
    }
    
    /* Increment/Decrement Buttons - Light Theme */
    [data-testid="stNumberInput"] button {
        color: #1e293b !important;
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-color: #cbd5e1 !important;
    }
    
    [data-testid="stNumberInput"] button:hover {
        background-color: #f1f5f9 !important;
        color: #1e293b !important;
    }
    
    /* Help Icon Tooltip - Light Theme */
    [data-testid="stTooltipIcon"] {
        color: #7c3aed !important;
    }
    
    /* Help text and tooltip content - Light Theme */
    [data-testid="stTooltipHoverTarget"] {
        color: #7c3aed !important;
    }
    
    .stTooltip {
        color: #1e293b !important;
    }
    
    [role="tooltip"] {
        color: #1e293b !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Info/Success boxes */
    .stAlert {
        border-radius: 10px;
        color: #1e293b !important;
        background-color: #f0f0f0 !important;
    }
    
    .stAlert p {
        color: #1e293b !important;
    }
    
    /* Result cards */
    .result-card {
        background: rgba(241, 245, 249, 0.8) !important;
        border: 1px solid rgba(124, 58, 237, 0.2);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        color: #1e293b !important;
    }
    
    .result-card p,
    .result-card span,
    .result-card div {
        color: #1e293b !important;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(124, 58, 237, 0.2);
    }
    
    /* Metric displays */
    [data-testid="stMetric"] {
        background: rgba(241, 245, 249, 0.8) !important;
        border: 1px solid rgba(124, 58, 237, 0.2);
        padding: 15px;
        border-radius: 12px;
        color: #1e293b !important;
    }
    
    [data-testid="stMetric"] p,
    [data-testid="stMetric"] span,
    [data-testid="stMetric"] div {
        color: #1e293b !important;
    }
    
    /* Theme Toggle Button */
    .theme-toggle {
        position: fixed;
        top: 70px;
        right: 20px;
        z-index: 999;
        background: linear-gradient(90deg, #7c3aed, #6d28d9);
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
        transition: all 0.3s ease;
    }
    
    .theme-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5);
    }
</style>
"""


def apply_theme():
    """Apply theme based on session state"""
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    
    theme_css = DARK_THEME_CSS if st.session_state.theme == "dark" else LIGHT_THEME_CSS
    st.markdown(theme_css, unsafe_allow_html=True)


def get_theme_colors():
    """Get color values based on current theme"""
    if st.session_state.get("theme", "dark") == "dark":
        return {
            "bg": "#020617",
            "text": "#e2e8f0",
            "text_secondary": "#cbd5e1",
            "accent": "#a78bfa",
            "border": "#334155",
        }
    else:
        return {
            "bg": "#ffffff",
            "text": "#1e293b",
            "text_secondary": "#475569",
            "accent": "#7c3aed",
            "border": "#cbd5e1",
        }


def get_metric_style():
    """Get CSS for metric displays"""
    return ".stMetric { background-color: rgba(15, 23, 42, 0.8); border: 1px solid rgba(124, 58, 237, 0.3); }"
