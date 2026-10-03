"""The wallpaper: a pixel-art dusk over an observatory.

Painted at a low resolution -- about 360 art pixels tall whatever the screen --
with ordered (Bayer) dithering between a small set of colours, then enlarged
with nearest-neighbour so every art pixel stays a crisp square.

Composition, for a screen with Conky Orrery in the middle and conky-dashboard
down the right edge: the middle of the sky is kept dark and empty for the
Orrery's rings, and a striped sun sets on the horizon right under it, so it
hangs over the sunset like an instrument on a stand.  A ringed planet fills
the upper left, an observatory sits on the right-hand hill, and the far right
is quiet sky for the dashboard.
"""

import math
from pathlib import Path

import numpy as np
from PIL import Image

import palette as P

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32


def hexes(*cs):
    return np.array([P.rgb(c) for c in cs], dtype=np.float64)


# The sky, zenith to horizon.
SKY = hexes("#07060E", "#0B0916", "#0F0C1E", "#140F28", "#1A1232", "#22153C", "#2E1946",
            "#3F1D50", "#561F59", "#72245F", "#962C64", "#BC3966", "#E04F67", "#FF6E64",
            "#FF915E", "#FFB45E", "#FFD27A")

PLANET_BANDS = [
    hexes("#120C24", "#2A1E52", "#4A378A", "#6E55B8", "#9A80E0", "#C8B4FF"),   # violet
    hexes("#170B22", "#3A1844", "#6A2A68", "#A2407E", "#D7649A", "#FF9EC0"),   # rose
    hexes("#140D1C", "#33203E", "#5A3A62", "#8A5F86", "#BC92B2", "#EBCBE0"),   # dusty
]
RING = hexes("#2A1F2E", "#5C4448", "#9A7660", "#D2A878", "#F6D79A", "#FFF0C8")
MOON = hexes("#0E0B19", "#2B2540", "#5A5070", "#9A90A8", "#D8D0DC", "#F4EEF0")
SUN = hexes("#FFE08A", "#FFC46A", "#FFA05E", "#FF7A62", "#FF5C78", "#E8467E")
STAR = hexes(P.TEXT, P.SKY, P.GOLD, P.MAUVE, "#FFFFFF")


def bayer(h, w):
    return np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]


def dither_index(t, n, b):
    """t in [0, 1] -> palette index in [0, n-1], dithered by threshold map b."""
    v = np.clip(t, 0, 1) * (n - 1)
    lo = np.floor(v)
    return np.clip((lo + ((v - lo) > b)).astype(int), 0, n - 1)


def midpoint_ridge(rng, w, rough, lo, hi, anchors=None):
    """A 1-D fractal ridgeline, w samples, between lo and hi (row numbers)."""
    size = 1
    while size < w:
        size *= 2
    pts = np.zeros(size + 1)
    pts[0], pts[-1] = rng.uniform(0, 1), rng.uniform(0, 1)
    step, amp = size, 1.0
    while step > 1:
        half = step // 2
        for i in range(half, size, step):
            pts[i] = (pts[i - half] + pts[i + half]) / 2 + rng.uniform(-amp, amp) * 0.5
        step, amp = half, amp * rough
    pts = (pts - pts.min()) / (np.ptp(pts) + 1e-9)
    ridge = lo + (hi - lo) * pts[:w]
    if anchors is not None:
        ridge = ridge * (1 - anchors[1]) + anchors[0] * anchors[1]
    return ridge


