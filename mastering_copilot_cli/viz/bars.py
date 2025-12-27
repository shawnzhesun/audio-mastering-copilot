"""Vertical bar chart visualization for section analysis."""

from typing import List, Dict
import numpy as np
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich import box

from mastering_copilot_cli.analysis.sections import Section
from mastering_copilot_cli.analysis.normalization import SectionNormalization


# Unicode block characters for vertical bars (from bottom to top)
VERTICAL_BLOCKS = [
    " ",      # 0/8 Empty
    "▁",      # 1/8
    "▂",      # 2/8
    "▃",      # 3/8
    "▄",      # 4/8
    "▅",      # 5/8
    "▆",      # 6/8
    "▇",      # 7/8
    "█",      # 8/8 Full
]


def create_vertical_bars(
    values: List[float],
    min_val: float,
    max_val: float,
    height: int = 10,
    width: int = 1,
) -> List[str]:
    """Create vertical bar chart using Unicode blocks.

    Args:
        values: List of values to plot
        min_val: Minimum value for scaling
        max_val: Maximum value for scaling
        height: Height of chart in character rows
        width: Width of each bar in characters

    Returns:
        List of strings, one per row (top to bottom)
    """
    if not values or max_val == min_val:
        return [" " * (len(values) * width) for _ in range(height)]

    # Normalize values to 0-height range
    normalized = []
    for v in values:
        if np.isinf(v) or np.isnan(v):
            normalized.append(0.0)
        else:
            norm = (v - min_val) / (max_val - min_val)
            norm = max(0.0, min(1.0, norm))
            normalized.append(norm * height)

    # Build rows from top to bottom
    rows = []
    for row_idx in range(height):
        level = height - row_idx  # Current level (height at top, 1 at bottom)
        row_chars = []

        for norm_val in normalized:
            if norm_val >= level:
                # Full block at this level
                char = "█"
            elif norm_val >= level - 1:
                # Partial block
                fraction = norm_val - (level - 1)
                block_idx = int(fraction * 8)
                block_idx = max(0, min(8, block_idx))
                char = VERTICAL_BLOCKS[block_idx]
            else:
                # Empty
                char = " "

            # Repeat for width
            row_chars.append(char * width)

        rows.append("".join(row_chars))

    return rows


def create_section_bars_with_overlay(
    sections: List[Section],
    platform_results: List[SectionNormalization],
    height: int = 12,
    bar_width: int = 2,
) -> List[str]:
    """Create vertical bars with platform normalization overlay.

    Shows original LUFS as main bar, with colored indicator for platform treatment.

    Args:
        sections: List of sections
        platform_results: Platform normalization results for each section
        height: Chart height
        bar_width: Width of each bar

    Returns:
        List of row strings
    """
    if not sections:
        return []

    # Extract values
    lufs_values = [s.integrated_lufs if not np.isinf(s.integrated_lufs) else -60.0 for s in sections]

    # Determine range (use typical mastering range)
    min_lufs = -35.0  # Quiet
    max_lufs = -5.0   # Very loud

    # Create base bars
    rows = create_vertical_bars(lufs_values, min_lufs, max_lufs, height, bar_width)

    # Add platform treatment overlay (colored indicators on bars)
    # Show how each section ends up AFTER normalization relative to target
    indicator_row = []
    for result in platform_results:
        action_type = result.action.action_type
        resulting_lufs = result.resulting_lufs  # LUFS after platform normalization
        target_lufs = result.target_lufs

        # Calculate difference between resulting loudness and target
        diff = resulting_lufs - target_lufs

        if action_type == "clip_risk" or result.resulting_peak_db > result.target_peak_db:
            # Section will clip or exceed true peak limit
            indicator = "!"
        elif diff > 3.0:
            # Section ends up significantly above target (still too hot)
            indicator = "⚠"
        elif diff > 1.0:
            # Section ends up slightly above target (acceptable)
            indicator = "⌃"
        elif diff < -4.0:
            # Section ends up way below target (buried in mix)
            indicator = "⇣"
        elif diff < -1.5:
            # Section ends up below target (noticeable)
            indicator = "⌄"
        else:
            # Section is close to target (within ±1.5 dB - good!)
            indicator = "·"

        # Center the indicator in the bar width
        padding = (bar_width - 1) // 2
        indicator_str = " " * padding + indicator + " " * (bar_width - padding - 1)
        indicator_row.append(indicator_str)

    return rows, "".join(indicator_row)


