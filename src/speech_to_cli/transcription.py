"""Speech transcription using OpenAI Whisper API."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from openai import APIConnectionError, OpenAI


class Transcriber:
    """Handles audio transcription via OpenAI's Whisper API."""

    def __init__(
        self,
        client: OpenAI,
        model: str = "whisper-1",
        language: str = "en",
        log_transcripts: bool = False,
    ) -> None:
        self._client = client
        self._model = model
        self._language = language
        self._log_transcripts = log_transcripts
        self._logger = logging.getLogger(self.__class__.__name__)

    def transcribe(self, wav_path: Path) -> str:
        """Transcribe audio from a WAV file.

        Args:
            wav_path: Path to the WAV file

        Returns:
            Transcribed text, or empty string on failure
        """
        self._logger.info("Submitting audio to OpenAI for transcription.")

        try:
            with wav_path.open("rb") as audio_file:
                response = self._client.audio.transcriptions.create(
                    model=self._model,
                    file=audio_file,
                    language=self._language,
                )
        except APIConnectionError as exc:
            self._logger.error(
                "Transcription failed: could not reach OpenAI (%s). "
                "Check your network/DNS or VPN/firewall settings.",
                exc,
            )
            return ""
        except Exception as exc:
            self._logger.error("Transcription request failed: %s", exc, exc_info=True)
            return ""

        text = getattr(response, "text", "") or ""
        if text:
            if self._log_transcripts:
                self._logger.info("Transcription received: %s", text)
            else:
                self._logger.info("Transcription received.")
        else:
            self._logger.warning("Transcription response did not contain text.")

        return text.strip()
