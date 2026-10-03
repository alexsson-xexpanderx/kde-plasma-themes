"""A small kit for drawing filled pixel-art icons from shapes.

An icon is a list of layers, each a shape and the ramp it is painted from,
laid down in order.  Shapes are given on a 24-unit square, whatever the grid
they are drawn on, so one description makes both the 24-cell and the 16-cell
icon.  A cell belongs to a shape when at least half of it is inside.

Each layer is finished the way the folders are: an outline in the ramp's
darkest shade, the rest of it filled with a middle shade, a lighter one along
its top and left edges and a darker one along its bottom and right.  Details
painted over a part (the white "i" on a blue disc) are usually drawn flat,
without outline or edges.  The whole icon then gets the theme's hard shadow.

Ramps are lists of five colours, dark to light, as in palette.py.
"""

import math

import icons_art as A
import palette as P

U = 24.0        # the units shapes are given in

# Ramps for things that are not in the wallpaper's colours: paper and metal,
# and the near-black of screens.
WHITE = [P.SURFACE2, P.SUBTEXT, "#D8D3EC", P.TEXT, P.BRIGHT]
SCREEN = [P.VOID, P.CRUST, P.MANTLE, P.SURFACE0, P.SURFACE1]
METAL = [P.SURFACE0, P.SURFACE2, P.OVERLAY1, P.SUBTEXT, P.TEXT]
NIGHT = [P.VOID, "#1C1638", P.RAMP_VIOLET[0], P.RAMP_VIOLET[1], P.RAMP_VIOLET[2]]


# ---------------------------------------------------------------- shapes
#
# A shape is anything with inside(x, y, c): is the point (in units) inside,
# where c is the size of one cell in units -- so that a line can stay at least
# a cell wide on a small grid.

class Shape:
    def __or__(self, other):
        return Union(self, other)

    def __sub__(self, other):
        return Diff(self, other)

    def __and__(self, other):
        return Inter(self, other)


class Rect(Shape):
    def __init__(self, x0, y0, x1, y1, r=0.0):
        self.b, self.r = (x0, y0, x1, y1), r

    def inside(self, x, y, c):
        x0, y0, x1, y1 = self.b
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            return False
        r = self.r
        if r <= 0:
            return True
        cx = min(max(x, x0 + r), x1 - r)
        cy = min(max(y, y0 + r), y1 - r)
        return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


class Ellipse(Shape):
    def __init__(self, cx, cy, rx, ry=None):
        self.c, self.rx, self.ry = (cx, cy), rx, ry if ry is not None else rx

    def inside(self, x, y, c):
        return ((x - self.c[0]) / self.rx) ** 2 + ((y - self.c[1]) / self.ry) ** 2 <= 1


def Circle(cx, cy, r):
    return Ellipse(cx, cy, r)


class Ring(Shape):
    """An annulus, or a stretch of one between two angles (degrees, clockwise
    from three o'clock, since y runs down)."""

    def __init__(self, cx, cy, r, w, a0=None, a1=None):
        self.c, self.r, self.w, self.a = (cx, cy), r, w, (a0, a1)

    def inside(self, x, y, c):
        d = math.hypot(x - self.c[0], y - self.c[1])
        half = max(self.w, c) / 2
        if abs(d - self.r) > half:
            return False
        a0, a1 = self.a
        if a0 is None:
            return True
        a = math.degrees(math.atan2(y - self.c[1], x - self.c[0])) % 360
        a0, a1 = a0 % 360, a1 % 360
        return a0 <= a <= a1 if a0 <= a1 else (a >= a0 or a <= a1)


class Line(Shape):
    """A thick line with round ends, never thinner than a cell."""

    def __init__(self, x0, y0, x1, y1, w=1.5):
        self.p, self.q, self.w = (x0, y0), (x1, y1), w

    def inside(self, x, y, c):
        (ax, ay), (bx, by) = self.p, self.q
        dx, dy = bx - ax, by - ay
        t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(x - ax - t * dx, y - ay - t * dy) <= max(self.w, c) / 2


class Poly(Shape):
    def __init__(self, *points):
        self.pts = points

    def inside(self, x, y, c):
        inside, n = False, len(self.pts)
        for i in range(n):
            (x0, y0), (x1, y1) = self.pts[i], self.pts[(i + 1) % n]
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                inside = not inside
        return inside


class Union(Shape):
    def __init__(self, *shapes):
        self.shapes = shapes

    def inside(self, x, y, c):
        return any(s.inside(x, y, c) for s in self.shapes)


