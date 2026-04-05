"""
Electrical calculations module
"""
import math
from config.constants import (
    SYSTEM_VOLTAGE,
    POWER_FACTOR,
    DG_POWER_FACTOR,
    SAFETY_FACTOR,
    STANDARD_MCCBS
)


def calculate_current_from_kw(power_kw: float, voltage_v: int, pf: float) -> float:
    """
    Calculate current from power in kW
    Formula: I = P / (√3 × V × PF)
    
    Args:
        power_kw: Power in kilowatts
        voltage_v: Voltage in volts
        pf: Power factor
    
    Returns:
        Current in amperes
    """
    if power_kw <= 0:
        return 0.0
    return power_kw * 1000 / (math.sqrt(3) * voltage_v * pf)


def calculate_current_from_kva(power_kva: float, voltage_v: int) -> float:
    """
    Calculate current from power in kVA
    Formula: I = kVA × 1000 / (√3 × V)
    
    Args:
        power_kva: Power in kilovolt-amperes
        voltage_v: Voltage in volts
    
    Returns:
        Current in amperes
    """
    if power_kva <= 0:
        return 0.0
    return power_kva * 1000 / (math.sqrt(3) * voltage_v)


def apply_safety_factor(current_a: float, factor: float = SAFETY_FACTOR) -> float:
    """
    Apply safety factor to current for MCCB selection
    
    Args:
        current_a: Base current in amperes
        factor: Safety factor (default 1.25)
    
    Returns:
        Current with safety factor applied
    """
    return current_a * factor


def select_mccb_rating(current_a: float, safety_factor: float = SAFETY_FACTOR) -> int:
    """
    Select next standard MCCB rating for given current
    
    Args:
        current_a: Current in amperes
        safety_factor: Safety factor to apply
    
    Returns:
        Selected MCCB rating from standard list
    """
    required_current = apply_safety_factor(current_a, safety_factor)
    
    for rating in STANDARD_MCCBS:
        if rating >= required_current:
            return rating
    
    # Return highest rating if required exceeds all standard ratings
    return STANDARD_MCCBS[-1]


def calculate_busbar_size(total_current_a: float) -> tuple:
    """
    Suggest busbar dimensions based on total current
    
    Args:
        total_current_a: Total current in amperes
    
    Returns:
        tuple: (num_runs, width_mm, thickness_mm)
    """
    # Simplified rule: ~60A per 50x10mm aluminium busbar
    # Adjust based on actual ampacity
    ampacity_per_run = 60
    num_runs = max(2, math.ceil(total_current_a / ampacity_per_run))
    
    if total_current_a < 500:
        return (num_runs, 50, 10)
    elif total_current_a < 1000:
        return (num_runs, 63, 12)
    else:
        return (num_runs, 100, 16)
