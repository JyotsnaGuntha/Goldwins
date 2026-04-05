"""
PDF Report Generation Utilities
"""
import io
from typing import List, BinaryIO, Tuple
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, Preformatted, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from models.system_model import DesignObject
from renderers.bom_generator import BOMGenerator
from config.constants import PDF_MARGIN, PDF_TITLE_FONTSIZE, PDF_SECTION_FONTSIZE, PDF_NORMAL_FONTSIZE


class SVGDiagramScaler:
    """Intelligent SVG to PDF diagram scaling"""
    
    # Standard A4 paper in inches (portrait)
    A4_WIDTH = 8.27
    A4_HEIGHT = 11.69
    PTS_PER_INCH = 72.0
    
    @staticmethod
    def scale_svg_for_pdf(svg_string: str, diagram_name: str = "Diagram", max_margin: float = 0.5) -> Tuple[Flowable, str]:
        """
        Convert SVG to reportlab drawing with optimal scaling
        Fits entire diagram on single A4 page without cropping
        
        Args:
            svg_string: SVG content as string
            diagram_name: Name of diagram (for logging)
            max_margin: Margin in inches on each side
        
        Returns:
            Tuple of (Flowable drawing, orientation)
        """
        try:
            from svglib.svglib import svg2rlg
            import tempfile
            import os
            
            # Create temporary SVG file with UTF-8 encoding
            temp_svg = tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8')
            temp_svg.write(svg_string)
            temp_svg.close()
            
            try:
                # Convert SVG to reportlab drawing
                drawing = svg2rlg(temp_svg.name)
                if not drawing:
                    return None, "portrait"
                
                # Get SVG dimensions (svg2rlg returns in points/reportlab units)
                svg_width_pts = float(drawing.width) if drawing.width else 1087.5
                svg_height_pts = float(drawing.height) if drawing.height else 637.5
                
                # Convert to inches
                svg_width_in = svg_width_pts / SVGDiagramScaler.PTS_PER_INCH
                svg_height_in = svg_height_pts / SVGDiagramScaler.PTS_PER_INCH
                
                # Available space on A4-portrait with margins and heading space
                margin_total = 2 * max_margin  # Inches (top + bottom or left + right)
                heading_space = 0.8  # Space for title and description
                
                available_width = SVGDiagramScaler.A4_WIDTH - margin_total
                available_height = SVGDiagramScaler.A4_HEIGHT - margin_total - heading_space
                
                # Calculate scale factor to fit (use minimum to preserve aspect ratio)
                scale_w = available_width / svg_width_in
                scale_h = available_height / svg_height_in
                scale_factor = min(scale_w, scale_h)
                
                # Apply scaling
                final_width_in = svg_width_in * scale_factor
                final_height_in = svg_height_in * scale_factor
                
                # Set drawing dimensions in points
                drawing.width = final_width_in * SVGDiagramScaler.PTS_PER_INCH
                drawing.height = final_height_in * SVGDiagramScaler.PTS_PER_INCH
                
                return drawing, "portrait"
                
            finally:
                if os.path.exists(temp_svg.name):
                    os.remove(temp_svg.name)
                    
        except Exception as e:
            print(f"SVG scaling failed for {diagram_name}: {e}")
            import traceback
            traceback.print_exc()
            return None, "portrait"


