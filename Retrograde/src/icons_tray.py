"""The system tray's icons: one-colour pixel glyphs.

The tray and the applets' popups show symbolic icons: one colour, which Plasma
sets from the colour scheme as it draws them, so that they turn dark on a light
popup and follow the selection.  The theme's other icons are sprites in fixed
colours and cannot do that, so these are drawn apart, in ColorScheme-Text,
with ColorScheme-NegativeText and -NeutralText for warnings, and the text
colour faint for the parts of a level not reached, as Breeze does.

They are drawn on an 11-cell grid: at the tray's usual 22 px one cell is 2x2
screen pixels, the pixel of the window frame and of the 48 px icons.  The
strokes are one cell, the weight of Breeze's.

A family of states -- battery levels, signal strengths, volume -- is one
drawing with parts switched on and off, so that its states match; a lock,
a warning or a cross is a badge in the bottom right corner.
"""

import math

import palette as P

N = 11
FAINT = 0.35

# A glyph is N rows of N characters: '#' the text colour, '+' the same faint,
# 'r' the negative colour, 'y' the neutral one, '.' nothing.
STYLE = {"#": ("ColorScheme-Text", 1.0), "+": ("ColorScheme-Text", FAINT),
         "r": ("ColorScheme-NegativeText", 1.0), "y": ("ColorScheme-NeutralText", 1.0)}
COLOURS = {"ColorScheme-Text": P.TEXT, "ColorScheme-NegativeText": P.RED,
           "ColorScheme-NeutralText": P.AMBER}


# ---------------------------------------------------------------- helpers

def blank():
    return [["."] * N for _ in range(N)]


def grid(rows):
    assert len(rows) == N and all(len(r) == N for r in rows), rows
    return [list(r) for r in rows]


def cells(rows, ch="#", at=(0, 0)):
    """The cells of a map that are `ch`, moved by `at`."""
    return {(x + at[0], y + at[1]) for y, r in enumerate(rows) for x, c in enumerate(r) if c == ch}


def paint(g, where, ch):
    for x, y in where:
        if 0 <= x < N and 0 <= y < N:
            g[y][x] = ch
    return g


def faint(g):
    """Everything drawn, faint: a thing that is off or not there."""
    return [["+" if c != "." else c for c in row] for row in g]


def badge(g, rows, ch):
    """A small map in the bottom right corner, with a cell cleared above and
    to the left of it so that it stands apart from the glyph."""
    h, w = len(rows), len(rows[0])
    x0, y0 = N - w, N - h
    for y in range(y0 - 1, N):
        for x in range(x0 - 1, N):
            g[y][x] = "."
    for (x, y) in cells(rows, at=(x0, y0)):
        g[y][x] = ch
    return g


def struck(g, ch="#"):
    """Faint, with a stroke across: switched off."""
    g = faint(g)
    for i in range(1, N - 1):
        g[i][i] = ch
        if i + 1 < N:
            g[i][i + 1] = "."      # a gap along the stroke, so it reads over the glyph
    return g


def disc(cx, cy, r):
    return {(x, y) for y in range(N) for x in range(N)
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r}


LOCK = ["###", "#.#", "###", "###"]
CROSS = ["#.#", ".#.", "#.#"]
BANG = ["#", "#", ".", "#"]
BOLT = ["..##", ".##.", "####", ".##.", "##.."]


def locked(g):
    return badge(g, LOCK, "#")


def limited(g):
    return badge(g, BANG, "y")


def crossed(g):
    return badge(g, CROSS, "r")


# ---------------------------------------------------------------- sound

SPEAKER = cells(["....#", "...##", "..###", "#####", "#####", "#####", "..###", "...##", "....#"],
                at=(0, 1))
