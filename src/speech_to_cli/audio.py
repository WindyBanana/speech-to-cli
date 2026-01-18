"""Audio recording functionality."""

from __future__ import annotations

import logging
import tempfile
import time
import wave
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Records audio from the default input device."""

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
        """Check if currently recording."""
        return self._stream is not None

    def start(self) -> None:
        """Start recording audio."""
        if self.recording:
            return

        self._frames = []
        self._start_time = time.time()

        def callback(indata, frames, time_info, status) -> None:
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
        """Check if recording has reached the maximum duration."""
        if not self.recording or self._start_time is None:
            return False
        return (time.time() - self._start_time) >= self.max_seconds

    def stop(self) -> Optional[np.ndarray]:
        """Stop recording and return the audio data."""
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


def save_wav(audio: np.ndarray, sample_rate: int, channels: int) -> Path:
    """Save audio data to a temporary WAV file.

    Args:
        audio: Audio data as numpy array
        sample_rate: Sample rate in Hz
        channels: Number of audio channels

    Returns:
        Path to the temporary WAV file
    """
    logger = logging.getLogger("audio")

    # Clip and convert to 16-bit PCM
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = np.int16(clipped * 32767)

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file.close()
    path = Path(temp_file.name)

    # Write WAV file
    with path.open("wb") as handle:
        with wave.open(handle, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())

    logger.info("Saved audio to %s", path)
    return path
