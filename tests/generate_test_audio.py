"""Generate test audio files for testing."""

import numpy as np
import soundfile as sf
from pathlib import Path


def generate_test_wav(output_path: Path, duration: float = 1.0, sr: int = 48000):
    """Generate a simple test WAV file with a sine wave.

    Args:
        output_path: Where to save the file
        duration: Duration in seconds
        sr: Sample rate
    """
    t = np.linspace(0, duration, int(sr * duration))

    # Generate 440Hz sine wave (A4 note)
    frequency = 440.0
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)

    # Make stereo
    audio_stereo = np.stack([audio, audio], axis=1)

    sf.write(output_path, audio_stereo, sr)
    print(f"Generated test file: {output_path}")


if __name__ == "__main__":
    test_dir = Path(__file__).parent / "fixtures"
    test_dir.mkdir(exist_ok=True)

    generate_test_wav(test_dir / "test_sine_1s.wav", duration=1.0)
    generate_test_wav(test_dir / "test_sine_5s.wav", duration=5.0)
    print("Test audio files generated successfully!")
