"""Plasma style (desktop theme): the panel, popups, tooltips, task manager,
and the controls Plasma's own widgets use.

Everything is built from one routine, frame_grid(), which draws a small
sample of a frame pixel by pixel -- corners rounded in steps the way 8-bit art
rounds them, a one-pixel outline that follows the steps, an optional bevel, an
optional sunset stripe across the top, an optional indicator bar along one
edge -- and cuts it into the nine pieces KSvg stretches.  Shadows are hard and
offset down and to the right, as on the windows.
"""

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import palette as P
from svgkit import Document

STEPS_BIG = [4, 4, 2, 2]     # same rounding as the window corners
STEPS_SMALL = [2, 1]


@dataclass
class Frame:
    corner: int = 6
    steps: list = field(default_factory=lambda: list(STEPS_BIG))
    fill: tuple = None            # (colour, alpha)
    outline: tuple = None         # (colour, alpha)
    band: list = None             # colours of the stripes across the top, top first
    bevel_top: tuple = None       # (colour, alpha) for the row inside the top outline
    bevel_bottom: tuple = None    # (colour, alpha, rows) along the bottom inside
    indicator: tuple = None       # (edge, thickness, colour, alpha, inset)
    margins: tuple = None         # content margins: top, right, bottom, left


def frame_grid(f):
    C = f.corner
    N = 2 * C + 1
    steps = f.steps

    def cut(i):
        return steps[i] if i < len(steps) else 0

    def inside(x, y):
        if not (0 <= x < N and 0 <= y < N):
            return False
        dy = min(y, N - 1 - y)
        c = cut(dy)
        return c <= x < N - c

    grid = [[None] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            if not inside(x, y):
                continue
            cell = f.fill
            edge = not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if f.bevel_top and y == 1 and not edge:
                cell = blend(cell, f.bevel_top)
            if f.bevel_bottom and N - 1 - y <= f.bevel_bottom[2] and not edge:
                cell = blend(cell, f.bevel_bottom[:2])
            if f.indicator:
                side, thick, colour, alpha, inset = f.indicator
                d = {"bottom": N - 1 - y, "top": y, "left": x, "right": N - 1 - x}[side]
                along = x if side in ("top", "bottom") else y
                if d < thick and inset <= along < N - inset:
                    cell = blend(cell, (colour, alpha))
            if edge and f.outline:
                cell = blend(cell, f.outline)
            if f.band and y < len(f.band):
                cell = (f.band[y], 1.0)
            grid[y][x] = cell
    return grid, N


def blend(under, over):
    """Composite (colour, alpha) over (colour, alpha); None is transparent."""
    if over is None:
        return under
    if under is None or over[1] >= 1:
        return over
    (cu, au), (co, ao) = under, over
    a = ao + au * (1 - ao)
    if a <= 0:
        return None
    ru, ro = P.rgb(cu), P.rgb(co)
    rgb = [(o * ao + u * au * (1 - ao)) / a for u, o in zip(ru, ro)]
    return (P.hexc(*rgb), round(a, 3))


PIECES = ["topleft", "top", "topright", "left", "center", "right",
          "bottomleft", "bottom", "bottomright"]


class Sheet:
    """Lays groups out left to right, wrapping, so no two boxes touch."""

    def __init__(self):
        self.doc = Document(2000, 2000)
        self.x, self.y, self.row_h = 0, 0, 0

    def place(self, w, h):
        if self.x + w > 1900:
            self.x, self.y, self.row_h = 0, self.y + self.row_h + 6, 0
        at = (self.x, self.y)
        self.x += w + 6
        self.row_h = max(self.row_h, h)
        return at

    def grid_group(self, gid, grid, x0, y0, x1, y1):
        at = self.place(x1 - x0, y1 - y0)
        g = self.doc.group(gid, at[0], at[1], x1 - x0, y1 - y0)
        g.grid([row[x0:x1] for row in grid[y0:y1]])
        return g

    def hint(self, gid, w, h):
        at = self.place(max(w, 1), max(h, 1))
        self.doc.group(gid, at[0], at[1], w, h)

    def frame(self, prefix, f):
        grid, N = frame_grid(f)
        self.cut(prefix, grid, N, f.corner, f.margins)

    def cut(self, prefix, grid, N, C, margins):
        cuts = {
            "topleft": (0, 0, C, C), "top": (C, 0, C + 1, C), "topright": (C + 1, 0, N, C),
            "left": (0, C, C, C + 1), "center": (C, C, C + 1, C + 1), "right": (C + 1, C, N, C + 1),
            "bottomleft": (0, C + 1, C, N), "bottom": (C, C + 1, C + 1, N),
            "bottomright": (C + 1, C + 1, N, N),
        }
        name = (lambda p: "%s-%s" % (prefix, p)) if prefix else (lambda p: p)
        for piece in PIECES:
            self.grid_group(name(piece), grid, *cuts[piece])
        if margins:
            t, r, b, l = margins
            self.hint(name("hint-top-margin"), 1, t)
            self.hint(name("hint-right-margin"), r, 1)
            self.hint(name("hint-bottom-margin"), 1, b)
            self.hint(name("hint-left-margin"), l, 1)

    def shadow(self, f, offset, alpha=0.5, colour="#000000"):
        """Hard shadow tiles for KWindowShadow: the frame's own silhouette
        moved down and right by `offset`, minus the frame itself."""
        C = f.corner
        N = 2 * C + 1
        O = offset
        steps = f.steps

        def cut(i):
            return steps[i] if i < len(steps) else 0

        def inside(x, y):
            if not (0 <= x < N and 0 <= y < N):
                return False
            dy = min(y, N - 1 - y)
            c = cut(dy)
            return c <= x < N - c

        # grid covers x, y in [-1, N + O)
        G = N + O + 1
        grid = [[None] * G for _ in range(G)]
        for gy in range(G):
            for gx in range(G):
                x, y = gx - 1, gy - 1
                if inside(x - O, y - O) and not inside(x, y):
                    grid[gy][gx] = (colour, alpha)
        # tile rectangles in grid coordinates (window at 1..N)
        L, T = 1, 1
        tiles = {
            "shadow-topleft": (0, 0, 1, 1),
            "shadow-top": (L + C, 0, L + C + 1, 1),
            "shadow-topright": (L + N - C, 0, G, T + C),
            "shadow-left": (0, T + C, 1, T + C + 1),
            "shadow-right": (L + N, T + C, G, T + C + 1),
            "shadow-bottomleft": (0, T + N - C, L + C, G),
            "shadow-bottom": (L + C, T + N, L + C + 1, G),
            "shadow-bottomright": (L + N - C, T + N - C, G, G),
        }
        for gid, (x0, y0, x1, y1) in tiles.items():
            self.grid_group(gid, grid, x0, y0, x1, y1)
        self.hint("shadow-hint-top-margin", 1, 1)
        self.hint("shadow-hint-left-margin", 1, 1)
        self.hint("shadow-hint-right-margin", O, 1)
        self.hint("shadow-hint-bottom-margin", 1, O)

    def svg(self):
        self.doc.height = self.y + self.row_h + 6
        return self.doc.svg()


def write(root, rel, sheet):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sheet.svg())


