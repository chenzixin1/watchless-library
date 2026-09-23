#!/usr/bin/env python3
"""Check the packaged Skill, runtime, site, and required system tools."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def status(ok: bool, label: str, detail: str = "") -> bool:
    mark = "OK" if ok else "MISSING"
    print(f"[{mark:7}] {label}" + (f": {detail}" if detail else ""))
    return ok


def main() -> int:
    checks: list[bool] = []
    for command in ("ffmpeg", "ffprobe"):
        path = shutil.which(command)
        checks.append(status(bool(path), command, path or "not found"))

    runtime_python = ROOT / ".runtime" / "venv" / "bin" / "python"
    checks.append(status(runtime_python.exists(), "isolated runtime", str(runtime_python)))
    checks.append(status((ROOT / "dependencies" / "watchless" / "SKILL.md").exists(), "bundled watchless"))
    checks.append(status((ROOT / "dependencies" / "video-use" / "SKILL.md").exists(), "bundled video-use"))

    site = ROOT / "site"
    checks.append(status((site / "index.html").exists(), "site index"))
    checks.append(status((site / "assets" / "site.js").exists(), "site runtime"))

    catalog = site / "data" / "catalog.js"
    checks.append(status(catalog.exists(), "site catalog"))
    if catalog.exists():
        text = catalog.read_text(encoding="utf-8")
        checks.append(status("window.__CATALOG__" in text, "catalog format"))

    video = site / "media" / "tom-lee-sp8000" / "video.mp4"
    if video.exists():
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,pix_fmt", "-of", "json", str(video)],
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            stream = json.loads(result.stdout)["streams"][0]
            compatible = stream.get("codec_name") == "h264" and stream.get("pix_fmt") == "yuv420p"
            checks.append(status(compatible, "demo video", f"{stream.get('codec_name')} / {stream.get('pix_fmt')}"))
        except Exception:
            checks.append(status(False, "demo video", "ffprobe failed"))

    print(f"\nResult: {sum(checks)}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
