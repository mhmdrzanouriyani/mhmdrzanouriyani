#!/usr/bin/env python3
"""
Aurora-style GitHub profile cards generator.

Produces animated SVG cards (header, stats, tech stack, project cards,
social buttons) into ./assets/. Live numbers come from the GitHub API.

Run locally:   GITHUB_TOKEN=xxx python scripts/generate_cards.py
Offline demo:  python scripts/generate_cards.py --offline
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

# ============================ CONFIG (edit me) ============================
USERNAME = "mhmdrzanouriyani"
NAME = "Mohammadreza Nouriyani"
TAGLINE = "Computer Engineering @ BTU | Python, Full-Stack & AI | Creator @MohixCode"
HEADER_TAGS = ["Python", "TypeScript", "Next.js", "Linux", "Networking"]

STACK = {
    "LANGUAGES": ["Python", "TypeScript", "JavaScript", "C", "Bash"],
    "FRAMEWORKS": ["Next.js", "React", "FastAPI", "Flask", "aiogram", "Three.js"],
    "AI / DATA": ["TensorFlow.js", "Autoencoders", "Anomaly Detection"],
    "INFRA": ["Linux", "Docker", "PostgreSQL", "Redis", "Nginx", "Cisco"],
}

# Featured projects: repo name -> (title, description, language)
PROJECTS = [
    ("staj-takip", "SpikEdge Telemetry",
     "Real-time industrial dashboard with 3D view and in-browser AI anomaly detection",
     "TypeScript"),
    ("telegrambot", "Telegram Downloader Bot",
     "Production-ready async bot for YouTube, Shorts and Instagram downloads",
     "Python"),
    ("NetProbe-Plus", "NetProbe-Plus",
     "Network diagnostics and probing toolkit for hands-on troubleshooting",
     "Python"),
    ("programing-language-project", "Syntax Highlighter",
     "Lexer, parser and GUI editor built from scratch",
     "Python"),
]

SOCIALS = [  # (id, label, brand color)
    ("youtube", "YouTube", "#FF0033"),
    ("instagram", "Instagram", "#E1306C"),
    ("github", "GitHub", "#A78BFA"),
]
# ==========================================================================

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, Inter, Helvetica, Arial, sans-serif"
LANG_COLORS = {"Python": "#3572A5", "TypeScript": "#3178C6",
               "JavaScript": "#F1E05A", "HTML": "#E34C26", "C": "#555555"}

API = "https://api.github.com"


# ------------------------------ GitHub data -------------------------------
def gh(path: str, accept: str = "application/vnd.github+json"):
    req = urllib.request.Request(API + path, headers={"Accept": accept,
                                                      "User-Agent": USERNAME})
    token = os.getenv("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fetch_data() -> dict:
    user = gh(f"/users/{USERNAME}")
    repos, page = [], 1
    while True:
        batch = gh(f"/users/{USERNAME}/repos?per_page=100&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)
    try:
        commits = gh(f"/search/commits?q=author:{USERNAME}")["total_count"]
    except Exception:
        commits = 0
    with urllib.request.urlopen(user["avatar_url"] + "&s=200", timeout=20) as r:
        avatar = "data:image/png;base64," + base64.b64encode(r.read()).decode()
    by_name = {r["name"]: r for r in repos}
    return {"repos": user["public_repos"], "stars": stars, "commits": commits,
            "followers": user["followers"], "avatar": avatar, "by_name": by_name}


def offline_data() -> dict:
    return {"repos": 18, "stars": 12, "commits": 640, "followers": 30,
            "avatar": None, "by_name": {}}


# ------------------------------ SVG helpers -------------------------------
def text_w(s: str, size: float = 12, bold: bool = True) -> float:
    """Rough text width estimate (SVG in <img> can't measure text)."""
    return len(s) * size * (0.60 if bold else 0.55)


def aurora(w: int, h: int, uid: str, intensity: float = 1.0) -> str:
    """Blurred, slowly drifting colour blobs along the bottom edge."""
    blobs = [  # (cx ratio, colour, rx, ry, duration, dx)
        (0.18, "#7c3aed", 0.22, 0.40, 14, 60),
        (0.45, "#4f46e5", 0.20, 0.36, 18, -50),
        (0.68, "#a21caf", 0.18, 0.34, 16, 45),
        (0.90, "#0891b2", 0.16, 0.32, 20, -40),
    ]
    els = []
    for i, (cx, c, rx, ry, dur, dx) in enumerate(blobs):
        els.append(
            f'<ellipse class="b{i}" cx="{w*cx:.0f}" cy="{h*1.02:.0f}" '
            f'rx="{w*rx:.0f}" ry="{h*ry:.0f}" fill="{c}" '
            f'opacity="{0.55*intensity:.2f}"/>')
    keyframes = "".join(
        f"@keyframes m{i}{{0%,100%{{transform:translate(0,0)}}"
        f"50%{{transform:translate({dx}px,-{6+i*2}px)}}}}"
        f".b{i}{{animation:m{i} {dur}s ease-in-out infinite}}"
        for i, (_, _, _, _, dur, dx) in enumerate(blobs))
    return (f'<style>{keyframes}</style>'
            f'<filter id="blur{uid}" x="-50%" y="-50%" width="200%" height="200%">'
            f'<feGaussianBlur stdDeviation="{max(28, h*0.22):.0f}"/></filter>'
            f'<g filter="url(#blur{uid})">{"".join(els)}</g>')


def card(w: int, h: int, uid: str, body: str, intensity: float = 1.0) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs><clipPath id="clip{uid}"><rect width="{w}" height="{h}" rx="18"/></clipPath></defs>
<g clip-path="url(#clip{uid})">
<rect width="{w}" height="{h}" fill="#08080d"/>
{aurora(w, h, uid, intensity)}
</g>
<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="18" fill="none" stroke="#ffffff" stroke-opacity=".08"/>
<g font-family="{FONT}">{body}</g>
</svg>"""


def pill(x: float, y: float, label: str, size: float = 12,
         fill: str = "#1a1530", stroke: str = "#3b2f6b", color: str = "#cfc6ff") -> tuple[str, float]:
    w = text_w(label, size) + 22
    h = size + 14
    svg = (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2-3}" '
           f'fill="{fill}" stroke="{stroke}"/>'
           f'<text x="{x + w/2:.1f}" y="{y + h/2 + size*0.36:.1f}" text-anchor="middle" '
           f'font-size="{size}" font-weight="600" fill="{color}">{escape(label)}</text>')
    return svg, w


# -------------------------------- Cards -----------------------------------
def header_card(d: dict) -> str:
    W, H = 840, 200
    cx, cy, r = 100, 100, 46
    if d["avatar"]:
        avatar = (f'<clipPath id="av"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>'
                  f'<image href="{d["avatar"]}" x="{cx-r}" y="{cy-r}" width="{2*r}" '
                  f'height="{2*r}" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>')
    else:
        avatar = (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#14112a"/>'
                  f'<text x="{cx}" y="{cy+11}" text-anchor="middle" font-size="30" '
                  f'font-weight="800" fill="#c4b5fd">MN</text>')
    ring = (f'<defs><linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="#8b5cf6"/><stop offset="1" stop-color="#3b82f6"/>'
            f'</linearGradient></defs>'
            f'<circle cx="{cx}" cy="{cy}" r="{r+5}" fill="none" stroke="url(#ring)" stroke-width="4">'
            f'<animateTransform attributeName="transform" type="rotate" '
            f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="8s" repeatCount="indefinite"/></circle>')
    x = 185
    pills, px = [], x
    for t in HEADER_TAGS:
        s, w = pill(px, 128, t)
        pills.append(s)
        px += w + 9
    body = (ring + avatar +
            f'<text x="{x}" y="88" font-size="38" font-weight="800" fill="#ffffff" '
            f'letter-spacing="-.5">{escape(NAME)}</text>'
            f'<text x="{x}" y="114" font-size="14.5" fill="#a5a3c9">{escape(TAGLINE)}</text>'
            + "".join(pills))
    return card(W, H, "h", body)


def stats_card(d: dict) -> str:
    W, H = 840, 130
    items = [("REPOS", d["repos"], "#a78bfa"), ("STARS", d["stars"], "#60a5fa"),
             ("COMMITS", d["commits"], "#f59e0b"), ("FOLLOWERS", d["followers"], "#34d399")]
    col = W / len(items)
    body = []
    for i, (label, val, c) in enumerate(items):
        mx = col * i + col / 2
        body.append(f'<text x="{mx:.0f}" y="66" text-anchor="middle" font-size="34" '
                    f'font-weight="800" fill="{c}">{val:,}</text>'
                    f'<text x="{mx:.0f}" y="90" text-anchor="middle" font-size="11" '
                    f'font-weight="700" letter-spacing="2.5" fill="#6b6a85">{label}</text>')
        if i:
            body.append(f'<line x1="{col*i:.0f}" y1="32" x2="{col*i:.0f}" y2="98" '
                        f'stroke="#ffffff" stroke-opacity=".06"/>')
    return card(W, H, "s", "".join(body), 0.8)


def stack_card() -> str:
    W = 840
    row_h = 40
    H = 70 + row_h * len(STACK) + 10
    body = ['<text x="32" y="40" font-size="11" font-weight="700" letter-spacing="3" '
            'fill="#55546e">TECH STACK</text>']
    label_c = ["#a78bfa", "#60a5fa", "#f472b6", "#22d3ee"]
    for i, (label, items) in enumerate(STACK.items()):
        y = 62 + i * row_h
        body.append(f'<text x="32" y="{y+17}" font-size="11" font-weight="700" '
                    f'letter-spacing="1.5" fill="{label_c[i % 4]}">{label}</text>')
        px = 150
        for t in items:
            s, w = pill(px, y, t, 12, fill="#16161f", stroke="#2c2c3d", color="#e4e4f0")
            body.append(s)
            px += w + 8
    return card(W, H, "k", "".join(body), 0.9)


def project_card(i: int, repo: str, title: str, desc: str, lang: str, d: dict) -> str:
    W, H = 412, 150
    info = d["by_name"].get(repo, {})
    stars = info.get("stargazers_count", 0)
    # wrap description to two lines
    words, lines, cur = desc.split(), [], ""
    for wd in words:
        if text_w(cur + " " + wd, 13, False) > W - 60 and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    desc_svg = "".join(
        f'<text x="26" y="{78 + j*19}" font-size="13" fill="#9d9cb8">{escape(l)}</text>'
        for j, l in enumerate(lines[:2]))
    lc = LANG_COLORS.get(lang, "#8b5cf6")
    body = (f'<text x="26" y="46" font-size="18" font-weight="800" fill="#ffffff">'
            f'{escape(title)}</text>'
            f'<text x="{W-26}" y="46" text-anchor="end" font-size="16" fill="#6b6a85">↗</text>'
            + desc_svg +
            f'<circle cx="32" cy="{H-26}" r="5" fill="{lc}"/>'
            f'<text x="44" y="{H-22}" font-size="12" fill="#c9c8dd">{lang}</text>'
            f'<text x="{W-26}" y="{H-22}" text-anchor="end" font-size="12" '
            f'fill="#c9c8dd">★ {stars}</text>')
    return card(W, H, f"p{i}", body, 0.7)


ICONS = {  # simple 24x24 paths
    "linkedin": "M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05C20.6 8.65 21 11.2 21 14.5V21h-4v-5.8c0-1.4-.03-3.2-1.95-3.2-1.95 0-2.25 1.5-2.25 3.1V21H9z",
    "youtube": "M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12 31 31 0 0 0 1 16.8a3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8zM9.75 15.02V8.98L15.5 12z",
    "instagram": "M12 7.3A4.7 4.7 0 1 0 12 16.7 4.7 4.7 0 0 0 12 7.3zm0 7.7a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm6-7.9a1.1 1.1 0 1 1-2.2 0 1.1 1.1 0 0 1 2.2 0zM17 2H7a5 5 0 0 0-5 5v10a5 5 0 0 0 5 5h10a5 5 0 0 0 5-5V7a5 5 0 0 0-5-5zm3.2 15A3.2 3.2 0 0 1 17 20.2H7A3.2 3.2 0 0 1 3.8 17V7A3.2 3.2 0 0 1 7 3.8h10A3.2 3.2 0 0 1 20.2 7z",
    "github": "M12 .5a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.33-1.28-1.69-1.28-1.69-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.71 1.26 3.37.96.1-.75.4-1.26.73-1.55-2.56-.29-5.25-1.28-5.25-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.42-2.7 5.39-5.26 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5z",
    "email": "M2 5h20v14H2zm2 2v.5l8 5 8-5V7l-8 5z",
}


def social_button(sid: str, label: str, color: str) -> str:
    W, H = 150, 48
    body = (f'<defs><linearGradient id="g{sid}" x1="0" x2="1">'
            f'<stop offset="0" stop-color="{color}"/><stop offset="1" stop-color="#8b5cf6"/>'
            f'</linearGradient></defs>'
            f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{H/2-1}" fill="#0b0b12" '
            f'stroke="url(#g{sid})" stroke-width="1.6"/>'
            f'<g transform="translate(30 14) scale(.83)"><path d="{ICONS[sid]}" fill="{color}" '
            f'fill-rule="evenodd"/></g>'
            f'<text x="58" y="30" font-size="14.5" font-weight="700" fill="#ffffff">'
            f'{escape(label)}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}"><g font-family="{FONT}">{body}</g></svg>')


# --------------------------------- main -----------------------------------
def main() -> None:
    d = offline_data() if "--offline" in sys.argv else fetch_data()
    OUT.mkdir(parents=True, exist_ok=True)
    files = {"header.svg": header_card(d), "stats.svg": stats_card(d),
             "stack.svg": stack_card()}
    for i, p in enumerate(PROJECTS):
        files[f"project-{i}.svg"] = project_card(i, *p, d)
    for sid, label, color in SOCIALS:
        files[f"btn-{sid}.svg"] = social_button(sid, label, color)
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
    print(f"Wrote {len(files)} cards to {OUT}")


if __name__ == "__main__":
    main()
