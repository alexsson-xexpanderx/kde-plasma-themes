"""Hand-made icons for apps, devices, launcher categories, dialogs and the
power buttons, drawn from shapes with icons_draw -- filled, outlined and
shaded like the folders, in the wallpaper's colours.

DESIGNS maps a design to the icon names it answers to and the layers it is
drawn from (on a 24-unit square; see icons_draw).
"""

import math

import icons_art as A
import palette as P
from icons_draw import (METAL, NIGHT, SCREEN, WHITE, Circle, Ellipse, Line, Pixels, Poly, Rect,
                        Ring, Symbol, Union, Inter, detail, draw, gear, inset, part)

V, RO, RD, OR, GO = P.RAMP_VIOLET, P.RAMP_ROSE, P.RAMP_RED, P.RAMP_ORANGE, P.RAMP_GOLD
BR, SK, GY, MI = P.RAMP_BROWN, P.RAMP_SKY, P.RAMP_GREY, P.RAMP_MINT
PINK = [P.RAMP_RED[0], P.RAMP_ROSE[2], P.RAMP_RED[3], P.PINK, P.RAMP_ROSE[4]]

FULL = (2, 2, 22, 22)

# Symbols for the designs, (big, small).  Discs and boxes centred on the
# icon are an even number of cells wide, so these are too: an odd-width symbol
# on them sits half a cell off centre.
GLYPHS = {
    "i": ([".##.", ".##.", "....", "###.", ".##.", ".##.", "####"],
          ["##", "..", "##", "##", "##"]),
    "x": (["##....##", "###..###", ".######.", "..####..", "..####..", ".######.", "###..###",
           "##....##"],
          ["#..#", ".##.", ".##.", "#..#"]),
    "power": (["...##...", ".#.##.#.", "#..##..#", "#..##..#", "#......#", "#......#", ".#....#.",
               "..####.."],
              ["..##..", "#.##.#", "#....#", "#....#", ".####."]),
    "reboot": (["..####.#", ".#....##", "#....###", "#.......", "#......#", "#......#", ".#....#.",
                "..####.."],
               [".###.#", "#...##", "#.....", "#....#", ".####."]),
    "moon": (["..###.", ".###..", "###...", "###...", "###...", ".###..", "..###."],
             [".##.", "##..", "##..", "##..", ".##."]),
    "snow": (["...##...", ".#.##.#.", "..####..", "########", "########", "..####..", ".#.##.#.",
              "...##..."],
             ["..##..", "#.##.#", "######", "#.##.#", "..##.."]),
    "play": (["##....", "####..", "######", "######", "####..", "##...."],
             ["#...", "###.", "####", "###.", "#..."]),
    "down": (["...##...", "...##...", "...##...", "########", ".######.", "..####..", "...##..."],
             [".##.", ".##.", "####", ".##."]),
    "check": (["......##", ".....##.", "##..##..", ".####...", "..##...."],
              ["....##", "#..##.", "####..", ".##..."]),
    "dots": (["##.##.##", "##.##.##"], ["##..##"]),
    "question": (["..####..", ".##..##.", ".....##.", "....##..", "...##...", "........", "...##..."],
                 [".##.", "#..#", "..#.", "....", ".##."]),
    "important": (["...##...", "...##...", "...##...", "...##...", "........", "...##..."],
                  [".##.", ".##.", ".##.", "....", ".##."]),
    "star": (["...##...", "...##...", "########", ".######.", "..####..", ".##..##.", ".#....#."],
             ["..##..", "######", ".####.", ".#..#."]),
    "code": (["..#..#..", ".#....#.", "#......#", ".#....#.", "..#..#.."],
             [".#..#.", "#....#", ".#..#."]),
    "gear": (["..#..#..", ".######.", ".##..##.", "###..###", ".##..##.", ".######.", "..#..#.."],
             [".#..#.", "######", "##..##", "######", ".#..#."]),
    "font": (["...##...", "..####..", ".##..##.", ".##..##.", ".######.", ".##..##.", ".##..##."],
             ["..##..", ".#..#.", ".####.", ".#..#.", ".#..#."]),
    "bluetooth": (["..#...", "..##..", "#.#.#.", ".###..", "..#...", ".###..", "#.#.#.", "..##..",
                   "..#..."],
                  [".#..", ".##.", "##..", ".##.", ".#.."]),
}


def sym(name, colour, box=FULL, accent=None):
    s = Symbol(name, colour, box, accent)
    if name in GLYPHS:
        s.rows = GLYPHS[name]
    return s


# ---------------------------------------------------------------- pieces

def wallpaper(x0, y0, x1, y1):
    """A tiny Retrograde dusk: violet sky, the sunset, the sun on the horizon."""
    h = y1 - y0
    a, b = y0 + h * 0.45, y0 + h * 0.70
    cx = (x0 + x1) / 2
    return [
        detail(Rect(x0, y0, x1, a), V[1]),
        detail(Rect(x0, a, x1, b), RD[2]),
        detail(Rect(x0, b, x1, y1), OR[3]),
        detail(Inter(Circle(cx, y1, (x1 - x0) * 0.26), Rect(x0, y0, x1, y1)), P.GOLD),
        detail(Rect(x0, y1 - max(1.0, h * 0.12), x1, y1), V[0]),
    ]


def screen_frame(x0=2, y0=3, x1=22, y1=17):
    return [part(Rect(x0, y0, x1, y1, 1), METAL, 2),
            inset(Rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2), SCREEN, 1)]


def stand(x=12, y=17):
    return [part(Rect(x - 2, y, x + 2, y + 2.5), METAL, 2),
            part(Rect(x - 6, y + 2.5, x + 6, y + 4.5, 0.8), METAL, 3)]


def window_band(x0, y0, x1):
    """The sunset stripe the theme draws across the top of a window."""
    return [detail(Line(x0, y0 + 0.5 + i, x1, y0 + 0.5 + i, 1), c)
            for i, c in enumerate(P.SUNSET)]


def disc(ramp, tone=3):
    return part(Circle(12, 12, 10), ramp, tone)


def page_lines(x0, x1, ys, colour=GY[2]):
    return [detail(Line(x0, y, x1, y, 1), colour) for y in ys]


# ---------------------------------------------------------------- designs

GLOBE = [disc(SK),
         detail(Poly((5, 7), (10, 5), (12, 8), (9, 11), (10, 15), (7, 16), (4.5, 12)), MI[3]),
         detail(Poly((14, 10), (19, 8.5), (20.5, 13.5), (16, 18.5), (14, 15)), MI[3]),
         detail(Ring(12, 12, 10, 1, 200, 250), SK[4])]

GEAR = [part(gear(12, 12, 6.8, 8, 2.8, 0), V, 3),
        inset(Circle(12, 12, 3.2), GO, 3),
        detail(Circle(12, 12, 1.2), V[0])]

TERMINAL = [part(Rect(2, 3, 22, 21, 1.5), METAL, 2),
            detail(Line(3.5, 5.5, 20.5, 5.5, 1), P.PINK),
            detail(Line(3.5, 6.5, 20.5, 6.5, 1), P.AMBER),
            inset(Rect(4, 8, 20, 19), SCREEN, 1),
            detail(Union(Line(8, 10.5, 11.5, 13.5, 1.6), Line(11.5, 13.5, 8, 16.5, 1.6)), P.GOLD),
            detail(Line(13, 16.5, 16.5, 16.5, 1.6), P.GOLD)]

# Zen's three rings, cream on a dark tile.
CREAM = "#F4ECD8"
ZEN = [part(Rect(2, 2, 22, 22, 4), SCREEN, 3),
       detail(Ring(12, 12, 7.2, 2.2), CREAM),
       detail(Ring(12, 12, 4, 1.8), CREAM),
       detail(Circle(12, 12, 1.3), CREAM)]

