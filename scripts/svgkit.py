"""Shared helpers for every custom SVG on the profile.

Everything the profile renders (hero, section headers, stack, terminal,
footer, and the CI-generated stats cards) goes through this module so the
whole page shares one palette, one type system and one set of effects.

Fonts are embedded as base64 woff2 because GitHub renders README images
through its camo proxy inside <img>, which blocks external resources.
"""
from __future__ import annotations

import base64
import json
import math
import os
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"

# --------------------------------------------------------------------------- #
# Theme
# --------------------------------------------------------------------------- #
THEMES = {
    "brand": dict(
        name="brand",
        bg="#FBF8F1", bg2="#F3ECDB", ink="#1F1D1A", muted="#6B665C", faint="#9A948A",
        line="rgba(31,29,26,0.12)", line2="rgba(31,29,26,0.22)",
        glass="#FFFFFF", glass2="rgba(31,29,26,0.045)",
        cyan="#F5A623", violet="#FEBE3B", magenta="#C4503F", teal="#2F7A4F",
        green="#2F7A4F", amber="#F5A623", blue="#B23A2E",
        icon="#1F1D1A", aurora=0.35, grain=0.05,
    ),
    "brand-dark": dict(
        name="brand-dark",
        bg="#161410", bg2="#1F1B14", ink="#F6F1E7", muted="#B5AE9F", faint="#7D776B",
        line="rgba(246,241,231,0.12)", line2="rgba(246,241,231,0.22)",
        glass="rgba(255,255,255,0.05)", glass2="rgba(255,255,255,0.09)",
        cyan="#F5A623", violet="#FEBE3B", magenta="#E06A58", teal="#4CAF7A",
        green="#4CAF7A", amber="#F5A623", blue="#E06A58",
        icon="#F6F1E7", aurora=0.5, grain=0.07,
    ),
    "dark": dict(
        name="dark",
        bg="#070B1A", bg2="#0C1230", ink="#F1F5F9", muted="#98A2B8", faint="#5F6B85",
        line="rgba(255,255,255,0.10)", line2="rgba(255,255,255,0.18)",
        glass="rgba(255,255,255,0.045)", glass2="rgba(255,255,255,0.085)",
        cyan="#22D3EE", violet="#8B5CF6", magenta="#EC4899", teal="#2DD4BF",
        green="#34D399", amber="#FBBF24", blue="#60A5FA",
        icon="#E2E8F0", aurora=0.72, grain=0.07,
    ),
    "light": dict(
        name="light",
        bg="#F8FAFF", bg2="#EEF2FF", ink="#0B1020", muted="#55617A", faint="#8B95AB",
        line="rgba(11,16,32,0.10)", line2="rgba(11,16,32,0.18)",
        glass="rgba(255,255,255,0.72)", glass2="rgba(11,16,32,0.045)",
        cyan="#0E9FBF", violet="#6D28D9", magenta="#DB2777", teal="#0D9488",
        green="#059669", amber="#D97706", blue="#2563EB",
        icon="#1E293B", aurora=0.5, grain=0.05,
    ),
}


# --------------------------------------------------------------------------- #
# Fonts
# --------------------------------------------------------------------------- #
FONT_FILES = {
    ("Sora", 500): "Sora-500.woff2",
    ("Sora", 700): "Sora-700.woff2",
    ("Sora", 800): "Sora-800.woff2",
    ("Bricolage Grotesque", 700): "BricolageGrotesque-700.woff2",
    ("Bricolage Grotesque", 800): "BricolageGrotesque-800.woff2",
    ("Hanken Grotesk", 500): "HankenGrotesk-500.woff2",
    ("Hanken Grotesk", 600): "HankenGrotesk-600.woff2",
    ("JetBrains Mono", 400): "JetBrainsMono-400.woff2",
    ("JetBrains Mono", 600): "JetBrainsMono-600.woff2",
}


class Font:
    def __init__(self, family: str, weight: int):
        self.family, self.weight = family, weight
        self.path = FONT_DIR / FONT_FILES[(family, weight)]
        self.tt = TTFont(str(self.path))
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]
        self.upem = self.tt["head"].unitsPerEm
        self.b64 = base64.b64encode(self.path.read_bytes()).decode()

    def width(self, text: str, size: float, letter_spacing: float = 0.0) -> float:
        total = 0
        for ch in text:
            name = self.cmap.get(ord(ch)) or ".notdef"
            total += self.hmtx[name][0]
        return total / self.upem * size + letter_spacing * max(len(text) - 1, 0)

    @property
    def face(self) -> str:
        return (f"@font-face{{font-family:'{self.family}';font-weight:{self.weight};"
                f"src:url(data:font/woff2;base64,{self.b64}) format('woff2');}}")


