"""Extras: retrofetch, a small system fetch whose logo is a ringed planet like
the wallpaper's, drawn in real pixels -- half-block characters, two pixels to
a character cell, each in its own 24-bit colour."""

import math
import stat
from pathlib import Path

import palette as P

# The logo, laid out by hand: p the planet, a 13-pixel circle; b its ring
# behind it, f in front, F the ring's lit inner edge; * a sparkle, + its arms,
# and o w c m the other stars.  The planet and ring are mirrored to the pixel
# about the middle column; the ring is a one-pixel ellipse, 25 by 7, two
# pixels thick where it crosses in front.
LOGO = [
    "..+..............g.......",
    ".+*+......ppppp..........",
    "..+.....ppppppppp........",
    ".......ppppppppppp....w..",
    ".......ppppppppppp.......",
    "...bbbpppppppppppppbbb...",
    ".bb...ppppppppppppp...bb.",
    "f.....ppppppppppppp.....f",
    ".ff...ppppppppppppp...ff.",
    "...ffffFFFFFFFFFFFffff...",
    ".......fffffffffff.......",
    ".......ppppppppppp.......",
    ".m......ppppppppp........",
    "..........ppppp..........",
    "......................c..",
    ".........................",
]
W, H = len(LOGO[0]), len(LOGO)   # H must be even
MID, EQUATOR, RADIUS = W // 2, 7, 6.5

# The wallpaper's planet bands and ring, darkest first.
ROSE = ["#3A1844", "#6A2A68", "#A2407E", "#D7649A", "#FF9EC0"]
VIOLET = ["#2A1E52", "#4A378A", "#6E55B8", "#9A80E0", "#C8B4FF"]
DUSTY = ["#33203E", "#5A3A62", "#8A5F86", "#BC92B2", "#EBCBE0"]
RING = ["#5C4448", "#9A7660", "#D2A878", "#F6D79A", "#FFF0C8"]
BANDS = {1: DUSTY, 2: DUSTY, 3: ROSE, 4: ROSE, 5: VIOLET, 6: VIOLET, 7: ROSE, 8: ROSE,
         11: VIOLET, 12: VIOLET, 13: DUSTY}
NIGHT = "#100E1C"
STARS = {"*": P.GOLD, "+": P.mix(P.GOLD, NIGHT, 0.45), "w": P.TEXT, "c": P.SKY,
         "m": P.MAUVE, "g": P.SUBTEXT}


def light(x, y):
    """Light on the sphere, from the upper left and in front."""
    dx, dy = (x - MID) / RADIUS, (y - EQUATOR) / RADIUS
    dz = math.sqrt(max(0.0, 1 - dx * dx - dy * dy))
    lx, ly, lz = -0.5, -0.6, 0.62
    return max(0.0, (dx * lx + dy * ly + dz * lz) / math.sqrt(lx * lx + ly * ly + lz * lz))


def tone(ramp, t):
    return ramp[max(0, min(len(ramp) - 1, int(t * len(ramp))))]


def logo_pixels():
    body = [row.translate(str.maketrans("".join(STARS), "." * len(STARS))) for row in LOGO]
    for row in body:
        assert len(row) == W and row == row[::-1], "the planet must be symmetric"
    px = [[None] * W for _ in range(H)]
    for y, row in enumerate(LOGO):
        for x, m in enumerate(row):
            across = 1 - abs(x - MID) / MID          # 1 in the middle, 0 at the ring's tips
            if m == "p":
                t = 0.3 + 0.75 * light(x, y) ** 0.9
                if y == 11:                          # the ring's shadow, just under it
                    t = max(0.25, t - 0.2)
                px[y][x] = tone(BANDS[y], t)
                # The sunset, low on the wallpaper, lights the lower right edge.
                edge = any(not (0 <= y + dy < H and 0 <= x + dx < W) or body[y + dy][x + dx] == "."
                           for dx, dy in ((1, 0), (0, 1), (1, 1)))
                if edge and x - MID >= 3 and y - EQUATOR >= -2:
                    px[y][x] = P.mix(px[y][x], "#FF8A7A", 0.55)
            elif m == "F":
                px[y][x] = tone(RING, 0.78 + 0.2 * across)
            elif m == "f":
                px[y][x] = tone(RING, 0.5 + 0.25 * across)
            elif m == "b":
                px[y][x] = P.mix(tone(RING, 0.55 + 0.2 * across), NIGHT, 0.4)
            elif m in STARS:
                px[y][x] = STARS[m]
    return px


def fg(c):
    r, g, b = P.rgb(c)
    return "\\e[38;2;%d;%d;%dm" % (r, g, b)


def bg(c):
    r, g, b = P.rgb(c)
    return "\\e[48;2;%d;%d;%dm" % (r, g, b)


def logo_lines():
    px = logo_pixels()
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
keys=('%(pink)s' '%(coral)s' '%(amber)s' '%(gold)s' '%(mint)s' '%(sky)s' '%(blue)s' '%(mauve)s')

