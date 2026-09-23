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
W, H = 960, 480


def fmt_number(n: int) -> str:
    """Format large numbers with commas."""
    return f"{n:,}"


def render_radar(cx: float, cy: float, r: float) -> str:
    """Render the animated compass/radar chart with rotating scan beam matching the screenshot."""
    parts = []

    # ── Concentric solid & dashed circles ──
    # Outer circle
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
        f'stroke="{TEAL}" stroke-width="1.6" stroke-opacity="0.6"/>'
    )
    # Secondary outer ring
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r * 0.96:.1f}" fill="none" '
        f'stroke="{TEAL}" stroke-width="0.8" stroke-opacity="0.25"/>'
    )

    # Intermediate concentric rings (solid & dotted)
    rings = [
        (0.78, "solid", 0.7, 0.35),
        (0.64, "dashed", 0.6, 0.25),
        (0.50, "solid", 0.8, 0.40),
        (0.36, "dashed", 0.6, 0.25),
        (0.22, "solid", 0.8, 0.45),
        (0.08, "solid", 1.0, 0.60),
    ]
    for frac, style, sw, op in rings:
        dash = 'stroke-dasharray="3,3" ' if style == "dashed" else ''
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r * frac:.1f}" fill="none" '
            f'stroke="{TEAL}" stroke-width="{sw}" stroke-opacity="{op}" {dash}/>'
        )

    # ── Fine tick marks around outer perimeter (every 2 degrees) ──
    for deg in range(0, 360, 2):
        angle_rad = math.radians(deg - 90)
        if deg % 90 == 0:
            tl, sw, op = 12, 1.6, 0.8
        elif deg % 30 == 0:
            tl, sw, op = 8, 1.0, 0.6
        elif deg % 10 == 0:
            tl, sw, op = 5, 0.7, 0.4
        else:
            tl, sw, op = 3, 0.5, 0.25
        x1 = cx + (r - tl) * math.cos(angle_rad)
        y1 = cy + (r - tl) * math.sin(angle_rad)
        x2 = cx + r * math.cos(angle_rad)
        y2 = cy + r * math.sin(angle_rad)
        parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{TEAL}" stroke-width="{sw}" stroke-opacity="{op}"/>'
        )

    # ── Crosshairs along cardinal axes ──
    gap = r * 0.08
    parts.append(f'<line x1="{cx - r:.1f}" y1="{cy}" x2="{cx - gap:.1f}" y2="{cy}" stroke="{TEAL}" stroke-width="0.8" stroke-opacity="0.45"/>')
    parts.append(f'<line x1="{cx + gap:.1f}" y1="{cy}" x2="{cx + r:.1f}" y2="{cy}" stroke="{TEAL}" stroke-width="0.8" stroke-opacity="0.45"/>')
    parts.append(f'<line x1="{cx}" y1="{cy - r:.1f}" x2="{cx}" y2="{cy - gap:.1f}" stroke="{TEAL}" stroke-width="0.8" stroke-opacity="0.45"/>')
    parts.append(f'<line x1="{cx}" y1="{cy + gap:.1f}" x2="{cx}" y2="{cy + r:.1f}" stroke="{TEAL}" stroke-width="0.8" stroke-opacity="0.45"/>')

    # Sub-axis diagonal spokes (45°, 135°, 225°, 315°) dotted
    for diag_deg in [45, 135, 225, 315]:
        rad = math.radians(diag_deg - 90)
        dx1 = cx + gap * 1.5 * math.cos(rad)
        dy1 = cy + gap * 1.5 * math.sin(rad)
        dx2 = cx + (r * 0.95) * math.cos(rad)
        dy2 = cy + (r * 0.95) * math.sin(rad)
        parts.append(
            f'<line x1="{dx1:.1f}" y1="{dy1:.1f}" x2="{dx2:.1f}" y2="{dy2:.1f}" '
            f'stroke="{TEAL}" stroke-width="0.6" stroke-opacity="0.25" stroke-dasharray="2,3"/>'
        )

    # ── Cardinal direction labels ──
    label_r = r + 16
    for label, deg in [("N 000°", 0), ("E 090°", 90), ("S 180°", 180), ("W 270°", 270)]:
        angle_rad = math.radians(deg - 90)
        lx = cx + label_r * math.cos(angle_rad)
        ly = cy + label_r * math.sin(angle_rad)
        anchor = "middle"
        if deg == 0:
            ly -= 2
        elif deg == 180:
            ly += 10
        elif deg == 90:
            anchor = "start"
            lx += 3
            ly += 3
        elif deg == 270:
            anchor = "end"
            lx -= 3
            ly += 3
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" font-family="monospace" font-size="8.5" '
            f'fill="{TEAL}" font-weight="bold" text-anchor="{anchor}" opacity="0.85">{label}</text>'
        )

    # ── Telemetry watermark annotations inside rings ──
    parts.append(
        f'<text x="{cx - r * 0.28:.1f}" y="{cy - 4:.1f}" font-family="monospace" font-size="7" '
        f'fill="{TEAL}" opacity="0.45" text-anchor="middle">100K+</text>'
    )
    parts.append(
        f'<text x="{cx - r * 0.28:.1f}" y="{cy + 6:.1f}" font-family="monospace" font-size="6" '
        f'fill="{TEAL}" opacity="0.40" text-anchor="middle">MCP/TOOL</text>'
    )
    parts.append(
        f'<text x="{cx + r * 0.28:.1f}" y="{cy + 2:.1f}" font-family="monospace" font-size="6.5" '
        f'fill="{TEAL}" opacity="0.45" text-anchor="middle">HERMES</text>'
    )

    # ── Animated rotating radar sweep wedge (clockwise) ──
    def pt(deg_offset: float) -> tuple[float, float]:
        """Point on perimeter at deg_offset counter-clockwise behind leading edge."""
        a = math.radians(-deg_offset)
        return (r * math.sin(a), -r * math.cos(a))

    p0 = (0.0, -r)
    p15 = pt(15)
    p30 = pt(30)
    p50 = pt(50)
    p70 = pt(70)

    def arc(px: float, py: float, qx: float, qy: float) -> str:
        return f"M 0,0 L {px:.2f},{py:.2f} A {r:.1f},{r:.1f} 0 0,0 {qx:.2f},{qy:.2f} Z"

    w1 = arc(*p0, *p15)
    w2 = arc(*p15, *p30)
    w3 = arc(*p30, *p50)
    w4 = arc(*p50, *p70)

    sweep_group = (
        f'<g transform="translate({cx:.1f},{cy:.1f})">\n'
        f'  <g>\n'
        f'    <animateTransform attributeName="transform" type="rotate" '
        f'from="0" to="360" dur="5s" repeatCount="indefinite"/>\n'
        f'    <path d="{w1}" fill="{TEAL}" fill-opacity="0.32"/>\n'
        f'    <path d="{w2}" fill="{TEAL}" fill-opacity="0.18"/>\n'
        f'    <path d="{w3}" fill="{TEAL}" fill-opacity="0.08"/>\n'
        f'    <path d="{w4}" fill="{TEAL}" fill-opacity="0.03"/>\n'
        f'    <line x1="0" y1="{-r * 0.08:.1f}" x2="0" y2="{-r:.1f}" '
        f'stroke="{TEAL}" stroke-width="2" stroke-opacity="0.95"/>\n'
        f'    <circle cx="0" cy="{-r:.1f}" r="3" fill="{TEAL}" opacity="0.9"/>\n'
        f'  </g>\n'
        f'</g>'
    )
    parts.append(sweep_group)

    # ── Radar center hub & pulse ripple ──
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r * 0.08:.1f}" fill="{BG}" '
        f'stroke="{TEAL}" stroke-width="1.5" stroke-opacity="0.8"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="{TEAL}" opacity="0.9"/>'
    )
    # Expanding pulse ring
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="6" fill="none" stroke="{TEAL}" stroke-width="1.8">'
        f'<animate attributeName="r" values="6;{r * 0.25:.1f};6" dur="2.4s" repeatCount="indefinite"/>'
        f'<animate attributeName="stroke-opacity" values="0.8;0;0.8" dur="2.4s" repeatCount="indefinite"/>'
        f'</circle>'
    )

    # ── LIVE SCAN badge at bottom ──
    badge_y = cy + r + 26
    bw, bh = 76, 20
    bx = cx - (bw / 2)
    parts.append(
        f'<rect x="{bx:.1f}" y="{badge_y - bh/2:.1f}" width="{bw}" height="{bh}" rx="10" '
        f'fill="{BG}" stroke="{TEAL}" stroke-width="1.0" stroke-opacity="0.75"/>'
    )
    # Blinking green beacon
    parts.append(
        f'<circle cx="{bx + 14:.1f}" cy="{badge_y:.1f}" r="4" fill="{TEAL}">'
        f'<animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite"/>'
        f'</circle>'
    )
    parts.append(
        f'<text x="{bx + 24:.1f}" y="{badge_y + 3.5:.1f}" font-family="monospace" font-size="8.5" '
        f'fill="{TEAL}" font-weight="bold" opacity="0.9">LIVE SCAN</text>'
    )

    return "\n".join(parts)


