"""Timecode conversion utilities."""


def seconds_to_timecode(seconds: float) -> str:
    """Convert seconds to MM:SS.mmm format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timecode string
    """
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:06.3f}"


def timecode_to_seconds(timecode: str) -> float:
    """Convert MM:SS.mmm format to seconds.

    Args:
        timecode: Formatted timecode string

    Returns:
        Time in seconds
    """
    parts = timecode.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid timecode format: {timecode}")

    minutes = int(parts[0])
    seconds = float(parts[1])

    return minutes * 60 + seconds


def format_time_range(start_sec: float, end_sec: float) -> str:
    """Format a time range.

    Args:
        start_sec: Start time in seconds
        end_sec: End time in seconds

    Returns:
        Formatted range string like "01:23.456 - 01:26.456"
    """
    return f"{seconds_to_timecode(start_sec)} - {seconds_to_timecode(end_sec)}"
