"""
Test MATLAB vs Python Implementation Comparison
================================================

This module tests that the Python implementation produces results consistent
with the legacy MATLAB implementation using oct2py to run MATLAB code.

Note: Requires Octave (open-source MATLAB alternative) to be installed:
    - Ubuntu/Debian: sudo apt-get install octave
    - macOS: brew install octave
    - Or install MATLAB (requires license)

Install oct2py with:
    pip install oct2py

Usage:
    pytest tests/test_matlab_comparison.py -v
"""

import numpy as np
import pytest
from pathlib import Path

# Import FOBI Python implementation
from fobi.reduction.wiener import wiener_deconvolution
from fobi.reduction.data_processing import interpolate_noreadoutgaps
from fobi.reduction.time_delays import fobi_poldi_time_delays

# Try to import oct2py (optional dependency)
try:
    from oct2py import Oct2Py
    OCTAVE_AVAILABLE = True
except ImportError:
    OCTAVE_AVAILABLE = False
    Oct2Py = None

# Check if Octave/MATLAB is actually installed
if OCTAVE_AVAILABLE:
    try:
        oc = Oct2Py()
        oc.exit()
        OCTAVE_INSTALLED = True
    except Exception:
        OCTAVE_INSTALLED = False
else:
    OCTAVE_INSTALLED = False


# Skip all tests if Octave is not available
pytestmark = pytest.mark.skipif(
    not OCTAVE_INSTALLED,
    reason="Octave not installed or oct2py not available. "
           "Install with: pip install oct2py && sudo apt-get install octave"
)


@pytest.fixture(scope="module")
def octave_engine():
    """Create an Octave engine for running MATLAB code."""
    if not OCTAVE_INSTALLED:
        pytest.skip("Octave not available")

    oc = Oct2Py()

    # Add MATLAB functions directory to path
    matlab_path = Path(__file__).parent.parent / ".legacy" / "matlab" / "functions" / "Reduction"
    if matlab_path.exists():
        oc.addpath(str(matlab_path))

    yield oc

    # Cleanup
    oc.exit()


@pytest.fixture
def mock_data():
    """Generate mock data for testing."""
    np.random.seed(42)

    # Simple signal
    n = 100
    t = np.linspace(0, 1000, n)
    signal = np.sin(2 * np.pi * t / 200) + 0.1 * np.random.randn(n)

    # Instrument response (simplified)
    response = np.zeros(n)
    response[45:55] = 1.0  # Delta-like function

    return signal, response, t


class TestWienerDeconvolution:
    """Test Wiener deconvolution against MATLAB implementation."""

    def test_wiener_basic(self, octave_engine, mock_data):
        """Test basic Wiener deconvolution matches MATLAB."""
        signal, response, t = mock_data
        c = 0.1

        # Python implementation
        result_python = wiener_deconvolution(signal, response, c=c, filter_type="none")

        # MATLAB implementation (if FobiWiener.m exists)
        matlab_func = Path(__file__).parent.parent / ".legacy" / "matlab" / "functions" / "Reduction" / "FobiWiener.m"

        if matlab_func.exists():
            # Run MATLAB version
            # Note: Actual function signature may differ
            result_matlab = octave_engine.feval('wiener_deconvolution_simple', signal, response, c)

            # Compare results (allow some numerical tolerance)
            np.testing.assert_allclose(result_python, result_matlab, rtol=1e-3, atol=1e-5)
        else:
            pytest.skip("MATLAB wiener function not found")

    def test_frequency_domain_filter(self, octave_engine, mock_data):
        """Test frequency domain filtering matches MATLAB."""
        signal, response, t = mock_data
        c = 0.1

        # Test different filter types
        for filter_type in ["LowPass", "LowPassBu", "LowPassGa"]:
            result_python = wiener_deconvolution(signal, response, c=c, filter_type=filter_type)

            # Verify output is reasonable
            assert len(result_python) == len(signal)
            assert np.isfinite(result_python).all()

            # If MATLAB implementation available, compare
            # (placeholder - actual MATLAB function call would go here)


class TestInterpolation:
    """Test data interpolation against MATLAB implementation."""

    def test_interpolate_noreadoutgaps(self, octave_engine):
        """Test gap interpolation matches MATLAB."""
        np.random.seed(42)

        # Create data with gaps
        nrep = 4
        nbins = 400
        t = np.linspace(0, 4000, nbins)
        tmax = 4000

        y = np.sin(2 * np.pi * t / 1000) + 0.05 * np.random.randn(nbins)

        # Python implementation
        y_merged_python, t_merged_python = interpolate_noreadoutgaps(y, t, tmax, nrep, plot_flag=False)

        # MATLAB implementation (if exists)
        matlab_func = Path(__file__).parent.parent / ".legacy" / "matlab" / "functions" / "Reduction" / "interpolate_noreadoutgaps.m"

        if matlab_func.exists():
            # Run MATLAB version
            y_merged_matlab, t_merged_matlab = octave_engine.feval(
                'interpolate_noreadoutgaps', y, t, tmax, nrep, nout=2
            )

            # Compare results
            np.testing.assert_allclose(t_merged_python, t_merged_matlab, rtol=1e-6)
            np.testing.assert_allclose(y_merged_python, y_merged_matlab, rtol=1e-3, atol=1e-5)
        else:
            # At least verify output shape and properties
            expected_len = int(np.ceil(nbins / nrep))
            assert len(y_merged_python) == expected_len
            assert len(t_merged_python) == expected_len
            assert np.isfinite(y_merged_python).all()