# KDE's System Settings: two sliders.
SLIDERS = [part(Rect(2, 3, 22, 21, 2.5), NIGHT, 3),
           detail(Line(6, 9, 18, 9, 1.4), NIGHT[1]),
           detail(Line(6, 15, 18, 15, 1.4), NIGHT[1]),
           detail(Line(6, 9, 15, 9, 1.4), P.PINK),
           detail(Line(6, 15, 9, 15, 1.4), SK[3]),
           part(Rect(13, 7, 17, 11, 1), WHITE, 3),
           part(Rect(7, 13, 11, 17, 1), WHITE, 3)]

TEXT_EDITOR = [part(Rect(4, 3, 20, 22, 1), WHITE, 3),
               inset(Rect(5, 4, 19, 7.5), PINK, 3),
               *[part(Rect(x, 1.5, x + 1.5, 6), METAL, 3) for x in (6, 9.5, 13, 16.5)],
               *page_lines(7, 17, (10.5, 13.5, 16.5, 19.5))]

STORE = [part(Ring(12, 9, 4, 1.8, 180, 360), PINK, 2),
         part(Rect(4, 8, 20, 21, 1), PINK, 3),
         sym("star", P.BRIGHT, (5, 10, 19, 20))]

CAMERA = [part(Rect(8.5, 4, 15.5, 8, 0.5), METAL, 2),
          part(Rect(2, 7, 22, 20, 1.5), METAL, 2),
          part(Circle(12, 13.5, 5.4), SCREEN, 2),
          inset(Circle(12, 13.5, 3.4), SK, 2),
          detail(Rect(10, 11, 11.6, 12.6), P.BRIGHT),
          detail(Rect(17, 9, 20, 10.6), P.GOLD)]

VIEWER = [part(Rect(3, 2, 16, 20, 0.5), WHITE, 3),
          *page_lines(5.5, 13.5, (5.5, 8.5, 11.5)),
          part(Line(18, 17, 21.5, 20.5, 2.8), V, 1),
          part(Circle(14.5, 13.5, 4.8), V, 3),
          inset(Circle(14.5, 13.5, 3.2), SK, 3)]

IMAGE = [part(Rect(2, 4, 22, 20, 1), GO, 2),
         *wallpaper(4, 6, 20, 18),
         detail(Poly((4, 18), (4, 13), (7, 11), (10, 14), (11.5, 18)), V[0]),
         detail(Poly((14, 18), (16.5, 12.5), (20, 15), (20, 18)), V[0])]

ARCHIVE = [part(Rect(3, 9, 21, 21, 0.5), BR, 3),
           part(Rect(2, 6, 22, 10, 0.5), BR, 4),
           detail(Rect(11, 6.5, 13, 20.5), P.GOLD)]

CALCULATOR = [part(Rect(5, 2, 19, 22, 1.5), V, 2),
              inset(Rect(7, 4, 17, 8.5), MI, 1),
              *[detail(Rect(x, y, x + 2, y + 2), P.BRIGHT if (x, y) != (15, 17) else P.PINK)
                for y in (11, 14, 17) for x in (7, 11, 15)]]

VINYL = [part(Circle(12, 12, 10), SCREEN, 2),
         detail(Ring(12, 12, 7, 0.8), SCREEN[3]),
         detail(Ring(12, 12, 8.6, 0.8, 200, 250), P.SUBTEXT),
         inset(Circle(12, 12, 3.8), PINK, 3),
         detail(Circle(12, 12, 1.1), P.VOID)]

VIDEO = [part(Rect(2, 4, 22, 18, 1), METAL, 2),
         inset(Rect(4, 6, 20, 16), NIGHT, 3),
         sym("play", P.GOLD, (4, 6, 20, 16)),
         *stand(12, 18)[:1], part(Rect(6, 20, 18, 21.8, 0.8), METAL, 3)]

FIREFOX = [part(Poly((14, 1.5), (19, 3.5), (15.5, 5.5)), OR, 3),
           part(Circle(12, 12.5, 9.8), OR, 3),
           inset(Circle(13.5, 11, 6.2), V, 2),
           detail(Poly((3.5, 9), (7.5, 5.5), (9.5, 8.5), (6.5, 12.5)), OR[4])]

CHROME = [part(Ring(12, 12, 7.6, 5.2, 210, 330), RD, 3),
          part(Ring(12, 12, 7.6, 5.2, 330, 90), GO, 3),
          part(Ring(12, 12, 7.6, 5.2, 90, 210), MI, 3),
          part(Circle(12, 12, 4.2), WHITE, 3),
          inset(Circle(12, 12, 2.7), SK, 2)]

MAIL = [part(Rect(2, 6, 22, 19, 1), WHITE, 3),
        detail(Line(3, 7, 12, 13.5, 1.2), WHITE[0]),
        detail(Line(12, 13.5, 21, 7, 1.2), WHITE[0]),
        detail(Circle(12, 13.6, 1.6), P.PINK)]

THUNDERBIRD = MAIL + [part(Poly((2, 10), (6, 3.5), (12, 3), (9.5, 6.5), (13, 7.5), (6, 11)), V, 3),
                      detail(Circle(7, 6, 0.8), P.GOLD)]

# Steam, pixel by pixel, in the logo's own proportions (measured from it): the
# big wheel up on the right, a ring round its hub; the arm down to the small
# wheel, whose ring opens where the bar joins; the bar leaving the disc on the
# left.  Dark on a pale disc, as the logo is usually shown.  Drawn from shapes,
# the thin rings broke up and the arm ran into the wheels.  At 16 cells the
# small wheel keeps only an L of its ring.
STEAM_BIG = [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    ".............####.......",
    "............##ww##......",
    "...........##w##w##.....",
    "...........#w####w#.....",
    "...........#w####w#.....",
    "..........###w##w##.....",
    "..........####ww##......",
    "..##.....########.......",
    "..#############.........",
    "..#######w###...........",
    "...#######w#............",
    "......#w##w#............",
    "......##ww##............",
    ".......####.............",
]
STEAM_SMALL = [
    "................",
    "................",
    "................",
    "................",
    ".........##.....",
    "........#ww#....",
    ".......#w##w#...",
    ".......#w##w#...",
    ".########ww#....",
    ".####w#####.....",
    "..##ww#.........",
    "....##..........",
]
STEAM = [part(Circle(12, 12, 10), WHITE, 3),
         Pixels(STEAM_BIG, STEAM_SMALL, {"#": NIGHT[1], "w": WHITE[3]})]

DISCORD = [part(Union(Rect(2, 6, 22, 19, 5), Circle(6.5, 7, 3.2), Circle(17.5, 7, 3.2),
                      Poly((4, 15), (2.5, 20), (8, 17)), Poly((20, 15), (21.5, 20), (16, 17))), V, 3),
           detail(Ellipse(8.5, 12.2, 2, 2.4), V[0]),
           detail(Ellipse(15.5, 12.2, 2, 2.4), V[0])]

SPOTIFY = [disc(MI),
           detail(Ring(12, 24, 15, 1.9, 250, 290), MI[0]),
           detail(Ring(12, 25.5, 12.8, 1.7, 247, 293), MI[0]),
           detail(Ring(12, 27, 11, 1.5, 244, 296), MI[0])]

VLC = [part(Poly((12, 2.5), (17.5, 18), (6.5, 18)), OR, 3),
       detail(Inter(Rect(0, 7, 24, 9.4), Poly((12, 2.5), (17.5, 18), (6.5, 18))), P.TEXT),
       detail(Inter(Rect(0, 12, 24, 14.4), Poly((12, 2.5), (17.5, 18), (6.5, 18))), P.TEXT),
       part(Rect(3.5, 17.5, 20.5, 21, 1), OR, 2)]

