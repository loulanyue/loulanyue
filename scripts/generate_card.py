#!/usr/bin/env python3
"""
Generate the loulanyue GitHub profile SVG card.

Usage:
    python scripts/generate_card.py --token $GITHUB_TOKEN --output profile-card.svg

Fetches live data from GitHub API and renders the full card SVG including:
  - Original public repos count
  - Total owned stars
  - Followers
  - Upstream PRs (public contributions)
  - Radar chart (capability signal)
  - Update timestamp
"""

import argparse
import json
import math
import re
import sys
import urllib.request
from datetime import datetime, timezone


# ──────────────────────────────────────────────────────────────────────────────
# GitHub API helpers
# ──────────────────────────────────────────────────────────────────────────────

USERNAME = "loulanyue"
GRAPHQL_URL = "https://api.github.com/graphql"
REST_BASE = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "loulanyue-profile-card/1.0",
    }


def gql(token: str, query: str, variables: dict = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(GRAPHQL_URL, data=payload, headers=_headers(token))
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def rest_get(token: str, path: str) -> dict | list:
    url = f"{REST_BASE}{path}"
    req = urllib.request.Request(url, headers=_headers(token))
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


# ──────────────────────────────────────────────────────────────────────────────
# Data fetching
# ──────────────────────────────────────────────────────────────────────────────

STATS_QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(
      ownerAffiliations: OWNER
      privacy: PUBLIC
      isFork: false
      first: 1
    ) {
      totalCount
    }
    repositoriesContributedTo(
      includeUserRepositories: false
      contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]
      first: 1
    ) {
      totalCount
    }
  }
}
"""

STARS_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(
      ownerAffiliations: OWNER
      privacy: PUBLIC
      isFork: false
      first: 100
      after: $after
    ) {
      pageInfo { hasNextPage endCursor }
      nodes { stargazerCount }
    }
  }
}
"""

PR_COUNT_QUERY = """
query($q: String!) {
  search(type: ISSUE, query: $q, first: 1) {
    issueCount
  }
}
"""


def fetch_stats(token: str) -> dict:
    # Basic stats
    data = gql(token, STATS_QUERY, {"login": USERNAME})["data"]["user"]
    followers = data["followers"]["totalCount"]
    own_repos = data["repositories"]["totalCount"]

    # Total owned stars (paginated)
    total_stars = 0
    after = None
    while True:
        page = gql(token, STARS_QUERY, {"login": USERNAME, "after": after})
        repos_page = page["data"]["user"]["repositories"]
        for node in repos_page["nodes"]:
            total_stars += node["stargazerCount"]
        pi = repos_page["pageInfo"]
        if not pi["hasNextPage"]:
            break
        after = pi["endCursor"]

    # Public upstream PRs (author = user, not in own repos)
    pr_query = f"type:pr author:{USERNAME} -user:{USERNAME} is:public"
    pr_data = gql(token, PR_COUNT_QUERY, {"q": pr_query})
    upstream_prs = pr_data["data"]["search"]["issueCount"]

    return {
        "own_repos": own_repos,
        "total_stars": total_stars,
        "followers": followers,
        "upstream_prs": upstream_prs,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d UTC"),
    }


# ──────────────────────────────────────────────────────────────────────────────
# SVG rendering
# ──────────────────────────────────────────────────────────────────────────────

TEAL = "#1a9e8f"
TEAL_DARK = "#0d7a6e"
TEAL_FAINT = "#e6f5f3"
TEXT_DARK = "#0d2b26"
TEXT_MID = "#4a7a74"
TEXT_LIGHT = "#7ab5ae"
BG = "#f7fafa"
BORDER = "#cce8e5"
W, H = 900, 280


def fmt_number(n: int) -> str:
    """Format large numbers with commas."""
    return f"{n:,}"


