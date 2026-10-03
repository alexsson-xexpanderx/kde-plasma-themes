"""Hand-made pixel art for the icon theme: folders, file pages, the trash and
the launcher's sun, and the small symbols drawn on them.

Everything here is a grid: a list of rows, each cell (colour, opacity) or None.
There are two grids per icon, 24 cells across for 24 px and up and 16 cells
across for 16 and 22 px.  Symbols are drawn as text, one character a cell:
'#' is the symbol's colour, '+' its accent, anything else is empty.
"""

import palette as P

SHADOW = (P.VOID, 0.75)

# ---------------------------------------------------------------- symbols
#
# Big ones are at most 9 cells wide and 7 tall (the PDF letters are 11), small
# ones at most 5 by 5.  A name missing from SMALL is left off the 16-cell icon.

BIG = {
    "documents": [
        ".######..",
        ".#....##.",
        ".#.##..#.",
        ".#.....#.",
        ".#.###.#.",
        ".#.....#.",
        ".#######.",
    ],
    "download": [
        "....#....",
        "....#....",
        "..#.#.#..",
        "...###...",
        "....#....",
        "#.......#",
        "#########",
    ],
    "music": [
        "...######",
        "...######",
        "...#....#",
        "...#....#",
        ".###..###",
        "####.####",
        ".##...##.",
    ],
    "pictures": [
        "#########",
        "#....++.#",
        "#..#.++.#",
        "#.###...#",
        "#######.#",
        "#########",
    ],
    "videos": [
        "#########",
        "#..#....#",
        "#..##...#",
        "#..###..#",
        "#..##...#",
        "#..#....#",
        "#########",
    ],
    "home": [
        "....#....",
        "...###...",
        "..#####..",
        ".#######.",
        "..#####..",
        "..##.##..",
        "..##.##..",
    ],
    "desktop": [
        "#########",
        "#.......#",
        "#.......#",
        "#########",
        "....#....",
        "..#####..",
    ],
    "templates": [
        "#########",
        "#...#...#",
        "#...#...#",
        "#########",
        "#.......#",
        "#########",
    ],
    "people": [
        ".##...##.",
        ".##...##.",
        ".........",
        "####.####",
        "####.####",
        "####.####",
    ],
    "globe": [
        "..#####..",
        ".#..#..#.",
        "#########",
        "#...#...#",
        "#########",
        ".#..#..#.",
        "..#####..",
    ],
    "cloud": [
        "...##....",
        "..####.#.",
        ".#######.",
        "#########",
        "#########",
        ".#######.",
    ],
    "code": [
        "...#.#...",
        "..#...#..",
        ".#.....#.",
        "#.......#",
        ".#.....#.",
        "..#...#..",
        "...#.#...",
    ],
    "games": [
        ".#######.",
        "##.###.##",
        "#...#.#.#",
        "##.####.#",
        "#########",
        ".##...##.",
    ],
    "recent": [
        "..#####..",
        ".#..#..#.",
        "#...#...#",
        "#...###.#",
        "#.......#",
        ".#.....#.",
        "..#####..",
    ],
    "star": [
        "....#....",
        "...###...",
        "#########",
        ".#######.",
        "..#####..",
        ".###.###.",
        ".##...##.",
    ],
    "important": [
        "...###...",
        "...###...",
        "...###...",
        "...###...",
        ".........",
        "...###...",
    ],
    "locked": [
        "..#####..",
        ".##...##.",
        ".#.....#.",
        "#########",
        "####.####",
        "####.####",
        "#########",
    ],
    "unlocked": [
        "..#####..",
        ".##...##.",
        ".##......",
        "#########",
        "####.####",
        "####.####",
        "#########",
    ],
    "mail": [
        "#########",
        "##.....##",
        "#.#...#.#",
        "#..#.#..#",
        "#...#...#",
        "#########",
    ],
    "script": [
        "#........",
        ".#.......",
        "..#......",
        ".#.......",
        "#...#####",
    ],
    "text": [
        "#########",
        ".........",
        "#######..",
        ".........",
        "#########",
        ".........",
        "#####....",
    ],
    "book": [
        "##.##.##.",
        "##.##.##.",
        "##.##..##",
        "##.##..##",
        "##.##...#",
        "#########",
    ],
    "temp": [
        ".#######.",
        "..#...#..",
        "...#.#...",
        "....#....",
        "...#.#...",
        "..#...#..",
        ".#######.",
    ],
    "git": [
        ".#.....#.",
        ".#.....#.",
        ".#....#..",
        ".#..##...",
        ".###.....",
        ".#.......",
        ".#.......",
    ],
    "trash": [
        "..#####..",
        "#########",
        ".#######.",
        ".#.#.#.#.",
        ".#.#.#.#.",
        ".#.#.#.#.",
        "..#####..",
    ],
    "print": [
        "..#####..",
        "..#...#..",
        "#########",
        "#.......#",
        "#########",
        "..#####..",
    ],
    "grid": [
        "#########",
        "#...#...#",
        "#########",
        "#...#...#",
        "#########",
        "#...#...#",
        "#########",
    ],
    "chart": [
        "#########",
        "#.......#",
        "#.....+.#",
        "#...+.+.#",
        "#.+.+.+.#",
        "#########",
        "....#....",
    ],
    "pdf": [
        "##..##..###",
        "#.#.#.#.#..",
        "##..#.#.##.",
        "#...#.#.#..",
        "#...##..#..",
    ],
    "zip": [
        "...#.#...",
        "....#....",
        "...#.#...",
        "....#....",
        "...###...",
        "...#.#...",
        "...###...",
    ],
    "gear": [
        "...#.#...",
        ".#######.",
        ".##...##.",
        "###...###",
        ".##...##.",
        ".#######.",
        "...#.#...",
    ],
    "font": [
        "...###...",
        "..##.##..",
        ".##...##.",
        ".#######.",
        ".##...##.",
        ".##...##.",
    ],
    "disc": [
        "..#####..",
        ".#######.",
        "###...###",
        "##..#..##",
        "###...###",
        ".#######.",
        "..#####..",
    ],
    "box": [
        ".#######.",
        "#...#...#",
        "#########",
        "#...#...#",
        "#...#...#",
        "#########",
    ],
    "key": [
        ".###.....",
        "#...#####",
        "#...#.#.#",
        ".###.....",
    ],
    "calendar": [
        ".#.....#.",
        "#########",
        "#########",
        "#.#.#.#.#",
        "#.......#",
        "#.#.#.#.#",
        "#########",
    ],
    "person": [
        "...###...",
        "...###...",
        "...###...",
        ".........",
        ".#######.",
        "#########",
    ],
    "markdown": [
        "#...#..#.",
        "##.##..#.",
        "#.#.#..#.",
        "#...#.###",
        "#...#..#.",
    ],
    "braces": [
        ".##...##.",
        ".#.....#.",
        ".#.....#.",
        "#.......#",
        ".#.....#.",
        ".#.....#.",
        ".##...##.",
    ],
    "database": [
        ".#######.",
        "#.......#",
        ".#######.",
        "#.......#",
        ".#######.",
        "#.......#",
        ".#######.",
    ],
    "pen": [
        "....#....",
        "...###...",
        "..#.#.#..",
        "..#.#.#..",
        "..#####..",
        "...###...",
        "...###...",
    ],
    "question": [
        "..#####..",
        ".##...##.",
        ".....##..",
        "....##...",
        "....##...",
        ".........",
        "....##...",
    ],
    "window": [
        "#########",
        "#########",
        "#.......#",
        "#.......#",
        "#.......#",
        "#########",
    ],
    "terminal": [
        "#########",
        "#.......#",
        "#.#.....#",
        "#..#....#",
        "#.#..##.#",
        "#.......#",
        "#########",
    ],
}

