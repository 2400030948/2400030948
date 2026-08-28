"""Generate theme-aware radar SVGs from JSON data and public GitHub languages."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ACCENT = "#39D353"
EXCLUDED = {"shell", "makefile", "dockerfile", "batchfile", "procfile"}


def fetch_json(url: str) -> object:
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-assets-generator"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def github_language_axes(username: str) -> list[dict[str, object]]:
    totals: dict[str, int] = {}
    try:
        repos = fetch_json(f"https://api.github.com/users/{username}/repos?per_page=100&type=owner")
        for repo in repos if isinstance(repos, list) else []:
            if repo.get("fork"):
                continue
            languages = fetch_json(repo["languages_url"])
            if isinstance(languages, dict):
                for name, count in languages.items():
                    if name.lower() not in EXCLUDED:
                        totals[name] = totals.get(name, 0) + int(count)
    except (HTTPError, URLError, TimeoutError, KeyError, ValueError):
        pass
    if not totals:
        return [{"label": "No data yet", "value": 0}]
    total = sum(totals.values())
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:8]
    return [{"label": name, "value": round(count / total * 100, 1)} for name, count in ranked]


def point(cx: float, cy: float, radius: float, index: int, count: int, value: float) -> str:
    angle = -math.pi / 2 + (index * 2 * math.pi / count)
    distance = radius * value / 100
    return f"{cx + math.cos(angle) * distance:.1f},{cy + math.sin(angle) * distance:.1f}"


def make_svg(title: str, axes: list[dict[str, object]], theme: str) -> str:
    dark = theme == "dark"
    background = "#0d1117" if dark else "#ffffff"
    foreground = "#e6edf3" if dark else "#24292f"
    muted = "#8b949e" if dark else "#57606a"
    grid = "#30363d" if dark else "#d0d7de"
    width, height, cx, cy, radius = 720, 420, 360, 220, 140
    count = max(3, len(axes))
    rings = []
    for level in (20, 40, 60, 80, 100):
        points = " ".join(point(cx, cy, radius, i, count, level) for i in range(count))
        rings.append(f'<polygon points="{points}" fill="none" stroke="{grid}" stroke-width="1"/>')
    spokes = []
    labels = []
    for index, axis in enumerate(axes):
        end = point(cx, cy, radius, index, count, 100)
        spokes.append(f'<line x1="{cx}" y1="{cy}" x2="{end.split(",")[0]}" y2="{end.split(",")[1]}" stroke="{grid}"/>')
        angle = -math.pi / 2 + (index * 2 * math.pi / count)
        lx = cx + math.cos(angle) * (radius + 28)
        ly = cy + math.sin(angle) * (radius + 28)
        anchor = "middle" if abs(math.cos(angle)) < 0.35 else ("start" if lx > cx else "end")
        labels.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" fill="{foreground}">{axis["label"]}</text>')
    values = " ".join(point(cx, cy, radius, i, count, float(axis["value"])) for i, axis in enumerate(axes))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
<rect width="100%" height="100%" rx="12" fill="{background}"/>
<text x="32" y="42" fill="{foreground}" font-family="system-ui, sans-serif" font-size="20" font-weight="700">{title}</text>
<g font-family="system-ui, sans-serif" font-size="13">{"".join(rings)}{"".join(spokes)}
<polygon points="{values}" fill="{ACCENT}" fill-opacity="0.22" stroke="{ACCENT}" stroke-width="3" stroke-linejoin="round"/>
{"".join(labels)}</g>
<text x="32" y="395" fill="{muted}" font-family="system-ui, sans-serif" font-size="12">{("Self-rating, 0-100" if "Self" in title else "Share of detected repository language bytes")}</text>
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills", type=Path, default=ROOT / "assets/skills.json")
    parser.add_argument("--username", default="2400030948")
    parser.add_argument("--language-output", type=Path, default=ROOT / "assets/languages.json")
    args = parser.parse_args()
    skills = json.loads(args.skills.read_text(encoding="utf-8"))
    args.language_output.write_text(json.dumps({"title": "GitHub language mix", "axes": github_language_axes(args.username)}, indent=2) + "\n", encoding="utf-8")
    for theme in ("dark", "light"):
        (ROOT / f"assets/radar-{theme}.svg").write_text(make_svg(skills["title"], skills["axes"], theme), encoding="utf-8")
        languages = json.loads(args.language_output.read_text(encoding="utf-8"))
        (ROOT / f"assets/languages-radar-{theme}.svg").write_text(make_svg(languages["title"], languages["axes"], theme), encoding="utf-8")


if __name__ == "__main__":
    main()