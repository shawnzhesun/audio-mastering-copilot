"""Generate a test audio file with varying loudness sections."""

import numpy as np
import soundfile as sf
from pathlib import Path


def generate_dynamic_test(output_path: Path, duration: float = 15.0, sr: int = 48000):
    """Generate test file with varying loudness sections.

    This creates a more realistic test that demonstrates platform normalization.

    Args:
        output_path: Where to save the file
        duration: Total duration in seconds
        sr: Sample rate
    """
    t = np.linspace(0, duration, int(sr * duration))

    # Create sections with different loudness levels
    section_duration = duration / 5  # 5 sections
    audio = np.zeros_like(t)

    for i in range(5):
        start_idx = int(i * section_duration * sr)
        end_idx = int((i + 1) * section_duration * sr)

        # Generate sine wave with varying amplitude
        section_t = t[start_idx:end_idx]

        # Different amplitudes for each section
        if i == 0:
            amp = 0.7  # Loud section
        elif i == 1:
            amp = 0.3  # Quiet section
        elif i == 2:
            amp = 0.9  # Very loud section
        elif i == 3:
            amp = 0.5  # Medium section
        else:
            amp = 0.4  # Quiet-medium section

        # Mix of frequencies for more realistic sound
        freq1 = 440.0  # A4
        freq2 = 880.0  # A5
        freq3 = 220.0  # A3

        section_audio = (
            amp * 0.5 * np.sin(2 * np.pi * freq1 * (section_t - section_t[0]))
            + amp * 0.3 * np.sin(2 * np.pi * freq2 * (section_t - section_t[0]))
            + amp * 0.2 * np.sin(2 * np.pi * freq3 * (section_t - section_t[0]))
        )

        # Add slight fade in/out to each section
        fade_len = int(0.05 * sr)  # 50ms fade
        if i > 0:
            fade_in = np.linspace(0, 1, fade_len)
            section_audio[:fade_len] *= fade_in
        if i < 4:
            fade_out = np.linspace(1, 0, fade_len)
            section_audio[-fade_len:] *= fade_out

        audio[start_idx:end_idx] = section_audio

    # Make stereo
    audio_stereo = np.stack([audio, audio], axis=1)

    sf.write(output_path, audio_stereo, sr)
    print(f"Generated dynamic test file: {output_path}")


if __name__ == "__main__":
    test_dir = Path(__file__).parent / "fixtures"
    test_dir.mkdir(exist_ok=True)

    generate_dynamic_test(test_dir / "test_dynamic_15s.wav", duration=15.0)
    print("Dynamic test audio file generated successfully!")
