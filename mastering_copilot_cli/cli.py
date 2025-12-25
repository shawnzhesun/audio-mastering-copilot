"""Main CLI application using Typer."""

from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from mastering_copilot_cli import __version__
from mastering_copilot_cli.io.audio_loader import load_audio, get_audio_info, AudioLoadError
from mastering_copilot_cli.util.timecode import seconds_to_timecode
from mastering_copilot_cli.dsp.loudness import analyze_loudness
from mastering_copilot_cli.dsp.peaks import analyze_peaks
from mastering_copilot_cli.config.profiles import get_profile, list_profiles, get_profile_names
from mastering_copilot_cli.analysis.sections import analyze_sections
from mastering_copilot_cli.analysis.normalization import simulate_normalization, compare_platforms
from mastering_copilot_cli.viz.terminal import (
    display_loudness_summary,
    display_loudness_timeline,
    display_peaks_summary,
    display_platform_summary,
)
from mastering_copilot_cli.viz.bars import render_multi_platform_comparison

app = typer.Typer(
    name="mastering-copilot",
    help="Terminal-native audio mastering analysis CLI",
    add_completion=False,
)

console = Console()


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print(f"mastering-copilot version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Audio mastering analysis CLI."""
    pass


@app.command()
def analyze(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Audio file to analyze",
    ),
    profile: Optional[List[str]] = typer.Option(
        None,
        "--profile",
        "-p",
        help="Platform normalization profile (e.g., spotify, netease)",
    ),
    target_lufs: Optional[float] = typer.Option(
        None,
        "--target-lufs",
        help="Override target LUFS (e.g., -14.0)",
    ),
    true_peak_limit: Optional[float] = typer.Option(
        None,
        "--true-peak-limit",
        "--tp",
        help="True peak limit in dB (e.g., -1.0)",
    ),
    window: float = typer.Option(
        3.0,
        "--window",
        "-w",
        help="Segment window size in seconds",
        min=0.5,
        max=30.0,
    ),
    top: int = typer.Option(
        10,
        "--top",
        "-n",
        help="Number of worst segments to show",
        min=1,
        max=100,
    ),
    mono: bool = typer.Option(
        False,
        "--mono",
        help="Also analyze as mono (compatibility check)",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
):
    """Analyze an audio file for mastering metrics and suggestions.

    This command performs comprehensive loudness analysis, peak detection,
    platform normalization simulation, and provides actionable mastering suggestions.
    """
    if no_color:
        console.no_color = True

    console.print(f"\n[bold cyan]Analyzing:[/bold cyan] {input_file.name}")
    console.print()

    # Load audio file
    try:
        with console.status("[bold yellow]Loading audio file..."):
            audio, sample_rate = load_audio(input_file)
            info = get_audio_info(input_file)

    except AudioLoadError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Display track summary
    _display_track_summary(info, audio)

    # Perform loudness analysis
    with console.status("[bold yellow]Analyzing loudness..."):
        loudness_metrics = analyze_loudness(audio, sample_rate)

    # Display loudness results
    display_loudness_summary(console, loudness_metrics)
    display_loudness_timeline(console, loudness_metrics)

    # Perform peak analysis
    with console.status("[bold yellow]Analyzing peaks..."):
        peak_metrics = analyze_peaks(
            audio, sample_rate, integrated_lufs=loudness_metrics.integrated_lufs
        )

    # Display peak results
    display_peaks_summary(console, peak_metrics)

    # Section analysis
    with console.status("[bold yellow]Analyzing sections..."):
        section_analysis = analyze_sections(audio, sample_rate, window_size=window)

    # Platform normalization simulation
    if profile:
        # Get requested profiles
        profiles_to_check = []
        for prof_name in profile:
            prof = get_profile(prof_name)
            if prof:
                profiles_to_check.append(prof)
            else:
                console.print(f"[yellow]Warning:[/yellow] Unknown profile '{prof_name}'")

        if profiles_to_check:
            with console.status("[bold yellow]Simulating platform normalization..."):
                platform_results = compare_platforms(
                    profiles_to_check,
                    loudness_metrics.integrated_lufs,
                    peak_metrics.sample_peak_db,
                    peak_metrics.true_peak_db,
                    section_analysis,
                )

            # Display platform summary
            display_platform_summary(console, platform_results)

            # Display per-section visualization for each platform
            platform_sections = {
                name: result.section_results
                for name, result in platform_results.items()
            }
            render_multi_platform_comparison(
                console,
                section_analysis.sections,
                platform_sections,
                max_sections=50,
            )

            # Display any issues
            for platform_name, result in platform_results.items():
                if result.issues:
                    console.print(f"\n[bold yellow]{result.profile.display_name} Issues:[/bold yellow]")
                    for issue in result.issues:
                        console.print(f"  • {issue}")
    else:
        console.print("\n[dim]Tip: Use --profile to simulate platform normalization (e.g., --profile spotify)[/dim]\n")

    # TODO: Add flags and suggestions

    console.print("\n[green]✓ Analysis complete![/green]\n")


@app.command()
def check(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Audio file to check",
    ),
    target: float = typer.Option(
        -14.0,
        "--target",
        "-t",
        help="Target LUFS",
    ),
    tp: float = typer.Option(
        -1.0,
        "--tp",
        help="True peak limit in dB",
    ),
):
    """Quick pass/fail check against target levels.

    Provides a simple yes/no answer with what needs to change.
    """
    console.print(f"\n[bold cyan]Checking:[/bold cyan] {input_file.name}")
    console.print(f"Target: {target} LUFS, True Peak Limit: {tp} dB\n")

    console.print("[dim]This command is not yet implemented.[/dim]\n")


