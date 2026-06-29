#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crop a rectangular region out of a rendered slide image.

Why this exists: lecture notes need to embed the original figures from the
PPT (e.g. the 3D scattering-function plot FIG 13.1-6). Those figures live
inside a rendered page image (pages/0007.png). Rather than re-drawing them
(which risks distorting the original meaning) or embedding the whole page
(which wastes space and carries unrelated text), we crop just the figure's
bounding box out of the page image and save it as a standalone PNG that the
LaTeX notes can \includegraphics.

The model using the skill looks at the page image, decides the pixel
coordinates of the figure bounding box, and calls this script with them.
In the LaTeX notes the cropped PNG is embedded via includegraphics.

Usage:
    python crop_figure.py <page_image.png> --bbox X1,Y1,X2,Y2 --out fig.png
    python crop_figure.py <page_image.png> --bbox X1,Y1,X2,Y2 --out fig.png --pad 15

Coordinates are in pixels, measured from the top-left of the page image.
(X1,Y1) = top-left of the figure, (X2,Y2) = bottom-right.
"""
import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def parse_bbox(s):
    parts = [int(x.strip()) for x in s.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be X1,Y1,X2,Y2")
    x1, y1, x2, y2 = parts
    if x2 <= x1 or y2 <= y1:
        raise ValueError("need X2>X1 and Y2>Y1, got %s" % s)
    return x1, y1, x2, y2


def main():
    ap = argparse.ArgumentParser(description="Crop a figure region out of a slide image")
    ap.add_argument("page", help="source page image (e.g. pages/0007.png)")
    ap.add_argument("--bbox", required=True, help="X1,Y1,X2,Y2 in pixels")
    ap.add_argument("--out", required=True, help="output PNG path")
    ap.add_argument("--pad", type=int, default=10, help="extra margin in px (default 10)")
    args = ap.parse_args()

    from PIL import Image

    src = Path(args.page)
    if not src.exists():
        print("[ERROR] source image not found: %s" % src, file=sys.stderr)
        sys.exit(1)

    x1, y1, x2, y2 = parse_bbox(args.bbox)
    img = Image.open(src)
    W, H = img.size
    # apply padding, clamp to image bounds
    x1 = max(0, x1 - args.pad)
    y1 = max(0, y1 - args.pad)
    x2 = min(W, x2 + args.pad)
    y2 = min(H, y2 + args.pad)

    crop = img.crop((x1, y1, x2, y2))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    crop.save(str(out))

    print('{"ok": true, "out": "%s", "size": [%d, %d]}' % (out, crop.size[0], crop.size[1]))


if __name__ == "__main__":
    main()
