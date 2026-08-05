#!/usr/bin/env python3
"""Prepare storyboard crops and the output directory for the video run."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


OUTPUT_SUBDIRS = (
    "00_reference",
    "01_storyboard_crops",
    "02_product_assets",
    "03_prompts",
    "04_tasks",
    "05_raw_clips",
    "06_qc",
    "07_edit",
    "final",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    return parser.parse_args()


def run_ffmpeg(source: Path, crop: dict[str, int], destination: Path) -> None:
    crop_filter = (
        f"crop={crop['width']}:{crop['height']}:{crop['x']}:{crop['y']},"
        "scale=-2:420:flags=lanczos"
    )
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        crop_filter,
        "-frames:v",
        "1",
        str(destination),
    ]
    subprocess.run(command, check=True)


def make_product_reference(source: Path, destination: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        "crop=1050:420:(iw-1050)/2:0,scale=1050:420:flags=lanczos",
        "-frames:v",
        "1",
        str(destination),
    ]
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    output_dir = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = Path(manifest["storyboard_source"]).expanduser().resolve()

    if not source.is_file():
        raise SystemExit(f"Storyboard not found: {source}")
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required")

    for name in OUTPUT_SUBDIRS:
        (output_dir / name).mkdir(parents=True, exist_ok=True)

    reference_copy = output_dir / "00_reference" / source.name
    if not reference_copy.exists():
        shutil.copy2(source, reference_copy)

    crops = manifest["storyboard_crops"]
    for shot_number, crop in sorted(crops.items(), key=lambda item: int(item[0])):
        destination = output_dir / "01_storyboard_crops" / f"shot_{int(shot_number):02d}.png"
        run_ffmpeg(source, crop, destination)
        print(f"[OK] shot {shot_number}: {destination}")

    for shot_number in (3, 7):
        source_crop = output_dir / "01_storyboard_crops" / f"shot_{shot_number:02d}.png"
        destination = output_dir / "02_product_assets" / f"reference_shot_{shot_number:02d}.png"
        make_product_reference(source_crop, destination)
        print(f"[OK] product reference {shot_number}: {destination}")

    print(f"[OK] Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
