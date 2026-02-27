import argparse
import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "Thiagosdep"
GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
{
  user(login: "%s") {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
    pullRequests { totalCount }
    issues { totalCount }
  }
}
"""


def fetch_stats(token: str) -> dict:
    body = json.dumps({"query": QUERY % USERNAME}).encode()
    req = Request(GRAPHQL_URL, data=body, headers={
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    })
    with urlopen(req) as resp:
        user = json.loads(resp.read())["data"]["user"]

    return {
        "commits": (
            user["contributionsCollection"]["totalCommitContributions"]
            + user["contributionsCollection"]["restrictedContributionsCount"]
        ),
        "stars": sum(r["stargazerCount"] for r in user["repositories"]["nodes"]),
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "repos": user["repositories"]["totalCount"],
    }


def demo_stats() -> dict:
    return {"commits": 1847, "stars": 342, "prs": 156, "issues": 89, "repos": 42}


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    out = Path("assets/generated")
    out.mkdir(parents=True, exist_ok=True)

    stats = demo_stats() if args.demo else fetch_stats(os.environ["GITHUB_TOKEN"])
    (out / "stats.svg").write_text(generate_svg(stats))
    print(f"Generated stats.svg: {stats}")


if __name__ == "__main__":
    main()