def radar_path(cx: float, cy: float, r: float, values: list[float], scale: float = 1.0) -> str:
    """
    Build SVG polygon path for radar chart.
    values: list of 0..1 floats for each axis (evenly spaced, starting from top).
    """
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        angle = math.radians(-90 + i * 360 / n)
        pr = r * v * scale
        x = cx + pr * math.cos(angle)
        y = cy + pr * math.sin(angle)
        pts.append(f"{x:.2f},{y:.2f}")
    return "M " + " L ".join(pts) + " Z"


def ring_path(cx: float, cy: float, r: float, n_axes: int) -> str:
    """Polygon ring for the radar grid."""
    pts = []
    for i in range(n_axes):
        angle = math.radians(-90 + i * 360 / n_axes)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        pts.append(f"{x:.2f},{y:.2f}")
    return "M " + " L ".join(pts) + " Z"


def spoke_lines(cx: float, cy: float, r: float, n_axes: int) -> str:
    lines = []
    for i in range(n_axes):
        angle = math.radians(-90 + i * 360 / n_axes)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        lines.append(f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{x:.2f}" y2="{y:.2f}" '
                     f'stroke="{TEAL}" stroke-width="0.5" stroke-opacity="0.35"/>')
    return "\n".join(lines)


def render_radar(cx: float, cy: float, r: float) -> str:
    """Render the compass/radar chart matching the screenshot style."""
    # Axis values (0..1): agent runtimes, model systems, dev tooling, security, upstream
    values = [0.72, 0.58, 0.65, 0.80, 0.55]
    n = len(values)
    rings = [0.25, 0.50, 0.75, 1.0]

    parts = []

    # Outer circle border
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                 f'stroke="{TEAL}" stroke-width="1.2" stroke-opacity="0.4"/>')

    # Grid rings
    for frac in rings:
        parts.append(f'<path d="{ring_path(cx, cy, r * frac, n)}" '
                     f'fill="none" stroke="{TEAL}" stroke-width="0.6" stroke-opacity="0.3"/>')

    # Spoke lines
    parts.append(spoke_lines(cx, cy, r, n))

    # Cardinal labels
    label_r = r + 14
    cardinals = [("N 000°", 0), ("E 090°", 90), ("S 180°", 180), ("W 270°", 270)]
    for label, deg in cardinals:
        angle = math.radians(deg - 90)
        lx = cx + label_r * math.cos(angle)
        ly = cy + label_r * math.sin(angle)
        anchor = "middle"
        if deg == 0:
            ly -= 4
        elif deg == 180:
            ly += 10
        elif deg == 90:
            anchor = "start"
            lx += 2
        elif deg == 270:
            anchor = "end"
            lx -= 2
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" '
                     f'font-family="monospace" font-size="6.5" fill="{TEAL}" '
                     f'text-anchor="{anchor}" opacity="0.7">{label}</text>')

    # Data fill
    parts.append(f'<path d="{radar_path(cx, cy, r, values)}" '
                 f'fill="{TEAL}" fill-opacity="0.18" '
                 f'stroke="{TEAL}" stroke-width="1.5"/>')

    # Center dot
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="{TEAL}" opacity="0.7"/>')

    # LIVE SCAN badge
    badge_y = cy + r + 22
    parts.append(f'<rect x="{cx - 28}" y="{badge_y - 8}" width="56" height="14" rx="3" '
                 f'fill="none" stroke="{TEAL}" stroke-width="0.8" opacity="0.6"/>')
    parts.append(f'<circle cx="{cx - 18}" cy="{badge_y - 1}" r="3" fill="{TEAL}" opacity="0.8"/>')
    parts.append(f'<text x="{cx - 11}" y="{badge_y + 3}" '
                 f'font-family="monospace" font-size="7" fill="{TEAL}" opacity="0.8">'
                 f'LIVE SCAN</text>')

    return "\n".join(parts)


