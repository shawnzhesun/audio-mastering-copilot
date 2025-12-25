"""Audio unit conversion utilities."""

import numpy as np


def linear_to_db(linear: float | np.ndarray) -> float | np.ndarray:
    """Convert linear amplitude to dB.

    Args:
        linear: Linear amplitude value(s)

    Returns:
        dB value(s)
    """
    return 20 * np.log10(np.maximum(linear, 1e-10))


def db_to_linear(db: float | np.ndarray) -> float | np.ndarray:
    """Convert dB to linear amplitude.

    Args:
        db: dB value(s)

    Returns:
        Linear amplitude value(s)
    """
    return 10 ** (db / 20)


def lufs_to_linear(lufs: float) -> float:
    """Convert LUFS to linear gain multiplier.

    Args:
        lufs: LUFS value

    Returns:
        Linear gain multiplier
    """
    return 10 ** (lufs / 20)


def format_db(db: float, decimals: int = 1) -> str:
    """Format dB value with proper sign and unit.

    Args:
        db: dB value
        decimals: Number of decimal places

    Returns:
        Formatted string like "+3.2 dB" or "-14.0 dB"
    """
    sign = "+" if db >= 0 else ""
    return f"{sign}{db:.{decimals}f} dB"


def format_lufs(lufs: float, decimals: int = 1) -> str:
    """Format LUFS value with unit.

    Args:
        lufs: LUFS value
        decimals: Number of decimal places

    Returns:
        Formatted string like "-14.0 LUFS"
    """
    return f"{lufs:.{decimals}f} LUFS"


def format_lu(lu: float, decimals: int = 1) -> str:
    """Format LU (Loudness Units) value.

    Args:
        lu: LU value
        decimals: Number of decimal places

    Returns:
        Formatted string like "8.5 LU"
    """
    return f"{lu:.{decimals}f} LU"
