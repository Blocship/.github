"""Builds the Blocship org-profile art (profile/assets/*.svg), brand light + dark.

Run:  python scripts/build_org.py
Copy and numbers mirror blocship.io.
"""
from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgkit import (BODY, DISPLAY, MONO, ROOT, THEMES, border_beam, esc, fmt, font, glass,  # noqa: E402
                    glow_filter, grain_filter, icon, shimmer, svg, text, write)

OUT = ROOT / "profile" / "assets"
EASE = "cubic-bezier(.22,1,.36,1)"
VARIANTS = ("brand", "brand-dark")

STATS = (("6,000", "drivers in production"), ("30+", "products shipped & live"),
         ("7 yrs", "building real software"), ("AI", "in production, not demos"))

CASES = [
    dict(name="The Courier App", tag="LOGISTICS · FULL-STACK", result="Scaled to 6,000 drivers", url="https://www.thecourier.app/",
         did="A driver platform for daily deliveries: onboarding, sign-up, and the flows a courier fleet runs on every day.",
         built="We inherited a slow app with badly wired flows and code that couldn't scale. We rebuilt the whole thing and took it to 6,000 drivers in production.",
         broke=("BROKE", "Someone pointed a DDoS at the OTP sign-up endpoint in production, right when new drivers were trying to join."),
         fix="We put Turnstile in front of it and stopped the attack without taking the app down. Sign-up got faster and the hiring data got cleaner."),
    dict(name="YDigest", tag="AI · LLM PIPELINE", result="500K → 10K API calls", url="https://ydigest.app/",
         did="A YouTube transcript and summarizer app. Follow your favourite channels and the feed fills up with transcripts and summaries in the format you prefer.",
         built="It came to us as a vibe-coded prototype. We rebuilt the data layer underneath it and turned it into something that could run at scale.",
         broke=("BROKE", "Supabase was logging 500,000 REST calls. Runaway requests and a couple of memory leaks were driving the bill up and stability down."),
         fix="We added proper caching, traced the leaks, and got it down to 10,000 calls. Same product, 98% less traffic."),
    dict(name="Calcount Australia", tag="MOBILE · NUTRITION", result="70K+ users a year", url="https://www.caloriecounter.com.au/",
         did="A free calorie-tracking app for a web product that already saw 70,000+ users a year. Australian and New Zealand foods, barcode scanning built in.",
         built="We turned their web product into a mobile app and wired the barcode scanner to a nutrient database built for the region.",
         broke=("HARD PART", "Nutrition data has to be exact. For someone counting calories, a wrong barcode match or a US figure is worse than showing nothing."),
         fix="We matched every scan against an AU/NZ food database, so what comes back is the real local number rather than a rough guess."),
    dict(name="WithLyla", tag="WEB · RESCUE", result="Flows fixed, fully responsive", url="https://www.withlyla.com/",
         did="A travel-insurance website for a Hong Kong company, covering the quote, purchase and policy flows travellers depend on.",
         built="We came in to rescue it. Every API got reconnected, the flows got wired up the way they should have been, and the caching layer was rebuilt.",
         broke=("BROKE", "The flows and caching had serious flaws, and the site wasn't responsive at all. It fell apart on the phones most travellers book from."),
         fix="We fixed the flows and caching end to end, then made it responsive on every screen size we could throw at it."),
]

PROBLEMS = [
    ("SEPA", "SEPA & virtual IBANs", "Direct-debit mandates, credit-transfer reconciliation, and the webhook lifecycles SEPA actually requires."),
    ("PAY", "Stripe Connect split-fee", "Marketplace payouts to connected accounts, convenience + management fees, subscription paywalls."),
    ("RTC", "Real-time video (Agora / WebRTC)", "Stable join → live → reconnect lifecycle, secure token handling, cross-device reliability."),
    ("BLE", "BLE & device sensors", "Barometric floor detection, hardware pairing, and taming real-world signal noise."),
    ("SaaS", "Multi-tenant + AI agents", "Platform plus client instances, with LLM workflows that hold up in production, not just in a demo."),
    ("SHIP", "App Store & Play submission", "Metadata, permissions and compliance handled so your build passes review without rejections."),
]

