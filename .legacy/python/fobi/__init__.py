"""
FOBI: Full-spectrum Bragg edge transmission imaging
====================================================

A Python package for processing neutron time-of-flight imaging data using
the FOBI parametric reconstruction technique.

Modules
-------
reduction
    Core data reduction and Wiener deconvolution functions
edge_fitting
    Bragg edge fitting with Gaussian and Voigt models
utils
    Utility functions for data handling and visualization

References
----------
Carminati, C., et al. (2020). "FOBI technique for parametric reconstruction
of neutron time-of-flight imaging." Nature Scientific Reports.
https://www.nature.com/articles/s41598-020-71705-4
"""

__version__ = "1.0.0"
__author__ = "FOBI Development Team"
__license__ = "MIT"

from . import reduction
from . import edge_fitting
from . import utils

__all__ = ["reduction", "edge_fitting", "utils"]
