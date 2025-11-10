"""
Data Processing Utilities
==========================

Functions for handling detector readout gaps, interpolation, and data merging.
"""

import numpy as np
from typing import Optional, Tuple
import matplotlib.pyplot as plt


def interpolate_noreadoutgaps(
    y: np.ndarray,
    t: np.ndarray,
    tmax: float,
    nrep: int,
    plot_flag: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Interpolate and merge chopper repetitions to remove readout gaps.

    Neutron detectors often have readout gaps between consecutive measurements.
    This function interpolates the data onto a uniform time grid and averages
    over multiple chopper repetitions to fill these gaps.

    Parameters
    ----------
    y : np.ndarray
        Input signal (intensity vs time), shape (n,)
    t : np.ndarray
        Time-of-flight values, shape (n,)
    tmax : float
        Maximum time-of-flight value
    nrep : int
        Number of chopper repetitions
    plot_flag : bool, optional
        If True, plot the individual repetitions and merged result

    Returns
    -------
    y_merged : np.ndarray
        Merged signal with readout gaps removed, shape (replen,)
    t_merged : np.ndarray
        Corresponding time array, shape (replen,)

    Notes
    -----
    The function works by:
    1. Interpolating data onto a uniform grid covering all repetitions
    2. Reshaping into (replen, nrep) where each column is one repetition
    3. Averaging across repetitions using nanmean to handle gaps

    Examples
    --------
    >>> y = np.random.randn(800)  # 8 repetitions of 100 bins each
    >>> t = np.linspace(0, 8000, 800)
    >>> y_merged, t_merged = interpolate_noreadoutgaps(y, t, 8000, 8)
    >>> print(y_merged.shape)  # (100,)
    """
    # Reformat arrays to 1D
    y = np.squeeze(y)
    t = np.squeeze(t)

    if y.ndim > 1:
        y = y.flatten()
    if t.ndim > 1:
        t = t.flatten()

    # Calculate length of one repetition
    replen = int(np.ceil(len(y) / nrep))

    # Create uniform time grid
    t_tot = np.linspace(t[0], tmax, nrep * replen)

    # Interpolate onto uniform grid
    y_int = np.interp(t_tot, t, y)

    # Reshape into (replen, nrep) - each column is one repetition
    y_overlap = np.zeros((replen, nrep))

    for i in range(nrep):
        start_idx = replen * i
        end_idx = replen * (i + 1)
        y_overlap[:, i] = y_int[start_idx:end_idx]

    # Average over repetitions (use nanmean to handle NaN values)
    y_merged = np.nanmean(y_overlap, axis=1)

    # Time array for one repetition
    t_merged = t_tot[:replen]

    # Optional plotting
    if plot_flag:
        plt.figure(figsize=(10, 6))
        for i in range(nrep):
            plt.plot(t_merged, y_overlap[:, i], alpha=0.5, label=f"Rep {i+1}")
        plt.plot(t_merged, y_merged, 'k-', linewidth=2, label="Merged")
        plt.xlabel("Time-of-Flight (µs)")
        plt.ylabel("Intensity")
        plt.legend()
        plt.title("Chopper Repetitions and Merged Result")
        plt.grid(True, alpha=0.3)
        plt.show()

    return y_merged, t_merged
