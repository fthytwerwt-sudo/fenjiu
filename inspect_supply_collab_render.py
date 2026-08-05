from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path("/Volumes/WD_BLACK/汾酒尼泊尔")
RENDER = ROOT / "_qa_supply_collab_render_final"
CONTACT = ROOT / "_qa_supply_collab_contact_final"
REPORT = ROOT / "_qa_supply_collab_visual.json"


def natural_page(path: Path) -> int:
    return int(path.stem.split("-")[-1])


def content_bbox(image: Image.Image):
    white = Image.new("RGB", image.size, "white")
    return ImageChops.difference(image.convert("RGB"), white).getbbox()


def main() -> None:
    if CONTACT.exists():
        shutil.rmtree(CONTACT)
    CONTACT.mkdir(parents=True)
    failures: list[str] = []
    documents: list[dict] = []
    total_pages = 0
    for folder in sorted(path for path in RENDER.iterdir() if path.is_dir()):
        pages = sorted(folder.glob("page-*.png"), key=natural_page)
        if not pages:
            failures.append(f"{folder.name} 没有页面")
            continue
        total_pages += len(pages)
        page_summaries = []
        rendered_pages = []
        for page in pages:
            image = Image.open(page).convert("RGB")
            bbox = content_bbox(image)
            if bbox is None:
                failures.append(f"{folder.name}/{page.name} 为空白页")
                bbox = (0, 0, 0, 0)
            else:
                left, top, right, bottom = bbox
                if left <= 2 or right >= image.width - 2:
                    failures.append(f"{folder.name}/{page.name} 内容接近左右裁切边缘：{bbox}")
                if top <= 2 or bottom >= image.height - 2:
                    failures.append(f"{folder.name}/{page.name} 内容接近上下裁切边缘：{bbox}")
            page_summaries.append({"page": page.name, "size": image.size, "content_bbox": bbox})
            rendered_pages.append(image)

        thumb_width = 360
        label_height = 28
        margin = 18
        columns = 4
        first_ratio = rendered_pages[0].height / rendered_pages[0].width
        thumb_height = round(thumb_width * first_ratio)
        rows = math.ceil(len(rendered_pages) / columns)
        canvas = Image.new(
            "RGB",
            (
                margin + columns * (thumb_width + margin),
                margin + rows * (thumb_height + label_height + margin),
            ),
            "#D9E2EC",
        )
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()
        for index, image in enumerate(rendered_pages):
            col = index % columns
            row = index // columns
            x = margin + col * (thumb_width + margin)
            y = margin + row * (thumb_height + label_height + margin)
            thumb = image.copy()
            thumb.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            slot = Image.new("RGB", (thumb_width, thumb_height), "white")
            slot.paste(thumb, ((thumb_width - thumb.width) // 2, (thumb_height - thumb.height) // 2))
            canvas.paste(slot, (x, y))
            draw.text((x, y + thumb_height + 6), f"{folder.name}  p.{index + 1}", fill="#102A43", font=font)
        contact_path = CONTACT / f"{folder.name}.png"
        canvas.save(contact_path, quality=95)
        documents.append(
            {
                "document": folder.name,
                "pages": len(pages),
                "contact_sheet": str(contact_path),
                "page_checks": page_summaries,
            }
        )
    for apple_double in CONTACT.glob("._*"):
        if apple_double.is_file():
            apple_double.unlink()
    report = {
        "status": "passed" if not failures else "failed",
        "document_count": len(documents),
        "page_count": total_pages,
        "failures": failures,
        "documents": documents,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "documents"}, ensure_ascii=False, indent=2))
    print(f"contact_sheets={len([path for path in CONTACT.glob('*.png') if not path.name.startswith('._')])}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
