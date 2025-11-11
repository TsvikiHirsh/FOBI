"""
Utility functions for edge fitting.
"""

import numpy as np


def find_nearest(array: np.ndarray, value: float) -> int:
    """
    Find the index of the nearest value in an array.

    Parameters
    ----------
    array : np.ndarray
        Input array to search
    value : float
        Target value to find

    Returns
    -------
    idx : int
        Index of nearest value

    Examples
    --------
    >>> arr = np.array([1, 3, 5, 7, 9])
    >>> find_nearest(arr, 6.2)
    2  # Index of value 5
    """
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx
