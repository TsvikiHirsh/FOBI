"""
Tests for FOBI utilities module.
"""

import pytest
import numpy as np

from fobi.utils import generate_test_data
from fobi.utils.synthetic_data import generate_chopper_modulated_data


class TestGenerateTestData:
    """Tests for synthetic test data generation."""

    def test_basic_generation(self):
        """Test basic data generation."""
        I, I0, t = generate_test_data(
            shape=(10, 10, 100),
            edge_position=50,
            edge_width=5,
            edge_height=0.3,
        )

        assert I.shape == (10, 10, 100)
        assert I0.shape == (10, 10, 100)
        assert len(t) == 100

        # Check data is physical (non-negative)
        assert np.all(I >= 0)
        assert np.all(I0 >= 0)

    def test_edge_in_transmission(self):
        """Test that edge is present in transmission."""
        I, I0, t = generate_test_data(
            shape=(5, 5, 500),
            edge_position=250,
            edge_width=10,
            edge_height=0.5,
            noise_level=0.01,
        )

        # Compute transmission for center pixel
        with np.errstate(divide='ignore', invalid='ignore'):
            trans = I[2, 2, :] / I0[2, 2, :]
            trans[~np.isfinite(trans)] = 1.0

        # Transmission should decrease at edge position
        before_edge = np.mean(trans[200:240])
        after_edge = np.mean(trans[260:300])

        assert before_edge > after_edge  # Step down

    def test_spatial_variation(self):
        """Test spatial variation in edge parameters."""
        I, I0, t = generate_test_data(
            shape=(20, 20, 200),
            edge_position=100,
            add_spatial_variation=True,
        )

        # Extract edges from different pixels
        trans1 = I[0, 0, :] / (I0[0, 0, :] + 1e-10)
        trans2 = I[19, 19, :] / (I0[19, 19, :] + 1e-10)

        # Edge positions should be slightly different
        edge1 = np.argmin(np.diff(trans1))
        edge2 = np.argmin(np.diff(trans2))

        # Should have some difference due to spatial variation
        assert abs(edge1 - edge2) > 0

    def test_no_spatial_variation(self):
        """Test data without spatial variation."""
        I, I0, t = generate_test_data(
            shape=(10, 10, 200),
            edge_position=100,
            add_spatial_variation=False,
        )

        # All pixels should have same edge position
        edges = []
        for i in range(5):
            for j in range(5):
                trans = I[i, j, :] / (I0[i, j, :] + 1e-10)
                edge_pos = np.argmin(np.diff(trans))
                edges.append(edge_pos)

        edges = np.array(edges)
        # Very small variation (only due to noise)
        assert np.std(edges) < 5


class TestGenerateChopperModulatedData:
    """Tests for chopper-modulated synthetic data."""

    def test_basic_chopper_data(self):
        """Test basic chopper data generation."""
        I_mod, I0_mod, t, tmax = generate_chopper_modulated_data(
            shape=(5, 5, 400),
            nrep=8,
            chopper_id='POLDI',
        )

        assert I_mod.shape == (5, 5, 400)
        assert I0_mod.shape == (5, 5, 400)
        assert len(t) == 400
        assert tmax > 0

        # Check data is physical
        assert np.all(I_mod >= 0)
        assert np.all(I0_mod >= 0)

    def test_different_choppers(self):
        """Test different chopper configurations."""
        for chopper_id in ['POLDI', '4x10', '5x8', '3x14']:
            I_mod, I0_mod, t, tmax = generate_chopper_modulated_data(
                shape=(3, 3, 200),
                nrep=4,
                chopper_id=chopper_id,
                noise_level=0.02,
            )

            assert I_mod.shape == (3, 3, 200)
            assert np.all(np.isfinite(I_mod))

    def test_invalid_chopper(self):
        """Test that invalid chopper ID raises error."""
        with pytest.raises(ValueError):
            generate_chopper_modulated_data(
                shape=(3, 3, 100),
                nrep=4,
                chopper_id='INVALID',
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
