"""A very small SVG writer for pixel-aligned theme art.

KDE themes are SVG files whose elements are found by id and drawn into a
rectangle by KSvg.  The art here is almost all axis-aligned rectangles on a
pixel grid, so this does little more than collect <rect>s into named groups.

Every group gets an almost-invisible rectangle covering its full extent, the
same trick Breeze uses: KSvg sizes an element by its bounding box, and a corner
whose top-left pixel happens to be transparent must still measure its full
size.
"""

from xml.sax.saxutils import escape

PLACEHOLDER = 'fill="#000000" fill-opacity="0.004"'


def fmt(v):
    return ("%.3f" % v).rstrip("0").rstrip(".")


class Group:
    def __init__(self, gid, x, y, w, h, placeholder=True):
        self.gid, self.x, self.y, self.w, self.h = gid, x, y, w, h
        self.items = []
        if placeholder and w > 0 and h > 0:
            self.items.append('<rect x="%s" y="%s" width="%s" height="%s" %s/>'
                              % (fmt(x), fmt(y), fmt(w), fmt(h), PLACEHOLDER))

    def rect(self, x, y, w, h, colour, opacity=1.0, cls=None):
        """x, y relative to the group's origin."""
        if w <= 0 or h <= 0:
            return
        attrs = ['x="%s" y="%s" width="%s" height="%s"'
                 % (fmt(self.x + x), fmt(self.y + y), fmt(w), fmt(h))]
        if cls:
            attrs.append('class="%s" style="fill:currentColor"' % cls)
        else:
            attrs.append('fill="%s"' % colour)
        if opacity < 1:
            attrs.append('fill-opacity="%s"' % fmt(opacity))
        self.items.append("<rect %s/>" % " ".join(attrs))

    def raw(self, text):
        self.items.append(text)

    def pixels(self, rows, colours, unit=1.0, ox=0, oy=0):
        """Draw a pixel map.  rows is a list of strings; each character is a key
        into colours (a colour, or (colour, opacity)); '.' and ' ' are empty."""
        cells = []
        for row in rows:
            line = []
            for ch in row:
                c = colours.get(ch) if ch not in ". " else None
                if c is not None and not isinstance(c, tuple):
                    c = (c, 1.0)
                line.append(c)
            cells.append(line)
        self.grid(cells, unit, ox, oy)

    def grid(self, cells, unit=1.0, ox=0, oy=0):
        """Draw a grid of cells, each (colour, opacity) or None, one cell per
        `unit` from (ox, oy).  Runs of a cell along a row become one rect, and
        a run repeated on the rows below grows into a taller one.

        This has to look right at any display scale, not only 100%.  At 115%
        a cell's edge lands part-way across a screen pixel, and the two cells
        meeting there each cover only part of it: drawn side by side they leave
        it partly transparent, so a surface built a row at a time comes out
        see-through along every row.  So every solid run is first laid down
        underneath as well, reaching one cell further right and one row further
        down wherever the cells it reaches into are solid too.  At 100% the
        exact rects on top hide it entirely; scaled, it fills in those pixels."""
        h = len(cells)
        w = max((len(r) for r in cells), default=0)

        def cell(x, y):
            if 0 <= y < h and 0 <= x < len(cells[y]):
                return cells[y][x]
            return None

        def solid(x, y):
            c = cell(x, y)
            return c is not None and c[1] >= 1

        # Runs along each row, merged down the rows while they repeat.
        boxes = []                   # [x0, y0, x1, y1, cell]
        open_runs = {}
        for y in range(h):
            row_runs = {}
            x = 0
            while x < w:
                c = cell(x, y)
                if c is None:
                    x += 1
                    continue
                k = x
                while k < w and cell(k, y) == c:
                    k += 1
                key = (x, k, c)
                box = open_runs.get(key)
                if box is None:
                    box = [x, y, k, y + 1, c]
                    boxes.append(box)
                else:
                    box[3] = y + 1
                row_runs[key] = box
                x = k
            open_runs = row_runs

        def put(x0, y0, x1, y1, c):
            self.rect(ox + x0 * unit, oy + y0 * unit, (x1 - x0) * unit, (y1 - y0) * unit,
                      c[0], c[1])

        for x0, y0, x1, y1, c in boxes:
            if c[1] < 1:
                continue
            right = all(solid(x1, y) for y in range(y0, y1))
            down = all(solid(x, y1) for x in range(x0, x1))
            if right and down and solid(x1, y1):
                put(x0, y0, x1 + 1, y1 + 1, c)
            else:
                if right:
                    put(x0, y0, x1 + 1, y1, c)
                if down:
                    put(x0, y0, x1, y1 + 1, c)
        for x0, y0, x1, y1, c in boxes:
            put(x0, y0, x1, y1, c)

    def svg(self):
        return '<g id="%s">\n  %s\n</g>' % (escape(self.gid), "\n  ".join(self.items))


class Document:
    def __init__(self, width, height, stylesheet=None):
        self.width, self.height = width, height
        self.groups = []
        self.stylesheet = stylesheet

    def group(self, gid, x, y, w, h, placeholder=True):
        g = Group(gid, x, y, w, h, placeholder)
        self.groups.append(g)
        return g

    def svg(self):
        head = ('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
                'width="%s" height="%s" viewBox="0 0 %s %s" shape-rendering="crispEdges">'
                % (fmt(self.width), fmt(self.height), fmt(self.width), fmt(self.height)))
        parts = [head]
        if self.stylesheet:
            parts.append('<defs><style type="text/css" id="current-color-scheme">%s</style></defs>'
                         % self.stylesheet)
        parts += [g.svg() for g in self.groups]
        parts.append("</svg>\n")
        return "\n".join(parts)