def render_multi_platform_comparison(
    console: Console,
    sections: List[Section],
    platform_results_dict: Dict[str, List[SectionNormalization]],
    max_sections: int = 40,
) -> None:
    """Render comparison of multiple platforms as stacked histograms.

    Shows section LUFS horizontally across time with platform target reference lines.
    Each platform is displayed in its own row for better readability.

    Args:
        console: Rich console
        sections: List of sections
        platform_results_dict: Dict of platform_name -> list of SectionNormalization
        max_sections: Maximum sections to display
    """
    # Subsample sections if needed
    if len(sections) > max_sections:
        step = len(sections) // max_sections
        sections = sections[::step]
        platform_results_dict = {
            name: results[::step] for name, results in platform_results_dict.items()
        }

    platforms = list(platform_results_dict.items())
    num_sections = len(sections)

    if len(platforms) == 0 or num_sections == 0:
        return

    # Chart dimensions
    chart_height = 12  # Height in character rows
    chart_width = min(70, num_sections * 2)  # Width based on sections
    bar_width = max(1, chart_width // num_sections)

    # LUFS range for visualization
    min_lufs = -25.0
    max_lufs = -5.0

    text = Text()
    text.append("Platform Normalization Comparison\n", style="bold cyan")
    text.append(f"Timeline: {num_sections} sections × ~3s each\n\n", style="dim")

    # Render each platform
    for platform_name, results in platforms:
        # Platform header with target
        target_lufs = results[0].target_lufs
        text.append(f"{platform_name}", style="bold yellow")
        text.append(f" (target: {target_lufs:.1f} LUFS)\n", style="dim")

        # Get resulting LUFS for each section after normalization
        resulting_lufs_values = [r.resulting_lufs for r in results]

        # Create histogram
        histogram_rows = _create_horizontal_histogram(
            resulting_lufs_values,
            target_lufs,
            min_lufs,
            max_lufs,
            chart_height,
            bar_width,
        )

        # Draw histogram with LUFS labels on the left
        for row_idx, row in enumerate(histogram_rows):
            # Calculate LUFS value for this row
            lufs_at_row = max_lufs - (row_idx * (max_lufs - min_lufs) / chart_height)

            # Add LUFS label on the left (right-aligned in 4 chars)
            text.append(f"{lufs_at_row:>4.0f} ", style="dim")
            text.append(row + "\n", style="white")

        # Draw indicator row showing status of each section
        text.append("     ", style="")  # Space to align with LUFS labels
        for result in results:
            diff = result.resulting_lufs - result.target_lufs
            action_type = result.action.action_type

            # Determine indicator
            if action_type == "clip_risk" or result.resulting_peak_db > result.target_peak_db:
                indicator = "!"
                style = "red bold"
            elif diff > 3.0:
                indicator = "⚠"
                style = "red"
            elif diff > 1.0:
                indicator = "⌃"
                style = "yellow"
            elif diff < -4.0:
                indicator = "⇣"
                style = "magenta"
            elif diff < -1.5:
                indicator = "⌄"
                style = "yellow"
            else:
                indicator = "·"
                style = "green"

            # Build indicator string with padding
            ind_str = (indicator * bar_width).ljust(bar_width)
            text.append(ind_str, style=style)

        text.append("\n\n")

    # Add LUFS scale at bottom
    text.append("LUFS Scale: ", style="dim")
    text.append(f"{max_lufs:.0f} ", style="red")
    text.append("(loud) ... ", style="dim")
    text.append(f"{(max_lufs+min_lufs)/2:.0f} ", style="yellow")
    text.append("... ", style="dim")
    text.append(f"{min_lufs:.0f}", style="cyan")
    text.append(" (quiet)\n\n", style="dim")

    # Legend
    text.append("After normalization: ", style="bold dim")
    text.append("· Near target  ", style="green")
    text.append("⌃ Above  ", style="yellow")
    text.append("⌄ Below  ", style="yellow")
    text.append("⚠ Too hot  ", style="red")
    text.append("⇣ Buried  ", style="magenta")
    text.append("! Clip", style="red bold")

    panel = Panel(text, border_style="magenta", box=box.ROUNDED)
    console.print(panel)
    console.print()


def _create_horizontal_histogram(
    values: List[float],
    target_line: float,
    min_val: float,
    max_val: float,
    height: int,
    bar_width: int,
) -> List[str]:
    """Create horizontal histogram with target reference line.

    Args:
        values: List of LUFS values to plot
        target_line: Target LUFS to mark on chart
        min_val: Minimum LUFS for scale
        max_val: Maximum LUFS for scale
        height: Chart height in rows
        bar_width: Width of each bar in characters

    Returns:
        List of row strings (top to bottom)
    """
    if not values:
        return []

    # Calculate target line position
    target_norm = (target_line - min_val) / (max_val - min_val)
    target_row = height - int(target_norm * height)

    rows = []
    for row_idx in range(height):
        level_threshold = max_val - (row_idx * (max_val - min_val) / height)
        row_chars = []

        for val in values:
            if np.isinf(val) or np.isnan(val):
                val = min_val

            # Determine what to draw at this position
            if row_idx == target_row:
                # Target reference line
                char = "─"
                repeat = bar_width
            elif val >= level_threshold:
                # Bar extends to this level
                char = "█"
                repeat = bar_width
            elif val >= level_threshold - (max_val - min_val) / height * 0.5:
                # Partial bar
                char = "▄"
                repeat = bar_width
            else:
                # Empty space
                char = " "
                repeat = bar_width

            row_chars.append(char * repeat)

        rows.append("".join(row_chars))

    return rows
