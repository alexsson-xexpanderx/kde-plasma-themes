"""Extras: retrofetch, a small system fetch whose logo is the striped sun drawn
in real pixels -- half-block characters, two pixels to a character cell, each
in its own 24-bit colour."""

import math
import stat
from pathlib import Path

import palette as P

W, H = 20, 16   # logo size in pixels; H must be even


def sun_pixels():
    ramp = ["#FFE08A", "#FFD27A", "#FFC46A", "#FFB45E", "#FFA05E", "#FF8A62",
            "#FF7A62", "#FF6A6E", "#FF5C78", "#F0507C", "#E8467E"]
    cx, cy, r = W / 2, 8.6, 8.2
    px = [[None] * W for _ in range(H)]
    gaps = {9: 1, 11: 1, 13: 2}           # slats: row -> height, thicker lower down
    skip = set()
    for row, hgt in gaps.items():
        skip.update(range(row, row + hgt))
    for y in range(H):
        for x in range(W):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r and y not in skip:
                px[y][x] = ramp[min(len(ramp) - 1, int(y / H * len(ramp)))]
    # the horizon under it
    for x in range(W):
        if px[H - 1][x] is None:
            px[H - 1][x] = P.MAUVE if x % 2 == 0 else None
    return px


def fg(c):
    r, g, b = P.rgb(c)
    return "\\e[38;2;%d;%d;%dm" % (r, g, b)


def bg(c):
    r, g, b = P.rgb(c)
    return "\\e[48;2;%d;%d;%dm" % (r, g, b)


def logo_lines():
    px = sun_pixels()
    lines = []
    for y in range(0, H, 2):
        out = ""
        for x in range(W):
            top, bot = px[y][x], px[y + 1][x]
            if top and bot:
                out += fg(top) + bg(bot) + "▀\\e[0m"
            elif top:
                out += fg(top) + "▀\\e[0m"
            elif bot:
                out += fg(bot) + "▄\\e[0m"
            else:
                out += " "
        lines.append(out)
    return lines


SCRIPT = r'''#!/usr/bin/env bash
# retrofetch -- a system fetch for the Retrograde theme.
#   retrofetch            your system
#   RETROFETCH_DEMO=1     the theme's own facts, for screenshots
logo=(
%(logo)s
)
keys=('%(pink)s' '%(coral)s' '%(amber)s' '%(gold)s' '%(mauve)s' '%(sky)s' '%(blue)s')

if [ -n "$RETROFETCH_DEMO" ]; then
    who="retrograde"; host="observatory"
    rows=("theme|Retrograde" "style|pixel corners, hard shadows" "windows|KWin, planet buttons"
          "font|Noto Sans, Hack" "conky|Orrery, dashboard" "cursor|Retrograde pixel"
          "palette|dusk")
else
    who="${USER:-$(id -un)}"; host="$(hostname 2>/dev/null || cat /etc/hostname)"
    os="$(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-$(uname -s)}")"
    up="$(uptime -p 2>/dev/null | sed 's/^up //')"
    plasma="$(plasmashell --version 2>/dev/null | awk '{print $2}')"
    rows=("os|$os" "kernel|$(uname -r)" "uptime|$up" "shell|$(basename "${SHELL:-sh}")"
          "desktop|Plasma ${plasma:-?}" "theme|Retrograde" "term|${TERM_PROGRAM:-$TERM}")
fi

printf '\n'
printf '  %%s  \e[1m%(pink)s%%s\e[0m%(sub)s@\e[1m%(sky)s%%s\e[0m\n' "${logo[0]}" "$who" "$host"
printf '  %%s  %(dim)s%%s\e[0m\n' "${logo[1]}" "$(printf '%%*s' $(( ${#who} + ${#host} + 1 )) '' | tr ' ' '-')"
for i in 0 1 2 3 4 5; do
    IFS='|' read -r k v <<< "${rows[$i]}"
    printf '  %%s  ' "${logo[$((i + 2))]}"
    printf '%%b%%-9s\e[0m%%s\n' "${keys[$i]}" "$k" "$v"
done
printf '\n  '
for i in 0 1 2 3 4 5 6 7; do printf '\e[4%%dm   ' "$i"; done; printf '\e[0m\n  '
for i in 0 1 2 3 4 5 6 7; do printf '\e[10%%dm   ' "$i"; done; printf '\e[0m\n\n'
'''


def build(out):
    d = Path(out).parent / "extras"
    d.mkdir(parents=True, exist_ok=True)
    logo = "\n".join("    $'%s'" % l for l in logo_lines())
    script = SCRIPT % {
        "logo": logo, "pink": fg(P.PINK), "coral": fg(P.CORAL), "amber": fg(P.AMBER),
        "gold": fg(P.GOLD), "mauve": fg(P.MAUVE), "sky": fg(P.SKY), "blue": fg(P.BLUE),
        "sub": fg(P.SUBTEXT), "dim": fg(P.SURFACE2),
    }
    path = d / "retrofetch"
    path.write_text(script)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "theme")
