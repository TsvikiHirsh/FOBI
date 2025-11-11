# FOBI: Full-spectrum Bragg Edge Transmission Imaging

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python package for reconstructing high-resolution neutron transmission spectra from chopper-modulated time-of-flight measurements using Wiener deconvolution.

## Features

- **Simple API**: Clean, object-oriented interface with method chaining
- **1D Focused**: Optimized for 1D spectrum reconstruction (the primary use case)
- **Multiple Choppers**: Support for POLDI, 4x10, 5x8, and 3x14 configurations
- **Flexible Filtering**: Frequency-domain filters for noise reduction
- **Interactive Tools**: Jupyter notebook tutorial and Streamlit web app
- **Well Tested**: Comprehensive test suite including MATLAB comparison tests
- **Legacy Support**: Original MATLAB and Python code preserved for reference

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/fobi.git
cd fobi

# Install the package
pip install -e .

# Install development dependencies (optional, for testing and notebooks)
pip install -e ".[dev]"
```

### Basic Usage

```python
import fobi

# Load data and reconstruct spectrum with method chaining
result = (fobi.Workflow
    .load(signal="sample.csv", openbeam="openbeam.csv", L=9)
    .interpolate(tmax=10000, nrep=8)
    .convolve(chopper="POLDI", noise_level=0.1)
    .reconstruct())

# Plot results
result.plot(what="transmission", x_axis="wavelength")

# Save results
result.save("output.csv")
```

That's it! The new API handles all the complexity for you.

## What is FOBI?

FOBI (Full-spectrum Bragg edge transmission) is a parametric reconstruction technique for neutron time-of-flight imaging. It uses **Wiener deconvolution** to reconstruct high-resolution transmission spectra from measurements that are:

- **Chopper-modulated**: Multiple time windows overlap in detector
- **Gap-affected**: Readout dead time creates missing data
- **Noisy**: Statistical noise from neutron counting

### How It Works

1. **Interpolation**: Fill readout gaps by averaging multiple repetitions
2. **Chopper Response**: Calculate instrument response function
3. **Wiener Deconvolution**: Frequency-domain reconstruction with noise regularization
4. **Wavelength Conversion**: Convert time-of-flight to wavelength

## Tutorial

See the [Jupyter notebook tutorial](notebooks/tutorial.ipynb) for a comprehensive guide with:

- Generating synthetic data
- Parameter exploration
- Comparing different settings
- Analyzing Bragg edges

Run the tutorial:

```bash
jupyter notebook notebooks/tutorial.ipynb
```

## Interactive Web App

Launch the Streamlit app for interactive exploration:

```bash
# 1D reconstruction (new API)
streamlit run streamlit_app_1d.py

# 2D imaging (legacy, for spatially-resolved data)
streamlit run streamlit_app.py
```

The 1D app provides:
- Synthetic data generation
- CSV upload/download
- Real-time parameter adjustment
- Comparison with true transmission
- Code examples

## API Documentation

### Loading Data

```python
import fobi

# From CSV files
workflow = fobi.Workflow.load(
    signal="sample.csv",
    openbeam="openbeam.csv",
    L=9  # flight path length in meters
)

# From numpy arrays
workflow = fobi.Workflow.load_arrays(
    signal=signal_array,
    openbeam=openbeam_array,
    time=time_array,
    L=9
)
```

### Processing Pipeline

```python
# Interpolate readout gaps
workflow = workflow.interpolate(
    tmax=10000,  # max time-of-flight (µs)
    nrep=8       # number of chopper repetitions
)

# Set up chopper response
workflow = workflow.convolve(
    chopper="POLDI",           # chopper configuration
    noise_level=0.1,           # Wiener regularization
    filter_type="LowPassGa"    # optional frequency filter
)

# Reconstruct spectrum
result = workflow.reconstruct(
    roll=0  # optional circular shift
)
```

### Result Object

```python
# Access reconstructed data
result.transmission   # Reconstructed transmission spectrum
result.signal         # Reconstructed sample signal
result.openbeam       # Reconstructed open beam
result.time           # Time-of-flight array
result.wavelength     # Wavelength array (if L provided)
result.metadata       # Reconstruction parameters

# Plot results
result.plot(what="transmission", x_axis="wavelength")
result.plot(what="all", x_axis="time")  # Plot everything

