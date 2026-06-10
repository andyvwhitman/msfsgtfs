#!/usr/bin/env python3
"""Build the GTFS feed ZIP from the hand-maintained source files.

The Maine State Ferry Service feed is authored by hand rather than delivered as a
ZIP by a provider. The raw GTFS text files live in ``msfs_gtfs_package/``; this
script zips them into ``backend/Archive.zip`` (a generated artifact, not committed),
which the Flask backend loads via ``gtfs_kit``.

Dev loop: edit files in ``msfs_gtfs_package/`` -> run ``python build_feed.py`` ->
restart Flask.
"""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "msfs_gtfs_package"
OUTPUT = ROOT / "backend" / "Archive.zip"


def build_feed():
    txt_files = sorted(SOURCE_DIR.glob("*.txt"))
    if not txt_files:
        raise SystemExit(f"No .txt files found in {SOURCE_DIR}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in txt_files:
            # arcname must be the bare filename so GTFS files sit at the archive
            # root, which gtfs_kit.read_feed requires.
            zf.write(f, arcname=f.name)

    print(f"Built {OUTPUT} from {len(txt_files)} files:")
    for f in txt_files:
        print(f"  - {f.name}")


if __name__ == "__main__":
    build_feed()
