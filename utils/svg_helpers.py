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
    Convert SVG string to PNG using cairosvg
    
    Args:
        svg_string: SVG content as string
        output_path: Optional path to save PNG. If None, creates temp file
        width: PNG width in pixels
        height: PNG height in pixels
    
    Returns:
        Path to generated PNG file, or None if conversion failed
    """
    try:
        import cairosvg
        
        # Create temporary file if no output path specified
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            output_path = temp_file.name
            temp_file.close()
        
        # Convert SVG to PNG
        png_buffer = io.BytesIO()
        cairosvg.svg2png(
            bytestring=svg_string.encode('utf-8'),
            write_to=png_buffer,
            output_width=width,
            output_height=height
        )
        
        # Write to file
        with open(output_path, 'wb') as f:
            f.write(png_buffer.getvalue())
        
        return output_path
    
    except ImportError as e:
        print(f"Warning: cairosvg not installed. SVG-to-PNG conversion skipped. Error: {e}")
        return None
    except Exception as e:
        print(f"Error converting SVG to PNG: {e}")
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