# ---------------------------------------------------------------- surfaces

OUTLINE = (P.mix(P.MAUVE, P.CRUST, 0.70), 1.0)
QUIET_OUTLINE = (P.SURFACE1, 1.0)


def dialog(alpha):
    return Frame(corner=6, fill=(P.MANTLE, alpha), outline=OUTLINE, band=list(P.SUNSET),
                 margins=(len(P.SUNSET) + 5, 7, 7, 7))


def panel(alpha):
    return Frame(corner=6, fill=(P.CRUST, alpha), outline=QUIET_OUTLINE,
                 bevel_top=(P.SURFACE0, 0.9), margins=(4, 4, 4, 4))


def tooltip(alpha):
    return Frame(corner=4, steps=list(STEPS_SMALL), fill=(P.CRUST, alpha),
                 outline=QUIET_OUTLINE, margins=(7, 9, 7, 9))


def widget_background(alpha):
    return Frame(corner=6, fill=(P.MANTLE, alpha), outline=OUTLINE, band=list(P.SUNSET),
                 margins=(len(P.SUNSET) + 6, 8, 8, 8))


def surface(sheet_fn, frame, shadow_offset, shadow_alpha=0.5):
    s = Sheet()
    s.frame("", frame)
    s.shadow(frame, shadow_offset, shadow_alpha)
    s.hint("hint-stretch-borders", 1, 1)
    return s


