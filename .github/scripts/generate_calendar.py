#!/usr/bin/env python3
"""Generate a dark/amber GitHub contribution calendar SVG."""
import os
import sys
from datetime import datetime

import requests

USER = os.environ["USERNAME"]
TOKEN = os.environ["GH_TOKEN"]

QUERY = """
query($user: String!) {
  user(login: $user) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": QUERY, "variables": {"user": USER}},
    headers={"Authorization": f"Bearer {TOKEN}"},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()
if "errors" in data:
    print(data["errors"], file=sys.stderr)
    sys.exit(1)

cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"]
total = cal["totalContributions"]

# Theme
BG = "#080807"
BORDER = "#2a2510"
MUTED = "#5a5040"
LEVELS = ["#0e0d0b", "#3d2a0a", "#7a5410", "#a67a15", "#d4920a"]

def level(count: int) -> str:
    if count == 0:
        return LEVELS[0]
    if count <= 3:
        return LEVELS[1]
    if count <= 8:
        return LEVELS[2]
    if count <= 15:
        return LEVELS[3]
    return LEVELS[4]

CELL = 11
GAP = 3
LEFT = 32
TOP = 22
RADIUS = 2

cols = len(weeks)
rows = 7
width = LEFT + cols * (CELL + GAP) + 12
height = TOP + rows * (CELL + GAP) + 14

out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    f'<rect width="{width}" height="{height}" fill="{BG}"/>',
]

# Day-of-week labels (Mon/Wed/Fri — GitHub-standard subset)
for idx, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
    y = TOP + idx * (CELL + GAP) + 9
    out.append(
        f'<text x="4" y="{y}" fill="{MUTED}" '
        f'font-family="\'Courier New\', monospace" font-size="9" letter-spacing="1">{label}</text>'
    )

# Month labels — first week whose first day falls in that month
seen = set()
for wi, w in enumerate(weeks):
    first = w["contributionDays"][0]
    dt = datetime.strptime(first["date"], "%Y-%m-%d")
    key = (dt.year, dt.month)
    if key not in seen and dt.day <= 7:
        seen.add(key)
        x = LEFT + wi * (CELL + GAP)
        out.append(
            f'<text x="{x}" y="14" fill="{MUTED}" '
            f'font-family="\'Courier New\', monospace" font-size="9" letter-spacing="1">'
            f'{dt.strftime("%b").upper()}</text>'
        )

# Cells
for wi, w in enumerate(weeks):
    for d in w["contributionDays"]:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        wd = (dt.weekday() + 1) % 7   # Sunday=0 (GitHub style)
        x = LEFT + wi * (CELL + GAP)
        y = TOP + wd * (CELL + GAP)
        fill = level(d["contributionCount"])
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="{RADIUS}" fill="{fill}"/>'
        )

# Footer: total count on the right
footer_y = height - 4
out.append(
    f'<text x="{width - 8}" y="{footer_y}" fill="{MUTED}" '
    f'font-family="\'Courier New\', monospace" font-size="9" letter-spacing="1" '
    f'text-anchor="end">{total} CONTRIBUTIONS IN THE LAST YEAR</text>'
)

out.append("</svg>")

with open("contribution_calendar.svg", "w") as f:
    f.write("\n".join(out))

print(f"Generated: {cols} weeks, {total} total contributions")
