#!/usr/bin/env python3
"""
Generate the Cloud Keynote Architecture Hero SVG for loulanyue GitHub Profile.
Faithfully recreates the 2026 Hangzhou Apsara Conference keynote stage:
- "机器智能时代的基石 / Foundations of the Machine Intelligence Era"
- Three core pillars: "AI模型" | "AI芯片" | "AI云"
- Dual-wing PCB bus circuit traces with traveling electric pulses
- Conference stage horizon, stepped neon rails, and keynote banner
"""

import math
import random

W, H = 1200, 368
BG = "#020408"
CYAN = "#00e5ff"
CYAN_GLOW = "#00f0ff"
GOLD = "#e5b358"
WHITE = "#ffffff"
MUTED_BLUE = "#527593"
DARK_GLASS = "#050c16"
BORDER = "#14293d"


def generate_stars(count: int = 70) -> str:
    random.seed(42)
    stars = []
    for _ in range(count):
        sx = random.randint(15, W - 15)
        sy = random.randint(15, H - 15)
        sr = round(random.uniform(0.5, 1.4), 1)
        sop = round(random.uniform(0.15, 0.65), 2)
        dur = round(random.uniform(2.5, 5.0), 1)
        stars.append(
            f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="#a8cce8" opacity="{sop}">'
            f'<animate attributeName="opacity" values="{sop};{min(sop+0.35, 0.95):.2f};{sop}" '
            f'dur="{dur}s" repeatCount="indefinite"/>'
            f'</circle>'
        )
    return "\n".join(stars)


def generate_left_circuit() -> str:
    """Generate left-side PCB traces spreading outward from AI模型 block with pulse streams."""
    paths = [
        # (path_data, length_approx, delay)
        ("M 390,130 L 330,130 L 290,90 L 150,90 L 120,60 L 40,60", 420, "0s"),
        ("M 390,145 L 320,145 L 280,105 L 170,105 L 140,75 L 70,75", 380, "0.5s"),
        ("M 390,160 L 310,160 L 270,120 L 130,120 L 100,90 L 90,90", 350, "1.0s"),
        ("M 390,175 L 310,175 L 270,215 L 140,215 L 110,245 L 40,245", 410, "0.3s"),
        ("M 390,190 L 320,190 L 280,230 L 160,230 L 130,260 L 60,260", 390, "0.8s"),
        ("M 390,205 L 330,205 L 290,245 L 180,245 L 150,275 L 90,275", 360, "1.3s"),
    ]
    parts = []
    # Base circuit lines
    for p, _, _ in paths:
        parts.append(
            f'<path d="{p}" fill="none" stroke="#18364e" stroke-width="1.4" stroke-linecap="round"/>'
        )

    # Animated traveling energy pulse lines
    for p, length, delay in paths:
        parts.append(
            f'<path d="{p}" fill="none" stroke="{CYAN}" stroke-width="2.2" '
            f'stroke-dasharray="14,{length}" stroke-linecap="round" filter="url(#keynote-glow)">'
            f'<animate attributeName="stroke-dashoffset" from="{length}" to="0" dur="2.4s" begin="{delay}" repeatCount="indefinite"/>'
            f'</path>'
        )

    # Solder pads / terminal nodes
    terminals = [
        (40, 60), (70, 75), (90, 90),
        (40, 245), (60, 260), (90, 275),
        (150, 90), (170, 105), (140, 215), (160, 230),
        (290, 90), (280, 105), (270, 215), (280, 230)
    ]
    for tx, ty in terminals:
        parts.append(
            f'<circle cx="{tx}" cy="{ty}" r="2.8" fill="#040d18" stroke="#3f7294" stroke-width="1.2"/>'
            f'<circle cx="{tx}" cy="{ty}" r="1.2" fill="{CYAN}"/>'
        )

    return "\n".join(parts)


