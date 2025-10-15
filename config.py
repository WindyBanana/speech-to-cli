import logging

PTT_KEY = "KEY_RIGHTALT"
PRESS_ENTER = True
MODEL = "gpt-4o-transcribe"
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
MAX_RECORD_SECONDS = 10

# Logging behaviour
LOG_LEVEL = logging.INFO  # set to logging.WARNING to quiet most logs
LOG_FORMAT = "%(message)s"  # omit timestamps to keep console clean
LOG_TRANSCRIPTS = False  # set True to log the recognized text
