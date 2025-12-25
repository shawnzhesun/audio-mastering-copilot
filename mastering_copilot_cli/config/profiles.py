"""Platform normalization profiles for streaming services."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class NormalizationProfile:
    """Profile for a streaming platform's normalization behavior."""

    name: str
    display_name: str
    target_lufs: float
    true_peak_limit: float  # dBTP
    applies_normalization: bool
    limiter_on_boost: bool  # Whether limiting is applied when boosting
    max_boost_db: Optional[float] = None  # Maximum boost allowed (None = unlimited)
    description: str = ""


# Built-in platform profiles based on public documentation
BUILTIN_PROFILES: Dict[str, NormalizationProfile] = {
    "spotify": NormalizationProfile(
        name="spotify",
        display_name="Spotify",
        target_lufs=-14.0,
        true_peak_limit=-1.0,
        applies_normalization=True,
        limiter_on_boost=False,  # Spotify only turns down, doesn't boost by default
        max_boost_db=0.0,
        description="Spotify normalizes to -14 LUFS, only reduces volume (no boost)",
    ),
    "apple_music": NormalizationProfile(
        name="apple_music",
        display_name="Apple Music",
        target_lufs=-16.0,
        true_peak_limit=-1.0,
        applies_normalization=True,
        limiter_on_boost=False,
        max_boost_db=0.0,
        description="Apple Music normalizes to -16 LUFS, only reduces volume",
    ),
    "youtube": NormalizationProfile(
        name="youtube",
        display_name="YouTube",
        target_lufs=-14.0,
        true_peak_limit=-1.0,
        applies_normalization=True,
        limiter_on_boost=False,
        max_boost_db=0.0,
        description="YouTube normalizes to -14 LUFS, only reduces volume",
    ),
    "youtube_music": NormalizationProfile(
        name="youtube_music",
        display_name="YouTube Music",
        target_lufs=-14.0,
        true_peak_limit=-1.0,
        applies_normalization=True,
        limiter_on_boost=False,
        max_boost_db=0.0,
        description="YouTube Music normalizes to -14 LUFS",
    ),
    "tidal": NormalizationProfile(
        name="tidal",
        display_name="TIDAL",
        target_lufs=-14.0,
        true_peak_limit=-1.0,
        applies_normalization=True,
        limiter_on_boost=False,
        max_boost_db=0.0,
        description="TIDAL normalizes to -14 LUFS",
    ),
    "amazon_music": NormalizationProfile(
        name="amazon_music",
        display_name="Amazon Music",
        target_lufs=-14.0,
        true_peak_limit=-2.0,
        applies_normalization=True,
        limiter_on_boost=False,
        max_boost_db=0.0,
        description="Amazon Music normalizes to -14 LUFS",
    ),
    "deezer": NormalizationProfile(
        name="deezer",
        display_name="Deezer",
        target_lufs=-15.0,
        true_peak_limit=-1.0,
        applies_normalization=True,
        limiter_on_boost=False,
        max_boost_db=0.0,
        description="Deezer normalizes to -15 LUFS",
    ),
    "netease": NormalizationProfile(
        name="netease",
        display_name="NetEase Cloud Music",
        target_lufs=-13.0,
        true_peak_limit=-1.0,
        applies_normalization=True,
        limiter_on_boost=False,
        max_boost_db=0.0,
        description="NetEase Cloud Music normalizes to -13 LUFS (estimated)",
    ),
    "soundcloud": NormalizationProfile(
        name="soundcloud",
        display_name="SoundCloud",
        target_lufs=-14.0,
        true_peak_limit=-1.0,
        applies_normalization=True,
        limiter_on_boost=True,  # SoundCloud applies limiting when boosting
        max_boost_db=None,
        description="SoundCloud normalizes to -14 LUFS with limiting on boost",
    ),
    "cd": NormalizationProfile(
        name="cd",
        display_name="CD/WAV Master",
        target_lufs=-9.0,  # Typical mastering target for CD
        true_peak_limit=-0.3,
        applies_normalization=False,
        limiter_on_boost=False,
        description="Traditional CD mastering reference (-9 LUFS, -0.3 dBTP)",
    ),
}


def get_profile(name: str) -> Optional[NormalizationProfile]:
    """Get a platform profile by name.

    Args:
        name: Profile name (e.g., 'spotify', 'youtube')

    Returns:
        NormalizationProfile if found, None otherwise
    """
    return BUILTIN_PROFILES.get(name.lower())


def list_profiles() -> Dict[str, NormalizationProfile]:
    """Get all available profiles.

    Returns:
        Dictionary of profile name to NormalizationProfile
    """
    return BUILTIN_PROFILES.copy()


def get_profile_names() -> list[str]:
    """Get list of all profile names.

    Returns:
        List of profile names
    """
    return list(BUILTIN_PROFILES.keys())
