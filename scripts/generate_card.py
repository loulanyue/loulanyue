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


## ──────────────────────────────────────────────────────────────────────────────
# SVG rendering (Cyberpunk Dark Mode)
# ──────────────────────────────────────────────────────────────────────────────

BG = "#03070d"
BORDER = "#0e1c28"
CYAN = "#00e5ff"
CYAN_GLOW = "#00f0ff"
EMERALD = "#00ff9d"
PURPLE = "#9d65ff"
TEXT_WHITE = "#ffffff"
TEXT_MUTED = "#7b919e"
TEXT_DARK_MUTED = "#455a68"
LINE_COLOR = "#122332"
W, H = 1024, 512


def fmt_number(n: int) -> str:
    """Format large numbers with commas."""
    return f"{n:,}"


def render_radar(cx: float, cy: float, r: float) -> str:
    """Render the animated cyber dark radar with rotating scan beam and detected targets."""
    parts = []

    # ── Concentric solid & dashed rings ──
    # Outer main circle
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
        f'stroke="{CYAN}" stroke-width="1.4" stroke-opacity="0.35"/>'
    )
    # Secondary outer boundary
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r * 0.96:.1f}" fill="none" '
        f'stroke="{CYAN}" stroke-width="0.6" stroke-opacity="0.15"/>'
    )

    # Intermediate rings
    rings = [
        (0.72, "solid", 0.6, 0.20),
        (0.48, "solid", 0.7, 0.25),
        (0.24, "solid", 0.8, 0.30),
    ]
    for frac, style, sw, op in rings:
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r * frac:.1f}" fill="none" '
            f'stroke="{CYAN}" stroke-width="{sw}" stroke-opacity="{op}"/>'
        )

    # ── Outer perimeter fine tick marks (every 5 degrees) ──
    for deg in range(0, 360, 5):
        angle_rad = math.radians(deg - 90)
        if deg % 90 == 0:
            tl, sw, op = 10, 1.4, 0.6
        elif deg % 30 == 0:
            tl, sw, op = 6, 0.8, 0.35
        else:
            tl, sw, op = 3, 0.5, 0.18
        x1 = cx + (r - tl) * math.cos(angle_rad)
        y1 = cy + (r - tl) * math.sin(angle_rad)
        x2 = cx + r * math.cos(angle_rad)
        y2 = cy + r * math.sin(angle_rad)
        parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{CYAN}" stroke-width="{sw}" stroke-opacity="{op}"/>'
        )

    # ── Axis Crosshairs ──
    gap = r * 0.12
    parts.append(f'<line x1="{cx - r:.1f}" y1="{cy}" x2="{cx - gap:.1f}" y2="{cy}" stroke="{CYAN}" stroke-width="0.8" stroke-opacity="0.25"/>')
    parts.append(f'<line x1="{cx + gap:.1f}" y1="{cy}" x2="{cx + r:.1f}" y2="{cy}" stroke="{CYAN}" stroke-width="0.8" stroke-opacity="0.25"/>')
    parts.append(f'<line x1="{cx}" y1="{cy - r:.1f}" x2="{cx}" y2="{cy - gap:.1f}" stroke="{CYAN}" stroke-width="0.8" stroke-opacity="0.25"/>')
    parts.append(f'<line x1="{cx}" y1="{cy + gap:.1f}" x2="{cx}" y2="{cy + r:.1f}" stroke="{CYAN}" stroke-width="0.8" stroke-opacity="0.25"/>')

    # ── Cardinal direction labels ──
    label_r = r + 15
    for label, deg in [("N 000°", 0), ("E 090°", 90), ("S 180°", 180), ("W 270°", 270)]:
        angle_rad = math.radians(deg - 90)
        lx = cx + label_r * math.cos(angle_rad)
        ly = cy + label_r * math.sin(angle_rad)
        anchor = "middle"
        if deg == 0:
            ly -= 2
        elif deg == 180:
            ly += 9
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
            f'fill="{CYAN}" font-weight="bold" text-anchor="{anchor}" opacity="0.9">{label}</text>'
        )

    # ── Animated rotating radar sweep sector (clockwise) ──
    def pt(deg_offset: float) -> tuple[float, float]:
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
        f'    <path d="{w1}" fill="{CYAN}" fill-opacity="0.30"/>\n'
        f'    <path d="{w2}" fill="{CYAN}" fill-opacity="0.16"/>\n'
        f'    <path d="{w3}" fill="{CYAN}" fill-opacity="0.08"/>\n'
        f'    <path d="{w4}" fill="{CYAN}" fill-opacity="0.02"/>\n'
        f'    <line x1="0" y1="{-r * 0.1:.1f}" x2="0" y2="{-r:.1f}" '
        f'stroke="{CYAN_GLOW}" stroke-width="2" stroke-opacity="0.95" filter="url(#glow)"/>\n'
        f'    <circle cx="0" cy="{-r:.1f}" r="2.5" fill="{CYAN_GLOW}"/>\n'
        f'  </g>\n'
        f'</g>'
    )
    parts.append(sweep_group)

    # ── Detected Targets / Blips on Radar ──
    # 1. MCP / TOOL (Northwest)
    mcp_x, mcp_y = cx - 85, cy - 65
    parts.append(
        f'<g>\n'
        f'  <circle cx="{mcp_x}" cy="{mcp_y}" r="4" fill="{CYAN}" filter="url(#glow)"/>\n'
        f'  <text x="{mcp_x}" y="{mcp_y + 16}" font-family="monospace" font-size="8" '
        f'fill="{CYAN}" text-anchor="middle" font-weight="bold" opacity="0.9">MCP / TOOL</text>\n'
        f'</g>'
    )

    # 2. HERMES (Northeast)
    hermes_x, hermes_y = cx + 80, cy - 80
    parts.append(
        f'<g>\n'
        f'  <circle cx="{hermes_x}" cy="{hermes_y}" r="4" fill="{EMERALD}" filter="url(#glow)"/>\n'
        f'  <text x="{hermes_x}" y="{hermes_y + 16}" font-family="monospace" font-size="8" '
        f'fill="{EMERALD}" text-anchor="middle" font-weight="bold" opacity="0.9">HERMES</text>\n'
        f'</g>'
    )

    # 3. 100K+ (Southeast)
    k_x, k_y = cx + 96, cy + 68
    parts.append(
        f'<g>\n'
        f'  <circle cx="{k_x}" cy="{k_y}" r="4" fill="{PURPLE}" filter="url(#glow)"/>\n'
        f'  <text x="{k_x}" y="{k_y + 16}" font-family="monospace" font-size="8" '
        f'fill="{PURPLE}" text-anchor="middle" font-weight="bold" opacity="0.9">100K+</text>\n'
        f'</g>'
    )

    # ── Radar Center Hub with Pulse Wave ──
    # Center outer ring
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="16" fill="{BG}" '
        f'stroke="{CYAN}" stroke-width="1.6" stroke-opacity="0.8"/>'
    )
    # Center solid glowing core
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="6.5" fill="{CYAN_GLOW}" filter="url(#glow)"/>'
    )
    # Expanding pulse wave
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="6" fill="none" stroke="{CYAN}" stroke-width="1.8">'
        f'<animate attributeName="r" values="6;{r * 0.28:.1f};6" dur="2.4s" repeatCount="indefinite"/>'
        f'<animate attributeName="stroke-opacity" values="0.85;0;0.85" dur="2.4s" repeatCount="indefinite"/>'
        f'</circle>'
    )

    # ── LIVE SCAN badge at bottom ──
    badge_y = cy + r + 26
    bw, bh = 76, 20
    bx = cx - (bw / 2)
    parts.append(
        f'<rect x="{bx:.1f}" y="{badge_y - bh/2:.1f}" width="{bw}" height="{bh}" rx="10" '
        f'fill="#05141d" stroke="{CYAN}" stroke-width="0.9" stroke-opacity="0.6"/>'
    )
    # Blinking green beacon
    parts.append(
        f'<circle cx="{bx + 14:.1f}" cy="{badge_y:.1f}" r="3.5" fill="{EMERALD}" filter="url(#glow)">'
        f'<animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite"/>'
        f'</circle>'
    )
    parts.append(
        f'<text x="{bx + 24:.1f}" y="{badge_y + 3.5:.1f}" font-family="monospace" font-size="8.5" '
        f'fill="{CYAN}" font-weight="bold" opacity="0.95">LIVE SCAN</text>'
    )

    return "\n".join(parts)


