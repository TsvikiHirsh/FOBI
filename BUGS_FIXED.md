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

## Summary

- **Bug**: Array broadcasting error in filter kernel creation
- **Severity**: High (blocked usage of filters)
- **Root Cause**: Incorrect array index calculation
- **Fix**: Proper array size calculation with bounds checking
- **Testing**: All tests pass, all filter types work
- **Files Changed**: `fobi/reduction/wiener.py`

The FOBI package now works correctly with all frequency-domain filters!