class Diff(Shape):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def inside(self, x, y, c):
        return self.a.inside(x, y, c) and not self.b.inside(x, y, c)


class Inter(Shape):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def inside(self, x, y, c):
        return self.a.inside(x, y, c) and self.b.inside(x, y, c)


def gear(cx, cy, r, teeth=8, tooth=2.6, hole=3.0):
    body = Circle(cx, cy, r)
    parts = [body]
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        ca, sa = math.cos(a), math.sin(a)
        w = tooth / 2
        # a square tooth standing out of the rim
        pts = [(cx + ca * (r - 1) - sa * w, cy + sa * (r - 1) + ca * w),
               (cx + ca * (r + tooth) - sa * w, cy + sa * (r + tooth) + ca * w),
               (cx + ca * (r + tooth) + sa * w, cy + sa * (r + tooth) - ca * w),
               (cx + ca * (r - 1) + sa * w, cy + sa * (r - 1) - ca * w)]
        parts.append(Poly(*pts))
    return Union(*parts) - Circle(cx, cy, hole) if hole else Union(*parts)


# ---------------------------------------------------------------- layers

class Layer:
    def __init__(self, shape, ramp, tone=3, outline=True, edges=True, flat=None):
        self.shape, self.ramp, self.tone = shape, ramp, tone
        self.outline, self.edges = outline, edges
        self.flat = flat            # one colour for the whole layer, if given


def part(shape, ramp, tone=3):
    """A solid part: outline, fill, lit and shaded edges."""
    return Layer(shape, ramp, tone)


def detail(shape, colour):
    """Something painted on: one colour, no outline, no edges."""
    return Layer(shape, None, outline=False, edges=False, flat=colour)


def inset(shape, ramp, tone=3):
    """A part set into another: edges but no outline of its own."""
    return Layer(shape, ramp, tone, outline=False)


class Symbol:
    """One of icons_art's text-drawn symbols, centred in a box given in units."""

    def __init__(self, name, colour, box, accent=None):
        self.name, self.colour, self.box, self.accent = name, colour, box, accent


class Pixels:
    """Pixels placed by hand, one map per grid: rows of characters starting
    at the top-left cell, each a key into `colours`; '.' and ' ' are left
    alone.  For a logo whose details are too small for shapes to land
    reliably on the grid -- Steam's wheels and arm."""

    def __init__(self, big, small, colours):
        self.rows, self.colours = (big, small), colours


def mask(shape, n, samples=4):
    c = U / n
    out = [[False] * n for _ in range(n)]
    need = samples * samples / 2
    for y in range(n):
        for x in range(n):
            hits = 0
            for j in range(samples):
                for i in range(samples):
                    if shape.inside((x + (i + 0.5) / samples) * c, (y + (j + 0.5) / samples) * c, c):
                        hits += 1
            out[y][x] = hits >= need
    return out


def draw(n, layers):
    """Rasterise a layered icon onto an n-cell grid."""
    grid = A.blank(n)
    for layer in layers:
        if isinstance(layer, Pixels):
            for y, row in enumerate(layer.rows[0 if n == 24 else 1]):
                for x, ch in enumerate(row):
                    if ch in layer.colours:
                        grid[y][x] = (layer.colours[ch], 1.0)
            continue
        if isinstance(layer, Symbol):
            own = getattr(layer, "rows", None)
            rows = own[0 if n == 24 else 1] if own else (A.BIG if n == 24 else A.SMALL).get(layer.name)
            if rows:
                x0, y0, x1, y1 = layer.box
                k = n / U
                box = (int(x0 * k), int(y0 * k), int(math.ceil(x1 * k)) - 1, int(math.ceil(y1 * k)) - 1)
                A.stamp_centred(grid, rows, box, layer.colour, layer.accent)
            continue
        m = mask(layer.shape, n)
        cells = {(x, y) for y in range(n) for x in range(n) if m[y][x]}
        if layer.flat:
            for x, y in cells:
                grid[y][x] = (layer.flat, 1.0)
            continue
        R, t = layer.ramp, layer.tone
        edge = A.outline_cells(cells) if layer.outline else set()
        inner = cells - edge
        for x, y in cells:
            if (x, y) in edge:
                c = R[0]
            elif layer.edges and ((x, y - 1) not in inner or (x - 1, y) not in inner):
                c = R[min(4, t + 1)]
            elif layer.edges and ((x, y + 1) not in inner or (x + 1, y) not in inner):
                c = R[max(1, t - 1)]
            else:
                c = R[t]
            grid[y][x] = (c, 1.0)
    return A.add_shadow(grid)