PALETTE = [part(Ellipse(11, 13, 9.5, 8) - Circle(8, 17.5, 1.8), GO, 4),
           detail(Circle(6.5, 11, 1.7), P.PINK), detail(Circle(10.5, 8, 1.7), SK[3]),
           detail(Circle(15, 8.5, 1.7), V[3]), detail(Circle(17, 12.5, 1.7), MI[3]),
           part(Line(13, 17, 21, 4, 2.2), BR, 2),
           detail(Line(12, 18.5, 13.2, 16.5, 2.2), P.PINK)]

INKSCAPE = [part(Poly((12, 1.5), (22, 15.5), (18, 15.5), (18, 20), (15.5, 17), (13, 22), (10.5, 17),
                      (6.5, 20), (6, 15.5), (2, 15.5)), V, 2),
            detail(Poly((12, 2.5), (16, 8), (13.8, 7.2), (12, 9.2), (10.2, 7.2), (8, 8)), P.BRIGHT)]

KRITA = [part(Union(Circle(9, 15, 6), Circle(15, 18.5, 3.2), Circle(5, 8.5, 2.4)), PINK, 3),
         part(Line(14.5, 9.5, 21.5, 2.5, 2.8), BR, 3),
         part(Line(11.5, 12.5, 14.5, 9.5, 3.4), METAL, 3),
         part(Line(8, 16, 11.8, 12.2, 3.6), V, 3)]

BLENDER = [part(Union(Ring(13.5, 13.5, 6.4, 3.6), Poly((2.5, 6.5), (12.5, 6.5), (10.5, 9.8), (4.5, 9.8)),
                      Poly((5, 10.5), (9.5, 10.5), (8.5, 13.5), (6, 13.5))), OR, 3),
           inset(Circle(13.5, 13.5, 3), SK, 3),
           detail(Circle(13.5, 13.5, 1.1), P.BRIGHT)]

OBS = [disc(SCREEN, 3),
       *[detail(Circle(x, y, 3), P.TEXT) for x, y in ((12, 7.5), (7.8, 14.8), (16.2, 14.8))],
       *[detail(Circle(x, y, 1.3), SCREEN[2]) for x, y in ((12, 7.5), (7.8, 14.8), (16.2, 14.8))]]

TELEGRAM = [disc(SK),
            detail(Poly((5, 11.5), (18, 6), (15.5, 18), (12, 15), (10.5, 17.5), (10, 13.5)), P.BRIGHT),
            detail(Line(10.2, 13.5, 15, 9.2, 1), SK[1])]

VSCODE = [part(Poly((15.5, 2), (21.5, 5), (21.5, 19), (15.5, 22), (6.5, 14.5), (3.5, 17), (2, 16),
                    (2, 8), (3.5, 7), (6.5, 9.5)), SK, 3),
          detail(Poly((15.5, 8), (15.5, 16), (10.5, 12)), SK[1])]

KDENLIVE = [part(Rect(2, 10, 22, 21, 1), SCREEN, 3),
            part(Poly((2, 6.5), (21, 3), (21.6, 6.4), (2.6, 9.8)), WHITE, 3),
            *[detail(Line(x, 5.5 - (x - 5) * 0.18, x + 2, 8.6 - (x - 5) * 0.18, 1.4), SCREEN[1])
              for x in (5, 10, 15)],
            sym("play", P.PINK, (2, 11, 22, 21))]

HEADPHONES = [part(Ring(12, 14, 8.5, 2.4, 180, 360), V, 2),
              part(Rect(2, 13, 6.8, 21, 1.5), PINK, 3),
              part(Rect(17.2, 13, 22, 21, 1.5), PINK, 3)]

AUDIO_EDITOR = HEADPHONES + [detail(Rect(x, 17 - h, x + 1, 17 + h), P.AMBER)
                             for x, h in ((8, 1), (9.5, 3), (11, 2), (12.5, 4), (14, 1.5), (15.5, 2.5))]

ZOOM = [disc(SK),
        detail(Rect(4.5, 8.5, 13, 15.5, 1.5), P.BRIGHT),
        detail(Poly((14.5, 12), (19.5, 8.5), (19.5, 15.5)), P.BRIGHT)]

CHAT = [part(Union(Rect(2, 3, 22, 16, 3), Poly((6, 15), (6, 21), (12, 15))), PINK, 3),
        sym("dots", P.BRIGHT, (2, 3, 22, 16))]

PHONE = [part(Rect(6, 1.5, 18, 22.5, 2), SCREEN, 3),
         *wallpaper(7.5, 4, 16.5, 18.5),
         detail(Circle(12, 20.5, 1), SCREEN[4])]

KDECONNECT = PHONE + [part(Circle(18, 18, 4.2), PINK, 3),
                      detail(Ring(18, 18, 2, 1, 180, 360), P.BRIGHT)]

MONITOR = [*screen_frame(2, 3, 22, 17)[:1], *wallpaper(4, 5, 20, 15), *stand(12, 17)]

SYSMONITOR = [*screen_frame(2, 3, 22, 17),
              *[detail(Line(*seg, 1.2), P.PINK) for seg in
                ((4.5, 11, 8, 11), (8, 11, 10, 6.5), (10, 6.5, 12.5, 14), (12.5, 14, 14.5, 9.5),
                 (14.5, 9.5, 16, 11), (16, 11, 19.5, 11))],
              *stand(12, 17)]

DEVELOPMENT = [*screen_frame(2, 3, 22, 17), sym("code", P.PINK, (4, 5, 20, 15)), *stand(12, 17)]

SYSTEM = [*screen_frame(2, 3, 22, 17), sym("gear", P.GOLD, (4, 5, 20, 15)), *stand(12, 17)]

INFO = [disc(SK), sym("i", P.BRIGHT)]
WARNING = [part(Poly((12, 2), (22.5, 20.5), (1.5, 20.5)), GO, 3), sym("important", SCREEN[1], (2, 8, 22, 20))]
ERROR = [disc(RD), sym("x", P.BRIGHT)]
QUESTION = [disc(V), sym("question", P.BRIGHT)]

KEY = [part(Union(Circle(7.5, 8, 5.5), Line(10.5, 11, 20.5, 21, 3.6), Line(16.5, 17, 20, 13.5, 3.4),
                  Line(13.5, 14, 16.2, 11.3, 3.4)), GO, 3),
       detail(Circle(6.5, 7, 1.6), GO[0])]

WALLET = [part(Rect(2, 6, 22, 20, 1.5), BR, 3),
          part(Rect(13, 10, 22.5, 16, 1), BR, 4),
          detail(Circle(17, 13, 1.3), P.GOLD)]


def shield(ramp, mark):
    return [part(Poly((12, 2), (21, 5), (20, 13), (12, 22), (4, 13), (3, 5)), ramp, 3),
            sym(mark, P.BRIGHT, (3, 4, 21, 18))]


CALENDAR = [part(Rect(3, 4, 21, 21, 1), WHITE, 3),
            inset(Rect(4, 5, 20, 9), PINK, 3),
            detail(Rect(7, 2.5, 8.6, 6.5), SCREEN[3]), detail(Rect(15.4, 2.5, 17, 6.5), SCREEN[3]),
            *[detail(Rect(x, y, x + 2, y + 2), P.PINK if (x, y) == (13, 14) else GY[2])
              for y in (11, 14, 17) for x in (5, 9, 13, 17)]]

CONTACTS = [part(Rect(2, 4, 22, 20, 1.5), WHITE, 3),
            detail(Circle(8.5, 10, 2.8), V[2]),
            detail(Rect(4.5, 13.5, 12.5, 17.8, 2), V[2]),
            *page_lines(14, 19.5, (9, 12, 15))]

NOTES = [part(Poly((3, 3), (21, 3), (21, 16), (16, 21), (3, 21)), GO, 3),
         part(Poly((16, 21), (16, 16), (21, 16)), GO, 1),
         *page_lines(6, 17, (7, 10, 13), GO[0])]

