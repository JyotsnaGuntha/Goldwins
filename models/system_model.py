"""
System Model - Represents all user inputs for the microgrid system
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class SystemInput:
    """Represents all user input parameters for the microgrid system"""
    
    # Power inputs (in kW/kVA)
    solar_kw: float = 100.0
    grid_kw: float = 120.0
    dg_ratings_kva: List[float] = field(default_factory=lambda: [250.0, 250.0])
    
    # System configuration
    num_poles: int = 4  # 3 or 4
    num_outgoing_feeders: int = 3
    
    def validate(self) -> bool:
        """Validate all input parameters"""
        if self.solar_kw < 0 or self.grid_kw < 0:
            raise ValueError("Power ratings cannot be negative")
        if any(dg < 0 for dg in self.dg_ratings_kva):
            raise ValueError("DG ratings cannot be negative")
        if self.num_poles not in [3, 4]:
            raise ValueError("System must be 3-phase or 4-pole")
        if self.num_outgoing_feeders < 1 or self.num_outgoing_feeders > 5:
            raise ValueError("Outgoing feeders must be between 1 and 5")
        return True
    
    @property
    def num_dgs(self) -> int:
        """Get number of DGs"""
        return len(self.dg_ratings_kva)
    
    @property
    def has_solar(self) -> bool:
        """Check if solar is available"""
        return self.solar_kw > 0
    
    @property
    def has_grid(self) -> bool:
        """Check if grid is available"""
        return self.grid_kw > 0
    
    @property
    def has_dgs(self) -> bool:
        """Check if any DGs are available"""
        return self.num_dgs > 0


# ==================== DESIGN OUTPUT MODELS ====================

@dataclass
class Incomer:
    """Represents an incomer (source with MCCB)"""
    name: str
    source_type: str  # "DG", "Grid", "Solar"
    rating_kw_or_kva: float
    current_a: float
    mccb_rating_a: int
    
    def __repr__(self) -> str:
        return f"{self.name}: {self.mccb_rating_a}A MCCB ({self.source_type})"


@dataclass
class Outgoing:
    """Represents an outgoing feeder"""
    name: str
    mccb_rating_a: int
    
    def __repr__(self) -> str:
        return f"{self.name}: {self.mccb_rating_a}A MCCB"


@dataclass
class BusbarDesign:
    """Represents busbar sizing"""
    num_runs: int = 2
    width_mm: int = 50
    thickness_mm: int = 10
    length_mm: int = 100
    material: str = "Aluminium"
    
    def __repr__(self) -> str:
        return f"{self.num_runs} runs {self.width_mm}x{self.thickness_mm}mm {self.material}"


@dataclass
class MicrogridController:
    """Represents the MGC controller"""
    name: str = "Smart AMF Controller"
    type: str = "Microgrid Controller"
    
    def __repr__(self) -> str:
        return f"{self.name} ({self.type})"


@dataclass
class DesignObject:
    """Complete design object - single source of truth for all outputs"""
    
    incomers: List[Incomer] = field(default_factory=list)
    outgoings: List[Outgoing] = field(default_factory=list)
    busbar: BusbarDesign = field(default_factory=BusbarDesign)
    controller: MicrogridController = field(default_factory=MicrogridController)
    
    # System parameters
    system_voltage_v: int = 415
    num_poles: int = 4
    total_current_a: float = 0.0
    
    # Metadata
    created_from_system_input: dict = field(default_factory=dict)
    
    def num_incomers(self) -> int:
        """Get number of incomers"""
        return len(self.incomers)
    
    def num_outgoings(self) -> int:
        """Get number of outgoings"""
        return len(self.outgoings)
    
    def get_all_mccbs(self) -> List[dict]:
        """Get list of all MCCBs in the design"""
        result = []
        for ic in self.incomers:
            result.append({
                "type": "Incomer",
                "name": ic.name,
                "rating_a": ic.mccb_rating_a,
                "poles": self.num_poles,
                "source": ic.source_type
            })
        for og in self.outgoings:
            result.append({
                "type": "Outgoing",
                "name": og.name,
                "rating_a": og.mccb_rating_a,
                "poles": self.num_poles,
                "source": "Load Feeder"
            })
        return result
    
    def __repr__(self) -> str:
        return f"Design: {self.num_incomers()} incomers, {self.num_outgoings()} outgoings, {self.busbar}"
