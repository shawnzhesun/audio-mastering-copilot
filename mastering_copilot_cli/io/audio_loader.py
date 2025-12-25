"""Audio file loading with fallback to ffmpeg for non-WAV formats."""

from pathlib import Path
import subprocess
import tempfile
from typing import Tuple

import numpy as np
import soundfile as sf


class AudioLoadError(Exception):
    """Raised when audio file cannot be loaded."""
    pass


def load_audio(file_path: str | Path) -> Tuple[np.ndarray, int]:
    """Load audio file and return as float32 numpy array.

    Tries soundfile first for WAV files, falls back to ffmpeg for other formats.

    Args:
        file_path: Path to audio file

    Returns:
        Tuple of (audio_data, sample_rate) where:
        - audio_data: np.ndarray of shape (n_samples, n_channels) or (n_samples,) for mono
        - sample_rate: Sample rate in Hz

    Raises:
        AudioLoadError: If file cannot be loaded
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise AudioLoadError(f"File not found: {file_path}")

    # Try soundfile first (works for WAV, FLAC, OGG)
    try:
        audio, sr = sf.read(str(file_path), dtype="float32", always_2d=False)
        return audio, sr
    except Exception as e:
        # Fall back to ffmpeg for other formats (MP3, M4A, etc.)
        try:
            return _load_with_ffmpeg(file_path)
        except Exception as ffmpeg_error:
            raise AudioLoadError(
                f"Failed to load audio with both soundfile and ffmpeg.\n"
                f"soundfile error: {e}\n"
                f"ffmpeg error: {ffmpeg_error}"
            )


def _load_with_ffmpeg(file_path: Path) -> Tuple[np.ndarray, int]:
    """Load audio using ffmpeg.

    Args:
        file_path: Path to audio file

    Returns:
        Tuple of (audio_data, sample_rate)

    Raises:
        AudioLoadError: If ffmpeg fails
    """
    # First, probe to get sample rate and channel count
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate,channels",
        "-of", "default=noprint_wrappers=1",
        str(file_path),
    ]

    try:
        probe_result = subprocess.run(
            probe_cmd, capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise AudioLoadError(f"ffprobe failed: {e}")

    # Parse probe output
    probe_lines = probe_result.stdout.strip().split("\n")
    metadata = dict(line.split("=") for line in probe_lines if "=" in line)

    try:
        sample_rate = int(metadata["sample_rate"])
        channels = int(metadata["channels"])
    except (KeyError, ValueError) as e:
        raise AudioLoadError(f"Failed to parse audio metadata: {e}")

    # Decode to PCM float32
    with tempfile.NamedTemporaryFile(suffix=".f32", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", str(file_path),
            "-f", "f32le",
            "-acodec", "pcm_f32le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            "-y",
            tmp_path,
        ]

        subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            check=True,
            stderr=subprocess.DEVNULL,
        )

        # Read raw PCM data
        audio = np.fromfile(tmp_path, dtype=np.float32)

        # Reshape to (n_samples, n_channels) or keep 1D for mono
        if channels > 1:
            audio = audio.reshape(-1, channels)

        return audio, sample_rate

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise AudioLoadError(f"ffmpeg decode failed: {e}")
    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


def get_audio_info(file_path: str | Path) -> dict:
    """Get basic audio file information without loading the entire file.

    Args:
        file_path: Path to audio file

    Returns:
        Dictionary with keys: duration, sample_rate, channels, format
    """
    file_path = Path(file_path)

    try:
        info = sf.info(str(file_path))
        return {
            "duration": info.duration,
            "sample_rate": info.samplerate,
            "channels": info.channels,
            "format": info.format,
        }
    except Exception:
        # Fall back to ffprobe
        try:
            return _get_info_with_ffprobe(file_path)
        except Exception as e:
            raise AudioLoadError(f"Failed to get audio info: {e}")


def _get_info_with_ffprobe(file_path: Path) -> dict:
    """Get audio info using ffprobe.

    Args:
        file_path: Path to audio file

    Returns:
        Dictionary with audio information
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=duration,sample_rate,channels:format=format_name",
        "-of", "default=noprint_wrappers=1",
        str(file_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise AudioLoadError(f"ffprobe failed: {e}")

    # Parse output
    lines = result.stdout.strip().split("\n")
    metadata = dict(line.split("=") for line in lines if "=" in line)

    return {
        "duration": float(metadata.get("duration", 0)),
        "sample_rate": int(metadata.get("sample_rate", 0)),
        "channels": int(metadata.get("channels", 0)),
        "format": metadata.get("format_name", "unknown"),
    }