def render_svg(stats: dict) -> str:
    own_repos = fmt_number(stats["own_repos"])
    total_stars = fmt_number(stats["total_stars"])
    followers = fmt_number(stats["followers"])
    upstream_prs = fmt_number(stats["upstream_prs"])
    updated_at = stats["updated_at"]

    # Radar center & radius
    radar_cx = 745.0
    radar_cy = 225.0
    radar_r = 150.0

    radar_svg = render_radar(radar_cx, radar_cy, radar_r)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700;900&amp;family=Noto+Sans+SC:wght@500;700;900&amp;display=swap');
      .heading {{ font-family: 'Space Grotesk', -apple-system, sans-serif; font-weight: 900; }}
      .subheading {{ font-family: 'Noto Sans SC', 'PingFang SC', sans-serif; }}
      .body-eng {{ font-family: 'Space Grotesk', -apple-system, sans-serif; font-weight: 500; }}
      .mono {{ font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace; }}
    </style>
    <!-- Background subtle tech grid -->
    <pattern id="tech-grid" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#e1f0ee" stroke-width="0.75"/>
    </pattern>
  </defs>

  <!-- Card background -->
  <rect width="{W}" height="{H}" rx="18" fill="{BG}" stroke="{BORDER}" stroke-width="1.8"/>
  <rect width="{W}" height="{H}" rx="18" fill="url(#tech-grid)"/>

  <!-- ── Left content ── -->

  <!-- Top Status -->
  <circle cx="52" cy="56" r="5" fill="{TEAL}"/>
  <text x="66" y="60" class="mono" font-size="11.5" fill="{TEAL}"
        font-weight="bold" letter-spacing="1.2">OPEN-SOURCE SYSTEMS ENGINEER · LOUISVILLE, KY</text>

  <!-- Giant Brand Name -->
  <text x="50" y="136" class="heading" font-size="62" fill="{TEXT_DARK}" letter-spacing="3.5">LOULANYUE</text>

  <!-- Underline under brand name -->
  <line x1="50" y1="152" x2="495" y2="152" stroke="{TEAL}" stroke-width="2.5"/>

  <!-- Chinese Philosophy Subtitle -->
  <text x="50" y="192" class="subheading" font-size="16" fill="{TEXT_DARK}" font-weight="700" letter-spacing="0.5">
    以开放系统工程推动智能体基础设施走向可验证、可组合与可持续演进
  </text>

  <!-- English Subtitle (two lines) -->
  <text x="50" y="222" class="body-eng" font-size="13" fill="{TEXT_MID}" letter-spacing="0.2">
    Advancing agentic infrastructure through open systems engineered for verification,
  </text>
  <text x="50" y="242" class="body-eng" font-size="13" fill="{TEXT_MID}" letter-spacing="0.2">
    composability, and long-term evolution.
  </text>

  <!-- Section Label -->
  <text x="50" y="282" class="mono" font-size="10.5" fill="{TEXT_MID}" letter-spacing="1.5" font-weight="bold">
    ENGINEERING SURFACE / 工程领域
  </text>

  <!-- Tags Row -->
  <!-- Tag 1: AGENT RUNTIMES -->
  <rect x="50" y="295" width="144" height="26" rx="13" fill="#e9f6f3" stroke="#bde6df" stroke-width="1.2"/>
  <circle cx="68" cy="308" r="4.5" fill="{TEAL}"/>
  <text x="79" y="312" class="mono" font-size="10" fill="{TEXT_DARK}" font-weight="bold" letter-spacing="0.8">AGENT RUNTIMES</text>

  <!-- Tag 2: MODEL SYSTEMS -->
  <rect x="204" y="295" width="138" height="26" rx="13" fill="#ebf6f1" stroke="#c4e7da" stroke-width="1.2"/>
  <circle cx="222" cy="308" r="4.5" fill="#2eb875"/>
  <text x="233" y="312" class="mono" font-size="10" fill="{TEXT_DARK}" font-weight="bold" letter-spacing="0.8">MODEL SYSTEMS</text>

  <!-- Tag 3: DEVELOPER TOOLING -->
  <rect x="352" y="295" width="160" height="26" rx="13" fill="#eff3f9" stroke="#cbdcf0" stroke-width="1.2"/>
  <circle cx="370" cy="308" r="4.5" fill="#5b86e5"/>
  <text x="381" y="312" class="mono" font-size="10" fill="{TEXT_DARK}" font-weight="bold" letter-spacing="0.8">DEVELOPER TOOLING</text>

  <!-- ── 4 Stats Columns ── -->
  <!-- Stat 1: Own repos -->
  <text x="50" y="375" class="heading" font-size="38" fill="{TEXT_DARK}">{own_repos}</text>
  <text x="50" y="394" class="mono" font-size="9.5" fill="{TEAL}" letter-spacing="0.8" font-weight="bold">ORIGINAL SYSTEMS</text>
  <text x="50" y="408" class="subheading" font-size="9.5" fill="{TEXT_MID}">自有开放项目</text>

  <!-- Stat 2: Stars -->
  <text x="188" y="375" class="heading" font-size="38" fill="{TEXT_DARK}">{total_stars}</text>
  <text x="188" y="394" class="mono" font-size="9.5" fill="{TEAL}" letter-spacing="0.8" font-weight="bold">OWNED STARS</text>
  <text x="188" y="408" class="subheading" font-size="9.5" fill="{TEXT_MID}">自有项目星标</text>

  <!-- Stat 3: Followers -->
  <text x="340" y="375" class="heading" font-size="38" fill="{TEXT_DARK}">{followers}</text>
  <text x="340" y="394" class="mono" font-size="9.5" fill="{TEAL}" letter-spacing="0.8" font-weight="bold">FOLLOWERS</text>
  <text x="340" y="408" class="subheading" font-size="9.5" fill="{TEXT_MID}">关注者</text>

  <!-- Stat 4: Upstream PRs -->
  <text x="466" y="375" class="heading" font-size="38" fill="{TEXT_DARK}">{upstream_prs}</text>
  <text x="466" y="394" class="mono" font-size="9.5" fill="{TEAL}" letter-spacing="0.8" font-weight="bold">UPSTREAM PRS</text>
  <text x="466" y="408" class="subheading" font-size="9.5" fill="{TEXT_MID}">公开上游贡献</text>

  <!-- ── Footer Bar ── -->
  <text x="50" y="448" class="mono" font-size="10" fill="{TEAL}" letter-spacing="1.5" font-weight="bold">
    DESIGN → CONTRIBUTE → VERIFY → STEWARD
  </text>
  <text x="910" y="448" class="mono" font-size="10" fill="{TEAL}" letter-spacing="1.2" font-weight="bold" text-anchor="end">
    UPDATED {updated_at}
  </text>

  <!-- ── Animated Radar Chart (right) ── -->
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
