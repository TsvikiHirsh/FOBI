"""
Chopper Time Delay Functions
=============================

Functions to calculate instrument response functions for different
chopper configurations used in time-of-flight neutron imaging.
"""

import numpy as np
from typing import Optional


def fobi_poldi_time_delays(time: np.ndarray) -> np.ndarray:
    """
    Calculate time delays for POLDI chopper configuration.

    The POLDI chopper has 8 slits at specific angular positions that
    create a characteristic time-delay pattern in the TOF spectrum.

    Parameters
    ----------
    time : np.ndarray
        Time-of-flight array

    Returns
    -------
    D : np.ndarray
        Time delay response function (instrument response)

    Notes
    -----
    POLDI slit angles (in degrees from closed position):
    [0, 9.363, 21.475, 37.039, 50.417, 56.664, 67.422, 75.406]

    The function uses linear interpolation between bins to accurately
    represent the angular positions.
    """
    Nt = len(time)

    # POLDI slit angles (degrees)
    angles = np.array([0, 9.363, 21.475, 37.039, 50.417, 56.664, 67.422, 75.406])

    # Convert to relative positions (0 to 1)
    angles = np.flip(90 - angles)
    angles = angles - angles[0]
    angles = angles / 90

    # Convert to array indices
    shifts = Nt * angles

    # Create impulse response with linear interpolation
    D = np.zeros(Nt)

    for i in range(len(shifts)):
        # Linear interpolation between bins
        sfloor = int(np.floor(shifts[i]))
        rest = shifts[i] - sfloor

        if sfloor < Nt:
            D[sfloor] += (1 - rest)
        if sfloor + 1 < Nt:
            D[sfloor + 1] += rest

    return D


def fobi_4x10_time_delays(time: np.ndarray) -> np.ndarray:
    """
    Calculate time delays for 4x10 chopper configuration.

    This chopper has 4 groups of 10 slits each (40 slits total).

    Parameters
    ----------
    time : np.ndarray
        Time-of-flight array

    Returns
    -------
    D : np.ndarray
        Time delay response function
    """
    Nt = len(time)

    # 4x10 configuration: 4 groups of 10 slits
    # Angular spacing: 360 / 40 = 9 degrees per slit
    nslits = 40
    angles = np.linspace(0, 90, nslits // 4)  # One quarter of rotation

    # Normalize to 0-1
    angles = angles / 90

    # Convert to array indices
    shifts = Nt * angles

    # Create impulse response
    D = np.zeros(Nt)

    for i in range(len(shifts)):
        sfloor = int(np.floor(shifts[i]))
        rest = shifts[i] - sfloor

        if sfloor < Nt:
            D[sfloor] += (1 - rest)
        if sfloor + 1 < Nt:
            D[sfloor + 1] += rest

    return D


def fobi_5x8_time_delays(time: np.ndarray) -> np.ndarray:
    """
    Calculate time delays for 5x8 chopper configuration.

    This chopper has 5 groups of 8 slits each (40 slits total).

    Parameters
    ----------
    time : np.ndarray
        Time-of-flight array

    Returns
    -------
    D : np.ndarray
        Time delay response function
    """
    Nt = len(time)

    # 5x8 configuration: 5 groups of 8 slits
    nslits = 40
    angles = np.linspace(0, 90, nslits // 4)

    # Normalize to 0-1
    angles = angles / 90

    # Convert to array indices
    shifts = Nt * angles

    # Create impulse response
    D = np.zeros(Nt)

    for i in range(len(shifts)):
        sfloor = int(np.floor(shifts[i]))
        rest = shifts[i] - sfloor

        if sfloor < Nt:
            D[sfloor] += (1 - rest)
        if sfloor + 1 < Nt:
            D[sfloor + 1] += rest

    return D


def fobi_3x14_time_delays(time: np.ndarray) -> np.ndarray:
    """
    Calculate time delays for 3x14 chopper configuration.

    This chopper has 3 groups of 14 slits each (42 slits total).

    Parameters
    ----------
    time : np.ndarray
        Time-of-flight array

    Returns
    -------
    D : np.ndarray
        Time delay response function
    """
    Nt = len(time)

    # 3x14 configuration: 3 groups of 14 slits
    nslits = 42
    angles = np.linspace(0, 90, nslits // 3)

    # Normalize to 0-1
    angles = angles / 90

    # Convert to array indices
    shifts = Nt * angles

    # Create impulse response
    D = np.zeros(Nt)

    for i in range(len(shifts)):
        sfloor = int(np.floor(shifts[i]))
        rest = shifts[i] - sfloor

        if sfloor < Nt:
            D[sfloor] += (1 - rest)
        if sfloor + 1 < Nt:
            D[sfloor + 1] += rest

    return D
