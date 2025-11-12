"""
FOBI Utilities Module
=====================

General utility functions for visualization, data handling, and I/O.
"""

from .visualization import plot_transmission_spectrum, plot_edge_maps
from .synthetic_data import (
    generate_test_data,
    generate_realistic_poldi_data,
    generate_realistic_chopper_modulated_data,
    poldi_neutron_flux,
    wavelength_to_tof,
    tof_to_wavelength,
    generate_realistic_bragg_edges,
)

__all__ = [
    "plot_transmission_spectrum",
    "plot_edge_maps",
    "generate_test_data",
    "generate_realistic_poldi_data",
    "generate_realistic_chopper_modulated_data",
    "poldi_neutron_flux",
    "wavelength_to_tof",
    "tof_to_wavelength",
    "generate_realistic_bragg_edges",
]