if [ -n "$RETROFETCH_DEMO" ]; then
    who="retrograde"; host="observatory"
    rows=("theme|Retrograde" "style|pixel corners, hard shadows" "windows|KWin, planet buttons"
          "font|Departure Mono" "conky|Orrery, dashboard" "cursor|Retrograde pixel"
          "palette|dusk")
else
    who="${USER:-$(id -un)}"; host="$(hostname 2>/dev/null || cat /etc/hostname)"
    os="$(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-$(uname -s)}")"
    up="$(uptime -p 2>/dev/null | sed 's/^up //')"
    plasma="$(plasmashell --version 2>/dev/null | awk '{print $2}')"

    # The CPU's model without the trademarks and the clock, and its threads.
    cpu="$(sed -n 's/^model name[[:space:]]*: //p' /proc/cpuinfo | head -n 1 \
           | sed -e 's/(R)//g; s/(TM)//g; s/ CPU//; s/ @.*//; s/ [0-9]*-Core Processor//' \
                 -e 's/ Processor//; s/  */ /g; s/ *$//')"
    cpu="${cpu:-unknown} ($(nproc 2>/dev/null || echo ?))"

    # The GPU's name as its driver gives it; lspci's where glxinfo is missing.
    gpu="$(glxinfo -B 2>/dev/null | sed -n 's/^OpenGL renderer string: //p' | sed 's/ (.*//')"
    if [ -z "$gpu" ] && command -v lspci >/dev/null; then
        gpu="$(lspci -mm 2>/dev/null | awk -F'"' '/VGA|3D|Display/ {
            v = $4; d = $6
            if (v ~ /^Advanced Micro Devices/) v = "AMD"
            else if (v ~ /^Intel/) v = "Intel"
            else if (v ~ /^NVIDIA/) v = "NVIDIA"
            if (match(d, /\[.*\]/)) d = substr(d, RSTART + 1, RLENGTH - 2)
            print v " " d; exit }')"
    fi

    # Memory in use, as free(1) counts it, of the total.
    ram="$(awk '/^MemTotal:/ {t = $2} /^MemAvailable:/ {a = $2}
                END {printf "%%.1f GiB / %%.1f GiB", (t - a) / 1048576, t / 1048576}' /proc/meminfo)"

    rows=("os|$os" "kernel|$(uname -r)" "uptime|$up" "shell|$(basename "${SHELL:-sh}")"
          "desktop|Plasma ${plasma:-?}" "theme|Retrograde"
          "cpu|$cpu" "gpu|${gpu:-unknown}" "ram|$ram")
fi

# The colour bar: the eight colours over their bright versions, one half
# block each with a gap between, centred under the planet.
bar="%(bar_side)s"
for i in 0 1 2 3 4 5 6 7; do
    [ "$i" -gt 0 ] && bar+=" "
    printf -v square '\e[3%%dm\e[10%%dm▀\e[0m' "$i" "$i"
    bar+="$square"
done
bar+="%(bar_side)s"

# The text: who and where, a rule under it, then a key and a value a row.
printf -v line '\e[1m%(pink)s%%s\e[0m%(sub)s@\e[1m%(sky)s%%s\e[0m' "$who" "$host"
text=("$line")
printf -v line '%(dim)s%%s\e[0m' "$(printf '%%*s' $(( ${#who} + ${#host} + 1 )) '' | tr ' ' '-')"
text+=("$line")
for i in "${!rows[@]}"; do
    IFS='|' read -r k v <<< "${rows[$i]}"
    printf -v line '%%b%%-9s\e[0m%%s' "${keys[$(( i %% ${#keys[@]} ))]}" "$k" "$v"
    text+=("$line")
done

# The planet with the bar right under it, centred against the text.
art=("${logo[@]}" "$bar")
lines=$(( ${#text[@]} > ${#art[@]} ? ${#text[@]} : ${#art[@]} ))
top=$(( (lines - ${#art[@]}) / 2 ))
printf '\n'
for (( i = 0; i < lines; i++ )); do
    a=$(( i - top ))
    if (( a >= 0 && a < ${#art[@]} )); then left="${art[$a]}"; else left="%(blank)s"; fi
    printf '  %%s  %%s\n' "$left" "${text[$i]:-}"
done
printf '\n'
'''


def bar_side():
    """Spaces either side of the colour bar, eight squares and seven gaps, so
    that it is exactly as wide as the logo and centred under it."""
    assert (W - 15) % 2 == 0
    return " " * ((W - 15) // 2)


def build(out):
    d = Path(out).parent / "extras"
    d.mkdir(parents=True, exist_ok=True)
    logo = "\n".join("    $'%s'" % l for l in logo_lines())
    script = SCRIPT % {
        "logo": logo, "pink": fg(P.PINK), "coral": fg(P.CORAL), "amber": fg(P.AMBER),
        "gold": fg(P.GOLD), "mauve": fg(P.MAUVE), "sky": fg(P.SKY), "blue": fg(P.BLUE),
        "mint": fg(P.MINT), "sub": fg(P.SUBTEXT), "dim": fg(P.SURFACE2),
        "bar_side": bar_side(), "blank": " " * W,
    }
    path = d / "retrofetch"
    path.write_text(script)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "theme")
