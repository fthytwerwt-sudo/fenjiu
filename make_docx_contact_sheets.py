from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path("qa/docx")
OUT = ROOT / "_contact_sheets"
OUT.mkdir(exist_ok=True)


def page_number(path: Path) -> int:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return int(digits or 0)


for folder in sorted(p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith("_")):
    pages = sorted(
        (p for p in folder.glob("page-*.png") if not p.name.startswith("._")),
        key=page_number,
    )
    if not pages:
        continue
    for start in range(0, len(pages), 4):
        batch = pages[start : start + 4]
        thumbs = []
        for page in batch:
            image = Image.open(page).convert("RGB")
            width = 440
            height = int(image.height * width / image.width)
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            thumbs.append((page.name, image.copy()))
        canvas_width = 920
        canvas_height = 50 + max(img.height for _, img in thumbs)
        canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 12), f"{folder.name} | pages {start + 1}-{start + len(batch)}", fill="black")
        for index, (name, image) in enumerate(thumbs):
            x = 10 + (index % 2) * 455
            y = 40 + (index // 2) * (image.height + 25)
            if y + image.height > canvas.height:
                new_height = y + image.height + 10
                expanded = Image.new("RGB", (canvas.width, new_height), "white")
                expanded.paste(canvas, (0, 0))
                canvas = expanded
                draw = ImageDraw.Draw(canvas)
            canvas.paste(image, (x, y))
            draw.text((x, y), name, fill="#C00000")
        canvas.save(OUT / f"{folder.name}_{start + 1:02d}-{start + len(batch):02d}.jpg", quality=90)
