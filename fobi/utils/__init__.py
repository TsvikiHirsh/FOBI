"""
FOBI Utilities Module
=====================

General utility functions for visualization, data handling, and I/O.
"""

from .visualization import plot_transmission_spectrum, plot_edge_maps
from .synthetic_data import generate_test_data

__all__ = [
    "plot_transmission_spectrum",
    "plot_edge_maps",
    "generate_test_data",
]