WAVES = [
    {(6, 4), (6, 5), (6, 6)},
    {(7, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (7, 8)},
    {(9, 1), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (10, 8), (9, 9)},
]


def volume(lit, ch="#"):
    g = paint(blank(), SPEAKER, "#")
    for i, wave in enumerate(WAVES):
        paint(g, wave, ch if i < lit else "+")
    return g


def muted():
    g = paint(blank(), SPEAKER, "#")
    return paint(g, cells(["#...#", ".#.#.", "..#..", ".#.#.", "#...#"], at=(6, 3)), "r")


MIC = [
    "....###....",
    "...#...#...",
    "...#...#...",
    "...#...#...",
    ".#.#...#.#.",
    ".#.#...#.#.",
    ".#..###..#.",
    "..#.....#..",
    "...#####...",
    ".....#.....",
    "...#####...",
]


def mic(level):
    """The microphone, its capsule filled `level` rows of five from the bottom."""
    g = grid(MIC)
    for i in range(level):
        paint(g, {(4, 5 - i), (5, 5 - i), (6, 5 - i)}, "#")
    return g


# ---------------------------------------------------------------- networks

# The Wi-Fi fan: the dot, then three arcs, lit from the dot outwards.
WIFI = [
    {(5, 9)},
    {(4, 6), (5, 6), (6, 6), (3, 7), (7, 7)},
    {(3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (2, 5), (8, 5)},
    {(2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (1, 3), (9, 3), (0, 4), (10, 4)},
]


def lit_for(percent, parts=4):
    return 0 if percent <= 0 else min(parts, math.ceil(percent * parts / 100))


def wifi(lit):
    g = blank()
    for i, part in enumerate(WIFI):
        paint(g, part, "#" if i < lit else "+")
    return g


PORT = [
    "...........",
    ".#########.",
    ".#.......#.",
    ".#.#.#.#.#.",
    ".#.#.#.#.#.",
    ".#.......#.",
    ".#.......#.",
    ".###...###.",
    "...#...#...",
    "...#####...",
    "...........",
]

# Mobile signal: four bars, two cells wide, rising to the right.
BARS = [{(x, y) for x in (c, c + 1) for y in range(top, 10)} for c, top in ((0, 7), (3, 5), (6, 3), (9, 1))]
TECH = {
    "5g": ["###", "#..", "###", "..#", "###"],
    "edge": ["###", "#..", "##.", "#..", "###"],
    "gprs": ["###", "#..", "#.#", "#.#", "###"],
    "hsdpa": ["#.#", "#.#", "###", "#.#", "#.#"],
    "lte": ["#.#", "#.#", "###", "..#", "..#"],
    "umts": ["###", "..#", ".##", "..#", "###"],
}
TECH["hspa"] = TECH["hsupa"] = TECH["hsdpa"]


def mobile(lit, tech=None, lock=False):
    g = blank()
    for i, bar in enumerate(BARS):
        paint(g, bar, "#" if i < lit else "+")
    if tech:
        paint(g, cells(TECH[tech]), "#")
    elif lock:
        paint(g, cells(LOCK), "#")
    return g


RUNE = [
    "...........",
    ".....#.....",
    ".....##....",
    "...#.#.#...",
    "....###....",
    ".....#.....",
    "....###....",
    "...#.#.#...",
    ".....##....",
    ".....#.....",
    "...........",
]


def bluetooth(connected):
    g = grid(RUNE)
    return paint(g, {(1, 5), (9, 5)}, "#") if connected else g


PLANE = [
    ".....#.....",
    "....###....",
    "....###....",
    "...#####...",
    ".#########.",
    "###########",
    "....###....",
    "....###....",
    "...#####...",
    "..##...##..",
    "...........",
]


# ---------------------------------------------------------------- power

def battery(percent, charging=False):
    """A battery on its side, filled from the left: red at 10% and below,
    amber at 20%.  Charging, a bolt in the corner, which leaves the level
    readable (cut through the fill, the bolt hid it)."""
    g = blank()
    body = {(x, y) for x in range(10) for y in (2, 8)} | {(x, y) for x in (0, 9) for y in range(2, 9)}
    paint(g, body | {(10, 4), (10, 5), (10, 6)}, "#")
    w = round(percent * 6 / 100)
    if percent > 0:
        w = max(w, 1)
    ch = "r" if percent <= 10 else "y" if percent <= 20 else "#"
    fill = {(2 + x, y) for x in range(w) for y in range(4, 7)}
    paint(g, fill, ch)
    return badge(g, BOLT, "#") if charging else g


def battery_missing():
    g = blank()
    body = {(x, y) for x in range(10) for y in (2, 8)} | {(x, y) for x in (0, 9) for y in range(2, 9)}
    paint(g, body | {(10, 4), (10, 5), (10, 6)}, "#")
    return paint(g, cells(CROSS, at=(3, 4)), "r")


SUN = [
    ".....#.....",
    ".#...#...#.",
    "..#.....#..",
    "....###....",
    "...#####...",
    "##.#####.##",
    "...#####...",
    "....###....",
    "..#.....#..",
    ".#...#...#.",
    ".....#.....",
]
SUN_DIM = [
    "...........",
    ".....#.....",
    "..#.....#..",
    "....###....",
    "...#...#...",
    ".#.#...#.#.",
    "...#...#...",
    "....###....",
    "..#.....#..",
    ".....#.....",
    "...........",
]


def moon():
    """A crescent, opening to the upper right."""
    return paint(blank(), disc(5.0, 5.5, 4.6) - disc(7.4, 3.6, 3.7), "#")


CUP = [
    "..#..#.....",
    "...#..#....",
    "..#..#.....",
    "...........",
    "#######....",
    "#.....####.",
    "#.....#..#.",
    "#.....####.",
    "#.....#....",
    ".#...#.....",
    "..###......",
]


# ---------------------------------------------------------------- the rest

BELL = [
    "....###....",
    "...#...#...",
    "..#.....#..",
    "..#.....#..",
    "..#.....#..",
    "..#.....#..",
    ".#.......#.",
    ".#.......#.",
    "###########",
    "...........",
    "....###....",
]


def bell(ringing):
    g = grid(BELL)
    if ringing:
        for y in range(1, 8):
            row = "".join(g[y])
            a, b = row.index("#"), row.rindex("#")
            paint(g, {(x, y) for x in range(a, b)}, "#")
    return g


CLIPBOARD = [
    "...#####...",
    ".###...###.",
    ".#.#####.#.",
    ".#.......#.",
    ".#.#####.#.",
    ".#.......#.",
    ".#.#####.#.",
    ".#.......#.",
    ".#.###...#.",
    ".#.......#.",
    ".#########.",
]

PHONE = [
    ".#####.....",
    ".#...#.....",
    ".#...#..#..",
    ".#...#...#.",
    ".#...#.#.#.",
    ".#...#.#.#.",
    ".#...#.#.#.",
    ".#...#...#.",
    ".#####..#..",
    ".#.#.#.....",
    ".#####.....",
]

VAULT = [
    "...........",
    "###########",
    "#.........#",
    "#...###...#",
    "#..#...#..#",
    "#..#.#.#..#",
    "#..#...#..#",
    "#...###...#",
    "#.........#",
    "###########",
    ".#.......#.",
]

EJECT = [
    ".....#.....",
    "....###....",
    "...#####...",
    "..#######..",
    "...........",
    "..#######..",
    "...........",
    ".#########.",
    ".#.......#.",
    ".#.....#.#.",
    ".#########.",
]

PRINTER = [
    "...........",
    "..#######..",
    "..#.....#..",
    "###########",
    "#.........#",
    "#.......#.#",
    "#.........#",
    "#.#######.#",
    "###.....###",
    "..#.....#..",
    "..#######..",
]

PERSON = [
    "...........",
    "....###....",
    "...#...#...",
    "...#...#...",
    "...#...#...",
    "....###....",
    "...........",
    "..#######..",
    ".#.......#.",
    ".#.......#.",
    ".#########.",
]

CAPS = [
    ".....#.....",
    "....#.#....",
    "...#...#...",
    "..#.....#..",
    ".###...###.",
    "...#...#...",
    "...#...#...",
    "...#####...",
    "...........",
    "...#####...",
    "...........",
]

KEYCAP = [
    "...........",
    ".#########.",
    ".#.......#.",
    ".#...#...#.",
    ".#..##...#.",
    ".#...#...#.",
    ".#...#...#.",
    ".#..###..#.",
    ".#.......#.",
    ".#########.",
    "...........",
]

KEYBOARD = [
    "...........",
    "...........",
    "###########",
    "#.........#",
    "#.#.#.#.#.#",
    "#.........#",
    "#.#.#.#.#.#",
    "#.........#",
    "#..#####..#",
    "#.........#",
    "###########",
]

TOUCHPAD = [
    "...........",
    ".#########.",
    ".#.......#.",
    ".#.......#.",
    ".#.......#.",
    ".#.......#.",
    ".#.......#.",
    ".#########.",
    ".#...#...#.",
    ".#########.",
    "...........",
]

CAMERA = [
    "...........",
    "...........",
    "#######....",
    "#.....#..##",
    "#.....#.###",
    "#.....#####",
    "#.....#.###",
    "#.....#..##",
    "#######....",
    "...........",
    "...........",
]


def camera(on):
    g = grid(CAMERA)
    return paint(g, {(x, y) for x in range(1, 6) for y in range(3, 8)}, "#") if on else g


# The colour picker widget's pipette: bulb, collar, glass and tip along one
# diagonal.  The widget's divider and colour circle are its own drawing.
PIPETTE = [
    "........##.",
    ".......####",
    "....#..####",
    ".....#.###.",
    ".....##....",
    "....##.#...",
    "...##...#..",
    "..##.......",
    ".##........",
    ".#.........",
    "#..........",
]

PLAY = [
    "...........",
    "...#.......",
    "...##......",
    "...###.....",
    "...####....",
    "...#####...",
    "...####....",
    "...###.....",
    "...##......",
    "...#.......",
    "...........",
]
PAUSE = ["..###.###.." if 1 <= y <= 9 else "..........." for y in range(N)]
STOP = ["..#######.." if 2 <= y <= 8 else "..........." for y in range(N)]

ARROW = [
    "....###....",
    "....###....",
    "....###....",
    "....###....",
    ".#########.",
    "..#######..",
    "...#####...",
    "....###....",
    ".....#.....",
    "...........",
    "###########",
]
CHECK = [
    "...........",
    "...........",
    ".........#.",
    "........##.",
    ".......##..",
    ".#....##...",
    ".##..##....",
    "..####.....",
    "...##......",
    "...........",
    "...........",
]


# ---------------------------------------------------------------- names

def icons():
    """{icon name: glyph}, every name also under its -symbolic form."""
    out = {}

    def put(names, g):
        for name in names.split():
            out[name] = g

    # Sound.
    put("audio-volume-high audio-on", volume(3))
    put("audio-volume-medium", volume(2))
    put("audio-volume-low", volume(1))
    put("audio-ready", volume(0))
    put("audio-volume-muted audio-off", muted())
    put("audio-volume-high-warning", volume(3, "y"))
    put("audio-volume-high-danger", volume(3, "r"))
    put("microphone-sensitivity-high mic-on", mic(5))
    put("microphone-sensitivity-medium", mic(3))
    put("microphone-sensitivity-low", mic(1))
    put("mic-ready", mic(0))
    put("microphone-sensitivity-muted mic-off", struck(mic(0), "r"))

    # Wi-Fi.
    for p in (0, 20, 40, 60, 80, 100):
        put("network-wireless-%d network-wireless-connected-%02d" % (p, p), wifi(lit_for(p)))
        put("network-wireless-%d-locked" % p, locked(wifi(lit_for(p))))
        put("network-wireless-%d-limited" % p, limited(wifi(lit_for(p))))
    for p in (25, 50, 75):
        put("network-wireless-connected-%d" % p, wifi(lit_for(p)))
    for word, p in (("none", 0), ("weak", 25), ("ok", 50), ("good", 75), ("excellent", 100)):
        put("network-wireless-signal-%s" % word, wifi(lit_for(p)))
    for p in (0, 25, 50, 75, 100):
        put("nm-signal-%02d" % p, wifi(lit_for(p)))
    put("network-wireless-on", wifi(4))
    put("network-wireless-available network-wireless-acquiring", faint(wifi(4)))
    put("network-wireless-disconnected", crossed(faint(wifi(4))))
    put("network-wireless-off", struck(wifi(4)))

    # Wired, and the network as a whole.
    put("network-wired network-wired-activated nm-device-wired", grid(PORT))
    put("network-wired-activated-limited network-limited", limited(grid(PORT)))
    put("network-wired-activated-locked", locked(grid(PORT)))
    put("network-wired-available network-wired-unavailable network-unavailable", faint(grid(PORT)))
    put("network-wired-disconnected network-offline nm-no-connection", crossed(faint(grid(PORT))))

    # Mobile broadband.
    for p in (0, 20, 40, 60, 80, 100):
        lit = lit_for(p)
        put("network-mobile-%d" % p, mobile(lit))
        put("network-mobile-%d-locked" % p, mobile(lit, lock=True))
        for tech in TECH:
            put("network-mobile-%d-%s network-mobile-%d-%s-locked" % (p, tech, p, tech), mobile(lit, tech))
    put("network-mobile-on", mobile(4))
    put("network-mobile-available", faint(mobile(4)))
    put("network-mobile-off", struck(mobile(4)))

    # Bluetooth and flight mode.
    put("network-bluetooth", bluetooth(False))
    put("network-bluetooth-activated network-bluetooth-activated-locked", bluetooth(True))
    put("network-bluetooth-inactive", faint(bluetooth(False)))
    put("flightmode-on network-flightmode-on", grid(PLANE))
    put("flightmode-off network-flightmode-off", faint(grid(PLANE)))

    # Battery: every level, charging or not, under every power profile.
    for p in range(0, 101, 10):
        for charging in (False, True):
            name = "battery-%03d%s" % (p, "-charging" if charging else "")
            put(" ".join([name] + ["%s-profile-%s" % (name, prof)
                                   for prof in ("balanced", "performance", "powersave")]),
                battery(p, charging))
    for word, p in (("empty", 0), ("caution", 10), ("low", 20), ("good", 60), ("full", 100)):
        put("battery-%s" % word, battery(p))
        put("battery-%s-charging" % word, battery(p, True))
    put("battery-missing", battery_missing())
    put("system-suspend-inhibited", grid(CUP))
    put("system-suspend-uninhibited", faint(grid(CUP)))

    # Brightness and Night Light.
    put("brightness-high redshift-status-day", grid(SUN))
    put("brightness-low", grid(SUN_DIM))
    put("redshift-status-on", moon())
    put("redshift-status-off", faint(moon()))

    # Notifications, the clipboard, KDE Connect, the vault, removable devices.
    put("notification-active notification-progress-active", bell(True))
    put("notification-inactive notification-empty notification-progress-inactive notifications",
        bell(False))
    put("notification-disabled notifications-disabled", struck(bell(False)))
    put("klipper-symbolic", grid(CLIPBOARD))
    put("kdeconnect-tray kdeconnect-symbolic", grid(PHONE))
    put("plasmavault-symbolic", grid(VAULT))
    put("plasmavault_error", paint(grid(VAULT), cells(VAULT) & {(x, y) for x in range(3, 8)
                                                               for y in range(3, 8)}, "r"))
    put("device-notifier", grid(EJECT))
    put("printer-symbolic", grid(PRINTER))
    put("im-user", grid(PERSON))
    put("color-picker", grid(PIPETTE))

    # Keyboard, touchpad, camera, media, updates.
    put("input-caps-on", grid(CAPS))
    put("input-num-on input-combo-on", grid(KEYCAP))
    put("input-keyboard-virtual input-keyboard-virtual-on", grid(KEYBOARD))
    put("input-keyboard-virtual-off", struck(grid(KEYBOARD)))
    put("input-touchpad-on touchpad_enabled", grid(TOUCHPAD))
    put("input-touchpad-off touchpad_disabled", struck(grid(TOUCHPAD)))
    put("camera-on", camera(True))
    put("camera-ready", camera(False))
    put("camera-off", struck(camera(False)))
    put("media-playback-playing", grid(PLAY))
    put("media-playback-paused", grid(PAUSE))
    put("media-playback-stopped", grid(STOP))
    put("update-none", grid(CHECK))
    put("update-low", grid(ARROW))
    put("update-medium", paint(grid(ARROW), cells(ARROW), "y"))
    put("update-high", paint(grid(ARROW), cells(ARROW), "r"))
    put("update-busy", faint(grid(ARROW)))

    for name in list(out):
        if not name.endswith("-symbolic"):
            out.setdefault(name + "-symbolic", out[name])
    return out


def names():
    return set(icons())


# ---------------------------------------------------------------- SVG

def runs(g, ch):
    """Rectangles covering the cells that are `ch`: runs along each row."""
    out = []
    for y, row in enumerate(g):
        x = 0
        while x < N:
            if row[x] != ch:
                x += 1
                continue
            e = x
            while e < N and row[e] == ch:
                e += 1
            out.append((x, y, e - x))
            x = e
    return "".join("M%d %dh%dv1h-%dz" % (x, y, w, w) for x, y, w in out)


# Cells of empty margin round a glyph that is drawn larger than the tray's.
# The colour picker widget draws its pipette at 90% of the panel's
# thickness, not at the tray's icon size: on a panel whose tray icons are
# 22 px it comes out at 32, and 2.5 cells all round bring its cells to the
# size of the tray glyphs' beside it.
MARGIN = {"color-picker": 2.5}


def margin(name):
    return MARGIN.get(name.removesuffix("-symbolic"), 0)


def svg(g, pad=0):
    """The glyph as an SVG whose colours Plasma replaces with the scheme's:
    each cell a square in one path per kind, the classes KIconLoader
    recolours; `pad` cells of margin all round."""
    style = "".join(".%s{color:%s;}" % (cls, col) for cls, col in COLOURS.items())
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="%g %g %g %g">'
           % (-pad, -pad, N + 2 * pad, N + 2 * pad),
           '<style type="text/css" id="current-color-scheme">%s</style>' % style]
    solid = [["#" if c in "#ry" else "." for c in row] for row in g]
    if any(c in "ry" for row in g for c in row):
        # Under the coloured cells, all the solid ones in the text colour: at
        # a fractional scale the pixels where two colours meet are covered
        # by neither fully, and would come out partly transparent.
        out.append('<path class="ColorScheme-Text" fill="currentColor" d="%s"/>' % runs(solid, "#"))
    for ch, (cls, alpha) in STYLE.items():
        d = runs(g, ch)
        if d:
            opacity = "" if alpha >= 1 else ' fill-opacity="%g"' % alpha
            out.append('<path class="%s" fill="currentColor"%s d="%s"/>' % (cls, opacity, d))
    out.append("</svg>\n")
    return "\n".join(out)