def generate_right_circuit() -> str:
    """Generate right-side PCB traces spreading outward from AI云 block with pulse streams."""
    paths = [
        # (path_data, length_approx, delay)
        ("M 810,130 L 870,130 L 910,90 L 1050,90 L 1080,60 L 1160,60", 420, "0.2s"),
        ("M 810,145 L 880,145 L 920,105 L 1030,105 L 1060,75 L 1130,75", 380, "0.7s"),
        ("M 810,160 L 890,160 L 930,120 L 1070,120 L 1100,90 L 1110,90", 350, "1.2s"),
        ("M 810,175 L 890,175 L 930,215 L 1060,215 L 1090,245 L 1160,245", 410, "0.4s"),
        ("M 810,190 L 880,190 L 920,230 L 1040,230 L 1070,260 L 1140,260", 390, "0.9s"),
        ("M 810,205 L 870,205 L 910,245 L 1020,245 L 1050,275 L 1110,275", 360, "1.4s"),
    ]
    parts = []
    # Base circuit lines
    for p, _, _ in paths:
        parts.append(
            f'<path d="{p}" fill="none" stroke="#18364e" stroke-width="1.4" stroke-linecap="round"/>'
        )

    # Animated traveling energy pulse lines
    for p, length, delay in paths:
        parts.append(
            f'<path d="{p}" fill="none" stroke="{CYAN}" stroke-width="2.2" '
            f'stroke-dasharray="14,{length}" stroke-linecap="round" filter="url(#keynote-glow)">'
            f'<animate attributeName="stroke-dashoffset" from="{length}" to="0" dur="2.4s" begin="{delay}" repeatCount="indefinite"/>'
            f'</path>'
        )

    # Solder pads / terminal nodes
    terminals = [
        (1160, 60), (1130, 75), (1110, 90),
        (1160, 245), (1140, 260), (1110, 275),
        (1050, 90), (1030, 105), (1060, 215), (1040, 230),
        (910, 90), (920, 105), (930, 215), (920, 230)
    ]
    for tx, ty in terminals:
        parts.append(
            f'<circle cx="{tx}" cy="{ty}" r="2.8" fill="#040d18" stroke="#3f7294" stroke-width="1.2"/>'
            f'<circle cx="{tx}" cy="{ty}" r="1.2" fill="{CYAN}"/>'
        )

    return "\n".join(parts)


def render_block(x: int, y: int, title: str, subtitle: str, active: bool = False) -> str:
    """Render a single keynote pillar card."""
    cx = x + 55
    border_color = WHITE
    glow_attr = 'filter="url(#keynote-glow)"'
    
    return f"""
    <!-- Pillar Block: {title} -->
    <g>
      <!-- Shadow and outer glow box -->
      <rect x="{x}" y="{y}" width="110" height="110" rx="9" fill="{DARK_GLASS}"
            stroke="{border_color}" stroke-width="1.8" {glow_attr}/>
      <!-- Inset highlight line -->
      <rect x="{x + 3}" y="{y + 3}" width="104" height="104" rx="7" fill="none"
            stroke="#21405c" stroke-width="0.8" opacity="0.6"/>
      <!-- Core Title -->
      <text x="{cx}" y="{y + 64}" font-family="'Space Grotesk', 'Noto Sans SC', sans-serif"
            font-size="22" font-weight="900" fill="{WHITE}" letter-spacing="1.5" text-anchor="middle">{title}</text>
      <!-- Subtitle badge -->
      <text x="{cx}" y="{y + 88}" font-family="monospace"
            font-size="7.5" font-weight="bold" fill="#7599b5" letter-spacing="1.2" text-anchor="middle">{subtitle}</text>
    </g>"""


def render_inter_links() -> str:
    """Data bus links between Block 1-2 and Block 2-3 with pulsing bus lines."""
    parts = []
    # Link 1: 500 to 545 (between Model and Chip)
    for ly in [145, 170, 195]:
        parts.append(f'<line x1="500" y1="{ly}" x2="545" y2="{ly}" stroke="#1e4462" stroke-width="1.4"/>')
        parts.append(
            f'<circle cx="522" cy="{ly}" r="2" fill="{CYAN}" opacity="0.9" filter="url(#keynote-glow)">'
            f'<animate attributeName="opacity" values="0.3;1;0.3" dur="1.8s" repeatCount="indefinite"/>'
            f'</circle>'
        )

    # Link 2: 655 to 700 (between Chip and Cloud)
    for ly in [145, 170, 195]:
        parts.append(f'<line x1="655" y1="{ly}" x2="700" y2="{ly}" stroke="#1e4462" stroke-width="1.4"/>')
        parts.append(
            f'<circle cx="678" cy="{ly}" r="2" fill="{CYAN}" opacity="0.9" filter="url(#keynote-glow)">'
            f'<animate attributeName="opacity" values="0.3;1;0.3" dur="1.8s" begin="0.9s" repeatCount="indefinite"/>'
            f'</circle>'
        )

    return "\n".join(parts)


