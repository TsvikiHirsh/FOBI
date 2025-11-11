# FOBI Migration Guide

This document summarizes the refactoring from the legacy implementation to the new object-oriented API.

## What Changed?

### New Features ✨

1. **Object-Oriented API with Method Chaining**
   - Clean, fluent interface inspired by modern Python libraries
   - Easy to read and understand
   - Type-safe with helpful error messages

2. **1D-Focused Design**
   - Optimized for the primary use case (1D spectrum reconstruction)
   - Simpler interface for 1D data
   - 2D functionality preserved in legacy code

3. **Enhanced Tutorial & Documentation**
   - Comprehensive Jupyter notebook tutorial
   - New Streamlit app for 1D reconstruction
   - Better examples and use cases

4. **Testing Infrastructure**
   - MATLAB comparison tests using oct2py
   - Ensures Python implementation matches original MATLAB
   - Easy to verify correctness

5. **Better Organization**
   - Legacy code preserved in `.legacy/` folder
   - Clear separation of concerns
   - Modern Python package structure

## Code Comparison

### Old Way (Legacy)

```python
# Manual pipeline with multiple steps
from fobi.reduction import fobi_wiener_2d, interpolate_noreadoutgaps
from fobi.reduction.time_delays import fobi_poldi_time_delays
from fobi.reduction.wiener import wiener_deconvolution

# Load data
y = np.loadtxt('sample.csv')
y0 = np.loadtxt('openbeam.csv')
t = np.linspace(0, 10000, len(y))

# Step 1: Interpolate
y_merged, t_merged = interpolate_noreadoutgaps(y, t, tmax=10000, nrep=8)
y0_merged, _ = interpolate_noreadoutgaps(y0, t, tmax=10000, nrep=8)

# Step 2: Get chopper response
D = fobi_poldi_time_delays(t_merged)

# Step 3: Wiener deconvolution
nslits = 8
y_rec = nslits * wiener_deconvolution(y_merged, D, c=0.1)
y0_rec = nslits * wiener_deconvolution(y0_merged, D, c=0.1)

# Step 4: Calculate transmission
T = y_rec / y0_rec

# Step 5: Calculate wavelength manually
L = 9  # meters
wavelength = 3.956 * (t_merged / 1000) / L

# Step 6: Plot manually
import matplotlib.pyplot as plt
plt.plot(wavelength, T)
plt.xlabel('Wavelength (Å)')
plt.ylabel('Transmission')
plt.show()
```

### New Way (Current)

```python
# Clean method chaining
import fobi

result = (fobi.Workflow
    .load(signal="sample.csv", openbeam="openbeam.csv", L=9)
    .interpolate(tmax=10000, nrep=8)
    .convolve(chopper="POLDI", noise_level=0.1)
    .reconstruct())

# Everything is done! Just plot
result.plot(what="transmission", x_axis="wavelength")

# Or save
result.save("output.csv")
```

**Benefits:**
- 85% less code
- No manual calculations
- Built-in wavelength conversion
- Automatic error handling
- Easy to modify parameters

## Migration Steps

If you have existing code using the legacy API, follow these steps:

### Step 1: Update Imports

**Before:**
```python
from fobi.reduction import fobi_wiener_2d, interpolate_noreadoutgaps
from fobi.reduction.time_delays import fobi_poldi_time_delays
```

**After:**
```python
import fobi
```

### Step 2: Replace Function Calls with Workflow

**Before:**
```python
# Multiple function calls
y_merged, t_merged = interpolate_noreadoutgaps(y, t, tmax, nrep)
D = fobi_poldi_time_delays(t_merged)
y_rec = wiener_deconvolution(y_merged, D, c)
```

**After:**
```python
# Single workflow
result = (fobi.Workflow
    .load_arrays(signal=y, openbeam=y0, time=t, L=9)
    .interpolate(tmax=tmax, nrep=nrep)
    .convolve(chopper="POLDI", noise_level=c)
    .reconstruct())
```

### Step 3: Update Result Access

**Before:**
```python
# Results were separate variables
T = transmission
wavelength = 3.956 * (t / 1000) / L
```

**After:**
```python
# Results in single object
T = result.transmission
wavelength = result.wavelength  # Automatically calculated
```

### Step 4: Use Built-in Plotting

**Before:**
```python
import matplotlib.pyplot as plt
plt.plot(wavelength, T)
plt.xlabel('Wavelength (Å)')
plt.ylabel('Transmission')
plt.show()
```

**After:**
```python
result.plot(what="transmission", x_axis="wavelength")
```