@app.command()
def segments(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Audio file to analyze",
    ),
    window: float = typer.Option(
        3.0,
        "--window",
        "-w",
        help="Segment window size in seconds",
    ),
    sort: str = typer.Option(
        "penalty",
        "--sort",
        "-s",
        help="Sort by: penalty, lufs, peak",
    ),
    top: int = typer.Option(
        20,
        "--top",
        "-n",
        help="Number of segments to show",
    ),
):
    """Show segment-by-segment analysis table.

    Displays detailed metrics for each time segment of the track.
    """
    console.print(f"\n[bold cyan]Segment Analysis:[/bold cyan] {input_file.name}\n")
    console.print("[dim]This command is not yet implemented.[/dim]\n")


@app.command()
def profiles():
    """List available platform normalization profiles.

    Shows the built-in profiles and their target settings.
    """
    console.print("\n[bold cyan]Available Platform Profiles[/bold cyan]\n")

    all_profiles = list_profiles()

    table = Table(box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Platform", style="white")
    table.add_column("Target LUFS", style="yellow", justify="right")
    table.add_column("Peak Limit", style="yellow", justify="right")
    table.add_column("Description", style="dim")

    for name, prof in all_profiles.items():
        table.add_row(
            name,
            prof.display_name,
            f"{prof.target_lufs:.1f}",
            f"{prof.true_peak_limit:.1f} dBTP",
            prof.description[:60] + "..." if len(prof.description) > 60 else prof.description,
        )

    console.print(table)
    console.print("\n[dim]Usage: mastering-copilot analyze file.wav --profile spotify --profile youtube[/dim]\n")


def _display_track_summary(info: dict, audio):
    """Display basic track information."""
    import numpy as np

    table = Table(title="Track Summary", box=box.ROUNDED, show_header=False)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Determine channels
    if audio.ndim == 1:
        channels = 1
        n_samples = len(audio)
    else:
        n_samples, channels = audio.shape

    duration = info.get("duration", n_samples / info["sample_rate"])

    table.add_row("Duration", seconds_to_timecode(duration))
    table.add_row("Sample Rate", f"{info['sample_rate']} Hz")
    table.add_row("Channels", str(channels))
    table.add_row("Format", info.get("format", "unknown"))
    table.add_row("Samples", f"{n_samples:,}")

    console.print(table)
    console.print()


if __name__ == "__main__":
    app()
