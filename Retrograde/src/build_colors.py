"""Colour scheme for applications, and the Konsole scheme and profile."""

from pathlib import Path

from palette import *  # noqa: F401,F403
import palette as P
import build_fonts as FN


def section(name, values):
    lines = ["[%s]" % name]
    for key in sorted(values):
        lines.append("%s=%s" % (key, values[key]))
    return "\n".join(lines) + "\n"


def colours(bg, bg_alt, fg, fg_inactive, focus=P.ACCENT, hover=P.ACCENT,
            active=P.PINK, link=P.SKY, visited=P.MAUVE):
    return {
        "BackgroundNormal": P.csv(bg),
        "BackgroundAlternate": P.csv(bg_alt),
        "ForegroundNormal": P.csv(fg),
        "ForegroundInactive": P.csv(fg_inactive),
        "ForegroundActive": P.csv(active),
        "ForegroundLink": P.csv(link),
        "ForegroundVisited": P.csv(visited),
        "ForegroundNegative": P.csv(P.RED),
        "ForegroundNeutral": P.csv(P.AMBER),
        "ForegroundPositive": P.csv(P.MINT),
        "DecorationFocus": P.csv(focus),
        "DecorationHover": P.csv(hover),
    }


def colour_scheme():
    parts = []
    parts.append(section("ColorEffects:Disabled", {
        "Color": P.csv(P.MANTLE), "ColorAmount": "0", "ColorEffect": "0",
        "ContrastAmount": "0.55", "ContrastEffect": "1",
        "IntensityAmount": "0.1", "IntensityEffect": "2",
    }))
    parts.append(section("ColorEffects:Inactive", {
        "ChangeSelectionColor": "true", "Color": P.csv(P.MANTLE),
        "ColorAmount": "0.025", "ColorEffect": "2",
        "ContrastAmount": "0.1", "ContrastEffect": "2", "Enable": "false",
        "IntensityAmount": "0", "IntensityEffect": "0",
    }))
    parts.append(section("Colors:Button", colours(
        P.BASE, P.SURFACE0, P.TEXT, P.OVERLAY1)))
    parts.append(section("Colors:Complementary", colours(
        P.VOID, P.CRUST, P.TEXT, P.OVERLAY1)))
    parts.append(section("Colors:Header", colours(
        P.CRUST, P.MANTLE, P.TEXT, P.OVERLAY1)))
    parts.append(section("Colors:Header[Inactive]", colours(
        P.CRUST, P.MANTLE, P.SUBTEXT, P.OVERLAY0)))
    # Dark text on the pink: 7:1, where white on it would be under 3:1.
    parts.append(section("Colors:Selection", colours(
        P.ACCENT, P.mix(P.ACCENT, P.MAUVE, 0.5), P.CRUST, P.mix(P.CRUST, P.ACCENT, 0.35),
        active=P.CRUST, link=P.VOID, visited=P.VOID)))
    parts.append(section("Colors:Tooltip", colours(
        P.CRUST, P.MANTLE, P.TEXT, P.OVERLAY1)))
    parts.append(section("Colors:View", colours(
        P.CRUST, P.mix(P.CRUST, P.MANTLE, 0.55), P.TEXT, P.OVERLAY1)))
    parts.append(section("Colors:Window", colours(
        P.MANTLE, P.BASE, P.TEXT, P.OVERLAY1)))
    parts.append(section("General", {
        "ColorScheme": P.NAME, "Name": P.NAME, "shadeSortColumn": "true",
    }))
    parts.append(section("KDE", {"contrast": "4"}))
    parts.append(section("WM", {
        "activeBackground": P.csv(P.CRUST), "activeBlend": P.csv(P.CRUST),
        "activeForeground": P.csv(P.TEXT),
        "inactiveBackground": P.csv(P.CRUST), "inactiveBlend": P.csv(P.CRUST),
        "inactiveForeground": P.csv(P.OVERLAY1),
    }))
    return "\n".join(parts)


# Konsole.  Normal, faint and intense for each of the eight ANSI colours.
ANSI = [
    # normal,   intense
    (P.SURFACE1, P.OVERLAY0),           # black
    (P.RED, "#FF7D92"),                 # red
    (P.MINT, "#B1F0C9"),                # green
    (P.GOLD, "#FFE4AC"),                # yellow
    (P.BLUE, "#AECBFC"),                # blue
    (P.MAUVE, "#D8C6FF"),               # magenta
    (P.SKY, "#B4EDFA"),                 # cyan
    (P.SUBTEXT, P.TEXT),                # white
]


def konsole_scheme():
    parts = [section("Background", {"Color": P.csv(P.CRUST)}),
             section("BackgroundFaint", {"Color": P.csv(P.CRUST)}),
             section("BackgroundIntense", {"Color": P.csv(P.MANTLE)})]
    for i, (normal, intense) in enumerate(ANSI):
        parts.append(section("Color%d" % i, {"Color": P.csv(normal)}))
        parts.append(section("Color%dFaint" % i, {"Color": P.csv(P.mix(normal, P.CRUST, 0.4))}))
        parts.append(section("Color%dIntense" % i, {"Color": P.csv(intense)}))
    parts += [section("Foreground", {"Color": P.csv(P.TEXT)}),
              section("ForegroundFaint", {"Color": P.csv(P.OVERLAY1)}),
              section("ForegroundIntense", {"Color": P.csv(P.BRIGHT)}),
              section("General", {"Anchor": "0.5,0.5", "Blur": "true",
                                  "ColorRandomization": "false",
                                  "Description": P.NAME, "FillStyle": "Tile",
                                  "Opacity": "0.9", "Wallpaper": "",
                                  "WallpaperFlipType": "NoFlip",
                                  "WallpaperOpacity": "1"})]
    return "\n".join(parts)


def konsole_profile():
    return "\n".join([
        section("Appearance", {
            "ColorScheme": P.NAME,
            "Font": FN.qfont(),
            "UseFontLineChararacters": "true",
        }),
        section("Cursor Options", {
            "CursorShape": "0",
            "CustomCursorColor": P.csv(P.PINK),
            "CustomCursorTextColor": P.csv(P.CRUST),
            "UseCustomCursorColor": "true",
        }),
        section("General", {
            "Name": P.NAME, "Parent": "FALLBACK/", "TerminalMargin": "14",
            "TerminalCenter": "true",
        }),
        section("Terminal Features", {"BlinkingCursorEnabled": "true"}),
    ])


def build(out):
    out = Path(out)
    (out / "color-schemes").mkdir(parents=True, exist_ok=True)
    (out / "color-schemes" / ("%s.colors" % P.NAME)).write_text(colour_scheme())
    (out / "konsole").mkdir(parents=True, exist_ok=True)
    (out / "konsole" / ("%s.colorscheme" % P.NAME)).write_text(konsole_scheme())
    (out / "konsole" / ("%s.profile" % P.NAME)).write_text(konsole_profile())


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "theme")
    print("selection text contrast %.1f:1" % P.contrast(P.CRUST, P.ACCENT))
    print("body text contrast %.1f:1" % P.contrast(P.TEXT, P.MANTLE))
    print("inactive text contrast %.1f:1" % P.contrast(P.OVERLAY1, P.MANTLE))
