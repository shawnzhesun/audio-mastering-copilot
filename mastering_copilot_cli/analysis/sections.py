"""Section-by-section audio analysis."""

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pyloudnorm as pyln

from mastering_copilot_cli.dsp.peaks import analyze_peaks, PeakMetrics


@dataclass
class Section:
    """Represents an analyzed section of audio."""

    index: int
    start_time: float  # seconds
    end_time: float  # seconds
    duration: float  # seconds
    integrated_lufs: float
    peak_db: float
    true_peak_db: float
    dynamic_range_db: float  # Local crest factor


@dataclass
class SectionAnalysis:
    """Complete section-by-section analysis."""

    sections: List[Section]
    window_size: float  # seconds
    hop_size: float  # seconds


def analyze_sections(
    audio: np.ndarray,
    sample_rate: int,
    window_size: float = 3.0,
    hop_size: float = 1.0,
) -> SectionAnalysis:
    """Analyze audio in overlapping sections.

    Args:
        audio: Audio data, shape (n_samples,) or (n_samples, n_channels)
        sample_rate: Sample rate in Hz
        window_size: Section window size in seconds
        hop_size: Hop between sections in seconds

    Returns:
        SectionAnalysis containing all sections
    """
    # Ensure 2D
    if audio.ndim == 1:
        audio = audio.reshape(-1, 1)

    window_samples = int(window_size * sample_rate)
    hop_samples = int(hop_size * sample_rate)

    meter = pyln.Meter(sample_rate)
    sections = []
    n_samples = audio.shape[0]
    section_idx = 0

    current_pos = 0
    while current_pos + window_samples <= n_samples:
        # Extract section
        section_audio = audio[current_pos : current_pos + window_samples]

        # Time information
        start_time = current_pos / sample_rate
        end_time = (current_pos + window_samples) / sample_rate
        duration = window_size

        # Loudness
        try:
            integrated_lufs = meter.integrated_loudness(section_audio)
        except ValueError:
            integrated_lufs = -np.inf

        # Peaks
        peak_linear = np.max(np.abs(section_audio))
        peak_db = 20 * np.log10(np.maximum(peak_linear, 1e-10))

        # True peak (simplified - just use sample peak for speed)
        # For full true peak, we'd need to oversample each section
        true_peak_db = peak_db  # Approximation

        # Dynamic range (local crest factor)
        rms = np.sqrt(np.mean(section_audio**2))
        if rms > 0:
            dynamic_range_db = 20 * np.log10(peak_linear / rms)
        else:
            dynamic_range_db = 0.0

        section = Section(
            index=section_idx,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            integrated_lufs=integrated_lufs,
            peak_db=peak_db,
            true_peak_db=true_peak_db,
            dynamic_range_db=dynamic_range_db,
        )

        sections.append(section)
        section_idx += 1
        current_pos += hop_samples

    return SectionAnalysis(
        sections=sections,
        window_size=window_size,
        hop_size=hop_size,
    )


def get_worst_sections(
    analysis: SectionAnalysis,
    metric: str = "lufs",
    n: int = 10,
    reverse: bool = False,
) -> List[Section]:
    """Get the worst (or best) sections by a metric.

    Args:
        analysis: SectionAnalysis
        metric: Metric to sort by ('lufs', 'peak', 'dynamic_range')
        n: Number of sections to return
        reverse: If True, return best instead of worst

    Returns:
        List of sections sorted by metric
    """
    if metric == "lufs":
        key = lambda s: s.integrated_lufs if not np.isinf(s.integrated_lufs) else -999
        reverse_sort = not reverse  # Higher LUFS = louder = "worse" for mastering
    elif metric == "peak":
        key = lambda s: s.peak_db
        reverse_sort = not reverse  # Higher peak = "worse"
    elif metric == "dynamic_range":
        key = lambda s: s.dynamic_range_db
        reverse_sort = reverse  # Lower DR = worse (but we want to sort ascending)
    else:
        raise ValueError(f"Unknown metric: {metric}")

    sorted_sections = sorted(analysis.sections, key=key, reverse=reverse_sort)
    return sorted_sections[:n]
