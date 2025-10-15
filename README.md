# Speech-to-CLI Push-to-Talk Daemon

Push-to-talk voice transcription helper for Linux desktops. Hold a configured key (Right Alt by default) to record audio, send it to OpenAI Whisper (`gpt-4o-transcribe`), and type the transcription into the active window via `xdotool`.

## Requirements
- Python 3.10 or newer
- `xdotool` installed on the system (`sudo apt install xdotool`)
- Permission to read `/dev/input/event*` (add your user to the `input` group or run with elevated privileges)
- An OpenAI API key with access to `gpt-4o-transcribe`

## Setup
```bash
git clone https://github.com/WindyBanana/speech-to-cli.git
cd speech-to-cli
cp .env.sample .env   # fill in OPENAI_API_KEY
./scripts/setup.sh
source .venv/bin/activate
```

The setup script creates the `.venv` virtual environment (if missing), upgrades `pip`, and installs dependencies from `requirements.txt`.

## Running
```bash
source .venv/bin/activate
python main.py
```

Hold the configured push-to-talk key (`config.PTT_KEY`) to start recording. Release the key (or wait 10 seconds) to submit the audio, transcribe it, and type the text. To automatically send Enter afterwards, leave `PRESS_ENTER = True` in `config.py`.

## Configuration
Adjust `config.py` to change:
- `PTT_KEY`: key name from `evdev.ecodes` (default `KEY_RIGHTALT`)
- `PRESS_ENTER`: whether to send the Enter key after typing the transcription
- `MODEL`: OpenAI transcription model (`gpt-4o-transcribe`)
- `AUDIO_SAMPLE_RATE`, `AUDIO_CHANNELS`, `MAX_RECORD_SECONDS`: audio capture parameters

Environment variables are loaded from `.env` using `python-dotenv`. At minimum, set `OPENAI_API_KEY`.
