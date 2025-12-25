"""Loudness analysis using BS.1770-4 standard via pyloudnorm."""

from typing import Tuple, List
from dataclasses import dataclass

import numpy as np
import pyloudnorm as pyln


@dataclass
class LoudnessMetrics:
    """Container for loudness analysis results."""

    integrated_lufs: float  # LUFS-I (integrated loudness)
    loudness_range: float  # LRA in LU
    max_short_term: float  # Maximum LUFS-S value
    min_short_term: float  # Minimum LUFS-S value
    short_term_timeline: List[Tuple[float, float]]  # List of (time_seconds, lufs_s)


def analyze_loudness(
    audio: np.ndarray,
    sample_rate: int,
    hop_seconds: float = 0.5,
) -> LoudnessMetrics:
    """Analyze loudness metrics using BS.1770-4 standard.

    Args:
        audio: Audio data as numpy array, shape (n_samples,) or (n_samples, n_channels)
        sample_rate: Sample rate in Hz
        hop_seconds: Hop size for short-term measurements in seconds

    Returns:
        LoudnessMetrics object containing all loudness measurements
    """
    # Ensure audio is 2D (n_samples, n_channels)
    if audio.ndim == 1:
        audio = audio.reshape(-1, 1)

    # Create meter
    meter = pyln.Meter(sample_rate)

    # Compute integrated loudness (LUFS-I)
    try:
        integrated_lufs = meter.integrated_loudness(audio)
    except ValueError:
        # Handle case where audio is too quiet
        integrated_lufs = -np.inf

    # Compute short-term loudness timeline
    short_term_timeline = _compute_short_term_timeline(audio, sample_rate, hop_seconds)

    # Extract short-term values
    if short_term_timeline:
        lufs_values = [lufs for _, lufs in short_term_timeline if not np.isinf(lufs)]
        if lufs_values:
            max_short_term = max(lufs_values)
            min_short_term = min(lufs_values)
        else:
            max_short_term = -np.inf
            min_short_term = -np.inf
    else:
        max_short_term = -np.inf
        min_short_term = -np.inf

    # Compute loudness range (LRA)
    # LRA is computed from the short-term loudness distribution
    try:
        # pyloudnorm doesn't have a direct LRA method, so we compute it manually
        # LRA = difference between 95th and 10th percentile of short-term loudness
        if lufs_values:
            lufs_sorted = sorted(lufs_values)
            idx_10 = int(len(lufs_sorted) * 0.10)
            idx_95 = int(len(lufs_sorted) * 0.95)
            loudness_range = lufs_sorted[idx_95] - lufs_sorted[idx_10]
        else:
            loudness_range = 0.0
    except Exception:
        loudness_range = 0.0

    return LoudnessMetrics(
        integrated_lufs=integrated_lufs,
        loudness_range=loudness_range,
        max_short_term=max_short_term,
        min_short_term=min_short_term,
        short_term_timeline=short_term_timeline,
    )


def _compute_short_term_timeline(
    audio: np.ndarray,
    sample_rate: int,
    hop_seconds: float = 0.5,
) -> List[Tuple[float, float]]:
    """Compute short-term loudness timeline.

    Args:
        audio: Audio data, shape (n_samples, n_channels)
        sample_rate: Sample rate in Hz
        hop_seconds: Hop size in seconds

    Returns:
        List of (time_seconds, lufs_s) tuples
    """
    # Short-term window is 3 seconds according to BS.1770
    window_seconds = 3.0
    window_samples = int(window_seconds * sample_rate)
    hop_samples = int(hop_seconds * sample_rate)

    meter = pyln.Meter(sample_rate)
    timeline = []

    n_samples = audio.shape[0]
    current_pos = 0

    while current_pos + window_samples <= n_samples:
        window = audio[current_pos : current_pos + window_samples]
        time_seconds = current_pos / sample_rate

        try:
            lufs_s = meter.integrated_loudness(window)
        except ValueError:
            # Window is too quiet
            lufs_s = -np.inf

        timeline.append((time_seconds, lufs_s))
        current_pos += hop_samples

    return timeline


def compute_gain_for_target(integrated_lufs: float, target_lufs: float) -> float:
    """Compute the gain adjustment needed to reach target loudness.

    Args:
        integrated_lufs: Current integrated loudness in LUFS
        target_lufs: Target loudness in LUFS

    Returns:
        Gain adjustment in dB (positive = make louder, negative = make quieter)
    """
    if np.isinf(integrated_lufs):
        return 0.0
    return target_lufs - integrated_lufs


def normalize_audio(
    audio: np.ndarray,
    sample_rate: int,
    target_lufs: float,
) -> Tuple[np.ndarray, float]:
    """Normalize audio to target LUFS level.

    Args:
        audio: Audio data
        sample_rate: Sample rate in Hz
        target_lufs: Target loudness in LUFS

    Returns:
        Tuple of (normalized_audio, gain_db_applied)
    """
    if audio.ndim == 1:
        audio_2d = audio.reshape(-1, 1)
    else:
        audio_2d = audio

    meter = pyln.Meter(sample_rate)

    try:
        current_lufs = meter.integrated_loudness(audio_2d)
    except ValueError:
        # Audio too quiet, return unchanged
        return audio, 0.0

    gain_db = compute_gain_for_target(current_lufs, target_lufs)

    # Apply gain
    gain_linear = 10 ** (gain_db / 20)
    normalized = audio * gain_linear

    return normalized, gain_db