class PDFReportGenerator:
    """Generate comprehensive PDF reports from design objects"""
    
    def __init__(self, design: DesignObject):
        """
        Initialize PDF generator
        
        Args:
            design: DesignObject to generate report from
        """
        self.design = design
        self.page_width, self.page_height = A4
        self.bom_gen = BOMGenerator(design)
    
    def generate_full_report(
        self,
        sld_svg_string: str,
        ga_svg_string: str,
        sld_png_path: str = None,
        ga_png_path: str = None,
        project_name: str = "Microgrid Panel Design"
    ) -> io.BytesIO:
        """
        Generate complete PDF report with all sections
        Full SLD and GA diagrams are embedded with intelligent scaling
        All diagrams sized to fit within standard A4 portrait pages without cropping
        
        Args:
            sld_svg_string: SVG string of SLD
            ga_svg_string: SVG string of GA
            sld_png_path: Optional path to pre-converted SLD PNG (fallback)
            ga_png_path: Optional path to pre-converted GA PNG (fallback)
            project_name: Title of the project
        
        Returns:
            BytesIO buffer containing PDF
        """
        buffer = io.BytesIO()
        
        # Scale SVG diagrams with optimal sizing for A4-portrait pages
        sld_drawing, _ = SVGDiagramScaler.scale_svg_for_pdf(sld_svg_string, "SLD")
        ga_drawing, _ = SVGDiagramScaler.scale_svg_for_pdf(ga_svg_string, "GA")
        
        # Create PDF document with portrait orientation
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=PDF_MARGIN,
            leftMargin=PDF_MARGIN,
            topMargin=PDF_MARGIN,
            bottomMargin=PDF_MARGIN
        )
        
        # Build story (pages)
        story = []
        
        # Page 1: Title Page
        story.extend(self._build_title_page(project_name))
        story.append(PageBreak())
        
        # Page 2: SLD (full diagram scaled intelligently)
        if sld_drawing:
            story.extend(self._build_sld_page_optimized(sld_drawing))
        elif sld_png_path:
            story.extend(self._build_sld_page(sld_png_path))
        else:
            story.append(Paragraph("Single Line Diagram (SLD)", self._get_styles()['Heading2']))
        story.append(PageBreak())
        
        # Page 3: GA (full diagram scaled intelligently)
        if ga_drawing:
            story.extend(self._build_ga_page_optimized(ga_drawing))
        elif ga_png_path:
            story.extend(self._build_ga_page(ga_png_path))
        else:
            story.append(Paragraph("General Arrangement (GA)", self._get_styles()['Heading2']))
        story.append(PageBreak())
        
        # Page 4: BOM
        story.extend(self._build_bom_page())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
   
    
    def _build_sld_page_optimized(self, drawing) -> List:
        """
        Build SLD page with optimized scaled drawing (full diagram, no cropping)
        
        Args:
            drawing: reportlab Drawing object (already scaled optimally)
        
        Returns:
            List of reportlab elements
        """
        styles = self._get_styles()
        story = [
            Paragraph("Single Line Diagram (SLD)", styles['Heading2']),
            Spacer(1, 0.15*inch),
            drawing,
            Spacer(1, 0.15*inch),
            Paragraph(
                "The Single Line Diagram represents the complete electrical architecture of the microgrid system, "
                "including all generation sources (Grid, Solar, DG), the main busbar, and load feeders with protection devices. "
                "The diagram is scaled to fit the page while maintaining full detail and aspect ratio.",
                styles['Normal']
            )
        ]
        return story
    
    def _build_ga_page_optimized(self, drawing) -> List:
        """
        Build GA page with optimized scaled drawing (full diagram, no cropping)
        
        Args:
            drawing: reportlab Drawing object (already scaled optimally)
        
        Returns:
            List of reportlab elements
        """
        styles = self._get_styles()
        story = [
            Paragraph("General Arrangement (GA)", styles['Heading2']),
            Spacer(1, 0.15*inch),
            drawing,
            Spacer(1, 0.15*inch),
            Paragraph(
                "The General Arrangement diagram displays the physical layout and positioning of all electrical components "
                "in the microgrid panel, including MCCBs, busbars, connections, and control devices. "
                "The diagram is scaled to fit the page while maintaining full detail and aspect ratio.",
                styles['Normal']
            )
        ]
        return story
    
    def _build_sld_from_svg(self, svg_string: str) -> List:
        """
        Build SLD page content from SVG string
        
        Args:
            svg_string: SVG content as string
        
        Returns:
            List of reportlab elements
        """
        try:
            from svglib.svglib import svg2rlg
            import tempfile
            import os
            
            # Create temporary SVG file with proper UTF-8 encoding
            temp_svg = tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8')
            temp_svg.write(svg_string)
            temp_svg.close()
            
            try:
                # Convert SVG to drawing
                drawing = svg2rlg(temp_svg.name)
                if drawing:
                    drawing.width = 6.5*inch
                    drawing.height = 4*inch
                    
                    styles = self._get_styles()
                    story = [
                        Paragraph("Single Line Diagram (SLD)", styles['Heading2']),
                        Spacer(1, 0.3*inch),
                        drawing,
                        Spacer(1, 0.2*inch),
                        Paragraph("This diagram shows the complete electrical layout of your microgrid system.", styles['Normal'])
                    ]
                    return story
            finally:
                if os.path.exists(temp_svg.name):
                    os.remove(temp_svg.name)
        except Exception as e:
            print(f"SVG to PDF conversion for SLD failed: {e}")
        
        return None
    
    def _build_ga_from_svg(self, svg_string: str) -> List:
        """
        Build GA page content from SVG string
        
        Args:
            svg_string: SVG content as string
        
        Returns:
            List of reportlab elements
        """
        try:
            from svglib.svglib import svg2rlg
            import tempfile
            import os
            
            # Create temporary SVG file with proper UTF-8 encoding
            temp_svg = tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8')
            temp_svg.write(svg_string)
            temp_svg.close()
            
            try:
                # Convert SVG to drawing
                drawing = svg2rlg(temp_svg.name)
                if drawing:
                    drawing.width = 5.5*inch
                    drawing.height = 7*inch
                    
                    styles = self._get_styles()
                    story = [
                        Paragraph("General Arrangement (GA)", styles['Heading2']),
                        Spacer(1, 0.3*inch),
                        drawing,
                        Spacer(1, 0.2*inch),
                        Paragraph("This diagram shows the physical layout and positioning of all components.", styles['Normal'])
                    ]
                    return story
            finally:
                if os.path.exists(temp_svg.name):
                    os.remove(temp_svg.name)
        except Exception as e:
            print(f"SVG to PDF conversion for GA failed: {e}")
        
        return None
    
    def _build_title_page(self, project_name: str) -> List:
        """Build title page content"""
        styles = self._get_styles()
        story = []
        
        # Spacing
        story.append(Spacer(1, 40*mm))
        
        # Title
        story.append(Paragraph(
            project_name,
            ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=PDF_TITLE_FONTSIZE,
                textColor=colors.HexColor("#7c3aed"),
                alignment=1,  # Center alignment
                spaceAfter=20
            )
        ))
        
        story.append(Paragraph(
            "⚡ Smart Microgrid Panel Design",
            ParagraphStyle(
                'SubTitle',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor("#a78bfa"),
                alignment=1,
                spaceAfter=30
            )
        ))
        
        # Divider
        story.append(Spacer(1, 10*mm))
        
        # System information
        story.append(Paragraph("System Configuration", styles['Heading2']))
        story.append(Spacer(1, 5*mm))
        
        # System details table
        system_data = [
            ["Parameter", "Value"],
            ["System Voltage", f"{self.design.system_voltage_v}V"],
            ["Number of Poles", f"{self.design.num_poles}P"],
            ["Total System Current", f"{self.design.total_current_a:.2f}A"],
            ["Number of Incomers", str(self.design.num_incomers())],
            ["Number of Outgoings", str(self.design.num_outgoings())],
            ["Busbar Configuration", f"{self.design.busbar.num_runs} runs × {self.design.busbar.width_mm}×{self.design.busbar.thickness_mm}mm"],
        ]
        
        system_table = Table(system_data, colWidths=[200, 200])
        system_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(system_table)
        
        return story
    
    def _build_sld_page(self, sld_png_path: str) -> List:
        """Build SLD page"""
        styles = self._get_styles()
        story = []
        
        story.append(Paragraph("Single Line Diagram (SLD)", styles['Heading1']))
        story.append(Spacer(1, 12*mm))
        
        # Add image
        try:
            img = Image(sld_png_path, width=180*mm, height=120*mm)
            story.append(img)
        except Exception as e:
            story.append(Paragraph(f"Image not available: {str(e)}", styles['Normal']))
        
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph(
            "The Single Line Diagram shows all electrical connections between sources (DG, Grid, Solar), "
            "the main busbar, and load feeders with their respective protection (MCCBs) and the Microgrid Controller.",
            styles['Normal']
        ))
        
        return story
    
    def _build_ga_page(self, ga_png_path: str) -> List:
        """Build GA page"""
        styles = self._get_styles()
        story = []
        
        story.append(Paragraph("General Arrangement (GA)", styles['Heading1']))
        story.append(Spacer(1, 12*mm))
        
        # Add image
        try:
            img = Image(ga_png_path, width=150*mm, height=180*mm)
            story.append(img)
        except Exception as e:
            story.append(Paragraph(f"Image not available: {str(e)}", styles['Normal']))
        
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph(
            "The General Arrangement shows the physical layout of all components within the panel, "
            "including MCCB positioning, busbar routing, and space allocation for the Microgrid Controller.",
            styles['Normal']
        ))
        
        return story
    
    def _build_bom_page(self) -> List:
        """Build BOM page"""
        styles = self._get_styles()
        story = []
        
        story.append(Paragraph("Bill of Materials (BOM)", styles['Heading1']))
        story.append(Spacer(1, 12*mm))
        
        # BOM table
        bom_data = self.bom_gen.generate_bom_data()
        
        bom_table = Table(bom_data, colWidths=[30, 150, 80, 50, 60, 80])
        bom_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(bom_table)
        
        story.append(Spacer(1, 15*mm))
        
        # Specifications
        story.append(Paragraph("System Specifications", styles['Heading2']))
        story.append(Spacer(1, 5*mm))
        
        specs = f"""
        <b>Electrical Specifications:</b><br/>
        • System Voltage: {self.design.system_voltage_v}V, {self.design.num_poles}-Pole<br/>
        • Total System Current: {self.design.total_current_a:.2f}A<br/>
        • Total Number of MCCBs: {self.design.num_incomers() + self.design.num_outgoings()}<br/>
        • Total Incomers: {self.design.num_incomers()}<br/>
        • Total Outgoings: {self.design.num_outgoings()}<br/>
        <br/>
        <b>Busbar Specifications:</b><br/>
        • Material: {self.design.busbar.material}<br/>
        • Number of Runs: {self.design.busbar.num_runs}<br/>
        • Size per Run: {self.design.busbar.width_mm} × {self.design.busbar.thickness_mm} mm<br/>
        <br/>
        <b>Control System:</b><br/>
        • Controller Type: {self.design.controller.name}<br/>
        • Function: Automatic load management and synchronization<br/>
        """
        
        story.append(Paragraph(specs, styles['Normal']))
        
        return story
    
    def _get_styles(self):
        """Get or customize ReportLab styles"""
        styles = getSampleStyleSheet()
        
        # Customize normal style
        styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=styles['Normal'],
            fontSize=PDF_NORMAL_FONTSIZE,
            leading=14
        ))
        
        return styles