def render_stage_rails() -> str:
    """Render the keynote stage horizon line and stepped neon wings."""
    parts = []
    
    # Center horizon line
    parts.append(
        f'<line x1="330" y1="288" x2="870" y2="288" stroke="{WHITE}" stroke-width="1.8" filter="url(#keynote-glow)"/>'
    )
    parts.append(
        f'<line x1="290" y1="292" x2="910" y2="292" stroke="#2a5375" stroke-width="1.0" opacity="0.8"/>'
    )

    # Presenter Silhouette standing in the center
    # Head
    parts.append('<circle cx="600" cy="265" r="3.2" fill="#ffffff" opacity="0.9"/>')
    # Body & Suit
    parts.append('<path d="M 596,270 L 604,270 L 602,286 L 598,286 Z" fill="#ffffff" opacity="0.85"/>')
    # Legs
    parts.append('<line x1="599" y1="286" x2="599" y2="292" stroke="#ffffff" stroke-width="1.2"/>')
    parts.append('<line x1="601" y1="286" x2="601" y2="292" stroke="#ffffff" stroke-width="1.2"/>')
    # Spotlight puddle under presenter
    parts.append('<ellipse cx="600" cy="293" rx="14" ry="2.5" fill="#00e5ff" opacity="0.4" filter="url(#keynote-glow)"/>')

    # Stepped neon lines - Left wing
    left_rails = [
        "M 26,355 L 75,355 L 92,342 L 175,342",
        "M 36,345 L 82,345 L 99,332 L 185,332",
        "M 48,335 L 90,335 L 107,322 L 195,322",
        "M 62,325 L 98,325 L 115,312 L 205,312",
    ]
    for r in left_rails:
        parts.append(f'<path d="{r}" fill="none" stroke="{WHITE}" stroke-width="1.5" stroke-opacity="0.9" filter="url(#keynote-glow)"/>')

    # Stepped neon lines - Right wing
    right_rails = [
        "M 1174,355 L 1125,355 L 1108,342 L 1025,342",
        "M 1164,345 L 1118,345 L 1101,332 L 1015,332",
        "M 1152,335 L 1110,335 L 1093,322 L 1005,322",
        "M 1138,325 L 1102,325 L 1085,312 L 995,312",
    ]
    for r in right_rails:
        parts.append(f'<path d="{r}" fill="none" stroke="{WHITE}" stroke-width="1.5" stroke-opacity="0.9" filter="url(#keynote-glow)"/>')

    # Conference Banner Text
    parts.append(
        f'<text x="600" y="328" font-family="\'Space Grotesk\', \'Noto Sans SC\', sans-serif" '
        f'font-size="21" font-weight="900" fill="{WHITE}" letter-spacing="4" text-anchor="middle">'
        f'2026 杭州 · 云栖大会'
        f'</text>'
    )
    parts.append(
        f'<text x="600" y="346" font-family="monospace" '
        f'font-size="8.5" font-weight="bold" fill="#6086a6" letter-spacing="2.2" text-anchor="middle">'
        f'HANGZHOU APSARA CONFERENCE · KEYNOTE ARCHITECTURE'
        f'</text>'
    )

    return "\n".join(parts)


def generate_hero_svg() -> str:
    stars_svg = generate_stars(80)
    left_circuit_svg = generate_left_circuit()
    right_circuit_svg = generate_right_circuit()
    inter_links_svg = render_inter_links()
    stage_rails_svg = render_stage_rails()

    # Blocks
    block1 = render_block(390, 115, "AI模型", "AGENT RUNTIMES")
    block2 = render_block(545, 115, "AI芯片", "SILICON ARCH")
    block3 = render_block(700, 115, "AI云", "CLOUD INFRA")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700;900&amp;family=Noto+Sans+SC:wght@500;700;900&amp;display=swap');
    </style>
    <!-- Glow filter for cyber neon and keynote highlights -->
    <filter id="keynote-glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Stage center spotlight -->
    <radialGradient id="stage-spotlight" cx="50%" cy="45%" r="55%">
      <stop offset="0%" stop-color="#0c2338" stop-opacity="0.75"/>
      <stop offset="50%" stop-color="#061320" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{BG}" stop-opacity="0"/>
    </radialGradient>

    <!-- Card clip -->
    <clipPath id="hero-clip">
      <rect width="{W}" height="{H}" rx="14"/>
    </clipPath>
  </defs>

  <!-- ── Background ── -->
  <rect width="{W}" height="{H}" rx="14" fill="{BG}"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#stage-spotlight)"/>

  <!-- Starfield Dust -->
  <g clip-path="url(#hero-clip)">
    {stars_svg}
  </g>

  <!-- ── Top Headline ── -->
  <text x="600" y="52" font-family="'Space Grotesk', 'Noto Sans SC', sans-serif"
        font-size="30" font-weight="900" fill="{WHITE}" letter-spacing="4" text-anchor="middle">
    机器智能时代的基石
  </text>
  <text x="600" y="78" font-family="'Space Grotesk', sans-serif"
        font-size="13.5" font-weight="500" fill="#759cb8" letter-spacing="1.5" text-anchor="middle">
    Foundations of the Machine Intelligence Era
  </text>

  <!-- ── Dual-wing PCB Bus Circuit Traces ── -->
  <g id="circuit-traces">
    {left_circuit_svg}
    {right_circuit_svg}
  </g>

  <!-- ── Inter-block Bus Data Links ── -->
  {inter_links_svg}

  <!-- ── Three Core Keynote Pillar Blocks ── -->
  {block1}
  {block2}
  {block3}

  <!-- ── Conference Stage Horizon & Stepped Neon Rails ── -->
  {stage_rails_svg}

  <!-- Frame Border -->
  <rect width="{W}" height="{H}" rx="14" fill="none" stroke="{BORDER}" stroke-width="1.2"/>
</svg>"""

    return svg


def main():
    svg = generate_hero_svg()
    with open("hero-keynote.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("hero-keynote.svg generated successfully! Size:", len(svg), "bytes")


if __name__ == "__main__":
    main()
