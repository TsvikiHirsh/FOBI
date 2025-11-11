"""
Wiener Deconvolution for FOBI Reconstruction
=============================================

This module implements Wiener deconvolution for reconstructing neutron
time-of-flight transmission spectra from chopper-modulated measurements.
"""

import numpy as np
from scipy.signal import wiener
from scipy.ndimage import gaussian_filter1d
from typing import Literal, Optional

from .data_processing import interpolate_noreadoutgaps
from .time_delays import (
    fobi_poldi_time_delays,
    fobi_4x10_time_delays,
    fobi_5x8_time_delays,
    fobi_3x14_time_delays,
)


def wiener_deconvolution(
    f: np.ndarray,
    g: np.ndarray,
    c: float = 0.1,
    filter_type: Literal["none", "LowPass", "LowPassBu", "LowPassGa"] = "none",
) -> np.ndarray:
    """
    Perform Wiener deconvolution using the correlation theorem.

    The Wiener filter in frequency domain is:
        H = F * conj(G) / (|G|^2 + c)

    where F is the FFT of the measured signal, G is the FFT of the instrument
    response (chopper time delays), and c is a regularization constant.

    Parameters
    ----------
    f : np.ndarray
        Input signal (measured transmission), shape (n,)
    g : np.ndarray
        Instrument response function (time delays), shape (n,)
    c : float, optional
        Regularization constant (noise parameter), default 0.1
        Higher values give more smoothing but less resolution
    filter_type : str, optional
        Type of low-pass filter to apply in frequency domain:
        - 'none': No filtering (default)
        - 'LowPass': Rectangular window
        - 'LowPassBu': Butterworth-like filter
        - 'LowPassGa': Gaussian filter

    Returns
    -------
    H : np.ndarray
        Deconvolved signal (reconstructed transmission spectrum)

    Notes
    -----
    The deconvolution is performed in the frequency domain using the
    Wiener filter, which balances signal recovery with noise suppression.

    Examples
    --------
    >>> signal = np.random.randn(1000)
    >>> response = np.zeros(1000)
    >>> response[500] = 1.0  # Delta function
    >>> reconstructed = wiener_deconvolution(signal, response, c=0.01)
    """
    # Ensure column vectors
    f = np.squeeze(f)
    g = np.squeeze(g)

    if f.ndim > 1:
        f = f.flatten()
    if g.ndim > 1:
        g = g.flatten()

    # Correlation theorem: H = F * conj(G) / (|G|^2 + c)
    F = np.fft.fft(f)
    G = np.fft.fft(g)

    arg = F * np.conj(G) / (np.abs(G)**2 + c)

    # Apply optional frequency domain filtering
    if filter_type != "none":
        lf = len(f)
        K = _create_filter_kernel(lf, filter_type)
        arg = np.fft.fftshift(K) * arg

    # Inverse FFT and return real part
    H = np.real(np.fft.ifft(arg))

    return H


def _create_filter_kernel(
    length: int,
    filter_type: Literal["LowPass", "LowPassBu", "LowPassGa"]
) -> np.ndarray:
    """
    Create frequency domain filter kernel.

    Parameters
    ----------
    length : int
        Length of the kernel
    filter_type : str
        Type of filter ('LowPass', 'LowPassBu', or 'LowPassGa')

    Returns
    -------
    K : np.ndarray
        Filter kernel in frequency domain
    """
    K = np.zeros(length)

    # Center index
    if length % 2 == 0:
        x0 = length // 2
    else:
        x0 = length // 2

    if filter_type == "LowPass":
        # Rectangular window
        ww = 4
        width = round(x0 / ww)
        start = max(0, x0 - round(width/2))
        end = min(length, x0 + round(width/2))
        K[start:end] = 1

    elif filter_type == "LowPassBu":
        # Butterworth-like filter
        n = 5
        ww = 5
        width = max(1, round(x0 / ww))

        if x0 < length:
            K[x0] = 1

        # Right side
        right_len = length - x0 - 1
        if right_len > 0:
            D = np.arange(1, right_len + 1)
            HH = 1.0 / (1 + (D / width)**(2*n))
            K[x0+1:x0+1+len(HH)] = HH

        # Left side
        if x0 > 0:
            D = np.arange(1, x0 + 1)
            HH = 1.0 / (1 + (D / width)**(2*n))
            K[:x0] = np.flip(HH)

    elif filter_type == "LowPassGa":
        # Gaussian filter
        width = max(1, round(x0 / 10))

        if x0 < length:
            K[x0] = 1

        # Right side
        right_len = length - x0 - 1
        if right_len > 0:
            D = np.arange(1, right_len + 1)
            HH = np.exp(-(D**2 / (2 * width**2)))
            K[x0+1:x0+1+len(HH)] = HH

        # Left side
        if x0 > 0:
            D = np.arange(1, x0 + 1)
            HH = np.exp(-(D**2 / (2 * width**2)))
            K[:x0] = np.flip(HH)

    return K


