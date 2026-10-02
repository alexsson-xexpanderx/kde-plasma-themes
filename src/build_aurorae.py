"""Window decoration (Aurorae).

The look: a dark title bar with the sunset drawn as five one-pixel stripes
across the top of the active window; top corners rounded the way 8-bit art
rounds them, in two-pixel steps; a hard drop shadow offset down and to the
right, as on a 1980s desktop; and buttons that are pixel-art planets, which
show their glyph when the pointer is over them.

The frame is drawn once as a whole small window, pixel by pixel, and then cut
into the nine pieces Aurorae stretches.  That way the stepped corners, the
outline and the shadow are guaranteed to line up across the cuts.
"""

import math
from pathlib import Path

import palette as P
from svgkit import Document

# Geometry, in pixels at 100% scale.
UNIT = 2            # one "art pixel"
SHADOW = 4          # hard shadow offset
CORNER = 6          # width of the corner pieces
TITLE = 32          # full title bar height, stripes included
BAND = len(P.SUNSET)
BUTTON = 9 * UNIT   # buttons are 9x9 art pixels
TITLE_MAX = 30      # title bar height when maximised (no corner rounding)

# How far in each row of the top corners is cut away, top row first.
STEP = [4, 4, 2, 2]

OUTLINE_ACTIVE = P.mix(P.MAUVE, P.CRUST, 0.70)
OUTLINE_INACTIVE = P.SURFACE1
SHADOW_ALPHA = 0.55


def band_colours(active):
    if active:
        return list(P.SUNSET)
    return [P.mix(c, P.CRUST, 0.80) for c in P.SUNSET]


def window_pixels(active):
    """A whole sample window, its outline and its shadow, as a grid of
    (colour, alpha) or None.  The middle row and column are what the edges
    stretch."""
    L, R = CORNER, CORNER + SHADOW
    B = CORNER + SHADOW
    FW, FH = L + 1 + R, TITLE + 1 + B
    WW, WH = FW - SHADOW, FH - SHADOW          # the window itself
    outline = OUTLINE_ACTIVE if active else OUTLINE_INACTIVE
    band = band_colours(active)

    def inside(x, y):
        if not (0 <= x < WW and 0 <= y < WH):
            return False
        if y < len(STEP):
            cut = STEP[y]
            return cut <= x < WW - cut
        return True

    grid = [[None] * FW for _ in range(FH)]
    for y in range(FH):
        for x in range(FW):
            if inside(x, y):
                if y < BAND:
                    grid[y][x] = (band[y], 1.0)
                elif y < TITLE:
                    edge = x == 0 or x == WW - 1
                    grid[y][x] = (outline if edge else P.CRUST, 1.0)
                else:
                    edge = x == 0 or x == WW - 1 or y == WH - 1
                    grid[y][x] = (outline, 1.0) if edge else None   # client area
            elif inside(x - SHADOW, y - SHADOW):
                grid[y][x] = ("#000000", SHADOW_ALPHA)
    return grid, L, R, B, FW, FH


def put(doc, gid, grid, x0, y0, x1, y1, at):
    """Copy grid[y0:y1][x0:x1] into a group placed at `at`."""
    g = doc.group(gid, at[0], at[1], x1 - x0, y1 - y0)
    g.grid([row[x0:x1] for row in grid[y0:y1]])
    return g