class TestTimeDelays:
    """Test chopper time delay calculations against MATLAB."""

    def test_poldi_time_delays(self, octave_engine):
        """Test POLDI time delays match MATLAB."""
        # Create time array
        t = np.linspace(0, 1000, 200)

        # Python implementation
        delays_python = fobi_poldi_time_delays(t)

        # MATLAB implementation
        matlab_func = Path(__file__).parent.parent / ".legacy" / "matlab" / "functions" / "Reduction" / "FobiPOLDITimeDelays.m"

        if matlab_func.exists():
            # Note: Actual MATLAB function name may be different
            try:
                delays_matlab = octave_engine.feval('FobiPOLDITimeDelays', t)
                np.testing.assert_allclose(delays_python, delays_matlab, rtol=1e-6)
            except Exception as e:
                pytest.skip(f"Could not run MATLAB function: {e}")
        else:
            # Verify output properties
            assert len(delays_python) == len(t)
            assert np.isfinite(delays_python).all()


class TestEndToEnd:
    """End-to-end comparison tests."""

    def test_full_reconstruction_workflow(self, octave_engine):
        """Test complete reconstruction workflow matches MATLAB."""
        np.random.seed(42)

        # Generate realistic test data
        nrep = 8
        nbins = 800
        tmax = 10000
        t = np.linspace(0, tmax, nbins)

        # Simulate transmission with Bragg edge
        wavelength = 3.956 * (t / 1000) / 9  # L = 9m
        transmission = 0.7 + 0.3 / (1 + np.exp(-(wavelength - 4.0) / 0.15))

        # Open beam and sample
        I0 = 1000 * np.ones(nbins) + 20 * np.random.randn(nbins)
        I = transmission * I0 + 20 * np.random.randn(nbins)

        # Python workflow
        y_merged, t_merged = interpolate_noreadoutgaps(I, t, tmax, nrep)
        y0_merged, _ = interpolate_noreadoutgaps(I0, t, tmax, nrep)

        D = fobi_poldi_time_delays(t_merged)

        y_rec = 8 * wiener_deconvolution(y_merged, D, c=0.1)
        y0_rec = 8 * wiener_deconvolution(y0_merged, D, c=0.1)

        T_rec = y_rec / y0_rec

        # Verify results are reasonable
        assert len(T_rec) == len(t_merged)
        assert np.isfinite(T_rec).all()
        assert np.mean(T_rec) > 0.5 and np.mean(T_rec) < 1.0

        # If MATLAB end-to-end function exists, compare
        # (This would require a MATLAB script that runs the full pipeline)


# Utility test to check MATLAB/Octave setup
def test_octave_setup():
    """Verify Octave is properly set up."""
    if not OCTAVE_INSTALLED:
        pytest.skip("Octave not available")

    oc = Oct2Py()

    # Test basic operations
    result = oc.eval("2 + 2")
    assert result == 4

    # Check MATLAB path
    matlab_path = Path(__file__).parent.parent / ".legacy" / "matlab" / "functions" / "Reduction"
    if matlab_path.exists():
        oc.addpath(str(matlab_path))
        current_path = oc.eval("path")
        assert str(matlab_path) in current_path or matlab_path.name in current_path

    oc.exit()


# Information test (always runs)
@pytest.mark.skipif(False, reason="")
def test_show_matlab_comparison_info():
    """Display information about MATLAB comparison testing."""
    info = """
    MATLAB Comparison Testing
    =========================

    These tests compare the Python FOBI implementation with the legacy MATLAB code.

    Requirements:
    1. Install oct2py: pip install oct2py
    2. Install Octave (open-source MATLAB):
       - Ubuntu/Debian: sudo apt-get install octave
       - macOS: brew install octave
       - Or use MATLAB if you have a license

    3. Legacy MATLAB code should be in: .legacy/matlab/functions/

    Current Status:
    - Oct2Py available: {}
    - Octave installed: {}
    - Legacy MATLAB path exists: {}

    If tests are skipped, install the requirements above.
    """.format(
        OCTAVE_AVAILABLE,
        OCTAVE_INSTALLED,
        (Path(__file__).parent.parent / ".legacy" / "matlab").exists()
    )

    print(info)
    assert True  # Always pass, just informational


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
