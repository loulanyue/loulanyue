#!/usr/bin/env python3
"""
Generate the loulanyue GitHub profile SVG card (Keynote Aligned Edition).

Usage:
    python scripts/generate_card.py --token $GITHUB_TOKEN --output profile-card.svg

Fetches live data from GitHub API and renders the full card SVG including:
  - Original public repos count
  - Total owned stars
  - Followers
  - Upstream PRs (public contributions)
  - Radar chart (capability signal)
  - Update timestamp
Visually harmonized with hero-keynote.svg (1200px width, cosmic obsidian, frosted glass, PCB traces).
"""

import argparse
import json
import math
import os
import random
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
        "User-Agent": "loulanyue-profile-card/2.0",
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
# SVG rendering (Keynote-Harmonized Cosmic Cyberpunk)
# ──────────────────────────────────────────────────────────────────────────────

W, H = 1200, 540
BG = "#020408"
CYAN = "#00e5ff"
CYAN_GLOW = "#00f0ff"
EMERALD = "#00ff9d"
PURPLE = "#9d65ff"
GOLD = "#e5b358"
WHITE = "#ffffff"
TEXT_WHITE = "#ffffff"
TEXT_MUTED = "#759cb8"
TEXT_DARK_MUTED = "#527593"
DARK_GLASS = "#050c16"
BORDER = "#14293d"
LINE_COLOR = "#18364e"


def fmt_number(n: int) -> str:
    """Format large numbers with commas."""
    return f"{n:,}"


def generate_stars(count: int = 75) -> str:
    """Generate subtle twinkling starlight dust across the card canvas."""
    random.seed(88)
    stars = []
    for _ in range(count):
        sx = random.randint(20, W - 20)
        sy = random.randint(20, H - 20)
        sr = round(random.uniform(0.5, 1.4), 1)
        sop = round(random.uniform(0.12, 0.60), 2)
        dur = round(random.uniform(2.6, 5.2), 1)
        stars.append(
            f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="#a8cce8" opacity="{sop}">'
            f'<animate attributeName="opacity" values="{sop};{min(sop+0.35, 0.95):.2f};{sop}" '
            f'dur="{dur}s" repeatCount="indefinite"/>'
            f'</circle>'
        )
    return "\n".join(stars)


def generate_card_circuit() -> str:
    """
    Generate interconnecting PCB copper traces bridging the content area with the radar.
    Features traveling electric energy pulses and solder terminals matching keynote stage.
    """
    paths = [
        # (path_data, length_approx, delay)
        # Trace 1: From engineering section top across toward radar northwest
        ("M 530,296 L 680,296 L 720,250 L 765,250", 250, "0.1s"),
        # Trace 2: From badges area down & across toward radar southwest
        ("M 550,332 L 670,332 L 720,380 L 780,380 L 805,355", 280, "0.7s"),
        # Trace 3: From stats divider line extending towards radar
        ("M 700,362 L 740,362 L 775,320 L 795,320", 160, "1.4s"),
        # Trace 4: Subtle top trace near Louisville status
        ("M 380,52 L 460,52 L 490,25 L 620,25 L 650,52 L 740,52", 400, "0.4s"),
        # Trace 5: Trace under stats flowing to corner
        ("M 690,440 L 730,440 L 760,470 L 820,470", 170, "1.0s"),
    ]
    parts = []
    # Base circuit lines
    for p, _, _ in paths:
        parts.append(
            f'<path d="{p}" fill="none" stroke="{LINE_COLOR}" stroke-width="1.3" stroke-linecap="round"/>'
        )

    # Animated traveling energy pulse lines
    for p, length, delay in paths:
        parts.append(
            f'<path d="{p}" fill="none" stroke="{CYAN}" stroke-width="2.0" '
            f'stroke-dasharray="14,{length}" stroke-linecap="round" filter="url(#glow)">'
            f'<animate attributeName="stroke-dashoffset" from="{length}" to="0" '
            f'dur="2.5s" begin="{delay}" repeatCount="indefinite"/>'
            f'</path>'
        )

    # Solder pads / terminal nodes
    terminals = [
        (765, 250), (805, 355), (795, 320), (820, 470),
        (530, 296), (720, 250), (670, 332), (720, 380),
        (740, 362), (460, 52), (490, 25), (620, 25), (650, 52), (740, 52)
    ]
    for tx, ty in terminals:
        parts.append(
            f'<circle cx="{tx}" cy="{ty}" r="2.6" fill="#040d18" stroke="#3f7294" stroke-width="1.1"/>'
            f'<circle cx="{tx}" cy="{ty}" r="1.1" fill="{CYAN}"/>'
        )

    return "\n".join(parts)


