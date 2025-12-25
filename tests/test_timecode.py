"""Tests for timecode utilities."""

import pytest
from mastering_copilot_cli.util.timecode import (
    seconds_to_timecode,
    timecode_to_seconds,
    format_time_range,
)


def test_seconds_to_timecode():
    """Test conversion from seconds to timecode."""
    assert seconds_to_timecode(0) == "00:00.000"
    assert seconds_to_timecode(1.5) == "00:01.500"
    assert seconds_to_timecode(65.123) == "01:05.123"
    assert seconds_to_timecode(3661.999) == "61:01.999"


def test_timecode_to_seconds():
    """Test conversion from timecode to seconds."""
    assert timecode_to_seconds("00:00.000") == 0.0
    assert timecode_to_seconds("00:01.500") == 1.5
    assert timecode_to_seconds("01:05.123") == 65.123
    assert abs(timecode_to_seconds("61:01.999") - 3661.999) < 0.001


def test_timecode_roundtrip():
    """Test that timecode conversion is reversible."""
    test_values = [0, 1.5, 60, 65.123, 3600]
    for seconds in test_values:
        timecode = seconds_to_timecode(seconds)
        result = timecode_to_seconds(timecode)
        assert abs(result - seconds) < 0.001


def test_format_time_range():
    """Test time range formatting."""
    result = format_time_range(10.5, 13.5)
    assert result == "00:10.500 - 00:13.500"

    result = format_time_range(65, 70)
    assert result == "01:05.000 - 01:10.000"


def test_invalid_timecode():
    """Test handling of invalid timecode format."""
    with pytest.raises(ValueError):
        timecode_to_seconds("invalid")

    with pytest.raises(ValueError):
        timecode_to_seconds("1:2:3")
