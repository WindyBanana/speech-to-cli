from __future__ import annotations

import logging
import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Iterable, Optional

import evdev
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from evdev import InputDevice, ecodes
from openai import OpenAI

import config


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    log_format = getattr(config, "LOG_FORMAT", "%(levelname)s: %(message)s")
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    level = getattr(config, "LOG_LEVEL", logging.INFO)
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)


class AudioRecorder:
    def __init__(self, sample_rate: int, channels: int, max_seconds: int) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.max_seconds = max_seconds
        self._frames: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._start_time: Optional[float] = None
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        if self.recording:
            return
        self._frames = []
        self._start_time = time.time()

        def callback(indata, frames, time_info, status) -> None:  # type: ignore[no-untyped-def]
            if status:
                self._logger.warning("Audio stream status: %s", status)
            self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=callback,
        )
        self._stream.start()
        self._logger.info("Recording started.")

    def has_reached_max_duration(self) -> bool:
        if not self.recording or self._start_time is None:
            return False
        return (time.time() - self._start_time) >= self.max_seconds

    def stop(self) -> Optional[np.ndarray]:
        if not self.recording:
            return None
        if self._stream:
            self._stream.stop()
            self._stream.close()
        self._stream = None
        duration = 0.0
        if self._start_time is not None:
            duration = time.time() - self._start_time
        self._start_time = None
        if not self._frames:
            self._logger.warning("No audio frames captured.")
            return None
        audio = np.concatenate(self._frames, axis=0)
        self._frames = []
        self._logger.info("Recording stopped after %.2f seconds.", duration)
        return audio


