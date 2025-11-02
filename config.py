import logging

from features import Features

PTT_KEY = "KEY_RIGHTSHIFT"
PTT_KEYSYM = "Shift_R"  # xdotool keysym for the push-to-talk key (set None if unused)
PRESS_ENTER = True
MODEL = "gpt-4o-transcribe"
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
MAX_RECORD_SECONDS = 60

# Logging behaviour
LOG_LEVEL = logging.INFO  # set to logging.WARNING to quiet most logs
LOG_FORMAT = "%(message)s"  # omit timestamps to keep console clean
LOG_TRANSCRIPTS = False  # set True to log the recognized text
FEATURE_FLAGS = {
    Features.DASHBOARD: False,
}
LOG_FORMAT = "%(message)s"  # omit timestamps to keep console clean
LOG_TRANSCRIPTS = False  # set True to log the recognized text