SMALL = {
    "documents": ["####.", "#..##", "#.#.#", "#...#", "#####"],
    "download": ["..#..", "#.#.#", ".###.", "..#..", "#####"],
    "music": ["..##.", "..#.#", "..#..", "###..", "###.."],
    "pictures": ["....+", "..#..", ".###.", "#####"],
    "videos": [".#...", ".##..", ".###.", ".##..", ".#..."],
    "home": ["..#..", ".###.", "#####", ".#.#.", ".#.#."],
    "desktop": ["#####", "#...#", "#####", "..#..", ".###."],
    "templates": ["#####", "#.#.#", "#####", "#...#", "#####"],
    "people": ["#...#", ".....", "##.##", "##.##"],
    "globe": [".###.", "#.#.#", "#####", "#.#.#", ".###."],
    "cloud": ["..##.", ".####", "#####"],
    "code": [".#.#.", "#...#", ".#.#."],
    "games": [".###.", "##.##", "#####", "#...#"],
    "recent": [".###.", "#.#.#", "#.###", "#...#", ".###."],
    "star": ["..#..", "#####", ".###.", "##.##"],
    "important": ["..#..", "..#..", "..#..", ".....", "..#.."],
    "locked": [".###.", "#...#", "#####", "##.##", "#####"],
    "unlocked": [".###.", "#....", "#####", "##.##", "#####"],
    "mail": ["#####", "##.##", "#.#.#", "#####"],
    "script": ["#....", ".#...", "#..##"],
    "text": ["#####", ".....", "####.", ".....", "#####"],
    "book": ["##.#.", "##.#.", "##.##", "#####"],
    "temp": ["#####", ".#.#.", "..#..", ".#.#.", "#####"],
    "git": ["#...#", "#..#.", "###..", "#...."],
    "trash": [".###.", "#####", ".#.#.", ".#.#.", ".###."],
    "print": [".###.", "#####", "#...#", "#####"],
    "grid": ["#####", "#.#.#", "#####", "#.#.#", "#####"],
    "chart": ["....+", "..+.+", "+.+.+", "#####"],
    "pdf": ["###..", "#.#..", "###..", "#....", "#...."],
    "zip": [".#.#.", "..#..", ".#.#.", "..#..", ".###."],
    "gear": [".#.#.", "#####", "##.##", "#####", ".#.#."],
    "font": [".###.", "#...#", "#####", "#...#", "#...#"],
    "disc": [".###.", "#####", "##.##", "#####", ".###."],
    "box": ["#####", "#.#.#", "#####", "#...#", "#####"],
    "key": [".#...", "#.###", ".#.#."],
    "calendar": ["#####", "#####", "#.#.#", "#...#", "#####"],
    "person": [".###.", ".###.", ".....", "#####", "#####"],
    "markdown": ["#...#", "##.##", "#.#.#", "#...#"],
    "braces": ["##.##", "#...#", ".#.#.", "#...#", "##.##"],
    "database": [".###.", "#...#", ".###.", "#...#", ".###."],
    "pen": ["..#..", ".#.#.", ".#.#.", ".###.", "..#.."],
    "question": [".###.", "...#.", "..#..", ".....", "..#.."],
    "window": ["#####", "#####", "#...#", "#...#", "#####"],
    "terminal": ["#####", "#...#", "##..#", "#.###", "#####"],
}


