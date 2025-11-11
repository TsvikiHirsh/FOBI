# Using Real Iron Powder Data

## Overview

The iron powder data in `notebooks/` is **direct time-of-flight (TOF) data** from a pulsed neutron source, **not chopper-modulated data**. This is an important distinction that affects how you analyze it.

## Data Type: Direct TOF vs Chopper-Modulated

### Direct TOF Data (Your Iron Powder Data)
- **Source**: Pulsed neutron source (e.g., ISIS, SNS, J-PARC)
- **Time bins**: Independent measurements, each bin = one TOF value
- **Transmission calculation**: Simple ratio `T = Sample / OpenBeam`
- **FOBI needed?**: **NO** - Direct transmission is sufficient
- **Your data**: `iron_powder.csv`, `openbeam.csv`

### Chopper-Modulated Data (FOBI Required)
- **Source**: Continuous source with chopper (e.g., POLDI at PSI)
- **Time bins**: Overlapping chopper windows
- **Transmission calculation**: Requires Wiener deconvolution (FOBI)
- **FOBI needed?**: **YES** - Must deconvolve chopper response
- **Example**: Synthetic data in `tutorial.ipynb`

## How to Analyze Your Iron Powder Data

### Method 1: Direct TOF Analysis (Recommended for Your Data)

Use the notebook: **`iron_powder_direct_tof.ipynb`**

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
signal_df = pd.read_csv('notebooks/iron_powder.csv')
openbeam_df = pd.read_csv('notebooks/openbeam.csv')

# Calculate wavelength
time_step = 10  # µs per stack
L = 9  # meters
time = signal_df['stack'] * time_step
wavelength = 3.956 * (time / 1000) / L

# Calculate transmission (no FOBI needed!)
transmission = signal_df['counts'] / openbeam_df['counts']

# Plot
plt.plot(wavelength, transmission)
plt.xlabel('Wavelength (Å)')
plt.ylabel('Transmission')
plt.title('Iron Powder - Direct TOF')
plt.show()
```

### Method 2: Using FOBI API (Educational/Demonstration)

While FOBI isn't needed for this data, you can still use the API for demonstration:

```python
import fobi

# Load data (filtered to 1-10 Å)
result = (fobi.Workflow
    .load("notebooks/iron_powder_filtered.csv",
          "notebooks/openbeam_filtered.csv", L=9)
    .interpolate(tmax=20470, nrep=1)  # nrep=1 for direct TOF
    .convolve(chopper="POLDI", noise_level=0.1)  # Just for demonstration
    .reconstruct())

# Note: Results won't match direct transmission exactly
# because FOBI is designed for chopper-modulated data
```

## Data Files

### Original Data
- **`iron_powder.csv`**: 2400 stacks, 10 µs/stack, 0.004-10.549 Å
- **`openbeam.csv`**: Corresponding open beam reference
- **Format**: Columns: `stack`, `counts`, `err`

### Pre-processed Data
- **`iron_powder_filtered.csv`**: Filtered to 1-10 Å range
- **`openbeam_filtered.csv`**: Corresponding open beam
- **Format**: Columns: `time`, `signal`

### Analysis Results
- **`iron_powder_analysis.csv`**: Full analysis results
- **`iron_powder_1to10A.csv`**: Filtered results (1-10 Å)

## Expected Results

### Bragg Edges (BCC Iron)
Your transmission spectrum should show three clear Bragg edges:

| Edge | hkl | Wavelength (Å) | Description |
|------|-----|----------------|-------------|
| 1 | (110) | 2.027 | First edge, strongest |
| 2 | (200) | 2.866 | Second edge |
| 3 | (211) | 4.050 | Third edge |

### Typical Values
- **Transmission range**: 0.02 - 0.6
- **Mean transmission**: ~0.12
- **Best viewing range**: 1.5 - 5.0 Å (contains all edges)

## Streamlit App Usage

The Streamlit app now includes your real data:

```bash
streamlit run streamlit_app_1d.py
```

**Steps**:
1. Select **"Real Iron Powder Example"** from the sidebar
2. Set wavelength range (default: 1-10 Å)
3. Click **"Load Real Data (Direct TOF)"**
4. View the direct transmission (Sample/OpenBeam)
5. Optionally compare with FOBI reconstruction (educational)

**Note**: The app will show you both:
- **Direct transmission**: Simple ratio (correct for this data)
- **FOBI reconstruction**: Just for demonstration purposes

## Notebooks

### For Your Real Data
- **`iron_powder_direct_tof.ipynb`** ✅ **USE THIS**
  - Direct TOF analysis
  - Simple transmission calculation
  - Bragg edge identification
  - Smoothing and visualization

### For Learning FOBI
- **`tutorial.ipynb`** ✅ **Learn FOBI here**
  - Synthetic chopper-modulated data
  - Full FOBI workflow
  - Parameter exploration
  - Method chaining examples

### Comparison (Educational)
- **`iron_powder_example.ipynb`**
  - Shows how FOBI would work (if data was chopper-modulated)
  - Good for understanding the difference
  - Not the correct method for this specific data

## Quick Reference

### When to Use FOBI
✅ Chopper-modulated measurements
✅ POLDI, BOA beamlines
✅ Overlapping time windows
✅ Multiple chopper repetitions

### When NOT to Use FOBI (Direct TOF Instead)
✅ Pulsed neutron sources (ISIS, SNS, J-PARC)
✅ Independent time bins
✅ Your iron powder data
✅ Most TOF measurements from pulsed sources

## Summary

**For your iron powder data**:
1. ✅ Use **direct TOF analysis**: `T = Sample / OpenBeam`
2. ✅ Run **`iron_powder_direct_tof.ipynb`** notebook
3. ✅ Expected to see **3 Bragg edges** at 2.027, 2.866, 4.050 Å
4. ❌ **Don't use FOBI** - it's designed for chopper-modulated data

**To learn FOBI**:
1. ✅ Use **`tutorial.ipynb`** with synthetic chopper data
2. ✅ Understand method chaining API
3. ✅ Explore parameters and filters
4. ✅ Apply to real chopper-modulated measurements when available

Your iron powder data is excellent for demonstrating direct TOF analysis and Bragg edge identification!