def decoration_svg():
    doc = Document(400, 200)
    doc.group("hint-stretch-borders", 390, 190, 4, 4)
    col = 0
    for prefix, active in (("decoration", True), ("decoration-inactive", False)):
        grid, L, R, B, FW, FH = window_pixels(active)
        T = TITLE
        ox, oy = col, 0
        cuts = {
            "topleft": (0, 0, L, T), "top": (L, 0, L + 1, T), "topright": (L + 1, 0, FW, T),
            "left": (0, T, L, T + 1), "center": (L, T, L + 1, T + 1), "right": (L + 1, T, FW, T + 1),
            "bottomleft": (0, T + 1, L, FH), "bottom": (L, T + 1, L + 1, FH),
            "bottomright": (L + 1, T + 1, FW, FH),
        }
        for name, (x0, y0, x1, y1) in cuts.items():
            # Spread the pieces out a little so their boxes never touch.
            at = (ox + x0 + {0: 0, L: 4, L + 1: 8}.get(x0, 8),
                  oy + y0 + {0: 0, T: 4, T + 1: 8}.get(y0, 8))
            put(doc, "%s-%s" % (prefix, name), grid, x0, y0, x1, y1, at)
        col += 60

    # Maximised: no corners, no outline, no shadow -- just the bar.
    for prefix, active in (("decoration-maximized", True),
                           ("decoration-maximized-inactive", False)):
        g = doc.group(prefix + "-center", col, 0, 20, TITLE_MAX)
        for i, c in enumerate(band_colours(active)):
            g.rect(0, i, 20, 1, c)
        g.rect(0, BAND, 20, TITLE_MAX - BAND, P.CRUST)
        col += 30
    return doc.svg()


# ---------------------------------------------------------------- buttons

def planet(colour, lit=0.0):
    """A 9x9 pixel planet lit from the upper left, as rows of tone keys.
    Tones: h highlight, l light, b base, s shade, d deep shade."""
    rows = []
    lx, ly, lz = -0.55, -0.65, 0.55
    n = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / n, ly / n, lz / n
    r = 4.5
    for y in range(9):
        row = ""
        for x in range(9):
            dx, dy = x - 4, y - 4
            if dx * dx + dy * dy > r * r:
                row += "."
                continue
            # Sample at the pixel centre, on a sphere of radius r.
            sx, sy = dx / r, dy / r
            sz = math.sqrt(max(0.0, 1 - sx * sx - sy * sy))
            v = sx * lx + sy * ly + sz * lz + lit
            row += ("h" if v > 0.93 else "l" if v > 0.70 else
                    "b" if v > 0.30 else "s" if v > 0.0 else "d")
        rows.append(row)
    return rows


def tones(colour, dim=False):
    if dim:
        return {"h": P.mix(colour, P.CRUST, 0.35), "l": P.mix(colour, P.CRUST, 0.45),
                "b": P.mix(colour, P.CRUST, 0.55), "s": P.mix(colour, P.CRUST, 0.68),
                "d": P.mix(colour, P.CRUST, 0.78)}
    return {"h": P.mix(colour, "#FFFFFF", 0.55), "l": P.mix(colour, "#FFFFFF", 0.22),
            "b": colour, "s": P.mix(colour, P.VOID, 0.35), "d": P.mix(colour, P.VOID, 0.58)}


GLYPHS = {
    "close": [".........", ".........", "..x...x..", "...x.x...", "....x....",
              "...x.x...", "..x...x..", ".........", "........."],
    "maximize": [".........", ".........", "..xxxxx..", "..x...x..", "..x...x..",
                 "..x...x..", "..xxxxx..", ".........", "........."],
    "restore": [".........", ".........", ".........", "...xxx...", "...x.x...",
                "...xxx...", ".........", ".........", "........."],
    "minimize": [".........", ".........", ".........", ".........", ".........",
                 ".........", "..xxxxx..", ".........", "........."],
    "alldesktops": [".........", ".........", "..x...x..", ".........", "....x....",
                    ".........", "..x...x..", ".........", "........."],
    "keepabove": [".........", ".........", ".........", "....x....", "...x.x...",
                  "..x...x..", ".........", ".........", "........."],
    "keepbelow": [".........", ".........", ".........", "..x...x..", "...x.x...",
                  "....x....", ".........", ".........", "........."],
    "shade": [".........", ".........", "..xxxxx..", ".........", "....x....",
              "...x.x...", "..x...x..", ".........", "........."],
    "help": [".........", "...xxx...", "..x...x..", "......x..", ".....x...",
             "....x....", ".........", "....x....", "........."],
}

BUTTON_COLOUR = {
    "close": P.PINK, "maximize": P.AMBER, "restore": P.AMBER, "minimize": P.MAUVE,
    "alldesktops": P.MINT, "keepabove": P.SKY, "keepbelow": P.SKY,
    "shade": P.BLUE, "help": P.GOLD,
}