def render_badges() -> str:
    """Render 3 frosted dark-glass micro-badges for Engineering Surface."""
    badges_info = [
        (48, 312, 148, "AGENT RUNTIMES", CYAN, "#95c5dc"),
        (210, 312, 142, "MODEL SYSTEMS", EMERALD, "#98dcc0"),
        (366, 312, 168, "DEVELOPER TOOLING", PURPLE, "#c3b5ec"),
    ]
    parts = []
    for bx, by, bw, label, dot_col, text_col in badges_info:
        parts.append(f"""
    <!-- Badge: {label} -->
    <g>
      <rect x="{bx}" y="{by}" width="{bw}" height="28" rx="6" fill="{DARK_GLASS}"
            stroke="#1b3b55" stroke-width="1.2"/>
      <rect x="{bx + 2}" y="{by + 2}" width="{bw - 4}" height="24" rx="4" fill="none"
            stroke="#21405c" stroke-width="0.7" opacity="0.6"/>
      <circle cx="{bx + 14}" cy="{by + 14}" r="3.5" fill="{dot_col}" filter="url(#glow)">
        <animate attributeName="opacity" values="0.75;1;0.75" dur="2.0s" repeatCount="indefinite"/>
      </circle>
      <text x="{bx + 26}" y="{by + 17.5}" class="mono" font-size="9" fill="{text_col}"
            font-weight="bold" letter-spacing="0.8">{label}</text>
    </g>""")
    return "\n".join(parts)