# ---------------------------------------------------------------- widgets

def tasks():
    s = Sheet()
    small = dict(corner=4, steps=list(STEPS_SMALL))
    states = {
        "normal": dict(indicator=None, ind=(P.OVERLAY1, 1.0), fill=None),
        "minimized": dict(ind=(P.SURFACE2, 1.0), fill=None),
        "hover": dict(ind=None, fill=(P.SURFACE0, 0.85)),
        "focus": dict(ind=(P.PINK, 1.0), fill=(P.BASE, 0.95)),
        "attention": dict(ind=(P.AMBER, 1.0), fill=(P.mix(P.AMBER, P.CRUST, 0.82), 0.95)),
        "progress": dict(ind=(P.MINT, 1.0), fill=(P.mix(P.MINT, P.CRUST, 0.80), 0.9)),
    }
    for orient, edge in (("", "bottom"), ("north-", "top"), ("west-", "left"), ("east-", "right")):
        for state, st in states.items():
            ind = st.get("ind")
            fr = Frame(fill=st["fill"], margins=(4, 6, 4, 6),
                       indicator=(edge, 2, ind[0], ind[1], 3) if ind else None, **small)
            s.frame(orient + state, fr)
    s.hint("hint-stretch-borders", 1, 1)
    return s


def viewitem():
    s = Sheet()
    small = dict(corner=4, steps=list(STEPS_SMALL), margins=(4, 6, 4, 6))
    s.frame("normal", Frame(**small))
    s.frame("hover", Frame(fill=(P.SURFACE1, 0.55), outline=(P.SURFACE2, 0.8), **small))
    s.frame("selected", Frame(fill=(P.PINK, 0.20), outline=(P.PINK, 0.75), **small))
    s.frame("selected+hover", Frame(fill=(P.PINK, 0.30), outline=(P.PINK, 0.95), **small))
    s.hint("hint-stretch-borders", 1, 1)
    return s


def button():
    s = Sheet()
    small = dict(corner=4, steps=list(STEPS_SMALL), margins=(5, 8, 6, 8))
    raised = dict(bevel_top=("#FFFFFF", 0.07), bevel_bottom=(P.VOID, 0.55, 1))
    s.frame("normal", Frame(fill=(P.BASE, 1.0), outline=(P.SURFACE2, 1.0), **raised, **small))
    s.frame("hover", Frame(outline=(P.PINK, 0.85), **small))
    s.frame("focus", Frame(outline=(P.PINK, 1.0), **small))
    s.frame("pressed", Frame(fill=(P.CRUST, 1.0), outline=(P.SURFACE2, 1.0),
                             bevel_top=(P.VOID, 0.7), **small))
    s.frame("toolbutton-hover", Frame(fill=(P.SURFACE0, 0.9), outline=(P.SURFACE1, 1.0), **small))
    s.frame("toolbutton-focus", Frame(outline=(P.PINK, 0.9), **small))
    s.frame("toolbutton-pressed", Frame(fill=(P.CRUST, 1.0), outline=(P.PINK, 0.7),
                                        bevel_top=(P.VOID, 0.7), **small))
    s.hint("hint-stretch-borders", 1, 1)
    return s


