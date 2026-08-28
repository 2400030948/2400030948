"""Generate compact project cards, enriching them with safe public GitHub metadata."""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OWNER = "2400030948"


def repo_data(name: str) -> dict[str, object]:
    request = Request(f"https://api.github.com/repos/{OWNER}/{name}", headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-assets-generator"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(request, timeout=15) as response:
            data = json.load(response)
            return {key: data.get(key) for key in ("stargazers_count", "forks_count", "language")}
    except (HTTPError, URLError, TimeoutError, ValueError):
        return {}


def card(project: dict[str, object], theme: str, metadata: dict[str, object]) -> str:
    dark = theme == "dark"
    background = "#0d1117" if dark else "#ffffff"
    foreground = "#e6edf3" if dark else "#24292f"
    muted = "#8b949e" if dark else "#57606a"
    border = "#30363d" if dark else "#d0d7de"
    name = html.escape(str(project["name"]))
    description = html.escape(str(project["description"]))
    technologies = html.escape(" · ".join(project["technologies"]))
    repo = f"https://github.com/{OWNER}/{project['repo']}"
    live = []
    if metadata.get("language"):
        live.append(f"Primary language: {html.escape(str(metadata['language']))}")
    if metadata.get("stargazers_count") is not None:
        live.append(f"Stars: {metadata['stargazers_count']}")
    live_text = "  ·  ".join(live)
    words = str(project["description"]).split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > 52 and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    description_lines = "".join(f'<tspan x="30" dy="{0 if index == 0 else 20}">{html.escape(line)}</tspan>' for index, line in enumerate(lines[:2]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 250" role="img" aria-label="{name} project card">
<rect x="1" y="1" width="458" height="248" rx="12" fill="{background}" stroke="{border}"/>
<rect x="1" y="1" width="6" height="248" rx="3" fill="#39D353"/>
<g font-family="system-ui, sans-serif"><text x="30" y="42" fill="{foreground}" font-size="19" font-weight="700">{name}</text>
<text x="30" y="76" fill="{muted}" font-size="13">{description_lines}</text>
<text x="30" y="133" fill="{foreground}" font-size="12">{technologies}</text>
<text x="30" y="180" fill="{muted}" font-size="11">{html.escape(live_text) if live_text else "Public repository"}</text>
<a href="{repo}"><text x="30" y="218" fill="#39D353" font-size="13" font-weight="700">View repository →</text></a></g></svg>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", type=Path, default=ROOT / "assets/projects.json")
    args = parser.parse_args()
    projects = json.loads(args.projects.read_text(encoding="utf-8"))
    for index, project in enumerate(projects, 1):
        metadata = repo_data(str(project["repo"]))
        for theme in ("dark", "light"):
            output = ROOT / f"assets/project-{index}-{theme}.svg"
            output.write_text(card(project, theme, metadata), encoding="utf-8")


if __name__ == "__main__":
    main()