def render_radar(cx: float, cy: float, r: float) -> str:
    """Render the animated cyber dark radar with rotating scan beam and detected targets."""
    parts = []

    # ── Concentric solid & dashed rings ──
    # Outer main circle
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
        f'stroke="{WHITE}" stroke-width="1.4" stroke-opacity="0.4" filter="url(#glow)"/>'
    )
    # Secondary outer boundary
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r * 0.96:.1f}" fill="none" '
        f'stroke="{CYAN}" stroke-width="0.8" stroke-opacity="0.25"/>'
    )

    # Intermediate rings
    rings = [
        (0.72, "solid", 0.7, 0.22),
        (0.48, "solid", 0.8, 0.28),
        (0.24, "solid", 0.9, 0.32),
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
            tl, sw, op = 10, 1.4, 0.7
        elif deg % 30 == 0:
            tl, sw, op = 6, 0.8, 0.4
        else:
            tl, sw, op = 3, 0.5, 0.2
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
    parts.append(f'<line x1="{cx - r:.1f}" y1="{cy}" x2="{cx - gap:.1f}" y2="{cy}" stroke="{WHITE}" stroke-width="0.8" stroke-opacity="0.3"/>')
    parts.append(f'<line x1="{cx + gap:.1f}" y1="{cy}" x2="{cx + r:.1f}" y2="{cy}" stroke="{WHITE}" stroke-width="0.8" stroke-opacity="0.3"/>')
    parts.append(f'<line x1="{cx}" y1="{cy - r:.1f}" x2="{cx}" y2="{cy - gap:.1f}" stroke="{WHITE}" stroke-width="0.8" stroke-opacity="0.3"/>')
    parts.append(f'<line x1="{cx}" y1="{cy + gap:.1f}" x2="{cx}" y2="{cy + r:.1f}" stroke="{WHITE}" stroke-width="0.8" stroke-opacity="0.3"/>')

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
            ly += 9
        elif deg == 90:
            anchor = "start"
            lx += 4
            ly += 3
        elif deg == 270:
            anchor = "end"
            lx -= 4
            ly += 3
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" font-family="monospace" font-size="8.5" '
            f'fill="{CYAN}" font-weight="bold" text-anchor="{anchor}" opacity="0.95">{label}</text>'
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
        f'    <path d="{w1}" fill="{CYAN}" fill-opacity="0.28"/>\n'
        f'    <path d="{w2}" fill="{CYAN}" fill-opacity="0.15"/>\n'
        f'    <path d="{w3}" fill="{CYAN}" fill-opacity="0.07"/>\n'
        f'    <path d="{w4}" fill="{CYAN}" fill-opacity="0.02"/>\n'
        f'    <line x1="0" y1="{-r * 0.1:.1f}" x2="0" y2="{-r:.1f}" '
        f'stroke="{WHITE}" stroke-width="2" stroke-opacity="0.95" filter="url(#glow)"/>\n'
        f'    <circle cx="0" cy="{-r:.1f}" r="2.8" fill="{WHITE}" filter="url(#glow)"/>\n'
        f'  </g>\n'
        f'</g>'
    )
    parts.append(sweep_group)

    # ── Detected Targets / Blips on Radar ──
    # 1. MCP / TOOL (Northwest)
    mcp_x, mcp_y = cx - 88, cy - 68
    parts.append(
        f'<g>\n'
        f'  <circle cx="{mcp_x}" cy="{mcp_y}" r="4" fill="{CYAN}" filter="url(#glow)"/>\n'
        f'  <circle cx="{mcp_x}" cy="{mcp_y}" r="8" fill="none" stroke="{CYAN}" stroke-width="0.8" opacity="0.6">\n'
        f'    <animate attributeName="r" values="4;12;4" dur="2.2s" repeatCount="indefinite"/>\n'
        f'    <animate attributeName="opacity" values="0.8;0.1;0.8" dur="2.2s" repeatCount="indefinite"/>\n'
        f'  </circle>\n'
        f'  <text x="{mcp_x}" y="{mcp_y + 16}" font-family="monospace" font-size="8" '
        f'fill="{CYAN}" text-anchor="middle" font-weight="bold" opacity="0.95">MCP / TOOL</text>\n'
        f'</g>'
    )

    # 2. HERMES (Northeast)
    hermes_x, hermes_y = cx + 82, cy - 82
    parts.append(
        f'<g>\n'
        f'  <circle cx="{hermes_x}" cy="{hermes_y}" r="4" fill="{EMERALD}" filter="url(#glow)"/>\n'
        f'  <circle cx="{hermes_x}" cy="{hermes_y}" r="8" fill="none" stroke="{EMERALD}" stroke-width="0.8" opacity="0.6">\n'
        f'    <animate attributeName="r" values="4;12;4" dur="2.5s" begin="0.4s" repeatCount="indefinite"/>\n'
        f'    <animate attributeName="opacity" values="0.8;0.1;0.8" dur="2.5s" begin="0.4s" repeatCount="indefinite"/>\n'
        f'  </circle>\n'
        f'  <text x="{hermes_x}" y="{hermes_y + 16}" font-family="monospace" font-size="8" '
        f'fill="{EMERALD}" text-anchor="middle" font-weight="bold" opacity="0.95">HERMES</text>\n'
        f'</g>'
    )

    # 3. 100K+ (Southeast)
    k_x, k_y = cx + 98, cy + 70
    parts.append(
        f'<g>\n'
        f'  <circle cx="{k_x}" cy="{k_y}" r="4" fill="{PURPLE}" filter="url(#glow)"/>\n'
        f'  <circle cx="{k_x}" cy="{k_y}" r="8" fill="none" stroke="{PURPLE}" stroke-width="0.8" opacity="0.6">\n'
        f'    <animate attributeName="r" values="4;12;4" dur="2.8s" begin="0.8s" repeatCount="indefinite"/>\n'
        f'    <animate attributeName="opacity" values="0.8;0.1;0.8" dur="2.8s" begin="0.8s" repeatCount="indefinite"/>\n'
        f'  </circle>\n'
        f'  <text x="{k_x}" y="{k_y + 16}" font-family="monospace" font-size="8" '
        f'fill="{PURPLE}" text-anchor="middle" font-weight="bold" opacity="0.95">100K+</text>\n'
        f'</g>'
    )

    # ── Radar Center Hub with Pulse Wave ──
    # Center outer ring
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="16" fill="{DARK_GLASS}" '
        f'stroke="{WHITE}" stroke-width="1.6" stroke-opacity="0.8" filter="url(#glow)"/>'
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

    # ── LIVE SCAN badge at bottom (Keynote Frosted Glass Edition) ──
    badge_y = cy + r + 30
    bw, bh = 88, 22
    bx = cx - (bw / 2)
    parts.append(
        f'<rect x="{bx:.1f}" y="{badge_y - bh/2:.1f}" width="{bw}" height="{bh}" rx="6" '
        f'fill="{DARK_GLASS}" stroke="#1b3952" stroke-width="1.2"/>'
    )
    parts.append(
        f'<rect x="{bx + 2:.1f}" y="{badge_y - bh/2 + 2:.1f}" width="{bw - 4}" height="{bh - 4}" rx="4" '
        f'fill="none" stroke="#21405c" stroke-width="0.7" opacity="0.6"/>'
    )
    # Blinking green beacon
    parts.append(
        f'<circle cx="{bx + 14:.1f}" cy="{badge_y:.1f}" r="3.5" fill="{EMERALD}" filter="url(#glow)">'
        f'<animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite"/>'
        f'</circle>'
    )
    parts.append(
        f'<text x="{bx + 25:.1f}" y="{badge_y + 3.5:.1f}" font-family="monospace" font-size="8.5" '
        f'fill="{CYAN}" font-weight="bold" opacity="0.95" letter-spacing="1">LIVE SCAN</text>'
    )

    return "\n".join(parts)