def lineedit():
    s = Sheet()
    small = dict(corner=4, steps=list(STEPS_SMALL), margins=(5, 8, 5, 8))
    s.frame("base", Frame(fill=(P.CRUST, 1.0), outline=(P.SURFACE1, 1.0),
                          bevel_top=(P.VOID, 0.8), **small))
    s.frame("hover", Frame(outline=(P.SURFACE2, 1.0), **small))
    s.frame("focus", Frame(outline=(P.PINK, 1.0), **small))
    s.frame("focusframe", Frame(outline=(P.PINK, 1.0), **small))
    s.hint("hint-focus-over-base", 1, 1)
    s.hint("hint-stretch-borders", 1, 1)
    return s


def plasmoidheading():
    """Header and footer strips in popups.  A heading is stretched out to the
    popup's own edges, so it keeps clear of what the popup draws there: the
    sunset stripe along the top and the one-pixel outline round the sides."""
    s = Sheet()
    band = len(P.SUNSET)
    C = band + 2
    for prefix, divider in (("header", "bottom"), ("footer", "top")):
        f = Frame(corner=C, steps=[], fill=(P.CRUST, 0.55),
                  indicator=(divider, 1, P.SURFACE1, 1.0, 1),
                  margins=(4, 6, 5, 6) if prefix == "header" else (5, 6, 4, 6))
        grid, N = frame_grid(f)
        for y in range(N):
            for x in range(N):
                clear_top = prefix == "header" and y < band
                clear_bottom = prefix == "footer" and y == N - 1
                if clear_top or clear_bottom or x == 0 or x == N - 1:
                    grid[y][x] = None
        s.cut(prefix, grid, N, C, f.margins)
    s.hint("hint-stretch-borders", 1, 1)
    return s


def frame_svg():
    s = Sheet()
    small = dict(corner=4, steps=list(STEPS_SMALL), margins=(4, 4, 4, 4))
    s.frame("plain", Frame(outline=(P.SURFACE1, 1.0), **small))
    s.frame("raised", Frame(fill=(P.BASE, 1.0), outline=(P.SURFACE2, 1.0),
                            bevel_top=("#FFFFFF", 0.06), bevel_bottom=(P.VOID, 0.5, 1), **small))
    s.frame("sunken", Frame(fill=(P.CRUST, 1.0), outline=(P.SURFACE1, 1.0),
                            bevel_top=(P.VOID, 0.8), **small))
    s.hint("hint-stretch-borders", 1, 1)
    return s


def menubaritem():
    s = Sheet()
    small = dict(corner=4, steps=list(STEPS_SMALL), margins=(4, 6, 4, 6))
    s.frame("normal", Frame(**small))
    s.frame("hover", Frame(fill=(P.SURFACE1, 0.6), **small))
    s.frame("pressed", Frame(fill=(P.PINK, 0.25), outline=(P.PINK, 0.8), **small))
    s.hint("hint-stretch-borders", 1, 1)
    return s


def listitem():
    s = Sheet()
    small = dict(corner=4, steps=list(STEPS_SMALL), margins=(4, 6, 4, 6))
    s.frame("normal", Frame(**small))
    s.frame("hover", Frame(fill=(P.SURFACE1, 0.55), **small))
    s.frame("pressed", Frame(fill=(P.PINK, 0.25), outline=(P.PINK, 0.8), **small))
    s.frame("section", Frame(indicator=("bottom", 1, P.SURFACE1, 1.0, 0), **small))
    g = s.doc.group("separator", *s.place(8, 1), 8, 1)
    g.rect(0, 0, 8, 1, P.SURFACE1)
    s.hint("hint-stretch-borders", 1, 1)
    return s


def tabbar():
    s = Sheet()
    for orient, edge in (("north", "bottom"), ("south", "top"), ("west", "right"), ("east", "left")):
        s.frame("%s-active-tab" % orient,
                Frame(corner=4, steps=list(STEPS_SMALL), fill=(P.SURFACE0, 0.9),
                      indicator=(edge, 2, P.PINK, 1.0, 2), margins=(4, 8, 4, 8)))
    s.hint("hint-stretch-borders", 1, 1)
    return s


