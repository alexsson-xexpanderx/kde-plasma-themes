"""Pixel-art cursor theme.

Drawn on a 12 x 12 grid and enlarged by whole numbers only, so every size a
desktop offers -- 24, 36, 48, 60, 72, 96 -- is exactly 2, 3, 4, 5, 6 or 8
screen pixels per art pixel and nothing is ever smoothed.  The busy cursor is a
planet going round a striped sun.  Anything not drawn here comes from Breeze.

Needs xcursorgen.
"""

import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

import palette as P

GRID = 12
SIZES = [24, 36, 48, 60, 72, 96]

INK = {
    "o": P.VOID, "f": P.TEXT, "s": "#ABA5CE", "w": "#FFFFFF",
    "p": P.PINK, "g": P.GOLD, "a": P.AMBER, "m": P.MAUVE, "k": P.SKY, "r": P.RED,
    "c": P.CORAL,
}

ARROW = [
    "o...........",
    "oo..........",
    "ofo.........",
    "offo........",
    "offfo.......",
    "offffo......",
    "offfffo.....",
    "offffffo....",
    "offffoooo...",
    "offoofo.....",
    "oo..ofso....",
    "o....oo.....",
]

# Badges drawn over the arrow's lower right: (column, row, rows).
HELP = (7, 0, ["oooo.", "oggo.", "ooggo", ".ogoo", ".ooo.", ".ogo.", ".ooo."])
COPY = (7, 7, ["ooooo", "omwmo", "owwwo", "omwmo", "ooooo"])
ALIAS = (7, 7, ["ooooo", "o.wwo", "o.kwo", "okk.o", "ooooo"])
CONTEXT_MENU = (6, 5, ["oooooo", "offffo", "oooooo", "offffo", "oooooo", "offffo", "oooooo"])


def badge(spec):
    col, row, art = spec
    rows = [list(r) for r in ARROW]
    for j, line in enumerate(art):
        for i, ch in enumerate(line):
            if ch != "." and row + j < GRID and col + i < GRID:
                rows[row + j][col + i] = ch
    for j, line in enumerate(art):           # interiors left as '.' become fill
        for i, ch in enumerate(line):
            if ch == "." and 0 < i < len(line) - 1 and 0 < j < len(art) - 1:
                if row + j < GRID and col + i < GRID:
                    rows[row + j][col + i] = "o"
    return ["".join(r) for r in rows]


ART = {
    "default": ((0, 0), ARROW),
    "pointer": ((4, 0), [
        "...oo.......",
        "..offo......",
        "..offo......",
        "..offooo....",
        "..offofoooo.",
        "ooofffffofo.",
        "offfffffffo.",
        "offfffffffo.",
        ".offfffffso.",
        "..offffffso.",
        "...offfsso..",
        "....oooooo..",
    ]),
    "grab": ((6, 6), [
        "............",
        "....oooo....",
        "..oofofoo...",
        ".ofofofofo..",
        ".ofofofofo..",
        ".offfffffoo.",
        "oofffffffofo",
        "offffffffffo",
        ".offfffffffo",
        "..offfffffso",
        "...offffsso.",
        "....ooooooo.",
    ]),
    "grabbing": ((6, 6), [
        "............",
        "............",
        "............",
        "....oooooo..",
        "...ofofofoo.",
        "..oofffffofo",
        ".offfffffffo",
        ".offfffffffo",
        "..offfffffso",
        "...offffsso.",
        "....ooooooo.",
        "............",
    ]),
    "text": ((5, 6), [
        "..ooo.ooo...",
        "..offoffo...",
        "...oofoo....",
        "....ofo.....",
        "....ofo.....",
        "....ofo.....",
        "....ofo.....",
        "....ofo.....",
        "....ofo.....",
        "...oofoo....",
        "..offoffo...",
        "..ooo.ooo...",
    ]),
    "crosshair": ((5, 5), [
        ".....o......",
        "....oko.....",
        "....oko.....",
        "....oko.....",
        ".oooo.oooo..",
        "okkk.p.kkko.",
        ".oooo.oooo..",
        "....oko.....",
        "....oko.....",
        "....oko.....",
        ".....o......",
        "............",
    ]),
    "move": ((5, 5), [
        ".....o......",
        "....ofo.....",
        "...offfo....",
        "....ofo.....",
        ".o..ofo..o..",
        "offfffffffo.",
        ".o..ofo..o..",
        "....ofo.....",
        "...offfo....",
        "....ofo.....",
        ".....o......",
        "............",
    ]),
    "ns-resize": ((5, 5), [
        ".....o......",
        "....ofo.....",
        "...offfo....",
        "..offfffo...",
        "..ooofooo...",
        "....ofo.....",
        "....ofo.....",
        "..ooofooo...",
        "..offfffo...",
        "...offfo....",
        "....ofo.....",
        ".....o......",
    ]),
    "ew-resize": ((5, 5), [
        "............",
        "............",
        "............",
        "...o...o....",
        "..oo...oo...",
        ".ofooooofo..",
        "offfffffffo.",
        ".ofooooofo..",
        "..oo...oo...",
        "...o...o....",
        "............",
        "............",
    ]),
    "nwse-resize": ((5, 5), [
        "............",
        ".ooooo......",
        ".offfo......",
        ".offo.......",
        ".ofofo......",
        ".oo.ofo.....",
        ".....ofo.oo.",
        "......ofofo.",
        ".......offo.",
        "......offfo.",
        "......ooooo.",
        "............",
    ]),
    "not-allowed": ((5, 5), [
        "...ooooo....",
        "..orrrrro...",
        ".orroooorro.",
        "orro...orrro",
        "oro...orroro",
        "oro..orro.ro",
        "oro.orro..ro",
        "ororro...oro",
        "orrro...orro",
        ".orroooorro.",
        "..orrrrrro..",
        "...ooooooo..",
    ]),
    "help": ((0, 0), badge(HELP)),
    "copy": ((0, 0), badge(COPY)),
    "alias": ((0, 0), badge(ALIAS)),
    "context-menu": ((0, 0), badge(CONTEXT_MENU)),
    "zoom-in": ((4, 4), [
        "..oooo......",
        ".offffo.....",
        "offpfffo....",
        "ofppppfo....",
        "offpfffo....",
        "offffffo....",
        ".offffoo....",
        "..ooooooo...",
        "......ooo...",
        ".......ooo..",
        "........ooo.",
        ".........oo.",
    ]),
    "zoom-out": ((4, 4), [
        "..oooo......",
        ".offffo.....",
        "offffffo....",
        "ofppppfo....",
        "offffffo....",
        "offffffo....",
        ".offffoo....",
        "..ooooooo...",
        "......ooo...",
        ".......ooo..",
        "........ooo.",
        ".........oo.",
    ]),
}

