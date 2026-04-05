"""
Design Builder - Orchestrates design creation from system input
"""
from typing import List
from models.system_model import SystemInput, DesignObject, Incomer, Outgoing, BusbarDesign, MicrogridController
from config.constants import SYSTEM_VOLTAGE, POWER_FACTOR, DG_POWER_FACTOR
from engine.calculations import (
    calculate_current_from_kw,
    calculate_current_from_kva,
    select_mccb_rating,
    calculate_busbar_size
)


class DesignBuilder:
    """Builds design object from system input"""
    
    def __init__(self, system_input: SystemInput):
        """
        Initialize design builder
        
        Args:
            system_input: SystemInput object with user parameters
        """
        self.system_input = system_input
        self.system_input.validate()
        self.voltage = SYSTEM_VOLTAGE
    
    def build(self) -> DesignObject:
        """
        Build complete design object
        
        Returns:
            DesignObject with all computed parameters
        """
        design = DesignObject(
            system_voltage_v=self.voltage,
            num_poles=self.system_input.num_poles
        )
        
        # Build incomers
        incomers = self._build_incomers()
        design.incomers = incomers
        
        # Calculate total current
        total_current = sum(ic.current_a for ic in incomers)
        design.total_current_a = total_current
        
        # Build outgoings
        outgoings = self._build_outgoings(total_current)
        design.outgoings = outgoings
        
        # Size busbar
        design.busbar = self._size_busbar(total_current)
        
        # Add controller
        design.controller = MicrogridController()
        
        # Store source input
        design.created_from_system_input = {
            "solar_kw": self.system_input.solar_kw,
            "grid_kw": self.system_input.grid_kw,
            "dg_ratings_kva": self.system_input.dg_ratings_kva,
            "num_poles": self.system_input.num_poles
        }
        
        return design
    
    def _build_incomers(self) -> List[Incomer]:
        """Build list of incomers (sources with MCCBs)"""
        incomers = []
        ic_counter = 1
        
        # DG incomers
        for i, dg_kva in enumerate(self.system_input.dg_ratings_kva):
            current = calculate_current_from_kva(dg_kva, self.voltage)
            mccb = select_mccb_rating(current)
            incomers.append(Incomer(
                name=f"IC {ic_counter}",
                source_type="DG",
                rating_kw_or_kva=dg_kva,
                current_a=current,
                mccb_rating_a=mccb
            ))
            ic_counter += 1
        
        # Grid incomer
        if self.system_input.has_grid:
            current = calculate_current_from_kw(self.system_input.grid_kw, self.voltage, POWER_FACTOR)
            mccb = select_mccb_rating(current)
            incomers.append(Incomer(
                name=f"IC {ic_counter}",
                source_type="Grid",
                rating_kw_or_kva=self.system_input.grid_kw,
                current_a=current,
                mccb_rating_a=mccb
            ))
            ic_counter += 1
        
        # Solar incomer
        if self.system_input.has_solar:
            current = calculate_current_from_kw(self.system_input.solar_kw, self.voltage, POWER_FACTOR)
            mccb = select_mccb_rating(current)
            incomers.append(Incomer(
                name=f"IC {ic_counter}",
                source_type="Solar",
                rating_kw_or_kva=self.system_input.solar_kw,
                current_a=current,
                mccb_rating_a=mccb
            ))
        
        return incomers
    
    def _build_outgoings(self, total_current: float) -> List[Outgoing]:
        """
        Build list of outgoing feeders with balanced load distribution
        
        Args:
            total_current: Total available current from incomers
        
        Returns:
            List of Outgoing objects
        """
        outgoings = []
        num_feeders = self.system_input.num_outgoing_feeders
        
        # Default preset for 3 feeders (common case)
        if num_feeders == 3:
            ratings = [400, 400, 250]
        else:
            # For other cases, distribute load
            avg_current = total_current / num_feeders
            ratings = [select_mccb_rating(avg_current) for _ in range(num_feeders)]
        
        for i in range(num_feeders):
            outgoings.append(Outgoing(
                name=f"O/G {i+1}",
                mccb_rating_a=ratings[i] if i < len(ratings) else select_mccb_rating(total_current / num_feeders)
            ))
        
        return outgoings
    
    def _size_busbar(self, total_current: float) -> BusbarDesign:
        """
        Size busbar based on total current
        
        Args:
            total_current: Total current in amperes
        
        Returns:
            BusbarDesign object
        """
        num_runs, width, thickness = calculate_busbar_size(total_current)
        return BusbarDesign(
            num_runs=num_runs,
            width_mm=width,
            thickness_mm=thickness,
            length_mm=100,
            material="Aluminium"
        )
