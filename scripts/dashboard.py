#!/usr/bin/env python3
"""GUI dashboard for speech-to-cli.

Provides Start/Stop controls for main.py and basic management of the
OPENAI_API_KEY stored in the project's .env file.
"""

from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext
from typing import Optional

import evdev

from openai import OpenAI

import config
from main import PushToTalkDaemon


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
SCRIPT_ENTRYPOINT = PROJECT_ROOT / "main.py"
ENV_PATH = PROJECT_ROOT / ".env"


class DashboardApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.daemon: Optional[PushToTalkDaemon] = None
        self.daemon_thread: Optional[threading.Thread] = None
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.status_var = tk.StringVar(value="Status: stopped")
        self.api_key_var = tk.StringVar(value=self._load_api_key())
        self.api_message_var = tk.StringVar(
            value="API key loaded" if self.api_key_var.get() else "No API key saved"
        )

        root.title("Speech-to-CLI")
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.resizable(False, False)

        api_frame = tk.LabelFrame(root, text="OpenAI API Key")
        api_frame.pack(fill="x", padx=12, pady=(12, 6))

        self.api_entry = tk.Entry(
            api_frame, textvariable=self.api_key_var, show="*", width=40
        )
        self.api_entry.pack(fill="x", padx=8, pady=(8, 4))

        api_controls = tk.Frame(api_frame)
        api_controls.pack(fill="x", padx=8, pady=(0, 4))

        self.show_api_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            api_controls,
            text="Show key",
            variable=self.show_api_var,
            command=self.toggle_api_visibility,
        ).pack(side="left")

        tk.Button(api_controls, text="Save key", command=self.save_api_key).pack(
            side="right"
        )

        tk.Label(api_frame, textvariable=self.api_message_var, anchor="w").pack(
            fill="x", padx=8, pady=(0, 6)
        )

        tk.Label(root, textvariable=self.status_var, anchor="w").pack(
            fill="x", padx=12, pady=(6, 6)
        )

        log_frame = tk.LabelFrame(root, text="Logs")
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.log_text.configure(state="disabled")

        buttons_frame = tk.Frame(root)
        buttons_frame.pack(fill="x", padx=12, pady=(0, 12))

        self.start_button = tk.Button(buttons_frame, text="Start Recording", command=self.start_recording)
        self.start_button.pack(fill="x")

        self.stop_button = tk.Button(buttons_frame, text="Stop Recording", command=self.stop_recording)
        self.stop_button.pack(fill="x", pady=(6, 0))
        self.stop_button.configure(state="disabled")

        self.root.after(100, self._drain_log_queue)

    def start_recording(self) -> None:
        if not self.daemon:
            key = self.api_key_var.get().strip()
            if not key:
                self.status_var.set("Status: add an API key before starting")
                return
            try:
                self._write_api_key(key)
            except OSError as exc:
                self.status_var.set(f"Status: could not save key ({exc})")
                return

            self._clear_log()
            self._redirect_stdout()

            client = OpenAI(api_key=key)
            self.daemon = PushToTalkDaemon(
                client=client,
                ptt_key_name=config.PTT_KEY,
                press_enter=config.PRESS_ENTER,
                model=config.MODEL,
                sample_rate=config.AUDIO_SAMPLE_RATE,
                channels=config.AUDIO_CHANNELS,
                max_seconds=config.MAX_RECORD_SECONDS,
            )

        self.daemon.start_recording()
        self.status_var.set("Status: recording")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def stop_recording(self) -> None:
        if self.daemon:
            self.daemon.stop_recording()
        self.status_var.set("Status: stopped")
        self._reset_buttons()

    def on_close(self) -> None:
        if self.daemon:
            self.daemon.stop_listening()
            if self.daemon_thread:
                self.daemon_thread.join(timeout=1)
        self.root.destroy()

    def save_api_key(self) -> None:
        key = self.api_key_var.get().strip()
        if not key:
            self.api_message_var.set("Enter an API key before saving")
            return
        try:
            self._write_api_key(key)
        except OSError as exc:
            self.api_message_var.set(f"Could not save key ({exc})")
            return
        self.api_message_var.set("API key saved")

    def toggle_api_visibility(self) -> None:
        self.api_entry.configure(show="" if self.show_api_var.get() else "*")

    def _redirect_stdout(self) -> None:
        sys.stdout = self

    def _restore_stdout(self) -> None:
        sys.stdout = sys.__stdout__

    def write(self, text: str) -> None:
        self.log_queue.put(text)

    def flush(self) -> None:
        pass

    def _drain_log_queue(self) -> None:
        updated = False
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self._append_log(line)
                updated = True
        if updated:
            self.log_text.see("end")
        self.root.after(100, self._drain_log_queue)

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _append_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.configure(state="disabled")

    def _reset_buttons(self) -> None:
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.api_message_var.set(
            "API key saved" if self.api_key_var.get().strip() else "No API key saved"
        )

    def _load_api_key(self) -> str:
        if not ENV_PATH.exists():
            return ""

        try:
            for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("OPENAI_API_KEY="):
                    value = line.split("=", 1)[1].strip()
                    if value.startswith(''') and value.endswith('''):
                        value = value[1:-1]
                    return value
        except OSError:
            return ""
        return ""

    def _write_api_key(self, key: str) -> None:
        lines = []
        found = False

        if ENV_PATH.exists():
            existing = ENV_PATH.read_text(encoding="utf-8").splitlines()
        else:
            existing = []

        for line in existing:
            if line.startswith("OPENAI_API_KEY="):
                lines.append(f"OPENAI_API_KEY={key}")
                found = True
            else:
                lines.append(line)

        if not found:
            lines.append(f"OPENAI_API_KEY={key}")

        text = "\n".join(lines)
        if text and not text.endswith("\n"):
            text += "\n"

        ENV_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    root = tk.Tk()
    DashboardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
