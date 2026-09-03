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
<text x="30" y="180" fill="{muted}" font-size="11">{html.escape(live_text) if live_text else "Public repository"}</text></g></svg>'''


def fetch_user() -> dict[str, object]:
    request = Request(f"https://api.github.com/users/{OWNER}", headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-assets-generator"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError):
        return {}


def fetch_owned_repos() -> list[dict[str, object]]:
    token = os.environ.get("GITHUB_TOKEN")
    repos: list[dict[str, object]] = []
    page = 1
    try:
        while True:
            request = Request(
                f"https://api.github.com/users/{OWNER}/repos?per_page=100&page={page}&type=owner",
                headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-assets-generator"},
            )
            if token:
                request.add_header("Authorization", f"Bearer {token}")
            with urlopen(request, timeout=15) as response:
                batch = json.load(response)
            repos += batch
            if len(batch) < 100:
                break
            page += 1
    except (HTTPError, URLError, TimeoutError, ValueError):
        pass
    return [repo for repo in repos if not repo.get("fork")]


CONTRIB_QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}
"""

def fetch_contribution_stats() -> tuple[int, int, int] | None:
    """Return (total, current_streak, longest_streak), or None without a token."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    body = json.dumps({"query": CONTRIB_QUERY, "variables": {"login": OWNER}}).encode()
    request = Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-assets-generator",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None
    if data.get("errors"):
        return None
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = sorted((day["date"], day["contributionCount"]) for week in calendar["weeks"] for day in week["contributionDays"])
    if not days:
        return calendar["totalContributions"], 0, 0
    longest = streak = 0
    for _, count in days:
        streak = streak + 1 if count > 0 else 0
        longest = max(longest, streak)
    current = 0
    for date, count in reversed(days):
        if count > 0:
            current += 1
        elif date != days[-1][0]:
            break
    return calendar["totalContributions"], current, longest


def stats_card(theme: str, tiles: list[tuple[str, str]]) -> str:
    dark = theme == "dark"
    background = "#0d1117" if dark else "#ffffff"
    foreground = "#e6edf3" if dark else "#24292f"
    muted = "#8b949e" if dark else "#57606a"
    border = "#30363d" if dark else "#d0d7de"
    accent = "#39D353"
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    width, pad, row_height = 480, 24, 46
    height = pad + 52 + (rows - 1) * row_height + 17 + pad
    tile_width = (width - 2 * pad) / cols
    parts = [
        f'<text x="{pad}" y="{pad + 14}" font-size="15" font-weight="700" fill="{accent}">Krishna Magar</text>',
        f'<text x="{width - pad}" y="{pad + 14}" font-size="11" text-anchor="end" fill="{muted}">at a glance</text>',
        f'<line x1="{pad}" y1="{pad + 26}" x2="{width - pad}" y2="{pad + 26}" stroke="{border}"/>',
    ]
    top = pad + 52
    for index, (label, value) in enumerate(tiles):
        cx = pad + (index % cols) * tile_width
        cy = top + (index // cols) * row_height
        parts.append(f'<text x="{cx:.0f}" y="{cy:.0f}" font-size="23" font-weight="700" fill="{foreground}">{html.escape(value)}</text>')
        parts.append(f'<text x="{cx:.0f}" y="{cy + 17:.0f}" font-size="10.5" fill="{muted}">{html.escape(label)}</text>')
    body = "".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="Krishna Magar GitHub statistics" font-family="system-ui, sans-serif">'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{background}" stroke="{border}"/>'
        f"{body}</svg>"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", type=Path, default=ROOT / "assets/projects.json")
    args = parser.parse_args()

    user = fetch_user()
    owned = fetch_owned_repos()
    total_stars = sum(int(repo.get("stargazers_count", 0)) for repo in owned)

    tiles = [
        ("Public repos", f"{int(user.get('public_repos', 0)):,}"),
        ("Followers", f"{int(user.get('followers', 0)):,}"),
        ("Total stars", f"{total_stars:,}"),
    ]
    contribution_stats = fetch_contribution_stats()
    if contribution_stats:
        total, current, longest = contribution_stats
        tiles += [
            ("Contributions (1y)", f"{total:,}"),
            ("Current streak", f"{current:,}"),
            ("Longest streak", f"{longest:,}"),
        ]

    for theme in ("dark", "light"):
        output = ROOT / f"assets/card-stats-{theme}.svg"
        output.write_text(stats_card(theme, tiles), encoding="utf-8")
    print(f"wrote card-stats-*.svg  ({len(tiles)} tiles)")

    projects = json.loads(args.projects.read_text(encoding="utf-8"))
    for index, project in enumerate(projects, 1):
        metadata = repo_data(str(project["repo"]))
        for theme in ("dark", "light"):
            output = ROOT / f"assets/project-{index}-{theme}.svg"
            output.write_text(card(project, theme, metadata), encoding="utf-8")


if __name__ == "__main__":
    main()