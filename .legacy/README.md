# Legacy Code Archive

This directory contains the original MATLAB implementation and the first Python conversion of FOBI, preserved for reference and testing purposes.

## Directory Structure

```
.legacy/
├── matlab/              # Original MATLAB implementation
│   ├── functions/      # MATLAB function library
│   │   ├── Reduction/  # Core reconstruction functions
│   │   ├── EdgeFitting/# Bragg edge analysis
│   │   └── Utilities/  # Helper functions
│   └── scripts/        # Analysis scripts
│       ├── 01_SortMergeData.m
│       ├── 02_FobiReduction.m
│       └── 03_Fitting_new.m
│
└── python/             # First Python conversion
    ├── fobi/          # Python package (original structure)
    └── tests/         # Original test suite
```

## MATLAB Code

The MATLAB implementation is the original reference implementation from the publication:

> Carminati, C., et al. "Bragg-edge attenuation spectra at voxel level from 4D wavelength-resolved neutron tomography."
> *Nature Scientific Reports* 10, 13893 (2020).

### Key MATLAB Functions

- `FobiWiener.m` - Wiener deconvolution implementation
- `interpolate_noreadoutgaps.m` - Gap interpolation and merging
- `FobiPOLDITimeDelays.m` - Chopper response calculation
- `EdgeFitGaussian.m` - Bragg edge fitting

### Running MATLAB Code

The MATLAB code is preserved for:

1. **Reference**: Understanding the original algorithm
2. **Testing**: Comparing Python results with MATLAB (see `tests/test_matlab_comparison.py`)
3. **Legacy Support**: For users who need the original implementation

## Python Legacy Code

The `python/` subdirectory contains the first full Python conversion. This has been superseded by the new object-oriented API with method chaining, but is preserved for:

- Backward compatibility testing
- Reference for the conversion process
- Comparison with the new API

## Using Legacy Code for Testing

### Comparing with MATLAB

The new Python implementation can be tested against MATLAB using `oct2py`:

```python
# Install oct2py and Octave
# pip install oct2py
# sudo apt-get install octave  # or brew install octave on macOS

pytest tests/test_matlab_comparison.py -v
```

This will run comparison tests that:
1. Execute the same operations in both MATLAB and Python
2. Compare results with numerical tolerance
3. Ensure the Python implementation is accurate

### Example Comparison

```python
import numpy as np
from oct2py import Oct2Py
from fobi.reduction import wiener_deconvolution

# Start Octave engine
oc = Oct2Py()
oc.addpath('.legacy/matlab/functions/Reduction')

# Generate test data
signal = np.random.randn(100)
response = np.zeros(100)
response[50] = 1.0

# Python
result_python = wiener_deconvolution(signal, response, c=0.1)

# MATLAB
result_matlab = oc.feval('FobiWiener', signal, response, 0.1)

# Compare
assert np.allclose(result_python, result_matlab, rtol=1e-3)
```

## Migration from Legacy to New API

If you have code using the legacy Python API, here's how to migrate to the new object-oriented API:

### Old Approach (Legacy)

```python
from fobi.reduction import fobi_wiener_2d, interpolate_noreadoutgaps
from fobi.reduction.time_delays import fobi_poldi_time_delays

# Manual pipeline
y_merged, t_merged = interpolate_noreadoutgaps(y, t, tmax, nrep)
y0_merged, _ = interpolate_noreadoutgaps(y0, t, tmax, nrep)
D = fobi_poldi_time_delays(t_merged)
y_rec = 8 * wiener_deconvolution(y_merged, D, c=0.1)
y0_rec = 8 * wiener_deconvolution(y0_merged, D, c=0.1)
T = y_rec / y0_rec
```

### New Approach (Current)

```python
import fobi

# Clean method chaining
result = (fobi.Workflow
    .load_arrays(signal=y, openbeam=y0, time=t, L=9)
    .interpolate(tmax=tmax, nrep=8)
    .convolve(chopper="POLDI", noise_level=0.1)
    .reconstruct())

# Access results
T = result.transmission
wavelength = result.wavelength
```

## Benefits of New API

1. **Cleaner**: Method chaining is more readable
2. **Safer**: Type checking and validation
3. **More Features**: Built-in plotting, saving, wavelength conversion
4. **Better Tested**: Comprehensive test suite including MATLAB comparison
5. **1D Focused**: Optimized for 1D spectrum reconstruction (the main use case)

## Preservation Policy

This legacy code is:
- **Read-only**: No updates or bug fixes
- **Tested**: Comparison tests ensure consistency
- **Documented**: Kept as reference material
- **Versioned**: Snapshots from specific git commits

For all new work, use the current API in the main `fobi/` package.

## License

Both MATLAB and Python legacy code are under the same MIT license as the main package.

## References

- Original Publication: https://www.nature.com/articles/s41598-020-71705-4
- MATLAB Central: (if applicable)
- Python Package Index: (if applicable)