# Name -> drawing.  These are the names Qt, GTK, browsers and X11 ask for.
ALIASES = {
    "default": ["left_ptr", "arrow", "top_left_arrow", "left_arrow", "right_ptr",
                "dnd-none", "center_ptr", "x-cursor", "X_cursor"],
    "pointer": ["hand", "hand1", "hand2", "pointing_hand", "9d800788f1b08800ae810202380a0822",
                "e29285e634086352946a0e7090d73106"],
    "grab": ["openhand", "fleur-open", "5aca4d189052212118709018842178c0",
             "9141b49c8149039304290b508d208c40"],
    "grabbing": ["closedhand", "dnd-move", "move-hand", "208530c400c041818281048008011002",
                 "fcf21c00b30f7e3f83fe0dfd12e71cff"],
    "text": ["xterm", "ibeam", "vertical-text"],
    "crosshair": ["cross", "tcross", "cross_reverse", "diamond_cross", "cell", "plus"],
    "move": ["fleur", "size_all", "all-scroll", "4498f0e0c1937ffe01fd06f973665830",
             "9081237383d90e509aa00f00170e968f"],
    "ns-resize": ["size_ver", "sb_v_double_arrow", "v_double_arrow", "n-resize", "s-resize",
                  "top_side", "bottom_side", "row-resize", "split_v", "double_arrow",
                  "00008160000006810000408080010102", "2870a09082c103050810ffdffffe0204"],
    "ew-resize": ["size_hor", "sb_h_double_arrow", "h_double_arrow", "e-resize", "w-resize",
                  "left_side", "right_side", "col-resize", "split_h",
                  "028006030e0e7ebffc7f7070c0600140", "14fef782d02440884392942c11205230"],
    "nwse-resize": ["size_fdiag", "nw-resize", "se-resize", "top_left_corner",
                    "bottom_right_corner", "c7088f0f3e6c8088236ef8e1e3e70000"],
    "nesw-resize": ["size_bdiag", "ne-resize", "sw-resize", "top_right_corner",
                    "bottom_left_corner", "fcf1c3c7cd4491d801f1e1c78f100000"],
    "not-allowed": ["crossed_circle", "forbidden", "no-drop", "dnd-no-drop", "circle",
                    "03b6e0fcb3499374a867c041f52298f0"],
    "help": ["question_arrow", "whats_this", "left_ptr_help", "dnd-ask",
             "5c6cd98b3f3ebcb1f9c7f1c204630408", "d9ce0ab605698f320427677b458ad60b"],
    "copy": ["dnd-copy", "1081e37283d90000800003c07f3ef6bf", "6407b0e94181790501fd1e167b474872",
             "b66166c04f8c3109214a4fbd64a50fc8"],
    "alias": ["link", "dnd-link", "3085a0e285430894940527032f8b26df",
              "640fb0e74195791501fd1ed57b41487f", "a2a266d0498c3104214a47bd64ab0fc8"],
    "context-menu": [],
    "zoom-in": ["zoom_in"],
    "zoom-out": ["zoom_out"],
    "wait": ["watch", "0426c94ea35c87780ff01dc239897213"],
    "progress": ["left_ptr_watch", "half-busy", "00000000000000020006000e7e9ffc3f",
                 "08e8e1c95fe2fc01f976f1e063a24ccd", "3ecb610c1bf2410f44200f48c40d3599"],
}


