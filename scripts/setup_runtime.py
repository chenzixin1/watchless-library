#!/usr/bin/env python3
"""Create an isolated runtime for bundled Watchless and video-use dependencies."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHLESS = ROOT / "dependencies" / "watchless"
VIDEO_USE = ROOT / "dependencies" / "video-use"
RUNTIME = ROOT / ".runtime" / "venv"


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up the isolated Python runtime")
    parser.add_argument("--python", default=sys.executable, help="Python 3.10+ executable")
    parser.add_argument("--rebuild", action="store_true", help="Recreate the runtime from scratch")
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is required")
    if not WATCHLESS.exists() or not VIDEO_USE.exists():
        raise SystemExit("Bundled dependencies are missing")

    if args.rebuild and RUNTIME.exists():
        shutil.rmtree(RUNTIME)
    if not (RUNTIME / "bin" / "python").exists():
        RUNTIME.parent.mkdir(parents=True, exist_ok=True)
        run([args.python, "-m", "venv", str(RUNTIME)])

    python = str(RUNTIME / "bin" / "python")
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    run([
        python,
        "-m",
        "pip",
        "install",
        "-r",
        str(WATCHLESS / "scripts" / "requirements.txt"),
        "yt-dlp",
        "curl-cffi",
    ])
    run([python, "-m", "pip", "install", "-e", str(VIDEO_USE)])

    print(f"Runtime ready: {RUNTIME}")
    print("System commands still required: ffmpeg, ffprobe, and a Chromium-based browser")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
