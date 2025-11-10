# FOBI: Full-spectrum Bragg Edge Transmission Imaging

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**FOBI** is a Python package for processing neutron time-of-flight (TOF) imaging data using parametric reconstruction with Wiener deconvolution. It enables extraction of material properties from Bragg edge patterns in neutron transmission spectra.

## 🔬 Overview

FOBI uses Wiener deconvolution to reconstruct transmission spectra from chopper-modulated neutron TOF measurements. The technique provides:

- **Parametric reconstruction** of transmission spectra
- **2D spatially-resolved analysis** for imaging applications
- **Bragg edge fitting** to extract material properties:
  - Lattice spacing (edge position)
  - Strain/stress (edge shifts)
  - Texture (edge broadening)
  - Phase fractions (edge heights)

### Key Features

✨ **Complete Python implementation** - Converted from original MATLAB code
🚀 **Fast Wiener deconvolution** - FFT-based frequency domain processing
🗺️ **2D imaging support** - Pixel-by-pixel analysis
📊 **Interactive Streamlit app** - Explore data visually
🧪 **Comprehensive tests** - >90% code coverage
📚 **Detailed documentation** - API reference and user guides

## 📖 Publication

This package implements the method described in:

> **Carminati, C., et al.** (2020). "Bragg-edge attenuation spectra at voxel level from 4D wavelength-resolved neutron tomography." *Nature Scientific Reports* 10, 13893.
>
> 🔗 [https://www.nature.com/articles/s41598-020-71705-4](https://www.nature.com/articles/s41598-020-71705-4)

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/fobi.git
cd fobi

# Install package
pip install -e .

# Or install with optional dependencies
pip install -e ".[dev,viz,fits]"
```

### Basic Usage

```python
import numpy as np
from fobi.reduction import fobi_wiener_2d
from fobi.edge_fitting import edge_fit_gaussian_2d

# Load your data
I = np.load('sample_data.npy')      # Sample transmission
I0 = np.load('open_beam_data.npy')  # Open beam (normalization)
t = np.load('tof_spectrum.npy')     # Time-of-flight array

# FOBI reconstruction
T, y_rec, y0_rec, t_merged = fobi_wiener_2d(
    I, I0, t,
    tmax=0.03,           # Maximum TOF (s)
    nrep=4,              # Chopper repetitions
    chopper_id='POLDI',  # Chopper configuration
    c=0.1                # Wiener constant
)

# Fit Bragg edges
edge_pos, edge_width, edge_height = edge_fit_gaussian_2d(
    T, t_merged,
    spectrum_range=(0, 10),  # Fitting window
    est_p=4.8e-3,            # Estimated position
    est_w=4.4e-5,            # Estimated width
    est_h=3e-3,              # Estimated height
    BC_p=(4e-3, 5.4e-3),     # Position bounds
    BC_w=(0, 1e-3),          # Width bounds
    BC_h=(0, 1e-1)           # Height bounds
)
```

### Interactive Streamlit App

Launch the interactive web application:

```bash
streamlit run streamlit_app.py
```

Features:
- 📊 Generate synthetic test data
- 🔄 Run FOBI reconstruction with adjustable parameters
- 🎯 Fit Bragg edges interactively
- 🗺️ Visualize 2D parameter maps
- 📈 Explore transmission spectra pixel-by-pixel

![Streamlit App Screenshot](docs/streamlit_screenshot.png)

## 📚 Documentation

### User Guides

- **[Installation Guide](docs/installation.md)** - Detailed setup instructions
- **[User Guide](docs/user_guide.md)** - Step-by-step tutorials
- **[API Reference](docs/api_reference.md)** - Complete function documentation
- **[Examples](scripts_python/)** - Working example scripts

### Package Structure

```
fobi/
├── fobi/                      # Main package
│   ├── reduction/            # Wiener deconvolution and data processing
│   │   ├── wiener.py        # Wiener deconvolution functions
│   │   ├── data_processing.py  # Interpolation and gap filling
│   │   └── time_delays.py   # Chopper response functions
│   ├── edge_fitting/         # Bragg edge fitting
│   │   ├── gaussian.py      # Gaussian edge models
│   │   └── utils.py         # Fitting utilities
│   └── utils/                # Utilities
│       ├── visualization.py # Plotting functions
│       └── synthetic_data.py # Test data generation
├── tests/                    # Comprehensive test suite
├── scripts_python/           # Example scripts
├── streamlit_app.py         # Interactive web app
└── docs/                     # Documentation
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=fobi --cov-report=html

# Run specific test file
pytest tests/test_reduction.py -v
```

## 🎯 Example Workflow

### 1. Generate or Load Test Data

```python
from fobi.utils import generate_test_data

# Generate synthetic data for testing
I, I0, t = generate_test_data(
    shape=(50, 50, 800),
    edge_position=400,
    edge_width=20,
    edge_height=0.5,
    noise_level=0.03
)
```

### 2. Apply Spatial Filtering (Optional)

```python
from scipy.ndimage import uniform_filter

kernel_size = (5, 5)
I_filtered = uniform_filter(I, size=(kernel_size[0], kernel_size[1], 1))
I0_filtered = uniform_filter(I0, size=(kernel_size[0], kernel_size[1], 1))
```

### 3. FOBI Reconstruction

```python
from fobi.reduction import fobi_wiener_2d

T, y_rec, y0_rec, t_merged = fobi_wiener_2d(
    I_filtered, I0_filtered, t,
    tmax=t[-1],
    nrep=8,
    chopper_id='POLDI',
    c=0.1,
    roll=0
)
```

### 4. Edge Fitting

```python
from fobi.edge_fitting import edge_fit_gaussian_2d

edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
    T, t_merged,
    spectrum_range=(t_merged[0], t_merged[-1]),
    est_p=t_merged[len(t_merged)//2],
    est_w=(t_merged[1] - t_merged[0]) * 3,
    est_h=-0.05,
    BC_p=(t_merged[0], t_merged[-1]),
    BC_w=(0.01, 10),
    BC_h=(-1, 0)
)
```

### 5. Visualize Results

```python
from fobi.utils import plot_edge_maps

fig = plot_edge_maps(edge_p, edge_w, edge_h)
fig.savefig('edge_maps.png', dpi=150, bbox_inches='tight')
```

## 🔧 Supported Instruments

The package supports the following chopper configurations:

| Chopper ID | Description | Slits | Beamline |
|------------|-------------|-------|----------|
| `POLDI` | POLDI configuration | 8 | PSI (Switzerland) |
| `4x10` | 4 groups × 10 slits | 40 | Custom |
| `5x8` | 5 groups × 8 slits | 40 | Custom |
| `3x14` | 3 groups × 14 slits | 42 | Custom |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Original MATLAB implementation by C. Carminati et al.
- Paul Scherrer Institut (PSI) neutron imaging group
- Nature Scientific Reports for publishing the original method

## 📞 Contact

For questions or issues, please:
- Open an issue on GitHub
- Contact the maintainers
- Refer to the [original publication](https://www.nature.com/articles/s41598-020-71705-4)

## 🔗 Related Resources

- [Neutron Imaging at PSI](https://www.psi.ch/en/niag)
- [Nature Scientific Reports article](https://www.nature.com/articles/s41598-020-71705-4)
- [Original MATLAB code](https://github.com/your-org/fobi/tree/main/functions)

---

**Note:** This is a Python conversion of the original MATLAB FOBI package. The original MATLAB code is preserved in the `functions/` and `scripts/` directories for reference.
