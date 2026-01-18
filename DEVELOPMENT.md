# Speech-to-CLI Development Roadmap

This document describes the project architecture, current status, and remaining work for full cross-platform support.

## Project Overview

Speech-to-CLI is a push-to-talk speech recognition daemon that:
1. Listens for a configurable hotkey
2. Records audio while the key is held
3. Sends audio to OpenAI Whisper for transcription
4. Types the result into the currently focused window

## Architecture

### Directory Structure

```
speech-to-cli/
├── src/speech_to_cli/          # Main package (NEW - cross-platform)
│   ├── __init__.py             # Package init, version
│   ├── cli.py                  # CLI entry point with argparse
│   ├── config.py               # Dataclass-based configuration
│   ├── daemon.py               # Main orchestration logic
│   ├── audio.py                # Audio recording (cross-platform via sounddevice)
│   ├── transcription.py        # OpenAI Whisper API integration
│   └── platforms/              # Platform-specific implementations
│       ├── __init__.py         # Platform detection + base interface
│       ├── linux.py            # Linux: evdev + xdotool
│       ├── macos.py            # macOS: pynput
│       └── windows.py          # Windows: pynput
├── packaging/                  # Distribution files
│   ├── homebrew/
│   │   └── speech-to-cli.rb    # Homebrew formula for macOS
│   ├── linux/
│   │   └── speech-to-cli.service  # systemd user service
│   └── windows/
│       └── build.py            # PyInstaller build script
├── main.py                     # Legacy entry point (Linux only)
├── config.py                   # Legacy config (Linux only)
├── features.py                 # Legacy features enum
├── pyproject.toml              # Modern Python packaging
├── requirements.txt            # Legacy requirements
└── README.md                   # User documentation
```

### Platform Abstraction

The `platforms/` module provides a common interface for platform-specific operations:

```python
class PlatformHandler(ABC):
    def start_listening(self, key_name: str, callback: KeyCallback) -> None
    def stop_listening(self) -> None
    def type_text(self, text: str, press_enter: bool = False) -> None
    def release_key(self, key_name: str) -> None
```

**Platform detection** happens automatically via `sys.platform`:
- `linux` → `LinuxHandler` (evdev + xdotool)
- `darwin` → `MacOSHandler` (pynput)
- `win32` → `WindowsHandler` (pynput)

### Dependencies by Platform

| Dependency | Linux | macOS | Windows | Purpose |
|------------|-------|-------|---------|---------|
| numpy | ✓ | ✓ | ✓ | Audio array handling |
| sounddevice | ✓ | ✓ | ✓ | Audio recording |
| openai | ✓ | ✓ | ✓ | Whisper API |
| python-dotenv | ✓ | ✓ | ✓ | Environment config |
| evdev | ✓ | - | - | Linux input devices |
| pynput | - | ✓ | ✓ | Keyboard hooks |

System dependencies:
- **Linux**: `xdotool`, `libportaudio2`, membership in `input` group
- **macOS**: Accessibility permissions, `portaudio` (via Homebrew)
- **Windows**: None (pynput handles everything)

---

## Status & TODO

### Completed ✓

- [x] Restructure codebase into `src/speech_to_cli/` package
- [x] Create platform abstraction layer (`PlatformHandler` interface)
- [x] Implement Linux handler (evdev + xdotool) - migrated from original
- [x] Implement macOS handler (pynput)
- [x] Implement Windows handler (pynput)
- [x] Create shared audio recording module
- [x] Create shared transcription module
- [x] Add dataclass-based configuration with env var support
- [x] Create CLI with argparse (--key, --enter/--no-enter, --verbose, etc.)
- [x] Create `pyproject.toml` for modern packaging
- [x] Update `.gitignore` for build artifacts
- [x] Update `README.md` with cross-platform instructions
- [x] Create Homebrew formula template
- [x] Create PyInstaller build script
- [x] Create systemd service file
- [x] Add APIConnectionError handling for better error messages
- [x] Push to GitHub on `feature/cross-platform-support` branch

### Remaining - macOS