# Save results
result.save("output.csv", format="csv")
result.save("output.npy", format="npy")
```

## Chopper Configurations

| Chopper | Slits | Application |
|---------|-------|-------------|
| POLDI   | 8     | PSI standard configuration |
| 4x10    | 10    | Custom configuration |
| 5x8     | 8     | Custom configuration |
| 3x14    | 14    | Custom configuration |

## Parameters Guide

### Noise Level (`noise_level`)

Controls the Wiener filter regularization:

- **Lower (0.01)**: Sharper features, more noise
- **Medium (0.1)**: Balanced (recommended starting point)
- **Higher (1.0)**: Smoother, may blur edges

### Filter Types (`filter_type`)

Frequency-domain filters:

- `"none"`: No filtering (default)
- `"LowPass"`: Rectangular window
- `"LowPassBu"`: Butterworth-like filter
- `"LowPassGa"`: Gaussian filter

## Legacy Code

The original MATLAB implementation and first Python conversion are preserved in [.legacy/](.legacy/):

```
.legacy/
├── matlab/      # Original MATLAB code
└── python/      # First Python conversion
```

See [.legacy/README.md](.legacy/README.md) for details on:
- Using the legacy code
- Testing against MATLAB
- Migration guide

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### MATLAB Comparison Tests

Compare Python implementation with legacy MATLAB code:

```bash
# Install Octave (open-source MATLAB)
# Ubuntu/Debian: sudo apt-get install octave
# macOS: brew install octave

# Install oct2py
pip install oct2py

# Run comparison tests
pytest tests/test_matlab_comparison.py -v
```

### Test Coverage

```bash
pytest --cov=fobi --cov-report=html
# Open htmlcov/index.html
```

## Project Structure

```
FOBI/
├── fobi/                    # Main package
│   ├── workflow.py         # New OO API with method chaining
│   ├── reduction/          # Core reconstruction algorithms
│   ├── edge_fitting/       # Bragg edge analysis (2D legacy)
│   └── utils/              # Utilities
├── notebooks/              # Tutorial notebooks
│   └── tutorial.ipynb      # Comprehensive tutorial
├── tests/                  # Test suite
│   ├── test_*.py          # Unit tests
│   └── test_matlab_comparison.py  # MATLAB comparison
├── .legacy/                # Legacy code archive
│   ├── matlab/            # Original MATLAB implementation
│   └── python/            # First Python conversion
├── streamlit_app_1d.py    # Interactive 1D app (new API)
├── streamlit_app.py       # Interactive 2D app (legacy)
└── pyproject.toml         # Package configuration
```

## Examples

### Example 1: Iron Powder

```python
import fobi

# Generate iron powder data (for demonstration)
# In practice, load your real data

result = (fobi.Workflow
    .load("iron_sample.csv", "iron_openbeam.csv", L=9)
    .interpolate(tmax=10000, nrep=8)
    .convolve(chopper="POLDI", noise_level=0.1, filter_type="LowPassGa")
    .reconstruct())

# Identify Bragg edges
# Iron BCC edges at: 2.027 Å (110), 2.866 Å (200), 4.050 Å (211)
result.plot(what="transmission", x_axis="wavelength")
```

### Example 2: Parameter Sweep

```python
import fobi
import matplotlib.pyplot as plt

noise_levels = [0.01, 0.1, 0.5, 1.0]
results = []

for noise in noise_levels:
    result = (fobi.Workflow
        .load_arrays(signal=signal, openbeam=openbeam, time=t, L=9)
        .interpolate(tmax=10000, nrep=8)
        .convolve(chopper="POLDI", noise_level=noise)
        .reconstruct())
    results.append(result)

# Compare results
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, result, noise in zip(axes.flat, results, noise_levels):
    ax.plot(result.wavelength, result.transmission)
    ax.set_title(f'Noise level = {noise}')
```

### Example 3: Batch Processing

```python
import fobi
from pathlib import Path

# Process multiple samples
data_dir = Path("data/")
samples = list(data_dir.glob("sample_*.csv"))

for sample_file in samples:
    result = (fobi.Workflow
        .load(signal=sample_file, openbeam="openbeam.csv", L=9)
        .interpolate(tmax=10000, nrep=8)
        .convolve(chopper="POLDI", noise_level=0.1)
        .reconstruct())

    # Save with sample name
    output_file = f"results/{sample_file.stem}_reconstructed.csv"
    result.save(output_file)
```

## Citation

If you use FOBI in your research, please cite:

```bibtex
@article{carminati2020fobi,
  title={Bragg-edge attenuation spectra at voxel level from 4D wavelength-resolved neutron tomography},
  author={Carminati, C. and others},
  journal={Scientific Reports},
  volume={10},
  pages={13893},
  year={2020},
  publisher={Nature Publishing Group},
  doi={10.1038/s41598-020-71705-4}
}
```

**Publication**: [Nature Scientific Reports](https://www.nature.com/articles/s41598-020-71705-4)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/fobi/issues)
- **Documentation**: See [notebooks/tutorial.ipynb](notebooks/tutorial.ipynb)
- **Questions**: Open a discussion on GitHub

## Acknowledgments

- Original MATLAB implementation by the FOBI team
- Python conversion and new API design
- Neutron imaging community at PSI and beyond

## Changelog

### Version 1.0.0 (Current)

- Complete refactoring to object-oriented API
- Method chaining for clean workflows
- Focus on 1D spectrum reconstruction
- Comprehensive tutorial notebook
- Interactive Streamlit web app
- MATLAB comparison tests with oct2py
- Legacy code preserved in `.legacy/`
- Full documentation and examples

### Legacy Versions

See [.legacy/README.md](.legacy/README.md) for information about previous implementations.