CLOCK = [part(Circle(12, 12, 10), GO, 2),
         inset(Circle(12, 12, 7.8), WHITE, 3),
         detail(Line(12, 12, 12, 6, 1.4), SCREEN[1]),
         detail(Line(12, 12, 16, 14, 1.4), SCREEN[1]),
         detail(Circle(12, 12, 1), P.PINK)]

WEATHER = [part(Circle(14.5, 8.5, 5.5), GO, 3),
           part(Union(Circle(8, 15, 4), Circle(13, 13, 5), Circle(17.5, 15.5, 3.5), Rect(4, 15, 21, 19.5, 2)),
                WHITE, 3)]

MAPS = [part(Poly((2, 6), (8, 4), (16, 6), (22, 4), (22, 19), (16, 21), (8, 19), (2, 21)), SK, 3),
        detail(Poly((8, 4.6), (16, 6.6), (16, 20.4), (8, 18.4)), SK[2]),
        part(Union(Circle(14, 8, 4), Poly((10.6, 10), (17.4, 10), (14, 16.5))), PINK, 3),
        detail(Circle(14, 8, 1.4), P.BRIGHT)]

TORRENT = [disc(SK), sym("down", P.BRIGHT)]

GAMEPAD = [part(Union(Rect(2, 7, 22, 16, 4), Circle(6, 16, 3.5), Circle(18, 16, 3.5)), V, 3),
           detail(Union(Rect(6.5, 8.8, 8.5, 14.2), Rect(4.8, 10.5, 10.2, 12.5)), V[0]),
           detail(Circle(16, 10, 1.3), P.PINK), detail(Circle(18.5, 12.6, 1.3), P.GOLD)]

WINE = [part(Poly((5, 2), (19, 2), (18.5, 8), (12, 13), (5.5, 8)), WHITE, 3),
        inset(Poly((5.3, 6), (18.7, 6), (18.5, 8), (12, 13), (5.5, 8)), RD, 3),
        detail(Rect(11, 13, 13, 19), WHITE[2]),
        part(Rect(6, 19, 18, 21.5, 1), WHITE, 3)]

MULTIMEDIA = [disc(PINK), sym("play", P.BRIGHT)]

TOOLBOX = [part(Ring(12, 8.5, 4, 1.8, 180, 360), METAL, 2),
           part(Rect(2, 8, 22, 21, 1), RD, 3),
           detail(Line(2.5, 12.5, 21.5, 12.5, 1), RD[1]),
           detail(Rect(10.5, 11, 13.5, 14), P.GOLD)]

EDUCATION = [part(Rect(6.5, 10, 17.5, 17, 2), V, 2),
             part(Poly((12, 4), (22.5, 9), (12, 14), (1.5, 9)), V, 2),
             detail(Line(19, 9.5, 19, 16, 1), P.GOLD), detail(Circle(19, 16.6, 1.3), P.GOLD)]

FLASK_SHAPE = Union(Rect(9.5, 2, 14.5, 9), Poly((9.5, 8), (14.5, 8), (21, 20), (19.5, 21.5), (4.5, 21.5), (3, 20)))
SCIENCE = [part(FLASK_SHAPE, WHITE, 3),
           inset(Inter(FLASK_SHAPE, Rect(0, 13, 24, 21)), SK, 3),
           detail(Circle(10, 16, 1), P.BRIGHT), detail(Circle(14, 18, 1.2), P.BRIGHT)]

CUBE = [part(Poly((12, 2), (21, 7), (21, 17), (12, 22), (3, 17), (3, 7)), GO, 3),
        detail(Poly((12, 12.5), (20.5, 7.6), (20.5, 16.6), (12, 21.4)), GO[2]),
        detail(Poly((3.5, 7.4), (12, 2.6), (20.5, 7.4), (12, 12)), GO[4])]

HARDDISK = [part(Rect(2, 6, 22, 18, 1.5), METAL, 3),
            detail(Rect(4, 12.5, 15, 13.8), SCREEN[1]),
            detail(Rect(17.5, 12.3, 19.8, 14), P.MINT),
            detail(Rect(4, 8.5, 15, 10.5), METAL[4])]

USB = [part(Rect(14, 7.5, 21.5, 14.5, 0.5), METAL, 3),
       part(Rect(2.5, 6, 15.5, 16, 1.5), V, 3),
       detail(Rect(16.5, 9.2, 18.2, 10.8), SCREEN[1]), detail(Rect(16.5, 11.6, 18.2, 13.2), SCREEN[1]),
       detail(Rect(5, 8.5, 12, 13.5, 0.8), V[4])]

OPTICAL = [part(Circle(12, 12, 10) - Circle(12, 12, 1.8), WHITE, 3),
           detail(Ring(12, 12, 7, 1.2, 290, 340), P.PINK),
           detail(Ring(12, 12, 7, 1.2, 110, 160), SK[3]),
           detail(Ring(12, 12, 4.2, 1.2, 0, 359.9), WHITE[1])]

FLOPPY = [part(Rect(3, 3, 21, 21, 1), V, 2),
          inset(Rect(8, 3.5, 17, 9), METAL, 3),
          detail(Rect(14, 4.5, 15.6, 8), SCREEN[1]),
          inset(Rect(6, 12.5, 18, 20.5), WHITE, 3),
          *page_lines(7.5, 16.5, (15, 17.8), P.PINK)]

LAPTOP = [part(Rect(4, 4, 20, 15.5, 1), METAL, 2),
          *wallpaper(5.5, 5.5, 18.5, 14),
          part(Poly((1.5, 15.5), (22.5, 15.5), (21, 19.5), (3, 19.5)), METAL, 3)]

SERVER = [part(Rect(6, 2, 18, 22, 1), METAL, 2),
          *[detail(Rect(8, y, 16, y + 2), SCREEN[1]) for y in (4.5, 8.5, 12.5)],
          *[detail(Rect(14.2, y + 0.5, 15.4, y + 1.5), c) for y, c in ((4.5, P.MINT), (8.5, P.GOLD), (12.5, P.MINT))],
          detail(Circle(12, 18.5, 1.4), P.PINK)]

NETWORK = [detail(Union(Line(12, 8, 12, 12, 1.4), Line(5, 12, 19, 12, 1.4), Line(5, 12, 5, 15, 1.4),
                         Line(19, 12, 19, 15, 1.4)), METAL[3]),
           part(Rect(8.5, 2, 15.5, 8.5, 1), SK, 3),
           part(Rect(1.5, 14.5, 8.5, 21, 1), PINK, 3),
           part(Rect(15.5, 14.5, 22.5, 21, 1), GO, 3)]

KEYBOARD = [part(Rect(1, 7, 23, 18, 1.5), METAL, 3),
            *[detail(Rect(x, y, x + 2, y + 2), METAL[4])
              for y in (9, 12) for x in (3, 6, 9, 13, 16, 19)],
            detail(Rect(7, 15, 17, 16.5), METAL[4])]

MOUSE = [part(Ellipse(12, 12.5, 6.5, 9.5), METAL, 3),
         detail(Line(12, 3.5, 12, 10, 1), METAL[1]),
         detail(Line(6, 10, 18, 10, 1), METAL[1]),
         detail(Rect(11.2, 5, 12.8, 8), P.PINK)]

PRINTER = [part(Rect(6, 3, 18, 10), WHITE, 3),
           part(Rect(2, 9, 22, 18, 1.5), METAL, 3),
           part(Rect(6, 15, 18, 21.5), WHITE, 3),
           *page_lines(8, 16, (17.5, 19.5)),
           detail(Rect(18, 11, 20, 12.5), P.MINT)]

