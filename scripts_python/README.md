# FOBI Python Scripts

This directory contains example scripts demonstrating how to use the FOBI Python package.

## Scripts

### `fobi_reduction_example.py`

Complete FOBI workflow demonstration including:
- Data loading (or synthetic data generation)
- Spatial filtering
- FOBI Wiener deconvolution
- Bragg edge fitting
- Visualization of results

**Usage:**
```bash
python fobi_reduction_example.py
```

## Adapting for Your Data

To use these scripts with your own neutron imaging data:

1. **Load your data** - Replace the synthetic data generation with:
   ```python
   I0 = np.load('your_open_beam.npy')  # Open beam
   I = np.load('your_sample.npy')       # Sample
   t = np.load('your_tof.npy')          # Time-of-flight array
   ```

2. **Set parameters** - Adjust FOBI parameters for your instrument:
   ```python
   tmax = 0.03          # Maximum TOF (s) for POLDI
   nrep = 4             # Number of chopper repetitions
   chopper_id = 'POLDI' # Chopper configuration
   c = 0.1              # Wiener constant
   roll = 165           # Shift to re-center spectrum
   ```

3. **Adjust edge fitting** - Set appropriate edge parameters:
   ```python
   spectrum_range = [0, 10]    # Fitting window
   est_p = 4.8e-3              # Estimated edge position
   est_w = 4.4e-5              # Estimated edge width
   est_h = 3e-3                # Estimated edge height
   ```

## Requirements

All scripts require the FOBI package to be installed:
```bash
pip install -e ..
```

Or install dependencies directly:
```bash
pip install -r ../requirements.txt
```
