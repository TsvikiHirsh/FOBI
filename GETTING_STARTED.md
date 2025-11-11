# Getting Started with FOBI

Welcome to the refactored FOBI package! This guide will help you get started quickly.

## Quick Start (5 minutes)

### 1. Install the Package

```bash
cd /work/nuclear/FOBI

# Install main package
pip install -e .

# Install with development tools (recommended)
pip install -e ".[dev]"
```

### 2. Run Your First Reconstruction

```python
import fobi
import numpy as np

# Generate synthetic data
from fobi.utils import generate_test_data
I, I0, t = generate_test_data(shape=(1, 1, 800), noise_level=0.02)

# Extract 1D arrays
signal = I[0, 0, :]
openbeam = I0[0, 0, :]

# Reconstruct with method chaining
result = (fobi.Workflow
    .load_arrays(signal=signal, openbeam=openbeam, time=t, L=9)
    .interpolate(tmax=t[-1], nrep=8)
    .convolve(chopper="POLDI", noise_level=0.1)
    .reconstruct())

# Plot
result.plot(what="transmission", x_axis="wavelength")
```

**That's it!** You just reconstructed a neutron transmission spectrum.

## Interactive Tutorial (30 minutes)

### Option 1: Jupyter Notebook (Recommended)

```bash
# Install Jupyter (if not already installed)
pip install jupyter

# Launch notebook
jupyter notebook notebooks/tutorial.ipynb
```

The tutorial covers:
- Data generation
- Basic reconstruction
- Parameter exploration
- Iron powder example
- Saving/loading results

### Option 2: Streamlit Web App

```bash
# Launch interactive app
streamlit run streamlit_app_1d.py
```

Features:
- Generate synthetic data
- Upload your CSV files
- Adjust parameters in real-time
- Compare with ground truth
- Export results

## Example Use Cases

### Example 1: Load from CSV Files

```python
import fobi

# Your data files
result = (fobi.Workflow
    .load(
        signal="path/to/sample.csv",
        openbeam="path/to/openbeam.csv",
        L=9  # flight path in meters
    )
    .interpolate(tmax=10000, nrep=8)
    .convolve(chopper="POLDI", noise_level=0.1)
    .reconstruct())

# Save results
result.save("reconstruction.csv")
```

### Example 2: Explore Parameters

```python
import fobi
import matplotlib.pyplot as plt

# Load data once
workflow = fobi.Workflow.load("sample.csv", "openbeam.csv", L=9)

# Try different noise levels
noise_levels = [0.01, 0.1, 0.5, 1.0]

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

for ax, noise in zip(axes.flat, noise_levels):
    result = (workflow
        .interpolate(tmax=10000, nrep=8)
        .convolve(chopper="POLDI", noise_level=noise)
        .reconstruct())

    ax.plot(result.wavelength, result.transmission)
    ax.set_title(f'Noise level = {noise}')
    ax.set_xlabel('Wavelength (Å)')
    ax.set_ylabel('Transmission')

plt.tight_layout()
plt.show()
```

### Example 3: Batch Processing

```python
import fobi
from pathlib import Path

data_dir = Path("data/measurements/")
output_dir = Path("results/")
output_dir.mkdir(exist_ok=True)

# Process all samples
for sample_file in data_dir.glob("sample_*.csv"):
    print(f"Processing {sample_file.name}...")

    result = (fobi.Workflow
        .load(signal=sample_file, openbeam="data/openbeam.csv", L=9)
        .interpolate(tmax=10000, nrep=8)
        .convolve(chopper="POLDI", noise_level=0.1)
        .reconstruct())

    # Save with same name
    output_file = output_dir / f"{sample_file.stem}_reconstructed.csv"
    result.save(output_file)

    print(f"  → Saved to {output_file}")
```

## Understanding the Workflow

The reconstruction pipeline has 4 steps:

### Step 1: Load Data

```python
workflow = fobi.Workflow.load(
    signal="sample.csv",      # Sample measurement
    openbeam="openbeam.csv",  # Open beam (normalization)
    L=9                        # Flight path length (optional)
)
```

**What it does**: Loads your time-of-flight data

### Step 2: Interpolate

```python
workflow = workflow.interpolate(
    tmax=10000,  # Maximum time-of-flight (µs)
    nrep=8       # Number of chopper repetitions
)
```

**What it does**:
- Fills readout gaps
- Merges multiple chopper repetitions
- Creates uniform time grid

