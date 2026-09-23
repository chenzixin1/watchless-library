#!/usr/bin/env python3
"""Run the bundled Watchless pipeline with the bundled video-use integration."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime" / "venv"
RUNNER = ROOT / "dependencies" / "watchless" / "scripts" / "00_build_video_notes.py"
VIDEO_USE = ROOT / "dependencies" / "video-use"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pass arguments to the bundled Watchless runner",
        add_help=False,
    )
    parser.add_argument("--cwd", default=str(ROOT), help="Working directory for Watchless outputs")
    parser.add_argument("-h", "--help", action="store_true")
    known, forwarded = parser.parse_known_args()

    python = RUNTIME / "bin" / "python"
    if not python.exists():
        raise SystemExit("Runtime is missing. Run: python3 scripts/setup_runtime.py")
    if not RUNNER.exists():
        raise SystemExit(f"Watchless runner is missing: {RUNNER}")

    env = os.environ.copy()
    env["VIDEO_USE_SKILL_DIR"] = str(VIDEO_USE)
    env["PATH"] = f"{RUNTIME / 'bin'}:{env.get('PATH', '')}"

    if known.help and not forwarded:
        forwarded = ["--help"]
    elif known.help:
        forwarded.append("--help")

    command = [str(python), str(RUNNER), *forwarded]
    print("+", " ".join(command))
    return subprocess.run(command, cwd=Path(known.cwd).expanduser().resolve(), env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
