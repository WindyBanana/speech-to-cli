"""macOS-specific implementation using pynput."""

from __future__ import annotations

import logging
import threading
from typing import Optional

from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode

from . import KeyCallback, PlatformHandler


# Mapping of common key names to pynput Key objects
KEY_MAP = {
    # Function keys
    "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
    "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
    "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    "f13": Key.f13, "f14": Key.f14, "f15": Key.f15, "f16": Key.f16,
    "f17": Key.f17, "f18": Key.f18, "f19": Key.f19, "f20": Key.f20,
    # Special keys
    "pause": Key.pause,
    "scroll_lock": Key.scroll_lock,
    "print_screen": Key.print_screen,
    "insert": Key.insert,
    "delete": Key.delete,
    "home": Key.home,
    "end": Key.end,
    "page_up": Key.page_up,
    "page_down": Key.page_down,
    # Modifiers (less common for PTT but supported)
    "ctrl": Key.ctrl,
    "ctrl_l": Key.ctrl_l,
    "ctrl_r": Key.ctrl_r,
    "alt": Key.alt,
    "alt_l": Key.alt_l,
    "alt_r": Key.alt_r,
    "shift": Key.shift,
    "shift_l": Key.shift_l,
    "shift_r": Key.shift_r,
    "cmd": Key.cmd,
    "cmd_l": Key.cmd_l,
    "cmd_r": Key.cmd_r,
}


class MacOSHandler(PlatformHandler):
    """macOS platform handler using pynput for input and typing."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._listener: Optional[keyboard.Listener] = None
        self._controller = Controller()
        self._target_key: Optional[Key | KeyCode] = None
        self._callback: Optional[KeyCallback] = None
        self._key_name: str = ""

    def _resolve_key(self, key_name: str) -> Key | KeyCode:
        """Convert a key name to a pynput Key or KeyCode."""
        key_lower = key_name.lower()

        # Check our mapping first
        if key_lower in KEY_MAP:
            return KEY_MAP[key_lower]

        # Single character = regular key
        if len(key_name) == 1:
            return KeyCode.from_char(key_name)

        # Try to get from Key enum directly
        try:
            return getattr(Key, key_lower)
        except AttributeError:
            pass

        raise ValueError(
            f"Unknown key name: {key_name}. "
            f"Available keys: {', '.join(sorted(KEY_MAP.keys()))}"
        )

    def _matches_key(self, pressed_key: Key | KeyCode | None) -> bool:
        """Check if the pressed key matches our target key."""
        if pressed_key is None or self._target_key is None:
            return False

        # Direct comparison
        if pressed_key == self._target_key:
            return True

        # Handle KeyCode comparison (for character keys)
        if isinstance(pressed_key, KeyCode) and isinstance(self._target_key, KeyCode):
            return pressed_key.char == self._target_key.char

        return False

    def _on_press(self, key: Key | KeyCode | None) -> None:
        """Handle key press events."""
        if self._matches_key(key) and self._callback:
            self._callback(True)

    def _on_release(self, key: Key | KeyCode | None) -> None:
        """Handle key release events."""
        if self._matches_key(key) and self._callback:
            self._callback(False)

    def start_listening(self, key_name: str, callback: KeyCallback) -> None:
        """Start listening for key events using pynput.

        Note: On macOS, you must grant Accessibility permissions to the
        terminal/app running this script in System Preferences >
        Privacy & Security > Accessibility.
        """
        self._key_name = key_name
        self._target_key = self._resolve_key(key_name)
        self._callback = callback

        self._logger.info(
            "Listening for key '%s' (grant Accessibility permissions if not working)",
            key_name,
        )

        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

        # Block until stopped (similar to Linux behavior)
        try:
            self._listener.join()
        except KeyboardInterrupt:
            self._logger.info("Interrupted by user, exiting.")
        finally:
            self.stop_listening()

    def stop_listening(self) -> None:
        """Stop the keyboard listener."""
        if self._listener:
            self._listener.stop()
            self._listener = None

    def type_text(self, text: str, press_enter: bool = False) -> None:
        """Type text using pynput keyboard controller."""
        try:
            self._controller.type(text)
            self._logger.info("Typed transcription into focused window.")

            if press_enter:
                self._controller.press(Key.enter)
                self._controller.release(Key.enter)
                self._logger.info("Sent Enter key as configured.")
        except Exception as exc:
            self._logger.error("Failed to type text: %s", exc)

    def release_key(self, key_name: str) -> None:
        """Release a potentially stuck key."""
        try:
            key = self._resolve_key(key_name)
            self._controller.release(key)
        except Exception as exc:
            self._logger.warning("Failed to release key %s: %s", key_name, exc)