def fobi_wiener_2d(
    I: np.ndarray,
    I0: np.ndarray,
    t: np.ndarray,
    tmax: float,
    nrep: int,
    chopper_id: Literal["POLDI", "4x10", "5x8", "3x14"],
    c: float = 0.1,
    filter_type: str = "none",
    roll: int = 0,
    flag_smooth: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform 2D spatially-resolved FOBI Wiener deconvolution.

    This function processes entire 2D detector images, performing Wiener
    deconvolution pixel-by-pixel to reconstruct transmission spectra.

    Parameters
    ----------
    I : np.ndarray
        Sample transmission data, shape (rows, cols, time_bins)
    I0 : np.ndarray
        Open beam (normalization) data, shape (rows, cols, time_bins)
    t : np.ndarray
        Time-of-flight values for each bin, shape (time_bins,)
    tmax : float
        Maximum time-of-flight value
    nrep : int
        Number of chopper repetitions
    chopper_id : str
        Chopper configuration ('POLDI', '4x10', '5x8', or '3x14')
    c : float, optional
        Wiener filter regularization parameter, default 0.1
    filter_type : str, optional
        Frequency domain filter type ('none', 'LowPass', 'LowPassBu', 'LowPassGa')
    roll : int, optional
        Circular shift to apply to reconstructed spectra, default 0
    flag_smooth : int, optional
        Smoothing span for moving average filter (0 = no smoothing)

    Returns
    -------
    T : np.ndarray
        Reconstructed transmission (sample/open beam), shape (rows, cols, time_bins)
    y_rec : np.ndarray
        Reconstructed sample intensity, shape (rows, cols, time_bins)
    y0_rec : np.ndarray
        Reconstructed open beam intensity, shape (rows, cols, time_bins)
    t_merged : np.ndarray
        Merged time-of-flight array after interpolation

    Notes
    -----
    The function performs the following steps for each pixel:
    1. Interpolate readout gaps and merge repetitions
    2. Apply optional smoothing
    3. Perform Wiener deconvolution on sample and open beam
    4. Calculate transmission as ratio of deconvolved signals
    5. Apply optional circular shift

    Examples
    --------
    >>> I = np.random.randn(100, 100, 1000)
    >>> I0 = np.random.randn(100, 100, 1000)
    >>> t = np.linspace(0, 10000, 1000)
    >>> T, y_rec, y0_rec, t_merged = fobi_wiener_2d(
    ...     I, I0, t, 10000, 8, 'POLDI', c=0.1
    ... )
    """
    siz = I.shape

    # Get central pixel for time array calculation
    y0_center = np.squeeze(I0[round(siz[0]/2), round(siz[1]/2), :])
    _, t_merged = interpolate_noreadoutgaps(y0_center, t, tmax, nrep, plot_flag=False)

    # Choose time delays based on chopper configuration
    chopper_functions = {
        "POLDI": fobi_poldi_time_delays,
        "4x10": fobi_4x10_time_delays,
        "5x8": fobi_5x8_time_delays,
        "3x14": fobi_3x14_time_delays,
    }

    if chopper_id not in chopper_functions:
        raise ValueError(f"Unknown chopper ID: {chopper_id}. "
                        f"Choose from {list(chopper_functions.keys())}")

    D = chopper_functions[chopper_id](t_merged)

    # Number of slits for each chopper
    nslits_map = {"POLDI": 8, "4x10": 10, "5x8": 8, "3x14": 14}
    nslits = nslits_map[chopper_id]

    # Initialize output arrays
    T = np.zeros((siz[0], siz[1], len(t_merged)))
    y_rec = np.zeros_like(T)
    y0_rec = np.zeros_like(T)

    # Process each pixel
    for i in range(siz[0]):
        print(f"FOBI reduction of row: {i+1}/{siz[0]}")
        for j in range(siz[1]):
            y = np.squeeze(I[i, j, :])
            y0 = np.squeeze(I0[i, j, :])

            # Optional smoothing
            if flag_smooth:
                from scipy.signal import savgol_filter
                window_length = min(flag_smooth, len(y) - 1)
                if window_length % 2 == 0:
                    window_length -= 1
                if window_length >= 3:
                    y = savgol_filter(y, window_length, 3)
                    y0 = savgol_filter(y0, window_length, 3)

            # Interpolate readout gaps
            y, _ = interpolate_noreadoutgaps(y, t, tmax, nrep, plot_flag=False)
            y0, _ = interpolate_noreadoutgaps(y0, t, tmax, nrep, plot_flag=False)

            # Wiener deconvolution
            yrec = nslits * nrep * wiener_deconvolution(y, D, c, filter_type)
            y0rec = nslits * nrep * wiener_deconvolution(y0, D, c, filter_type)

            # Calculate transmission (deconvolve T directly for better edge contrast)
            with np.errstate(divide='ignore', invalid='ignore'):
                T_ratio = y / y0
                T_ratio[~np.isfinite(T_ratio)] = 1.0
            Trec = nslits * wiener_deconvolution(T_ratio, D, c, filter_type)

            # Apply circular shift if requested
            yrec_merged = np.roll(yrec, roll)
            y0rec_merged = np.roll(y0rec, roll)
            Trec_merged = np.roll(Trec, roll)

            T[i, j, :] = Trec_merged
            y_rec[i, j, :] = yrec_merged
            y0_rec[i, j, :] = y0rec_merged

    return T, y_rec, y0_rec, t_merged