class Painter:
    def __init__(self, w, h, seed=1977):
        self.w, self.h = w, h
        self.rng = np.random.default_rng(seed)
        self.b = bayer(h, w)
        self.img = np.zeros((h, w, 3))
        yy, xx = np.mgrid[0:h, 0:w]
        self.xx, self.yy = xx.astype(float), yy.astype(float)
        self.u = h / 360.0                  # size unit: one pixel on a 360-tall canvas
        self.horizon = round(h * 0.87)
        self.cx = w / 2

    # ------------------------------------------------------------- layers
    def sky(self):
        y = self.yy / self.horizon
        # Most of the sky stays in the dark third of the ramp; the warm end is
        # squeezed into the last stretch above the horizon.
        lower = np.clip((y - 0.64) / 0.36, 0, None)
        t = np.where(y < 0.64, 0.30 * (np.clip(y, 0, 1) / 0.64) ** 1.3, 0.30 + 0.70 * lower ** 2.0)
        # A warm swell centred under the Orrery, where the sun goes down.
        d = np.hypot((self.xx - self.cx) / (self.w * 0.20), (self.yy - self.horizon) / (self.h * 0.16))
        t = t + 0.16 * np.exp(-d * d * 2.2) * (y > 0.45)
        # Faint dusk at the far edges, so the corners are not flat black.
        edge = np.abs(self.xx - self.cx) / (self.w / 2)
        t = t + 0.035 * edge ** 3 * (1 - y)
        t = np.clip(t, 0, 0.995)
        idx = dither_index(t, len(SKY), self.b)
        self.img[:] = SKY[idx]
        self.sky_t = t

    def nebula(self):
        """A dim band of dust across the upper sky, dithered into the dark."""
        w, h, u = self.w, self.h, self.u
        # value noise, a few octaves
        n = np.zeros((h, w))
        for octave, amp in ((24, 0.55), (12, 0.28), (6, 0.17)):
            gh, gw = h // octave + 2, w // octave + 2
            g = self.rng.uniform(0, 1, (gh, gw))
            gy, gx = self.yy / octave, self.xx / octave
            y0, x0 = gy.astype(int), gx.astype(int)
            fy, fx = gy - y0, gx - x0
            fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
            a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
            c = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
            n += amp * (a * (1 - fy) + c * fy)
        # a diagonal band from upper left to the right, avoiding the centre top
        band = (self.yy - (0.10 * h + (self.xx / w) * 0.28 * h)) / (0.16 * h)
        mask = np.exp(-band ** 2) * np.clip((n - 0.42) * 2.2, 0, 1)
        mask *= np.clip((np.abs(self.xx - self.cx) - 0.10 * w) / (0.12 * w), 0.08, 1)   # kept off the Orrery
        mask *= (self.yy < self.horizon * 0.7)
        neb = hexes("#1B1236", "#2A1645", "#3B1B52")
        lvl = mask * 3.2
        for k in range(3):
            on = lvl - k > self.b + 0.0
            self.img[on] = neb[k]
        self.neb = mask

    def stars(self):
        w, h, u = self.w, self.h, self.u
        rng = self.rng
        count = int(w * h / 110)
        xs = rng.uniform(0, w, count).astype(int)
        ys = (rng.beta(1.1, 2.4, count) * self.horizon * 0.95).astype(int)
        for x, y in zip(xs, ys):
            if self.occupied(x, y):
                continue
            if math.hypot(x - self.cx, (y - self.h / 2)) < 110 * self.u and rng.uniform() < 0.6:
                continue
            depth = y / self.horizon
            bright = rng.uniform(0.25, 1.0) * (1 - 0.65 * depth)
            col = STAR[rng.choice(5, p=[0.55, 0.16, 0.12, 0.12, 0.05])]
            base = self.img[y, x]
            self.img[y, x] = base + (col - base) * bright
        # A few sparkles: a bright centre and four dim arms.
        for _ in range(int(w * h / 9000)):
            x = int(rng.uniform(4, w - 4))
            y = int(rng.uniform(4, self.horizon * 0.55))
            if self.occupied(x, y, pad=6):
                continue
            col = STAR[rng.choice(5, p=[0.5, 0.2, 0.15, 0.1, 0.05])]
            arm = 2 if rng.uniform() < 0.35 else 1
            self.blend(x, y, col, 1.0)
            for k in range(1, arm + 1):
                a = 0.55 if k == 1 else 0.25
                for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                    self.blend(x + dx, y + dy, col, a)

    def blend(self, x, y, col, a):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img[y, x] = self.img[y, x] + (col - self.img[y, x]) * a

    def occupied(self, x, y, pad=2):
        for (cx, cy, r) in self.keepout:
            if (x - cx) ** 2 + (y - cy) ** 2 < (r + pad) ** 2:
                return True
        return False

    def planet(self, cx, cy, r, tilt=-0.32):
        """A banded planet lit from the lower right, with rings."""
        xx, yy, b = self.xx, self.yy, self.b
        dx, dy = (xx - cx) / r, (yy - cy) / r
        ca, sa = math.cos(tilt), math.sin(tilt)
        # ring-plane coordinates: u along the ring, v across it
        ru = dx * ca + dy * sa
        rv = -dx * sa + dy * ca
        flat = 0.24
        rr = np.sqrt(ru ** 2 + (rv / flat) ** 2)
        ring_mask = ((rr > 1.30) & (rr < 1.52)) | ((rr > 1.60) & (rr < 2.02)) | ((rr > 2.08) & (rr < 2.18))
        ring_shade = np.where(rr < 1.55, 0.42, np.where(rr < 2.05, 0.82, 0.60))
        # Cassini-like fine gaps
        ring_shade = ring_shade - 0.18 * ((rr > 1.78) & (rr < 1.82))
        disc = dx ** 2 + dy ** 2 <= 1.0
        front = rv > 0              # the half of the ring nearer to us

        # back half of the ring, behind the planet
        back = ring_mask & ~front & ~disc
        self.paint_ring(back, ring_shade, ru)

        # the planet
        dz = np.sqrt(np.clip(1 - dx ** 2 - dy ** 2, 0, 1))
        L = np.array([0.55, 0.45, 0.70])
        L = L / np.linalg.norm(L)
        light = np.clip(dx * L[0] + dy * L[1] + dz * L[2], 0, 1)
        # the ring throws a shadow band across the planet
        shadow_v = rv + 0.10
        ring_shadow = (np.abs(shadow_v) < 0.07) | ((np.abs(shadow_v) > 0.13) & (np.abs(shadow_v) < 0.17))
        light = light * np.where(ring_shadow & (rv < 0.25), 0.55, 1.0)
        # latitude bands, along the ring tilt
        lat = rv
        band_id = (np.floor((lat + 1.2) * 5.3 + 0.6 * np.sin(ru * 3.1)) % 3).astype(int)
        t = light ** 0.85
        for k in range(3):
            m = disc & (band_id == k)
            ramp = PLANET_BANDS[k]
            idx = dither_index(t[m], len(ramp), b[m])
            self.img[m] = ramp[idx]
        # rim of atmosphere on the lit limb
        rim = disc & (dx ** 2 + dy ** 2 > 0.86) & (light > 0.35)
        self.img[rim] = self.img[rim] * 0.5 + np.array(P.rgb("#FFB0D0")) * 0.5

        # front half of the ring, over the planet
        frontm = ring_mask & front
        self.paint_ring(frontm, ring_shade, ru)
        self.keepout.append((cx, cy, r * 1.15))

    def paint_ring(self, mask, shade, ru):
        t = np.clip(shade + 0.18 * ru, 0, 1)
        idx = dither_index(t[mask], len(RING), self.b[mask])
        self.img[mask] = RING[idx]

    def moon(self, cx, cy, r):
        dx, dy = (self.xx - cx) / r, (self.yy - cy) / r
        disc = dx ** 2 + dy ** 2 <= 1
        dz = np.sqrt(np.clip(1 - dx ** 2 - dy ** 2, 0, 1))
        L = np.array([-0.62, 0.52, 0.30])
        L = L / np.linalg.norm(L)
        light = np.clip(dx * L[0] + dy * L[1] + dz * L[2], 0, 1)
        t = 0.12 + 0.88 * light
        idx = dither_index(t[disc], len(MOON), self.b[disc])
        self.img[disc] = MOON[idx]
        # two craters
        for ox, oy, cr in ((-0.35, 0.25, 0.22), (-0.05, 0.55, 0.14)):
            c = disc & ((dx - ox) ** 2 + (dy - oy) ** 2 < cr ** 2)
            self.img[c] = self.img[c] * 0.80
        self.keepout.append((cx, cy, r * 1.4))

    def shooting_star(self, x0, y0, length, angle):
        ca, sa = math.cos(angle), math.sin(angle)
        for i in range(int(length)):
            a = (1 - i / length) ** 1.6
            x, y = round(x0 + ca * i), round(y0 + sa * i)
            if a > BAYER[y % 4, x % 4] * 0.9:
                self.blend(x, y, np.array(P.rgb("#FFFFFF")), min(1, a * 1.1))
            if i < length * 0.4:
                self.blend(x, y + 1, np.array(P.rgb(P.SKY)), a * 0.35)

    def sun(self, cx, cy, r):
        dx, dy = self.xx - cx, self.yy - cy
        disc = dx ** 2 + dy ** 2 <= r * r
        top, bottom = cy - r, self.horizon
        # gold at the top of what shows, pink where it meets the horizon
        t = np.clip((self.yy - top) / (bottom - top), 0, 1)
        idx = dither_index(t, len(SUN), self.b)
        # slats cut across the lower part of the visible disc, widening downwards
        slats = np.zeros_like(disc)
        y, k = top + (bottom - top) * 0.42, 0
        while y < bottom:
            gap = (1 + k) * self.u
            slats |= (self.yy >= round(y)) & (self.yy < round(y + gap))
            y += gap + max(2.0, 5 - k) * self.u
            k += 1
        show = disc & ~slats & (self.yy < bottom)
        self.img[show] = SUN[idx[show]]
        # a dithered halo
        d = np.sqrt(dx ** 2 + dy ** 2)
        halo = (d > r) & (d < r * 1.3) & (self.yy < bottom)
        a = np.clip(1 - (d - r) / (r * 0.3), 0, 1) ** 1.5 * 0.7
        on = halo & (a > self.b)
        self.img[on] = self.img[on] * 0.5 + np.array(P.rgb("#FF8A66")) * 0.5

    def mountains(self):
        """Two far ranges, opening into a valley where the sun sets."""
        w, h, u, rng = self.w, self.h, self.u, self.rng
        hz = self.horizon
        x = np.arange(w)
        valley = np.exp(-((x - self.cx) / (w * 0.13)) ** 2)
        sunward = lambda xs: 0.30 + 0.70 * np.exp(-((xs - self.cx) / (w * 0.28)) ** 2)

        # Distant peaks: tall, jagged, pale with distance, rim-lit by the sun.
        edges = (np.abs(x - self.cx) / (w / 2)) ** 1.5
        peaks = midpoint_ridge(rng, w, 0.62, hz - 62 * u, hz - 12 * u) - edges * 22 * u
        peaks = peaks + valley * (hz - peaks) * 0.92
        self.fill_ridge(peaks, hexes("#4A2463", "#3C1F57", "#30194B"), rim="#FF8A70",
                        rim_strength=sunward, depth=26 * u, shade_lit=True)

        # Far hills: darker and lower, in front of the peaks.
        hills = midpoint_ridge(rng, w, 0.55, hz - 26 * u, hz - 4 * u)
        hills = hills + valley * (hz - hills) * 0.98
        self.fill_ridge(hills, hexes("#2A1642", "#231338", "#1D1030"), rim="#D0507A",
                        rim_strength=lambda xs: 0.6 * sunward(xs), depth=14 * u)

    def fill_ridge(self, ridge, cols, rim=None, rim_strength=None, depth=None, shade_lit=False):
        """Fill everything below a ridgeline with a dithered vertical ramp.
        With shade_lit, slopes facing the sun (the middle of the screen) are
        drawn a shade lighter than slopes facing away."""
        h = self.h
        top = np.round(ridge).astype(int)
        depth = depth or h * 0.10
        rim_c = np.array(P.rgb(rim)) if rim else None
        smooth = np.convolve(ridge, np.ones(7) / 7, mode="same")
        for x in range(self.w):
            y0 = max(0, top[x])
            if y0 >= h:
                continue
            t = np.clip(np.arange(h - y0) / depth, 0, 1)
            if shade_lit:
                # slope of the smoothed ridge: faces turned to the sun are lighter
                a, b = max(0, x - 5), min(self.w - 1, x + 5)
                slope = (smooth[b] - smooth[a]) / max(1, b - a)
                facing = -slope if x < self.cx else slope
                t = np.clip(t + (0.32 if facing > 0.15 else 0.0), 0, 1)
            idx = dither_index(t, len(cols), self.b[y0:, x])
            self.img[y0:, x] = cols[idx]
            if rim_c is not None:
                s = float(np.atleast_1d(rim_strength(np.array([x])))[0])
                self.img[y0, x] = self.img[y0, x] + (rim_c - self.img[y0, x]) * s
                steep = x > 0 and abs(top[x] - top[x - 1]) > 1
                if steep and y0 + 1 < h:
                    self.img[y0 + 1, x] = self.img[y0 + 1, x] + (rim_c - self.img[y0 + 1, x]) * s * 0.5
        return top

    def lake(self):
        """Still water from the horizon down, holding the sun's reflection."""
        w, h, u, rng = self.w, self.h, self.u, self.rng
        top = self.horizon
        water = self.yy >= top
        depth = np.clip((self.yy - top) / (h - top), 0, 1)
        t = 0.42 - 0.34 * depth ** 0.7
        idx = dither_index(t, len(SKY), self.b)
        self.img[water] = SKY[idx[water]]
        # the reflection: broken horizontal strokes under the sun
        y, k = top + 1, 0
        while y < h:
            half = self.sun_r * (1.05 - 0.50 * (y - top) / (h - top)) * rng.uniform(0.55, 1.0)
            off = rng.uniform(-3, 3) * u
            col = SUN[min(len(SUN) - 1, 1 + k % 5)]
            for x in range(max(0, int(self.cx - half + off)), min(w, int(self.cx + half + off))):
                if rng.uniform() > 0.15:
                    a = 0.9 * (1 - abs(x - self.cx - off) / (half + 1)) ** 0.5
                    self.blend(x, int(y), col, a)
            y += int(rng.integers(2, 4) * u)
            k += 1
        # a glint along the waterline, brightest under the sun
        glint = np.array(P.rgb("#FF9A70"))
        for x in range(w):
            a = 0.75 * math.exp(-((x - self.cx) / (w * 0.16)) ** 2)
            if a > 0.05:
                self.blend(x, top, glint, a)
        # faint ripples catching the sky elsewhere
        for _ in range(int(w * 0.35)):
            x = int(rng.uniform(0, w))
            yy = int(top + 3 * u + rng.uniform(0, 1) ** 1.5 * (h - top - 3 * u))
            ln = int(rng.uniform(2, 7) * u)
            for i in range(ln):
                self.blend(x + i, yy, np.array(P.rgb("#5A2A66")), 0.35)

    def foreground(self):
        """Near hills, black against the water: pines on the left, the
        observatory on the right."""
        w, h, u, rng = self.w, self.h, self.u, self.rng
        x = np.arange(w)
        left = h - np.clip(1 - x / (w * 0.30), 0, 1) ** 1.5 * 50 * u
        peak = w * 0.80
        right = h - np.clip(1 - np.abs(x - peak) / (w * 0.20), 0, 1) ** 0.75 * 58 * u
        right = np.minimum(right, h - np.clip((x - peak) / (w * 0.20), 0, 1) * 58 * u)
        ridge = np.minimum(left, right) + midpoint_ridge(rng, w, 0.6, 0, 5 * u)
        # flatten a shelf for the observatory to stand on
        shelf = np.abs(x - peak) < 22 * u
        ridge[shelf] = ridge[int(peak)] if not shelf.all() else ridge[shelf]
        ridge[shelf] = np.min(ridge[shelf])
        near = hexes("#0D0A18", "#0A0813", "#07060E")
        self.fill_ridge(ridge, near, rim="#4A2558", rim_strength=lambda xs: 0.7, depth=30 * u)
        self.pines(ridge, int(w * 0.015), int(w * 0.24), 0.7)
        self.pines(ridge, int(peak + 28 * u), int(w * 0.98), 0.45)
        self.pines(ridge, int(w * 0.62), int(peak - 30 * u), 0.35)
        self.observatory(int(peak), int(ridge[int(peak)]))

    def pines(self, ridge, x0, x1, density):
        w, u, rng = self.w, self.u, self.rng
        col = np.array(P.rgb("#06050B"))
        rim = np.array(P.rgb("#3A1E4A"))
        step = max(3, int(4.5 * u))
        for x in range(x0, x1, step):
            if rng.uniform() > density:
                continue
            x += int(rng.uniform(-1, 1) * u)
            if not 0 <= x < w:
                continue
            base = int(ridge[x]) + int(2 * u)
            th = int(rng.uniform(10, 19) * u)
            for j in range(th):
                # three tiers of branches, each widening downwards
                tier = (j * 3) // th
                frac = ((j * 3) % th) / th
                half = int((0.6 + tier * 0.9 + frac * 1.4) * u)
                y = base - th + j
                for dx in range(-half, half + 1):
                    if 0 <= x + dx < w and 0 <= y < self.h:
                        self.img[y, x + dx] = col
                if j % 2 == 0:
                    self.blend(x - half, y, rim, 0.7)
            for j in range(int(3 * u)):           # trunk
                self.blend(x, base + j, col, 1)

    def observatory(self, x, ground):
        """A domed observatory, slit open and lit, telescope out."""
        s = 1.6 * self.u
        R = int(11 * s)
        body_w, body_h = 2 * R + int(4 * s), int(10 * s)
        dome_c = np.array(P.rgb("#1D1733"))
        dome_hi = np.array(P.rgb("#8A4A84"))
        body_c = np.array(P.rgb("#100C1E"))
        trim = np.array(P.rgb("#2C2346"))
        gold = np.array(P.rgb(P.GOLD))
        amber = np.array(P.rgb(P.AMBER))
        tube = np.array(P.rgb("#3A2F55"))
        top_body = ground - body_h

        def box(x0, y0, x1, y1, c, a=1.0):
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    self.blend(xx, yy, c, a)

        # annex to the right, flat roofed
        ax0, ax1 = x + body_w // 2 - int(2 * s), x + body_w // 2 + int(12 * s)
        box(ax0, ground - int(7 * s), ax1, ground + 3, body_c)
        box(ax0, ground - int(7 * s), ax1, ground - int(6 * s), trim)
        box(ax1 - int(6 * s), ground - int(5 * s), ax1 - int(3 * s), ground - int(2 * s), amber, 0.9)
        # main drum
        box(x - body_w // 2, top_body, x + body_w // 2, ground + 3, body_c)
        box(x - body_w // 2, top_body, x + body_w // 2, top_body + max(1, int(s)), trim)
        # dome, shaded from the left where the sunset is
        cy = top_body
        for yy in range(cy - R, cy + 1):
            for xx in range(x - R, x + R + 1):
                d2 = (xx - x) ** 2 + (yy - cy) ** 2
                if d2 <= R * R:
                    nx = (xx - x) / R
                    lit = max(0.0, -nx) * 0.55
                    c = dome_c + (dome_hi - dome_c) * lit
                    if lit > 0 and (lit * 1.6) % 1 < BAYER[yy % 4, xx % 4] * 0.5:
                        c = dome_c + (dome_hi - dome_c) * lit * 0.6
                    self.blend(xx, yy, c, 1)
                    if d2 > (R - 1.1) ** 2 and xx < x:
                        self.blend(xx, yy, np.array(P.rgb("#C0607E")), 0.85)
        # ribs
        for ang in (-0.55, 0.55):
            for i in range(R):
                xx = int(x + math.sin(ang) * i * 0.95)
                yy = int(cy - math.cos(ang) * i * 0.95)
                if (xx - x) ** 2 + (yy - cy) ** 2 < (R - 1) ** 2:
                    self.blend(xx, yy, trim, 0.7)
        # the slit, lit gold from inside, and the telescope
        sw = max(2, int(2.5 * s))
        sx = x + int(2 * s)
        box(sx, cy - R + 1, sx + sw, cy + 1, gold)
        box(sx, cy - int(R * 0.45), sx + sw, cy + 1, amber, 0.6)
        for i in range(int(R * 0.95)):
            tx = sx + sw // 2 - 1 - int(i * 0.30)
            ty = cy - int(R * 0.30) - i
            for k in range(max(2, int(1.6 * s))):
                self.blend(tx + k, ty, tube, 1)
        # glow spilling out of the slit
        for yy in range(cy - R - int(9 * s), cy + 1):
            for xx in range(x - int(10 * s), x + int(12 * s)):
                if (xx - x) ** 2 + (yy - cy) ** 2 <= R * R:
                    continue
                d = math.hypot(xx - sx, (yy - (cy - R * 0.6)) * 0.9)
                a = max(0.0, 1 - d / (10 * s)) * 0.32
                if a > BAYER[yy % 4, xx % 4] * 0.5:
                    self.blend(xx, yy, amber, a)
        # windows and door in the drum
        for wx in (x - body_w // 2 + int(4 * s), x + body_w // 2 - int(7 * s)):
            box(wx, top_body + int(3 * s), wx + int(3 * s), top_body + int(6 * s), amber, 0.95)
        box(x - int(2 * s), ground - int(6 * s), x + int(2 * s), ground + 3, np.array(P.rgb("#251C33")))
        box(x - int(2 * s), ground - int(6 * s), x + int(2 * s), ground - int(5 * s), gold, 0.6)
        # a mast with a red light
        box(ax1 - int(3 * s), ground - int(16 * s), ax1 - int(3 * s) + max(1, int(0.6 * s)), ground - int(7 * s), trim)
        self.blend(ax1 - int(3 * s), ground - int(17 * s), np.array(P.rgb(P.PINK)), 1)

    # ------------------------------------------------------------- whole
    def paint(self):
        w, h, u = self.w, self.h, self.u
        self.keepout = []
        self.sky()
        self.nebula()
        pr = 58 * u
        self.planet(min(w * 0.16, w / 2 - 175 * u), h * 0.30, pr)
        self.moon(w * 0.715, h * 0.20, 9 * u)
        self.stars()
        self.shooting_star(w * 0.84, h * 0.09, 34 * u, math.radians(158))
        self.sun_r = 34 * u
        self.sun(self.cx, self.horizon - 2 * u, self.sun_r)
        self.mountains()
        self.lake()
        self.foreground()
        return np.clip(self.img, 0, 255).astype(np.uint8)


SIZES = [
    # width, height, art pixel size
    (3440, 1440, 4), (2560, 1080, 3), (5120, 1440, 4),
    (1920, 1080, 3), (2560, 1440, 4), (3840, 2160, 6),
    (1920, 1200, 3), (2560, 1600, 4), (1366, 768, 2), (1280, 800, 2),
]


def render(width, height, scale):
    w, h = math.ceil(width / scale), math.ceil(height / scale)
    art = Painter(w, h).paint()
    im = Image.fromarray(art, "RGB").resize((w * scale, h * scale), Image.NEAREST)
    return im.crop((0, 0, width, height)), Image.fromarray(art, "RGB")


def metadata():
    import json
    return json.dumps({
        "KPlugin": {
            "Authors": [{"Name": P.AUTHOR}],
            "Id": P.NAME,
            "License": "CC-BY-SA-4.0",
            "Name": "%s Dusk" % P.NAME,
        }
    }, indent=4) + "\n"


def build(out, sizes=SIZES):
    d = Path(out) / "wallpapers" / P.NAME
    (d / "contents" / "images").mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text(metadata())
    first = None
    for (wd, ht, sc) in sizes:
        im, art = render(wd, ht, sc)
        im.save(d / "contents" / "images" / ("%dx%d.png" % (wd, ht)), optimize=True)
        if first is None:
            first = im
    first.resize((400, round(400 * first.height / first.width)), Image.LANCZOS).save(
        d / "contents" / "screenshot.png")


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "theme"
    if len(sys.argv) > 2 and sys.argv[2] == "quick":
        build(out, SIZES[:1])
    else:
        build(out)
