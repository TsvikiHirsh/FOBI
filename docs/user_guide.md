# FOBI User Guide

This guide provides detailed instructions for using the FOBI package for neutron time-of-flight imaging analysis.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Basic Concepts](#basic-concepts)
4. [Step-by-Step Tutorial](#step-by-step-tutorial)
5. [Advanced Usage](#advanced-usage)
6. [Troubleshooting](#troubleshooting)

## Introduction

FOBI (Full-spectrum Bragg edge transmission imaging) is a parametric reconstruction technique for neutron time-of-flight imaging. This guide will walk you through:

- Loading and preparing your data
- Running FOBI Wiener deconvolution
- Fitting Bragg edges
- Interpreting results

## Installation

### Requirements

- Python 3.8 or higher
- NumPy, SciPy, Matplotlib
- Optional: Streamlit for interactive app

### Install from source

```bash
git clone https://github.com/your-org/fobi.git
cd fobi
pip install -e .
```

### Install with optional dependencies

```bash
# For development (includes pytest)
pip install -e ".[dev]"

# For FITS file support
pip install -e ".[fits]"

# For interactive visualization
pip install -e ".[viz]"

# Install everything
pip install -e ".[dev,fits,viz]"
```

## Basic Concepts

### What is FOBI?

FOBI uses Wiener deconvolution to reconstruct neutron transmission spectra from chopper-modulated measurements. The key steps are:

1. **Data preparation**: Load sample and open beam data
2. **Interpolation**: Fill readout gaps by averaging chopper repetitions
3. **Deconvolution**: Apply Wiener filter to remove chopper modulation
4. **Edge fitting**: Fit Gaussian models to Bragg edges

### Key Parameters

#### Wiener Deconvolution Parameters

- **`tmax`**: Maximum time-of-flight (seconds)
- **`nrep`**: Number of chopper repetitions
- **`chopper_id`**: Chopper configuration ('POLDI', '4x10', '5x8', '3x14')
- **`c`**: Wiener regularization constant (0.01 to 1.0)
  - Lower values: Less smoothing, more noise
  - Higher values: More smoothing, less resolution
- **`roll`**: Circular shift to re-center spectrum (optional)

#### Edge Fitting Parameters

- **`spectrum_range`**: (min, max) wavelength/TOF window for fitting
- **`est_p`**: Initial guess for edge position
- **`est_w`**: Initial guess for edge width (standard deviation)
- **`est_h`**: Initial guess for edge height (negative for transmission drop)
- **`BC_p`**: (lower, upper) bounds for position
- **`BC_w`**: (lower, upper) bounds for width
- **`BC_h`**: (lower, upper) bounds for height

## Step-by-Step Tutorial

### Step 1: Import Required Modules

```python
import numpy as np
import matplotlib.pyplot as plt

from fobi.reduction import fobi_wiener_2d
from fobi.edge_fitting import edge_fit_gaussian, edge_fit_gaussian_2d
from fobi.utils import plot_transmission_spectrum, plot_edge_maps
```

### Step 2: Load Your Data

#### Option A: Load Real Data

```python
# Load from NumPy files
I = np.load('sample_transmission.npy')    # Sample data (rows, cols, time_bins)
I0 = np.load('open_beam.npy')             # Open beam (rows, cols, time_bins)
t = np.load('tof_spectrum.npy')           # Time-of-flight array (time_bins,)

# Or load from FITS files (requires astropy)
from astropy.io import fits
I = fits.getdata('sample.fits')
I0 = fits.getdata('open_beam.fits')
```

#### Option B: Generate Synthetic Test Data

```python
from fobi.utils import generate_test_data

I, I0, t = generate_test_data(
    shape=(50, 50, 800),      # (rows, cols, time_bins)
    edge_position=400,        # Edge position in bins
    edge_width=20,            # Edge width in bins
    edge_height=0.5,          # Transmission drop (0-1)
    noise_level=0.03,         # Relative noise level
    add_spatial_variation=True
)

print(f"Data shape: {I.shape}")
print(f"Time array length: {len(t)}")
```

### Step 3: Apply Spatial Filtering (Optional but Recommended)

Spatial filtering improves statistics by averaging neighboring pixels:

```python
from scipy.ndimage import uniform_filter

# Moving average filter
kernel_size = (5, 5)  # Spatial kernel size in pixels

I_filtered = np.zeros_like(I)
I0_filtered = np.zeros_like(I0)

for i in range(I.shape[2]):
    I_filtered[:, :, i] = uniform_filter(I[:, :, i], size=kernel_size)
    I0_filtered[:, :, i] = uniform_filter(I0[:, :, i], size=kernel_size)

print("Filtering complete!")
```

### Step 4: FOBI Wiener Deconvolution

#### Single Pixel Test

Before processing the entire dataset, test on a single pixel:

```python
from fobi.reduction import wiener_deconvolution, interpolate_noreadoutgaps
from fobi.reduction.time_delays import fobi_poldi_time_delays

# Extract single pixel
row, col = 25, 25
y = I_filtered[row, col, :]
y0 = I0_filtered[row, col, :]

# Parameters
tmax = t[-1]
nrep = 8
chopper_id = 'POLDI'
c = 0.1

# Interpolate readout gaps
y_merged, t_merged = interpolate_noreadoutgaps(y, t, tmax, nrep, plot_flag=True)
y0_merged, _ = interpolate_noreadoutgaps(y0, t, tmax, nrep, plot_flag=False)

# Get chopper response
D = fobi_poldi_time_delays(t_merged)

# Deconvolve
nslits = 8
y_rec = nslits * nrep * wiener_deconvolution(y_merged, D, c)
y0_rec = nslits * nrep * wiener_deconvolution(y0_merged, D, c)

# Compute transmission
T_rec = y_rec / y0_rec

# Plot result
plt.figure(figsize=(10, 5))
plt.plot(t_merged, T_rec)
plt.xlabel('Time-of-Flight (µs)')
plt.ylabel('Transmission')
plt.title(f'Reconstructed Transmission - Pixel ({row}, {col})')
plt.grid(True)
plt.show()
```

#### Full 2D Reconstruction

Process the entire 2D image:

```python
print("Running FOBI 2D reconstruction...")

T, y_rec, y0_rec, t_merged = fobi_wiener_2d(
    I_filtered, I0_filtered, t,
    tmax=t[-1],
    nrep=8,
    chopper_id='POLDI',
    c=0.1,
    flag_smooth=0,  # Additional smoothing (0 = none)
    roll=0          # Circular shift
)

print(f"Reconstruction complete!")
print(f"Output shape: {T.shape}")
print(f"Reconstructed spectrum length: {len(t_merged)}")
```

### Step 5: Visualize Transmission Spectra

```python
# Plot transmission for a single pixel
row, col = 25, 25

fig = plot_transmission_spectrum(
    t_merged,
    T[row, col, :],
    title=f"Pixel ({row}, {col})"
)
plt.show()

# Or create custom plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Time-averaged images
axes[0, 0].imshow(np.mean(I, axis=2), cmap='viridis')
axes[0, 0].set_title('Sample (time-averaged)')

axes[0, 1].imshow(np.mean(I0, axis=2), cmap='viridis')
axes[0, 1].set_title('Open Beam (time-averaged)')

# Reconstructed transmission
axes[1, 0].imshow(np.mean(T, axis=2), cmap='plasma')
axes[1, 0].set_title('Transmission (time-averaged)')

# Single spectrum
axes[1, 1].plot(t_merged, T[row, col, :])
axes[1, 1].set_xlabel('Time-of-Flight (µs)')
axes[1, 1].set_ylabel('Transmission')
axes[1, 1].set_title(f'Pixel ({row}, {col})')
axes[1, 1].grid(True)

plt.tight_layout()
plt.show()
```

### Step 6: Fit Bragg Edges

#### Single Pixel Test

First, test edge fitting on a single pixel to determine appropriate parameters:

```python
# Select pixel and spectrum range
row, col = 25, 25
spectrum_range = (t_merged[0], t_merged[-1])

# Initial guesses (adjust based on your data)
est_p = t_merged[len(t_merged)//2]  # Middle of spectrum
est_w = (t_merged[1] - t_merged[0]) * 5  # ~5 bins wide
est_h = -0.05  # Negative for transmission drop

# Boundary conditions
BC_p = (t_merged[0], t_merged[-1])
BC_w = (0.001, 100)
BC_h = (-1, 0)

# Fit with plotting
pos, wid, h = edge_fit_gaussian(
    T[row, col, :],
    t_merged,
    spectrum_range,
    est_p, est_w, est_h,
    BC_p, BC_w, BC_h,
    smooth_span=1,
    plot_result=True
)

print(f"Fitted parameters:")
print(f"  Position: {pos:.4f}")
print(f"  Width: {wid:.4f}")
print(f"  Height: {h:.4f}")

plt.show()
```

#### Full 2D Edge Fitting

Once parameters are optimized, fit all pixels:

```python
print("Fitting edges for all pixels...")

edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
    T,
    t_merged,
    spectrum_range,
    est_p, est_w, est_h,
    BC_p, BC_w, BC_h
)

print("Edge fitting complete!")

# Calculate statistics
print(f"\nEdge Position:")
print(f"  Mean: {np.nanmean(edge_p):.4f}")
print(f"  Std:  {np.nanstd(edge_p):.4f}")

print(f"\nEdge Width:")
print(f"  Mean: {np.nanmean(edge_w):.4f}")
print(f"  Std:  {np.nanstd(edge_w):.4f}")

print(f"\nEdge Height:")
print(f"  Mean: {np.nanmean(edge_h):.4f}")
print(f"  Std:  {np.nanstd(edge_h):.4f}")
```

### Step 7: Visualize Edge Maps

```python
# Create edge parameter maps
fig = plot_edge_maps(
    edge_p, edge_w, edge_h,
    titles=("Edge Position", "Edge Width (FWHM)", "Edge Height"),
    cmap='viridis'
)

plt.savefig('edge_maps.png', dpi=300, bbox_inches='tight')
plt.show()
```

## Advanced Usage

### Custom Chopper Configuration

If you have a custom chopper configuration:

```python
def custom_chopper_delays(time):
    """Define your custom chopper response."""
    Nt = len(time)

    # Define slit angles (degrees)
    angles = np.array([0, 10, 20, 30, 40, 50])

    # Convert to relative positions
    angles = angles / 90  # Normalize to 0-1
    shifts = Nt * angles

    # Create impulse response
    D = np.zeros(Nt)
    for shift in shifts:
        idx = int(shift)
        frac = shift - idx
        if idx < Nt:
            D[idx] += (1 - frac)
        if idx + 1 < Nt:
            D[idx + 1] += frac

    return D
```

### Multiple Edge Fitting

For materials with multiple Bragg edges:

```python
# Define multiple edge regions
edge_ranges = [
    (3.0, 4.0),   # First edge
    (5.0, 6.0),   # Second edge
    (7.0, 8.0),   # Third edge
]

# Fit each edge separately
results = []

for i, (range_min, range_max) in enumerate(edge_ranges):
    print(f"Fitting edge {i+1}...")

    edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
        T,
        t_merged,
        (range_min, range_max),
        est_p=(range_min + range_max) / 2,
        est_w=0.2,
        est_h=-0.05,
        BC_p=(range_min, range_max),
        BC_w=(0.01, 1),
        BC_h=(-1, 0)
    )

    results.append((edge_p, edge_w, edge_h))

# Visualize all edges
fig, axes = plt.subplots(len(results), 3, figsize=(15, 5*len(results)))

for i, (edge_p, edge_w, edge_h) in enumerate(results):
    axes[i, 0].imshow(edge_p, cmap='viridis')
    axes[i, 0].set_title(f'Edge {i+1} - Position')

    axes[i, 1].imshow(edge_w, cmap='viridis')
    axes[i, 1].set_title(f'Edge {i+1} - Width')

    axes[i, 2].imshow(edge_h, cmap='viridis')
    axes[i, 2].set_title(f'Edge {i+1} - Height')

plt.tight_layout()
plt.show()
```

## Troubleshooting

### Common Issues

#### 1. Poor reconstruction quality

**Problem**: Reconstructed spectrum is noisy or has artifacts

**Solutions**:
- Increase Wiener constant `c` (try 0.5 or 1.0)
- Apply spatial filtering with larger kernel
- Use `flag_smooth` parameter for temporal smoothing
- Check that `nrep` is correct for your data

#### 2. Edge fitting fails

**Problem**: Fitted parameters are NaN or unrealistic

**Solutions**:
- Adjust boundary conditions `BC_p`, `BC_w`, `BC_h`
- Check that `spectrum_range` contains the edge
- Improve initial guesses `est_p`, `est_w`, `est_h`
- Increase `smooth_span` to reduce noise
- Ensure sufficient data points in fitting range

#### 3. Incorrect edge positions

**Problem**: Fitted edge positions don't match expected values

**Solutions**:
- Adjust `roll` parameter to center spectrum
- Check time-of-flight calibration
- Verify chopper configuration (`chopper_id`)
- Check that `nrep` matches your measurement

#### 4. Memory issues with large datasets

**Problem**: Out of memory errors

**Solutions**:
- Process data in chunks
- Reduce spatial resolution (bin pixels)
- Use smaller time binning
- Process on machine with more RAM

### Getting Help

If you encounter issues:

1. Check the [API Reference](api_reference.md)
2. Review example scripts in `scripts_python/`
3. Try the Streamlit app for interactive parameter exploration
4. Open an issue on GitHub

## Next Steps

- Explore the [API Reference](api_reference.md) for detailed function documentation
- Run the example scripts in `scripts_python/`
- Try the interactive Streamlit app
- Read the [original publication](https://www.nature.com/articles/s41598-020-71705-4)