def render_particles() -> str:
    """Render ambient floating cyber particles with multi-directional random vectors."""
    particles_data = [
        # (cx, cy, r, color, glow, (dx1, dy1, dx2, dy2), dur, op_vals)
        # Top-left region (Header / title / brand)
        (115, 36, 1.4, CYAN, True, (16, -18, 8, -28), 6.5, "0.2;0.8;0.3;0.9;0.2"),
        (260, 85, 2.0, CYAN_GLOW, True, (-20, -15, -35, -8), 7.2, "0.15;0.7;0.2;0.85;0.15"),
        (430, 42, 1.2, TEXT_WHITE, False, (22, 18, 38, 28), 8.1, "0.2;0.9;0.1;0.75;0.2"),
        (480, 110, 1.8, EMERALD, True, (-18, 20, -28, 35), 6.8, "0.1;0.8;0.4;0.9;0.1"),

        # Mid-left region (Subtitles & tags)
        (580, 175, 2.0, CYAN, True, (28, -14, 45, -6), 7.5, "0.2;0.95;0.3;0.8;0.2"),
        (620, 225, 1.5, PURPLE, True, (-25, 15, -42, 8), 8.6, "0.15;0.75;0.2;0.9;0.15"),
        (520, 275, 1.8, EMERALD, True, (15, 24, 25, 42), 6.2, "0.3;0.9;0.2;0.85;0.3"),

        # Bottom-left stats area
        (120, 470, 1.5, CYAN, False, (20, -18, 35, -28), 7.4, "0.2;0.85;0.3;0.7;0.2"),
        (310, 490, 2.2, EMERALD, True, (-24, -16, -40, -10), 8.4, "0.15;0.8;0.2;0.95;0.15"),
        (490, 480, 1.3, TEXT_WHITE, False, (18, 22, 32, 36), 6.6, "0.3;0.75;0.2;0.85;0.3"),

        # Periphery of Radar chart
        (750, 95, 2.2, CYAN, True, (25, -20, 42, -12), 8.2, "0.2;0.95;0.35;0.85;0.2"),
        (1130, 85, 1.6, TEXT_WHITE, False, (-15, 25, -25, 45), 7.0, "0.15;0.7;0.3;0.9;0.15"),
        (1150, 215, 1.8, CYAN_GLOW, True, (-30, 14, -55, 6), 6.4, "0.3;0.9;0.2;0.8;0.3"),
        (1140, 420, 2.0, PURPLE, True, (-18, 24, -32, 40), 9.2, "0.1;0.8;0.3;0.95;0.1"),
    ]

    parts = [
        '  <!-- ── Animated Multi-Directional Ambient Particles ── -->',
        '  <g id="ambient-particles" clip-path="url(#card-clip)">',
    ]
    for cx, cy, r, col, glow, (dx1, dy1, dx2, dy2), dur, op in particles_data:
        glow_attr = ' filter="url(#glow)"' if glow else ''
        parts.append(
            f'    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" opacity="0.3"{glow_attr}>\n'
            f'      <animateTransform attributeName="transform" type="translate"\n'
            f'        values="0,0; {dx1},{dy1}; {dx2},{dy2}; 0,0"\n'
            f'        keyTimes="0; 0.45; 0.8; 1"\n'
            f'        dur="{dur}s" repeatCount="indefinite"/>\n'
            f'      <animate attributeName="opacity"\n'
            f'        values="{op}"\n'
            f'        dur="{dur}s" repeatCount="indefinite"/>\n'
            f'    </circle>'
        )
    parts.append('  </g>')
    return "\n".join(parts)