@lru_cache(maxsize=None)
def font(family: str, weight: int) -> Font:
    return Font(family, weight)


def faces(*specs: tuple[str, int]) -> str:
    return "".join(font(f, w).face for f, w in specs)


DISPLAY = "'Bricolage Grotesque', ui-sans-serif, -apple-system, 'Segoe UI', Roboto, sans-serif"
BODY = "'Hanken Grotesk', ui-sans-serif, -apple-system, 'Segoe UI', Roboto, sans-serif"
SANS = "'Sora', ui-sans-serif, -apple-system, 'Segoe UI', Roboto, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


# --------------------------------------------------------------------------- #
# Icons (simple-icons paths, 24x24 viewBox)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=None)
def icons() -> dict:
    return json.loads((ROOT / "scripts" / "icons.json").read_text())


def icon(name: str, x: float, y: float, size: float, fill: str, opacity: float = 1) -> str:
    """Render a simple-icon centred at (x, y) with the given box size."""
    d = icons()[name]["d"]
    s = size / 24
    return (f'<path transform="translate({x - size/2:.2f} {y - size/2:.2f}) scale({s:.4f})" '
            f'd="{d}" fill="{fill}" opacity="{opacity}"/>')


# --------------------------------------------------------------------------- #
# Primitives
# --------------------------------------------------------------------------- #
def esc(s: str) -> str:
    return escape(s, {'"': "&quot;"})


def fmt(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def svg(width: int, height: int, body: str, style: str = "", defs: str = "",
        font_specs=(), aria: str = "") -> str:
    css = faces(*font_specs) + style
    title = f"<title>{esc(aria)}</title>" if aria else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{esc(aria)}">{title}'
            f"<style>{css}</style><defs>{defs}</defs>{body}</svg>")


def text(x, y, s, size, *, fill, weight=500, family=SANS, anchor="start",
         spacing=0.0, opacity=1.0, extra="") -> str:
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return (f'<text x="{fmt(x)}" y="{fmt(y)}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{op}{extra}>{esc(s)}</text>')


def rounded_perimeter(w: float, h: float, r: float) -> float:
    return 2 * (w + h) - 8 * r + 2 * math.pi * r


def grain_filter(fid: str = "grain") -> str:
    return (f'<filter id="{fid}" x="0" y="0" width="100%" height="100%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>'
            f'<feColorMatrix type="saturate" values="0"/>'
            f'<feComponentTransfer><feFuncA type="linear" slope="0.5"/></feComponentTransfer></filter>')


def glow_filter(fid: str, std: float = 10) -> str:
    return (f'<filter id="{fid}" x="-50%" y="-50%" width="200%" height="200%">'
            f'<feGaussianBlur stdDeviation="{std}"/></filter>')


def aurora_defs(t: dict, prefix: str = "au") -> str:
    """Radial gradients for soft aurora blobs (no blur filter: cheap + smooth)."""
    cols = [t["cyan"], t["violet"], t["magenta"], t["teal"], t["blue"]]
    out = []
    for i, c in enumerate(cols):
        out.append(f'<radialGradient id="{prefix}{i}"><stop offset="0" stop-color="{c}" stop-opacity="0.5"/>'
                   f'<stop offset="0.45" stop-color="{c}" stop-opacity="0.18"/>'
                   f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>')
    return "".join(out)


def aurora_blobs(t: dict, w: int, h: int, prefix: str = "au", seed: int = 0) -> tuple[str, str]:
    """Returns (css, body) for drifting aurora blobs covering a w x h area."""
    import random
    rnd = random.Random(seed)
    css, body = [], []
    n = 6
    for i in range(n):
        g = f"{prefix}{i % 5}"
        cx, cy = rnd.uniform(0.05, 0.95) * w, rnd.uniform(0.05, 0.95) * h
        r = rnd.uniform(0.24, 0.42) * max(w, h) * 0.9
        dur = rnd.uniform(16, 30)
        dx, dy = rnd.uniform(-0.12, 0.12) * w, rnd.uniform(-0.25, 0.25) * h
        sx, sy = rnd.uniform(0.85, 1.25), rnd.uniform(0.8, 1.2)
        css.append(f"@keyframes {prefix}d{i}{{0%{{transform:translate(0,0) scale(1,1)}}"
                   f"50%{{transform:translate({dx:.0f}px,{dy:.0f}px) scale({sx:.2f},{sy:.2f})}}"
                   f"100%{{transform:translate({-dx*0.6:.0f}px,{-dy*0.5:.0f}px) scale(1,1)}}}}")
        body.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="url(#{g})" '
                    f'style="transform-origin:{cx:.0f}px {cy:.0f}px;animation:{prefix}d{i} {dur:.1f}s ease-in-out infinite alternate;'
                    f'animation-delay:{-rnd.uniform(0, dur):.1f}s" />')
    style = "".join(css)
    group = (f'<g style="mix-blend-mode:screen" opacity="{t["aurora"]}">' if t["name"] == "dark"
             else f'<g opacity="{t["aurora"]}">') + "".join(body) + "</g>"
    return style, group