def scrollbar():
    """Scrollbar: a thin groove and a chunky pixel slider."""
    s = Sheet()
    for orient in ("vertical", "horizontal"):
        s.frame("background-%s" % orient,
                Frame(corner=2, steps=[1], fill=(P.CRUST, 0.6)))
    knob = dict(corner=3, steps=[1])
    s.frame("slider", Frame(fill=(P.SURFACE2, 1.0), bevel_top=("#FFFFFF", 0.10), **knob))
    s.frame("mouseover-slider", Frame(fill=(P.mix(P.SURFACE2, P.PINK, 0.45), 1.0),
                                      bevel_top=("#FFFFFF", 0.12), **knob))
    s.frame("sunken-slider", Frame(fill=(P.PINK, 1.0), **knob))
    s.hint("hint-scrollbar-size", 10, 10)
    s.hint("hint-stretch-borders", 1, 1)
    return s


def bar_meter():
    """Progress bars as rows of lit cells, like an LED meter."""
    s = Sheet()
    s.frame("bar-inactive", Frame(corner=2, steps=[1], fill=(P.CRUST, 1.0),
                                  outline=(P.SURFACE1, 1.0)))
    s.frame("bar-active", Frame(corner=2, steps=[1], fill=(P.PINK, 1.0),
                                bevel_top=("#FFFFFF", 0.25)))
    s.hint("hint-bar-size", 6, 6)
    s.hint("hint-stretch-borders", 1, 1)
    return s


def slider():
    s = Sheet()
    d = s.doc

    def knob(gid, fill, ring=None):
        at = s.place(16, 16)
        g = d.group(gid, at[0], at[1], 16, 16)
        rows = ["...oooooooooo...", "..oFFFFFFFFFFo..", ".oFHHFFFFFFFFFo.", "oFHHFFFFFFFFFFSo",
                "oFHFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo",
                "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo",
                "oFFFFFFFFFFFFSSo", ".oFFFFFFFFFFSSo.", "..oSSSSSSSSSSo..", "...oooooooooo..."]
        g.pixels(rows, {"o": ring or P.VOID, "F": fill, "H": P.mix(fill, "#FFFFFF", 0.45),
                        "S": P.mix(fill, P.VOID, 0.35)})
    for orient in ("horizontal", "vertical"):
        knob("%s-slider-handle" % orient, P.TEXT)
        knob("%s-slider-hover" % orient, P.mix(P.TEXT, P.PINK, 0.35), P.PINK)
        knob("%s-slider-focus" % orient, P.mix(P.TEXT, P.PINK, 0.35), P.PINK)
        at = s.place(16, 16)
        d.group("%s-slider-shadow" % orient, at[0], at[1], 16, 16)
    s.hint("hint-handle-size", 16, 16)
    return s


def switch():
    s = Sheet()
    d = s.doc
    for state, fill in (("inactive", P.SURFACE1), ("active", P.PINK)):
        for piece, w in (("left", 4), ("center", 1), ("right", 4)):
            at = s.place(w, 12)
            g = d.group("%s-%s" % (state, piece), at[0], at[1], w, 12)
            if piece == "center":
                g.rect(0, 0, 1, 12, P.VOID)
                g.rect(0, 1, 1, 10, fill)
                g.rect(0, 1, 1, 1, "#FFFFFF", 0.12)
            else:
                rows = ["..oo", ".oFF", "oFHF", "oFFF", "oFFF", "oFFF", "oFFF", "oFFF",
                        "oFFF", "oFFF", ".oFF", "..oo"]
                if piece == "right":
                    rows = [r[::-1] for r in rows]
                g.pixels(rows, {"o": P.VOID, "F": fill, "H": P.mix(fill, "#FFFFFF", 0.12)})
    for gid, fill, ring in (("handle", P.TEXT, P.VOID), ("handle-hover", P.TEXT, P.PINK),
                            ("handle-focus", P.TEXT, P.PINK), ("handle-pressed", P.SUBTEXT, P.PINK)):
        at = s.place(16, 16)
        g = d.group(gid, at[0], at[1], 16, 16)
        rows = ["..oooooooooooo..", ".oFFFFFFFFFFFFo.", "oFHHFFFFFFFFFFFo", "oFHFFFFFFFFFFFSo",
                "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo",
                "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo", "oFFFFFFFFFFFFFSo",
                "oFFFFFFFFFFFFSSo", "oSSSSSSSSSSSSSSo", ".oSSSSSSSSSSSSo.", "..oooooooooooo.."]
        g.pixels(rows, {"o": ring, "F": fill, "H": "#FFFFFF", "S": P.mix(fill, P.VOID, 0.35)})
    at = s.place(16, 16)
    d.group("handle-shadow", at[0], at[1], 16, 16)
    s.hint("hint-bar-size", 12, 12)
    s.hint("hint-stretch-borders", 1, 1)
    return s


