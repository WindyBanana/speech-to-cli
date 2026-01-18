"""Configuration management for speech-to-cli."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Optional


def get_default_ptt_key() -> str:
    """Get the default PTT key for the current platform."""
    if sys.platform == "linux":
        return "KEY_RIGHTSHIFT"
    elif sys.platform == "darwin":
        return "shift_r"  # pynput key name
    elif sys.platform == "win32":
        return "shift_r"
    return "shift_r"


def get_default_ptt_keysym() -> Optional[str]:
    """Get the default PTT keysym for key release (Linux only)."""
    if sys.platform == "linux":
        return "Shift_R"
    return None


@dataclass
class Config:
    """Application configuration."""

    # Push-to-talk settings
    ptt_key: str = field(default_factory=get_default_ptt_key)
    ptt_keysym: Optional[str] = field(default_factory=get_default_ptt_keysym)
    press_enter: bool = True

    # OpenAI settings
    model: str = "gpt-4o-transcribe"
    language: str = "en"

    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    max_record_seconds: int = 60

    # Logging settings
    log_level: int = logging.INFO
    log_format: str = "%(message)s"
    log_transcripts: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        config = cls()

        # Override with environment variables if present
        if ptt_key := os.getenv("SPEECH_PTT_KEY"):
            config.ptt_key = ptt_key
        if ptt_keysym := os.getenv("SPEECH_PTT_KEYSYM"):
            config.ptt_keysym = ptt_keysym if ptt_keysym.lower() != "none" else None
        if press_enter := os.getenv("SPEECH_PRESS_ENTER"):
            config.press_enter = press_enter.lower() in ("true", "1", "yes")
        if model := os.getenv("SPEECH_MODEL"):
            config.model = model
        if language := os.getenv("SPEECH_LANGUAGE"):
            config.language = language
        if sample_rate := os.getenv("SPEECH_SAMPLE_RATE"):
            config.sample_rate = int(sample_rate)
        if max_seconds := os.getenv("SPEECH_MAX_SECONDS"):
            config.max_record_seconds = int(max_seconds)
        if log_level := os.getenv("SPEECH_LOG_LEVEL"):
            config.log_level = getattr(logging, log_level.upper(), logging.INFO)
        if log_transcripts := os.getenv("SPEECH_LOG_TRANSCRIPTS"):
            config.log_transcripts = log_transcripts.lower() in ("true", "1", "yes")

        return config


def configure_logging(config: Config) -> None:
    """Set up logging with the given configuration."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(config.log_format)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(config.log_level)
    root.handlers.clear()
    root.addHandler(handler)
