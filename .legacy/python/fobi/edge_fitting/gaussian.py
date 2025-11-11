"""
Gaussian Edge Fitting
=====================

Functions for fitting Gaussian models to Bragg edges in transmission spectra.
"""

import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
from typing import Tuple, Optional
import matplotlib.pyplot as plt

from .utils import find_nearest


def gaussian_model(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Gaussian function for edge fitting.

    The derivative of transmission shows Gaussian-like peaks at Bragg edges.

    Parameters
    ----------
    x : np.ndarray
        Independent variable (wavelength or TOF)
    a : float
        Amplitude (edge height)
    b : float
        Center position (edge position)
    c : float
        Width (standard deviation, related to edge broadening)

    Returns
    -------
    y : np.ndarray
        Gaussian function values
    """
    return a * np.exp(-((x - b)**2) / (2 * c**2))


def edge_fit_gaussian(
    signal: np.ndarray,
    spectrum: np.ndarray,
    spectrum_range: Tuple[float, float],
    est_p: float,
    est_w: float,
    est_h: float,
    BC_p: Tuple[float, float],
    BC_w: Tuple[float, float],
    BC_h: Tuple[float, float],
    smooth_span: int = 0,
    plot_result: bool = False,
) -> Tuple[float, float, float]:
    """
    Fit a Gaussian model to a single Bragg edge.

    This function fits the derivative of the transmission spectrum with a
    Gaussian to extract edge position, width, and height.

    Parameters
    ----------
    signal : np.ndarray
        Transmission spectrum, shape (n,)
    spectrum : np.ndarray
        Wavelength or TOF array, shape (n,)
    spectrum_range : tuple of float
        (min, max) range for fitting
    est_p : float
        Initial guess for edge position
    est_w : float
        Initial guess for edge width
    est_h : float
        Initial guess for edge height (amplitude)
    BC_p : tuple of float
        (lower, upper) bounds for position
    BC_w : tuple of float
        (lower, upper) bounds for width
    BC_h : tuple of float
        (lower, upper) bounds for height
    smooth_span : int, optional
        Smoothing window size (0 = no smoothing)
    plot_result : bool, optional
        If True, plot the fit result

    Returns
    -------
    pos : float
        Fitted edge position
    wid : float
        Fitted edge width
    h : float
        Fitted edge height

    Notes
    -----
    The fitting is performed on the derivative of the transmission spectrum,
    as Bragg edges appear as step-like features in transmission and
    Gaussian-like peaks in the derivative.

    Examples
    --------
    >>> spectrum = np.linspace(0, 10, 1000)
    >>> signal = 1 - 0.5 / (1 + np.exp(-(spectrum - 5) / 0.1))  # Smooth step
    >>> pos, wid, h = edge_fit_gaussian(
    ...     signal, spectrum, (4, 6), 5.0, 0.1, -0.5,
    ...     (4, 6), (0.01, 1), (-2, 0), smooth_span=5
    ... )
    """
    # Prepare data: compute derivative
    d_spectrum = spectrum[:-1]

    # Optional smoothing using Savitzky-Golay filter
    if smooth_span > 0:
        window_length = min(smooth_span, len(signal) - 1)
        if window_length % 2 == 0:
            window_length -= 1
        if window_length >= 3:
            signal = savgol_filter(signal, window_length, 3)

    # Compute derivative
    d_signal = np.diff(signal)

    # Extract fitting range
    idx_min = find_nearest(d_spectrum, spectrum_range[0])
    idx_max = find_nearest(d_spectrum, spectrum_range[1])

    x = d_spectrum[idx_min:idx_max+1]
    y = d_signal[idx_min:idx_max+1]

    # Handle NaN values
    valid = np.isfinite(y)
    x = x[valid]
    y = y[valid]

    if len(x) < 3:
        # Not enough points to fit
        return np.nan, np.nan, np.nan

    # Set up bounds and initial guess
    p0 = [est_h, est_p, est_w]
    bounds = ([BC_h[0], BC_p[0], BC_w[0]], [BC_h[1], BC_p[1], BC_w[1]])

    try:
        # Perform curve fitting
        popt, _ = curve_fit(gaussian_model, x, y, p0=p0, bounds=bounds, maxfev=5000)
        h, pos, wid = popt

        # Optional plotting
        if plot_result:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

            # Plot derivative and fit
            ax1.plot(x, y, 'b-', label="Data (derivative)")
            x_fit = np.linspace(x[0], x[-1], 500)
            y_fit = gaussian_model(x_fit, h, pos, wid)
            ax1.plot(x_fit, y_fit, 'r--', linewidth=2, label="Gaussian fit")
            ax1.axvline(pos, color='g', linestyle=':', label=f"Position = {pos:.3f}")
            ax1.set_xlabel("Wavelength / TOF")
            ax1.set_ylabel("d(Transmission)/dx")
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_title("Edge Derivative and Gaussian Fit")

            # Plot original signal
            idx_sig_min = find_nearest(spectrum, spectrum_range[0])
            idx_sig_max = find_nearest(spectrum, spectrum_range[1])
            ax2.plot(spectrum[idx_sig_min:idx_sig_max+1],
                    signal[idx_sig_min:idx_sig_max+1], 'b-')
            ax2.axvline(pos, color='g', linestyle=':', label=f"Position = {pos:.3f}")
            ax2.set_xlabel("Wavelength / TOF")
            ax2.set_ylabel("Transmission")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.set_title("Original Transmission Spectrum")

            plt.tight_layout()
            plt.show()

        return pos, wid, h

    except (RuntimeError, ValueError) as e:
        # Fitting failed
        print(f"Warning: Gaussian fit failed - {e}")
        return np.nan, np.nan, np.nan


def edge_fit_gaussian_2d(
    data: np.ndarray,
    spectrum: np.ndarray,
    spectrum_range: Tuple[float, float],
    est_p: float,
    est_w: float,
    est_h: float,
    BC_p: Tuple[float, float],
    BC_w: Tuple[float, float],
    BC_h: Tuple[float, float],
    mask: Optional[np.ndarray] = None,
    test: Optional[Tuple[int, int]] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform 2D spatially-resolved Gaussian edge fitting.

    This function fits Bragg edges pixel-by-pixel across a 2D detector image,
    producing spatial maps of edge position, width, and height.

    Parameters
    ----------
    data : np.ndarray
        Transmission data, shape (rows, cols, spectrum_length)
    spectrum : np.ndarray
        Wavelength or TOF array
    spectrum_range : tuple of float
        (min, max) range for fitting
    est_p : float
        Initial guess for edge position
    est_w : float
        Initial guess for edge width
    est_h : float
        Initial guess for edge height
    BC_p : tuple of float
        (lower, upper) bounds for position
    BC_w : tuple of float
        (lower, upper) bounds for width
    BC_h : tuple of float
        (lower, upper) bounds for height
    mask : np.ndarray, optional
        Binary mask (1 = fit, 0 = skip), shape (rows, cols)
    test : tuple of int, optional
        If provided, only fit pixel (test[0], test[1]) and plot result

    Returns
    -------
    edge_p : np.ndarray
        Edge position map, shape (rows, cols)
    edge_w : np.ndarray
        Edge width map, shape (rows, cols)
    edge_h : np.ndarray
        Edge height map, shape (rows, cols)

    Notes
    -----
    NaN values are assigned to masked-out or failed fit pixels.

    Examples
    --------
    >>> data = np.random.randn(100, 100, 1000)
    >>> spectrum = np.linspace(0, 10, 1000)
    >>> edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
    ...     data, spectrum, (4, 6), 5.0, 0.1, -0.5,
    ...     (4, 6), (0.01, 1), (-2, 0)
    ... )
    """
    s = data.shape

    # Create default mask if not provided
    if mask is None:
        mask = np.ones((s[0], s[1]))

    # Initialize output arrays
    edge_p = np.zeros((s[0], s[1]))
    edge_w = np.zeros((s[0], s[1]))
    edge_h = np.zeros((s[0], s[1]))

    # Test mode: fit single pixel with plotting
    if test is not None:
        i, j = test
        edge_fit_gaussian(
            np.squeeze(data[i, j, :]), spectrum, spectrum_range,
            est_p, est_w, est_h, BC_p, BC_w, BC_h, smooth_span=1, plot_result=True
        )
        return edge_p, edge_w, edge_h

    # Fit all pixels
    for i in range(s[0]):
        print(f"Fitting row: {i+1}/{s[0]}")
        for j in range(s[1]):
            if mask[i, j] == 1:
                a, b, c = edge_fit_gaussian(
                    np.squeeze(data[i, j, :]), spectrum, spectrum_range,
                    est_p, est_w, est_h, BC_p, BC_w, BC_h, smooth_span=0, plot_result=False
                )
                edge_p[i, j] = a
                edge_w[i, j] = b
                edge_h[i, j] = c
            else:
                edge_p[i, j] = np.nan
                edge_w[i, j] = np.nan
                edge_h[i, j] = np.nan

    return edge_p, edge_w, edge_h
