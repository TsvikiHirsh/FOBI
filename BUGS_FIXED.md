# Bug Fixes

## Filter Kernel Array Broadcasting Error

### Issue

When using frequency-domain filters (`LowPassBu`, `LowPassGa`), the code would crash with:

```
ValueError: could not broadcast input array from shape (500,) into shape (501,)
```

This occurred when the filter kernel creation tried to assign arrays of mismatched sizes.

### Root Cause

In `fobi/reduction/wiener.py`, the `_create_filter_kernel()` function had incorrect logic for calculating array indices:

```python
# Old code (buggy)
if length % 2 == 0:
    x0 = length // 2 + 1  # This caused issues
else:
    x0 = length // 2

# Left side
D = np.arange(1, x0)
HH = 1.0 / (1 + (D / width)**(2*n))
K[:x0] = np.flip(HH)[:len(K[:x0])]  # Arrays don't match!
```

The problem:
- For even-length arrays, `x0 = length // 2 + 1` created wrong split
- Generated arrays `HH` had different length than target `K[:x0]`
- Python couldn't broadcast mismatched shapes

### Fix

Updated the logic to properly calculate array sizes:

```python
# New code (fixed)
if length % 2 == 0:
    x0 = length // 2
else:
    x0 = length // 2

# Right side
right_len = length - x0 - 1
if right_len > 0:
    D = np.arange(1, right_len + 1)
    HH = 1.0 / (1 + (D / width)**(2*n))
    K[x0+1:x0+1+len(HH)] = HH  # Exact match

# Left side
if x0 > 0:
    D = np.arange(1, x0 + 1)
    HH = 1.0 / (1 + (D / width)**(2*n))
    K[:x0] = np.flip(HH)  # Exact match
```

Key improvements:
1. Simplified `x0` calculation
2. Explicitly calculate left and right array lengths
3. Use exact array sizes (no slicing with `[:len(...)]`)
4. Add bounds checking (`if x0 > 0`, `if right_len > 0`)
5. Ensure `width >= 1` to avoid division by zero

### Testing

Tested with various array lengths and all filter types:

```python
# Test results
✓ LowPass      length= 100 OK
✓ LowPassBu    length= 100 OK
✓ LowPassGa    length= 100 OK
✓ LowPass      length= 101 OK
✓ LowPassBu    length= 101 OK
✓ LowPassGa    length= 101 OK
✓ LowPass      length= 500 OK
✓ LowPassBu    length= 500 OK
✓ LowPassGa    length= 500 OK
✓ LowPass      length= 501 OK
✓ LowPassBu    length= 501 OK
✓ LowPassGa    length= 501 OK
```

All combinations now work correctly!

### Affected Code

**File**: [fobi/reduction/wiener.py](fobi/reduction/wiener.py)
**Function**: `_create_filter_kernel()`
**Lines**: 117-175

### Impact

This fix enables:
- ✅ All frequency-domain filters work correctly
- ✅ Both even and odd-length arrays supported
- ✅ Tutorial notebook section 5.3 now works
- ✅ All workflow tests pass (23/23)

### Verification

You can verify the fix works:

```python
import fobi
import numpy as np

# Generate data
t = np.linspace(0, 10000, 8000)
signal = np.random.randn(len(t)) + 1000
openbeam = np.random.randn(len(t)) + 1000

# Test all filters - should all work now!
for filt in ['none', 'LowPass', 'LowPassBu', 'LowPassGa']:
    result = (fobi.Workflow
        .load_arrays(signal=signal, openbeam=openbeam, time=t, L=9)
        .interpolate(tmax=10000, nrep=8)
        .convolve(chopper="POLDI", noise_level=0.1, filter_type=filt)
        .reconstruct())
    print(f"✓ {filt} works!")
```

### Status

**Fixed** ✅ - Committed to main codebase

---

## Empty Plots - Incorrect Wavelength Range

### Issue

All plots appeared empty in the tutorial notebook. When viewing plots with `plt.xlim(2, 6)` (typical Bragg edge range), no data was visible.

### Root Cause

After merging chopper repetitions in `interpolate_noreadoutgaps()`, the time array represented one chopper period (0 to tmax/nrep), not the full time range (0 to tmax). The wavelength calculation used this compressed time directly:

```python
# Old code (buggy)
wavelength = 3.956 * (self._time_processed / 1000) / self._L
# Result: wavelength range of [0, 0.549] Å instead of [0, 4.4] Å
```

This caused wavelength to span only ~0-0.5 Å when it should span 0-4.4 Å for typical measurements.

### Fix

Store `tmax` and `nrep` during interpolation, then scale the time appropriately for wavelength calculation:

```python
# In interpolate():
self._tmax = tmax
self._nrep = nrep

# In reconstruct():
time_for_wavelength = self._time_processed * self._nrep if self._nrep else self._time_processed
wavelength = 3.956 * (time_for_wavelength / 1000) / self._L
```

This scales the compressed time back to the full range, giving correct wavelength values.

### Testing

Created comprehensive test suite in [tests/test_plotting.py](tests/test_plotting.py):

```
✅ 10/10 plotting tests pass
✅ Wavelength range correct
✅ Data visible in typical range (2-6 Å)
✅ All filters produce valid plots
✅ Comparison plots work correctly
```

### Affected Code

**File**: [fobi/workflow.py](fobi/workflow.py)
- `__init__()`: Added `_tmax` and `_nrep` attributes (lines 212-213)
- `interpolate()`: Store tmax and nrep (lines 323-325)
- `reconstruct()`: Scale time for wavelength (lines 431-437)

### Impact

This fix enables:
- ✅ Correct wavelength calculation after merging
- ✅ Plots show data in expected ranges
- ✅ Tutorial notebook works correctly
- ✅ Comparison with true transmission possible

### Verification

```python
import fobi
import numpy as np

# Generate test data
t = np.linspace(0, 10000, 8000)
signal = np.random.randn(len(t)) + 1000
openbeam = np.random.randn(len(t)) + 1000

# Reconstruct and plot
result = (fobi.Workflow
    .load_arrays(signal=signal, openbeam=openbeam, time=t, L=9)
    .interpolate(tmax=10000, nrep=8)
    .convolve(chopper="POLDI", noise_level=0.1)
    .reconstruct())

# Should now have correct wavelength range
print(f"Wavelength range: [{result.wavelength.min():.3f}, {result.wavelength.max():.3f}] Å")
# Output: Wavelength range: [0.000, 4.392] Å  ✅ Correct!

# Plot should show data
result.plot(what="transmission", x_axis="wavelength")  # Now works!
```

### Status

**Fixed** ✅ - Committed to main codebase

---

## Summary

### Bug 1: Filter Kernel Array Error
- **Severity**: High (blocked filter usage)
- **Root Cause**: Array index calculation error
- **Fix**: Proper array size calculation
- **Files**: `fobi/reduction/wiener.py`

### Bug 2: Empty Plots
- **Severity**: High (all plots appeared empty)
- **Root Cause**: Incorrect wavelength scaling after merging
- **Fix**: Scale time by nrep for wavelength calculation
- **Files**: `fobi/workflow.py`

### Test Results

```bash
pytest tests/test_workflow.py -v    # 23/23 passed ✅
pytest tests/test_plotting.py -v    # 10/10 passed ✅
```

**All bugs fixed!** The FOBI package now works correctly with proper plotting and all filter types.