STEPS = [("Scope honestly", "Work out what's worth building, and what isn't, before any code."),
         ("Architect", "Data model, integrations and the hard parts first, so nothing gets ripped out later."),
         ("Ship in weeks", "Working, reviewed software in weeks, not a six-month black box."),
         ("Maintain & scale", "We stick around. Real products need a team that still knows them when they grow.")]

SECTIONS = {
    "work": ("01", "What it did. What we built. What broke.", "selected work"),
    "problems": ("02", "The parts most studios skip", "hard problems"),
    "approach": ("03", "How we work", "first call to long after launch"),
    "oss": ("04", "Open source", "packages we maintain"),
    "team": ("05", "The studio behind the work", "a founder out front"),
    "contact": ("06", "Tell me your problem", "I'll tell you straight"),
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def wrap(s: str, f, size: float, max_w: float) -> list[str]:
    lines, cur = [], ""
    for w in s.split():
        trial = (cur + " " + w).strip()
        if f.width(trial, size) <= max_w: cur = trial
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def logo_mark(x, y, size=28) -> str:
    """Blocship 'b' mark from the site icon (17x19 viewBox)."""
    s = size / 19
    return (f'<g transform="translate({x} {y}) scale({s:.3f})">'
            '<path d="M3.75 4.90625H6.37503C9.89588 4.90625 12.7501 7.76046 12.7501 11.2813C12.7501 14.8022 9.89588 17.6564 6.37503 17.6564H3.75V4.90625Z" fill="url(#lg1)"/>'
            '<rect y="4.15723" width="4.50004" height="13.5001" fill="url(#lg2)"/>'
            '<path d="M3.75 8.65918H6.75003C7.99268 8.65918 9.00005 9.66655 9.00005 10.9092C9.00005 12.1519 7.99268 13.1592 6.75003 13.1592H3.75V8.65918Z" fill="#E8AF2B"/>'
            '<rect y="0.40625" width="4.50004" height="4.50004" fill="#E4AF31"/>'
            '<path d="M12.75 13.4063C12.75 12.1636 13.7574 11.1562 15 11.1562C16.2427 11.1562 17.2501 12.1636 17.2501 13.4063C17.2501 14.6489 16.2427 15.6563 15 15.6563C13.7574 15.6563 12.75 14.6489 12.75 13.4063Z" fill="url(#lg3)"/></g>')


def logo_defs() -> str:
    return ('<linearGradient id="lg1" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FEBE3B"/><stop offset="1" stop-color="#F9A720"/></linearGradient>'
            '<linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#FEBE3B"/><stop offset="1" stop-color="#FEA62B"/></linearGradient>'
            '<linearGradient id="lg3" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FEA62B"/><stop offset="1" stop-color="#FE901D"/></linearGradient>')


def frame(t: dict, W: int, H: int, cid: str, r=26):
    dark = t["name"].endswith("dark")
    defs = (f'<clipPath id="{cid}"><rect width="{W}" height="{H}" rx="{r}"/></clipPath>'
            f'<linearGradient id="{cid}bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["bg"]}"/><stop offset="1" stop-color="{t["bg2"]}"/></linearGradient>'
            f'<radialGradient id="{cid}am"><stop offset="0" stop-color="{t["amber"]}" stop-opacity="{0.28 if not dark else 0.22}"/><stop offset="1" stop-color="{t["amber"]}" stop-opacity="0"/></radialGradient>'
            + grain_filter(cid + "g"))
    css = (f"@keyframes {cid}drift{{0%{{transform:translate(0,0) scale(1)}}100%{{transform:translate(40px,-24px) scale(1.12)}}}}")
    open_ = (f'<g clip-path="url(#{cid})"><rect width="{W}" height="{H}" fill="url(#{cid}bg)"/>'
             f'<circle cx="{W*0.82:.0f}" cy="{H*0.1:.0f}" r="{max(W,H)*0.38:.0f}" fill="url(#{cid}am)" style="transform-origin:{W*0.82:.0f}px {H*0.1:.0f}px;animation:{cid}drift 18s ease-in-out infinite alternate"/>'
             f'<rect width="{W}" height="{H}" filter="url(#{cid}g)" opacity="{t["grain"]}" style="mix-blend-mode:multiply"/>')
    close = f'</g><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="{r-0.5}" fill="none" stroke="{t["line"]}"/>'
    return defs, css, open_, close


def tag(x, y, label, t, fill=None, ink=None, mono=None) -> str:
    m = mono or font("JetBrains Mono", 600)
    w = m.width(label, 10.5, 1.2) + 20
    return (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{w:.0f}" height="22" rx="6" fill="{fill or t["amber"]}" fill-opacity="{0.22 if fill is None else 1}"/>'
            + text(x + 10, y + 15, label, 10.5, fill=ink or t["ink"], weight=600, family=MONO, spacing=1.2)
            + f'<!--{w:.0f}-->')


# --------------------------------------------------------------------------- #
# hero
# --------------------------------------------------------------------------- #
def hero(t: dict) -> str:
    W, H = 1200, 540
    dark = t["name"].endswith("dark")
    d800, h500, m600 = font("Bricolage Grotesque", 800), font("Hanken Grotesk", 500), font("JetBrains Mono", 600)
    defs, css, open_, close = frame(t, W, H, "hr", r=28)
    defs += logo_defs() + glow_filter("hg", 10)
    avatar = base64.b64encode((ROOT / "assets" / "img" / "founder.jpg").read_bytes()).decode()
    defs += ('<clipPath id="av"><circle cx="0" cy="0" r="30"/></clipPath>'
             f'<linearGradient id="hl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["amber"]}"/><stop offset="1" stop-color="{t["violet"]}"/></linearGradient>'
             f'<linearGradient id="hline" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["line2"]}"/><stop offset="1" stop-color="{t["line2"]}"/></linearGradient>')
    css += ("@keyframes up{0%{opacity:0;transform:translateY(14px)}100%{opacity:1;transform:translateY(0)}}"
            "@keyframes mark{0%{transform:scaleX(0)}100%{transform:scaleX(1)}}"
            "@keyframes ring{0%{r:7;opacity:.8}100%{r:22;opacity:0}}"
            "@keyframes tick{0%,100%{opacity:1}50%{opacity:.35}}")
    b = [open_]
    L = 64

    def up(delay, inner): return f'<g style="animation:up 1s {delay}s {EASE} both">{inner}</g>'

    # wordmark
    b.append(up(0, logo_mark(L, 46, 34) + text(L + 44, 74, "blocship", 28, fill=t["ink"], weight=800, family=DISPLAY)))
    # eyebrow
    b.append(up(0.08, f'<rect x="{L}" y="112" width="22" height="2" fill="{t["amber"]}"/>'
                + text(L + 32, 117, "FOUNDER-LED STUDIO · YOU DEAL WITH ME DIRECTLY", 11.5, fill=t["amber"], weight=600, family=MONO, spacing=1.6)))
    # headline with marker highlight under "senior team"
    size = 50
    l1, l2 = "One person owns your build.", "A senior team ships it."
    pre = d800.width("A ", size); hw = d800.width("senior team", size)
    y1, y2 = 180, 238
    b.append(up(0.16, text(L, y1, l1, size, fill=t["ink"], weight=800, family=DISPLAY)))
    b.append(up(0.28, f'<rect x="{L+pre-4:.0f}" y="{y2-size*0.52:.0f}" width="{hw+8:.0f}" height="{size*0.62:.0f}" rx="4" fill="{t["amber"]}" opacity="{0.55 if not dark else 0.4}" '
                      f'style="transform-origin:{L+pre:.0f}px 0;animation:mark 1.1s .7s {EASE} both"/>'
                      + text(L, y2, l2, size, fill=t["ink"], weight=800, family=DISPLAY)))
    # body
    body = ("Most studios put a project manager between you and whoever writes the code. I don't. I own the work, set the architecture "
            "and stay on the hook while a small senior team ships it alongside me. Flutter mobile, Node and TypeScript backends, Postgres, "
            "AI with Claude, OpenAI and Gemini, and the occasional bit of hardware.")
    for i, ln in enumerate(wrap(body, h500, 17, 640)):
        b.append(up(0.36 + i * 0.04, text(L, 292 + i * 26, ln, 17, fill=t["muted"], weight=500, family=BODY)))
    # stats
    sy = 400
    xs = L
    for i, (num, lab) in enumerate(STATS):
        nw = d800.width(num, 30)
        b.append(up(0.55 + i * 0.1, text(xs, sy, num, 30, fill=t["ink"], weight=800, family=DISPLAY)
                 + text(xs, sy + 22, lab, 12, fill=t["muted"], weight=600, family=BODY)))
        xs += max(nw, h500.width(lab, 12)) + 44
        if i < 3: b.append(f'<rect x="{xs-22:.0f}" y="{sy-26}" width="1" height="56" fill="{t["line"]}"/>')
    # CTA pill
    cy = 470
    lab = "Book a call  →"
    cw = d800.width(lab, 15) + 48
    b.append(up(0.95, f'<rect x="{L}" y="{cy}" width="{cw:.0f}" height="44" rx="22" fill="{t["amber"]}"/>'
                 + text(L + 24, cy + 28, lab, 15, fill="#1F1D1A", weight=800, family=DISPLAY)
                 + text(L + cw + 22, cy + 27, "15 minutes · no pitch · times in your timezone", 12.5, fill=t["muted"], weight=500, family=BODY)))

    # right: founder card + pipeline
    px, py = 830, 70
    b.append(up(0.3, glass(px, py, 306, 120, 20, t, fill=t["glass"] if not dark else t["glass2"])
                 + border_beam(px, py, 306, 120, 20, gid="hbeam", seg=60, dur=6, width=1.2)
                 + f'<g transform="translate({px+48} {py+60})"><circle r="33" fill="{t["amber"]}" opacity=".9"/>'
                 f'<image href="data:image/jpeg;base64,{avatar}" x="-30" y="-30" width="60" height="60" clip-path="url(#av)"/></g>'
                 + text(px + 96, py + 50, "Shahzad", 18, fill=t["ink"], weight=800, family=DISPLAY)
                 + text(px + 96, py + 70, "founder & principal engineer", 12.5, fill=t["muted"], weight=600, family=BODY)
                 + text(px + 96, py + 92, "I set the architecture on every build", 12, fill=t["faint"], weight=500, family=BODY)))
    defs += f'<linearGradient id="hbeam" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["amber"]}"/><stop offset="1" stop-color="{t["magenta"]}"/></linearGradient>'
    # pipeline
    nodes = ["Scope", "Architect", "Ship", "Maintain"]
    ny = 262
    nx = [px + 30 + i * 86 for i in range(4)]
    b.append(up(0.5, f'<path d="M{nx[0]} {ny} H{nx[-1]}" stroke="{t["line2"]}" stroke-width="2" stroke-dasharray="4 6"/>'))
    pulse = (f'<circle cy="{ny}" r="6" fill="{t["amber"]}" filter="url(#hg)"><animate attributeName="cx" values="{nx[0]};{nx[-1]}" dur="4s" repeatCount="indefinite" calcMode="spline" keySplines="0.45 0 0.55 1" keyTimes="0;1"/>'
             f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.08;0.92;1" dur="4s" repeatCount="indefinite"/></circle>')
    b.append(up(0.5, pulse))
    for i, (x, n) in enumerate(zip(nx, nodes)):
        b.append(up(0.55 + i * 0.1, f'<circle cx="{x}" cy="{ny}" r="14" fill="{t["bg"]}" stroke="{t["amber"]}" stroke-width="2"/>'
                     f'<circle cx="{x}" cy="{ny}" r="14" fill="none" stroke="{t["amber"]}" style="animation:ring 2.4s {i*0.6:.1f}s ease-out infinite"/>'
                     + text(x, ny + 5, str(i + 1), 12, fill=t["ink"], weight=600, family=MONO, anchor="middle")
                     + text(x, ny + 36, n, 12.5, fill=t["muted"], weight=600, family=BODY, anchor="middle")))
    b.append(up(0.6, text(px + 30, ny - 32, "HOW A BUILD RUNS", 10.5, fill=t["faint"], weight=600, family=MONO, spacing=1.5)))
    # proof chips
    chips = [("✓", "You talk to me, not a salesperson"), ("✓", "Risky parts sequenced first"), ("✓", "Written, clear, async updates"), ("✓", "We stick around after launch")]
    for i, (m, c) in enumerate(chips):
        yy = 340 + i * 36
        b.append(up(0.8 + i * 0.08, f'<circle cx="{px+38}" cy="{yy}" r="9" fill="{t["green"]}" opacity=".18"/>'
                     + text(px + 38, yy + 4, m, 11, fill=t["green"], weight=600, family=MONO, anchor="middle")
                     + text(px + 58, yy + 5, c, 14, fill=t["ink"], weight=500, family=BODY)))
    b.append(close)
    return svg(W, H, "".join(b), style=css, defs=defs,
               font_specs=(("Bricolage Grotesque", 800), ("Hanken Grotesk", 500), ("Hanken Grotesk", 600), ("JetBrains Mono", 600)),
               aria="Blocship: one person owns your build, a senior team ships it")


# --------------------------------------------------------------------------- #
# section header
# --------------------------------------------------------------------------- #
def header(t: dict, idx: str, title: str, caption: str) -> str:
    W, H = 1200, 76
    d800, m600 = font("Bricolage Grotesque", 800), font("JetBrains Mono", 600)
    css = "@keyframes hin{0%{opacity:0;transform:translateX(-14px)}100%{opacity:1;transform:translateX(0)}}@keyframes hl{0%{transform:scaleX(0)}100%{transform:scaleX(1)}}"
    defs = glow_filter("hg", 4)
    size = 30 if d800.width(title, 30) < 760 else 26
    tw = d800.width(title, size)
    b = [f'<g style="animation:hin .9s {EASE} both"><rect x="0" y="22" width="34" height="34" rx="10" fill="{t["amber"]}"/>'
         + text(17, 44.5, idx, 12.5, fill="#1F1D1A", weight=600, family=MONO, anchor="middle")
         + text(50, 48, title, size, fill=t["ink"], weight=800, family=DISPLAY) + "</g>"]
    x0 = 50 + tw + 24; cw = m600.width(caption.upper(), 11, 1.4); x1 = W - cw - 24
    b.append(f'<rect x="{x0:.0f}" y="38" width="{max(x1-x0,0):.0f}" height="1.5" fill="{t["line2"]}" style="transform-origin:{x0:.0f}px 0;animation:hl 1.4s .3s {EASE} both"/>')
    b.append(f'<circle cy="38.75" r="3" fill="{t["amber"]}" filter="url(#hg)"><animate attributeName="cx" from="{x0:.0f}" to="{x1:.0f}" dur="4.5s" begin="1.2s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1"/>'
             f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.85;1" dur="4.5s" begin="1.2s" repeatCount="indefinite"/></circle>')
    b.append(text(W - 2, 42.5, caption.upper(), 11, fill=t["amber"], weight=600, family=MONO, anchor="end", spacing=1.4))
    return svg(W, H, "".join(b), style=css, defs=defs, font_specs=(("Bricolage Grotesque", 800), ("JetBrains Mono", 600)), aria=f"{idx} {title}")


# --------------------------------------------------------------------------- #
# case study card
# --------------------------------------------------------------------------- #
def case(t: dict, c: dict, i: int) -> str:
    W = 590
    dark = t["name"].endswith("dark")
    d800, h500, h600, m600 = font("Bricolage Grotesque", 800), font("Hanken Grotesk", 500), font("Hanken Grotesk", 600), font("JetBrains Mono", 600)
    PAD = 30
    LAB = int(max(m600.width(l, 10.5, 1.2) for l in ("DID", "BUILT", "FIX", c["broke"][0])) + 16)
    tw = W - PAD * 2 - LAB
    rows = [("DID", c["did"], False), ("BUILT", c["built"], False), (c["broke"][0], c["broke"][1], True), ("FIX", c["fix"], False)]
    laid = []
    y = 112
    for lab, body, hot in rows:
        lines = wrap(body, h500, 14.5, tw - (24 if hot else 0))
        h = len(lines) * 21 + (22 if hot else 10)
        laid.append((lab, lines, hot, y, h)); y += h + 10
    H = int(y + 14)
    defs, css, open_, close = frame(t, W, H, f"cs{i}", r=22)
    css += "@keyframes up{0%{opacity:0;transform:translateY(10px)}100%{opacity:1;transform:translateY(0)}}"
    b = [open_]
    b.append(f'<g style="animation:up .8s .05s {EASE} both">' + text(PAD, 50, c["name"], 24, fill=t["ink"], weight=800, family=DISPLAY)
             + text(PAD, 74, c["result"], 14, fill=t["amber"] if dark else "#B7791F", weight=600, family=BODY) + "</g>")
    m = tag(W - PAD - (m600.width(c["tag"], 10.5, 1.2) + 20), 34, c["tag"], t)
    b.append(m)
    for k, (lab, lines, hot, yy, h) in enumerate(laid):
        g = [f'<g style="animation:up .8s {0.2 + k*0.12:.2f}s {EASE} both">']
        if hot:
            g.append(f'<rect x="{PAD}" y="{yy-6}" width="{W-PAD*2}" height="{h}" rx="12" fill="{t["magenta"]}" fill-opacity="{0.1 if not dark else 0.16}" stroke="{t["magenta"]}" stroke-opacity=".35"/>')
        else:
            g.append(f'<rect x="{PAD}" y="{yy+h-2}" width="{W-PAD*2}" height="1" fill="{t["line"]}" opacity=".8"/>')
        lx = PAD + (12 if hot else 0)
        g.append(text(lx, yy + 14, lab, 10.5, fill=t["magenta"] if hot else t["faint"], weight=600, family=MONO, spacing=1.2))
        for j, ln in enumerate(lines):
            g.append(text(PAD + LAB + (12 if hot else 0), yy + 14 + j * 21, ln, 14.5, fill=t["ink"], weight=500, family=BODY))
        g.append("</g>"); b.append("".join(g))
    b.append(close)
    return svg(W, H, "".join(b), style=css, defs=defs,
               font_specs=(("Bricolage Grotesque", 800), ("Hanken Grotesk", 500), ("Hanken Grotesk", 600), ("JetBrains Mono", 600)), aria=c["name"])


# --------------------------------------------------------------------------- #
# hard problems grid
# --------------------------------------------------------------------------- #
def problems(t: dict) -> str:
    W = 1200
    h500, d800, m600 = font("Hanken Grotesk", 500), font("Bricolage Grotesque", 800), font("JetBrains Mono", 600)
    cols, gap, PAD = 3, 18, 28
    cw = (W - PAD * 2 - gap * (cols - 1)) / cols
    cells = []
    for i, (tg, title, body) in enumerate(PROBLEMS):
        lines = wrap(body, h500, 14, cw - 48)
        cells.append((tg, title, lines))
    rh = [max(96 + len(cells[r*cols + k][2]) * 20 for k in range(cols)) for r in range(2)]
    H = int(PAD * 2 + sum(rh) + gap)
    defs, css, open_, close = frame(t, W, H, "pb")
    css += "@keyframes pop{0%{opacity:0;transform:translateY(12px) scale(.97)}100%{opacity:1;transform:translateY(0) scale(1)}}"
    sc, sd, sb = shimmer(W, H, dur=12, opacity=0.5 if not t["name"].endswith("dark") else 0.07)
    css += sc; defs += sd
    b = [open_]
    y = PAD
    for r in range(2):
        for k in range(cols):
            i = r * cols + k; tg, title, lines = cells[i]
            x = PAD + k * (cw + gap)
            inner = [glass(x, y, cw, rh[r], 18, t, fill=t["glass"] if not t["name"].endswith("dark") else t["glass2"]),
                     tag(x + 22, y + 22, tg, t),
                     text(x + 22, y + 72, title, 18, fill=t["ink"], weight=800, family=DISPLAY)]
            for j, ln in enumerate(lines):
                inner.append(text(x + 22, y + 96 + j * 20, ln, 14, fill=t["muted"], weight=500, family=BODY))
            b.append(f'<g style="transform-origin:{x+cw/2:.0f}px {y+rh[r]/2:.0f}px;animation:pop .8s {0.08*i:.2f}s {EASE} both">{"".join(inner)}</g>')
        y += rh[r] + gap
    b.append(sb); b.append(close)
    return svg(W, H, "".join(b), style=css, defs=defs,
               font_specs=(("Bricolage Grotesque", 800), ("Hanken Grotesk", 500), ("JetBrains Mono", 600)), aria="Hard problems we ship through")


# --------------------------------------------------------------------------- #
# approach steps
# --------------------------------------------------------------------------- #
def approach(t: dict) -> str:
    W, H = 1200, 250
    h500, d800 = font("Hanken Grotesk", 500), font("Bricolage Grotesque", 800)
    defs, css, open_, close = frame(t, W, H, "ap")
    defs += glow_filter("ag", 8)
    css += "@keyframes up{0%{opacity:0;transform:translateY(10px)}100%{opacity:1;transform:translateY(0)}}@keyframes ring{0%{r:16;opacity:.7}100%{r:30;opacity:0}}"
    b = [open_]
    n = len(STEPS); PAD = 150
    xs = [PAD + i * ((W - 2 * PAD) / (n - 1)) for i in range(n)]
    ly = 70
    b.append(f'<path d="M{xs[0]} {ly} H{xs[-1]}" stroke="{t["line2"]}" stroke-width="2" stroke-dasharray="4 7"/>')
    b.append(f'<circle cy="{ly}" r="7" fill="{t["amber"]}" filter="url(#ag)"><animate attributeName="cx" values="{xs[0]};{xs[-1]}" dur="6s" repeatCount="indefinite" calcMode="spline" keySplines="0.45 0 0.55 1" keyTimes="0;1"/>'
             f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.06;0.94;1" dur="6s" repeatCount="indefinite"/></circle>')
    colw = (W - 2 * PAD) / (n - 1)
    for i, (x, (title, body)) in enumerate(zip(xs, STEPS)):
        g = [f'<g style="animation:up .9s {0.15+i*0.15:.2f}s {EASE} both">',
             f'<circle cx="{x:.0f}" cy="{ly}" r="16" fill="{t["bg"]}" stroke="{t["amber"]}" stroke-width="2.5"/>',
             f'<circle cx="{x:.0f}" cy="{ly}" r="16" fill="none" stroke="{t["amber"]}" style="animation:ring 2.8s {i*0.7:.1f}s ease-out infinite"/>',
             text(x, ly + 5, f"0{i+1}", 12, fill=t["ink"], weight=600, family=MONO, anchor="middle"),
             text(x, ly + 54, title, 19, fill=t["ink"], weight=800, family=DISPLAY, anchor="middle")]
        for j, ln in enumerate(wrap(body, h500, 13.5, colw - 24)):
            g.append(text(x, ly + 80 + j * 19, ln, 13.5, fill=t["muted"], weight=500, family=BODY, anchor="middle"))
        g.append("</g>"); b.append("".join(g))
    b.append(close)
    return svg(W, H, "".join(b), style=css, defs=defs,
               font_specs=(("Bricolage Grotesque", 800), ("Hanken Grotesk", 500), ("JetBrains Mono", 600)), aria="How we work")


# --------------------------------------------------------------------------- #
# buttons + footer
# --------------------------------------------------------------------------- #
BUTTONS = {"call": (None, "Book a call  →", True), "linkedin": ("linkedin", "LinkedIn", False),
           "website": (None, "blocship.io", False), "github": ("github", "GitHub", False)}


def button(t: dict, ic, label, primary) -> str:
    d800 = font("Bricolage Grotesque", 800)
    H = 56; tw = d800.width(label, 16)
    W = int(24 + (22 + 12 if ic else 0) + tw + 26)
    dark = t["name"].endswith("dark")
    fill = t["amber"] if primary else (t["glass"] if not dark else t["glass2"])
    ink = "#1F1D1A" if primary else t["ink"]
    sc, sd, sb = shimmer(W, H, dur=6, opacity=0.35 if primary or not dark else 0.1)
    defs = sd + f'<clipPath id="bc"><rect width="{W}" height="{H}" rx="16"/></clipPath><linearGradient id="bb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["amber"]}"/><stop offset="1" stop-color="{t["magenta"]}"/></linearGradient>'
    b = [f'<g clip-path="url(#bc)"><rect width="{W}" height="{H}" rx="16" fill="{fill}"/>',
         icon(ic, 35, H / 2, 22, ink) if ic else "",
         text(24 + (34 if ic else 0), H / 2 + 6, label, 16, fill=ink, weight=800, family=DISPLAY), sb, "</g>",
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="15.5" fill="none" stroke="{t["line2"] if not primary else "none"}"/>']
    if not primary: b.append(border_beam(0.5, 0.5, W - 1, H - 1, 15.5, gid="bb", seg=60, dur=4.5, width=1.4))
    return svg(W, H, "".join(b), style=sc, defs=defs, font_specs=(("Bricolage Grotesque", 800),), aria=label)


def footer(t: dict) -> str:
    W, H = 1200, 200
    d800, h500 = font("Bricolage Grotesque", 800), font("Hanken Grotesk", 500)
    defs, css, open_, close = frame(t, W, H, "ft")
    defs += logo_defs()
    css += "@keyframes up{0%{opacity:0;transform:translateY(10px)}100%{opacity:1;transform:translateY(0)}}@keyframes wave{0%{transform:translateX(0)}100%{transform:translateX(-300px)}}"
    b = [open_]
    # moving amber wave band
    pts = "".join(f" C{x+75} {150+18*((i%2)*2-1)} {x+75} {150-18*((i%2)*2-1)} {x+150} 150" for i, x in enumerate(range(0, 1800, 150)))
    b.append(f'<path d="M0 150{pts} L1800 {H} L0 {H} Z" fill="{t["amber"]}" opacity=".9" style="animation:wave 9s linear infinite"/>')
    b.append(f'<path d="M0 162{pts.replace("150", "162").replace("132", "148").replace("168", "176")} L1800 {H} L0 {H} Z" fill="{t["violet"]}" opacity=".55" style="animation:wave 13s linear infinite"/>')
    b.append(f'<g style="animation:up 1s .2s {EASE} both">' + logo_mark(W / 2 - 150, 48, 40)
             + text(W / 2 - 98, 80, "blocship", 34, fill=t["ink"], weight=800, family=DISPLAY)
             + text(W / 2, 118, "A founder-led Flutter and full-stack AI studio. You work with the person who designs your architecture.", 14.5, fill=t["muted"], weight=500, family=BODY, anchor="middle") + "</g>")
    b.append(close)
    return svg(W, H, "".join(b), style=css, defs=defs, font_specs=(("Bricolage Grotesque", 800), ("Hanken Grotesk", 500)), aria="Blocship")


# --------------------------------------------------------------------------- #
def main():
    for t in (THEMES[v] for v in VARIANTS):
        sfx = "" if t["name"] == "brand" else "-dark"
        write(OUT / f"hero{sfx}.svg", hero(t))
        write(OUT / f"problems{sfx}.svg", problems(t))
        write(OUT / f"approach{sfx}.svg", approach(t))
        write(OUT / f"footer{sfx}.svg", footer(t))
        for i, c in enumerate(CASES):
            write(OUT / "cases" / f"{i+1}{sfx}.svg", case(t, c, i))
        for key, (idx, title, cap) in SECTIONS.items():
            write(OUT / "headers" / f"{key}{sfx}.svg", header(t, idx, title, cap))
        for key, (ic, label, primary) in BUTTONS.items():
            write(OUT / "buttons" / f"{key}{sfx}.svg", button(t, ic, label, primary))


if __name__ == "__main__":
    main()
