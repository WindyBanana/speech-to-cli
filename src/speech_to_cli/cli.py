"""Command-line interface for speech-to-cli."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from .config import Config, configure_logging
from .daemon import PushToTalkDaemon


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Push-to-talk speech recognition daemon.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  speech-to-cli                     # Run with default settings
  speech-to-cli --key f13           # Use F13 as PTT key
  speech-to-cli --no-enter          # Don't press Enter after typing

Environment variables:
  OPENAI_API_KEY        Required: Your OpenAI API key
  SPEECH_PTT_KEY        PTT key name (platform-specific)
  SPEECH_PRESS_ENTER    Press Enter after typing (true/false)
  SPEECH_MODEL          Whisper model (default: gpt-4o-transcribe)
  SPEECH_LANGUAGE       Language code (default: en)
  SPEECH_MAX_SECONDS    Max recording duration (default: 60)
  SPEECH_LOG_LEVEL      Log level (DEBUG/INFO/WARNING/ERROR)
  SPEECH_LOG_TRANSCRIPTS Log transcription text (true/false)
""",
    )
    parser.add_argument(
        "--key",
        "-k",
        help="Push-to-talk key name (e.g., f13, pause, shift_r)",
    )
    parser.add_argument(
        "--enter/--no-enter",
        dest="press_enter",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="Press Enter after typing the transcription",
    )
    parser.add_argument(
        "--model",
        "-m",
        help="Whisper model to use (default: gpt-4o-transcribe)",
    )
    parser.add_argument(
        "--language",
        "-l",
        help="Language code for transcription (default: en)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--log-transcripts",
        action="store_true",
        help="Log transcription text",
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Build configuration
    config = Config.from_env()

    # Override with CLI arguments
    if args.key:
        config.ptt_key = args.key
    if args.press_enter is not None:
        config.press_enter = args.press_enter
    if args.model:
        config.model = args.model
    if args.language:
        config.language = args.language
    if args.verbose:
        config.log_level = logging.DEBUG
    if args.log_transcripts:
        config.log_transcripts = True

    # Set up logging
    configure_logging(config)
    logger = logging.getLogger("main")

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY is not set. Set it in your environment or .env file.")
        return 1

    # Show platform info
    logger.info("Platform: %s", sys.platform)
    logger.info("PTT key: %s", config.ptt_key)
    if config.press_enter:
        logger.info("Will press Enter after typing")

    # Create OpenAI client and run daemon
    client = OpenAI(api_key=api_key)
    daemon = PushToTalkDaemon(client=client, config=config)

    try:
        daemon.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        daemon.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
