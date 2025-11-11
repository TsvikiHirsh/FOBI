"""
Test New Workflow API
=====================

Tests for the new object-oriented Workflow API with method chaining.
"""

import numpy as np
import pytest
import tempfile
from pathlib import Path
import pandas as pd

from fobi import Workflow, ReconstructionResult


@pytest.fixture
def mock_1d_data():
    """Generate mock 1D data for testing."""
    np.random.seed(42)

    # Parameters
    L = 9  # meters
    tmax = 10000  # microseconds
    nrep = 8
    nbins = 800

    # Time array
    t = np.linspace(0, tmax, nbins)

    # Wavelength
    wavelength = 3.956 * (t / 1000) / L

    # Transmission with Bragg edge
    edge_position = 4.0
    edge_width = 0.15
    edge_height = 0.3
    transmission = 0.7 + edge_height / (1 + np.exp(-(wavelength - edge_position) / edge_width))

    # Open beam
    openbeam_base = np.ones_like(t) * 1000
    openbeam = openbeam_base + np.random.randn(len(t)) * 0.02 * openbeam_base

    # Sample signal
    signal_base = transmission * openbeam_base
    signal = signal_base + np.random.randn(len(t)) * 0.02 * signal_base

    return t, signal, openbeam, L, tmax, nrep