### Step 3: Set up Chopper Response

```python
workflow = workflow.convolve(
    chopper="POLDI",           # Chopper configuration
    noise_level=0.1,           # Wiener regularization (higher = smoother)
    filter_type="LowPassGa"    # Optional frequency filter
)
```

**What it does**:
- Calculates instrument response function
- Sets reconstruction parameters

### Step 4: Reconstruct

```python
result = workflow.reconstruct(
    roll=0  # Optional circular shift
)
```

**What it does**:
- Performs Wiener deconvolution
- Calculates transmission spectrum
- Converts to wavelength (if L provided)

## Key Concepts

### Chopper Configurations

| Name | Slits | Use Case |
|------|-------|----------|
| POLDI | 8 | PSI standard, good all-around |
| 4x10 | 10 | Higher resolution |
| 5x8 | 8 | Custom setup |
| 3x14 | 14 | More slits, better statistics |

### Noise Level (Regularization)

- **Low (0.01)**: Sharp features, more noise
- **Medium (0.1)**: Balanced (recommended)
- **High (1.0)**: Very smooth, may lose detail

**Rule of thumb**: Start with 0.1, increase if too noisy, decrease if too smooth

### Frequency Filters

- `"none"`: No filtering (default)
- `"LowPass"`: Simple cutoff
- `"LowPassBu"`: Butterworth (smooth rolloff)
- `"LowPassGa"`: Gaussian (very smooth)

**When to use**: Add filter if you have high-frequency noise

## Common Issues

### Issue 1: "No data loaded"

```python
# ❌ Wrong - forgot to load data
result = fobi.Workflow().interpolate(tmax=10000, nrep=8)

# ✅ Correct - load data first
result = (fobi.Workflow
    .load("sample.csv", "openbeam.csv", L=9)
    .interpolate(tmax=10000, nrep=8)
    ...)
```

### Issue 2: "Wavelength not available"

```python
# ❌ Wrong - no L provided
result = fobi.Workflow.load("sample.csv", "openbeam.csv")  # No L
result.plot(x_axis="wavelength")  # ERROR!

# ✅ Correct - provide L
result = fobi.Workflow.load("sample.csv", "openbeam.csv", L=9)
result.plot(x_axis="wavelength")  # Works!
```

### Issue 3: CSV Column Names

```python
# If your CSV has different column names
result = fobi.Workflow.load(
    signal="sample.csv",
    openbeam="openbeam.csv",
    L=9,
    time_col="tof",           # Instead of "time"
    signal_col="intensity"    # Instead of "signal"
)
```

## Next Steps

### Learn More

1. **Tutorial Notebook**: `jupyter notebook notebooks/tutorial.ipynb`
2. **Migration Guide**: See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
3. **Full Documentation**: See [README_NEW.md](README_NEW.md)

### Run Tests

```bash
# Test the new API
pytest tests/test_workflow.py -v

# Compare with MATLAB (requires Octave)
pip install oct2py
sudo apt-get install octave
pytest tests/test_matlab_comparison.py -v
```

### Explore Legacy Code

If you need 2D imaging or want to understand the original implementation:

1. **Legacy README**: [.legacy/README.md](.legacy/README.md)
2. **Original MATLAB**: [.legacy/matlab/](.legacy/matlab/)
3. **Original Python**: [.legacy/python/](.legacy/python/)

## Getting Help

### Documentation

- **Tutorial**: [notebooks/tutorial.ipynb](notebooks/tutorial.ipynb)
- **API Guide**: [README_NEW.md](README_NEW.md)
- **Migration**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **Summary**: [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)

### Examples

Run the Streamlit app to see interactive examples:

```bash
streamlit run streamlit_app_1d.py
```

### Support

- GitHub Issues: [Report bugs or request features]
- Documentation: Check the notebooks and README files
- Code Examples: See tutorial notebook

## Summary

**You've learned**:
- ✅ How to install FOBI
- ✅ Basic reconstruction workflow
- ✅ Loading data from CSV or arrays
- ✅ Parameter tuning
- ✅ Saving and plotting results

**Next steps**:
1. Try the tutorial notebook
2. Run the Streamlit app
3. Process your own data
4. Explore different parameters

**Remember**: The new API makes FOBI much easier to use. You went from ~25 lines of code to just 4 lines for a complete reconstruction!

Enjoy using FOBI! 🔬
