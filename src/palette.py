"""The Retrograde palette.  Every file the build writes takes its colours from here.

Night tones are a blue-violet near-black, the colour of the sky an hour after
sunset.  The accents are a 1970s sunset -- mauve, pink, coral, amber, gold --
plus the two cool colours Conky Orrery uses for the time of day.  They are
the Catppuccin-family colours the Orrery already draws in, pushed a little
warmer, and the pink sits next to conky-dashboard's #FF4081.
"""

NAME = "Retrograde"
AUTHOR = "alexsson"
VERSION = "1.0"

# Night: backgrounds, darkest first.
VOID = "#0A0913"     # shadows, the deepest sky
CRUST = "#100E1C"    # title bars, toolbars, the panel
MANTLE = "#161427"   # window backgrounds
BASE = "#1C1A30"     # raised surfaces: buttons, cards
SURFACE0 = "#252239"
SURFACE1 = "#312D4A"  # hairlines and outlines
SURFACE2 = "#433E62"
OVERLAY0 = "#5E5882"  # disabled text
OVERLAY1 = "#7E78A2"  # inactive text
SUBTEXT = "#AAA5CA"   # secondary text
TEXT = "#E7E4F6"      # the Orrery's clock colour, near enough
BRIGHT = "#F7F5FF"

# The sunset.  Read top to bottom it is the stripe across every active window.
MAUVE = "#C3A6FF"
PINK = "#FF5C8A"
CORAL = "#FF8266"
AMBER = "#FFAE5C"
GOLD = "#FFD685"
SUNSET = [MAUVE, PINK, CORAL, AMBER, GOLD]

# Cool colours: the Orrery's "today" and its seconds hoop.
SKY = "#8BE3F7"
BLUE = "#89B4FA"

# Signals.
MINT = "#8EE6B0"   # positive
RED = "#FF4F6A"    # negative
CREAM = "#F9E2AF"  # the Orrery's readouts

ACCENT = PINK


def rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(r, g, b):
    return "#%02X%02X%02X" % (round(r), round(g), round(b))


def mix(a, b, t):
    """t = 0 gives a, t = 1 gives b."""
    ra, rb = rgb(a), rgb(b)
    return hexc(*[x + (y - x) * t for x, y in zip(ra, rb)])


def csv(hex_colour):
    """KDE colour files write colours as r,g,b."""
    return ",".join(str(c) for c in rgb(hex_colour))


def luminance(hex_colour):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb(hex_colour))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# Icon ramps, dark to light.  Most are the wallpaper's own dithering ramps
# (build_wallpaper.py: the sky, the planet's bands, its rings); the icons take
# their colours from these so they sit on the desktop as part of the picture.
RAMP_VIOLET = ["#2A1E52", "#4A378A", "#6E55B8", "#9A80E0", "#C8B4FF"]
RAMP_ROSE = ["#3A1844", "#6A2A68", "#A2407E", "#D7649A", "#FF9EC0"]
RAMP_RED = ["#561F59", "#962C64", "#BC3966", "#E04F67", "#FF6E64"]
RAMP_ORANGE = ["#962C64", "#E04F67", "#FF6E64", "#FF915E", "#FFB45E"]
RAMP_GOLD = ["#9A7660", "#D2A878", "#FFB45E", "#FFD27A", "#FFF0C8"]
RAMP_BROWN = ["#2A1F2E", "#5C4448", "#9A7660", "#D2A878", "#F6D79A"]
RAMP_GREY = [SURFACE0, SURFACE2, OVERLAY1, SUBTEXT, TEXT]
# Not in the wallpaper: where candy draws in blue-green and cyan, the icons go
# to the sky blue the Orrery used to draw "today" in, and its shades.
RAMP_SKY = ["#22385E", "#3E6A9A", "#5FA6D0", SKY, "#D2F6FF"]
# Only for a folder the user colours green in Dolphin.
RAMP_MINT = ["#1E4A44", "#2E7A62", "#52B08A", MINT, "#D0F7E0"]