def button_svg(kind):
    colour = BUTTON_COLOUR[kind]
    glyph = GLYPHS[kind]
    grey = P.SURFACE2
    states = [
        # element prefix,    planet colour, dim,   lit,   glyph colour
        ("active",           colour,  False, 0.0,  None),
        ("hover",            colour,  False, 0.25, P.VOID),
        ("pressed",          colour,  True,  0.0,  P.VOID),
        ("deactivated",      grey,    True,  0.0,  None),
        ("inactive",         grey,    False, 0.0,  None),
        ("hover-inactive",   colour,  False, 0.25, P.VOID),
        ("pressed-inactive", colour,  True,  0.0,  P.VOID),
        ("deactivated-inactive", grey, True, 0.0,  None),
    ]
    doc = Document(len(states) * (BUTTON + 4), BUTTON)
    for i, (prefix, c, dim, lit, gc) in enumerate(states):
        g = doc.group(prefix + "-center", i * (BUTTON + 4), 0, BUTTON, BUTTON)
        g.pixels(planet(c, lit), tones(c, dim), unit=UNIT)
        if gc:
            g.pixels(glyph, {"x": (gc, 0.92)}, unit=UNIT)
    return doc.svg()


def rc():
    return "\n".join([
        "[General]",
        "ActiveTextColor=%s" % P.csv(P.TEXT),
        "InactiveTextColor=%s" % P.csv(P.OVERLAY1),
        "UseTextShadow=false",
        "TitleAlignment=Center",
        "TitleVerticalAlignment=Center",
        "Animation=90",
        "LeftButtons=MS",
        "RightButtons=IAX",
        "Shadow=true",
        "",
        "[Layout]",
        "BorderLeft=1",
        "BorderRight=1",
        "BorderBottom=1",
        "BorderLeftMaximized=0",
        "BorderRightMaximized=0",
        "BorderBottomMaximized=0",
        "TitleEdgeTop=%d" % (BAND + 4),
        "TitleEdgeBottom=%d" % (TITLE - BAND - 4 - BUTTON),
        "TitleEdgeLeft=10",
        "TitleEdgeRight=10",
        "TitleEdgeTopMaximized=%d" % (BAND + 2),
        "TitleEdgeBottomMaximized=%d" % (TITLE_MAX - BAND - 2 - BUTTON),
        "TitleEdgeLeftMaximized=10",
        "TitleEdgeRightMaximized=10",
        "TitleBorderLeft=10",
        "TitleBorderRight=10",
        "TitleHeight=%d" % BUTTON,
        "ButtonWidth=%d" % BUTTON,
        "ButtonHeight=%d" % BUTTON,
        "ButtonSpacing=6",
        "ButtonMarginTop=0",
        "ExplicitButtonSpacer=10",
        "PaddingTop=0",
        "PaddingLeft=0",
        "PaddingRight=%d" % SHADOW,
        "PaddingBottom=%d" % SHADOW,
        "",
    ])


def metadata():
    return "\n".join([
        "[Desktop Entry]",
        "Name=%s" % P.NAME,
        "Comment=Pixel planets and a sunset stripe",
        "X-KDE-PluginInfo-Author=%s" % P.AUTHOR,
        "X-KDE-PluginInfo-Name=%s" % P.NAME,
        "X-KDE-PluginInfo-Version=%s" % P.VERSION,
        "X-KDE-PluginInfo-License=GPLv3",
        "X-KDE-PluginInfo-EnabledByDefault=true",
        "",
    ])


def build(out):
    d = Path(out) / "aurorae" / "themes" / P.NAME
    d.mkdir(parents=True, exist_ok=True)
    (d / "decoration.svg").write_text(decoration_svg())
    for kind in GLYPHS:
        (d / ("%s.svg" % kind)).write_text(button_svg(kind))
    (d / ("%src" % P.NAME)).write_text(rc())
    (d / "metadata.desktop").write_text(metadata())


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "theme")
    for row in planet(P.PINK):
        print(row)