- [ ] **Test on actual macOS hardware**
  - Install: `pip install -e ".[macos]"`
  - Run: `speech-to-cli --verbose`
  - Verify Accessibility permissions prompt appears
  - Test PTT key detection
  - Test text typing into various apps
- [ ] Test Homebrew formula installation
- [ ] Update Homebrew formula SHA256 hash for release
- [ ] Test different PTT keys (F13, etc.)
- [ ] Verify audio recording works (portaudio)

### Remaining - Windows

- [ ] **Test on actual Windows hardware**
  - Install: `pip install -e ".[windows]"`
  - Run: `speech-to-cli --verbose`
  - Test PTT key detection
  - Test text typing into various apps
- [ ] Run PyInstaller build: `python packaging/windows/build.py`
- [ ] Test the generated .exe
- [ ] Test on Windows 10 and Windows 11
- [ ] Consider creating Inno Setup installer (optional)
- [ ] Test if admin privileges are needed for keyboard hooks
- [ ] Add to Windows startup (optional feature)

### Remaining - Linux

- [ ] Test new package structure on Linux (install from pyproject.toml)
- [ ] Verify systemd service works
- [ ] Test `pip install speech-to-cli[linux]` flow

### Remaining - General

- [ ] Add unit tests for shared modules (audio, transcription, config)
- [ ] Add integration tests per platform
- [ ] Set up GitHub Actions for CI
  - Lint with ruff
  - Type check with mypy
  - Run tests
- [ ] Create GitHub Release workflow
  - Build Windows .exe
  - Update Homebrew formula
- [ ] Publish to PyPI
- [ ] Add Wayland support for Linux (currently X11 only via xdotool)

### Future Enhancements (Nice to Have)

- [ ] System tray icon for Windows/macOS
- [ ] GUI settings panel
- [ ] Multiple language support (configurable per-session)
- [ ] Local Whisper model option (offline mode)
- [ ] Custom post-processing (commands, macros)
- [ ] Audio level indicator

---

## How to Continue Development

### Setting Up

```bash
cd /home/erikn/git/speech-to-cli-cross-platform
git checkout feature/cross-platform-support

# Create venv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,linux]"  # or [dev,macos] or [dev,windows]
```

### Testing Locally

```bash
# Set API key
export OPENAI_API_KEY="your-key"

# Run with verbose output
speech-to-cli --verbose

# Or run directly
python -m speech_to_cli.cli --verbose
```

### Key Files to Modify

| Task | File(s) |
|------|---------|
| Change platform behavior | `src/speech_to_cli/platforms/{linux,macos,windows}.py` |
| Add CLI options | `src/speech_to_cli/cli.py` |
| Change config defaults | `src/speech_to_cli/config.py` |
| Fix audio issues | `src/speech_to_cli/audio.py` |
| Fix transcription | `src/speech_to_cli/transcription.py` |
| Update dependencies | `pyproject.toml` |

### Platform-Specific Notes

**Linux:**
- Uses `evdev` for raw input device access (requires `input` group)
- Uses `xdotool` for typing (X11 only, no Wayland)
- Key names are evdev format: `KEY_RIGHTSHIFT`, `KEY_PAUSE`, etc.

**macOS:**
- Uses `pynput` which requires Accessibility permissions
- User must grant permission in System Preferences > Privacy & Security > Accessibility
- Key names are pynput format: `shift_r`, `f13`, `pause`, etc.

**Windows:**
- Uses `pynput` which should work without special permissions
- May need to run as Administrator for some key combinations
- Key names same as macOS: `shift_r`, `f13`, `pause`, etc.

---

## Git Workflow

```bash
# Current branch
git branch  # feature/cross-platform-support

# After testing, merge to master
git checkout master
git merge feature/cross-platform-support
git push origin master

# Tag a release
git tag -a v0.2.0 -m "Cross-platform support"
git push origin v0.2.0
```

## Repository Info

- **GitHub**: https://github.com/WindyBanana/speech-to-cli
- **Branch**: `feature/cross-platform-support`
- **Old local repo** (Linux-only, disconnected): `/home/erikn/git/speech-to-cli`
- **New cross-platform repo**: `/home/erikn/git/speech-to-cli-cross-platform`
