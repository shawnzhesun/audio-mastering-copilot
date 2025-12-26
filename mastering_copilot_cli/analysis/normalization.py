"""Platform normalization simulation and prediction."""

from dataclasses import dataclass
from typing import List, Dict

import numpy as np

from mastering_copilot_cli.config.profiles import NormalizationProfile
from mastering_copilot_cli.analysis.sections import Section, SectionAnalysis


@dataclass
class NormalizationAction:
    """Action taken by platform normalization."""

    action_type: str  # 'none', 'reduce', 'boost', 'limit'
    gain_db: float  # Gain adjustment applied
    will_clip: bool  # Whether clipping will occur
    will_limit: bool  # Whether limiting will occur
    description: str  # Human-readable description


@dataclass
class SectionNormalization:
    """Normalization result for a section."""

    section: Section
    original_lufs: float
    target_lufs: float
    resulting_lufs: float  # After normalization
    original_peak_db: float
    target_peak_db: float
    resulting_peak_db: float  # After gain adjustment
    action: NormalizationAction


@dataclass
class PlatformNormalization:
    """Complete normalization simulation for a platform."""

    profile: NormalizationProfile
    overall_action: NormalizationAction
    section_results: List[SectionNormalization]
    will_sound_good: bool
    issues: List[str]  # List of potential issues


def simulate_normalization(
    profile: NormalizationProfile,
    integrated_lufs: float,
    peak_db: float,
    true_peak_db: float,
    section_analysis: SectionAnalysis,
) -> PlatformNormalization:
    """Simulate how a platform will normalize the audio.

    Args:
        profile: Platform normalization profile
        integrated_lufs: Overall integrated LUFS
        peak_db: Overall peak level
        true_peak_db: Overall true peak level
        section_analysis: Section-by-section analysis

    Returns:
        PlatformNormalization with detailed prediction
    """
    # Calculate required gain to reach target
    if np.isinf(integrated_lufs):
        gain_db = 0.0
    else:
        gain_db = profile.target_lufs - integrated_lufs

    # Determine overall action
    overall_action = _determine_action(
        gain_db=gain_db,
        peak_db=peak_db,
        true_peak_db=true_peak_db,
        profile=profile,
    )

    # Simulate per-section results
    section_results = []
    for section in section_analysis.sections:
        section_result = _simulate_section(section, gain_db, profile)
        section_results.append(section_result)

    # Analyze issues
    issues = _analyze_issues(overall_action, section_results, profile)

    # Determine if it will sound good
    will_sound_good = _evaluate_quality(overall_action, section_results, issues)

    return PlatformNormalization(
        profile=profile,
        overall_action=overall_action,
        section_results=section_results,
        will_sound_good=will_sound_good,
        issues=issues,
    )


def _determine_action(
    gain_db: float,
    peak_db: float,
    true_peak_db: float,
    profile: NormalizationProfile,
) -> NormalizationAction:
    """Determine what action the platform will take."""

    if not profile.applies_normalization:
        return NormalizationAction(
            action_type="none",
            gain_db=0.0,
            will_clip=False,
            will_limit=False,
            description="No normalization applied",
        )

    # Check if boost is needed
    if gain_db > 0:
        # Need to boost
        if profile.max_boost_db is not None and gain_db > profile.max_boost_db:
            # Boost capped
            actual_gain = profile.max_boost_db
            return NormalizationAction(
                action_type="none",  # No boost applied
                gain_db=0.0,
                will_clip=False,
                will_limit=False,
                description=f"No change (quieter than target by {-gain_db:.1f} dB)",
            )
        else:
            # Check if boosting will cause peaks to exceed limit
            resulting_peak = true_peak_db + gain_db

            if resulting_peak > profile.true_peak_limit:
                if profile.limiter_on_boost:
                    return NormalizationAction(
                        action_type="limit",
                        gain_db=gain_db,
                        will_clip=False,
                        will_limit=True,
                        description=f"Boosted by {gain_db:.1f} dB with limiting",
                    )
                else:
                    # Can't boost without exceeding peak limit
                    return NormalizationAction(
                        action_type="none",
                        gain_db=0.0,
                        will_clip=False,
                        will_limit=False,
                        description=f"No boost (would exceed {profile.true_peak_limit:.1f} dBTP)",
                    )
            else:
                return NormalizationAction(
                    action_type="boost",
                    gain_db=gain_db,
                    will_clip=False,
                    will_limit=False,
                    description=f"Boosted by {gain_db:.1f} dB",
                )

    elif gain_db < -0.5:  # Need to reduce (with some threshold)
        return NormalizationAction(
            action_type="reduce",
            gain_db=gain_db,
            will_clip=False,
            will_limit=False,
            description=f"Reduced by {-gain_db:.1f} dB",
        )

    else:
        # Within tolerance
        return NormalizationAction(
            action_type="none",
            gain_db=0.0,
            will_clip=False,
            will_limit=False,
            description="No change (at target)",
        )


