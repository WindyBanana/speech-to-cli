#!/usr/bin/env python3
"""Build script for creating Windows executable using PyInstaller."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "speech-to-cli",
        "--add-data",
        f"{src_dir / 'speech_to_cli'};speech_to_cli",
        "--hidden-import",
        "pynput.keyboard._win32",
        "--hidden-import",
        "pynput.mouse._win32",
        str(src_dir / "speech_to_cli" / "cli.py"),
    ]

    print("Building Windows executable...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        print("\nBuild successful!")
        print(f"Executable: {project_root / 'dist' / 'speech-to-cli.exe'}")
    else:
        print("\nBuild failed!")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
