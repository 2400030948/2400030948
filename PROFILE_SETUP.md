# Profile README setup

This repository is the public profile repository for [Krishna Magar](https://github.com/2400030948). The checked-in SVGs are generated locally with Python and do not require a token.

## Requirements

- Python 3.10 or newer
- Pillow (`python -m pip install Pillow`), already available in the development environment
- A public GitHub repository named exactly `2400030948`

## Generate assets on Windows

From PowerShell at the repository root:

```powershell
python scripts/radar.py
python scripts/cards.py
```

The commands refresh `assets/languages.json`, both radar themes, and eight project-card variants. GitHub API access is optional; unauthenticated access is enough for a small profile. Set `GITHUB_TOKEN` only in your local environment when you need a higher API limit.

To create a portrait, add your own `me.png` at the repository root, then run:

```powershell
python scripts/dotify.py me.png assets/portrait.svg --circular --columns 72
```

The README does not reference the portrait until that file exists, so no personal image is required.

## Preview and checks

Open `preview.html` directly in a browser after generating assets. For a quick validation:

```powershell
python -m json.tool assets/skills.json > $null
python -m json.tool assets/projects.json > $null
python -m json.tool assets/languages.json > $null
Get-ChildItem assets\*.svg | Measure-Object
```

## GitHub Actions

The repository must be **Public**. In **Settings -> Actions -> General -> Workflow permissions**, select **Read and write permissions**. Enable Actions, then use the **Actions** tab to run `Regenerate profile radars and cards`, `Generate contribution snake`, or `Refresh GitHub metrics` with **Run workflow**.

The radar and snake workflows use the repository-provided `GITHUB_TOKEN`. Metrics can use it as a fallback, but a `METRICS_TOKEN` secret is recommended for the metrics action's broader API access. Create that secret in **Settings -> Secrets and variables -> Actions -> New repository secret** with the name `METRICS_TOKEN`; enter the token directly in GitHub, never in this repository or chat.

Schedules use UTC cron expressions corresponding to early morning in Asia/Kolkata. Generated assets are committed by the workflows, and the actions only commit when files changed.

## Troubleshooting

- If a workflow cannot push, recheck the repository visibility and workflow permission setting.
- If language data is empty, run `python scripts/radar.py` again later or provide `GITHUB_TOKEN`; the visual renders a clear “No data yet” state.
- If `dotify.py` cannot open an image, confirm the path and that Pillow supports its format.
- If the snake is not visible yet, run its workflow once; the README intentionally points to generated output that may not exist on a fresh repository.