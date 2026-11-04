#!/usr/bin/env python3
"""Build dark-mode twins (*-dark.svg) of the static De Stijl assets.

Dark mode inverts the non-colors only: black grid lines become white so the
structure stays visible on GitHub's dark canvas, and white fields become black.
Red, blue and yellow are untouched.
"""
import re
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
STATIC = ["header", "rule", "footer", "block-red", "block-yellow", "block-blue"]
SWAP = {"#111111": "#FFFFFF", "#FFFFFF": "#111111", "#F8F9FA": "#000000"}


def invert(svg: str) -> str:
    return re.sub(r"#(?:111111|FFFFFF|F8F9FA)\b", lambda m: SWAP[m.group(0).upper()], svg, flags=re.I)


for name in STATIC:
    src = ASSETS / f"{name}.svg"
    (ASSETS / f"{name}-dark.svg").write_text(invert(src.read_text()), encoding="utf-8")
    print(f"wrote {name}-dark.svg")
