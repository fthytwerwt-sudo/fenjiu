#!/usr/bin/env python3
"""Ensure generated XLSX worksheets persist a frozen header pane."""

from __future__ import annotations

import os
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("", NS)


def patch_sheet(data: bytes, rows: int) -> bytes:
    root = ET.fromstring(data)
    sheet_views = root.find(f"{{{NS}}}sheetViews")
    if sheet_views is None:
        sheet_views = ET.Element(f"{{{NS}}}sheetViews")
        root.insert(0, sheet_views)
    sheet_view = sheet_views.find(f"{{{NS}}}sheetView")
    if sheet_view is None:
        sheet_view = ET.SubElement(sheet_views, f"{{{NS}}}sheetView", {"workbookViewId": "0"})
    for pane in list(sheet_view.findall(f"{{{NS}}}pane")):
        sheet_view.remove(pane)
    pane = ET.Element(
        f"{{{NS}}}pane",
        {"ySplit": str(rows), "topLeftCell": f"A{rows + 1}", "activePane": "bottomLeft", "state": "frozen"},
    )
    sheet_view.insert(0, pane)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main() -> None:
    path = Path(sys.argv[1])
    rows = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    fd, temp_name = tempfile.mkstemp(prefix=path.stem + "-", suffix=".xlsx", dir=path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(path, "r") as src, zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as dst:
            for info in src.infolist():
                data = src.read(info.filename)
                if info.filename.startswith("xl/worksheets/sheet") and info.filename.endswith(".xml"):
                    data = patch_sheet(data, rows)
                dst.writestr(info, data)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
