#!/usr/bin/env python3
"""
FOBI Reduction Example Script
==============================

This script demonstrates the complete FOBI workflow:
1. Load open beam and sample data
2. Apply spatial filtering
3. Perform FOBI Wiener deconvolution
4. Fit Bragg edges to extract material properties
5. Visualize results

Adapted from the original MATLAB script: scripts/02_FobiReduction.m
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter

# Import FOBI modules
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fobi.reduction import fobi_wiener_2d
from fobi.edge_fitting import edge_fit_gaussian, edge_fit_gaussian_2d
from fobi.utils import plot_transmission_spectrum, plot_edge_maps, generate_test_data


def moving_average_filter(data, kernel_size):
    """
    Apply moving average filter to 3D data.

    Parameters
    ----------
    data : np.ndarray
        Input data (rows, cols, time_bins)
    kernel_size : tuple
        Filter size (spatial_x, spatial_y)

    Returns
    -------
    filtered : np.ndarray
        Filtered data
    """
    filtered = np.zeros_like(data)

    # Apply 2D moving average in spatial dimensions
    for i in range(data.shape[2]):
        filtered[:, :, i] = uniform_filter(
            data[:, :, i],
            size=(kernel_size[0], kernel_size[1]),
            mode='constant'
        )

    return filtered


def main():
    """Main FOBI reduction workflow."""

    print("=" * 70)
    print("FOBI Reduction Example")
    print("=" * 70)

    # ========================================================================
    # Step 1: Load or generate test data
    # ========================================================================
    print("\n[1/5] Loading data...")

    # For this example, we'll generate synthetic test data
    # In practice, replace this with your actual data loading:
    # I0 = np.load('OB.npy')  # Open beam
    # I = np.load('Sample.npy')  # Sample
    # t = np.load('spectrum_tof.npy')  # Time-of-flight

    I, I0, t = generate_test_data(
        shape=(50, 50, 800),  # Small size for quick demo
        edge_position=400,
        edge_width=20,
        edge_height=0.5,
        noise_level=0.03,
    )

    print(f"   Data shape: {I.shape}")
    print(f"   Time bins: {len(t)}")

    # ========================================================================
    # Step 2: Apply spatial filtering (optional but recommended)
    # ========================================================================
    print("\n[2/5] Applying spatial filtering...")

    kernel = (5, 5)  # Moving average kernel size (pixels)
    I_filter = moving_average_filter(I, kernel)
    I0_filter = moving_average_filter(I0, kernel)

    # Visualize filtering effect
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].imshow(np.nanmean(I, axis=2), cmap='viridis')
    axes[0].set_title('Raw Data (time-averaged)')
    axes[0].axis('off')

    axes[1].imshow(np.nanmean(I_filter, axis=2), cmap='viridis')
    axes[1].set_title('Filtered Data (time-averaged)')
    axes[1].axis('off')

    plt.tight_layout()
    plt.savefig('filtering_comparison.png', dpi=150, bbox_inches='tight')
    print("   Saved: filtering_comparison.png")

    # ========================================================================
    # Step 3: FOBI Wiener Deconvolution
    # ========================================================================
    print("\n[3/5] Performing FOBI Wiener deconvolution...")

    # FOBI parameters
    tmax = t[-1]  # Maximum time-of-flight
    nrep = 8      # Number of chopper repetitions
    chopper_id = 'POLDI'  # Chopper configuration
    c = 0.1       # Wiener regularization constant
    flag_smooth = 0  # Smoothing (0 = none)
    roll = 0      # Circular shift to re-center spectrum

    print(f"   Chopper: {chopper_id}, Repetitions: {nrep}")
    print(f"   Wiener constant: {c}")

    T_fobi, y_rec, y0_rec, t_merged = fobi_wiener_2d(
        I_filter, I0_filter, t, tmax, nrep, chopper_id,
        c=c, flag_smooth=flag_smooth, roll=roll
    )

    print(f"   Reconstructed spectrum length: {len(t_merged)}")

    # Visualize transmission spectrum from a single pixel
    row, col = 25, 25
    fig = plot_transmission_spectrum(
        t_merged,
        T_fobi[row, col, :],
        title=f"Pixel ({row}, {col})",
    )
    plt.savefig('transmission_spectrum.png', dpi=150, bbox_inches='tight')
    print("   Saved: transmission_spectrum.png")

    # ========================================================================
    # Step 4: Edge Fitting
    # ========================================================================
    print("\n[4/5] Fitting Bragg edges...")

    # Edge fitting parameters
    spectrum_range = (t_merged[0], t_merged[-1])  # Full range

    # For synthetic data, we know the edge is around bin 50 (400/8 reps)
    est_p = t_merged[50]  # Estimated position
    est_w = (t_merged[1] - t_merged[0]) * 3  # Estimated width
    est_h = -0.05  # Estimated height (negative for edge drop in derivative)

    # Boundary conditions
    BC_p = (est_p * 0.8, est_p * 1.2)
    BC_w = (est_w * 0.1, est_w * 5)
    BC_h = (-0.5, 0)

    print(f"   Edge position estimate: {est_p:.3f}")
    print(f"   Fitting {T_fobi.shape[0]}x{T_fobi.shape[1]} pixels...")

    # Test single pixel fit first
    print("   Testing single pixel fit...")
    pos, wid, h = edge_fit_gaussian(
        T_fobi[row, col, :],
        t_merged,
        spectrum_range,
        est_p, est_w, est_h,
        BC_p, BC_w, BC_h,
        smooth_span=1,
        plot_result=True,
    )

    plt.savefig('edge_fit_single_pixel.png', dpi=150, bbox_inches='tight')
    print(f"   Fitted parameters: pos={pos:.3f}, width={wid:.3f}, height={h:.3f}")
    print("   Saved: edge_fit_single_pixel.png")

    # Fit all pixels (2D)
    print("   Fitting all pixels (this may take a minute)...")
    edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
        T_fobi,
        t_merged,
        spectrum_range,
        est_p, est_w, est_h,
        BC_p, BC_w, BC_h,
    )

    # ========================================================================
    # Step 5: Visualize Results
    # ========================================================================
    print("\n[5/5] Visualizing results...")

    fig = plot_edge_maps(
        edge_p, edge_w, edge_h,
        titles=("Edge Position", "Edge Width", "Edge Height"),
    )
    plt.savefig('edge_maps.png', dpi=150, bbox_inches='tight')
    print("   Saved: edge_maps.png")

    # Summary statistics
    print("\n" + "=" * 70)
    print("Results Summary")
    print("=" * 70)
    print(f"Edge Position: {np.nanmean(edge_p):.3f} ± {np.nanstd(edge_p):.3f}")
    print(f"Edge Width:    {np.nanmean(edge_w):.3f} ± {np.nanstd(edge_w):.3f}")
    print(f"Edge Height:   {np.nanmean(edge_h):.3f} ± {np.nanstd(edge_h):.3f}")
    print("=" * 70)

    print("\nFOBI reduction complete!")
    print("Generated files:")
    print("  - filtering_comparison.png")
    print("  - transmission_spectrum.png")
    print("  - edge_fit_single_pixel.png")
    print("  - edge_maps.png")


if __name__ == '__main__':
    main()
