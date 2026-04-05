"""
General Arrangement (GA) Renderer - Physical Panel Layout
"""
import svgwrite as svg
from models.system_model import DesignObject
from config.constants import (
    GA_PANEL_WIDTH, GA_PANEL_HEIGHT, GA_MCCB_HEIGHT, GA_MCCB_WIDTH,
    GA_COLUMN_GAP, GA_BUSBAR_WIDTH, GA_BUSBAR_THICKNESS,
    COLOR_WHITE, COLOR_BUSBAR, COLOR_MGC
)


class GARenderer:
    """Renders General Arrangement (physical panel layout) from design object"""
    
    def __init__(self, design: DesignObject):
        """
        Initialize GA renderer
        
        Args:
            design: DesignObject to render
        """
        self.design = design
        # Scale for SVG (convert mm to px at 1px = 1mm scale)
        self.scale = 1.0
        
        svg_width = GA_PANEL_WIDTH * self.scale + 100
        svg_height = GA_PANEL_HEIGHT * self.scale + 100
        
        self.dwg = svg.Drawing(
            size=(f"{svg_width}px", f"{svg_height}px"),
            profile='full'
        )
    
    def render(self) -> str:
        """
        Render complete GA as SVG string
        
        Returns:
            SVG content as string
        """
        self._draw_panel_outline()
        self._draw_title()
        self._draw_busbar()
        self._draw_mccbs()
        self._draw_dimensions()
        
        return self.dwg.tostring()
    
    def _draw_panel_outline(self):
        """Draw panel frame/outline"""
        margin = 30
        panel_x = margin
        panel_y = margin + 40
        
        self.panel_x = panel_x
        self.panel_y = panel_y
        
        # Panel border
        self.dwg.add(self.dwg.rect(
            insert=(panel_x, panel_y),
            size=(GA_PANEL_WIDTH * self.scale, GA_PANEL_HEIGHT * self.scale),
            fill="#1e293b",
            stroke=COLOR_WHITE,
            stroke_width=2
        ))
        
        # Corner marks
        corner_size = 10
        corners = [
            (panel_x, panel_y),
            (panel_x + GA_PANEL_WIDTH * self.scale, panel_y),
            (panel_x, panel_y + GA_PANEL_HEIGHT * self.scale),
            (panel_x + GA_PANEL_WIDTH * self.scale, panel_y + GA_PANEL_HEIGHT * self.scale)
        ]
        
        for cx, cy in corners:
            self.dwg.add(self.dwg.circle(
                center=(cx, cy),
                r=4,
                fill=COLOR_WHITE,
                stroke="none"
            ))
    
    def _draw_title(self):
        """Draw title and legend"""
        self.dwg.add(self.dwg.text(
            "General Arrangement (GA) - Physical Panel Layout",
            insert=(50, 25),
            font_size=18,
            font_weight="bold",
            fill="#94a3b8",
            font_family="Arial"
        ))
    
    def _draw_busbar(self):
        """Draw busbars on the panel"""
        margin_top = 50  # Distance from top of panel
        busbar_y = self.panel_y + margin_top
        
        # Draw multiple busbar runs
        for run in range(self.design.busbar.num_runs):
            busbar_x = self.panel_x + 40 + run * (GA_BUSBAR_WIDTH + 20)
            
            # Busbar representation
            self.dwg.add(self.dwg.rect(
                insert=(busbar_x, busbar_y),
                size=(GA_BUSBAR_WIDTH * self.scale, GA_PANEL_HEIGHT * self.scale - margin_top - 60),
                fill=COLOR_BUSBAR,
                stroke=COLOR_WHITE,
                stroke_width=1.5,
                opacity=0.7
            ))
            
            # Label
            self.dwg.add(self.dwg.text(
                f"BBR {run + 1}\n{self.design.busbar.width_mm}×{self.design.busbar.thickness_mm}mm",
                insert=(busbar_x + GA_BUSBAR_WIDTH / 2 * self.scale, busbar_y + 30),
                font_size=9,
                fill=COLOR_WHITE,
                text_anchor="middle",
                font_family="Arial"
            ))
        
        self.busbar_y = busbar_y
    
    def _draw_mccbs(self):
        """Draw MCCBs on the panel"""
        num_total = self.design.num_incomers() + self.design.num_outgoings()
        
        # Layout MCCBs in columns
        mccbs_column_width = (GA_PANEL_WIDTH * self.scale - 150) / 2
        col1_x = self.panel_x + 120
        col2_x = col1_x + mccbs_column_width
        
        mccb_y = self.panel_y + 100
        mccb_counter = 0
        
        # Draw incomers (left column)
        col_x = col1_x
        for incomer in self.design.incomers:
            self._draw_mccb_symbol(col_x, mccb_y, incomer.mccb_rating_a, incomer.name, "Incomer")
            mccb_y += GA_MCCB_HEIGHT + 10
            mccb_counter += 1
            
            # Switch to second column if needed
            if mccb_counter == len(self.design.incomers):
                mccb_y = self.panel_y + 100
                col_x = col2_x
        
        # Draw outgoings (right column or continuation)
        for outgoing in self.design.outgoings:
            if mccb_counter >= len(self.design.incomers) and col_x == col1_x:
                col_x = col2_x
                mccb_y = self.panel_y + 100
            
            self._draw_mccb_symbol(col_x, mccb_y, outgoing.mccb_rating_a, outgoing.name, "Outgoing")
            mccb_y += GA_MCCB_HEIGHT + 10
            mccb_counter += 1
    
    def _draw_mccb_symbol(self, x: float, y: float, rating_a: int, label: str, mccb_type: str):
        """Draw single MCCB symbol"""
        # MCCB body
        self.dwg.add(self.dwg.rect(
            insert=(x, y),
            size=(GA_MCCB_WIDTH * self.scale, GA_MCCB_HEIGHT * self.scale),
            fill="#0f172a",
            stroke="#60a5fa",
            stroke_width=1.5
        ))
        
        # Terminals (top and bottom)
        terminal_y_top = y - 5
        terminal_y_bottom = y + GA_MCCB_HEIGHT * self.scale + 5
        terminal_x_center = x + GA_MCCB_WIDTH / 2 * self.scale
        
        self.dwg.add(self.dwg.line(
            (terminal_x_center, terminal_y_top), (terminal_x_center, y),
            stroke=COLOR_WHITE, stroke_width=1
        ))
        self.dwg.add(self.dwg.line(
            (terminal_x_center, y + GA_MCCB_HEIGHT * self.scale), (terminal_x_center, terminal_y_bottom),
            stroke=COLOR_WHITE, stroke_width=1
        ))
        
        # Label
        self.dwg.add(self.dwg.text(
            label,
            insert=(x + GA_MCCB_WIDTH / 2 * self.scale, y + GA_MCCB_HEIGHT / 2 * self.scale - 8),
            font_size=8,
            fill=COLOR_WHITE,
            text_anchor="middle",
            font_family="Arial",
            font_weight="bold"
        ))
        
        # Rating
        self.dwg.add(self.dwg.text(
            f"{rating_a}A",
            insert=(x + GA_MCCB_WIDTH / 2 * self.scale, y + GA_MCCB_HEIGHT / 2 * self.scale + 8),
            font_size=7,
            fill="#94a3b8",
            text_anchor="middle",
            font_family="Arial"
        ))
    
    def _draw_dimensions(self):
        """Draw dimension annotations"""
        # Panel dimensions
        dim_y = self.panel_y + GA_PANEL_HEIGHT * self.scale + 20
        
        # Width dimension
        self.dwg.add(self.dwg.line(
            (self.panel_x, dim_y), (self.panel_x + GA_PANEL_WIDTH * self.scale, dim_y),
            stroke="#94a3b8", stroke_width=0.5
        ))
        self.dwg.add(self.dwg.text(
            f"{GA_PANEL_WIDTH}mm",
            insert=(self.panel_x + GA_PANEL_WIDTH / 2 * self.scale, dim_y + 15),
            font_size=10,
            fill="#94a3b8",
            text_anchor="middle"
        ))
        
        # Height dimension
        dim_x = self.panel_x - 20
        self.dwg.add(self.dwg.text(
            f"{GA_PANEL_HEIGHT}mm",
            insert=(dim_x, self.panel_y + GA_PANEL_HEIGHT / 2 * self.scale),
            font_size=10,
            fill="#94a3b8",
            text_anchor="middle",
            transform=f"rotate(-90, {dim_x}, {self.panel_y + GA_PANEL_HEIGHT / 2 * self.scale})"
        ))
