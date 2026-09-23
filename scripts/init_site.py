#!/usr/bin/env python3
"""Initialize a learning-site instance from the bundled fixed template."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "site-template"
INGEST = ROOT / "scripts" / "ingest.py"
USAGE = ROOT / "references" / "site-usage.md"


def copy_file(source: Path, target: Path, overwrite: bool) -> None:
    if target.exists() and not overwrite:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize the fixed learning-site template")
    parser.add_argument("site", nargs="?", default=str(ROOT / "site"), help="Target site directory")
    parser.add_argument("--refresh-template", action="store_true", help="Refresh fixed HTML/CSS/JS files")
    args = parser.parse_args()

    site = Path(args.site).expanduser().resolve()
    if not TEMPLATE.exists():
        raise SystemExit(f"Template is missing: {TEMPLATE}")

    for source in TEMPLATE.rglob("*"):
        if source.is_file():
            copy_file(source, site / source.relative_to(TEMPLATE), args.refresh_template)

    (site / "data").mkdir(parents=True, exist_ok=True)
    (site / "media").mkdir(parents=True, exist_ok=True)
    (site / "tools").mkdir(parents=True, exist_ok=True)
    copy_file(INGEST, site / "tools" / "ingest.py", True)
    copy_file(USAGE, site / "README.md", False)

    print(f"Learning site ready: {site}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
