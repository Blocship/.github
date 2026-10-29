"""Live open-source cards for the Blocship org profile (runs in CI -> dist/)."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgkit import BODY, DISPLAY, MONO, THEMES, border_beam, font, glass, glow_filter, icon, svg, text  # noqa: E402

TOKEN = os.environ.get("GITHUB_TOKEN")
REPOS = [("Blocship", "stories_page_view"), ("Blocship", "blocship_logger"), ("Blocship", "code_keg"), ("Blocship", "readmore")]
EASE = "cubic-bezier(.22,1,.36,1)"


def gql(q, **v):
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": q, "variables": v}).encode(),
                                 headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "blocship-oss"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if "errors" in out: raise SystemExit(out["errors"])
    return out["data"]


Q = "query($o:String!,$n:String!){repository(owner:$o,name:$n){name nameWithOwner description url stargazerCount forkCount primaryLanguage{name color}}}"


def wrap(s, f, size, max_w, max_lines=3):
    lines, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if f.width(t, size) <= max_w: cur = t
        else:
            lines.append(cur); cur = w
            if len(lines) == max_lines: break
    if len(lines) < max_lines and cur: lines.append(cur)
    if len(lines) == max_lines and len(" ".join(lines)) < len(s):
        last = lines[-1]
        while f.width(last + "…", size) > max_w and last: last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def cards(t, repos):
    n = max(len(repos), 1); W, H = 1200, 236
    d800, h500, m600 = font("Bricolage Grotesque", 800), font("Hanken Grotesk", 500), font("JetBrains Mono", 600)
    dark = t["name"].endswith("dark")
    defs = [f'<linearGradient id="bb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["amber"]}"/><stop offset="1" stop-color="{t["magenta"]}"/></linearGradient>', glow_filter("sg", 6)]
    css = ("@keyframes up{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:translateY(0)}}"
           "@keyframes twinkle{0%,100%{transform:scale(1) rotate(0deg)}50%{transform:scale(1.25) rotate(18deg)}}")
    gap = 20; cw = (W - gap * (n - 1)) / n
    b = []
    for i, r in enumerate(repos):
        x = i * (cw + gap); lang = r.get("primaryLanguage") or {}
        defs.append(f'<clipPath id="c{i}"><rect x="{x:.1f}" y="0" width="{cw:.1f}" height="{H}" rx="22"/></clipPath>')
        b.append(f'<g style="animation:up .9s {0.1+i*0.12:.2f}s {EASE} both">')
        b.append(f'<g clip-path="url(#c{i})">' + glass(x, 0, cw, H, 22, t, fill="#fff" if not dark else t["glass2"], stroke="none")
                 + f'<circle cx="{x+cw-16}" cy="-14" r="92" fill="{t["amber"]}" opacity="{0.18 if not dark else 0.12}"/></g>')
        b.append(f'<rect x="{x+0.5}" y="0.5" width="{cw-1:.1f}" height="{H-1}" rx="21.5" fill="none" stroke="{t["line"]}"/>')
        b.append(border_beam(x + 0.5, 0.5, cw - 1, H - 1, 21.5, gid="bb", seg=100, dur=6, delay=-i * 1.5, width=1.3))
        b.append(icon("github", x + 36, 42, 20, t["icon"]))
        b.append(text(x + 54, 39, r["nameWithOwner"].split("/")[0] + " /", 12.5, fill=t["muted"], weight=600, family=MONO))
        size = 22
        while d800.width(r["name"], size) > cw - 48 and size > 14: size -= 1
        b.append(text(x + 24, 78, r["name"], size, fill=t["ink"], weight=800, family=DISPLAY))
        for j, ln in enumerate(wrap(r.get("description") or "No description yet.", h500, 13.5, cw - 48)):
            b.append(text(x + 24, 106 + j * 20, ln, 13.5, fill=t["muted"], weight=500, family=BODY))
        yb = H - 30
        if lang:
            b.append(f'<circle cx="{x+30}" cy="{yb-4}" r="5.5" fill="{lang.get("color") or t["muted"]}"/>' + text(x + 42, yb, lang["name"], 12.5, fill=t["ink"], weight=600, family=MONO))
        sx = x + cw - 24
        b.append(text(sx, yb, f"{r['forkCount']} forks", 12.5, fill=t["muted"], weight=600, family=MONO, anchor="end"))
        fw = m600.width(f"{r['forkCount']} forks", 12.5)
        stx = sx - fw - 18
        b.append(text(stx, yb, str(r["stargazerCount"]), 12.5, fill=t["ink"], weight=600, family=MONO, anchor="end"))
        sw = m600.width(str(r["stargazerCount"]), 12.5)
        star = f'M{stx-sw-12:.1f} {yb-11} l2.2 4.6 5 .7-3.6 3.5.9 5-4.5-2.4-4.5 2.4.9-5-3.6-3.5 5-.7z'
        b.append(f'<g style="transform-origin:{stx-sw-12:.1f}px {yb-4}px;animation:twinkle 2.6s {i*0.4:.1f}s ease-in-out infinite">'
                 f'<path d="{star}" fill="{t["amber"]}" filter="url(#sg)" opacity=".7"/><path d="{star}" fill="{t["amber"]}"/></g></g>')
    return svg(W, H, "".join(b), style=css, defs="".join(defs),
               font_specs=(("Bricolage Grotesque", 800), ("Hanken Grotesk", 500), ("JetBrains Mono", 600)), aria="Open-source packages")


def main(out="dist"):
    repos = [gql(Q, o=o, n=n)["repository"] for o, n in REPOS]
    repos = [r for r in repos if r]
    o = Path(out); o.mkdir(exist_ok=True)
    for key in ("brand", "brand-dark"):
        sfx = "" if key == "brand" else "-dark"
        (o / f"oss{sfx}.svg").write_text(cards(THEMES[key], repos), encoding="utf-8")
        print("wrote", o / f"oss{sfx}.svg")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist")
