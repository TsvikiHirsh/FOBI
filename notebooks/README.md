# Notebooks

This directory contains tutorial notebooks and example data for FOBI.

## Notebooks

### [tutorial.ipynb](tutorial.ipynb)
Complete FOBI tutorial with synthetic chopper-modulated data. Demonstrates:
- Method chaining API
- Parameter exploration
- Different choppers and filters
- Synthetic iron powder with Bragg edges

### [iron_powder_example.ipynb](iron_powder_example.ipynb)
Analysis of real iron powder TOF data. **Note**: This data is direct TOF (not chopper-modulated), so it demonstrates direct transmission calculation rather than FOBI reconstruction.

## Data Files

### Real Measurement Data
- `iron_powder.csv` - Iron powder sample TOF data (2400 stacks, 10 µs/stack)
- `openbeam.csv` - Open beam reference (no sample)

**Note**: These are **direct time-of-flight measurements**, not chopper-modulated data.
- Each stack = 10 µs time bin
- Wavelength = 3.956 × (time_ms) / L(m)
- For direct TOF: transmission = signal / openbeam (no FOBI needed)

### Filtered Data (1-10 Å)
- `iron_powder_filtered.csv` - Filtered to 1-10 Å wavelength range
- `openbeam_filtered.csv` - Corresponding open beam

### Generated Files
- `sample_signal.csv` - Synthetic sample from tutorial
- `sample_openbeam.csv` - Synthetic open beam from tutorial
- `reconstruction_results.csv` - FOBI reconstruction output

## When to Use FOBI

**Use FOBI when**:
- Data is from a **chopper-modulated** neutron source
- Multiple time windows overlap (chopper repetitions)
- Need to deconvolve chopper response function
- Working with POLDI, BOA, or similar chopper instruments

**Use direct transmission when**:
- Data is from **pulsed source** (e.g., ISIS, SNS, J-PARC)
- Each time bin is independent (no chopper modulation)
- Direct TOF spectrum available
- Simply: transmission = sample / open_beam

## Example Usage

### Direct TOF Data (like iron_powder.csv)
```python
import pandas as pd

# Load data
signal_df = pd.read_csv('iron_powder.csv')
openbeam_df = pd.read_csv('openbeam.csv')

# Calculate transmission directly
time = signal_df['stack'] * 10  # µs
wavelength = 3.956 * (time / 1000) / 9  # Å
transmission = signal_df['counts'] / openbeam_df['counts']

# Plot
import matplotlib.pyplot as plt
plt.plot(wavelength, transmission)
plt.xlabel('Wavelength (Å)')
plt.ylabel('Transmission')
plt.show()
```

### Chopper-Modulated Data (use FOBI)
```python
import fobi

# For chopper-modulated data
result = (fobi.Workflow
    .load(signal="chopper_data.csv", openbeam="chopper_ob.csv", L=9)
    .interpolate(tmax=10000, nrep=8)  # Merge chopper repetitions
    .convolve(chopper="POLDI", noise_level=0.1)  # Deconvolve chopper response
    .reconstruct())  # Get transmission spectrum

result.plot(what="transmission", x_axis="wavelength")
```

## Iron Powder Bragg Edges

Expected for BCC iron:
- **Fe (110)**: 2.027 Å
- **Fe (200)**: 2.866 Å
- **Fe (211)**: 4.050 Å

These edges should be visible in both direct TOF and FOBI-reconstructed spectra.
