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
    bg, cyan, mag, amber, ink, dim = "#05060b", "#19f6ff", "#ff2e88", "#ffb000", "#e8fbff", "#5d6680"
    font = "'JetBrains Mono','SF Mono',Menlo,Consolas,'DejaVu Sans Mono',monospace"

    items = [
        ("COMMITS", stats["commits"], cyan),
        ("STARS", stats["stars"], amber),
        ("PULL_REQ", stats["prs"], mag),
        ("ISSUES", stats["issues"], cyan),
        ("REPOS", stats["repos"], mag),
    ]

    max_sqrt = max(math.sqrt(v) for _, v, _ in items) or 1
    seg_w, seg_gap, segs_max = 8, 3, 18
    y0, gap = 104, 30

    rows = ""
    for i, (label, value, color) in enumerate(items):
        y = y0 + i * gap
        lit = max(1, round((math.sqrt(value) / max_sqrt) * segs_max)) if value else 0
        delay = 0.2 + i * 0.12
        segs = ""
        for k in range(segs_max):
            x = 205 + k * (seg_w + seg_gap)
            on = k < lit
            fill = color if on else dim
            op = "0.9" if on else "0.18"
            begin = f"{delay + k * 0.03:.2f}s"
            segs += (
                f'<rect x="{x}" y="{y - 11}" width="{seg_w}" height="13" fill="{fill}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="{op}" dur="0.15s" begin="{begin}" fill="freeze"/></rect>'
            )
        rows += (
            f'  <g opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{delay:.2f}s" fill="freeze"/>'
            f'<text x="28" y="{y}" fill="{dim}" font-family="{font}" font-size="12" letter-spacing="1">{label}</text>'
            f'<text x="190" y="{y}" fill="{ink}" font-family="{font}" font-size="14" font-weight="700" text-anchor="end">{fmt(value)}</text>'
            f"{segs}"
            f"</g>\n"
        )

    corners = "".join(
        f'<path d="{d}" fill="none" stroke="{cyan}" stroke-width="2"/>'
        for d in (
            "M8 26V8H26", f"M{w - 26} 8H{w - 8}V26",
            f"M{w - 8} {h - 26}V{h - 8}H{w - 26}", f"M26 {h - 8}H8V{h - 26}",
        )
    )

    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">\n'
        f"  <defs>"
        f'<pattern id="g" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="{cyan}" stroke-opacity=".06"/></pattern>'
        f'<pattern id="s" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" fill-opacity=".35"/></pattern>'
        f"</defs>\n"
        f'  <rect width="{w}" height="{h}" fill="{bg}"/>\n'
        f'  <rect width="{w}" height="{h}" fill="url(#g)"/>\n'
        f'  <text x="28" y="36" fill="{mag}" font-family="{font}" font-size="12" letter-spacing="2">■ TELEMETRY</text>\n'
        f'  <text x="{w - 28}" y="36" fill="{dim}" font-family="{font}" font-size="11" text-anchor="end">'
        f"uplink: github.com/{USERNAME}</text>\n"
        f'  <line x1="28" y1="50" x2="{w - 28}" y2="50" stroke="{cyan}" stroke-opacity=".25"/>\n'
        f'  <text x="28" y="72" fill="{cyan}" font-family="{font}" font-size="13">$ telemetry --source github --refresh 12h</text>\n'
        f"{rows}"
        f'  <rect width="{w}" height="{h}" fill="url(#s)"/>\n'
        f"  {corners}\n"
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
