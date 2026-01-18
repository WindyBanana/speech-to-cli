# Speech-to-CLI

Cross-platform push-to-talk speech recognition that types into any application. Hold a key to record, release to transcribe via OpenAI Whisper and type the result into the focused window.

## Supported Platforms

| Platform | Input Method | Typing Method | Status |
|----------|-------------|---------------|--------|
| Linux    | evdev       | xdotool       | Stable |
| macOS    | pynput      | pynput        | Beta   |
| Windows  | pynput      | pynput        | Beta   |

## Requirements

- Python 3.10+
- OpenAI API key with access to `gpt-4o-transcribe`
- Platform-specific requirements below

## Installation

### macOS (Homebrew)

```bash
brew tap WindyBanana/tap
brew install speech-to-cli
```

Or install manually:

```bash
pip install speech-to-cli[macos]
```

**Important:** Grant Accessibility permissions in System Preferences > Privacy & Security > Accessibility for your terminal app.

### Linux

```bash
# Install system dependencies (Debian/Ubuntu)
sudo apt install xdotool libportaudio2 portaudio19-dev

# Add yourself to the input group
sudo usermod -aG input $USER
newgrp input  # or log out and back in

# Install the package
pip install speech-to-cli[linux]
```

### Windows

Download the latest `.exe` from [Releases](https://github.com/WindyBanana/speech-to-cli/releases), or install via pip:

```bash
pip install speech-to-cli[windows]
```

## Configuration

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

Or create a `.env` file:

```
OPENAI_API_KEY=your-api-key
```

## Usage

```bash
speech-to-cli                     # Run with defaults
speech-to-cli --key f13           # Use F13 as PTT key
speech-to-cli --no-enter          # Don't press Enter after typing
speech-to-cli --verbose           # Enable debug logging
```

### Default PTT Keys

| Platform | Default Key      |
|----------|------------------|
| Linux    | Right Shift      |
| macOS    | Right Shift      |
| Windows  | Right Shift      |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `SPEECH_PTT_KEY` | Push-to-talk key name | Platform default |
| `SPEECH_PRESS_ENTER` | Press Enter after typing | true |
| `SPEECH_MODEL` | Whisper model | gpt-4o-transcribe |
| `SPEECH_LANGUAGE` | Language code | en |
| `SPEECH_MAX_SECONDS` | Max recording duration | 60 |
| `SPEECH_LOG_LEVEL` | Log level | INFO |
| `SPEECH_LOG_TRANSCRIPTS` | Log transcription text | false |

## Development

```bash
# Clone and install in development mode
git clone https://github.com/WindyBanana/speech-to-cli.git
cd speech-to-cli

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install with development dependencies
pip install -e ".[dev,linux]"  # or [dev,macos] or [dev,windows]

# Run tests
pytest

# Run linting
ruff check src/
mypy src/
```

### Building Windows Executable

```bash
pip install pyinstaller
python packaging/windows/build.py
```

The executable will be in `dist/speech-to-cli.exe`.

## Troubleshooting

### macOS: "Input not being detected"
Grant Accessibility permissions to your terminal in System Preferences > Privacy & Security > Accessibility.

### Linux: "No input devices found"
Add your user to the `input` group:
```bash
sudo usermod -aG input $USER
newgrp input
```

### Linux: "xdotool not found"
Install xdotool:
```bash
sudo apt install xdotool
```

### All platforms: "API key not set"
Set `OPENAI_API_KEY` in your environment or `.env` file.

## License

MIT