class PushToTalkDaemon:
    def __init__(
        self,
        client: OpenAI,
        ptt_key_name: str,
        press_enter: bool,
        model: str,
        sample_rate: int,
        channels: int,
        max_seconds: int,
    ) -> None:
        self._client = client
        self._press_enter = press_enter
        self._model = model
        self._logger = logging.getLogger(self.__class__.__name__)
        self._recorder = AudioRecorder(sample_rate, channels, max_seconds)
        self._ptt_key_code = self._resolve_keycode(ptt_key_name)
        self._devices = self._discover_devices()
        self._fd_to_device: Dict[int, InputDevice] = {dev.fd: dev for dev in self._devices}
        if not self._devices:
            self._logger.error("No input devices found. Ensure you have permission to read /dev/input/event*.")  # noqa: E501
        else:
            for device in self._devices:
                self._logger.info("Listening on %s (%s)", device.path, device.name)

    def _resolve_keycode(self, key_name: str) -> int:
        try:
            return evdev.ecodes.ecodes[key_name]
        except KeyError as exc:
            raise ValueError(f"Unknown key name: {key_name}") from exc

    def _discover_devices(self) -> list[InputDevice]:
        devices = []
        for path in evdev.list_devices():
            try:
                device = InputDevice(path)
            except OSError as exc:
                logging.getLogger(self.__class__.__name__).warning(
                    "Skipping input device %s: %s", path, exc
                )
                continue
            caps = device.capabilities().get(ecodes.EV_KEY, [])
            key_codes: Iterable[int]
            if isinstance(caps, dict):
                key_codes = (code for codes in caps.values() for code in codes)
            else:
                key_codes = caps
            if self._ptt_key_code in set(key_codes):
                devices.append(device)
                continue
            if ecodes.EV_KEY in device.capabilities():
                devices.append(device)
        return devices

    def run(self) -> None:
        if not self._fd_to_device:
            return
        try:
            while True:
                self._check_recording_duration()
                ready, _, _ = select.select(self._fd_to_device.keys(), [], [], 0.1)
                for fd in ready:
                    device = self._fd_to_device.get(fd)
                    if not device:
                        continue
                    try:
                        for event in device.read():
                            self._handle_event(event)
                    except BlockingIOError:
                        continue
                    except OSError as exc:
                        self._logger.error("Device read error (%s): %s", device.path, exc)
        except KeyboardInterrupt:
            self._logger.info("Interrupted by user, exiting.")
        finally:
            self._cleanup()

    def _handle_event(self, event) -> None:
        if event.type != ecodes.EV_KEY:
            return
        if event.code != self._ptt_key_code:
            return
        if event.value == 1:  # key down
            self._on_key_down()
        elif event.value == 0:  # key up
            self._on_key_up()

    def _on_key_down(self) -> None:
        if self._recorder.recording:
            return
        try:
            self._recorder.start()
        except Exception as exc:
            self._logger.error("Failed to start recording: %s", exc, exc_info=True)

    def _on_key_up(self) -> None:
        if not self._recorder.recording:
            return
        self._finalize_recording()

    def _check_recording_duration(self) -> None:
        if self._recorder.recording and self._recorder.has_reached_max_duration():
            self._logger.info("Maximum recording duration reached.")
            self._finalize_recording()

    def _finalize_recording(self) -> None:
        audio = self._recorder.stop()
        if audio is None:
            return
        wav_path = self._write_wav(audio)
        try:
            transcript = self._transcribe(wav_path)
            if transcript:
                self._type_text(transcript)
        finally:
            try:
                wav_path.unlink(missing_ok=True)
            except Exception as exc:
                self._logger.warning("Failed to remove temporary audio file %s: %s", wav_path, exc)

    def _write_wav(self, audio: np.ndarray) -> Path:
        clipped = np.clip(audio, -1.0, 1.0)
        pcm = np.int16(clipped * 32767)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.close()
        path = Path(temp_file.name)
        with path.open("wb") as handle:
            self._write_wave_bytes(handle, pcm.tobytes())
        self._logger.info("Saved audio to %s", path)
        return path

    def _write_wave_bytes(self, handle, frames: bytes) -> None:
        import wave

        with wave.open(handle, "wb") as wf:
            wf.setnchannels(self._recorder.channels)
            wf.setsampwidth(2)
            wf.setframerate(self._recorder.sample_rate)
            wf.writeframes(frames)

    def _transcribe(self, wav_path: Path) -> str:
        self._logger.info("Submitting audio to OpenAI for transcription.")
        try:
            with wav_path.open("rb") as audio_file:
                response = self._client.audio.transcriptions.create(
                    model=self._model,
                    file=audio_file,
                    language="en",
                )
        except Exception as exc:
            self._logger.error("Transcription request failed: %s", exc, exc_info=True)
            return ""
        text = getattr(response, "text", "") or ""
        if text:
            if getattr(config, "LOG_TRANSCRIPTS", False):
                self._logger.info("Transcription received: %s", text)
            else:
                self._logger.info("Transcription received.")
        else:
            self._logger.warning("Transcription response did not contain text.")
        return text.strip()

    def _type_text(self, text: str) -> None:
        keysym = getattr(config, "PTT_KEYSYM", None)
        if keysym:
            try:
                subprocess.run(
                    ["xdotool", "keyup", "--clearmodifiers", keysym],
                    check=True,
                )
            except (FileNotFoundError, subprocess.CalledProcessError) as exc:
                self._logger.warning("Failed to send keyup for %s: %s", keysym, exc)
        cmd = ["xdotool", "type", "--delay", "0", "--clearmodifiers", text]
        try:
            subprocess.run(cmd, check=True)
            self._logger.info("Typed transcription into focused window.")
            if self._press_enter:
                subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], check=True)
                self._logger.info("Sent Enter key as configured.")
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            self._logger.error("Failed to send text via xdotool: %s", exc, exc_info=True)

    def _cleanup(self) -> None:
        for device in self._devices:
            try:
                device.close()
            except Exception:
                pass


def ensure_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Check your .env file.")
    return api_key


def main() -> int:
    configure_logging()
    load_dotenv()
    try:
        api_key = ensure_api_key()
    except RuntimeError as exc:
        logging.getLogger("main").error(str(exc))
        return 1

    client = OpenAI(api_key=api_key)
    daemon = PushToTalkDaemon(
        client=client,
        ptt_key_name=config.PTT_KEY,
        press_enter=config.PRESS_ENTER,
        model=config.MODEL,
        sample_rate=config.AUDIO_SAMPLE_RATE,
        channels=config.AUDIO_CHANNELS,
        max_seconds=config.MAX_RECORD_SECONDS,
    )
    daemon.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
