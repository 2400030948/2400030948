"""
Generates an "at a glance" stat card SVG, matching the reference style:
dark rounded box, green username header, "at a glance" label, and a
2x3 grid of stats (total stars, public repos, followers, contributions
in the last year, current streak, longest streak).

Requires: requests
Env vars needed:
  GH_USERNAME   - your GitHub username
  GH_TOKEN      - a GitHub personal access token (repo + read:user scopes)
                  (in Actions, use secrets.GITHUB_TOKEN or a custom PAT)
"""

import os
import requests
from datetime import datetime, timedelta

USERNAME = os.environ["GH_USERNAME"]
TOKEN = os.environ["GH_TOKEN"]
OUTPUT_SVG = "assets/glance.svg"

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def gh_rest(path):
    r = requests.get(f"https://api.github.com{path}", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_basic_stats():
    user = gh_rest(f"/users/{USERNAME}")
    repos = gh_rest(f"/users/{USERNAME}/repos?per_page=100&type=owner")
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    public_repos = user.get("public_repos", 0)
    followers = user.get("followers", 0)
    return total_stars, public_repos, followers

def get_contribution_calendar():
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"login": USERNAME}},
        headers=HEADERS,
    )
    r.raise_for_status()
    data = r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in data["weeks"]:
        for day in week["contributionDays"]:
            days.append((day["date"], day["contributionCount"]))
    return days

def calc_contrib_and_streaks(days):
    total_1y = sum(count for _, count in days)

    days_sorted = sorted(days, key=lambda d: d[0])

    longest = 0
    running = 0
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    for date_str, count in days_sorted:
        if count > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    current = 0
    for date_str, count in reversed(days_sorted):
        if date_str > today_str:
            continue
        if count > 0:
            current += 1
        else:
            break

    return total_1y, current, longest

def build_svg(username, total_stars, public_repos, followers,
              contributions_1y, current_streak, longest_streak):

    W, H = 480, 166
    bg = "#0d1117"
    border = "#30363d"
    green = "#39D353"
    white = "#f0f6fc"
    gray = "#8b949e"

    def stat_block(x, y, value, label):
        return f'''
        <text x="{x}" y="{y}" font-family="Segoe UI, sans-serif" font-size="24" font-weight="700" fill="{white}">{value}</text>
        <text x="{x}" y="{y+20}" font-family="Segoe UI, sans-serif" font-size="12" fill="{gray}">{label}</text>
        '''

    col_xs = [24, 190, 356]
    row_ys = [82, 138]

    stats = [
        (total_stars, "Total stars"),
        (public_repos, "Public repos"),
        (followers, "Followers"),
        (contributions_1y, "Contributions (1y)"),
        (current_streak, "Current streak"),
        (longest_streak, "Longest streak"),
    ]

    blocks = ""
    idx = 0
    for row_y in row_ys:
        for col_x in col_xs:
            value, label = stats[idx]
            blocks += stat_block(col_x, row_y, value, label)
            idx += 1

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{bg}" stroke="{border}"/>
  <text x="24" y="34" font-family="Segoe UI, sans-serif" font-size="18" font-weight="700" fill="{green}">{username}</text>
  <text x="{W-24}" y="34" font-family="Segoe UI, sans-serif" font-size="12" fill="{gray}" text-anchor="end">at a glance</text>
  <line x1="24" y1="46" x2="{W-24}" y2="46" stroke="{border}" stroke-width="1"/>
  {blocks}
</svg>'''
    return svg

def main():
    total_stars, public_repos, followers = get_basic_stats()
    days = get_contribution_calendar()
    contributions_1y, current_streak, longest_streak = calc_contrib_and_streaks(days)

    svg = build_svg(
        USERNAME, total_stars, public_repos, followers,
        contributions_1y, current_streak, longest_streak
    )

    os.makedirs(os.path.dirname(OUTPUT_SVG), exist_ok=True)
    with open(OUTPUT_SVG, "w") as f:
        f.write(svg)

    print(f"Written {OUTPUT_SVG}")
    print(f"stars={total_stars} repos={public_repos} followers={followers} "
          f"contrib_1y={contributions_1y} current_streak={current_streak} "
          f"longest_streak={longest_streak}")

if __name__ == "__main__":
    main()