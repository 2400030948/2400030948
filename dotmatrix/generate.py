from PIL import Image, ImageEnhance, ImageFilter
import os, glob, math

# ---- CONFIG ----
INPUT_DIR = "dotmatrix/input"
OUTPUT_SVG = "dotmatrix/output/dotmatrix_portrait.svg"
GRID = 100
SPACING = 10
MAX_R = 4.8
PAD = 8
# ----------------

CANVAS = GRID * SPACING
VIEWBOX = CANVAS + PAD * 2

def find_source_image():
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    files = []
    for e in exts:
        files.extend(glob.glob(os.path.join(INPUT_DIR, e)))
    if not files:
        raise FileNotFoundError(
            f"No image found in {INPUT_DIR}. Put your photo there "
            "(jpg/jpeg/png/webp) and run again."
        )
    return files[0]

def luminance(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def to_hex(r, g, b):
    return "#%02x%02x%02x" % (
        max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
    )

def main():
    src = find_source_image()
    print(f"Using source image: {src}")

    im = Image.open(src).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = 0
    crop = im.crop((left, top, left + side, top + side))

    crop = crop.filter(ImageFilter.UnsharpMask(radius=3, percent=80, threshold=2))

    small = crop.resize((GRID, GRID), Image.LANCZOS)
    small = ImageEnhance.Contrast(small).enhance(1.12)
    small = ImageEnhance.Color(small).enhance(1.2)
    small = ImageEnhance.Brightness(small).enhance(1.22)  # brighter

    px = small.load()

    cx_center, cy_center = GRID / 2, GRID / 2
    max_dist = math.hypot(GRID / 2, GRID / 2)

    rows_svg = []
    for ry in range(GRID):
        circles = []
        for cx in range(GRID):
            r, g, b = px[cx, ry]
            lum = luminance(r, g, b) / 255.0
            factor = lum ** 0.9

            # synthetic vignette so corners/edges fade toward empty,
            # giving a "sticker/cutout" look instead of a filled square
            dist = math.hypot(cx - cx_center, ry - cy_center) / max_dist
            vignette = max(0.0, 1.0 - (dist ** 2.2) * 1.35)
            factor *= vignette

            radius = factor * MAX_R
            if radius < 0.35:
                if radius < 0.12:
                    continue
            x = PAD + cx * SPACING
            y = PAD + ry * SPACING
            color = to_hex(r, g, b)
            circles.append(f'<circle cx="{x}.0" cy="{y}.0" r="{radius:.2f}" fill="{color}"/>')
        rows_svg.append(f'<g class="rw r{ry}">' + "".join(circles) + "</g>")

    n = GRID
    delays = []
    for i in range(n):
        delay = (i / (n - 1)) * 2.5
        delays.append(f'.r{i}{{animation-delay:{delay:.3f}s}}')

    css = (
        "@keyframes rv{from{opacity:0}to{opacity:1}}"
        ".rw{animation:rv 0.45s ease-out both}" + "".join(delays)
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {VIEWBOX}.0 {VIEWBOX}.0" '
        f'width="{VIEWBOX}.0" height="{VIEWBOX}.0" '
        f'role="img" aria-label="dot-matrix portrait">'
        f'<style>{css}</style>'
        f'<g transform="translate({PAD}.0,{PAD}.0)">'
        + "".join(rows_svg) +
        '</g></svg>'
    )

    os.makedirs(os.path.dirname(OUTPUT_SVG), exist_ok=True)
    with open(OUTPUT_SVG, "w") as f:
        f.write(svg)

    print(f"Done. SVG written to {OUTPUT_SVG} ({len(svg)} bytes)")

if __name__ == "__main__":
    main()