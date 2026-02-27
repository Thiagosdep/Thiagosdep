import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "Thiagosdep"
API_BASE = "https://api.github.com"


def _get(url: str, headers: dict) -> dict | list:
    print(f"  GET {url}")
    req = Request(url, headers=headers)
    with urlopen(req) as resp:
        data = json.loads(resp.read())
    print(f"  -> OK")
    return data


def fetch_stats(token: str) -> dict:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    user = _get(f"{API_BASE}/users/{USERNAME}", headers)

    stars = 0
    page = 1
    while True:
        repos = _get(
            f"{API_BASE}/users/{USERNAME}/repos?per_page=100&page={page}&type=owner",
            headers,
        )
        if not repos:
            break
        stars += sum(r["stargazers_count"] for r in repos)
        page += 1

    prs = _get(
        f"{API_BASE}/search/issues?q=author:{USERNAME}+type:pr",
        headers,
    )

    issues = _get(
        f"{API_BASE}/search/issues?q=author:{USERNAME}+type:issue",
        headers,
    )

    commits = _get(
        f"{API_BASE}/search/commits?q=author:{USERNAME}",
        {**headers, "Accept": "application/vnd.github.cloak-preview+json"},
    )

    return {
        "commits": commits.get("total_count", 0),
        "stars": stars,
        "prs": prs.get("total_count", 0),
        "issues": issues.get("total_count", 0),
        "repos": user.get("public_repos", 0),
    }


def fmt(n: int) -> str:
    if n >= 10_000:
        return f"{n // 1000}k"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def generate_svg(stats: dict) -> str:
    w, h = 495, 270
    bg, border, text_c, dim = "#0d1117", "#30363d", "#e6edf3", "#7d8590"
    font = "'JetBrains Mono','Fira Code','Cascadia Code','SF Mono',monospace"

    items = [
        ("Commits", stats["commits"], "#58a6ff"),
        ("Stars", stats["stars"], "#f0883e"),
        ("PRs", stats["prs"], "#a371f7"),
        ("Issues", stats["issues"], "#3fb950"),
        ("Repos", stats["repos"], "#d2a8ff"),
    ]

    max_sqrt = max(math.sqrt(v) for _, v, _ in items) or 1
    bar_max = 180
    y0, gap = 100, 32

    rows = ""
    for i, (label, value, color) in enumerate(items):
        y = y0 + i * gap
        bar_w = max(6, (math.sqrt(value) / max_sqrt) * bar_max)
        delay = f"{0.2 + i * 0.12:.2f}s"

        rows += (
            f'  <g opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{delay}" fill="freeze"/>'
            f'<text x="32" y="{y}" fill="{dim}" font-family="{font}" font-size="13">{label}</text>'
            f'<text x="130" y="{y}" fill="{text_c}" font-family="{font}" font-size="14" font-weight="600">{fmt(value)}</text>'
            f'<rect x="195" y="{y - 11}" width="0" height="13" rx="3" fill="{color}" opacity="0.85">'
            f'<animate attributeName="width" from="0" to="{bar_w:.1f}" dur="0.5s" begin="{delay}" fill="freeze"/>'
            f"</rect>"
            f"</g>\n"
        )

    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <rect width="{w}" height="{h}" rx="10" fill="{bg}" stroke="{border}" stroke-width="1"/>\n'
        f'  <circle cx="20" cy="20" r="6" fill="#ff5f57"/>\n'
        f'  <circle cx="38" cy="20" r="6" fill="#febc2e"/>\n'
        f'  <circle cx="56" cy="20" r="6" fill="#28c840"/>\n'
        f'  <text x="{w / 2}" y="24" fill="{dim}" font-family="{font}" font-size="12" text-anchor="middle">'
        f"{USERNAME}@github — stats</text>\n"
        f'  <line x1="0" y1="40" x2="{w}" y2="40" stroke="{border}" stroke-width="1"/>\n'
        f'  <text x="20" y="65" fill="#3fb950" font-family="{font}" font-size="14">❯</text>\n'
        f'  <text x="38" y="65" fill="{text_c}" font-family="{font}" font-size="13">git stats --profile</text>\n'
        f"{rows}"
        f"</svg>\n"
    )


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN environment variable is required")

    out = Path("assets/generated")
    out.mkdir(parents=True, exist_ok=True)

    print(f"Fetching stats for {USERNAME}...")
    stats = fetch_stats(token)
    print(f"Stats: {stats}")

    svg = generate_svg(stats)
    (out / "stats.svg").write_text(svg)
    print("Generated stats.svg")


if __name__ == "__main__":
    main()
