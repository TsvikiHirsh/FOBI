"""
FOBI Workflow API
=================

Object-oriented API with method chaining for 1D signal reconstruction.

Example
-------
>>> import fobi
>>> result = (fobi.Workflow
...     .load(signal="iron_powder.csv", openbeam="openbeam.csv", L=9)
...     .interpolate(tmax=10000, nrep=8)
...     .convolve(chopper="POLDI", noise_level=0.1)
...     .reconstruct()
...     .plot())
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Union, Literal
from dataclasses import dataclass

from .reduction.wiener import wiener_deconvolution
from .reduction.data_processing import interpolate_noreadoutgaps
from .reduction.time_delays import (
    fobi_poldi_time_delays,
    fobi_4x10_time_delays,
    fobi_5x8_time_delays,
    fobi_3x14_time_delays,
)


@dataclass
class ReconstructionResult:
    """
    Container for reconstruction results.

    Attributes
    ----------
    transmission : np.ndarray
        Reconstructed transmission spectrum (sample/openbeam)
    signal : np.ndarray
        Reconstructed sample signal
    openbeam : np.ndarray
        Reconstructed open beam signal
    time : np.ndarray
        Time-of-flight array
    wavelength : Optional[np.ndarray]
        Wavelength array (if L is provided)
    metadata : dict
        Reconstruction parameters
    """
    transmission: np.ndarray
    signal: np.ndarray
    openbeam: np.ndarray
    time: np.ndarray
    wavelength: Optional[np.ndarray] = None
    metadata: dict = None

    def plot(self,
             what: Literal["transmission", "signal", "openbeam", "all"] = "transmission",
             x_axis: Literal["time", "wavelength"] = "time",
             figsize: tuple = (10, 6),
             **kwargs) -> 'ReconstructionResult':
        """
        Plot reconstruction results.

        Parameters
        ----------
        what : str
            What to plot: 'transmission', 'signal', 'openbeam', or 'all'
        x_axis : str
            X-axis variable: 'time' or 'wavelength'
        figsize : tuple
            Figure size (width, height)
        **kwargs
            Additional plotting arguments passed to plt.plot()

        Returns
        -------
        self : ReconstructionResult
            Returns self for method chaining
        """
        if x_axis == "wavelength" and self.wavelength is None:
            raise ValueError("Wavelength not available. Provide L when loading data.")

        x = self.wavelength if x_axis == "wavelength" else self.time
        x_label = "Wavelength (Å)" if x_axis == "wavelength" else "Time-of-Flight (µs)"

        if what == "all":
            fig, axes = plt.subplots(3, 1, figsize=(figsize[0], figsize[1]*2), sharex=True)

            axes[0].plot(x, self.transmission, **kwargs)
            axes[0].set_ylabel("Transmission")
            axes[0].grid(True, alpha=0.3)
            axes[0].set_title("FOBI Reconstruction Results")

            axes[1].plot(x, self.signal, **kwargs)
            axes[1].set_ylabel("Sample Signal")
            axes[1].grid(True, alpha=0.3)

            axes[2].plot(x, self.openbeam, **kwargs)
            axes[2].set_ylabel("Open Beam")
            axes[2].set_xlabel(x_label)
            axes[2].grid(True, alpha=0.3)

            plt.tight_layout()
        else:
            plt.figure(figsize=figsize)

            data_map = {
                "transmission": (self.transmission, "Transmission"),
                "signal": (self.signal, "Sample Signal"),
                "openbeam": (self.openbeam, "Open Beam"),
            }

            data, ylabel = data_map[what]
            plt.plot(x, data, **kwargs)
            plt.xlabel(x_label)
            plt.ylabel(ylabel)
            plt.title(f"FOBI Reconstruction: {ylabel}")
            plt.grid(True, alpha=0.3)

        plt.show()
        return self

    def save(self, filepath: Union[str, Path], format: Literal["csv", "npy"] = "csv") -> 'ReconstructionResult':
        """
        Save reconstruction results to file.

        Parameters
        ----------
        filepath : str or Path
            Output file path
        format : str
            File format: 'csv' or 'npy'

        Returns
        -------
        self : ReconstructionResult
            Returns self for method chaining
        """
        filepath = Path(filepath)

        if format == "csv":
            df = pd.DataFrame({
                'time': self.time,
                'transmission': self.transmission,
                'signal': self.signal,
                'openbeam': self.openbeam,
            })
            if self.wavelength is not None:
                df['wavelength'] = self.wavelength
            df.to_csv(filepath, index=False)
        elif format == "npy":
            data = {
                'time': self.time,
                'transmission': self.transmission,
                'signal': self.signal,
                'openbeam': self.openbeam,
                'wavelength': self.wavelength,
                'metadata': self.metadata,
            }
            np.save(filepath, data)
        else:
            raise ValueError(f"Unknown format: {format}")

        print(f"Results saved to {filepath}")
        return self


class Workflow:
    """
    Fluent API for FOBI 1D reconstruction workflow.

    This class provides a chainable interface for loading data, processing,
    and reconstructing neutron time-of-flight transmission spectra.

    Examples
    --------
    >>> import fobi
    >>>
    >>> # Load from CSV files
    >>> result = (fobi.Workflow
    ...     .load(signal="sample.csv", openbeam="openbeam.csv", L=9)
    ...     .interpolate(tmax=10000, nrep=8)
    ...     .convolve(chopper="POLDI", noise_level=0.1)
    ...     .reconstruct()
    ...     .plot())
    >>>
    >>> # Load from numpy arrays
    >>> result = (fobi.Workflow
    ...     .load_arrays(signal=y, openbeam=y0, time=t, L=9)
    ...     .interpolate(tmax=10000, nrep=8)
    ...     .convolve(chopper="POLDI", noise_level=0.1, filter_type="LowPassGa")
    ...     .reconstruct()
    ...     .save("output.csv"))
    """

    def __init__(self):
        """Initialize empty workflow."""
        self._signal_raw = None
        self._openbeam_raw = None
        self._time_raw = None
        self._L = None

        self._signal_processed = None
        self._openbeam_processed = None
        self._time_processed = None

        self._chopper_response = None
        self._chopper_id = None
        self._noise_level = 0.1
        self._filter_type = "none"

        self._result = None

    @classmethod
    def load(cls,
             signal: Union[str, Path],
             openbeam: Union[str, Path],
             L: Optional[float] = None,
             time_col: str = "time",
             signal_col: str = "signal",
             openbeam_col: str = "signal") -> 'Workflow':
        """
        Load signal and open beam data from CSV files.

        Parameters
        ----------
        signal : str or Path
            Path to sample signal CSV file
        openbeam : str or Path
            Path to open beam CSV file
        L : float, optional
            Flight path length in meters (for wavelength conversion)
        time_col : str
            Column name for time-of-flight data
        signal_col : str
            Column name for signal intensity in sample file
        openbeam_col : str
            Column name for signal intensity in openbeam file

        Returns
        -------
        workflow : Workflow
            New workflow instance with loaded data
        """
        workflow = cls()

        # Load signal data
        signal_df = pd.read_csv(signal)
        workflow._time_raw = signal_df[time_col].values
        workflow._signal_raw = signal_df[signal_col].values

        # Load open beam data
        openbeam_df = pd.read_csv(openbeam)
        workflow._openbeam_raw = openbeam_df[openbeam_col].values

        workflow._L = L

        return workflow

    @classmethod
    def load_arrays(cls,
                    signal: np.ndarray,
                    openbeam: np.ndarray,
                    time: np.ndarray,
                    L: Optional[float] = None) -> 'Workflow':
        """
        Load signal and open beam data from numpy arrays.

        Parameters
        ----------
        signal : np.ndarray
            Sample signal intensity, shape (n,)
        openbeam : np.ndarray
            Open beam intensity, shape (n,)
        time : np.ndarray
            Time-of-flight values, shape (n,)
        L : float, optional
            Flight path length in meters (for wavelength conversion)

        Returns
        -------
        workflow : Workflow
            New workflow instance with loaded data
        """
        workflow = cls()
        workflow._signal_raw = np.asarray(signal).squeeze()
        workflow._openbeam_raw = np.asarray(openbeam).squeeze()
        workflow._time_raw = np.asarray(time).squeeze()
        workflow._L = L

        return workflow

    def interpolate(self,
                   tmax: float,
                   nrep: int,
                   plot: bool = False) -> 'Workflow':
        """
        Interpolate readout gaps and merge repetitions.

        Parameters
        ----------
        tmax : float
            Maximum time-of-flight value
        nrep : int
            Number of chopper repetitions
        plot : bool
            If True, plot individual repetitions and merged result

        Returns
        -------
        self : Workflow
            Returns self for method chaining
        """
        if self._signal_raw is None:
            raise ValueError("No data loaded. Call load() or load_arrays() first.")

        # Process signal and openbeam
        self._signal_processed, self._time_processed = interpolate_noreadoutgaps(
            self._signal_raw, self._time_raw, tmax, nrep, plot_flag=plot
        )
        self._openbeam_processed, _ = interpolate_noreadoutgaps(
            self._openbeam_raw, self._time_raw, tmax, nrep, plot_flag=False
        )

        return self

    def convolve(self,
                chopper: Literal["POLDI", "4x10", "5x8", "3x14"] = "POLDI",
                noise_level: float = 0.1,
                filter_type: Literal["none", "LowPass", "LowPassBu", "LowPassGa"] = "none") -> 'Workflow':
        """
        Set up chopper response function for deconvolution.

        Parameters
        ----------
        chopper : str
            Chopper configuration: 'POLDI' (8 slits), '4x10', '5x8', or '3x14'
        noise_level : float
            Wiener filter regularization parameter (higher = more smoothing)
        filter_type : str
            Frequency domain filter: 'none', 'LowPass', 'LowPassBu', 'LowPassGa'

        Returns
        -------
        self : Workflow
            Returns self for method chaining
        """
        if self._time_processed is None:
            raise ValueError("No processed data. Call interpolate() first.")

        # Get chopper time delays
        chopper_functions = {
            "POLDI": fobi_poldi_time_delays,
            "4x10": fobi_4x10_time_delays,
            "5x8": fobi_5x8_time_delays,
            "3x14": fobi_3x14_time_delays,
        }

        if chopper not in chopper_functions:
            raise ValueError(f"Unknown chopper: {chopper}. Choose from {list(chopper_functions.keys())}")

        self._chopper_response = chopper_functions[chopper](self._time_processed)
        self._chopper_id = chopper
        self._noise_level = noise_level
        self._filter_type = filter_type

        return self

    def reconstruct(self, roll: int = 0) -> ReconstructionResult:
        """
        Perform Wiener deconvolution to reconstruct the spectrum.

        Parameters
        ----------
        roll : int
            Circular shift to apply to reconstructed spectra

        Returns
        -------
        result : ReconstructionResult
            Reconstruction results with chainable plotting/saving methods
        """
        if self._chopper_response is None:
            raise ValueError("Chopper response not set. Call convolve() first.")

        # Number of slits for normalization
        nslits_map = {"POLDI": 8, "4x10": 10, "5x8": 8, "3x14": 14}
        nslits = nslits_map[self._chopper_id]

        # Wiener deconvolution on signal and openbeam
        signal_rec = nslits * wiener_deconvolution(
            self._signal_processed,
            self._chopper_response,
            self._noise_level,
            self._filter_type
        )

        openbeam_rec = nslits * wiener_deconvolution(
            self._openbeam_processed,
            self._chopper_response,
            self._noise_level,
            self._filter_type
        )

        # Calculate transmission
        with np.errstate(divide='ignore', invalid='ignore'):
            transmission = signal_rec / openbeam_rec
            transmission[~np.isfinite(transmission)] = 1.0

        # Apply circular shift
        if roll != 0:
            signal_rec = np.roll(signal_rec, roll)
            openbeam_rec = np.roll(openbeam_rec, roll)
            transmission = np.roll(transmission, roll)

        # Calculate wavelength if L is provided
        wavelength = None
        if self._L is not None:
            # λ = h*t/(m*L) where h/m = 3.956 for neutrons
            # λ (Å) = 3956 * t (ms) / L (m)
            wavelength = 3.956 * (self._time_processed / 1000) / self._L

        # Create result object
        self._result = ReconstructionResult(
            transmission=transmission,
            signal=signal_rec,
            openbeam=openbeam_rec,
            time=self._time_processed,
            wavelength=wavelength,
            metadata={
                'chopper': self._chopper_id,
                'noise_level': self._noise_level,
                'filter_type': self._filter_type,
                'L': self._L,
                'roll': roll,
            }
        )

        return self._result