def render_svg(stats: dict) -> str:
    own_repos = fmt_number(stats["own_repos"])
    total_stars = fmt_number(stats["total_stars"])
    followers = fmt_number(stats["followers"])
    upstream_prs = fmt_number(stats["upstream_prs"])
    updated_at = stats["updated_at"]

    # Radar center
    radar_cx = 770.0
    radar_cy = 130.0
    radar_r = 90.0

    radar_svg = render_radar(radar_cx, radar_cy, radar_r)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&amp;display=swap');
    </style>
    <clipPath id="card-clip">
      <rect width="{W}" height="{H}" rx="12"/>
    </clipPath>
  </defs>

  <!-- Card background -->
  <rect width="{W}" height="{H}" rx="12" fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>

  <!-- Divider between left content and radar -->
  <line x1="650" y1="20" x2="650" y2="{H - 20}" stroke="{BORDER}" stroke-width="1"/>

  <!-- ── Left content ── -->

  <!-- Status pill -->
  <circle cx="32" cy="34" r="5" fill="{TEAL}"/>
  <text x="44" y="38" font-family="monospace" font-size="10.5" fill="{TEAL}"
        font-weight="bold" letter-spacing="1">OPEN-SOURCE SYSTEMS ENGINEER · LOUISVILLE, KY</text>

  <!-- Name -->
  <text x="30" y="95" font-family="'Space Grotesk', 'Arial Black', sans-serif"
        font-size="52" font-weight="900" fill="{TEXT_DARK}" letter-spacing="3">LOULANYUE</text>

  <!-- Name underline -->
  <line x1="30" y1="103" x2="610" y2="103" stroke="{TEAL}" stroke-width="2"/>

  <!-- Chinese subtitle -->
  <text x="30" y="128" font-family="'PingFang SC', 'Noto Sans SC', sans-serif"
        font-size="13" fill="{TEXT_DARK}" font-weight="600">
    以开放系统工程推动智能体基础设施走向可验证、可组合与可持续演进
  </text>

  <!-- English subtitle -->
  <text x="30" y="148" font-family="'Space Grotesk', Arial, sans-serif"
        font-size="11.5" fill="{TEXT_MID}">
    Advancing agentic infrastructure through open systems engineered for
  </text>
  <text x="30" y="163" font-family="'Space Grotesk', Arial, sans-serif"
        font-size="11.5" fill="{TEXT_MID}">
    verification, composability, and long-term evolution.
  </text>

  <!-- Engineering Surface label -->
  <text x="30" y="187" font-family="monospace" font-size="9.5"
        fill="{TEAL}" letter-spacing="1.5" font-weight="bold">ENGINEERING SURFACE / 工程领域</text>

  <!-- Tags -->
  <!-- Tag 1: AGENT RUNTIMES -->
  <rect x="30" y="194" width="138" height="22" rx="11" fill="none"
        stroke="{TEAL}" stroke-width="1.2"/>
  <circle cx="47" cy="205" r="4" fill="{TEAL}"/>
  <text x="57" y="209" font-family="monospace" font-size="9.5"
        fill="{TEXT_DARK}" font-weight="bold" letter-spacing="0.8">AGENT RUNTIMES</text>

  <!-- Tag 2: MODEL SYSTEMS -->
  <rect x="176" y="194" width="128" height="22" rx="11" fill="none"
        stroke="{TEAL}" stroke-width="1.2"/>
  <circle cx="193" cy="205" r="4" fill="{TEAL}"/>
  <text x="203" y="209" font-family="monospace" font-size="9.5"
        fill="{TEXT_DARK}" font-weight="bold" letter-spacing="0.8">MODEL SYSTEMS</text>

  <!-- Tag 3: DEVELOPER TOOLING -->
  <rect x="312" y="194" width="148" height="22" rx="11" fill="none"
        stroke="{TEAL}" stroke-width="1.2"/>
  <circle cx="329" cy="205" r="4" fill="{TEAL}"/>
  <text x="339" y="209" font-family="monospace" font-size="9.5"
        fill="{TEXT_DARK}" font-weight="bold" letter-spacing="0.8">DEVELOPER TOOLING</text>

  <!-- ── Stats row ── -->
  <!-- Stat 1: Own repos -->
  <text x="30" y="244" font-family="'Space Grotesk', Arial, sans-serif"
        font-size="32" font-weight="900" fill="{TEXT_DARK}">{own_repos}</text>
  <text x="30" y="258" font-family="monospace" font-size="8.5"
        fill="{TEAL}" letter-spacing="0.8" font-weight="bold">ORIGINAL SYSTEMS</text>
  <text x="30" y="269" font-family="'PingFang SC', 'Noto Sans SC', sans-serif"
        font-size="8.5" fill="{TEXT_MID}">自有开放项目</text>

  <!-- Stat 2: Stars -->
  <text x="155" y="244" font-family="'Space Grotesk', Arial, sans-serif"
        font-size="32" font-weight="900" fill="{TEXT_DARK}">{total_stars}</text>
  <text x="155" y="258" font-family="monospace" font-size="8.5"
        fill="{TEAL}" letter-spacing="0.8" font-weight="bold">OWNED STARS</text>
  <text x="155" y="269" font-family="'PingFang SC', 'Noto Sans SC', sans-serif"
        font-size="8.5" fill="{TEXT_MID}">自有项目星标</text>

  <!-- Stat 3: Followers -->
  <text x="330" y="244" font-family="'Space Grotesk', Arial, sans-serif"
        font-size="32" font-weight="900" fill="{TEXT_DARK}">{followers}</text>
  <text x="330" y="258" font-family="monospace" font-size="8.5"
        fill="{TEAL}" letter-spacing="0.8" font-weight="bold">FOLLOWERS</text>
  <text x="330" y="269" font-family="'PingFang SC', 'Noto Sans SC', sans-serif"
        font-size="8.5" fill="{TEXT_MID}">关注者</text>

  <!-- Stat 4: Upstream PRs -->
  <text x="440" y="244" font-family="'Space Grotesk', Arial, sans-serif"
        font-size="32" font-weight="900" fill="{TEXT_DARK}">{upstream_prs}</text>
  <text x="440" y="258" font-family="monospace" font-size="8.5"
        fill="{TEAL}" letter-spacing="0.8" font-weight="bold">UPSTREAM PRS</text>
  <text x="440" y="269" font-family="'PingFang SC', 'Noto Sans SC', sans-serif"
        font-size="8.5" fill="{TEXT_MID}">公开上游贡献</text>

  <!-- ── Footer ── -->
  <line x1="30" y1="{H - 1}" x2="{W - 30}" y2="{H - 1}" stroke="{BORDER}" stroke-width="0"/>
  <text x="30" y="{H + 16}" font-family="monospace" font-size="8.5"
        fill="{TEAL}" letter-spacing="1.2" font-weight="bold">
    DESIGN → CONTRIBUTE → VERIFY → STEWARD
  </text>
  <text x="{W - 30}" y="{H + 16}" font-family="monospace" font-size="8.5"
        fill="{TEXT_LIGHT}" text-anchor="end">UPDATED {updated_at}</text>

  <!-- Bottom footer bar inside card -->
  <line x1="30" y1="276" x2="620" y2="276" stroke="{BORDER}" stroke-width="0.8"/>
  <text x="30" y="287" font-family="monospace" font-size="8"
        fill="{TEAL}" letter-spacing="1" font-weight="bold" opacity="0.7">
    DESIGN → CONTRIBUTE → VERIFY → STEWARD
  </text>
  <text x="615" y="287" font-family="monospace" font-size="8"
        fill="{TEXT_LIGHT}" text-anchor="end">UPDATED {updated_at}</text>

  <!-- ── Radar chart (right) ── -->
  {radar_svg}
</svg>"""

    return svg


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate loulanyue profile card SVG")
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument("--output", default="profile-card.svg", help="Output SVG file path")
    args = parser.parse_args()

    print(f"Fetching stats for @{USERNAME}...")
    stats = fetch_stats(args.token)
    print(f"  Own repos    : {stats['own_repos']}")
    print(f"  Owned stars  : {stats['total_stars']:,}")
    print(f"  Followers    : {stats['followers']:,}")
    print(f"  Upstream PRs : {stats['upstream_prs']:,}")
    print(f"  Updated at   : {stats['updated_at']}")

    svg = render_svg(stats)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Card written to: {args.output}")


if __name__ == "__main__":
    main()