class TestWorkflowLoading:
    """Test data loading methods."""

    def test_load_arrays(self, mock_1d_data):
        """Test loading from numpy arrays."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        workflow = Workflow.load_arrays(
            signal=signal,
            openbeam=openbeam,
            time=t,
            L=L
        )

        assert workflow._signal_raw is not None
        assert workflow._openbeam_raw is not None
        assert workflow._time_raw is not None
        assert workflow._L == L
        assert len(workflow._signal_raw) == len(signal)

    def test_load_csv(self, mock_1d_data, tmp_path):
        """Test loading from CSV files."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        # Save to CSV
        signal_file = tmp_path / "signal.csv"
        openbeam_file = tmp_path / "openbeam.csv"

        pd.DataFrame({'time': t, 'signal': signal}).to_csv(signal_file, index=False)
        pd.DataFrame({'time': t, 'signal': openbeam}).to_csv(openbeam_file, index=False)

        # Load
        workflow = Workflow.load(
            signal=signal_file,
            openbeam=openbeam_file,
            L=L
        )

        assert workflow._signal_raw is not None
        assert workflow._openbeam_raw is not None
        assert workflow._L == L

    def test_load_without_L(self, mock_1d_data):
        """Test loading without flight path length."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        workflow = Workflow.load_arrays(
            signal=signal,
            openbeam=openbeam,
            time=t
        )

        assert workflow._L is None


class TestWorkflowProcessing:
    """Test processing pipeline."""

    def test_interpolate(self, mock_1d_data):
        """Test interpolation step."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        workflow = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep))

        assert workflow._signal_processed is not None
        assert workflow._openbeam_processed is not None
        assert workflow._time_processed is not None
        assert len(workflow._signal_processed) < len(signal)  # Should be merged

    def test_interpolate_without_load(self):
        """Test that interpolate fails without loading data first."""
        workflow = Workflow()

        with pytest.raises(ValueError, match="No data loaded"):
            workflow.interpolate(tmax=10000, nrep=8)

    def test_convolve(self, mock_1d_data):
        """Test chopper response setup."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        workflow = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1))

        assert workflow._chopper_response is not None
        assert workflow._chopper_id == "POLDI"
        assert workflow._noise_level == 0.1

    def test_convolve_different_choppers(self, mock_1d_data):
        """Test different chopper configurations."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        for chopper in ["POLDI", "4x10", "5x8", "3x14"]:
            workflow = (Workflow
                .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
                .interpolate(tmax=tmax, nrep=nrep)
                .convolve(chopper=chopper, noise_level=0.1))

            assert workflow._chopper_id == chopper

    def test_convolve_invalid_chopper(self, mock_1d_data):
        """Test invalid chopper name."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        with pytest.raises(ValueError, match="Unknown chopper"):
            (Workflow
                .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
                .interpolate(tmax=tmax, nrep=nrep)
                .convolve(chopper="INVALID", noise_level=0.1))


class TestWorkflowReconstruction:
    """Test reconstruction step."""

    def test_reconstruct(self, mock_1d_data):
        """Test full reconstruction."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        assert isinstance(result, ReconstructionResult)
        assert result.transmission is not None
        assert result.signal is not None
        assert result.openbeam is not None
        assert result.time is not None
        assert result.wavelength is not None  # Should have wavelength since L was provided

    def test_reconstruct_without_wavelength(self, mock_1d_data):
        """Test reconstruction without wavelength conversion."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t)  # No L
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        assert result.wavelength is None

    def test_reconstruct_with_roll(self, mock_1d_data):
        """Test reconstruction with circular shift."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct(roll=10))

        assert result.metadata['roll'] == 10

    def test_reconstruct_different_filters(self, mock_1d_data):
        """Test different frequency filters."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        for filter_type in ["none", "LowPass", "LowPassBu", "LowPassGa"]:
            result = (Workflow
                .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
                .interpolate(tmax=tmax, nrep=nrep)
                .convolve(chopper="POLDI", noise_level=0.1, filter_type=filter_type)
                .reconstruct())

            assert result.metadata['filter_type'] == filter_type


class TestReconstructionResult:
    """Test ReconstructionResult object."""

    @pytest.fixture
    def result(self, mock_1d_data):
        """Create a result object for testing."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        return (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

    def test_result_attributes(self, result):
        """Test result has all required attributes."""
        assert hasattr(result, 'transmission')
        assert hasattr(result, 'signal')
        assert hasattr(result, 'openbeam')
        assert hasattr(result, 'time')
        assert hasattr(result, 'wavelength')
        assert hasattr(result, 'metadata')

    def test_save_csv(self, result, tmp_path):
        """Test saving to CSV."""
        output_file = tmp_path / "output.csv"
        result.save(output_file, format='csv')

        assert output_file.exists()

        # Load and check
        df = pd.read_csv(output_file)
        assert 'time' in df.columns
        assert 'transmission' in df.columns
        assert 'wavelength' in df.columns

    def test_save_npy(self, result, tmp_path):
        """Test saving to numpy format."""
        output_file = tmp_path / "output.npy"
        result.save(output_file, format='npy')

        assert output_file.exists()

        # Load and check
        data = np.load(output_file, allow_pickle=True).item()
        assert 'time' in data
        assert 'transmission' in data
        assert 'metadata' in data

    def test_plot_transmission(self, result):
        """Test plotting transmission."""
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend for testing

        # Should not raise
        result.plot(what="transmission", x_axis="time")
        result.plot(what="transmission", x_axis="wavelength")

    def test_plot_all(self, result):
        """Test plotting all results."""
        import matplotlib
        matplotlib.use('Agg')

        # Should not raise
        result.plot(what="all", x_axis="wavelength")

    def test_plot_without_wavelength(self, mock_1d_data):
        """Test plotting fails without wavelength when requested."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t)  # No L
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        with pytest.raises(ValueError, match="Wavelength not available"):
            result.plot(what="transmission", x_axis="wavelength")


class TestMethodChaining:
    """Test that method chaining works correctly."""

    def test_full_chain(self, mock_1d_data):
        """Test complete method chain."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        # Should work in one go
        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1, filter_type="LowPassGa")
            .reconstruct(roll=0))

        assert isinstance(result, ReconstructionResult)

    def test_step_by_step(self, mock_1d_data):
        """Test building workflow step by step."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        # Build step by step
        workflow = Workflow.load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
        workflow = workflow.interpolate(tmax=tmax, nrep=nrep)
        workflow = workflow.convolve(chopper="POLDI", noise_level=0.1)
        result = workflow.reconstruct()

        assert isinstance(result, ReconstructionResult)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_workflow(self):
        """Test empty workflow."""
        workflow = Workflow()

        assert workflow._signal_raw is None
        assert workflow._result is None

    def test_transmission_values(self, mock_1d_data):
        """Test that transmission values are reasonable."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        # Transmission should be between 0 and 1 (mostly)
        assert np.all(result.transmission > 0)
        assert np.all(result.transmission < 2)  # Allow some noise

        # Check no NaN or Inf
        assert np.all(np.isfinite(result.transmission))

    def test_metadata_preservation(self, mock_1d_data):
        """Test that metadata is correctly preserved."""
        t, signal, openbeam, L, tmax, nrep = mock_1d_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.5, filter_type="LowPassBu")
            .reconstruct(roll=15))

        assert result.metadata['chopper'] == "POLDI"
        assert result.metadata['noise_level'] == 0.5
        assert result.metadata['filter_type'] == "LowPassBu"
        assert result.metadata['L'] == L
        assert result.metadata['roll'] == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
