"""
FOBI Edge Fitting Module
=========================

This module contains functions for fitting Bragg edges in neutron transmission
spectra to extract material properties such as lattice spacing, strain, and texture.
"""

from .gaussian import edge_fit_gaussian, edge_fit_gaussian_2d
from .utils import find_nearest

__all__ = [
    "edge_fit_gaussian",
    "edge_fit_gaussian_2d",
    "find_nearest",
]