def checkmarks():
    """Plasma's own checkbox and radio marks, in pixels."""
    s = Sheet()
    d = s.doc
    at = s.place(16, 16)
    g = d.group("checkbox", at[0], at[1], 16, 16)
    g.pixels(["................", "................", "................", "............xx..",
              "...........xxx..", "..........xxx...", ".........xxx....", "..xx....xxx.....",
              "..xxx..xxx......", "...xxxxxx.......", "....xxxx........", ".....xx.........",
              "................", "................", "................", "................"],
             {"x": P.PINK})
    at = s.place(16, 16)
    g = d.group("radiobutton", at[0], at[1], 16, 16)
    g.pixels(["................", "................", "................", "................",
              "................", "......xxxx......", ".....xxxxxx.....", ".....xxxxxx.....",
              ".....xxxxxx.....", ".....xxxxxx.....", "......xxxx......", "................",
              "................", "................", "................", "................"],
             {"x": P.PINK})
    return s


def radiobutton():
    s = Sheet()
    d = s.doc
    ring = ["....oooooooo....", "..ooFFFFFFFFoo..", ".oFFFFFFFFFFFFo.", ".oFFFFFFFFFFFFo.",
            "oFFFFFFFFFFFFFFo", "oFFFFFFFFFFFFFFo", "oFFFFFFFFFFFFFFo", "oFFFFFFFFFFFFFFo",
            "oFFFFFFFFFFFFFFo", "oFFFFFFFFFFFFFFo", "oFFFFFFFFFFFFFFo", "oFFFFFFFFFFFFFFo",
            ".oFFFFFFFFFFFFo.", ".oFFFFFFFFFFFFo.", "..ooFFFFFFFFoo..", "....oooooooo...."]
    for gid, fill, line in (("normal", P.CRUST, P.SURFACE2), ("hover", P.CRUST, P.PINK),
                            ("focus", P.CRUST, P.PINK), ("checked", P.CRUST, P.PINK)):
        at = s.place(16, 16)
        d.group(gid, at[0], at[1], 16, 16).pixels(ring, {"o": line, "F": fill})
    at = s.place(16, 16)
    g = d.group("symbol", at[0], at[1], 16, 16)
    g.pixels(["................"] * 5 + ["......xxxx......", ".....xxxxxx.....", ".....xxxxxx.....",
              ".....xxxxxx.....", ".....xxxxxx.....", "......xxxx......"] + ["................"] * 5,
             {"x": P.PINK})
    at = s.place(16, 16)
    d.group("shadow", at[0], at[1], 16, 16)
    s.hint("hint-size", 16, 16)
    return s


def calendar():
    s = Sheet()
    at = s.place(8, 8)
    g = s.doc.group("event", at[0], at[1], 8, 8)
    g.pixels(["..xxxx..", ".xxxxxx.", "xxxxxxxx", "xxxxxxxx", "xxxxxxxx", "xxxxxxxx",
              ".xxxxxx.", "..xxxx.."], {"x": P.AMBER})
    return s