def flip_h(rows):
    return [r[::-1] for r in rows]


ART["nesw-resize"] = ((6, 5), [r.ljust(GRID, ".")[::-1] for r in ART["nwse-resize"][1]])


def paint(rows, size):
    unit = size // GRID
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    for j, row in enumerate(rows):
        for i, ch in enumerate(row[:GRID]):
            if ch not in INK:
                continue
            c = P.rgb(INK[ch]) + (255,)
            for y in range(j * unit, (j + 1) * unit):
                for x in range(i * unit, (i + 1) * unit):
                    px[x, y] = c
    return im


def orbit_frame(n, frames, with_arrow):
    """Busy cursor: a planet round a little striped sun."""
    rows = [["."] * GRID for _ in range(GRID)]
    if with_arrow:
        for j, row in enumerate(ARROW[:9]):
            for i, ch in enumerate(row):
                if ch != ".":
                    rows[j][i] = ch
        cx, cy, rx, ry = 8.5, 8.5, 2.9, 2.2
    else:
        cx, cy, rx, ry = 5.5, 5.5, 4.6, 3.0
    # sun
    sun_r = 1.6 if with_arrow else 2.2
    for j in range(GRID):
        for i in range(GRID):
            d = math.hypot(i + 0.5 - cx, j + 0.5 - cy)
            if d <= sun_r + 0.25:
                rows[j][i] = "g" if j + 0.5 < cy else "a"
            elif d <= sun_r + 1.25 and not with_arrow:
                rows[j][i] = "o"
    ang = 2 * math.pi * n / frames
    for k, (col, lag) in enumerate((("p", 0.0), ("c", 0.45), ("m", 0.9))):
        a = ang - lag
        x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
        i, j = int(x), int(y)
        if 0 <= i < GRID and 0 <= j < GRID:
            if k == 0:
                for di, dj in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    if 0 <= i + di < GRID and 0 <= j + dj < GRID and not with_arrow:
                        rows[j + dj][i + di] = col
                rows[j][i] = col
            elif not with_arrow or k == 1:
                rows[j][i] = col
    return ["".join(r) for r in rows]


def build(out):
    if not shutil.which("xcursorgen"):
        raise SystemExit("xcursorgen is needed to build the cursors")
    theme = Path(out) / "icons" / ("%s-cursors" % P.NAME)
    if theme.exists():
        shutil.rmtree(theme)
    cursors = theme / "cursors"
    cursors.mkdir(parents=True)
    (theme / "index.theme").write_text(
        "[Icon Theme]\nName=%s Cursors\nComment=Pixel-art cursors\nInherits=breeze_cursors\n" % P.NAME)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        def make(name, frames_rows, hotspot, ms=None):
            lines = []
            for size in SIZES:
                unit = size // GRID
                for k, rows in enumerate(frames_rows):
                    png = tmp / ("%s-%d-%02d.png" % (name, size, k))
                    paint(rows, size).save(png)
                    hx, hy = hotspot
                    entry = "%d %d %d %s" % (size, hx * unit + unit // 2 * (hx > 0),
                                             hy * unit + unit // 2 * (hy > 0), png)
                    if ms:
                        entry += " %d" % ms
                    lines.append(entry)
            cfg = tmp / (name + ".cfg")
            cfg.write_text("\n".join(lines) + "\n")
            subprocess.run(["xcursorgen", str(cfg), str(cursors / name)], check=True)

        for name, (hot, rows) in ART.items():
            make(name, [rows], hot)
        frames = 16
        make("wait", [orbit_frame(n, frames, False) for n in range(frames)], (5, 5), 70)
        make("progress", [orbit_frame(n, frames, True) for n in range(frames)], (0, 0), 70)

    for name, aliases in ALIASES.items():
        for alias in aliases:
            link = cursors / alias
            if not link.exists():
                os.symlink(name, link)


def preview(path):
    names = list(ART) + ["wait", "progress"]
    tiles = []
    for name in names:
        if name == "wait":
            rows = orbit_frame(2, 16, False)
        elif name == "progress":
            rows = orbit_frame(2, 16, True)
        else:
            rows = ART[name][1]
        tiles.append(paint(rows, 48))
    sheet = Image.new("RGBA", (len(tiles) * 56 + 8, 64), P.rgb(P.SURFACE1) + (255,))
    for k, t in enumerate(tiles):
        sheet.alpha_composite(t, (8 + k * 56, 8))
    sheet.save(path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        preview(sys.argv[3])
    else:
        build(sys.argv[1] if len(sys.argv) > 1 else "theme")
