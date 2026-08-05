from __future__ import annotations

import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path("/Volumes/WD_BLACK/汾酒尼泊尔")
INPUT = ROOT / "汾酒海鲜_尼泊尔线上销售_供应链协同与资料交付体系"
OUTPUT = ROOT / "_qa_supply_collab_render_final"
PYTHON = Path("/Users/fan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")
RENDERER = Path(
    "/Users/fan/.codex/plugins/cache/openai-primary-runtime/documents/"
    "26.715.12143/skills/documents/render_docx.py"
)


def render(path: Path) -> tuple[str, int, str]:
    relative = path.relative_to(INPUT)
    folder_name = "__".join(relative.with_suffix("").parts)
    target = OUTPUT / folder_name
    target.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["FONTCONFIG_FILE"] = str(ROOT / "_qa_fontconfig" / "fonts.conf")
    environment["TMPDIR"] = "/private/tmp"
    result = subprocess.run(
        [
            str(PYTHON),
            str(RENDERER),
            str(path),
            "--output_dir",
            str(target),
            "--width",
            "1600",
            "--height",
            "2000",
        ],
        capture_output=True,
        text=True,
        env=environment,
        timeout=240,
    )
    message = (result.stdout + "\n" + result.stderr).strip()
    pages = len(list(target.glob("page-*.png")))
    return str(relative), pages, message if result.returncode else ""


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    files = sorted(INPUT.rglob("*.docx"))
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(render, path): path for path in files}
        for future in as_completed(futures):
            relative, pages, error = future.result()
            results.append((relative, pages, error))
            print(f"{relative}\t{pages}\t{'FAILED' if error else 'OK'}", flush=True)
    failures = [item for item in results if item[2] or item[1] == 0]
    print(f"documents={len(results)} pages={sum(item[1] for item in results)} failures={len(failures)}")
    if failures:
        for relative, pages, error in failures:
            print(f"\n{relative}\npages={pages}\n{error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