def busywidget():
    """A spinner: eight pixel dots on a ring, brighter towards the head.
    Plasma rotates the whole element."""
    s = Sheet()
    import math
    at = s.place(32, 32)
    g = s.doc.group("busywidget", at[0], at[1], 32, 32)
    for i in range(8):
        a = math.radians(i * 45)
        x, y = 16 + 11 * math.sin(a), 16 - 11 * math.cos(a)
        size = 4
        g.rect(round(x - size / 2), round(y - size / 2), size, size,
               P.mix(P.SURFACE2, P.PINK, i / 7), 0.35 + 0.65 * i / 7)
    s.hint("hint-rotation-angle", 45, 1)
    return s


# ---------------------------------------------------------------- package

def colors_file():
    # Plasma reads its colours from a file in the theme, in colour scheme
    # format; the application scheme is the same palette.
    from build_colors import colour_scheme
    return colour_scheme()


def metadata():
    return json.dumps({
        "KPlugin": {
            "Authors": [{"Name": P.AUTHOR}],
            "Category": "",
            "Description": "Pixel corners, a sunset stripe and hard shadows",
            "EnabledByDefault": True,
            "Id": P.NAME,
            "License": "GPL-3.0-or-later",
            "Name": P.NAME,
            "Version": P.VERSION,
        },
        "X-Plasma-API": "5.0",
    }, indent=4) + "\n"


def plasmarc():
    return "\n".join([
        "[AdaptiveTransparency]",
        "enabled=true",
        "",
        "[ContrastEffect]",
        "enabled=true",
        "contrast=0.35",
        "intensity=0.6",
        "saturation=1.4",
        "",
    ])


def build(out):
    root = Path(out) / "plasma" / "desktoptheme" / P.NAME
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    (root / "metadata.json").write_text(metadata())
    (root / "colors").write_text(colors_file())
    (root / "plasmarc").write_text(plasmarc())

    # Surfaces in three flavours: the default (lightly translucent, blurred
    # behind), opaque (no compositor) and solid (a panel set to opaque).
    for sub, alpha in (("", 0.94), ("opaque/", 1.0), ("solid/", 1.0)):
        write(root, sub + "dialogs/background.svg", surface(None, dialog(alpha), 4))
        write(root, sub + "widgets/panel-background.svg", surface(None, panel(alpha), 4))
        write(root, sub + "widgets/tooltip.svg", surface(None, tooltip(alpha), 3))
        write(root, sub + "widgets/background.svg", surface(None, widget_background(alpha), 4))
    write(root, "translucent/dialogs/background.svg", surface(None, dialog(0.88), 4))
    write(root, "translucent/widgets/panel-background.svg", surface(None, panel(0.86), 4))
    write(root, "translucent/widgets/tooltip.svg", surface(None, tooltip(0.92), 3))
    write(root, "translucent/widgets/background.svg", surface(None, widget_background(0.86), 4))

    for rel, sheet in (
        ("widgets/tasks.svg", tasks()), ("widgets/viewitem.svg", viewitem()),
        ("widgets/button.svg", button()), ("widgets/lineedit.svg", lineedit()),
        ("widgets/plasmoidheading.svg", plasmoidheading()), ("widgets/frame.svg", frame_svg()),
        ("widgets/menubaritem.svg", menubaritem()), ("widgets/listitem.svg", listitem()),
        ("widgets/tabbar.svg", tabbar()), ("widgets/scrollbar.svg", scrollbar()),
        ("widgets/bar_meter_horizontal.svg", bar_meter()), ("widgets/slider.svg", slider()),
        ("widgets/switch.svg", switch()), ("widgets/checkmarks.svg", checkmarks()),
        ("widgets/radiobutton.svg", radiobutton()), ("widgets/calendar.svg", calendar()),
        ("widgets/busywidget.svg", busywidget()),
    ):
        write(root, rel, sheet)


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "theme")
