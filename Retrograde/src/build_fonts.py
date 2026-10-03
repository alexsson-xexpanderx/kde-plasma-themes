"""The theme's font: Departure Mono, a pixel font by Helena Zhang, shipped
with its licence (SIL OFL 1.1) from src/fonts.

A pixel font is sharp only at sizes where each of its pixels covers a whole
number of screen pixels.  Departure Mono is drawn eleven pixels to the em, so
on the 115% display this theme is made on it is sharp at 14.35 pt: 22 screen
pixels, two to a font pixel.  At 12 pt the font's pixels fall between screen
pixels and the strokes come out uneven and soft; the next sharp size down,
7.17 pt, is too small to read.  It has one weight, so nothing is set bold:
KDE would make the bold up by smearing it.
"""

import shutil
from pathlib import Path

import palette as P

HERE = Path(__file__).resolve().parent
FILES = ["DepartureMono-Regular.otf", "DepartureMono-OFL.txt"]

FAMILY = "Departure Mono"
EM = 11        # font pixels to the em
SCALE = 1.15   # the display scale the size is worked out for
DPI = 96       # Qt's logical dots per inch, at which a point is 4/3 px


def points(n):
    """The point size at which one font pixel is n x n screen pixels."""
    return round(n * EM / SCALE * 72 / DPI, 4)


SIZE = points(2)


def qfont(size=SIZE):
    """The font as kdeglobals and Konsole store one (Qt 6's QFont::toString)."""
    return "%s,%s,-1,5,400,0,0,0,0,0,0,0,0,0,0,1" % (FAMILY, size)


def build(out):
    d = Path(out) / "fonts" / P.NAME
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for name in FILES:
        shutil.copy2(HERE / "fonts" / name, d / name)


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "theme")
    print(qfont())
