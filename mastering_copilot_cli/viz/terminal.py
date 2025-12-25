"""Rich terminal visualizations for analysis results."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text

from mastering_copilot_cli.dsp.loudness import LoudnessMetrics
from mastering_copilot_cli.dsp.peaks import PeakMetrics, headroom_db
from mastering_copilot_cli.viz.spark import sparkline, format_with_units, horizontal_bar
from mastering_copilot_cli.util.units import format_lufs, format_lu, format_db


def display_loudness_summary(console: Console, metrics: LoudnessMetrics):
    """Display loudness analysis summary table.

    Args:
        console: Rich console instance
        metrics: Loudness metrics to display
    """
    table = Table(title="Loudness Analysis", box=box.ROUNDED, show_header=False)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Visualization", style="dim")

    # Integrated LUFS
    table.add_row(
        "Integrated Loudness (LUFS-I)",
        format_lufs(metrics.integrated_lufs),
        _loudness_bar(metrics.integrated_lufs),
    )

    # Loudness Range
    table.add_row(
        "Loudness Range (LRA)",
        format_lu(metrics.loudness_range),
        _lra_indicator(metrics.loudness_range),
    )

    # Short-term range
    if metrics.short_term_timeline:
        table.add_row(
            "Max Short-Term (LUFS-S)",
            format_lufs(metrics.max_short_term),
            "",
        )
        table.add_row(
            "Min Short-Term (LUFS-S)",
            format_lufs(metrics.min_short_term),
            "",
        )

    console.print(table)
    console.print()


def display_loudness_timeline(console: Console, metrics: LoudnessMetrics, width: int = 80):
    """Display short-term loudness timeline as sparkline.

    Args:
        console: Rich console instance
        metrics: Loudness metrics
        width: Maximum width for sparkline
    """
    if not metrics.short_term_timeline:
        return

    # Extract LUFS values
    lufs_values = [lufs for _, lufs in metrics.short_term_timeline]

    # Subsample if too many points
    if len(lufs_values) > width:
        step = len(lufs_values) // width
        lufs_values = lufs_values[::step]

    # Generate sparkline
    spark = sparkline(lufs_values)

    # Create text with labels
    text = Text()
    text.append("Short-Term Loudness Timeline (LUFS-S)\n", style="bold cyan")
    text.append(f"Max: {format_lufs(metrics.max_short_term)}  ", style="green")
    text.append(f"Min: {format_lufs(metrics.min_short_term)}\n", style="yellow")
    text.append(spark, style="white")

    panel = Panel(text, box=box.ROUNDED, border_style="dim")
    console.print(panel)
    console.print()


def _loudness_bar(lufs: float) -> str:
    """Create a horizontal bar showing loudness level.

    Reference levels:
    -23 LUFS: EBU R128 broadcast standard
    -14 LUFS: Common streaming target (Spotify, YouTube)
    -6 LUFS: Very loud (mastering limit territory)

    Args:
        lufs: LUFS value

    Returns:
        Bar visualization string
    """
    # Map LUFS to bar (louder = more filled)
    # Use -30 to -5 LUFS as range
    return horizontal_bar(lufs, min_val=-30.0, max_val=-5.0, width=20)


def _lra_indicator(lra: float) -> str:
    """Create indicator for loudness range.

    LRA interpretation:
    < 4 LU: Very compressed/limited
    4-8 LU: Moderately compressed (typical for pop/rock)
    8-15 LU: Good dynamic range
    > 15 LU: Very dynamic (classical, jazz, live)

    Args:
        lra: Loudness range in LU

    Returns:
        Text indicator
    """
    if lra < 4:
        return "[red]Very compressed[/red]"
    elif lra < 8:
        return "[yellow]Moderate[/yellow]"
    elif lra < 15:
        return "[green]Good dynamics[/green]"
    else:
        return "[cyan]Very dynamic[/cyan]"


def display_peaks_summary(console: Console, metrics: PeakMetrics):
    """Display peak analysis summary table.

    Args:
        console: Rich console instance
        metrics: Peak metrics to display
    """
    table = Table(title="Peak Analysis", box=box.ROUNDED, show_header=False)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Info", style="dim")

    # Sample peak
    headroom = headroom_db(metrics.sample_peak_db)
    table.add_row(
        "Sample Peak",
        format_db(metrics.sample_peak_db),
        _peak_warning(metrics.sample_peak_db),
    )

    # True peak (approximate)
    tp_headroom = headroom_db(metrics.true_peak_db)
    table.add_row(
        "True Peak (approx)",
        format_db(metrics.true_peak_db) + "TP",
        _true_peak_warning(metrics.true_peak_db),
    )

    # Headroom
    table.add_row(
        "Headroom",
        format_db(headroom),
        _headroom_indicator(headroom),
    )

    # Crest factor
    table.add_row(
        "Crest Factor",
        format_db(metrics.crest_factor_db),
        _crest_indicator(metrics.crest_factor_db),
    )

    # PLR (if available)
    if metrics.peak_to_loudness_ratio_db != 0.0:
        table.add_row(
            "Peak-to-Loudness Ratio (PLR)",
            format_db(metrics.peak_to_loudness_ratio_db),
            _plr_indicator(metrics.peak_to_loudness_ratio_db),
        )

    console.print(table)
    console.print()


def _peak_warning(peak_db: float) -> str:
    """Generate warning message for sample peak level."""
    if peak_db >= -0.1:
        return "[red bold]⚠ At/near clipping![/red bold]"
    elif peak_db >= -1.0:
        return "[yellow]⚠ Very hot[/yellow]"
    elif peak_db >= -3.0:
        return "[yellow]Hot level[/yellow]"
    else:
        return "[green]OK[/green]"


def _true_peak_warning(tp_db: float) -> str:
    """Generate warning for true peak level."""
    if tp_db >= -0.5:
        return "[red bold]⚠ Exceeds -1 dBTP![/red bold]"
    elif tp_db >= -1.0:
        return "[yellow]⚠ Close to -1 dBTP[/yellow]"
    elif tp_db >= -2.0:
        return "[green]Good for streaming[/green]"
    else:
        return "[green]Safe headroom[/green]"


def _headroom_indicator(headroom: float) -> str:
    """Indicate headroom status."""
    if headroom < 0:
        return "[red]⚠ Clipping![/red]"
    elif headroom < 1.0:
        return "[yellow]Minimal[/yellow]"
    elif headroom < 3.0:
        return "[green]Adequate[/green]"
    else:
        return "[cyan]Plenty[/cyan]"


def _crest_indicator(crest_db: float) -> str:
    """Indicate crest factor status.

    Typical ranges:
    < 6 dB: Heavily limited/compressed
    6-12 dB: Moderate compression (typical for pop)
    12-18 dB: Good dynamics
    > 18 dB: Very dynamic
    """
    if crest_db < 6:
        return "[red]Heavily limited[/red]"
    elif crest_db < 12:
        return "[yellow]Compressed[/yellow]"
    elif crest_db < 18:
        return "[green]Good dynamics[/green]"
    else:
        return "[cyan]Very dynamic[/cyan]"


def _plr_indicator(plr_db: float) -> str:
    """Indicate peak-to-loudness ratio status.

    PLR indicates how much headroom exists relative to loudness.
    Typical ranges:
    < 8 dB: Over-limited
    8-12 dB: Typical for modern pop/rock
    12-18 dB: Good dynamics
    > 18 dB: Very dynamic
    """
    if plr_db < 8:
        return "[red]Over-limited[/red]"
    elif plr_db < 12:
        return "[yellow]Typical[/yellow]"
    elif plr_db < 18:
        return "[green]Good dynamics[/green]"
    else:
        return "[cyan]Very dynamic[/cyan]"


def display_platform_summary(console: Console, platform_results: dict):
    """Display summary table of platform normalization results.

    Args:
        console: Rich console
        platform_results: Dict of platform_name -> PlatformNormalization
    """
    from mastering_copilot_cli.analysis.normalization import PlatformNormalization

    table = Table(title="Platform Normalization Summary", box=box.ROUNDED)
    table.add_column("Platform", style="cyan", no_wrap=True)
    table.add_column("Target", style="white", justify="right")
    table.add_column("Action", style="white")
    table.add_column("Gain", style="white", justify="right")
    table.add_column("Status", style="white")

    for platform_name, result in platform_results.items():
        platform_display = result.profile.display_name

        # Target LUFS
        target_str = f"{result.profile.target_lufs:.1f} LUFS"

        # Action description
        action = result.overall_action

        # Gain string
        if action.gain_db > 0:
            gain_str = f"+{action.gain_db:.1f} dB"
        elif action.gain_db < 0:
            gain_str = f"{action.gain_db:.1f} dB"
        else:
            gain_str = "—"

        # Status indicator
        if result.will_sound_good:
            if action.action_type == "none":
                status = "[green]✓ Perfect[/green]"
            else:
                status = "[green]✓ Good[/green]"
        else:
            if action.will_limit:
                status = "[yellow]⚠ Will limit[/yellow]"
            elif action.will_clip:
                status = "[red]✗ Will clip[/red]"
            else:
                status = "[yellow]⚠ Check[/yellow]"

        table.add_row(
            platform_display,
            target_str,
            action.description,
            gain_str,
            status,
        )

    console.print(table)
    console.print()
