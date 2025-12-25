# Mastering Copilot

A terminal-native audio mastering analysis CLI that provides actionable insights for music production.

## Features

- LUFS (BS.1770) loudness analysis with integrated and short-term measurements
- True peak detection and approximation
- Platform-specific normalization simulation (Spotify, YouTube, etc.)
- Section-by-section analysis with timeline visualization
- Rule-based mastering suggestions
- Terminal-native visualizations using sparklines and tables

## Installation

```bash
uv sync
```

## Quick Start

Analyze an audio file:

```bash
mastering-copilot analyze input.wav
```

Check against specific targets:

```bash
mastering-copilot check input.wav --target -14 --tp -1.0
```

Analyze with platform profiles:

```bash
mastering-copilot analyze input.wav --profile spotify --profile netease
```

## Requirements

- Python 3.9+
- FFmpeg (for non-WAV format support)

## Development Status

- [x] Create skeleton CLI with Typer (Milestone 1)
- [x] Add loudness metrics with pyloudnorm (Milestone 2)
- [x] Implement peaks and true peak approximation (Milestone 3)
- [x] Add profiles configuration and normalization simulation (Milestone 4)
- [] Implement segmentation and worst sections analysis (Milestone 5)
- [] Add mastering suggestions functionality (Milestone 6)

## License

MIT