def dot_grid(t: dict, w: int, h: int, pid: str = "dots", step: int = 26, opacity=0.35) -> tuple[str, str]:
    defs = (f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<circle cx="1.5" cy="1.5" r="1.2" fill="{t["ink"]}"/></pattern>'
            f'<radialGradient id="{pid}Mask" cx="0.35" cy="0.4" r="0.75"><stop offset="0" stop-color="#fff" stop-opacity="0.8"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="{pid}M"><rect width="{w}" height="{h}" fill="url(#{pid}Mask)"/></mask>')
    body = f'<rect width="{w}" height="{h}" fill="url(#{pid})" mask="url(#{pid}M)" opacity="{opacity}"/>'
    return defs, body


def particles(t: dict, w: int, h: int, n: int = 22, seed: int = 1) -> tuple[str, str]:
    import random
    rnd = random.Random(seed)
    css = ("@keyframes floaty{0%{transform:translateY(0);opacity:.15}50%{opacity:.9}100%{transform:translateY(-22px);opacity:.2}}")
    cols = [t["cyan"], t["violet"], t["magenta"], t["ink"]]
    body = []
    for _ in range(n):
        x, y = rnd.uniform(20, w - 20), rnd.uniform(20, h - 20)
        r = rnd.uniform(1, 2.6)
        body.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{rnd.choice(cols)}" '
                    f'style="animation:floaty {rnd.uniform(4, 9):.1f}s {-rnd.uniform(0, 8):.1f}s ease-in-out infinite alternate"/>')
    return css, "".join(body)


def beam_gradient(t: dict, gid: str = "beam") -> str:
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{t["cyan"]}"/><stop offset="0.5" stop-color="{t["violet"]}"/>'
            f'<stop offset="1" stop-color="{t["magenta"]}"/></linearGradient>')


def border_beam(x, y, w, h, r, *, gid="beam", seg=90, dur=5.0, delay=0.0, width=1.6) -> str:
    """A short bright dash that travels around a rounded rect's border."""
    p = rounded_perimeter(w, h, r)
    return (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="{r}" fill="none" '
            f'stroke="url(#{gid})" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-dasharray="{seg} {p - seg:.1f}">'
            f'<animate attributeName="stroke-dashoffset" from="0" to="{-p:.1f}" dur="{dur}s" '
            f'begin="{delay}s" repeatCount="indefinite"/></rect>')


def glass(x, y, w, h, r, t: dict, *, fill=None, stroke=None, extra="") -> str:
    return (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="{r}" '
            f'fill="{fill or t["glass"]}" stroke="{stroke or t["line"]}" stroke-width="1"{extra}/>')


def shimmer(w: int, h: int, *, dur=9.0, delay=0.0, opacity=0.08, color="#fff") -> tuple[str, str]:
    """A soft diagonal light band sweeping across the surface."""
    css = f"@keyframes sweep{{0%{{transform:translateX({-w*0.9:.0f}px)}}100%{{transform:translateX({w*1.4:.0f}px)}}}}"
    defs = (f'<linearGradient id="sweepG" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="0"/><stop offset="0.5" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>')
    body = (f'<rect x="0" y="-20" width="{w*0.35:.0f}" height="{h+40}" fill="url(#sweepG)" '
            f'transform="skewX(-18)" style="animation:sweep {dur}s {delay}s cubic-bezier(.4,0,.2,1) infinite"/>')
    return css + "", defs + "", body


def gradient_text_defs(t: dict, gid="gtx", span=700) -> str:
    """Flowing gradient for display text, animated with a reflected translate."""
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{span}" y2="0" spreadMethod="reflect">'
            f'<stop offset="0" stop-color="{t["cyan"]}"/><stop offset="0.35" stop-color="{t["ink"]}"/>'
            f'<stop offset="0.65" stop-color="{t["violet"]}"/><stop offset="1" stop-color="{t["magenta"]}"/>'
            f'<animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="{span*2} 0" dur="9s" repeatCount="indefinite"/>'
            f'</linearGradient>')


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}  ({len(content.encode())/1024:.0f} KB)")