SPEAKER = [part(Rect(5, 2, 19, 22, 1.5), BR, 2),
           part(Circle(12, 15.5, 4.6), SCREEN, 2), detail(Circle(12, 15.5, 1.6), SCREEN[4]),
           part(Circle(12, 6.5, 2.6), SCREEN, 2)]

SOUNDCARD = [part(Rect(2, 5, 22, 17, 0.5), MI, 2),
             detail(Rect(4.5, 7.5, 10, 12.5), SCREEN[1]), detail(Rect(12, 8, 15, 11), SCREEN[1]),
             *[detail(Rect(x, 17, x + 1.2, 19.5), P.GOLD) for x in (5, 7, 9, 11, 13, 15, 17)]]

BATTERY = [part(Rect(20, 9.5, 22.5, 14.5, 0.5), METAL, 3),
           part(Rect(2, 7, 20.5, 17, 1.5), MI, 3),
           detail(Poly((12.5, 8.5), (8, 12.5), (11.5, 12.5), (10.5, 15.5), (15, 11.5), (11.5, 11.5)), P.GOLD)]

WEBCAM = [part(Rect(8, 16.5, 16, 21, 1), SCREEN, 3),
          part(Circle(12, 10, 7.6), SCREEN, 3),
          inset(Circle(12, 10, 4.6), SK, 2),
          detail(Rect(10, 7.5, 11.6, 9.1), P.BRIGHT)]

SHUTDOWN = [disc(RD), sym("power", P.BRIGHT)]
REBOOT = [disc(GO), sym("reboot", SCREEN[1])]
LOCK = [part(Union(Ring(12, 9.5, 5, 2.6, 180, 360), Rect(5.7, 9.5, 8.3, 12), Rect(15.7, 9.5, 18.3, 12)), METAL, 3),
        part(Rect(4, 11, 20, 21.5, 1.5), V, 3),
        detail(Union(Circle(12, 15, 1.6), Rect(11.3, 15, 12.7, 18.5)), V[0])]
LOGOUT = [part(Rect(3, 2, 14, 22, 0.5), BR, 3),
          detail(Circle(11.5, 12.5, 0.9), P.GOLD),
          part(Union(Rect(9, 10, 18, 14), Poly((17, 6.5), (22.5, 12), (17, 17.5))), PINK, 3)]
SUSPEND = [disc(NIGHT, 3), sym("moon", P.GOLD)]
HIBERNATE = [disc(SK), sym("snow", P.BRIGHT)]
USERS = [part(Union(Circle(15.5, 6.5, 3.4), Inter(Circle(15.5, 18.5, 6.2), Rect(8, 11.5, 23, 19))), V, 2),
         part(Union(Circle(9, 9.5, 3.6), Inter(Circle(9, 22, 6.8), Rect(1, 15, 17, 22))), PINK, 3)]

BELL = [part(Union(Rect(6, 5, 18, 16, 5), Poly((3.5, 18), (20.5, 18), (18, 12), (6, 12))), GO, 3),
        part(Circle(12, 19.5, 2.2), GO, 2),
        detail(Circle(12, 3.5, 1.2), GO[2])]

WINDOW = [part(Rect(2, 3, 22, 21, 1), SCREEN, 2),
          *window_band(3, 4, 21),
          *[detail(Rect(x, 11, x + 1.6, 12.6), P.SUBTEXT) for x in (5,)],
          *page_lines(5, 15, (12, 15, 18), P.SURFACE2)]

FONT = [part(Rect(2, 2, 22, 22, 3), V, 3), sym("font", P.BRIGHT)]

BLUETOOTH = [disc(SK), sym("bluetooth", P.BRIGHT)]

ACCESSIBILITY = [disc(SK),
                 detail(Circle(12, 6.5, 1.8), P.BRIGHT),
                 detail(Line(6, 9.5, 18, 9.5, 1.6), P.BRIGHT),
                 detail(Line(12, 9.5, 12, 14, 1.8), P.BRIGHT),
                 detail(Line(12, 14, 9, 18.5, 1.6), P.BRIGHT),
                 detail(Line(12, 14, 15, 18.5, 1.6), P.BRIGHT)]

PERSON = [disc(V), detail(Circle(12, 9, 3.4), P.BRIGHT),
          detail(Inter(Circle(12, 19.5, 6.2), Circle(12, 12, 9)), P.BRIGHT)]


SEARCH = [part(Line(15, 15, 20.5, 20.5, 3.2), METAL, 2),
          part(Circle(10.5, 10.5, 7.5), V, 3),
          inset(Circle(10.5, 10.5, 5.2), SK, 3),
          detail(Rect(7, 7, 9, 9), P.BRIGHT)]

TILES = [part(Rect(2, 2, 11, 11, 1.5), PINK, 3), part(Rect(13, 2, 22, 11, 1.5), GO, 3),
         part(Rect(2, 13, 11, 22, 1.5), SK, 3), part(Rect(13, 13, 22, 22, 1.5), V, 3)]

ACTIVITIES = [part(Rect(8, 2, 22, 13, 1), V, 2),
              part(Rect(5, 6, 19, 17, 1), PINK, 3),
              part(Rect(2, 10, 16, 21, 1), GO, 3)]

ANIMATIONS = [detail(Line(2, 9, 8, 9, 1.4), V[3]), detail(Line(3, 13, 9, 13, 1.4), V[3]),
              detail(Line(2, 17, 8, 17, 1.4), V[3]),
              part(Circle(15, 13, 7), PINK, 3)]

# The theme's own arrow cursor, as preferences-desktop-cursors.
CURSOR = [part(Poly((6, 2), (6, 20), (10.5, 15.5), (14, 22), (17, 20.5), (13.5, 14.5), (19.5, 14.5)), WHITE, 3)]

DEFAULT_APPS = TILES[:3] + [part(Rect(13, 13, 22, 22, 1.5), V, 3), sym("star", P.BRIGHT, (13, 13, 22, 22))]

def _slice(a0, a1, r=12):
    """A pie slice from the centre, between two angles (degrees, clockwise)."""
    pts = [(12, 12)] + [(12 + r * math.cos(math.radians(a)), 12 + r * math.sin(math.radians(a)))
                        for a in range(int(a0), int(a1) + 1, 5)]
    return Poly(*pts)


# One disc, flat slices on it: parts with outlines of their own came out as a
# ring of broken pieces.
COLOURWHEEL = [part(Circle(12, 12, 10), WHITE, 3),
               *[detail(Inter(_slice(a, a + 60), Circle(12, 12, 9)), ramp[3])
                 for a, ramp in ((270, RD), (330, OR), (30, GO), (90, MI), (150, SK), (210, V))],
               detail(Circle(12, 12, 3.4), P.BRIGHT)]

EFFECTS = [part(Poly((12, 2), (14.2, 9.8), (22, 12), (14.2, 14.2), (12, 22), (9.8, 14.2), (2, 12), (9.8, 9.8)),
                GO, 3),
           part(Poly((19, 2), (20, 4), (22, 5), (20, 6), (19, 8), (18, 6), (16, 5), (18, 4)), PINK, 3)]

TABLET = [part(Rect(2, 4, 22, 20, 2), SCREEN, 3),
          inset(Rect(5, 7, 19, 17), V, 2),
          part(Line(9, 15, 19, 5, 2.6), WHITE, 3),
          detail(Line(8, 16, 9.5, 14.5, 2.6), P.PINK)]

TOUCHPAD = [part(Rect(3, 3, 21, 21, 2.5), METAL, 3),
            inset(Rect(5, 5, 19, 15), METAL, 2),
            detail(Line(12, 16, 12, 19.5, 1), METAL[1])]

DESKTOPS = [part(Rect(2, 3, 11.5, 11, 1), V, 3), part(Rect(12.5, 3, 22, 11, 1), V, 3),
            part(Rect(2, 13, 11.5, 21, 1), V, 3), part(Rect(12.5, 13, 22, 21, 1), PINK, 3)]