def render_corner_rails() -> str:
    """Render stepped keynote neon rails on bottom corners for visual balance with hero."""
    parts = []
    # Bottom-right stepped rails near updated timestamp
    rails = [
        "M 1170,528 L 1135,528 L 1120,516 L 1070,516",
        "M 1160,520 L 1130,520 L 1115,508 L 1075,508",
    ]
    for r in rails:
        parts.append(
            f'<path d="{r}" fill="none" stroke="{WHITE}" stroke-width="1.2" stroke-opacity="0.7" filter="url(#glow)"/>'
        )
    return "\n".join(parts)


def render_svg(stats: dict) -> str:
    own_repos = fmt_number(stats["own_repos"])
    total_stars = fmt_number(stats["total_stars"])
    followers = fmt_number(stats["followers"])
    upstream_prs = fmt_number(stats["upstream_prs"])
    updated_at = stats["updated_at"]

    # Radar center & radius (optimized for 1200px canvas)
    radar_cx = 940.0
    radar_cy = 255.0
    radar_r = 165.0

    radar_svg = render_radar(radar_cx, radar_cy, radar_r)
    particles_svg = render_particles()
    stars_svg = generate_stars(75)
    circuit_svg = generate_card_circuit()
    badges_svg = render_badges()
    corner_rails_svg = render_corner_rails()

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700;900&amp;family=Noto+Sans+SC:wght@500;700;900&amp;display=swap');
      .heading {{ font-family: 'Space Grotesk', -apple-system, sans-serif; font-weight: 900; }}
      .subheading {{ font-family: 'Noto Sans SC', 'PingFang SC', sans-serif; }}
      .body-eng {{ font-family: 'Space Grotesk', -apple-system, sans-serif; font-weight: 500; }}
      .mono {{ font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace; }}
    </style>

    <!-- Keynote Glow Filter -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3.2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Card Clip Boundary -->
    <clipPath id="card-clip">
      <rect width="{W}" height="{H}" rx="14"/>
    </clipPath>

    <!-- Subtle Radar Ambient Spotlight -->
    <radialGradient id="radar-spotlight" cx="78%" cy="47%" r="48%">
      <stop offset="0%" stop-color="#0c2338" stop-opacity="0.60"/>
      <stop offset="60%" stop-color="#05121e" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="{BG}" stop-opacity="0"/>
    </radialGradient>

    <!-- Brand Header Ambient Spotlight -->
    <radialGradient id="brand-spotlight" cx="22%" cy="30%" r="45%">
      <stop offset="0%" stop-color="#081a2b" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="{BG}" stop-opacity="0"/>
    </radialGradient>

    <!-- Faint Keynote Cyber Grid -->
    <pattern id="cyber-grid" width="36" height="36" patternUnits="userSpaceOnUse">
      <path d="M 36 0 L 0 0 0 36" fill="none" stroke="#0a1a24" stroke-width="0.75" stroke-opacity="0.4"/>
      <circle cx="36" cy="36" r="0.75" fill="{CYAN}" fill-opacity="0.2"/>
    </pattern>

    <!-- Horizon Line Gradient -->
    <linearGradient id="horizon-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{CYAN}" stop-opacity="0"/>
      <stop offset="15%" stop-color="{CYAN}" stop-opacity="0.8"/>
      <stop offset="50%" stop-color="{WHITE}" stop-opacity="1"/>
      <stop offset="85%" stop-color="{CYAN}" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="{CYAN}" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <!-- ── Background Layers ── -->
  <rect width="{W}" height="{H}" rx="14" fill="{BG}"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#cyber-grid)"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#brand-spotlight)"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#radar-spotlight)"/>

  <!-- ── Starfield Dust (Keynote Synchronized) ── -->
  <g clip-path="url(#card-clip)">
    {stars_svg}
  </g>

  <!-- ── PCB Circuit Traces & Energy Pulses ── -->
  <g id="circuit-traces" clip-path="url(#card-clip)">
    {circuit_svg}
  </g>

  <!-- ── Ambient Cyber Particles ── -->
  {particles_svg}

  <!-- ── Stepped Keynote Corner Rails ── -->
  {corner_rails_svg}

  <!-- ── Outer Card Frame Border ── -->
  <rect width="{W}" height="{H}" rx="14" fill="none" stroke="{BORDER}" stroke-width="1.2"/>

  <!-- ── Top Status Header ── -->
  <g>
    <!-- Cyan pulsing dot -->
    <circle cx="48" cy="48" r="3.5" fill="{CYAN}" filter="url(#glow)">
      <animate attributeName="opacity" values="0.4;1;0.4" dur="1.8s" repeatCount="indefinite"/>
    </circle>
    <text x="60" y="52" class="mono" font-size="11" font-weight="bold" letter-spacing="1.2">
      <tspan fill="{CYAN}">OPEN-SOURCE SYSTEMS</tspan>
      <tspan fill="{CYAN}"> ENGINEER</tspan>
      <tspan fill="#2d495d"> ── </tspan>
      <tspan fill="#688ca6">LOUISVILLE, KY</tspan>
    </text>
    <!-- Keynote Edition Badge on right of header -->
    <rect x="576" y="38" width="138" height="20" rx="4" fill="{DARK_GLASS}"
          stroke="#18364e" stroke-width="1"/>
    <text x="645" y="52" class="mono" font-size="8.5" fill="#759cb8" font-weight="bold"
          letter-spacing="1.2" text-anchor="middle">2026 KEYNOTE SYS</text>
    <!-- Underline under OPEN-SOURCE SYSTEMS -->
    <line x1="60" y1="58" x2="225" y2="58" stroke="{CYAN}" stroke-width="1.4" filter="url(#glow)"/>
  </g>

  <!-- ── Big Brand Name ── -->
  <text x="48" y="146" class="heading" font-size="70" fill="{TEXT_WHITE}" letter-spacing="3" filter="url(#glow)">LOULANYUE</text>

  <!-- ── Chinese Philosophy Subtitle ── -->
  <text x="48" y="194" class="subheading" font-size="16.5" fill="{TEXT_WHITE}" font-weight="700" letter-spacing="0.6">
    以开放系统工程推动智能体基础设施走向可验证、可组合与可持续演进
  </text>

  <!-- ── English Subtitle ── -->
  <text x="48" y="226" class="body-eng" font-size="13" fill="{TEXT_MUTED}" letter-spacing="0.2">
    Advancing agentic infrastructure through open systems engineered
  </text>
  <text x="48" y="247" class="body-eng" font-size="13" fill="{TEXT_MUTED}" letter-spacing="0.2">
    for verification, composability, and long-term evolution.
  </text>

  <!-- ── Section Label: Engineering Surface ── -->
  <text x="48" y="296" class="mono" font-size="10.5" font-weight="bold" letter-spacing="1.2">
    <tspan fill="{CYAN}">ENGINEERING SURFACE</tspan>
    <tspan fill="{TEXT_DARK_MUTED}"> / 工程领域</tspan>
  </text>

  <!-- ── Frosted Dark-Glass Badges ── -->
  {badges_svg}

  <!-- ── Keynote Stage Horizon Divider Line ── -->
  <line x1="48" y1="365" x2="714" y2="365" stroke="url(#horizon-grad)" stroke-width="1.6" filter="url(#glow)"/>
  <line x1="48" y1="368" x2="714" y2="368" stroke="#18364e" stroke-width="0.9" opacity="0.7"/>

  <!-- ── 4 Stats Columns (Precise Keynote Metrics) ── -->
  <!-- Stat 1: Own repos -->
  <text x="48" y="416" class="heading" font-size="38" fill="{TEXT_WHITE}" filter="url(#glow)">{own_repos}</text>
  <text x="48" y="436" class="mono" font-size="9.5" fill="{CYAN}" letter-spacing="0.8" font-weight="bold">ORIGINAL SYSTEMS</text>
  <text x="48" y="452" class="subheading" font-size="9.5" fill="{TEXT_DARK_MUTED}">自有开放项目</text>

  <!-- Stat 2: Stars -->
  <text x="215" y="416" class="heading" font-size="38" fill="{TEXT_WHITE}" filter="url(#glow)">{total_stars}</text>
  <text x="215" y="436" class="mono" font-size="9.5" fill="{CYAN}" letter-spacing="0.8" font-weight="bold">OWNED STARS</text>
  <text x="215" y="452" class="subheading" font-size="9.5" fill="{TEXT_DARK_MUTED}">自有项目星标</text>

  <!-- Stat 3: Followers -->
  <text x="382" y="416" class="heading" font-size="38" fill="{TEXT_WHITE}" filter="url(#glow)">{followers}</text>
  <text x="382" y="436" class="mono" font-size="9.5" fill="{CYAN}" letter-spacing="0.8" font-weight="bold">FOLLOWERS</text>
  <text x="382" y="452" class="subheading" font-size="9.5" fill="{TEXT_DARK_MUTED}">关注者</text>

  <!-- Stat 4: Upstream PRs -->
  <text x="548" y="416" class="heading" font-size="38" fill="{TEXT_WHITE}" filter="url(#glow)">{upstream_prs}</text>
  <text x="548" y="436" class="mono" font-size="9.5" fill="{CYAN}" letter-spacing="0.8" font-weight="bold">UPSTREAM PRS</text>
  <text x="548" y="452" class="subheading" font-size="9.5" fill="{TEXT_DARK_MUTED}">公开上游贡献</text>

  <!-- ── Footer Bar ── -->
  <text x="48" y="504" class="mono" font-size="10.5" fill="{CYAN}" letter-spacing="1.5" font-weight="bold">
    DESIGN  →  CONTRIBUTE  →  VERIFY  →  STEWARD
  </text>
  <text x="1152" y="504" class="mono" font-size="10" fill="#527593" letter-spacing="1.2" font-weight="bold" text-anchor="end">
    UPDATED {updated_at}
  </text>

  <!-- ── Animated Cyber Radar (Right Wing) ── -->
  {radar_svg}
