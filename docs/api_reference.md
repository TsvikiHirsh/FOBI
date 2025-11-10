# FOBI API Reference

Complete API documentation for the FOBI package.

## Table of Contents

- [fobi.reduction](#fobireduction)
  - [wiener_deconvolution](#wiener_deconvolution)
  - [fobi_wiener_2d](#fobi_wiener_2d)
  - [interpolate_noreadoutgaps](#interpolate_noreadoutgaps)
  - [Time Delay Functions](#time-delay-functions)
- [fobi.edge_fitting](#fobiedge_fitting)
  - [edge_fit_gaussian](#edge_fit_gaussian)
  - [edge_fit_gaussian_2d](#edge_fit_gaussian_2d)
- [fobi.utils](#fobiutils)
  - [generate_test_data](#generate_test_data)
  - [generate_chopper_modulated_data](#generate_chopper_modulated_data)
  - [plot_transmission_spectrum](#plot_transmission_spectrum)
  - [plot_edge_maps](#plot_edge_maps)

---

## fobi.reduction

Module for data reduction and Wiener deconvolution.

### wiener_deconvolution

```python
fobi.reduction.wiener_deconvolution(
    f: np.ndarray,
    g: np.ndarray,
    c: float = 0.1,
    filter_type: Literal["none", "LowPass", "LowPassBu", "LowPassGa"] = "none"
) -> np.ndarray
```

Perform Wiener deconvolution using the correlation theorem in frequency domain.

**Parameters:**

- **f** (*np.ndarray*): Input signal (measured transmission), shape (n,)
- **g** (*np.ndarray*): Instrument response function (time delays), shape (n,)
- **c** (*float*, optional): Regularization constant, default 0.1. Higher values give more smoothing but less resolution
- **filter_type** (*str*, optional): Type of low-pass filter:
  - `'none'`: No filtering (default)
  - `'LowPass'`: Rectangular window
  - `'LowPassBu'`: Butterworth-like filter
  - `'LowPassGa'`: Gaussian filter

**Returns:**

- **H** (*np.ndarray*): Deconvolved signal (reconstructed transmission spectrum)

**Notes:**

The Wiener filter in frequency domain is: `H = F * conj(G) / (|G|^2 + c)`

**Example:**

```python
from fobi.reduction import wiener_deconvolution
import numpy as np

signal = np.random.randn(1000)
response = np.zeros(1000)
response[500] = 1.0  # Delta function

reconstructed = wiener_deconvolution(signal, response, c=0.01)
```

---

### fobi_wiener_2d

```python
fobi.reduction.fobi_wiener_2d(
    I: np.ndarray,
    I0: np.ndarray,
    t: np.ndarray,
    tmax: float,
    nrep: int,
    chopper_id: Literal["POLDI", "4x10", "5x8", "3x14"],
    c: float = 0.1,
    filter_type: str = "none",
    roll: int = 0,
    flag_smooth: int = 0
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
```

Perform 2D spatially-resolved FOBI Wiener deconvolution.

**Parameters:**

- **I** (*np.ndarray*): Sample transmission data, shape (rows, cols, time_bins)
- **I0** (*np.ndarray*): Open beam (normalization) data, shape (rows, cols, time_bins)
- **t** (*np.ndarray*): Time-of-flight values, shape (time_bins,)
- **tmax** (*float*): Maximum time-of-flight value
- **nrep** (*int*): Number of chopper repetitions
- **chopper_id** (*str*): Chopper configuration ('POLDI', '4x10', '5x8', or '3x14')
- **c** (*float*, optional): Wiener filter regularization parameter, default 0.1
- **filter_type** (*str*, optional): Frequency domain filter type, default 'none'
- **roll** (*int*, optional): Circular shift to apply to reconstructed spectra, default 0
- **flag_smooth** (*int*, optional): Smoothing span for moving average filter (0 = no smoothing)

**Returns:**

- **T** (*np.ndarray*): Reconstructed transmission, shape (rows, cols, time_bins)
- **y_rec** (*np.ndarray*): Reconstructed sample intensity, shape (rows, cols, time_bins)
- **y0_rec** (*np.ndarray*): Reconstructed open beam intensity, shape (rows, cols, time_bins)
- **t_merged** (*np.ndarray*): Merged time-of-flight array

**Example:**

```python
from fobi.reduction import fobi_wiener_2d
import numpy as np

I = np.random.randn(100, 100, 1000)
I0 = np.random.randn(100, 100, 1000)
t = np.linspace(0, 10000, 1000)

T, y_rec, y0_rec, t_merged = fobi_wiener_2d(
    I, I0, t, tmax=10000, nrep=8, chopper_id='POLDI', c=0.1
)
```

---

### interpolate_noreadoutgaps

```python
fobi.reduction.interpolate_noreadoutgaps(
    y: np.ndarray,
    t: np.ndarray,
    tmax: float,
    nrep: int,
    plot_flag: bool = False
) -> Tuple[np.ndarray, np.ndarray]
```

Interpolate and merge chopper repetitions to remove readout gaps.

**Parameters:**

- **y** (*np.ndarray*): Input signal (intensity vs time), shape (n,)
- **t** (*np.ndarray*): Time-of-flight values, shape (n,)
- **tmax** (*float*): Maximum time-of-flight value
- **nrep** (*int*): Number of chopper repetitions
- **plot_flag** (*bool*, optional): If True, plot the individual repetitions and merged result

**Returns:**

- **y_merged** (*np.ndarray*): Merged signal with readout gaps removed
- **t_merged** (*np.ndarray*): Corresponding time array

**Notes:**

The function works by:
1. Interpolating data onto a uniform grid covering all repetitions
2. Reshaping into (replen, nrep) where each column is one repetition
3. Averaging across repetitions using nanmean to handle gaps

---

### Time Delay Functions

#### fobi_poldi_time_delays

```python
fobi.reduction.fobi_poldi_time_delays(time: np.ndarray) -> np.ndarray
```

Calculate time delays for POLDI chopper configuration (8 slits).

#### fobi_4x10_time_delays

```python
fobi.reduction.fobi_4x10_time_delays(time: np.ndarray) -> np.ndarray
```

Calculate time delays for 4x10 chopper configuration (40 slits).

#### fobi_5x8_time_delays

```python
fobi.reduction.fobi_5x8_time_delays(time: np.ndarray) -> np.ndarray
```

Calculate time delays for 5x8 chopper configuration (40 slits).

#### fobi_3x14_time_delays

```python
fobi.reduction.fobi_3x14_time_delays(time: np.ndarray) -> np.ndarray
```

Calculate time delays for 3x14 chopper configuration (42 slits).

---

## fobi.edge_fitting

Module for fitting Bragg edges in transmission spectra.

### edge_fit_gaussian

```python
fobi.edge_fitting.edge_fit_gaussian(
    signal: np.ndarray,
    spectrum: np.ndarray,
    spectrum_range: Tuple[float, float],
    est_p: float,
    est_w: float,
    est_h: float,
    BC_p: Tuple[float, float],
    BC_w: Tuple[float, float],
    BC_h: Tuple[float, float],
    smooth_span: int = 0,
    plot_result: bool = False
) -> Tuple[float, float, float]
```

Fit a Gaussian model to a single Bragg edge.

**Parameters:**

- **signal** (*np.ndarray*): Transmission spectrum, shape (n,)
- **spectrum** (*np.ndarray*): Wavelength or TOF array, shape (n,)
- **spectrum_range** (*tuple*): (min, max) range for fitting
- **est_p** (*float*): Initial guess for edge position
- **est_w** (*float*): Initial guess for edge width
- **est_h** (*float*): Initial guess for edge height (amplitude, typically negative)
- **BC_p** (*tuple*): (lower, upper) bounds for position
- **BC_w** (*tuple*): (lower, upper) bounds for width
- **BC_h** (*tuple*): (lower, upper) bounds for height
- **smooth_span** (*int*, optional): Smoothing window size (0 = no smoothing)
- **plot_result** (*bool*, optional): If True, plot the fit result

**Returns:**

- **pos** (*float*): Fitted edge position
- **wid** (*float*): Fitted edge width
- **h** (*float*): Fitted edge height

**Notes:**

The fitting is performed on the derivative of the transmission spectrum, as Bragg edges appear as step-like features in transmission and Gaussian-like peaks in the derivative.

**Example:**

```python
from fobi.edge_fitting import edge_fit_gaussian
import numpy as np

spectrum = np.linspace(0, 10, 1000)
signal = 1 - 0.5 / (1 + np.exp(-(spectrum - 5) / 0.1))

pos, wid, h = edge_fit_gaussian(
    signal, spectrum, (4, 6),
    est_p=5.0, est_w=0.1, est_h=-0.5,
    BC_p=(4, 6), BC_w=(0.01, 1), BC_h=(-2, 0),
    smooth_span=5, plot_result=True
)
```

---

### edge_fit_gaussian_2d

```python
fobi.edge_fitting.edge_fit_gaussian_2d(
    data: np.ndarray,
    spectrum: np.ndarray,
    spectrum_range: Tuple[float, float],
    est_p: float,
    est_w: float,
    est_h: float,
    BC_p: Tuple[float, float],
    BC_w: Tuple[float, float],
    BC_h: Tuple[float, float],
    mask: Optional[np.ndarray] = None,
    test: Optional[Tuple[int, int]] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]
```

Perform 2D spatially-resolved Gaussian edge fitting.

**Parameters:**

- **data** (*np.ndarray*): Transmission data, shape (rows, cols, spectrum_length)
- **spectrum** (*np.ndarray*): Wavelength or TOF array
- **spectrum_range** (*tuple*): (min, max) range for fitting
- **est_p** (*float*): Initial guess for edge position
- **est_w** (*float*): Initial guess for edge width
- **est_h** (*float*): Initial guess for edge height
- **BC_p** (*tuple*): (lower, upper) bounds for position
- **BC_w** (*tuple*): (lower, upper) bounds for width
- **BC_h** (*tuple*): (lower, upper) bounds for height
- **mask** (*np.ndarray*, optional): Binary mask (1 = fit, 0 = skip), shape (rows, cols)
- **test** (*tuple*, optional): If provided, only fit pixel (test[0], test[1]) and plot result

**Returns:**

- **edge_p** (*np.ndarray*): Edge position map, shape (rows, cols)
- **edge_w** (*np.ndarray*): Edge width map, shape (rows, cols)
- **edge_h** (*np.ndarray*): Edge height map, shape (rows, cols)

**Example:**

```python
from fobi.edge_fitting import edge_fit_gaussian_2d
import numpy as np

data = np.random.randn(100, 100, 1000)
spectrum = np.linspace(0, 10, 1000)

edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
    data, spectrum, (4, 6),
    est_p=5.0, est_w=0.1, est_h=-0.5,
    BC_p=(4, 6), BC_w=(0.01, 1), BC_h=(-2, 0)
)
```

---

## fobi.utils

Utility functions for visualization and test data generation.

### generate_test_data

```python
fobi.utils.generate_test_data(
    shape: Tuple[int, int, int] = (50, 50, 500),
    edge_position: float = 250.0,
    edge_width: float = 10.0,
    edge_height: float = 0.5,
    noise_level: float = 0.02,
    add_spatial_variation: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]
```

Generate synthetic neutron transmission data with Bragg edges.

**Parameters:**

- **shape** (*tuple*): Data shape (rows, cols, time_bins)
- **edge_position** (*float*): Center position of the Bragg edge (in bins)
- **edge_width** (*float*): Width of the edge transition (in bins)
- **edge_height** (*float*): Edge drop (0 to 1, represents transmission decrease)
- **noise_level** (*float*): Relative noise level (standard deviation / mean)
- **add_spatial_variation** (*bool*): If True, add spatial gradients to edge parameters

**Returns:**

- **I** (*np.ndarray*): Sample transmission data, shape (rows, cols, time_bins)
- **I0** (*np.ndarray*): Open beam data, shape (rows, cols, time_bins)
- **t** (*np.ndarray*): Time-of-flight array, shape (time_bins,)

**Example:**

```python
from fobi.utils import generate_test_data

I, I0, t = generate_test_data(
    shape=(100, 100, 1000),
    edge_position=500,
    edge_width=20,
    edge_height=0.4,
    noise_level=0.03
)
```

---

### generate_chopper_modulated_data

```python
fobi.utils.generate_chopper_modulated_data(
    shape: Tuple[int, int, int] = (50, 50, 1000),
    nrep: int = 8,
    chopper_id: str = "POLDI",
    edge_position: float = 500.0,
    edge_width: float = 20.0,
    edge_height: float = 0.5,
    noise_level: float = 0.05
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]
```

Generate synthetic chopper-modulated neutron data for FOBI testing.

**Parameters:**

- **shape** (*tuple*): Data shape (rows, cols, time_bins)
- **nrep** (*int*): Number of chopper repetitions
- **chopper_id** (*str*): Chopper configuration ('POLDI', '4x10', '5x8', '3x14')
- **edge_position** (*float*): True edge position (in bins)
- **edge_width** (*float*): True edge width (in bins)
- **edge_height** (*float*): Edge transmission drop (0 to 1)
- **noise_level** (*float*): Relative noise level

**Returns:**

- **I_mod** (*np.ndarray*): Chopper-modulated sample data
- **I0_mod** (*np.ndarray*): Chopper-modulated open beam data
- **t** (*np.ndarray*): Time-of-flight array
- **tmax** (*float*): Maximum time-of-flight value

---

### plot_transmission_spectrum

```python
fobi.utils.plot_transmission_spectrum(
    spectrum: np.ndarray,
    transmission: np.ndarray,
    title: str = "Transmission Spectrum",
    edge_positions: Optional[list] = None,
    figsize: Tuple[int, int] = (12, 5)
)
```

Plot transmission spectrum with optional edge markers.

**Parameters:**

- **spectrum** (*np.ndarray*): Wavelength or TOF array
- **transmission** (*np.ndarray*): Transmission values
- **title** (*str*): Plot title
- **edge_positions** (*list*, optional): List of edge positions to mark
- **figsize** (*tuple*): Figure size (width, height)

**Returns:**

- **fig**: Matplotlib figure object

---

### plot_edge_maps

```python
fobi.utils.plot_edge_maps(
    edge_position: np.ndarray,
    edge_width: np.ndarray,
    edge_height: np.ndarray,
    titles: Optional[Tuple[str, str, str]] = None,
    figsize: Tuple[int, int] = (15, 5),
    cmap: str = "viridis"
)
```

Plot 2D maps of edge parameters.

**Parameters:**

- **edge_position** (*np.ndarray*): 2D array of edge positions
- **edge_width** (*np.ndarray*): 2D array of edge widths
- **edge_height** (*np.ndarray*): 2D array of edge heights
- **titles** (*tuple*, optional): Titles for (position, width, height) plots
- **figsize** (*tuple*): Figure size
- **cmap** (*str*): Colormap name

**Returns:**

- **fig**: Matplotlib figure object

---

## Constants and Enumerations

### Chopper Configurations

The package supports the following chopper configurations:

- **POLDI**: 8 slits at specific angles
- **4x10**: 4 groups of 10 slits (40 total)
- **5x8**: 5 groups of 8 slits (40 total)
- **3x14**: 3 groups of 14 slits (42 total)

### Filter Types

For Wiener deconvolution, the following frequency-domain filters are available:

- **none**: No filtering (default)
- **LowPass**: Rectangular window filter
- **LowPassBu**: Butterworth-like smooth filter
- **LowPassGa**: Gaussian filter

---

## Complete Example

```python
import numpy as np
from fobi.reduction import fobi_wiener_2d
from fobi.edge_fitting import edge_fit_gaussian_2d
from fobi.utils import generate_test_data, plot_edge_maps

# 1. Generate synthetic data
I, I0, t = generate_test_data(
    shape=(50, 50, 800),
    edge_position=400,
    edge_width=20,
    edge_height=0.5
)

# 2. Run FOBI reconstruction
T, _, _, t_merged = fobi_wiener_2d(
    I, I0, t,
    tmax=t[-1],
    nrep=8,
    chopper_id='POLDI',
    c=0.1
)

# 3. Fit edges
edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
    T, t_merged,
    spectrum_range=(t_merged[0], t_merged[-1]),
    est_p=t_merged[len(t_merged)//2],
    est_w=0.5,
    est_h=-0.05,
    BC_p=(t_merged[0], t_merged[-1]),
    BC_w=(0.01, 10),
    BC_h=(-1, 0)
)

# 4. Visualize results
fig = plot_edge_maps(edge_p, edge_w, edge_h)
fig.savefig('results.png', dpi=150)
```

---

For more examples and tutorials, see the [User Guide](user_guide.md).