FIREWALL = [part(Rect(2, 4, 22, 21, 0.5), RD, 3),
            *[detail(Line(2.5, y, 21.5, y, 1), RD[1]) for y in (8.5, 12.5, 16.5)],
            *[detail(Line(x, y0, x, y0 + 3, 1), RD[1])
              for y0, xs in ((5, (8, 16)), (9, (4, 12, 20)), (13, (8, 16)), (17, (4, 12, 20))) for x in xs]]

TABBOX = [part(Rect(2, 3, 16, 14, 1), SCREEN, 3), *[detail(Line(3, 4.5, 15, 4.5, 1), P.PINK)],
          part(Rect(8, 9, 22, 20, 1), SCREEN, 3),
          detail(Line(9, 10.5, 21, 10.5, 1), P.PINK), detail(Line(9, 11.5, 21, 11.5, 1), P.AMBER)]

BULB = [part(Circle(12, 9.5, 7.5), GO, 3),
        part(Rect(8.5, 15, 15.5, 19, 0.5), METAL, 3),
        detail(Line(9, 20.5, 15, 20.5, 1.4), METAL[1]),
        detail(Rect(9, 6, 11, 8), P.BRIGHT)]

GAUGE = [part(Inter(Circle(12, 15, 10), Rect(0, 0, 24, 17)), V, 3),
         detail(Ring(12, 15, 7.5, 1.4, 180, 250), MI[3]),
         detail(Ring(12, 15, 7.5, 1.4, 250, 310), GO[3]),
         detail(Ring(12, 15, 7.5, 1.4, 310, 360), RD[3]),
         detail(Line(12, 15, 17, 9, 1.6), P.BRIGHT),
         detail(Circle(12, 15, 1.6), P.BRIGHT)]

XORG = [*screen_frame(2, 3, 22, 17), sym("x", P.PINK, (4, 5, 20, 15)), *stand(12, 17)]


def sun_icon(n):
    return A.sun(n)


# ---------------------------------------------------------------- letter tiles
#
# For an icon whose conversion comes out noisy and that has no design: a tile
# in its own main colour with its initial, rather than shapes it does not have.

LETTERS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
}
TILE_RAMPS = [V, PINK, SK, GO, MI, OR, RO]


def _big(rows):
    """A letter at twice the size, for the 24-cell tile: one cell of the font
    becomes two by two, as the wallpaper's own pixels are four screen pixels."""
    return [r.replace("#", "##").replace(".", "..") for r in rows for _ in (0, 1)]


def _bold(rows):
    """A letter one cell bolder, and so an even six cells wide, for the
    16-cell tile, where an odd width would sit half a cell off centre."""
    out = []
    for r in rows:
        r = r + "."
        out.append("".join("#" if r[i] == "#" or (i and r[i - 1] == "#") else "."
                           for i in range(len(r))))
    return out


def letter_tile(n, letter, ramp):
    rows = LETTERS.get(letter.upper(), LETTERS["X"])
    ink = P.BRIGHT if P.contrast(P.BRIGHT, ramp[3]) >= 2.2 else ramp[0]
    s = Symbol(letter, ink, (2, 2, 22, 22))
    s.rows = (_big(rows), _bold(rows))
    return draw(n, [part(Rect(2, 2, 22, 22, 3), ramp, 3), s])


def doc(ramp, symbol):
    return lambda n: A.page(n, ramp, symbol)


# Dolphin: the violet folder with a dolphin leaping across its front.
DOLPHIN = (["......#......",
            ".....##......",
            "#..#######...",
            ".##########..",
            ".############",
            "#...#####...."],
           ["...#...", "#.####.", ".######", "#.##..."])


def dolphin(n):
    return A.folder(n, A.FOLDER_COLOURS["violet"], symbol_mask=DOLPHIN[0 if n == 24 else 1])