def _simulate_section(
    section: Section,
    gain_db: float,
    profile: NormalizationProfile,
) -> SectionNormalization:
    """Simulate normalization for a single section."""

    resulting_lufs = section.integrated_lufs + gain_db if not np.isinf(
        section.integrated_lufs
    ) else section.integrated_lufs
    resulting_peak_db = section.peak_db + gain_db

    # Determine action for this section
    if gain_db > 0:
        if resulting_peak_db > profile.true_peak_limit:
            action_type = "limit" if profile.limiter_on_boost else "clip_risk"
        else:
            action_type = "boost"
    elif gain_db < -0.5:
        action_type = "reduce"
    else:
        action_type = "none"

    will_clip = resulting_peak_db > 0.0
    will_limit = action_type == "limit"

    action = NormalizationAction(
        action_type=action_type,
        gain_db=gain_db,
        will_clip=will_clip,
        will_limit=will_limit,
        description=action_type,
    )

    return SectionNormalization(
        section=section,
        original_lufs=section.integrated_lufs,
        target_lufs=profile.target_lufs,
        resulting_lufs=resulting_lufs,
        original_peak_db=section.peak_db,
        target_peak_db=profile.true_peak_limit,
        resulting_peak_db=resulting_peak_db,
        action=action,
    )


def _analyze_issues(
    overall_action: NormalizationAction,
    section_results: List[SectionNormalization],
    profile: NormalizationProfile,
) -> List[str]:
    """Analyze potential issues with normalization."""

    issues = []

    # Check for clipping
    if overall_action.will_clip:
        issues.append("⚠ Will cause clipping")

    # Check for limiting
    if overall_action.will_limit:
        issues.append(f"Platform will apply limiting")

    # Check if track is much louder than target
    if overall_action.action_type == "reduce":
        issues.append(
            f"Track is {-overall_action.gain_db:.1f} dB louder than target" + (" - significant volume reduction" if overall_action.gain_db < -3.0 else " - volume reduction applied")   
        )

    # Check for hot sections
    hot_sections = [
        s for s in section_results if s.resulting_peak_db > profile.true_peak_limit
    ]
    if hot_sections and not profile.limiter_on_boost:
        issues.append(
            f"{len(hot_sections)} section(s) will exceed {profile.true_peak_limit:.1f} dBTP"
        )

    return issues


def _evaluate_quality(
    overall_action: NormalizationAction,
    section_results: List[SectionNormalization],
    issues: List[str],
) -> bool:
    """Evaluate if the normalized audio will sound good."""

    # Bad if clipping or major issues
    if overall_action.will_clip:
        return False

    if len(issues) > 2:
        return False

    # Good if no action needed or only minor reduction
    if overall_action.action_type in ["none", "reduce"]:
        if overall_action.gain_db > -6.0:
            return True

    # Check sections
    problematic_sections = [
        s for s in section_results if s.action.will_clip or s.action.will_limit
    ]

    if len(problematic_sections) > len(section_results) * 0.2:  # More than 20%
        return False

    return True


def compare_platforms(
    platforms: List[NormalizationProfile],
    integrated_lufs: float,
    peak_db: float,
    true_peak_db: float,
    section_analysis: SectionAnalysis,
) -> Dict[str, PlatformNormalization]:
    """Compare normalization across multiple platforms.

    Args:
        platforms: List of platform profiles
        integrated_lufs: Overall integrated LUFS
        peak_db: Overall peak level
        true_peak_db: Overall true peak level
        section_analysis: Section analysis

    Returns:
        Dictionary mapping platform name to normalization result
    """
    results = {}

    for profile in platforms:
        result = simulate_normalization(
            profile, integrated_lufs, peak_db, true_peak_db, section_analysis
        )
        results[profile.name] = result

    return results
