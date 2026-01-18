"""Linux-specific implementation using evdev and xdotool."""

from __future__ import annotations

import logging
import select
import subprocess
from typing import Dict, Iterable, Optional

import evdev
from evdev import InputDevice, ecodes

from . import KeyCallback, PlatformHandler


class LinuxHandler(PlatformHandler):
    """Linux platform handler using evdev for input and xdotool for typing."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._devices: list[InputDevice] = []
        self._fd_to_device: Dict[int, InputDevice] = {}
        self._key_code: Optional[int] = None
        self._callback: Optional[KeyCallback] = None
        self._running = False

    def _resolve_keycode(self, key_name: str) -> int:
        """Convert a key name to its evdev keycode."""
        try:
            return evdev.ecodes.ecodes[key_name]
        except KeyError as exc:
            raise ValueError(f"Unknown key name: {key_name}") from exc

    def _discover_devices(self) -> list[InputDevice]:
        """Find all input devices that support the configured key."""
        devices = []
        for path in evdev.list_devices():
            try:
                device = InputDevice(path)
            except OSError as exc:
                self._logger.warning("Skipping input device %s: %s", path, exc)
                continue

            caps = device.capabilities().get(ecodes.EV_KEY, [])
            key_codes: Iterable[int]
            if isinstance(caps, dict):
                key_codes = (code for codes in caps.values() for code in codes)
            else:
                key_codes = caps

            if self._key_code in set(key_codes):
                devices.append(device)
                continue

            if ecodes.EV_KEY in device.capabilities():
                devices.append(device)

        return devices

    def start_listening(self, key_name: str, callback: KeyCallback) -> None:
        """Start listening for key events on Linux input devices."""
        self._key_code = self._resolve_keycode(key_name)
        self._callback = callback
        self._devices = self._discover_devices()
        self._fd_to_device = {dev.fd: dev for dev in self._devices}

        if not self._devices:
            self._logger.error(
                "No input devices found. Ensure you have permission to read /dev/input/event*."
            )
            return

        for device in self._devices:
            self._logger.info("Listening on %s (%s)", device.path, device.name)

        self._running = True
        self._event_loop()

    def _event_loop(self) -> None:
        """Main event loop for processing input events."""
        try:
            while self._running:
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
        """Process a single input event."""
        if event.type != ecodes.EV_KEY:
            return
        if event.code != self._key_code:
            return
        if self._callback is None:
            return

        if event.value == 1:  # key down
            self._callback(True)
        elif event.value == 0:  # key up
            self._callback(False)

    def stop_listening(self) -> None:
        """Stop the event loop."""
        self._running = False

    def _cleanup(self) -> None:
        """Close all input devices."""
        for device in self._devices:
            try:
                device.close()
            except Exception:
                pass
        self._devices = []
        self._fd_to_device = {}

    def type_text(self, text: str, press_enter: bool = False) -> None:
        """Type text using xdotool."""
        cmd = ["xdotool", "type", "--delay", "0", "--clearmodifiers", text]
        try:
            subprocess.run(cmd, check=True)
            self._logger.info("Typed transcription into focused window.")
            if press_enter:
                subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], check=True)
                self._logger.info("Sent Enter key as configured.")
        except FileNotFoundError:
            self._logger.error("xdotool not found. Install it with: sudo apt install xdotool")
        except subprocess.CalledProcessError as exc:
            self._logger.error("Failed to send text via xdotool: %s", exc)

    def release_key(self, key_name: str) -> None:
        """Release a key using xdotool (useful for modifier keys)."""
        # Convert evdev key name to xdotool keysym if needed
        keysym = key_name.replace("KEY_", "").lower()
        try:
            subprocess.run(
                ["xdotool", "keyup", "--clearmodifiers", keysym],
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            self._logger.warning("Failed to send keyup for %s: %s", keysym, exc)
