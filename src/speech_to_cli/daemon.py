"""Push-to-talk daemon that coordinates recording, transcription, and typing."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional

from openai import OpenAI

from .audio import AudioRecorder, save_wav
from .config import Config
from .platforms import PlatformHandler, get_platform_handler
from .transcription import Transcriber


class PushToTalkDaemon:
    """Main daemon that handles push-to-talk speech recognition."""

    def __init__(self, client: OpenAI, config: Config) -> None:
        self._config = config
        self._logger = logging.getLogger(self.__class__.__name__)

        # Initialize components
        self._recorder = AudioRecorder(
            sample_rate=config.sample_rate,
            channels=config.channels,
            max_seconds=config.max_record_seconds,
        )
        self._transcriber = Transcriber(
            client=client,
            model=config.model,
            language=config.language,
            log_transcripts=config.log_transcripts,
        )
        self._platform: Optional[PlatformHandler] = None
        self._running = False
        self._check_thread: Optional[threading.Thread] = None

    def _on_key_event(self, is_pressed: bool) -> None:
        """Handle key press/release events."""
        if is_pressed:
            self._on_key_down()
        else:
            self._on_key_up()

    def _on_key_down(self) -> None:
        """Start recording when the PTT key is pressed."""
        if self._recorder.recording:
            return
        try:
            self._recorder.start()
        except Exception as exc:
            self._logger.error("Failed to start recording: %s", exc, exc_info=True)

    def _on_key_up(self) -> None:
        """Stop recording and process when the PTT key is released."""
        if not self._recorder.recording:
            return
        self._finalize_recording()

    def _finalize_recording(self) -> None:
        """Stop recording, transcribe, and type the result."""
        audio = self._recorder.stop()
        if audio is None:
            return

        # Save to WAV file
        wav_path = save_wav(
            audio,
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
        )

        try:
            # Transcribe
            transcript = self._transcriber.transcribe(wav_path)
            if transcript and self._platform:
                # Release the PTT key if configured (prevents stuck keys)
                if self._config.ptt_keysym:
                    self._platform.release_key(self._config.ptt_keysym)

                # Type the result
                self._platform.type_text(transcript, press_enter=self._config.press_enter)
        finally:
            # Clean up temporary file
            try:
                wav_path.unlink(missing_ok=True)
            except Exception as exc:
                self._logger.warning(
                    "Failed to remove temporary audio file %s: %s", wav_path, exc
                )

    def _duration_check_loop(self) -> None:
        """Background thread to check if max recording duration is reached."""
        import time

        while self._running:
            if self._recorder.recording and self._recorder.has_reached_max_duration():
                self._logger.info("Maximum recording duration reached.")
                self._finalize_recording()
            time.sleep(0.1)

    def run(self) -> None:
        """Start the daemon."""
        self._platform = get_platform_handler()
        self._running = True

        # Start background thread for duration checking
        self._check_thread = threading.Thread(target=self._duration_check_loop, daemon=True)
        self._check_thread.start()

        self._logger.info("Starting push-to-talk daemon...")

        try:
            # This blocks until stop_listening is called or interrupted
            self._platform.start_listening(
                key_name=self._config.ptt_key,
                callback=self._on_key_event,
            )
        finally:
            self._running = False
            if self._check_thread:
                self._check_thread.join(timeout=1.0)

    def stop(self) -> None:
        """Stop the daemon."""
        self._running = False
        if self._platform:
            self._platform.stop_listening()