## Feature Mapping

| Legacy Approach | New API | Notes |
|----------------|---------|-------|
| Manual CSV loading | `Workflow.load()` | Handles column names automatically |
| Numpy array passing | `Workflow.load_arrays()` | Direct array input |
| `interpolate_noreadoutgaps()` | `.interpolate()` | Part of workflow |
| `fobi_poldi_time_delays()` | `.convolve(chopper="POLDI")` | Automatic selection |
| `wiener_deconvolution()` | `.convolve()` + `.reconstruct()` | Combined into workflow |
| Manual wavelength calc | `result.wavelength` | Automatic if L provided |
| Manual plotting | `result.plot()` | Built-in with multiple options |
| Manual CSV save | `result.save()` | Supports CSV and NPY |

## Backwards Compatibility

The legacy code is **fully preserved** in [.legacy/python/](/.legacy/python/) and still works:

```python
# Legacy code still available
from fobi.reduction import fobi_wiener_2d
# ... use as before
```

However, for new projects, we **strongly recommend** using the new API because:

1. **Simpler**: Less code, fewer manual steps
2. **Safer**: Built-in validation and error checking
3. **More Features**: Plotting, saving, wavelength conversion
4. **Better Tested**: Includes MATLAB comparison tests
5. **Modern**: Follows Python best practices

## 2D vs 1D

### When to Use 1D API (New)

- **Single pixel or averaged spectra**
- **1D transmission measurements**
- **Quick analysis and exploration**
- **Learning FOBI**

Use the new `Workflow` API:

```python
result = (fobi.Workflow
    .load(signal="data.csv", openbeam="ob.csv", L=9)
    .interpolate(tmax=10000, nrep=8)
    .convolve(chopper="POLDI", noise_level=0.1)
    .reconstruct())
```

### When to Use 2D API (Legacy)

- **Full 2D detector images**
- **Spatially-resolved imaging**
- **Material property maps**
- **Advanced edge fitting**

Use the legacy `fobi_wiener_2d()`:

```python
from fobi.reduction import fobi_wiener_2d
T, y_rec, y0_rec, t_merged = fobi_wiener_2d(I, I0, t, tmax, nrep, chopper_id)
```

The 2D functionality is preserved but not refactored (yet). For 2D work, use the legacy code in [.legacy/python/fobi/](/.legacy/python/fobi/).

## Testing Your Migration

After migrating your code, verify it works correctly:

```python
# Old result
T_old = old_transmission_result

# New result
T_new = result.transmission

# Compare
import numpy as np
assert np.allclose(T_old, T_new, rtol=1e-5)
print("Migration successful! Results match.")
```

## Common Pitfalls

### 1. Forgetting to Provide L

**Error:**
```python
result.plot(what="transmission", x_axis="wavelength")
# ValueError: Wavelength not available. Provide L when loading data.
```

**Solution:**
```python
# Add L parameter when loading
result = fobi.Workflow.load(..., L=9)
```

### 2. Wrong Data Format

**Error:**
```python
# CSV has columns 'tof' and 'intensity' instead of 'time' and 'signal'
```

**Solution:**
```python
# Specify column names
result = fobi.Workflow.load(
    signal="data.csv",
    openbeam="ob.csv",
    L=9,
    time_col="tof",
    signal_col="intensity"
)
```

### 3. Chopper Name Typo

**Error:**
```python
.convolve(chopper="poldi")  # lowercase
# ValueError: Unknown chopper: poldi
```

**Solution:**
```python
.convolve(chopper="POLDI")  # uppercase
```

## Getting Help

1. **Tutorial**: See [notebooks/tutorial.ipynb](notebooks/tutorial.ipynb)
2. **Examples**: Check the examples in this document
3. **Legacy Code**: Reference [.legacy/README.md](.legacy/README.md)
4. **Streamlit App**: Run `streamlit run streamlit_app_1d.py` for interactive exploration
5. **Issues**: Open an issue on GitHub

## Summary

The new FOBI API provides:

✅ **Cleaner code** with method chaining
✅ **Fewer lines** of code (up to 85% reduction)
✅ **Built-in features** (plotting, saving, wavelength conversion)
✅ **Better testing** (MATLAB comparison)
✅ **Modern Python** design patterns
✅ **Backwards compatibility** (legacy code preserved)

**Recommended**: Migrate to the new API for all 1D reconstruction work.

**Optional**: Keep using legacy code for 2D imaging until it's refactored.

---

**Questions?** See the [tutorial notebook](notebooks/tutorial.ipynb) or [README](README_NEW.md) for more information.
