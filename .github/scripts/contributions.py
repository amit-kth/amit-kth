"""Render a contribution calendar as an SVG that matches the README's look.

Usage: GITHUB_TOKEN=... LOGIN=username python contributions.py assets/contributions.svg
Stdlib only. Runs in GitHub Actions (see workflows/contributions.yml).
"""
import json, os, sys, urllib.request
from datetime import date

LEVELS = ["#EEE6F9", "#D2BAF4", "#A774E8", "#7C3AED", "#4A1F8A"]
FONT = "Inter, 'Segoe UI', system-ui, -apple-system, Helvetica, Arial, sans-serif"
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "readme-calendar"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = []
    for w in cal["weeks"]:
        col = [None] * 7
        for d in w["contributionDays"]:
            col[d["weekday"]] = (d["date"], d["contributionCount"])
        weeks.append(col)
    return weeks, cal["totalContributions"]


def render(weeks, total, note=None):
    P, C, X0, Y0 = 20, 16, 84, 104
    W = 1280
    H = Y0 + 7 * P + 70
    mx = max([c[1] for w in weeks for c in w if c] or [0])
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution calendar: {total} contributions in the last year">',
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F8F4FD"/><stop offset="1" stop-color="#EBDFFB"/></linearGradient></defs>',
        f'<style>text{{font-family:{FONT}}}</style>',
        f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="8" fill="url(#g)" stroke="#CDBBE6"/>',
        f'<text x="40" y="52" font-size="26" font-weight="700" fill="#14151F">{total:,} contributions in the last year</text>',
    ]
    if note:
        out.append(f'<text x="{W-40}" y="52" text-anchor="end" font-size="17" fill="#5A5470">{note}</text>')
    for r, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="40" y="{Y0 + r*P + 13}" font-size="14" fill="#5A5470">{lab}</text>')
    prev = None
    for i, w in enumerate(weeks):
        first = next((c for c in w if c), None)
        if first:
            m = date.fromisoformat(first[0]).month
            if m != prev:
                out.append(f'<text x="{X0 + i*P}" y="{Y0 - 14}" font-size="14" fill="#5A5470">{date(2000, m, 1):%b}</text>')
                prev = m
        for r, c in enumerate(w):
            if not c:
                continue
            n = c[1]
            lvl = 0 if n == 0 else min(4, max(1, -(-n * 4 // mx)))
            out.append(f'<rect x="{X0 + i*P}" y="{Y0 + r*P}" width="{C}" height="{C}" rx="2" fill="{LEVELS[lvl]}"><title>{n} on {c[0]}</title></rect>')
    ly = Y0 + 7 * P + 34
    lx = W - 40 - (5 * P + 90)
    out.append(f'<text x="{lx}" y="{ly + 13}" font-size="14" fill="#5A5470">Less</text>')
    for k, col in enumerate(LEVELS):
        out.append(f'<rect x="{lx + 44 + k*P}" y="{ly}" width="{C}" height="{C}" rx="2" fill="{col}"/>')
    out.append(f'<text x="{lx + 44 + 5*P + 6}" y="{ly + 13}" font-size="14" fill="#5A5470">More</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    weeks, total = fetch(os.environ["LOGIN"], os.environ["GITHUB_TOKEN"])
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.write(render(weeks, total))
