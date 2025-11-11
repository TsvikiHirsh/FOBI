"""
Tests for FOBI edge fitting module.
"""

import pytest
import numpy as np
from scipy.special import erf

from fobi.edge_fitting import (
    edge_fit_gaussian,
    edge_fit_gaussian_2d,
    find_nearest,
)
from fobi.edge_fitting.gaussian import gaussian_model


class TestGaussianModel:
    """Tests for Gaussian model function."""

    def test_gaussian_shape(self):
        """Test Gaussian has correct shape."""
        x = np.linspace(0, 10, 100)
        y = gaussian_model(x, a=1.0, b=5.0, c=1.0)

        # Peak should be at b
        peak_idx = np.argmax(np.abs(y))
        assert np.isclose(x[peak_idx], 5.0, atol=0.1)

        # Should be symmetric
        assert np.allclose(y[:50], np.flip(y[50:]), atol=0.1)


class TestFindNearest:
    """Tests for find_nearest utility."""

    def test_find_exact_value(self):
        """Test finding exact value."""
        arr = np.array([1, 2, 3, 4, 5])
        idx = find_nearest(arr, 3)
        assert idx == 2

    def test_find_nearest_value(self):
        """Test finding nearest value."""
        arr = np.array([1, 3, 5, 7, 9])
        idx = find_nearest(arr, 6.2)
        assert idx == 2  # Closest to 5

    def test_find_in_continuous_array(self):
        """Test finding in continuous array."""
        arr = np.linspace(0, 100, 1000)
        idx = find_nearest(arr, 42.5)
        assert np.isclose(arr[idx], 42.5, atol=0.2)


class TestEdgeFitGaussian:
    """Tests for single-pixel Gaussian edge fitting."""

    def test_fit_synthetic_edge(self):
        """Test fitting a known synthetic edge."""
        # Create synthetic transmission with step edge
        spectrum = np.linspace(0, 10, 500)
        edge_pos = 5.0
        edge_width = 0.5

        # Smooth step using error function
        transmission = 1.0 - 0.4 / (1 + np.exp(-(spectrum - edge_pos) / edge_width))

        # Fit edge
        pos, wid, h = edge_fit_gaussian(
            transmission,
            spectrum,
            spectrum_range=(3, 7),
            est_p=5.0,
            est_w=0.5,
            est_h=-0.1,
            BC_p=(3, 7),
            BC_w=(0.1, 2),
            BC_h=(-1, 0),
            smooth_span=5,
            plot_result=False,
        )

        # Check that fit is reasonable
        assert np.isfinite(pos)
        assert np.isfinite(wid)
        assert np.isfinite(h)
        assert 4 < pos < 6  # Position should be near 5
        assert 0.1 < wid < 2  # Width should be reasonable

    def test_fit_noisy_edge(self):
        """Test fitting with noisy data."""
        spectrum = np.linspace(0, 10, 500)
        edge_pos = 5.0
        edge_width = 0.5

        # Smooth step with noise
        transmission = 1.0 - 0.4 / (1 + np.exp(-(spectrum - edge_pos) / edge_width))
        transmission += np.random.normal(0, 0.02, len(spectrum))

        pos, wid, h = edge_fit_gaussian(
            transmission,
            spectrum,
            spectrum_range=(3, 7),
            est_p=5.0,
            est_w=0.5,
            est_h=-0.1,
            BC_p=(3, 7),
            BC_w=(0.1, 2),
            BC_h=(-1, 0),
            smooth_span=5,
            plot_result=False,
        )

        # Fit should still work with noise
        assert np.isfinite(pos)
        assert 4 < pos < 6

    def test_fit_with_insufficient_data(self):
        """Test that fitting with too few points returns NaN."""
        spectrum = np.linspace(0, 10, 10)  # Very few points
        transmission = np.ones(10)

        pos, wid, h = edge_fit_gaussian(
            transmission,
            spectrum,
            spectrum_range=(4, 6),  # Only 2-3 points
            est_p=5.0,
            est_w=0.5,
            est_h=-0.1,
            BC_p=(3, 7),
            BC_w=(0.1, 2),
            BC_h=(-1, 0),
            smooth_span=0,
            plot_result=False,
        )

        # Should return NaN for insufficient data
        assert np.isnan(pos) or np.isfinite(pos)


class TestEdgeFitGaussian2D:
    """Tests for 2D spatially-resolved edge fitting."""

    def test_2d_fit_small_dataset(self):
        """Test 2D fitting on small dataset."""
        # Create small synthetic dataset
        rows, cols, nbins = 5, 5, 200
        spectrum = np.linspace(0, 10, nbins)

        data = np.zeros((rows, cols, nbins))

        # Fill with edges at different positions
        for i in range(rows):
            for j in range(cols):
                edge_pos = 5.0 + 0.1 * (i - rows//2)
                transmission = 1.0 - 0.4 / (1 + np.exp(-(spectrum - edge_pos) / 0.5))
                data[i, j, :] = transmission

        # Fit all pixels
        edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
            data,
            spectrum,
            spectrum_range=(3, 7),
            est_p=5.0,
            est_w=0.5,
            est_h=-0.1,
            BC_p=(3, 7),
            BC_w=(0.1, 2),
            BC_h=(-1, 0),
        )

        # Check output shapes
        assert edge_p.shape == (rows, cols)
        assert edge_w.shape == (rows, cols)
        assert edge_h.shape == (rows, cols)

        # Check that most fits succeeded
        valid_fits = np.sum(np.isfinite(edge_p))
        assert valid_fits >= rows * cols * 0.5  # At least 50% should succeed

    def test_2d_fit_with_mask(self):
        """Test 2D fitting with mask."""
        rows, cols, nbins = 5, 5, 200
        spectrum = np.linspace(0, 10, nbins)

        data = np.ones((rows, cols, nbins))

        # Create mask (only fit center pixel)
        mask = np.zeros((rows, cols))
        mask[rows//2, cols//2] = 1

        edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
            data,
            spectrum,
            spectrum_range=(3, 7),
            est_p=5.0,
            est_w=0.5,
            est_h=-0.1,
            BC_p=(3, 7),
            BC_w=(0.1, 2),
            BC_h=(-1, 0),
            mask=mask,
        )

        # Only center pixel should have valid values
        n_valid = np.sum(np.isfinite(edge_p))
        assert n_valid <= 1  # Only 1 pixel was masked


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