DESIGNS = {
    "terminal": (TERMINAL, "org.xfce.terminal org.xfce.terminal-settings org.xfce.terminalemulator utilities-terminal org.kde.konsole konsole org.kde.yakuake yakuake "
                 "terminal gnome-terminal org.gnome.Terminal org.gnome.Console xterm alacritty "
                 "Alacritty kitty foot terminator qterminal xfce4-terminal lxterminal tilix "
                 "com.gexperts.Tilix wezterm org.wezfurlong.wezterm cool-retro-term"),
    "file-manager": (dolphin, "org.xfce.filemanager system-file-manager org.kde.dolphin dolphin nautilus "
                     "org.gnome.Nautilus thunar org.xfce.thunar pcmanfm pcmanfm-qt nemo "
                     "krusader org.kde.krusader doublecmd"),
    "text-editor": (TEXT_EDITOR, "org.xfce.settings.editor accessories-text-editor org.kde.kate kate org.kde.kwrite kwrite "
                    "gedit org.gnome.gedit org.gnome.TextEditor mousepad org.xfce.mousepad "
                    "featherpad pluma xed leafpad notepadqq text-editor"),
    "sliders": (SLIDERS, "systemsettings org.kde.systemsettings"),
    "settings": (GEAR, "org.xfce.settings.manager preferences-system preferences-desktop preferences-system-session-services "
                 "gnome-settings org.gnome.Settings gnome-control-center xfce4-settings-manager "
                 "preferences-other configurator applications-engineering"),
    "store": (STORE, "org.kde.discover plasmadiscover system-software-install org.gnome.Software "
              "gnome-software software-store pamac pamac-manager system-software-update "
              "applications-other-store"),
    "camera": (CAMERA, "org.xfce.screenshooter org.kde.spectacle spectacle applets-screenshooter accessories-screenshot "
               "gnome-screenshot org.gnome.Screenshot flameshot org.flameshot.Flameshot ksnip "
               "camera-photo org.kde.kamoso kamoso cheese org.gnome.Cheese accessories-camera"),
    "viewer": (VIEWER, "org.kde.okular okular evince org.gnome.Evince atril zathura "
               "org.pwmt.zathura document-viewer xreader qpdfview xpdf xpdfIcon"),
    "image": (IMAGE, "org.xfce.ristretto lighttable org.kde.gwenview gwenview eog org.gnome.eog org.gnome.Loupe ristretto "
              "image-viewer gthumb org.gnome.gThumb nomacs org.nomacs.ImageLounge shotwell "
              "org.gnome.Shotwell digikam org.kde.digikam preferences-desktop-wallpaper "
              "multimedia-photo-viewer"),
    "archive": (ARCHIVE, "org.kde.ark ark utilities-file-archiver file-roller org.gnome.FileRoller "
                "engrampa xarchiver peazip io.github.peazip.PeaZip"),
    "calculator": (CALCULATOR, "accessories-calculator org.kde.kcalc kcalc gnome-calculator "
                   "org.gnome.Calculator galculator qalculate qalculate-qt qalculate-gtk "
                   "speedcrunch org.speedcrunch.SpeedCrunch org.kde.kalk kalk"),
    "music": (VINYL, "multimedia-audio-player org.kde.elisa elisa rhythmbox org.gnome.Rhythmbox3 "
              "audacious clementine strawberry org.strawberrymusicplayer.strawberry lollypop "
              "amarok org.kde.amarok cantata deadbeef juk org.kde.juk quodlibet"),
    "video": (VIDEO, "multimedia-video-player mpv io.mpv.Mpv smplayer celluloid "
              "io.github.celluloid_player.Celluloid totem org.gnome.Totem dragonplayer "
              "org.kde.dragonplayer haruna org.kde.haruna parole kaffeine org.kde.kaffeine "
              "mplayer xine video-player"),
    "globe": (GLOBE, "org.xfce.webbrowser preferences-system-network-remote preferences-system-network-proxy preferences-web-browser-shortcuts internet-web-browser web-browser konqueror org.kde.konqueror falkon "
              "org.kde.falkon epiphany org.gnome.Epiphany midori qutebrowser "
              "org.qutebrowser.qutebrowser applications-internet preferences-desktop-locale "
              "google-earth-pro"),
    "firefox": (FIREFOX, "firefox firefox-esr org.mozilla.firefox firefox-developer-edition "
                "librewolf io.gitlab.librewolf-community waterfox floorp"),
    "zen": (ZEN, "zen-browser app.zen_browser.zen zen"),
    "chrome": (CHROME, "chromium chromium-browser google-chrome com.google.Chrome "
               "org.chromium.Chromium brave-browser com.brave.Browser vivaldi "
               "com.vivaldi.Vivaldi microsoft-edge"),
    "mail": (MAIL, "org.xfce.mailreader internet-mail mail-client org.kde.kmail2 kmail evolution org.gnome.Evolution "
             "geary org.gnome.Geary claws-mail mailspring mutt org.kde.merkuro.mail"),
    "thunderbird": (THUNDERBIRD, "thunderbird org.mozilla.Thunderbird betterbird eu.betterbird.Betterbird"),
    "steam": (STEAM, "steam com.valvesoftware.Steam steam-native steam-runtime"),
    "discord": (DISCORD, "discord com.discordapp.Discord vesktop dev.vencord.Vesktop webcord "
                "discord-canary armcord"),
    "spotify": (SPOTIFY, "spotify com.spotify.Client spotify-client spotify-launcher"),
    "vlc": (VLC, "vlc org.videolan.VLC"),
    "gimp": (PALETTE, "gimp org.gimp.GIMP gimp-2.10"),
    "palette": (PALETTE, "applications-graphics "
                "preferences-desktop-color kolourpaint org.kde.kolourpaint mtpaint pinta "
                "com.github.PintaProject.Pinta xpaint"),
    "inkscape": (INKSCAPE, "inkscape org.inkscape.Inkscape"),
    "krita": (KRITA, "krita org.kde.krita"),
    "blender": (BLENDER, "blender org.blender.Blender"),
    "obs": (OBS, "com.obsproject.Studio obs obs-studio"),
    "telegram": (TELEGRAM, "telegram telegram-desktop org.telegram.desktop telegramdesktop "
                 "kotatogram"),
    "vscode": (VSCODE, "code visual-studio-code com.visualstudio.code vscodium "
               "com.vscodium.codium code-oss"),
    "kdenlive": (KDENLIVE, "kdenlive org.kde.kdenlive shotcut org.shotcut.Shotcut openshot "
                 "org.openshot.OpenShot pitivi video-editor"),
    "audio-editor": (AUDIO_EDITOR, "audacity org.audacityteam.Audacity org.kde.kwave kwave "
                     "tenacity ardour"),
    "headphones": (HEADPHONES, "audio-headphones audio-headset"),
    "zoom": (ZOOM, "zoom us.zoom.Zoom zoom-linux Zoom skype com.skype.Client"),
    "chat": (CHAT, "internet-chat signal-desktop org.signal.Signal whatsapp com.rtosta.zapzap "
             "zapzap element-desktop im.riot.Riot pidgin hexchat konversation "
             "org.kde.konversation neochat org.kde.neochat polari irc-chat"),
    "phone": (PHONE, "smartphone phone multimedia-player pda preferences-desktop-touchscreen"),
    "kdeconnect": (KDECONNECT, "preferences-kde-connect kdeconnect org.kde.kdeconnect.app org.kde.kdeconnect.sms "
                   "kdeconnect-app"),
    "monitor": (MONITOR, "org.xfce.xfdesktop org.xfce.ScreenSaver krdc krfb computer video-display monitor display preferences-desktop-display "
                "preferences-desktop-display-randr"),
    "laptop": (LAPTOP, "computer-laptop"),
    "sysmonitor": (SYSMONITOR, "org.xfce.taskmanager preferences-smart-status utilities-system-monitor org.kde.plasma-systemmonitor "
                   "plasma-systemmonitor ksysguard org.gnome.SystemMonitor gnome-system-monitor "
                   "io.missioncenter.MissionCenter htop btop corectrl com.leinardi.gst"),
    "development": (DEVELOPMENT, "applications-development qtcreator org.qt-project.qtcreator "
                    "kdevelop org.kde.kdevelop geany org.geany.Geany qt5-designer qt6-designer "
                    "designer qt5-assistant qt6-assistant assistant qt5-linguist qt6-linguist "
                    "linguist qt5-qdbusviewer qt6-qdbusviewer cmake-gui ddd jetbrains-toolbox "
                    "android-studio"),
    "system": (SYSTEM, "applications-system"),
    "info": (INFO, "org.xfce.about dialog-information org.kde.kinfocenter kinfocenter hwinfo hardinfo"),
    "warning": (WARNING, "dialog-warning"),
    "error": (ERROR, "dialog-error"),
    "question": (QUESTION, "dialog-question help-browser system-help help-contents-browser"),
    "key": (KEY, "dialog-password password-manager keepassxc org.keepassxc.KeePassXC seahorse "
            "org.gnome.seahorse.Application bitwarden com.bitwarden.desktop "
            "preferences-desktop-user-password kgpg gpa org.kde.kwatchgnupg"),
    "wallet": (WALLET, "kwalletmanager org.kde.kwalletmanager5 org.kde.kwalletmanager kwalletmanager2 "
               "wallet-open org.kde.keepsecret"),
    "shield-high": (shield(MI, "check"), "security-high preferences-security"),
    "shield-medium": (shield(GO, "important"), "security-medium"),
    "shield-low": (shield(RD, "x"), "security-low"),
    "calendar": (CALENDAR, "org.kde.korganizer korganizer org.kde.merkuro.calendar "
                 "org.kde.merkuro gnome-calendar org.gnome.Calendar office-calendar calendar"),
    "contacts": (CONTACTS, "org.kde.kaddressbook kaddressbook office-address-book contacts "
                 "org.gnome.Contacts org.kde.merkuro.contact"),
    "notes": (NOTES, "org.kde.knotes knotes kjots org.kde.kjots notes org.kde.klevernotes "
              "notebook com.github.xournalpp.xournalpp xournalpp joplin obsidian md.obsidian.Obsidian"),
    "clock": (CLOCK, "ktimer kronometer ktimetracker org.kde.kclock kclock org.gnome.clocks gnome-clocks clock-app "
              "preferences-system-time alarm-clock"),
    "weather": (WEATHER, "org.kde.kweather kweather org.gnome.Weather gnome-weather weather"),
    "maps": (MAPS, "org.kde.marble marble org.kde.marble.maps org.kde.marble.behaim "
             "org.gnome.Maps gnome-maps maps org.kde.itinerary"),
    "torrent": (TORRENT, "ktorrent org.kde.ktorrent qbittorrent org.qbittorrent.qBittorrent "
                "transmission transmission-qt transmission-gtk deluge de.haeckerfelix.Fragments"),
    "gamepad": (GAMEPAD, "applications-games input-gaming preferences-desktop-gaming lutris net.lutris.Lutris "
                "com.heroicgameslauncher.hgl heroic itch io.itch.itch retroarch "
                "org.libretro.RetroArch playonlinux minigalaxy com.usebottles.bottles bottles"),
    "wine": (WINE, "wine winecfg wine-uninstaller wine-notepad wine-winecfg cxmenu-cxoffice-0-crossover"),
    "multimedia": (MULTIMEDIA, "applications-multimedia preferences-desktop-multimedia"),
    "toolbox": (TOOLBOX, "applications-utilities applications-accessories utilities"),
    "education": (EDUCATION, "applications-education org.kde.kwordquiz kwordquiz kturtle"),
    "science": (SCIENCE, "applications-science org.kde.labplot labplot fastqc"),
    "cube": (CUBE, "applications-other application-x-addon"),
    "harddisk": (HARDDISK, "partitionmanager org.kde.partitionmanager preferences-system-disks kdf drive-harddisk drive-harddisk-root drive-harddisk-system "
                 "drive-harddisk-solidstate drive-multidisk drive-partition"),
    "usb": (USB, "org.xfce.volman drive-removable-media drive-removable-media-usb drive-removable-media-usb-pendrive "
            "media-removable media-flash media-flash-memory-stick media-flash-sd-mmc "
            "org.kde.isoimagewriter"),
    "optical": (OPTICAL, "media-optical drive-optical media-optical-cd media-optical-dvd "
                "media-optical-bd media-optical-audio media-optical-data media-optical-recordable "
                "media-optical-cd-audio gcdmaster k3b org.kde.k3b brasero"),
    "floppy": (FLOPPY, "media-floppy"),
    "server": (SERVER, "network-server"),
    "network": (NETWORK, "network-workgroup preferences-system-network "
                "preferences-system-network-connection"),
    "search": (SEARCH, "org.xfce.appfinder kfind kmag krunner plasma-search preferences-desktop-search preferences-desktop-baloo "
               "system-search-app org.kde.krunner"),
    "tiles": (TILES, "applications-all preferences-desktop-icons"),
    "activities": (ACTIVITIES, "preferences-desktop-activities"),
    "animations": (ANIMATIONS, "preferences-desktop-animations"),
    "cursor": (CURSOR, "preferences-desktop-cursors"),
    "default-apps": (DEFAULT_APPS, "org.xfce.settings.default-applications preferences-desktop-default-applications"),
    "colourwheel": (COLOURWHEEL, "org.xfce.settings.color kcolorchooser preferences-desktop-display-color"),
    "effects": (EFFECTS, "preferences-desktop-effects"),
    "tablet": (TABLET, "preferences-desktop-tablet input-tablet"),
    "touchpad": (TOUCHPAD, "preferences-desktop-touchpad input-touchpad"),
    "desktops": (DESKTOPS, "org.xfce.workspaces preferences-desktop-virtual"),
    "firewall": (FIREWALL, "preferences-security-firewall"),
    "tabbox": (TABBOX, "preferences-system-tabbox"),
    "bulb": (BULB, "ktip"),
    "gauge": (GAUGE, "speedometer"),
    "xorg": (XORG, "xorg"),
    "sun": (sun_icon, "preferences-system-splash"),
    "filetypes": (doc(V, "gear"), "preferences-desktop-filetype-association"),
    "keyboard": (KEYBOARD, "org.xfce.settings.keyboard input-keyboard preferences-desktop-keyboard preferences-desktop-keyboard-shortcut fcitx"),
    "mouse": (MOUSE, "org.xfce.settings.mouse kmousetool input-mouse preferences-desktop-mouse preferences-desktop-peripherals"),
    "printer": (PRINTER, "cups printer preferences-devices-printer"),
    "speaker": (SPEAKER, "audio-speakers audio-speaker preferences-desktop-sound "
                "preferences-desktop-sounds org.pulseaudio.pavucontrol pavucontrol"),
    "soundcard": (SOUNDCARD, "audio-card"),
    "battery": (BATTERY, "org.xfce.powermanager preferences-system-power-management preferences-system-power"),
    "webcam": (WEBCAM, "camera-web"),
    "shutdown": (SHUTDOWN, "system-shutdown"),
    "reboot": (REBOOT, "system-reboot"),
    "lock": (LOCK, "system-lock-screen"),
    "logout": (LOGOUT, "system-log-out"),
    "suspend": (SUSPEND, "system-suspend"),
    "hibernate": (HIBERNATE, "system-hibernate system-suspend-hibernate"),
    "users": (USERS, "org.xfce.session system-switch-user preferences-system-users"),
    "bell": (BELL, "org.xfce.notification preferences-desktop-notification preferences-desktop-notification-bell"),
    "window": (WINDOW, "org.xfce.panel org.xfce.PanelProfiles org.xfce.xfwm4 org.xfce.xfwm4-tweaks org.xfce.settings.appearance preferences-system-windows preferences-system-windows-actions preferences-desktop-theme "
               "preferences-desktop-theme-global preferences-desktop-theme-applications "
               "preferences-desktop-plasma-theme preferences-desktop-theme-windowdecorations"),
    "font": (FONT, "kfontview kcharselect org.kde.kcharselect preferences-desktop-font preferences-desktop-font-installer"),
    "bluetooth": (BLUETOOTH, "preferences-system-bluetooth"),
    "accessibility": (ACCESSIBILITY, "org.xfce.settings.accessibility preferences-desktop-accessibility"),
    "person": (PERSON, "user-identity-app preferences-desktop-user preferences-system-login"),
    "writer": (doc(V, "documents"), "libreoffice-writer libreoffice-main libreoffice "
               "libreoffice-startcenter org.libreoffice.LibreOffice.writer "
               "org.libreoffice.LibreOffice onlyoffice-desktopeditors "
               "org.onlyoffice.desktopeditors applications-office"),
    "calc": (doc(MI, "grid"), "libreoffice-calc org.libreoffice.LibreOffice.calc"),
    "impress": (doc(OR, "chart"), "libreoffice-impress org.libreoffice.LibreOffice.impress"),
    "draw": (doc(GO, "pen"), "libreoffice-draw org.libreoffice.LibreOffice.draw"),
    "base": (doc(RO, "database"), "libreoffice-base org.libreoffice.LibreOffice.base"),
    "math": (doc(GY, "braces"), "libreoffice-math org.libreoffice.LibreOffice.math"),
}


