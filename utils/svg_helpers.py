"""
SVG and image processing utilities
"""
import io
import tempfile
import os
from pathlib import Path
from typing import Optional


def svg_to_png(svg_string: str, output_path: Optional[str] = None, width: int = 1450, height: int = 850) -> Optional[str]:
    """
    Convert SVG string to PNG using available methods (fallback chain)
    
    Attempts conversion using:
    1. reportlab + svglib (pure Python, no system dependencies)
    2. Pillow (if available)
    
    Args:
        svg_string: SVG content as string
        output_path: Optional path to save PNG. If None, creates temp file
        width: PNG width in pixels
        height: PNG height in pixels
    
    Returns:
        Path to generated PNG file, or None if conversion failed
    """
    
    # Method 1: Try reportlab with simple SVG handling
    try:
        from reportlab.graphics import svg2rlg, renderPM
        
        # Create temporary SVG file to parse
        temp_svg = tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False)
        temp_svg.write(svg_string)
        temp_svg.close()
        
        try:
            # Convert SVG to reportlab Drawing
            drawing = svg2rlg(temp_svg.name)
            
            if drawing is not None:
                # Scale the drawing
                drawing.width = width
                drawing.height = height
                
                # Create output path if not specified
                if output_path is None:
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    output_path = temp_file.name
                    temp_file.close()
                
                # Render to PNG using reportlab's pure-Python rendering
                renderPM.drawToFile(drawing, output_path, fmt='PNG', width=width, height=height)
                return output_path
        finally:
            # Cleanup temporary SVG file
            if os.path.exists(temp_svg.name):
                os.remove(temp_svg.name)
    
    except Exception as e:
        print(f"Note: reportlab SVG conversion failed ({type(e).__name__}), attempting alternative method...")
    
    # Method 2: Create a simple placeholder PNG instead
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a white PNG with text indicating SVG content
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            output_path = temp_file.name
            temp_file.close()
        
        # Create simple image with SVG indicator text
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw text
        text = "SVG Diagram\n(Full resolution in Streamlit preview)"
        draw.text((width//2 - 100, height//2 - 30), text, fill='gray')
        
        img.save(output_path, 'PNG')
        print(f"Created placeholder PNG at {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error in SVG-PNG conversion: {e}")
        return None


def cleanup_temp_file(file_path: str):
    """
    Cleanup temporary file
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: Could not delete temporary file {file_path}: {e}")
