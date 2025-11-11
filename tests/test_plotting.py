"""
Test Plotting Functionality
============================

Tests to ensure plots are generated correctly with proper data ranges.
"""

import numpy as np
import pytest
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

from fobi import Workflow


@pytest.fixture
def mock_iron_data():
    """Generate mock iron powder data with realistic Bragg edges."""
    np.random.seed(42)

    L = 9
    tmax = 10000
    nrep = 8
    nbins = 1000 * nrep

    t = np.linspace(0, tmax, nbins)
    wavelength = 3.956 * (t / 1000) / L

    # Iron BCC edges
    edges = [
        (2.027, 0.10, 0.25),  # (110)
        (2.866, 0.12, 0.20),  # (200)
        (4.050, 0.15, 0.30),  # (211)
    ]

    transmission = np.ones_like(wavelength) * 0.6
    for pos, width, height in edges:
        transmission += height / (1 + np.exp(-(wavelength - pos) / width))

    openbeam_base = np.ones_like(t) * 1000
    openbeam = openbeam_base + np.random.randn(len(t)) * 0.02 * openbeam_base
    signal_base = transmission * openbeam_base
    signal = signal_base + np.random.randn(len(t)) * 0.02 * signal_base

    return t, signal, openbeam, L, tmax, nrep


class TestWavelengthCalculation:
    """Test wavelength calculation is correct after merging."""

    def test_wavelength_range(self, mock_iron_data):
        """Test wavelength spans expected range."""
        t, signal, openbeam, L, tmax, nrep = mock_iron_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        # Expected wavelength range
        expected_max = 3.956 * (tmax / 1000) / L

        assert result.wavelength is not None
        assert result.wavelength[0] >= 0
        assert result.wavelength[-1] <= expected_max * 1.1  # Allow 10% margin
        assert result.wavelength[-1] > 4.0  # Should reach at least 4 Angstroms

        print(f"Wavelength range: [{result.wavelength.min():.3f}, {result.wavelength.max():.3f}] Å")

    def test_wavelength_scaling(self, mock_iron_data):
        """Test wavelength is properly scaled after merging repetitions."""
        t, signal, openbeam, L, tmax, nrep = mock_iron_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        # After merging, time_processed goes from 0 to tmax/nrep
        # But wavelength should go from 0 to wavelength_max (using full time range)
        time_max_processed = result.time.max()
        assert time_max_processed < tmax  # Time is compressed

        # But wavelength should use full range
        wavelength_max = result.wavelength.max()
        expected_wavelength_max = 3.956 * (tmax / 1000) / L

        # Should be close to expected (within 5%)
        assert abs(wavelength_max - expected_wavelength_max) < expected_wavelength_max * 0.05


