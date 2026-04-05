"""
Bill of Materials (BOM) Generator
"""
from typing import List
from models.system_model import DesignObject


class BOMGenerator:
    """Generates Bill of Materials from design object"""
    
    def __init__(self, design: DesignObject):
        """
        Initialize BOM generator
        
        Args:
            design: DesignObject to generate BOM from
        """
        self.design = design
    
    def generate_bom_data(self) -> List[List[str]]:
        """
        Generate BOM data as list of lists (compatible with ReportLab Table)
        
        Returns:
            List of lists: [Header row, Data rows...]
        """
        table_data = [["Sr No", "Component", "Rating", "Poles", "Quantity", "Remarks"]]
        sr = 1
        
        # ==================== INCOMERS ====================
        for incomer in self.design.incomers:
            component_name = f"{incomer.source_type} Incomer MCCB"
            rating = f"{incomer.mccb_rating_a}A"
            poles = f"{self.design.num_poles}P"
            
            table_data.append([
                str(sr),
                component_name,
                rating,
                poles,
                "1",
                f"({incomer.source_type})"
            ])
            sr += 1
        
        # ==================== OUTGOINGS ====================
        for outgoing in self.design.outgoings:
            component_name = f"{outgoing.name} Feeder MCCB"
            rating = f"{outgoing.mccb_rating_a}A"
            poles = f"{self.design.num_poles}P"
            
            table_data.append([
                str(sr),
                component_name,
                rating,
                poles,
                "1",
                "Load Feeder"
            ])
            sr += 1
        
        # ==================== BUSBAR ====================
        table_data.append([
            str(sr),
            f"Main Busbar ({self.design.busbar.material})",
            f"{self.design.busbar.width_mm}×{self.design.busbar.thickness_mm} mm",
            "-",
            str(self.design.busbar.num_runs),
            f"{self.design.busbar.num_runs} runs"
        ])
        sr += 1
        
        # ==================== CONTROLLER ====================
        table_data.append([
            str(sr),
            self.design.controller.name,
            self.design.controller.type,
            "-",
            "1",
            "Smart AMF"
        ])
        sr += 1
        
        # ==================== SUMMARY ROWS ====================
        table_data.append([
            "-",
            "",
            "",
            "",
            "",
            ""
        ])
        
        table_data.append([
            "-",
            "SYSTEM SUMMARY",
            "",
            "",
            "",
            ""
        ])
        
        table_data.append([
            "-",
            f"Total System Current",
            f"{self.design.total_current_a:.2f}A",
            "-",
            "-",
            f"@ {self.design.system_voltage_v}V"
        ])
        
        table_data.append([
            "-",
            f"Number of Incomers",
            str(self.design.num_incomers()),
            "-",
            "-",
            f"Sources"
        ])
        
        table_data.append([
            "-",
            f"Number of Outgoings",
            str(self.design.num_outgoings()),
            "-",
            "-",
            f"Load Feeders"
        ])
        
        return table_data
    
    def generate_bom_summary(self) -> str:
        """
        Generate human-readable BOM summary
        
        Returns:
            Formatted BOM text
        """
        lines = []
        lines.append("=" * 70)
        lines.append("BILL OF MATERIALS (BOM)")
        lines.append("=" * 70)
        lines.append("")
        
        # Incomers
        lines.append("INCOMERS (Sources):")
        lines.append("-" * 70)
        for incomer in self.design.incomers:
            lines.append(f"  • {incomer.name}: {incomer.mccb_rating_a}A MCCB ({incomer.source_type})")
        lines.append("")
        
        # Outgoings
        lines.append("OUTGOINGS (Load Feeders):")
        lines.append("-" * 70)
        for outgoing in self.design.outgoings:
            lines.append(f"  • {outgoing.name}: {outgoing.mccb_rating_a}A MCCB")
        lines.append("")
        
        # Busbar
        lines.append("BUSBAR:")
        lines.append("-" * 70)
        lines.append(f"  • Material: {self.design.busbar.material}")
        lines.append(f"  • Size: {self.design.busbar.width_mm}×{self.design.busbar.thickness_mm} mm")
        lines.append(f"  • Number of Runs: {self.design.busbar.num_runs}")
        lines.append("")
        
        # Controller
        lines.append("CONTROLLER:")
        lines.append("-" * 70)
        lines.append(f"  • Type: {self.design.controller.name}")
        lines.append(f"  • Function: {self.design.controller.type}")
        lines.append("")
        
        # Summary
        lines.append("SYSTEM SUMMARY:")
        lines.append("-" * 70)
        lines.append(f"  • Total System Voltage: {self.design.system_voltage_v}V, {self.design.num_poles}-Pole System")
        lines.append(f"  • Total Current: {self.design.total_current_a:.2f}A")
        lines.append(f"  • Total MCCBs (Incomers + Outgoings): {self.design.num_incomers() + self.design.num_outgoings()}")
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
