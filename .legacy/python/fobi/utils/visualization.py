"""
Visualization utilities for FOBI analysis.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple


def plot_transmission_spectrum(
    spectrum: np.ndarray,
    transmission: np.ndarray,
    title: str = "Transmission Spectrum",
    edge_positions: Optional[list] = None,
    figsize: Tuple[int, int] = (12, 5),
):
    """
    Plot transmission spectrum with optional edge markers.

    Parameters
    ----------
    spectrum : np.ndarray
        Wavelength or TOF array
    transmission : np.ndarray
        Transmission values
    title : str
        Plot title
    edge_positions : list, optional
        List of edge positions to mark with vertical lines
    figsize : tuple
        Figure size (width, height)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Plot transmission
    ax1.plot(spectrum, transmission, 'b-', linewidth=1.5)
    ax1.set_xlabel("Wavelength / TOF (µs)")
    ax1.set_ylabel("Transmission")
    ax1.set_title(f"{title} - Transmission")
    ax1.grid(True, alpha=0.3)

    if edge_positions:
        for pos in edge_positions:
            ax1.axvline(pos, color='r', linestyle='--', alpha=0.7)

    # Plot derivative
    d_transmission = np.diff(transmission)
    d_spectrum = spectrum[:-1]
    ax2.plot(d_spectrum, d_transmission, 'g-', linewidth=1.5)
    ax2.set_xlabel("Wavelength / TOF (µs)")
    ax2.set_ylabel("d(Transmission)/dx")
    ax2.set_title(f"{title} - Derivative")
    ax2.grid(True, alpha=0.3)

    if edge_positions:
        for pos in edge_positions:
            ax2.axvline(pos, color='r', linestyle='--', alpha=0.7)

    plt.tight_layout()
    return fig


def plot_edge_maps(
    edge_position: np.ndarray,
    edge_width: np.ndarray,
    edge_height: np.ndarray,
    titles: Optional[Tuple[str, str, str]] = None,
    figsize: Tuple[int, int] = (15, 5),
    cmap: str = "viridis",
):
    """
    Plot 2D maps of edge parameters.

    Parameters
    ----------
    edge_position : np.ndarray
        2D array of edge positions
    edge_width : np.ndarray
        2D array of edge widths
    edge_height : np.ndarray
        2D array of edge heights
    titles : tuple of str, optional
        Titles for (position, width, height) plots
    figsize : tuple
        Figure size
    cmap : str
        Colormap name
    """
    if titles is None:
        titles = ("Edge Position", "Edge Width", "Edge Height")

    fig, axes = plt.subplots(1, 3, figsize=figsize)

    # Position map
    im1 = axes[0].imshow(edge_position, cmap=cmap, aspect='auto')
    axes[0].set_title(titles[0])
    axes[0].set_xlabel("X (pixels)")
    axes[0].set_ylabel("Y (pixels)")
    plt.colorbar(im1, ax=axes[0], label="Position")

    # Width map
    im2 = axes[1].imshow(edge_width, cmap=cmap, aspect='auto')
    axes[1].set_title(titles[1])
    axes[1].set_xlabel("X (pixels)")
    axes[1].set_ylabel("Y (pixels)")
    plt.colorbar(im2, ax=axes[1], label="Width")

    # Height map
    im3 = axes[2].imshow(edge_height, cmap=cmap, aspect='auto')
    axes[2].set_title(titles[2])
    axes[2].set_xlabel("X (pixels)")
    axes[2].set_ylabel("Y (pixels)")
    plt.colorbar(im3, ax=axes[2], label="Height")

    plt.tight_layout()
    return fig
