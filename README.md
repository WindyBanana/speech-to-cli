# Speech-to-CLI Push-to-Talk Daemon

Push-to-talk voice transcription helper for Linux desktops. Hold a configured key (Right Alt by default) to record audio, send it to OpenAI Whisper (`gpt-4o-transcribe`), and type the transcription into the active window via `xdotool`.

## Requirements
- Python 3.10 or newer
- Python venv tooling (`sudo apt install python3.12-venv` on Debian/Ubuntu; older releases may use `python3-venv`)
- `xdotool` installed on the system (`sudo apt install xdotool`)
- PortAudio runtime/dev packages (`sudo apt install libportaudio2 portaudio19-dev`)
- Permission to read `/dev/input/event*` (add your user to the `input` group or run with elevated privileges)
- Add the user to the input group (`sudo usermod -aG input $USER`)
- An OpenAI API key with access to `gpt-4o-transcribe`

## Setup
1. Clone the repository:  
   ```bash
   git clone https://github.com/WindyBanana/speech-to-cli.git
   cd speech-to-cli
   ```
2. Copy the environment template and add your OpenAI key:  
   ```bash
   cp .env.sample .env
   nano .env  # or your preferred editor
   ```
   Replace `your_openai_api_key_here` with a valid `OPENAI_API_KEY`.
3. Create the virtual environment and install dependencies:  
   ```bash
   ./scripts/setup.sh
   ```
   This script creates (or reuses) `.venv`, upgrades `pip`, and installs everything from `requirements.txt`.  
   If you see `ensurepip is not available`, install the venv tooling and re-run:
   ```bash
   sudo apt install python3.12-venv   # or python3-venv on older distros
   rm -rf .venv
   ./scripts/setup.sh
   ```
4. Activate the environment whenever you work on the project:  
   ```bash
   source .venv/bin/activate
   ```

## Keyboard Input Permissions
You must be able to read keyboard events from `/dev/input/event*`. On most Debian/Ubuntu systems this means joining the `input` group:
```bash
sudo usermod -aG input $USER
newgrp input      # start a shell with the new group, or log out/in
```
If you skip the `usermod` command, the daemon will fail with `PermissionError` when trying to read `/dev/input/event*`.
Verify membership with `id` or `groups`; you should see `input` listed.

If `python main.py` fails with “PortAudio library not found”, install the PortAudio runtime/dev packages and rerun setup:
```bash
sudo apt install libportaudio2 portaudio19-dev
./scripts/setup.sh
```

## Running
```bash
source .venv/bin/activate
python main.py
```

Hold the configured push-to-talk key (`config.PTT_KEY`) to start recording. Release the key (or wait 10 seconds) to submit the audio, transcribe it, and type the text. To automatically send Enter afterwards, leave `PRESS_ENTER = True` in `config.py`.

When you're done, stop the script with `Ctrl+C` and leave the virtual environment with:
```bash
deactivate
```

## Configuration
Adjust `config.py` to change:
- `PTT_KEY`: key name from `evdev.ecodes` (default `KEY_RIGHTALT`)
- `PTT_KEYSYM`: X11 keysym sent to `xdotool keyup` before typing (set to `None` if your push-to-talk key is not a modifier)
- `PRESS_ENTER`: whether to send the Enter key after typing the transcription
- `MODEL`: OpenAI transcription model (`gpt-4o-transcribe`)
- `AUDIO_SAMPLE_RATE`, `AUDIO_CHANNELS`, `MAX_RECORD_SECONDS`: audio capture parameters

Environment variables are loaded from `.env` using `python-dotenv`. At minimum, set `OPENAI_API_KEY`.

### Optional Logging Tweaks
`config.py` exposes a few switches:
- `LOG_LEVEL`: set to `logging.WARNING` (or `"WARNING"`) to quiet most console output.
- `LOG_FORMAT`: defaults to `%(message)s` to avoid timestamps; change as desired.
- `LOG_TRANSCRIPTS`: set `True` if you want the recognized text logged to the console as well as typed via `xdotool`.

To keep the daemon running while you use other apps, start it in one terminal (or background it with `nohup python main.py &`) and switch focus to the target window before releasing the push-to-talk key.
