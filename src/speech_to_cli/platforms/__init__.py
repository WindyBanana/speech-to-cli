"""Platform-specific implementations for input handling and text typing."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import Callable, Optional

# Type alias for the callback function
KeyCallback = Callable[[bool], None]  # bool = is_pressed (True=down, False=up)


class PlatformHandler(ABC):
    """Abstract base class for platform-specific input/output handling."""

    @abstractmethod
    def start_listening(self, key_name: str, callback: KeyCallback) -> None:
        """Start listening for the specified key press/release events.

        Args:
            key_name: Platform-specific key identifier
            callback: Function called with True on key down, False on key up
        """
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """Stop listening for key events and clean up resources."""
        pass

    @abstractmethod
    def type_text(self, text: str, press_enter: bool = False) -> None:
        """Type the given text into the currently focused window.

        Args:
            text: The text to type
            press_enter: Whether to press Enter after typing
        """
        pass

    @abstractmethod
    def release_key(self, key_name: str) -> None:
        """Release a key that may be stuck (useful for modifier keys).

        Args:
            key_name: Platform-specific key identifier
        """
        pass


def get_platform_handler() -> PlatformHandler:
    """Factory function to get the appropriate platform handler.

    Returns:
        PlatformHandler instance for the current platform

    Raises:
        NotImplementedError: If the current platform is not supported
    """
    if sys.platform == "linux":
        from .linux import LinuxHandler
        return LinuxHandler()
    elif sys.platform == "darwin":
        from .macos import MacOSHandler
        return MacOSHandler()
    elif sys.platform == "win32":
        from .windows import WindowsHandler
        return WindowsHandler()
    else:
        raise NotImplementedError(f"Platform '{sys.platform}' is not supported")


def get_default_ptt_key() -> str:
    """Get the default push-to-talk key name for the current platform."""
    if sys.platform == "linux":
        return "KEY_PAUSE"
    elif sys.platform == "darwin":
        return "f13"  # F13 key, common on extended keyboards
    elif sys.platform == "win32":
        return "pause"
    else:
        return "pause"
