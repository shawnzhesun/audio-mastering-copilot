"""Peak detection including sample peak and true peak approximation."""

from typing import Tuple
from dataclasses import dataclass

import numpy as np
import soxr
from mastering_copilot_cli.util.units import linear_to_db


@dataclass
class PeakMetrics:
    """Container for peak analysis results."""

    sample_peak_db: float  # Maximum sample peak across all channels in dB
    sample_peak_linear: float  # Maximum sample peak in linear (0-1 range)
    true_peak_db: float  # Approximate true peak in dBTP
    true_peak_linear: float  # Approximate true peak in linear
    crest_factor_db: float  # Crest factor (peak to RMS ratio) in dB
    peak_to_loudness_ratio_db: float  # PLR in dB (requires LUFS input)


def analyze_peaks(
    audio: np.ndarray,
    sample_rate: int,
    integrated_lufs: float = None,
    oversample_factor: int = 4,
) -> PeakMetrics:
    """Analyze peak levels including true peak approximation.

    Args:
        audio: Audio data, shape (n_samples,) or (n_samples, n_channels)
        sample_rate: Sample rate in Hz
        integrated_lufs: Integrated LUFS for PLR calculation (optional)
        oversample_factor: Oversampling factor for true peak (4 or 8)

    Returns:
        PeakMetrics object containing peak measurements
    """
    # Ensure 2D array
    if audio.ndim == 1:
        audio = audio.reshape(-1, 1)

    # Sample peak (max absolute value across all channels)
    sample_peak_linear = np.max(np.abs(audio))
    sample_peak_db = linear_to_db(sample_peak_linear)

    # True peak approximation via oversampling
    true_peak_linear = _compute_true_peak(audio, sample_rate, oversample_factor)
    true_peak_db = linear_to_db(true_peak_linear)

    # Crest factor (peak to RMS ratio)
    rms = np.sqrt(np.mean(audio**2))
    crest_factor_db = linear_to_db(sample_peak_linear / rms if rms > 0 else 1.0)

    # Peak to Loudness Ratio (PLR)
    # PLR = peak level (dBFS) - integrated loudness (LUFS)
    if integrated_lufs is not None and not np.isinf(integrated_lufs):
        # Convert LUFS to dBFS equivalent (LUFS is roughly dBFS for full-scale sine)
        # PLR = sample_peak_db - integrated_lufs
        # But sample_peak_db is relative to 0 dBFS, so:
        peak_to_loudness_ratio_db = sample_peak_db - integrated_lufs
    else:
        peak_to_loudness_ratio_db = 0.0

    return PeakMetrics(
        sample_peak_db=sample_peak_db,
        sample_peak_linear=sample_peak_linear,
        true_peak_db=true_peak_db,
        true_peak_linear=true_peak_linear,
        crest_factor_db=crest_factor_db,
        peak_to_loudness_ratio_db=peak_to_loudness_ratio_db,
    )


def _compute_true_peak(
    audio: np.ndarray,
    sample_rate: int,
    oversample_factor: int = 4,
) -> float:
    """Compute true peak via oversampling.

    True peak detection requires oversampling to catch inter-sample peaks
    that can exceed 0 dBFS when reconstructed by a DAC.

    Args:
        audio: Audio data, shape (n_samples, n_channels)
        sample_rate: Original sample rate
        oversample_factor: Oversampling factor (4x or 8x per ITU-R BS.1770)

    Returns:
        Maximum true peak value (linear, 0-1+ range)
    """
    n_samples, n_channels = audio.shape
    max_true_peak = 0.0

    # Process each channel separately
    for ch in range(n_channels):
        channel_audio = audio[:, ch]

        # Oversample using high-quality resampler
        try:
            oversampled = soxr.resample(
                channel_audio,
                sample_rate,
                sample_rate * oversample_factor,
                quality="HQ",  # High quality for accurate peak detection
            )
        except Exception:
            # Fallback to scipy if soxr fails
            from scipy import signal

            oversampled = signal.resample(channel_audio, n_samples * oversample_factor)

        # Find peak in oversampled signal
        channel_peak = np.max(np.abs(oversampled))
        max_true_peak = max(max_true_peak, channel_peak)

    return max_true_peak


def check_clipping(audio: np.ndarray, threshold: float = 0.99) -> Tuple[bool, int]:
    """Check if audio contains clipping.

    Args:
        audio: Audio data
        threshold: Level to consider as clipping (default 0.99 = -0.09 dBFS)

    Returns:
        Tuple of (has_clipping, num_clipped_samples)
    """
    if audio.ndim == 1:
        audio = audio.reshape(-1, 1)

    clipped_samples = np.sum(np.abs(audio) >= threshold)
    has_clipping = clipped_samples > 0

    return has_clipping, int(clipped_samples)


def headroom_db(peak_db: float) -> float:
    """Calculate headroom to 0 dBFS.

    Args:
        peak_db: Peak level in dB

    Returns:
        Headroom in dB (positive value = below 0 dBFS)
    """
    return 0.0 - peak_db