# Designs standing in for an app's own logo.  Where the app is installed its
# real logo is converted instead (build_icons), which keeps it recognisable;
# these are for the apps that are not.
BRANDS = {"firefox", "chrome", "thunderbird", "steam", "discord", "spotify", "vlc", "gimp",
          "inkscape", "krita", "blender", "obs", "telegram", "vscode", "kdenlive", "audio-editor",
          "zoom"}


# Converted icons that were looked at and came out clean and recognisable.
# Every other conversion is replaced by a letter tile: no measure tells a
# clean conversion from one that reads as noise or as a shapeless blob as well
# as looking does.  Add to this only after looking.
CONVERT_OK = {
    # brands, whose own logo beats the design standing in for it
    "firefox", "discord", "com.spotify.Client", "spotify", "org.telegram.desktop", "telegram",
    "zoom-linux", "zoom",
    # apps
    "emacs", "claude-desktop", "ghostwriter", "blueman", "CMakeSetup", "account-google",
    "antigravity", "gtk3-demo", "ibus", "io.github.Hexchat", "io.github.janbar.noson",
    "org.gnome.Adwaita1.Demo", "org.gtk.gtk4.NodeEditor", "org.kde.kalm", "org.kde.kontrast",
    "qv4l2", "qvidcap", "rstudio", "sonolin", "zint-qt", "steam_icon_1771300", "steam_icon_459220",
    "kwikdisk", "akregator", "blinken", "palapeli", "pinentry",
    # KDE's games and toys with bold, simple logos
    "kdominate", "klickety", "granatier", "kalarm", "kapman", "kblocks", "kbreakout", "kdiamond",
    "kmouth", "kmymoney", "knights", "kolf", "kruler", "minuet", "sweeper", "kteatime", "kiriki",
    "kjumpingcube", "skladnik",
}


def brand_names():
    return {name for design in BRANDS for name in DESIGNS[design][1].split()}


def render(design, n):
    """One design on an n-cell grid."""
    layers = DESIGNS[design][0]
    return layers(n) if callable(layers) else draw(n, layers)


def names():
    """{icon name: design}"""
    out = {}
    for design, (_, ns) in DESIGNS.items():
        for name in ns.split():
            out.setdefault(name, design)
    return out