</svg>"""

    return svg


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def extract_existing_stats(svg_path: str) -> dict:
    fallback = {
        "own_repos": 14,
        "total_stars": 2448,
        "followers": 158,
        "upstream_prs": 355,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d UTC"),
    }
    if not os.path.exists(svg_path):
        return fallback
    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            content = f.read()
        m_repos = re.search(r'class="heading"[^>]*>([\d,]+)</text>\s*<text[^>]*>ORIGINAL SYSTEMS', content)
        m_stars = re.search(r'class="heading"[^>]*>([\d,]+)</text>\s*<text[^>]*>OWNED STARS', content)
        m_followers = re.search(r'class="heading"[^>]*>([\d,]+)</text>\s*<text[^>]*>FOLLOWERS', content)
        m_prs = re.search(r'class="heading"[^>]*>([\d,]+)</text>\s*<text[^>]*>UPSTREAM PRS', content)
        m_updated = re.search(r'UPDATED\s+([^<\n]+)', content)
        if m_repos:
            fallback["own_repos"] = int(m_repos.group(1).replace(",", ""))
        if m_stars:
            fallback["total_stars"] = int(m_stars.group(1).replace(",", ""))
        if m_followers:
            fallback["followers"] = int(m_followers.group(1).replace(",", ""))
        if m_prs:
            fallback["upstream_prs"] = int(m_prs.group(1).replace(",", ""))
        if m_updated:
            fallback["updated_at"] = m_updated.group(1).strip()
    except Exception as e:
        print(f"Warning: could not parse existing stats from {svg_path}: {e}")
    return fallback


def main():
    parser = argparse.ArgumentParser(description="Generate loulanyue profile card SVG")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub personal access token")
    parser.add_argument("--output", default="profile-card.svg", help="Output SVG file path")
    args = parser.parse_args()

    if args.token:
        print(f"Fetching stats for @{USERNAME} from GitHub API...")
        try:
            stats = fetch_stats(args.token)
        except Exception as e:
            print(f"Error fetching stats from API: {e}, falling back to existing stats.")
            stats = extract_existing_stats(args.output)
    else:
        print("No token provided, using existing stats...")
        stats = extract_existing_stats(args.output)

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
