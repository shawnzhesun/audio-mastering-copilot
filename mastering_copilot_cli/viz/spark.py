"""Sparkline and mini-chart generation for terminal output."""

from typing import List, Optional
import numpy as np


# Unicode block characters for sparklines (from lowest to highest)
SPARK_CHARS = "▁▂▃▄▅▆▇█"


def sparkline(values: List[float], min_val: Optional[float] = None, max_val: Optional[float] = None) -> str:
    """Generate a sparkline from a list of values.

    Args:
        values: List of numeric values
        min_val: Minimum value for scaling (auto-detected if None)
        max_val: Maximum value for scaling (auto-detected if None)

    Returns:
        String of sparkline characters
    """
    if not values:
        return ""

    # Remove any inf values
    clean_values = [v for v in values if not np.isinf(v)]
    if not clean_values:
        return "▁" * len(values)

    # Determine range
    if min_val is None:
        min_val = min(clean_values)
    if max_val is None:
        max_val = max(clean_values)

    # Avoid division by zero
    if max_val == min_val:
        return SPARK_CHARS[len(SPARK_CHARS) // 2] * len(values)

    # Map each value to a spark character
    result = []
    for v in values:
        if np.isinf(v):
            # Use lowest character for -inf
            result.append(SPARK_CHARS[0])
        else:
            # Normalize to 0-1 range
            normalized = (v - min_val) / (max_val - min_val)
            # Map to character index
            idx = int(normalized * (len(SPARK_CHARS) - 1))
            idx = max(0, min(len(SPARK_CHARS) - 1, idx))
            result.append(SPARK_CHARS[idx])

    return "".join(result)


def horizontal_bar(
    value: float,
    min_val: float = 0.0,
    max_val: float = 1.0,
    width: int = 20,
    filled_char: str = "█",
    empty_char: str = "░",
) -> str:
    """Generate a horizontal bar chart.

    Args:
        value: Current value
        min_val: Minimum value
        max_val: Maximum value
        width: Width of the bar in characters
        filled_char: Character for filled portion
        empty_char: Character for empty portion

    Returns:
        String representing the bar
    """
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)

    normalized = max(0.0, min(1.0, normalized))
    filled_width = int(normalized * width)

    return filled_char * filled_width + empty_char * (width - filled_width)


def vertical_bars(
    values: List[float],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    height: int = 10,
) -> List[str]:
    """Generate vertical bar chart lines.

    Args:
        values: List of values
        min_val: Minimum value
        max_val: Maximum value
        height: Height of the chart in lines

    Returns:
        List of strings, one per line (top to bottom)
    """
    if not values:
        return []

    if min_val is None:
        min_val = min(values)
    if max_val is None:
        max_val = max(values)

    if max_val == min_val:
        # All values the same
        return [" " * len(values) for _ in range(height)]

    # Normalize values to 0-height range
    normalized = [(v - min_val) / (max_val - min_val) * height for v in values]

    lines = []
    for level in range(height, 0, -1):
        line = ""
        for norm_val in normalized:
            if norm_val >= level:
                line += "█"
            elif norm_val >= level - 0.5:
                line += "▄"
            else:
                line += " "
        lines.append(line)

    return lines


def format_with_units(value: float, unit: str, decimals: int = 1) -> str:
    """Format a value with units for display.

    Args:
        value: Numeric value
        unit: Unit string (e.g., "dB", "LUFS", "LU")
        decimals: Number of decimal places

    Returns:
        Formatted string
    """
    if np.isinf(value):
        if value < 0:
            return f"-∞ {unit}"
        else:
            return f"∞ {unit}"

    return f"{value:.{decimals}f} {unit}"
