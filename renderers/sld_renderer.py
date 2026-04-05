"""
Single Line Diagram (SLD) Renderer
"""
import svgwrite as svg
from models.system_model import DesignObject
from config.constants import (
    SVG_WIDTH, SVG_HEIGHT, SVG_BACKGROUND_COLOR, SVG_BORDER_COLOR,
    Y_SOURCES, Y_DIVISION, Y_BUSBAR, IC_START_X, COMPONENT_SPACING,
    COLOR_WHITE, COLOR_GRID, COLOR_SOLAR, COLOR_DG, COLOR_MCCB,
    COLOR_BUSBAR, COLOR_MGC, COLOR_COMM, OUTGOING_SPACING
)


class SLDRenderer:
    """Renders Single Line Diagram from design object"""
    
    def __init__(self, design: DesignObject):
        """
        Initialize SLD renderer
        
        Args:
            design: DesignObject to render
        """
        self.design = design
        self.dwg = svg.Drawing(
            size=(f"{SVG_WIDTH}px", f"{SVG_HEIGHT}px"),
            profile='full'
        )
    
    def render(self) -> str:
        """
        Render complete SLD as SVG string
        
        Returns:
            SVG content as string
        """
        self._draw_background()
        self._draw_title_frame()
        self._draw_sources()
        self._draw_busbar()
        self._draw_controller()
        self._draw_outgoings()
        
        return self.dwg.tostring()
    
    def _draw_background(self):
        """Draw background and border"""
        self.dwg.add(self.dwg.rect(
            (15, 15),
            (SVG_WIDTH - 30, SVG_HEIGHT - 30),
            fill=SVG_BACKGROUND_COLOR,
            stroke=SVG_BORDER_COLOR,
            stroke_width=2,
            rx=15
        ))
    
    def _draw_title_frame(self):
        """Draw title and scope labels"""
        # Main title
        self.dwg.add(self.dwg.text(
            "⚡ Smart Microgrid Panel - Single Line Diagram (SLD)",
            insert=(SVG_WIDTH / 2, 50),
            font_size=20,
            font_weight="bold",
            fill="#94a3b8",
            text_anchor="middle",
            font_family="Arial"
        ))
        
        # Division line
        self.dwg.add(self.dwg.line(
            (30, Y_DIVISION),
            (SVG_WIDTH - 30, Y_DIVISION),
            stroke="#475569",
            stroke_width=1,
            stroke_dasharray="8,4"
        ))
        
        # Scope labels
        self.dwg.add(self.dwg.text(
            "CUSTOMER SCOPE",
            insert=(SVG_WIDTH / 2, Y_DIVISION - 30),
            font_size=16,
            font_weight="bold",
            fill="#94a3b8",
            text_anchor="middle"
        ))
        
        self.dwg.add(self.dwg.text(
            "KIRLOSKAR SMART AMF PANEL SCOPE",
            insert=(50, SVG_HEIGHT - 50),
            font_size=16,
            font_weight="bold",
            fill="#94a3b8"
        ))
    
    def _draw_sources(self):
        """Draw source symbols (DG, Grid, Solar) and incomers"""
        self.active_ic_x_positions = []
        current_x = IC_START_X
        
        for incomer in self.design.incomers:
            self._draw_single_incomer(incomer, current_x)
            self.active_ic_x_positions.append(current_x)
            current_x += COMPONENT_SPACING
        
        # Draw communication lines
        self._draw_communication_lines()
    
    def _draw_single_incomer(self, incomer, x: int):
        """Draw single incomer with source symbol"""
        
        # Source rating label
        self.dwg.add(self.dwg.text(
            f"{incomer.rating_kw_or_kva:.0f} {'kW' if incomer.source_type == 'Grid' else 'kVA' if incomer.source_type == 'DG' else 'kWp'}",
            insert=(x, Y_SOURCES - 85),
            font_size=16,
            font_weight="bold",
            fill=COLOR_WHITE,
            text_anchor="middle",
            font_family="Arial"
        ))
        
        # Draw source symbol
        if incomer.source_type == "DG":
            self._draw_dg_symbol(x, Y_SOURCES)
        elif incomer.source_type == "Grid":
            self._draw_grid_symbol(x, Y_SOURCES)
        elif incomer.source_type == "Solar":
            self._draw_solar_symbol(x, Y_SOURCES)
        
        # Connect to sync controller or directly to MCCB
        if incomer.source_type == "DG":
            # DG connects through sync controller
            sync_y = Y_DIVISION - 100
            self.dwg.add(self.dwg.line(
                (x, Y_SOURCES + 45), (x, sync_y),
                stroke=COLOR_WHITE, stroke_width=2
            ))
            
            # Sync controller box
            self.dwg.add(self.dwg.rect(
                insert=(x - 65, sync_y),
                size=(130, 40),
                fill="#1e293b",
                stroke=COLOR_DG,
                rx=5
            ))
            self.dwg.add(self.dwg.text(
                "Synch Controller",
                insert=(x, sync_y + 25),
                font_size=11,
                fill=COLOR_WHITE,
                text_anchor="middle"
            ))
            
            # Connect to MCCB
            self.dwg.add(self.dwg.line(
                (x, sync_y + 40), (x, Y_DIVISION + 40),
                stroke=COLOR_WHITE, stroke_width=2
            ))
        else:
            # Grid and Solar connect directly
            self.dwg.add(self.dwg.line(
                (x, Y_SOURCES + 30) if incomer.source_type == "Solar" else (x, Y_SOURCES + 40),
                (x, Y_DIVISION + 40),
                stroke=COLOR_WHITE, stroke_width=2
            ))
        
        # Draw MCCB
        self._draw_mccb(x, Y_DIVISION + 100, incomer.mccb_rating_a, incomer.name)
        
        # Connect MCCB to busbar
        self.dwg.add(self.dwg.line(
            (x, Y_DIVISION + 150), (x, Y_BUSBAR),
            stroke=COLOR_WHITE, stroke_width=2
        ))
    
    def _draw_dg_symbol(self, x: int, y: int):
        """Draw DG generator symbol"""
        self.dwg.add(self.dwg.circle(
            center=(x, y),
            r=45,
            stroke=COLOR_DG,
            fill="none",
            stroke_width=2.5
        ))
        self.dwg.add(self.dwg.text(
            "DG", insert=(x, y + 7),
            font_size=15,
            fill=COLOR_WHITE,
            text_anchor="middle"
        ))
    
    def _draw_grid_symbol(self, x: int, y: int):
        """Draw grid/tower symbol"""
        h = 60
        self.dwg.add(self.dwg.line((x, y), (x - 15, y + h), stroke=COLOR_WHITE, stroke_width=2))
        self.dwg.add(self.dwg.line((x, y), (x + 15, y + h), stroke=COLOR_WHITE, stroke_width=2))
        self.dwg.add(self.dwg.line((x - 15, y + h), (x + 15, y + h), stroke=COLOR_WHITE, stroke_width=2))
        self.dwg.add(self.dwg.line((x - 10, y + 25), (x + 10, y + 25), stroke=COLOR_WHITE, stroke_width=1.5))
        self.dwg.add(self.dwg.line((x - 12, y + 45), (x + 12, y + 45), stroke=COLOR_WHITE, stroke_width=1.5))
    
    def _draw_solar_symbol(self, x: int, y: int):
        """Draw solar panel symbol"""
        # Panel
        self.dwg.add(self.dwg.rect(
            insert=(x - 20, y + 10),
            size=(40, 45),
            fill="#1e293b",
            stroke=COLOR_WHITE,
            stroke_width=1.5
        ))
        # Grid lines
        for i in range(1, 4):
            self.dwg.add(self.dwg.line(
                (x - 20, y + 10 + i * 11), (x + 20, y + 10 + i * 11),
                stroke=COLOR_WHITE, stroke_opacity=0.5
            ))
            self.dwg.add(self.dwg.line(
                (x - 20 + i * 10, y + 10), (x - 20 + i * 10, y + 55),
                stroke=COLOR_WHITE, stroke_opacity=0.5
            ))
        # Sun
        self.dwg.add(self.dwg.circle(
            center=(x - 30, y - 5),
            r=8,
            stroke=COLOR_SOLAR,
            fill="none",
            stroke_width=2
        ))
    
    def _draw_mccb(self, x: int, y: int, rating_a: int, label: str):
        """Draw MCCB symbol"""
        # Vertical lines with break
        self.dwg.add(self.dwg.line(
            (x, y - 50), (x, y - 18),
            stroke=COLOR_WHITE, stroke_width=2
        ))
        self.dwg.add(self.dwg.line(
            (x, y + 18), (x, y + 50),
            stroke=COLOR_WHITE, stroke_width=2
        ))
        
        # Breaker arc symbol
        self.dwg.add(self.dwg.path(
            d=f"M{x},{y-18} A18,18 0 0,0 {x+18},{y+15}",
            stroke=COLOR_MCCB,
            fill="none",
            stroke_width=2.5
        ))
        
        # Text information
        self.dwg.add(self.dwg.text(
            f"{rating_a}A, {self.design.num_poles}P",
            insert=(x - 25, y - 5),
            font_size=12,
            fill="#e2e8f0",
            text_anchor="end",
            font_family="Arial"
        ))
        self.dwg.add(self.dwg.text(
            "Motorised MCCB",
            insert=(x - 25, y + 12),
            font_size=11,
            fill="#94a3b8",
            text_anchor="end",
            font_family="Arial"
        ))
        self.dwg.add(self.dwg.text(
            label,
            insert=(x + 35, y + 5),
            font_size=14,
            font_weight="bold",
            fill="#f1f5f9",
            text_anchor="start",
            font_family="Arial"
        ))
    
    def _draw_busbar(self):
        """Draw main busbar"""
        self.dwg.add(self.dwg.line(
            (100, Y_BUSBAR),
            (SVG_WIDTH - 100, Y_BUSBAR),
            stroke=COLOR_BUSBAR,
            stroke_width=7
        ))
        self.dwg.add(self.dwg.text(
            "MAIN BUSBAR (Aluminium)",
            insert=(110, Y_BUSBAR - 10),
            font_size=12,
            fill="#f87171"
        ))
    
    def _draw_controller(self):
        """Draw MGC controller"""
        mgc_x, mgc_y = SVG_WIDTH - 160, Y_DIVISION + 10
        size = 100
        
        self.dwg.add(self.dwg.rect(
            insert=(mgc_x, mgc_y),
            size=(size, size),
            fill="#1e1b4b",
            stroke=COLOR_MGC,
            stroke_width=3,
            rx=10
        ))
        
        # Terminal lines
        for i in range(5):
            off = 18 + i * 16
            self.dwg.add(self.dwg.line(
                (mgc_x + off, mgc_y - 10), (mgc_x + off, mgc_y),
                stroke=COLOR_MGC, stroke_width=2
            ))
            self.dwg.add(self.dwg.line(
                (mgc_x + off, mgc_y + size), (mgc_x + off, mgc_y + size + 10),
                stroke=COLOR_MGC, stroke_width=2
            ))
            self.dwg.add(self.dwg.line(
                (mgc_x - 10, mgc_y + off), (mgc_x, mgc_y + off),
                stroke=COLOR_MGC, stroke_width=2
            ))
            self.dwg.add(self.dwg.line(
                (mgc_x + size, mgc_y + off), (mgc_x + size + 10, mgc_y + off),
                stroke=COLOR_MGC, stroke_width=2
            ))
        
        # Label
        self.dwg.add(self.dwg.text(
            "MGC",
            insert=(mgc_x + size / 2, mgc_y + size / 2 + 8),
            font_size=20,
            fill=COLOR_WHITE,
            font_weight="bold",
            text_anchor="middle"
        ))
        
        self.mgc_x = mgc_x
        self.mgc_y = mgc_y
    
    def _draw_communication_lines(self):
        """Draw communication lines between MCCBs and controller"""
        if not hasattr(self, 'active_ic_x_positions'):
            return
        
        comm_y = Y_DIVISION - 20
        mgc_x = self.mgc_x if hasattr(self, 'mgc_x') else SVG_WIDTH - 160
        
        # Main communication line
        self.dwg.add(self.dwg.line(
            (self.active_ic_x_positions[0], comm_y),
            (mgc_x, comm_y),
            stroke=COLOR_COMM,
            stroke_width=1.2,
            stroke_dasharray="6,3"
        ))
        
        # Label
        self.dwg.add(self.dwg.text(
            "Communication and Control Lines",
            insert=(SVG_WIDTH / 2, comm_y - 12),
            font_size=13,
            fill=COLOR_COMM,
            text_anchor="middle"
        ))
        
        # Drop lines
        for ax in self.active_ic_x_positions:
            self.dwg.add(self.dwg.line(
                (ax, comm_y), (ax, Y_DIVISION + 40),
                stroke=COLOR_COMM, stroke_width=1,
                stroke_dasharray="4,2"
            ))
        
        if hasattr(self, 'mgc_y'):
            self.dwg.add(self.dwg.line(
                (mgc_x, comm_y), (mgc_x, self.mgc_y + 25),
                stroke=COLOR_COMM, stroke_width=1,
                stroke_dasharray="6,3"
            ))
    
    def _draw_outgoings(self):
        """Draw outgoing feeders"""
        x_out_start = 300
        
        for i, outgoing in enumerate(self.design.outgoings):
            ox = x_out_start + i * OUTGOING_SPACING
            if ox > SVG_WIDTH - 150:
                break
            
            # Connect to busbar
            self.dwg.add(self.dwg.line(
                (ox, Y_BUSBAR), (ox, Y_BUSBAR + 40),
                stroke=COLOR_WHITE, stroke_width=2
            ))
            
            # Draw MCCB
            self._draw_mccb(ox, Y_BUSBAR + 100, outgoing.mccb_rating_a, outgoing.name)
            
            # Connect to load
            self.dwg.add(self.dwg.line(
                (ox, Y_BUSBAR + 150), (ox, SVG_HEIGHT - 100),
                stroke=COLOR_WHITE, stroke_width=2
            ))
