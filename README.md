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

This project is in active development. See [Plan.md](Plan.md) for the implementation roadmap.

## License

MIT
