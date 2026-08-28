"""Turn a raster image into a clean dot-matrix SVG using Pillow."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageOps


def build_svg(image: Image.Image, columns: int, detail: float, color: bool, circular: bool, dot_size: float) -> str:
    source = ImageOps.exif_transpose(image).convert("RGB")
    aspect = source.height / source.width
    rows = max(1, round(columns * aspect * 0.52))
    source = source.resize((columns, rows), Image.Resampling.LANCZOS)
    gray = ImageOps.equalize(ImageOps.grayscale(source))
    width = columns * dot_size
    height = rows * dot_size
    dots = []
    for y in range(rows):
        for x in range(columns):
            luminance = gray.getpixel((x, y))
            intensity = max(0.0, min(1.0, (255 - luminance) / 255 * detail))
            if intensity < 0.06:
                continue
            radius = max(0.35, dot_size * 0.46 * intensity)
            fill = "#39D353" if color else "#24292f"
            if color:
                red, green, blue = source.getpixel((x, y))
                fill = f"#{red:02x}{green:02x}{blue:02x}"
            cx, cy = (x + 0.5) * dot_size, (y + 0.5) * dot_size
            if circular:
                distance = math.hypot(cx - width / 2, cy - height / 2)
                if distance > min(width, height) / 2:
                    continue
            dots.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="{fill}"/>')
    clip = f' clip-path="url(#circle)"' if circular else ""
    defs = f'<defs><clipPath id="circle"><circle cx="{width / 2:.2f}" cy="{height / 2:.2f}" r="{min(width, height) / 2:.2f}"/></clipPath></defs>' if circular else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}" role="img" aria-label="Dot matrix portrait"{clip}>{defs}{"".join(dots)}</svg>\n'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input image, for example me.png")
    parser.add_argument("output", type=Path, help="Output SVG path")
    parser.add_argument("--columns", type=int, default=72)
    parser.add_argument("--detail", type=float, default=1.0, help="Detail multiplier from 0.1 to 2.0")
    parser.add_argument("--color", action="store_true")
    parser.add_argument("--circular", action="store_true")
    parser.add_argument("--dot-size", type=float, default=8.0)
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"input image not found: {args.input}")
    if args.columns < 8 or args.dot_size <= 0:
        parser.error("columns must be at least 8 and dot-size must be positive")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(args.input) as image:
        args.output.write_text(build_svg(image, args.columns, max(0.1, min(2.0, args.detail)), args.color, args.circular, args.dot_size), encoding="utf-8")


if __name__ == "__main__":
    main()