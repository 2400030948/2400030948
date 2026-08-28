"""Turn a raster image into a clean dot-matrix SVG using Pillow."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageOps


def trim_photo_border(image: Image.Image) -> Image.Image:
    """Remove the light margin and dark frame commonly present in ID photos."""
    rgb = image.convert("RGB")
    width, height = rgb.size
    left, top = round(width * 0.025), round(height * 0.025)
    right, bottom = round(width * 0.975), round(height * 0.975)
    return rgb.crop((left, top, right, bottom))


def square_crop(image: Image.Image, focus_x: float, focus_y: float) -> Image.Image:
    width, height = image.size
    side = min(width, height)
    center_x = max(0.0, min(1.0, focus_x)) * width
    center_y = max(0.0, min(1.0, focus_y)) * height
    left = max(0, min(width - side, round(center_x - side / 2)))
    top = max(0, min(height - side, round(center_y - side / 2)))
    return image.crop((left, top, left + side, top + side))


def build_svg(
    image: Image.Image,
    columns: int,
    detail: float,
    color: bool,
    circular: bool,
    dot_size: float,
    equalize: bool,
    focus_x: float,
    focus_y: float,
) -> str:
    source = trim_photo_border(ImageOps.exif_transpose(image))
    source = square_crop(source, focus_x, focus_y)
    rows = columns
    source = source.resize((columns, rows), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(source)
    if equalize:
        gray = ImageOps.equalize(gray)
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
            fill = "#39D353"
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
    parser.add_argument("--columns", "--cols", dest="columns", type=int, default=72)
    parser.add_argument("--detail", type=float, default=1.0, help="Detail multiplier from 0.1 to 2.0")
    parser.add_argument("--equalize", action="store_true", help="Equalize grayscale contrast")
    parser.add_argument("--focus", nargs=2, type=float, metavar=("X", "Y"), default=(0.55, 0.45), help="Square crop focus as normalized X Y coordinates")
    parser.add_argument("--square", action="store_true", help="Use a square crop; retained for guide-compatible commands")
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
        args.output.write_text(
            build_svg(
                image,
                args.columns,
                max(0.1, min(2.0, args.detail)),
                args.color,
                args.circular,
                args.dot_size,
                args.equalize,
                args.focus[0],
                args.focus[1],
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()