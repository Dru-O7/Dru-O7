#!/usr/bin/env python3
"""Render a De Stijl (Neoplasticism) GitHub stats card to assets/stats.svg.

Uses the GraphQL API when GITHUB_TOKEN is set (the Actions workflow provides it);
falls back to the unauthenticated REST API otherwise, with contribution metrics shown as "—".
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

USER = os.environ.get("STATS_USER", "Dru-O7")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = Path(__file__).resolve().parent.parent / "assets" / "stats.svg"

RED, BLUE, YELLOW = "#E63946", "#1D3557", "#FFD166"
BLACK, WHITE, CANVAS = "#111111", "#FFFFFF", "#F8F9FA"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"


def call(url, body=None):
    headers = {"User-Agent": "destijl-stats", "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_graphql():
    query = """
    query($login: String!) {
      user(login: $login) {
        followers { totalCount }
        pullRequests { totalCount }
        repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
          totalCount
          nodes { stargazerCount }
        }
        contributionsCollection {
          totalCommitContributions
          contributionCalendar { totalContributions }
        }
      }
    }"""
    res = call("https://api.github.com/graphql", {"query": query, "variables": {"login": USER}})
    if "errors" in res:
        raise RuntimeError(res["errors"])
    u = res["data"]["user"]
    cc = u["contributionsCollection"]
    return {
        "contrib": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "prs": u["pullRequests"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
    }


def fetch_rest():
    repos = [r for r in call(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    prs = call(f"https://api.github.com/search/issues?q=author:{USER}+type:pr")["total_count"]
    return {
        "contrib": None,
        "commits": None,
        "stars": sum(r["stargazers_count"] for r in repos),
        "prs": prs,
        "repos": len(repos),
    }


def fmt(n):
    if n is None:
        return "—"
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def cell(x, y, w, h, fill, label, value, ink, size):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
        f'<text x="{x + 16}" y="{y + 21}" font-size="11" font-weight="700" letter-spacing="2" fill="{ink}">{label}</text>'
        f'<text x="{x + 14}" y="{y + h - 14}" font-size="{size}" font-weight="900" fill="{ink}">{value}</text>'
    )


def render(s):
    parts = [
        f'<rect width="600" height="220" fill="{BLACK}"/>',
        # title band: red mass + small yellow patch
        f'<rect x="10" y="10" width="400" height="50" fill="{RED}"/>',
        f'<text x="26" y="42" font-size="16" font-weight="800" letter-spacing="4" fill="{WHITE}">■ STATS / {USER.upper()}</text>',
        f'<rect x="420" y="10" width="170" height="50" fill="{YELLOW}"/>',
        # dominant white field
        cell(10, 70, 280, 140, WHITE, "CONTRIBUTIONS · 1Y", fmt(s["contrib"]), BLACK, 72),
        # 2x2 minor grid
        cell(300, 70, 140, 65, CANVAS, "STARS", fmt(s["stars"]), BLACK, 30),
        cell(450, 70, 140, 65, WHITE, "COMMITS · 1Y", fmt(s["commits"]), BLACK, 30),
        cell(300, 145, 140, 65, WHITE, "PULL REQS", fmt(s["prs"]), BLACK, 30),
        cell(450, 145, 140, 65, BLUE, "REPOS", fmt(s["repos"]), WHITE, 30),
    ]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="220" viewBox="0 0 600 220" '
        f'role="img" aria-labelledby="t"><title id="t">GitHub stats for {USER}</title>'
        f'<g font-family="{FONT}">' + "".join(parts) + "</g></svg>\n"
    )


def main():
    try:
        stats = fetch_graphql() if TOKEN else fetch_rest()
    except Exception as e:  # keep the previous card rather than publishing a broken one
        print(f"stats fetch failed: {e}", file=sys.stderr)
        return 1
    OUT.write_text(render(stats), encoding="utf-8")
    print(f"wrote {OUT}: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
