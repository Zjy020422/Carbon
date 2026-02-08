"""
Emission Calculation Module
碳排放计算模块
"""

from .emission_calculator import (
    EmissionCalculator,
    EmissionReportGenerator,
    EmissionResult,
    FlightParams
)

__all__ = [
    'EmissionCalculator',
    'EmissionReportGenerator',
    'EmissionResult',
    'FlightParams',
]
