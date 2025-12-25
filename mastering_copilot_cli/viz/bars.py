"""Vertical bar chart visualization for section analysis."""

from typing import List, Tuple, Optional
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
    # Add a row at bottom for platform action indicators
    indicator_row = []
    for result in platform_results:
        action_type = result.action.action_type

        if action_type == "reduce":
            indicator = "⌄"  # Down arrow - volume reduced
            color = "cyan"
        elif action_type == "boost":
            indicator = "⌃"  # Up arrow - volume boosted
            color = "yellow"
        elif action_type == "limit":
            indicator = "≈"  # Limited
            color = "red"
        elif action_type == "clip_risk":
            indicator = "!"  # Clipping risk
            color = "red bold"
        else:
            indicator = "·"  # No change
            color = "dim"

        # Center the indicator in the bar width
        padding = (bar_width - 1) // 2
        indicator_str = " " * padding + indicator + " " * (bar_width - padding - 1)
        indicator_row.append(indicator_str)

    return rows, "".join(indicator_row)


def render_platform_section_chart(
    console: Console,
    sections: List[Section],
    platform_results: List[SectionNormalization],
    platform_name: str,
    max_sections: int = 40,
) -> None:
    """Render a complete platform section analysis chart.

    Args:
        console: Rich console
        sections: List of sections
        platform_results: Platform normalization results
        platform_name: Name of platform
        max_sections: Maximum number of sections to display
    """
    # Subsample if too many sections
    if len(sections) > max_sections:
        step = len(sections) // max_sections
        sections = sections[::step]
        platform_results = platform_results[::step]

    # Create chart
    chart_rows, indicator_row = create_section_bars_with_overlay(
        sections, platform_results, height=10, bar_width=2
    )

    # Build text output
    text = Text()
    text.append(f"{platform_name} Normalization\n", style="bold cyan")
    text.append("Timeline (each bar = ~3s section)\n\n", style="dim")

    # Add chart rows
    for row in chart_rows:
        text.append(row + "\n", style="white")

    # Add indicator row with colors
    for i, result in enumerate(platform_results):
        action_type = result.action.action_type

        if action_type == "reduce":
            style = "cyan"
        elif action_type == "boost":
            style = "yellow"
        elif action_type == "limit":
            style = "red"
        elif action_type == "clip_risk":
            style = "red bold"
        else:
            style = "dim"

        # Get the indicator character
        indicator_str = indicator_row[i * 2: (i + 1) * 2]
        text.append(indicator_str, style=style)

    text.append("\n\n", style="")

    # Add LUFS labels
    lufs_values = [s.integrated_lufs if not np.isinf(s.integrated_lufs) else -60 for s in sections]

    # Show every nth value to avoid clutter
    label_row = []
    show_every = max(1, len(sections) // 10)

    for i, lufs in enumerate(lufs_values):
        if i % show_every == 0:
            label = f"{lufs:.0f}"
        else:
            label = ""

        # Pad to bar width
        padded = label.center(2)
        label_row.append(padded)

    text.append("".join(label_row), style="dim")

    # Add legend
    text.append("\n\n", style="")
    text.append("⌄ Reduced  ", style="cyan")
    text.append("⌃ Boosted  ", style="yellow")
    text.append("≈ Limited  ", style="red")
    text.append("· No change", style="dim")

    panel = Panel(text, border_style="blue", box=box.ROUNDED)
    console.print(panel)
    console.print()


def render_multi_platform_comparison(
    console: Console,
    sections: List[Section],
    platform_results_dict: dict,
    max_sections: int = 40,
) -> None:
    """Render comparison of multiple platforms side-by-side.

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

    # Get LUFS values for x-axis labels (shared across platforms)
    lufs_values = [s.integrated_lufs if not np.isinf(s.integrated_lufs) else -60 for s in sections]

    text = Text()
    text.append("Platform Normalization Comparison\n", style="bold cyan")
    text.append("Each column = ~3s section of your track\n\n", style="dim")

    # Render each platform
    for platform_name, results in platform_results_dict.items():
        # Platform name
        text.append(f"\n{platform_name}\n", style="bold yellow")

        # Create bars
        chart_rows, indicator_row = create_section_bars_with_overlay(
            sections, results, height=8, bar_width=2
        )

        # Add chart
        for row in chart_rows:
            text.append(row + "\n", style="white")

        # Add colored indicators
        for i, result in enumerate(results):
            action_type = result.action.action_type

            if action_type == "reduce":
                style = "cyan"
            elif action_type == "boost":
                style = "yellow"
            elif action_type == "limit":
                style = "red"
            elif action_type == "clip_risk":
                style = "red bold"
            else:
                style = "dim"

            indicator_str = indicator_row[i * 2: (i + 1) * 2]
            text.append(indicator_str, style=style)

        text.append("\n", style="")

    # Add shared LUFS labels at bottom
    text.append("\nLUFS: ", style="dim")
    show_every = max(1, len(sections) // 10)
    for i, lufs in enumerate(lufs_values):
        if i % show_every == 0:
            text.append(f"{lufs:.0f}".center(2), style="dim")
        else:
            text.append("  ", style="dim")

    # Legend
    text.append("\n\n", style="")
    text.append("⌄ Reduced  ", style="cyan")
    text.append("⌃ Boosted  ", style="yellow")
    text.append("≈ Limited  ", style="red")
    text.append("· No change", style="dim")

    panel = Panel(text, border_style="magenta", box=box.ROUNDED)
    console.print(panel)
    console.print()