class TestPlotDataVisibility:
    """Test that plots contain visible data in expected ranges."""

    def test_plot_has_data_in_typical_range(self, mock_iron_data):
        """Test plot has data in typical Bragg edge range (2-6 Å)."""
        t, signal, openbeam, L, tmax, nrep = mock_iron_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        # Check data in typical range
        in_range = (result.wavelength >= 2) & (result.wavelength <= 6)
        num_points_in_range = in_range.sum()

        assert num_points_in_range > 100, \
            f"Only {num_points_in_range} points in 2-6 Å range - plots will appear empty!"

        print(f"Points in visible range (2-6 Å): {num_points_in_range} / {len(result.wavelength)}")

    def test_manual_plot_has_content(self, mock_iron_data):
        """Test that manually creating a plot produces visible content."""
        t, signal, openbeam, L, tmax, nrep = mock_iron_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        # Create manual plot
        fig, ax = plt.subplots()
        ax.plot(result.wavelength, result.transmission)
        ax.set_xlim(2, 6)  # Typical viewing range

        # Check axis limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        assert xlim == (2, 6)
        assert ylim[0] < ylim[1]  # Y-axis should have range
        assert ylim[1] - ylim[0] > 0.1  # Should have reasonable y-range

        # Check line data
        lines = ax.get_lines()
        assert len(lines) == 1

        line_xdata = lines[0].get_xdata()
        line_ydata = lines[0].get_ydata()

        # Check data is in visible x-range
        visible_mask = (line_xdata >= 2) & (line_xdata <= 6)
        visible_points = visible_mask.sum()

        assert visible_points > 100, \
            f"Only {visible_points} points visible in plot - will appear empty!"

        plt.close(fig)

    def test_plot_method_produces_correct_ranges(self, mock_iron_data):
        """Test built-in plot method uses correct ranges."""
        t, signal, openbeam, L, tmax, nrep = mock_iron_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        # This should not raise and should produce a valid plot
        # (matplotlib in Agg mode won't show but will create figure)
        result.plot(what="transmission", x_axis="wavelength")

        # Check current figure
        fig = plt.gcf()
        axes = fig.get_axes()

        assert len(axes) > 0, "No axes created in plot"

        ax = axes[0]
        lines = ax.get_lines()

        assert len(lines) > 0, "No data lines in plot"

        # Check data
        line = lines[0]
        xdata = line.get_xdata()
        ydata = line.get_ydata()

        assert len(xdata) > 0, "No x-data in plot"
        assert len(ydata) > 0, "No y-data in plot"
        assert np.max(xdata) > 2, "X-data range too small - plot will be empty"

        plt.close(fig)


class TestComparisonPlots:
    """Test comparison plots work correctly."""

    def test_comparison_with_true_transmission(self, mock_iron_data):
        """Test comparison plot between reconstruction and true transmission."""
        t, signal, openbeam, L, tmax, nrep = mock_iron_data

        # Calculate true transmission
        wavelength_true = 3.956 * (t / 1000) / L
        edges = [(2.027, 0.10, 0.25), (2.866, 0.12, 0.20), (4.050, 0.15, 0.30)]
        transmission_true = np.ones_like(wavelength_true) * 0.6
        for pos, width, height in edges:
            transmission_true += height / (1 + np.exp(-(wavelength_true - pos) / width))

        # Reconstruct
        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1)
            .reconstruct())

        # Interpolate true transmission onto reconstructed grid
        true_trans_interp = np.interp(result.wavelength, wavelength_true, transmission_true)

        # Create comparison plot
        fig, ax = plt.subplots()
        ax.plot(result.wavelength, true_trans_interp, 'k-', label='True')
        ax.plot(result.wavelength, result.transmission, 'r-', label='Reconstructed')
        ax.set_xlim(2, 6)
        ax.legend()

        # Check both lines are visible
        lines = ax.get_lines()
        assert len(lines) == 2, "Both lines should be plotted"

        for i, line in enumerate(lines):
            xdata = line.get_xdata()
            ydata = line.get_ydata()

            visible = (xdata >= 2) & (xdata <= 6)
            visible_points = visible.sum()

            assert visible_points > 100, \
                f"Line {i} has only {visible_points} visible points!"

        plt.close(fig)


class TestAllFilters:
    """Test all filter types produce valid plots."""

    @pytest.mark.parametrize("filter_type", ["none", "LowPass", "LowPassBu", "LowPassGa"])
    def test_filter_produces_valid_plot(self, mock_iron_data, filter_type):
        """Test each filter type produces plottable results."""
        t, signal, openbeam, L, tmax, nrep = mock_iron_data

        result = (Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1, filter_type=filter_type)
            .reconstruct())

        # Check wavelength range
        assert result.wavelength.max() > 4.0, \
            f"Filter {filter_type}: wavelength range too small"

        # Check data in visible range
        visible = (result.wavelength >= 2) & (result.wavelength <= 6)
        assert visible.sum() > 100, \
            f"Filter {filter_type}: insufficient visible data points"

        # Try to plot
        result.plot(what="transmission", x_axis="wavelength")
        plt.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
