"""
Realistic synthetic test data generation for FOBI analysis with proper POLDI characteristics.
"""

import numpy as np
from typing import Tuple, Optional, List


def poldi_neutron_flux(wavelength: np.ndarray) -> np.ndarray:
    """
    Generate realistic POLDI neutron flux spectrum.

    POLDI provides neutrons in the 1-10 Angstrom range with:
    - Rise starting at 1 Å
    - Peak at ~1.5 Å
    - Long tail to ~8 Å

    Parameters
    ----------
    wavelength : np.ndarray
        Wavelength array in Angstroms

    Returns
    -------
    flux : np.ndarray
        Normalized neutron flux
    """
    # Maxwell-Boltzmann distribution modified for cold neutron guide
    # Peak wavelength around 1.5 Å
    lambda_peak = 1.5

    # Modified Maxwell-Boltzmann with exponential tail
    flux = (wavelength**3 / lambda_peak**4) * np.exp(-wavelength / lambda_peak)

    # Add exponential tail for longer wavelengths
    tail_contrib = 0.3 * np.exp(-(wavelength - 1.5) / 2.5)
    flux = flux + tail_contrib

    # Cutoff below 1 Å and above 8 Å
    flux[wavelength < 1.0] = 0
    flux[wavelength > 8.0] *= np.exp(-(wavelength[wavelength > 8.0] - 8.0) / 0.5)

    # Normalize
    flux = flux / np.max(flux)

    return flux


def wavelength_to_tof(wavelength: np.ndarray, L: float = 10.0) -> np.ndarray:
    """
    Convert wavelength (Å) to time-of-flight (microseconds).

    TOF = (m * L) / h * lambda
    where m is neutron mass, L is flight path, h is Planck constant

    For practical use: TOF [µs] ≈ 252.778 * L[m] * lambda[Å]

    Parameters
    ----------
    wavelength : np.ndarray
        Wavelength in Angstroms
    L : float
        Flight path length in meters (default 10 m for POLDI)

    Returns
    -------
    tof : np.ndarray
        Time-of-flight in microseconds
    """
    # Conversion constant: µs⋅m⁻¹⋅Å⁻¹
    conversion_factor = 252.778
    tof = conversion_factor * L * wavelength
    return tof


def tof_to_wavelength(tof: np.ndarray, L: float = 10.0) -> np.ndarray:
    """
    Convert time-of-flight (microseconds) to wavelength (Å).

    Parameters
    ----------
    tof : np.ndarray
        Time-of-flight in microseconds
    L : float
        Flight path length in meters

    Returns
    -------
    wavelength : np.ndarray
        Wavelength in Angstroms
    """
    conversion_factor = 252.778
    wavelength = tof / (conversion_factor * L)
    return wavelength


def bragg_edge_transmission(
    wavelength: np.ndarray,
    edge_lambda: float,
    edge_height: float = 0.4,
    sigma: float = 0.01
) -> np.ndarray:
    """
    Generate realistic Bragg edge in transmission.

    Bragg edges appear as step-like decreases in transmission at specific
    wavelengths corresponding to crystallographic planes.

    Parameters
    ----------
    wavelength : np.ndarray
        Wavelength array in Angstroms
    edge_lambda : float
        Bragg edge position in Angstroms
    edge_height : float
        Transmission drop at edge (0 to 1)
    sigma : float
        Edge width parameter (Angstroms)

    Returns
    -------
    transmission : np.ndarray
        Transmission values (0 to 1)
    """
    from scipy.special import erf

    # Smooth step function using error function
    transmission = 1.0 - (edge_height / 2) * (1 + erf((wavelength - edge_lambda) / sigma))

    return transmission


def generate_realistic_bragg_edges(
    wavelength: np.ndarray,
    material: str = 'Fe'
) -> np.ndarray:
    """
    Generate realistic Bragg edge pattern for common materials.

    Parameters
    ----------
    wavelength : np.ndarray
        Wavelength array in Angstroms
    material : str
        Material name ('Fe', 'Al', 'Cu', etc.)

    Returns
    -------
    transmission : np.ndarray
        Total transmission spectrum with multiple edges
    """
    transmission = np.ones_like(wavelength)

    if material == 'Fe':
        # Body-centered cubic (BCC) iron
        # Main edges: 110, 200, 211, 220, 310, 222
        edges = [
            {'lambda': 4.05, 'height': 0.35, 'sigma': 0.015},  # 110 edge
            {'lambda': 2.87, 'height': 0.25, 'sigma': 0.012},  # 200 edge
            {'lambda': 2.34, 'height': 0.20, 'sigma': 0.010},  # 211 edge
        ]
    elif material == 'Al':
        # Face-centered cubic (FCC) aluminum
        edges = [
            {'lambda': 4.05, 'height': 0.30, 'sigma': 0.015},  # 111 edge
            {'lambda': 2.86, 'height': 0.25, 'sigma': 0.012},  # 200 edge
            {'lambda': 2.02, 'height': 0.15, 'sigma': 0.010},  # 220 edge
        ]
    else:
        # Generic single edge
        edges = [{'lambda': 3.5, 'height': 0.35, 'sigma': 0.015}]

    # Apply all edges
    for edge in edges:
        edge_trans = bragg_edge_transmission(
            wavelength, edge['lambda'], edge['height'], edge['sigma']
        )
        transmission *= edge_trans

    return transmission


