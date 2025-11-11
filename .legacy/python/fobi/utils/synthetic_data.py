"""
Synthetic test data generation for FOBI analysis.
"""

import numpy as np
from typing import Tuple, Optional


def generate_test_data(
    shape: Tuple[int, int, int] = (50, 50, 500),
    edge_position: float = 250.0,
    edge_width: float = 10.0,
    edge_height: float = 0.5,
    noise_level: float = 0.02,
    add_spatial_variation: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate synthetic neutron transmission data with Bragg edges.

    This function creates realistic test data for FOBI analysis, including:
    - Smooth transmission edges (step-like features)
    - Optional spatial variation in edge parameters
    - Poisson noise to simulate counting statistics
    - Gaussian noise for detector readout

    Parameters
    ----------
    shape : tuple of int
        Data shape (rows, cols, time_bins)
    edge_position : float
        Center position of the Bragg edge (in bins)
    edge_width : float
        Width of the edge transition (in bins)
    edge_height : float
        Edge drop (0 to 1, represents transmission decrease)
    noise_level : float
        Relative noise level (standard deviation / mean)
    add_spatial_variation : bool
        If True, add spatial gradients to edge parameters

    Returns
    -------
    I : np.ndarray
        Sample transmission data with edge, shape (rows, cols, time_bins)
    I0 : np.ndarray
        Open beam (normalization) data, shape (rows, cols, time_bins)
    t : np.ndarray
        Time-of-flight array, shape (time_bins,)

    Examples
    --------
    >>> I, I0, t = generate_test_data(shape=(100, 100, 1000), edge_position=500)
    >>> print(I.shape)
    (100, 100, 1000)
    """
    rows, cols, nbins = shape

    # Create time-of-flight array (in microseconds)
    t = np.linspace(0, 10000, nbins)

    # Initialize arrays
    I = np.zeros((rows, cols, nbins))
    I0 = np.ones((rows, cols, nbins))

    # Create spatial coordinate grids for variation
    if add_spatial_variation:
        y_coords, x_coords = np.meshgrid(
            np.linspace(-1, 1, rows),
            np.linspace(-1, 1, cols),
            indexing='ij'
        )
        # Position varies by ±5% across detector
        position_map = edge_position * (1 + 0.05 * x_coords)
        # Width varies by ±10%
        width_map = edge_width * (1 + 0.1 * y_coords)
        # Height varies by ±10%
        height_map = edge_height * (1 + 0.1 * (x_coords + y_coords) / 2)
    else:
        position_map = np.full((rows, cols), edge_position)
        width_map = np.full((rows, cols), edge_width)
        height_map = np.full((rows, cols), edge_height)

    # Generate transmission spectra pixel by pixel
    for i in range(rows):
        for j in range(cols):
            # Create smooth edge using error function (integral of Gaussian)
            from scipy.special import erf

            # Edge shape: smooth step function
            edge = 0.5 * (1 - erf((np.arange(nbins) - position_map[i, j]) / width_map[i, j]))

            # Transmission: starts at 1, drops by edge_height at the edge
            transmission = 1.0 - height_map[i, j] * edge

            # Add baseline offset (typical transmission level)
            baseline = 0.8
            transmission = transmission * baseline

            # Open beam: flat spectrum with slight variation
            open_beam = np.ones(nbins) * baseline

            # Add Poisson noise (counting statistics)
            if noise_level > 0:
                # Scale to represent counts
                mean_counts = 10000
                transmission_counts = np.random.poisson(transmission * mean_counts)
                transmission = transmission_counts / mean_counts

                open_beam_counts = np.random.poisson(open_beam * mean_counts)
                open_beam = open_beam_counts / mean_counts

                # Add Gaussian readout noise
                transmission += np.random.normal(0, noise_level * baseline, nbins)
                open_beam += np.random.normal(0, noise_level * baseline, nbins)

            # Clip to physical range [0, inf)
            transmission = np.maximum(transmission, 0)
            open_beam = np.maximum(open_beam, 0)

            I[i, j, :] = transmission
            I0[i, j, :] = open_beam

    return I, I0, t


def generate_chopper_modulated_data(
    shape: Tuple[int, int, int] = (50, 50, 1000),
    nrep: int = 8,
    chopper_id: str = "POLDI",
    edge_position: float = 500.0,
    edge_width: float = 20.0,
    edge_height: float = 0.5,
    noise_level: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Generate synthetic chopper-modulated neutron data for FOBI testing.

    This creates realistic time-of-flight data as measured through a chopper,
    with multiple repetitions and readout gaps.

    Parameters
    ----------
    shape : tuple of int
        Data shape (rows, cols, time_bins)
    nrep : int
        Number of chopper repetitions
    chopper_id : str
        Chopper configuration ('POLDI', '4x10', '5x8', '3x14')
    edge_position : float
        True edge position (in bins, for reconstructed spectrum)
    edge_width : float
        True edge width (in bins)
    edge_height : float
        Edge transmission drop (0 to 1)
    noise_level : float
        Relative noise level

    Returns
    -------
    I_mod : np.ndarray
        Chopper-modulated sample data, shape (rows, cols, time_bins)
    I0_mod : np.ndarray
        Chopper-modulated open beam data, shape (rows, cols, time_bins)
    t : np.ndarray
        Time-of-flight array, shape (time_bins,)
    tmax : float
        Maximum time-of-flight value

    Notes
    -----
    This function simulates the measurement process:
    1. Generate true transmission spectrum
    2. Convolve with chopper response (time delays)
    3. Add readout gaps and repetitions
    4. Add noise

    The resulting data can be processed with fobi_wiener_2d to reconstruct
    the original transmission spectrum.
    """
    from ..reduction.time_delays import (
        fobi_poldi_time_delays,
        fobi_4x10_time_delays,
        fobi_5x8_time_delays,
        fobi_3x14_time_delays,
    )

    rows, cols, nbins = shape

    # Generate true transmission data
    I_true, I0_true, t_true = generate_test_data(
        shape=(rows, cols, nbins // nrep),
        edge_position=edge_position / nrep,
        edge_width=edge_width / nrep,
        edge_height=edge_height,
        noise_level=0,  # Add noise after convolution
        add_spatial_variation=True,
    )

    # Get chopper time delays
    chopper_functions = {
        "POLDI": fobi_poldi_time_delays,
        "4x10": fobi_4x10_time_delays,
        "5x8": fobi_5x8_time_delays,
        "3x14": fobi_3x14_time_delays,
    }

    if chopper_id not in chopper_functions:
        raise ValueError(f"Unknown chopper ID: {chopper_id}")

    D = chopper_functions[chopper_id](t_true)

    # Initialize modulated data
    I_mod = np.zeros(shape)
    I0_mod = np.zeros(shape)

    # Convolve each pixel with chopper response
    for i in range(rows):
        for j in range(cols):
            # Convolve with chopper response
            signal_conv = np.convolve(I_true[i, j, :], D, mode='same')
            open_conv = np.convolve(I0_true[i, j, :], D, mode='same')

            # Replicate to simulate multiple repetitions
            signal_rep = np.tile(signal_conv, nrep)
            open_rep = np.tile(open_conv, nrep)

            # Add readout gaps (simulate dead time)
            replen = len(signal_conv)
            for rep in range(nrep):
                start = rep * replen
                end = (rep + 1) * replen
                # Last 5% of each repetition is dead time
                gap_start = end - int(0.05 * replen)
                signal_rep[gap_start:end] = 0
                open_rep[gap_start:end] = 0

            # Trim to desired length
            I_mod[i, j, :] = signal_rep[:nbins]
            I0_mod[i, j, :] = open_rep[:nbins]

    # Add noise
    if noise_level > 0:
        mean_level = 0.8
        mean_counts = 10000

        for i in range(rows):
            for j in range(cols):
                # Poisson noise
                counts = np.random.poisson(I_mod[i, j, :] * mean_counts)
                I_mod[i, j, :] = counts / mean_counts

                counts0 = np.random.poisson(I0_mod[i, j, :] * mean_counts)
                I0_mod[i, j, :] = counts0 / mean_counts

                # Gaussian noise
                I_mod[i, j, :] += np.random.normal(0, noise_level * mean_level, nbins)
                I0_mod[i, j, :] += np.random.normal(0, noise_level * mean_level, nbins)

    # Create time array
    tmax = 10000.0
    t = np.linspace(0, tmax, nbins)

    return I_mod, I0_mod, t, tmax