def render_svg(stats: dict) -> str:
    own_repos = fmt_number(stats["own_repos"])
    total_stars = fmt_number(stats["total_stars"])
    followers = fmt_number(stats["followers"])
    upstream_prs = fmt_number(stats["upstream_prs"])
    updated_at = stats["updated_at"]

    # Radar center & radius
    radar_cx = 785.0
    radar_cy = 245.0
    radar_r = 160.0

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
    <!-- Glow filter for cyber neon elements -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Card background -->
  <rect width="{W}" height="{H}" fill="{BG}"/>

  <!-- ── Top Status Header ── -->
  <text x="35" y="52" class="mono" font-size="11" font-weight="bold" letter-spacing="1">
    <tspan fill="{CYAN}">OPEN-SOURCE SYSTEMS</tspan>
    <tspan fill="{CYAN}"> ENGINEER</tspan>
    <tspan fill="#324956"> ── </tspan>
    <tspan fill="#526a7a">LOUISVILLE, KY</tspan>
  </text>
  <!-- Underline under OPEN-SOURCE SYSTEMS -->
  <line x1="35" y1="58" x2="195" y2="58" stroke="{CYAN}" stroke-width="1.6"/>

  <!-- ── Big Brand Name ── -->
  <text x="35" y="148" class="heading" font-size="70" fill="{TEXT_WHITE}" letter-spacing="2.5">LOULANYUE</text>

  <!-- ── Chinese Philosophy Subtitle ── -->
  <text x="35" y="198" class="subheading" font-size="16" fill="{TEXT_WHITE}" font-weight="700" letter-spacing="0.5">
    以开放系统工程推动智能体基础设施走向可验证、可组合与可持续演进
  </text>

  <!-- ── English Subtitle ── -->
  <text x="35" y="234" class="body-eng" font-size="13" fill="{TEXT_MUTED}" letter-spacing="0.2">
    Advancing agentic infrastructure through open systems engineered for verification, composability, and long-term
  </text>
  <text x="35" y="254" class="body-eng" font-size="13" fill="{TEXT_MUTED}" letter-spacing="0.2">
    evolution.
  </text>

  <!-- ── Section Label ── -->
  <text x="35" y="304" class="mono" font-size="10.5" font-weight="bold" letter-spacing="1.2">
    <tspan fill="{CYAN}">ENGINEERING SURFACE</tspan>
    <tspan fill="{TEXT_DARK_MUTED}"> / 工程领域</tspan>
  </text>

  <!-- ── Tags Row ── -->
  <!-- Tag 1: AGENT RUNTIMES -->
  <rect x="35" y="318" width="144" height="26" rx="13" fill="#061622" stroke="#102f45" stroke-width="1.2"/>
  <circle cx="53" cy="331" r="4.5" fill="{CYAN}" filter="url(#glow)"/>
  <text x="64" y="335" class="mono" font-size="9.5" fill="#95c5dc" font-weight="bold" letter-spacing="0.8">AGENT RUNTIMES</text>

  <!-- Tag 2: MODEL SYSTEMS -->
  <rect x="189" y="318" width="138" height="26" rx="13" fill="#051918" stroke="#0e372e" stroke-width="1.2"/>
  <circle cx="207" cy="331" r="4.5" fill="{EMERALD}" filter="url(#glow)"/>
  <text x="218" y="335" class="mono" font-size="9.5" fill="#98dcc0" font-weight="bold" letter-spacing="0.8">MODEL SYSTEMS</text>

  <!-- Tag 3: DEVELOPER TOOLING -->
  <rect x="337" y="318" width="160" height="26" rx="13" fill="#131028" stroke="#2c2255" stroke-width="1.2"/>
  <circle cx="355" cy="331" r="4.5" fill="{PURPLE}" filter="url(#glow)"/>
  <text x="366" y="335" class="mono" font-size="9.5" fill="#c3b5ec" font-weight="bold" letter-spacing="0.8">DEVELOPER TOOLING</text>

  <!-- ── Divider Line above stats ── -->
  <line x1="35" y1="388" x2="550" y2="388" stroke="{LINE_COLOR}" stroke-width="1"/>

  <!-- ── 4 Stats Columns ── -->
  <!-- Stat 1: Own repos -->
  <text x="35" y="425" class="heading" font-size="38" fill="{TEXT_WHITE}">{own_repos}</text>
  <text x="35" y="444" class="mono" font-size="9.5" fill="{CYAN}" letter-spacing="0.8" font-weight="bold">ORIGINAL SYSTEMS</text>
  <text x="35" y="458" class="subheading" font-size="9.5" fill="{TEXT_DARK_MUTED}">自有开放项目</text>

  <!-- Stat 2: Stars -->
  <text x="175" y="425" class="heading" font-size="38" fill="{TEXT_WHITE}">{total_stars}</text>
  <text x="175" y="444" class="mono" font-size="9.5" fill="{CYAN}" letter-spacing="0.8" font-weight="bold">OWNED STARS</text>
  <text x="175" y="458" class="subheading" font-size="9.5" fill="{TEXT_DARK_MUTED}">自有项目星标</text>

  <!-- Stat 3: Followers -->
  <text x="315" y="425" class="heading" font-size="38" fill="{TEXT_WHITE}">{followers}</text>
  <text x="315" y="444" class="mono" font-size="9.5" fill="{CYAN}" letter-spacing="0.8" font-weight="bold">FOLLOWERS</text>
  <text x="315" y="458" class="subheading" font-size="9.5" fill="{TEXT_DARK_MUTED}">关注者</text>

  <!-- Stat 4: Upstream PRs -->
  <text x="445" y="425" class="heading" font-size="38" fill="{TEXT_WHITE}">{upstream_prs}</text>
  <text x="445" y="444" class="mono" font-size="9.5" fill="{CYAN}" letter-spacing="0.8" font-weight="bold">UPSTREAM PRS</text>
  <text x="445" y="458" class="subheading" font-size="9.5" fill="{TEXT_DARK_MUTED}">公开上游贡献</text>

  <!-- ── Footer Bar ── -->
  <text x="35" y="492" class="mono" font-size="10" fill="{CYAN}" letter-spacing="1.5" font-weight="bold">
    DESIGN  →  CONTRIBUTE  →  VERIFY  →  STEWARD
  </text>
  <text x="965" y="492" class="mono" font-size="10" fill="#4d6474" letter-spacing="1" font-weight="bold" text-anchor="end">
    UPDATED {updated_at}
  </text>

  <!-- ── Animated Cyber Radar (right) ── -->
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