def generate_realistic_poldi_data(
    shape: Tuple[int, int, int] = (50, 50, 500),
    wavelength_range: Tuple[float, float] = (1.0, 8.0),
    material: str = 'Fe',
    flight_path: float = 10.0,
    noise_level: float = 0.02,
    add_spatial_variation: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate realistic POLDI neutron imaging data.

    This creates physically realistic transmission data including:
    - Proper POLDI neutron flux spectrum (1-8 Å)
    - Realistic Bragg edges for specified material
    - Wavelength to TOF conversion
    - Counting statistics (Poisson noise)

    Parameters
    ----------
    shape : tuple
        Data shape (rows, cols, wavelength_bins)
    wavelength_range : tuple
        (min, max) wavelength in Angstroms
    material : str
        Material name for Bragg edges ('Fe', 'Al', 'Cu')
    flight_path : float
        Neutron flight path in meters
    noise_level : float
        Relative noise level
    add_spatial_variation : bool
        Add spatial gradients to simulate strain/texture

    Returns
    -------
    I : np.ndarray
        Sample transmission data, shape (rows, cols, wavelength_bins)
    I0 : np.ndarray
        Open beam data, shape (rows, cols, wavelength_bins)
    wavelength : np.ndarray
        Wavelength array in Angstroms
    tof : np.ndarray
        Time-of-flight array in microseconds
    """
    rows, cols, nbins = shape

    # Create wavelength array
    wavelength = np.linspace(wavelength_range[0], wavelength_range[1], nbins)

    # Convert to TOF
    tof = wavelength_to_tof(wavelength, L=flight_path)

    # Generate POLDI neutron flux
    flux = poldi_neutron_flux(wavelength)

    # Generate Bragg edge transmission pattern
    base_transmission = generate_realistic_bragg_edges(wavelength, material)

    # Initialize arrays
    I = np.zeros((rows, cols, nbins))
    I0 = np.zeros((rows, cols, nbins))

    # Create spatial coordinate grids for variation
    if add_spatial_variation:
        y_coords, x_coords = np.meshgrid(
            np.linspace(-1, 1, rows),
            np.linspace(-1, 1, cols),
            indexing='ij'
        )
        # Edge position varies by ±2% across detector (strain)
        position_shift = 0.02 * x_coords
    else:
        position_shift = np.zeros((rows, cols))

    # Generate data pixel by pixel
    for i in range(rows):
        for j in range(cols):
            # Apply edge position shift (simulates strain/stress)
            shifted_wavelength = wavelength * (1 + position_shift[i, j])
            transmission = generate_realistic_bragg_edges(shifted_wavelength, material)

            # Sample intensity: flux * transmission
            sample_intensity = flux * transmission

            # Open beam intensity: just flux
            open_beam_intensity = flux.copy()

            # Scale to typical count levels
            mean_counts = 5000
            sample_intensity = sample_intensity * mean_counts
            open_beam_intensity = open_beam_intensity * mean_counts

            # Add Poisson noise (counting statistics)
            if noise_level > 0:
                sample_intensity = np.random.poisson(sample_intensity)
                open_beam_intensity = np.random.poisson(open_beam_intensity)

                # Convert back to intensity
                sample_intensity = sample_intensity.astype(float)
                open_beam_intensity = open_beam_intensity.astype(float)

                # Add Gaussian readout noise
                sample_intensity += np.random.normal(0, noise_level * mean_counts, nbins)
                open_beam_intensity += np.random.normal(0, noise_level * mean_counts, nbins)

            # Ensure non-negative
            sample_intensity = np.maximum(sample_intensity, 0)
            open_beam_intensity = np.maximum(open_beam_intensity, 1)  # Avoid division by zero

            I[i, j, :] = sample_intensity
            I0[i, j, :] = open_beam_intensity

    return I, I0, wavelength, tof


def generate_realistic_chopper_modulated_data(
    shape: Tuple[int, int, int] = (50, 50, 800),
    nrep: int = 8,
    chopper_id: str = "POLDI",
    wavelength_range: Tuple[float, float] = (1.0, 8.0),
    material: str = 'Fe',
    flight_path: float = 10.0,
    noise_level: float = 0.03,
    add_spatial_variation: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Generate realistic chopper-modulated POLDI data.

    This simulates the actual measurement process:
    1. Generate true transmission spectrum
    2. Convolve with chopper response (time delays)
    3. Add repetitions and readout gaps
    4. Add noise

    Parameters
    ----------
    shape : tuple
        Data shape (rows, cols, time_bins)
    nrep : int
        Number of chopper repetitions
    chopper_id : str
        Chopper configuration
    wavelength_range : tuple
        (min, max) wavelength in Angstroms
    material : str
        Material for Bragg edges
    flight_path : float
        Flight path in meters
    noise_level : float
        Relative noise level
    add_spatial_variation : bool
        Add spatial variations

    Returns
    -------
    I_mod : np.ndarray
        Chopper-modulated sample data
    I0_mod : np.ndarray
        Chopper-modulated open beam data
    wavelength : np.ndarray
        Wavelength array in Angstroms
    tof : np.ndarray
        Time-of-flight array in microseconds
    tmax : float
        Maximum time-of-flight
    """
    from ..reduction.time_delays import (
        fobi_poldi_time_delays,
        fobi_4x10_time_delays,
        fobi_5x8_time_delays,
        fobi_3x14_time_delays,
    )

    rows, cols, nbins = shape

    # Generate true (unconvoluted) data at lower resolution
    nbins_true = nbins // nrep

    I_true, I0_true, wavelength_true, tof_true = generate_realistic_poldi_data(
        shape=(rows, cols, nbins_true),
        wavelength_range=wavelength_range,
        material=material,
        flight_path=flight_path,
        noise_level=0,  # Add noise after convolution
        add_spatial_variation=add_spatial_variation,
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

    D = chopper_functions[chopper_id](tof_true)

    # Initialize modulated data
    I_mod = np.zeros(shape)
    I0_mod = np.zeros(shape)

    # Convolve each pixel with chopper response
    print("Generating chopper-modulated data...")
    for i in range(rows):
        if i % 10 == 0:
            print(f"  Processing row {i+1}/{rows}")
        for j in range(cols):
            # Convolve with chopper response
            signal_conv = np.convolve(I_true[i, j, :], D, mode='same')
            open_conv = np.convolve(I0_true[i, j, :], D, mode='same')

            # Replicate to simulate multiple repetitions
            signal_rep = np.tile(signal_conv, nrep)
            open_rep = np.tile(open_conv, nrep)

            # Add readout gaps (simulate dead time between repetitions)
            replen = len(signal_conv)
            for rep in range(nrep):
                start = rep * replen
                end = (rep + 1) * replen
                # Last 3% of each repetition is dead time
                gap_start = end - int(0.03 * replen)
                signal_rep[gap_start:end] = 0
                open_rep[gap_start:end] = 0

            # Trim to desired length
            I_mod[i, j, :] = signal_rep[:nbins]
            I0_mod[i, j, :] = open_rep[:nbins]

    # Add noise
    if noise_level > 0:
        mean_counts = 5000

        for i in range(rows):
            for j in range(cols):
                # Poisson noise
                counts = np.random.poisson(np.maximum(I_mod[i, j, :], 0))
                I_mod[i, j, :] = counts.astype(float)

                counts0 = np.random.poisson(np.maximum(I0_mod[i, j, :], 0))
                I0_mod[i, j, :] = counts0.astype(float)

                # Gaussian readout noise
                I_mod[i, j, :] += np.random.normal(0, noise_level * mean_counts, nbins)
                I0_mod[i, j, :] += np.random.normal(0, noise_level * mean_counts, nbins)

                # Ensure non-negative
                I_mod[i, j, :] = np.maximum(I_mod[i, j, :], 0)
                I0_mod[i, j, :] = np.maximum(I0_mod[i, j, :], 1)

    # Create full time and wavelength arrays
    tmax = tof_true[-1] * nrep
    tof = np.linspace(tof_true[0], tmax, nbins)
    wavelength = tof_to_wavelength(tof, L=flight_path)

    return I_mod, I0_mod, wavelength, tof, tmax


# Keep old functions for backwards compatibility
def generate_test_data(
    shape: Tuple[int, int, int] = (50, 50, 500),
    edge_position: float = 250.0,
    edge_width: float = 10.0,
    edge_height: float = 0.5,
    noise_level: float = 0.02,
    add_spatial_variation: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Legacy function - generates realistic POLDI data.

    NOTE: This now calls generate_realistic_poldi_data with appropriate parameters.
    """
    # Convert old parameters to realistic wavelength-based generation
    I, I0, wavelength, tof = generate_realistic_poldi_data(
        shape=shape,
        wavelength_range=(1.0, 8.0),
        material='Fe',
        flight_path=10.0,
        noise_level=noise_level,
        add_spatial_variation=add_spatial_variation,
    )

    return I, I0, tof


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
    Legacy function - generates realistic chopper-modulated POLDI data.

    NOTE: This now calls generate_realistic_chopper_modulated_data.
    """
    I_mod, I0_mod, wavelength, tof, tmax = generate_realistic_chopper_modulated_data(
        shape=shape,
        nrep=nrep,
        chopper_id=chopper_id,
        wavelength_range=(1.0, 8.0),
        material='Fe',
        flight_path=10.0,
        noise_level=noise_level,
        add_spatial_variation=True,
    )

    return I_mod, I0_mod, tof, tmax