# ---------------------------------------------------------------- grids

def blank(n):
    return [[None] * n for _ in range(n)]


def solid(grid, x, y):
    n = len(grid)
    return 0 <= x < n and 0 <= y < n and grid[y][x] is not None and grid[y][x] is not SHADOW


def stamp(grid, rows, x0, y0, colour, accent=None):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "#":
                grid[y0 + j][x0 + i] = (colour, 1.0)
            elif ch == "+":
                grid[y0 + j][x0 + i] = (accent or colour, 1.0)


def stamp_centred(grid, rows, box, colour, accent=None):
    """Centre a symbol in box = (x0, y0, x1, y1), inclusive."""
    x0, y0, x1, y1 = box
    w, h = max(len(r) for r in rows), len(rows)
    stamp(grid, rows, x0 + (x1 - x0 + 1 - w) // 2, y0 + (y1 - y0 + 1 - h) // 2, colour, accent)


def add_shadow(grid):
    """The theme's hard shadow: one cell down and to the right of every solid
    cell, wherever that is still empty."""
    n = len(grid)
    on = [[solid(grid, x, y) for x in range(n)] for y in range(n)]
    for y in range(n - 1):
        for x in range(n - 1):
            if on[y][x] and grid[y + 1][x + 1] is None:
                grid[y + 1][x + 1] = SHADOW
    return grid


def outline_cells(shape):
    """The cells of a set that have a 4-neighbour outside it."""
    edge = set()
    for (x, y) in shape:
        if any((x + dx, y + dy) not in shape for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            edge.add((x, y))
    return edge


# ---------------------------------------------------------------- folders

# The theme's folder: a pink back and an amber front, the sun going down
# behind the hills.  The others are what Dolphin offers under "Folder Color".
FOLDER = dict(outline="#561F59", back="#BC3966", tab="#E04F67", front="#FFB45E",
              lit="#FFD27A", shade="#FF915E", symbol="#561F59")


def colourway(ramp, symbol=None, outline=None):
    return dict(outline=outline or ramp[0], back=ramp[1], tab=ramp[2], front=ramp[3],
                lit=ramp[4], shade=ramp[2], symbol=symbol or ramp[0])


FOLDER_COLOURS = {
    "red": colourway(P.RAMP_RED, outline=P.RAMP_ROSE[0]),
    "orange": colourway(P.RAMP_ORANGE),
    "yellow": colourway(P.RAMP_GOLD, symbol="#6A2A68", outline="#5C4448"),
    "green": colourway(P.RAMP_MINT),
    "cyan": colourway(P.RAMP_SKY),
    "blue": colourway(["#1E2A5E", "#3E4E9A", "#5F7FD0", P.BLUE, "#C4D8FD"]),
    "violet": colourway(P.RAMP_VIOLET, symbol=P.BRIGHT),
    "magenta": colourway(P.RAMP_ROSE),
    "brown": colourway(P.RAMP_BROWN),
    "grey": colourway(P.RAMP_GREY, symbol=P.SURFACE0),
    "black": dict(outline=P.VOID, back=P.CRUST, tab=P.SURFACE0, front=P.SURFACE1,
                  lit=P.SURFACE2, shade=P.SURFACE0, symbol=P.SUBTEXT),
}

# Where things go on each grid: the folder's edges, and the box its symbol is
# centred in.
FOLDER_GEOMETRY = {
    24: dict(T=3, B=19, L=1, R=21, tab=7, front=8, box=(2, 9, 20, 18)),
    16: dict(T=2, B=13, L=1, R=14, tab=4, front=6, box=(2, 7, 13, 12)),
}


def folder(n, colours=FOLDER, symbol=None, symbol_mask=None, open_=False):
    """A folder: tab and back panel behind, front panel over them.  `symbol` is
    a name from BIG/SMALL; `symbol_mask` a lifted one (a list of rows)."""
    g = FOLDER_GEOMETRY[n]
    T, B, L, R = g["T"], g["B"], g["L"], g["R"]
    kind = {}
    for x in range(L + 1, L + g["tab"]):
        kind[(x, T)] = "t"
    for x in range(L, L + g["tab"] + 1):
        kind[(x, T + 1)] = "t"
    for y in range(T + 2, B + 1):
        for x in range(L, R + 1 - (1 if y == T + 2 else 0)):
            kind[(x, y)] = "b"
    fy = T + (g["front"] - 3 if n == 24 else g["front"] - 2)
    lip = 2 if open_ else 0
    for y in range(fy, B + 1):
        for x in range(L + (lip if y == fy else 0), R + 1 - (lip if y == fy else 0)):
            kind[(x, y)] = "f"
    if open_:
        # An open folder's front drops forward: the back shows above it, and
        # the paper inside peeks out over the back's edge.
        for x in range(L + 2, R - 1):
            kind[(x, T + 3)] = "p"
    edge = outline_cells(set(kind))
    grid = blank(n)
    for (x, y), k in kind.items():
        if (x, y) in edge:
            c = colours["outline"]
        elif k == "t":
            c = colours["tab"]
        elif k == "b":
            c = colours["back"]
        elif k == "p":
            c = P.TEXT
        elif y == fy or (y == fy + 1 and open_):
            c = colours["lit"]
        elif y == B - 1:
            c = colours["shade"]
        else:
            c = colours["front"]
        grid[y][x] = (c, 1.0)
    # The front's top edge, where it meets the back, is drawn as a fold line.
    for x in range(L, R + 1):
        if kind.get((x, fy - 1)) == "b":
            grid[fy - 1][x] = (colours["outline"], 1.0)
    rows = symbol_mask
    if rows is None and symbol is not None:
        rows = (BIG if n == 24 else SMALL).get(symbol)
    if rows:
        stamp_centred(grid, rows, g["box"], colours["symbol"], colours["outline"])
    return add_shadow(grid)


# ---------------------------------------------------------------- file pages

# A page of paper with its corner folded, a band of the file's colour along the
# bottom, and the file's symbol in the middle.
PAGE_GEOMETRY = {
    24: dict(L=4, R=18, T=1, B=20, fold=4, band=(16, 18), box=(6, 5, 16, 14)),
    16: dict(L=3, R=12, T=1, B=14, fold=3, band=(11, 12), box=(4, 4, 11, 9)),
}
PAPER = dict(outline=P.SURFACE2, fill="#D8D3EC", lit=P.BRIGHT, shade=P.SUBTEXT,
             flap=P.SUBTEXT)


def page(n, ramp, symbol=None, accent=None):
    g = PAGE_GEOMETRY[n]
    L, R, T, B, F = g["L"], g["R"], g["T"], g["B"], g["fold"]
    shape = set()
    for y in range(T, B + 1):
        for x in range(L, R + 1):
            if not (y < T + F and x > R - F + (y - T)):
                shape.add((x, y))
    edge = outline_cells(shape)
    grid = blank(n)
    b0, b1 = g["band"]
    for (x, y) in shape:
        if (x, y) in edge:
            c = PAPER["outline"]
        elif b0 <= y <= b1:
            c = ramp[3] if y == b0 else ramp[2]
        elif x == L + 1 or y == T + 1:
            c = PAPER["lit"]
        elif x == R - 1 or y == b0 - 1:
            c = PAPER["shade"]
        else:
            c = PAPER["fill"]
        grid[y][x] = (c, 1.0)
    # The folded-down corner.
    for i in range(F):
        for j in range(i + 1):
            x, y = R - F + 1 + j, T + i
            grid[y][x] = (PAPER["flap"] if j < i else PAPER["outline"], 1.0)
    for i in range(F):
        grid[T + F - 1][R - F + 1 + i] = (PAPER["outline"], 1.0)
        grid[T + i][R - F + 1] = (PAPER["outline"], 1.0)
    rows = (BIG if n == 24 else SMALL).get(symbol) if symbol else None
    if rows:
        stamp_centred(grid, rows, g["box"], ink(ramp), accent or ramp[3])
    return add_shadow(grid)


def ink(ramp):
    """The shade of a ramp a symbol is drawn in on paper: the lighter of its
    two dark shades that still stands out (3:1), else the darker, else that
    darkened further -- gold's darks are too pale to read on paper."""
    for c in (ramp[1], ramp[0]):
        if P.contrast(c, PAPER["fill"]) >= 3:
            return c
    c = ramp[0]
    while P.contrast(c, PAPER["fill"]) < 3:
        c = P.mix(c, P.VOID, 0.2)
    return c


# ---------------------------------------------------------------- trash

def trash(n, full=False):
    """A pixel bin, violet like the panel's sky, with a lid; when full,
    crumpled paper in the sunset's colours shows over the rim."""
    V = P.RAMP_VIOLET
    grid = blank(n)
    if n == 24:
        L, R, lid, top, bot = 5, 18, 5, 7, 20
    else:
        L, R, lid, top, bot = 3, 12, 3, 5, 13
    shape = {}
    hx0, hx1 = (L + R) // 2 - (2 if n == 24 else 1), (L + R) // 2 + (2 if n == 24 else 1)
    for x in range(hx0, hx1 + 1):
        shape[(x, lid - 2)] = "h"
    shape[(hx0, lid - 1)] = shape[(hx1, lid - 1)] = "h"
    for y in (lid, lid + 1):
        for x in range(L - 1, R + 2):
            shape[(x, y)] = "lid"
    for y in range(top + 1, bot + 1):
        inset = 1 if y >= bot - 1 else 0
        for x in range(L + inset, R + 1 - inset):
            shape[(x, y)] = "body"
    if full:
        # Paper over the rim lifts the lid.
        lifted = {}
        for (x, y), k in shape.items():
            lifted[(x, y - 2 if k in ("h", "lid") else y)] = k
        shape = lifted
        for x, c in zip(range(L + 1, R), [P.TEXT, P.PINK, P.GOLD, P.TEXT, P.CORAL, P.TEXT,
                                         P.AMBER, P.TEXT, P.PINK, P.TEXT, P.GOLD, P.TEXT]):
            shape[(x, top - 1)] = ("paper", c)
            if (x - L) % 3 == 1:
                shape[(x, top - 2)] = ("paper", P.TEXT)
    edge = outline_cells(set(shape))
    for (x, y), k in shape.items():
        if isinstance(k, tuple):
            grid[y][x] = (k[1], 1.0)
            continue
        if (x, y) in edge:
            c = V[0]
        elif k == "lid":
            c = V[4] if y == min(yy for (_, yy), kk in shape.items() if kk == "lid") else V[3]
        elif k == "h":
            c = V[2]
        elif (x - L) % 3 == 0:
            c = V[1]
        else:
            c = V[2] if (x - L) % 3 == 2 else V[3]
        grid[y][x] = (c, 1.0)
    return add_shadow(grid)


# ---------------------------------------------------------------- the sun

def sun(n):
    """The launcher's icon: the wallpaper's striped sun on the horizon, with its
    reflection below -- the theme's emblem, as on the splash screen."""
    grid = blank(n)
    cx = (n - 1) / 2 - 0.5
    r = n * 0.40
    horizon = round(n * 0.62)
    ramp = ["#FFE08A", "#FFC46A", "#FFA05E", "#FF7A62", "#FF5C78", "#E8467E"]
    slats = {round(horizon - r * f) for f in (0.18, 0.40)}
    for y in range(n):
        for x in range(n):
            dx, dy = x - cx, y - horizon + 0.5
            if dy < 0 and dx * dx + dy * dy <= r * r and y not in slats:
                t = (y - (horizon - r)) / r
                grid[y][x] = (ramp[min(len(ramp) - 1, int(t * len(ramp)))], 1.0)
    # Horizon and the reflection's broken lines.
    for x in range(n // 12, n - n // 12):
        grid[horizon][x] = (P.MAUVE, 1.0)
    rows = [(horizon + 2, 0.32, "#FF7A62"), (horizon + 4, 0.22, "#FF5C78"),
            (horizon + 6, 0.12, "#E8467E")] if n == 24 else \
           [(horizon + 2, 0.28, "#FF7A62"), (horizon + 4, 0.14, "#E8467E")]
    for y, half, c in rows:
        if y < n - 1:
            for x in range(round(cx - n * half), round(cx + n * half) + 1):
                if (x + y) % 5:
                    grid[y][x] = (c, 1.0)
    return add_shadow(grid)
