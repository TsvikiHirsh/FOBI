"""
Tests for FOBI reduction module.
"""

import pytest
import numpy as np
from fobi.reduction import (
    wiener_deconvolution,
    interpolate_noreadoutgaps,
    fobi_poldi_time_delays,
    fobi_4x10_time_delays,
    fobi_5x8_time_delays,
    fobi_3x14_time_delays,
    fobi_wiener_2d,
)


class TestWienerDeconvolution:
    """Tests for Wiener deconvolution function."""

    def test_basic_deconvolution(self):
        """Test basic deconvolution with delta function."""
        # Create signal and delta response
        n = 100
        signal = np.random.randn(n)
        response = np.zeros(n)
        response[n//2] = 1.0  # Delta function

        # Deconvolve
        result = wiener_deconvolution(signal, response, c=0.01)

        # Result should be similar to original signal
        assert result.shape == signal.shape
        assert np.all(np.isfinite(result))

    def test_filter_types(self):
        """Test different filter types."""
        n = 100
        signal = np.random.randn(n)
        response = np.random.randn(n)
        response = response / np.sum(response)

        for filter_type in ['none', 'LowPass', 'LowPassBu', 'LowPassGa']:
            result = wiener_deconvolution(signal, response, c=0.1, filter_type=filter_type)
            assert result.shape == signal.shape
            assert np.all(np.isfinite(result))

    def test_regularization_parameter(self):
        """Test effect of regularization parameter."""
        n = 100
        signal = np.random.randn(n)
        response = np.random.randn(n)

        # Different regularization values
        result_low = wiener_deconvolution(signal, response, c=0.001)
        result_high = wiener_deconvolution(signal, response, c=10.0)

        # Higher regularization should give smoother result
        assert np.std(result_high) < np.std(result_low)

    def test_column_vector_handling(self):
        """Test that function handles column vectors correctly."""
        n = 100
        signal = np.random.randn(n, 1)  # Column vector
        response = np.random.randn(n, 1)

        result = wiener_deconvolution(signal, response, c=0.1)

        assert result.shape == (n,)
        assert np.all(np.isfinite(result))


class TestInterpolateNoReadoutGaps:
    """Tests for interpolation and gap filling."""

    def test_basic_interpolation(self):
        """Test basic interpolation and merging."""
        nrep = 4
        nbins = 100
        n_total = nrep * nbins

        # Create test data
        t = np.linspace(0, 1000, n_total)
        y = np.sin(2 * np.pi * t / 500)

        y_merged, t_merged = interpolate_noreadoutgaps(
            y, t, tmax=1000, nrep=nrep, plot_flag=False
        )

        assert len(y_merged) == nbins
        assert len(t_merged) == nbins
        assert np.all(np.isfinite(y_merged))

    def test_repetition_averaging(self):
        """Test that repetitions are properly averaged."""
        nrep = 8
        nbins = 50
        n_total = nrep * nbins

        # Create identical repetitions
        single_rep = np.random.randn(nbins)
        y = np.tile(single_rep, nrep)
        t = np.linspace(0, 1000, n_total)

        y_merged, t_merged = interpolate_noreadoutgaps(
            y, t, tmax=1000, nrep=nrep, plot_flag=False
        )

        # Merged should be close to original (allowing for interpolation)
        assert np.allclose(y_merged, single_rep, atol=0.1)


class TestTimeDelays:
    """Tests for chopper time delay functions."""

    def test_poldi_delays(self):
        """Test POLDI time delays."""
        t = np.linspace(0, 1000, 500)
        D = fobi_poldi_time_delays(t)

        assert len(D) == len(t)
        assert np.sum(D) > 0  # Should have non-zero response
        assert np.all(D >= 0)  # All values should be non-negative

    def test_4x10_delays(self):
        """Test 4x10 chopper delays."""
        t = np.linspace(0, 1000, 500)
        D = fobi_4x10_time_delays(t)

        assert len(D) == len(t)
        assert np.sum(D) > 0
        assert np.all(D >= 0)

    def test_5x8_delays(self):
        """Test 5x8 chopper delays."""
        t = np.linspace(0, 1000, 500)
        D = fobi_5x8_time_delays(t)

        assert len(D) == len(t)
        assert np.sum(D) > 0
        assert np.all(D >= 0)

    def test_3x14_delays(self):
        """Test 3x14 chopper delays."""
        t = np.linspace(0, 1000, 500)
        D = fobi_3x14_time_delays(t)

        assert len(D) == len(t)
        assert np.sum(D) > 0
        assert np.all(D >= 0)


class TestFobiWiener2D:
    """Tests for 2D FOBI Wiener deconvolution."""

    def test_basic_2d_deconvolution(self):
        """Test 2D deconvolution with small dataset."""
        # Small test dataset
        rows, cols, nbins = 5, 5, 100
        nrep = 4

        I = np.random.rand(rows, cols, nbins)
        I0 = np.random.rand(rows, cols, nbins)
        t = np.linspace(0, 1000, nbins)

        T, y_rec, y0_rec, t_merged = fobi_wiener_2d(
            I, I0, t, tmax=1000, nrep=nrep, chopper_id='POLDI',
            c=0.1, flag_smooth=0
        )

        # Check output shapes
        assert T.shape[0] == rows
        assert T.shape[1] == cols
        assert len(t_merged) == T.shape[2]

        # Check all values are finite
        assert np.all(np.isfinite(T))
        assert np.all(np.isfinite(y_rec))
        assert np.all(np.isfinite(y0_rec))

    def test_chopper_configurations(self):
        """Test different chopper configurations."""
        rows, cols, nbins = 3, 3, 50
        nrep = 4

        I = np.random.rand(rows, cols, nbins)
        I0 = np.random.rand(rows, cols, nbins)
        t = np.linspace(0, 1000, nbins)

        for chopper_id in ['POLDI', '4x10', '5x8', '3x14']:
            T, _, _, t_merged = fobi_wiener_2d(
                I, I0, t, tmax=1000, nrep=nrep, chopper_id=chopper_id, c=0.1
            )

            assert T.shape[0] == rows
            assert T.shape[1] == cols
            assert np.all(np.isfinite(T))

    def test_invalid_chopper_id(self):
        """Test that invalid chopper ID raises error."""
        I = np.random.rand(3, 3, 50)
        I0 = np.random.rand(3, 3, 50)
        t = np.linspace(0, 1000, 50)

        with pytest.raises(ValueError):
            fobi_wiener_2d(
                I, I0, t, tmax=1000, nrep=4, chopper_id='INVALID', c=0.1
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
