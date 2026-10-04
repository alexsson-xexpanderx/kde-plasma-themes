#!/usr/bin/env bash
# Set Departure Mono to the best size for this screen, desktop and Konsole.
#
#   ./font-size.sh              pick a size and set it
#   ./font-size.sh --size 13    start from 13 pt instead of 12
#   ./font-size.sh --show       only show what it would pick
#   ./font-size.sh --scale 1.9  use this display scale instead of reading it
#
# Departure Mono is a pixel font, sharp only where each of its pixels is a
# whole number of screen pixels.  If such a size is within 1.5 pt of the one
# you like, it uses that; otherwise it keeps yours, which is a little softer.
set -eu

size=12 scale="" show=no
while [ $# -gt 0 ]; do
    case "$1" in
        --size) size="$2"; shift ;;
        --scale) scale="$2"; shift ;;
        --show) show=yes ;;
        -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
    shift
done

# The main screen's scale, as KDE has it.
if [ -z "$scale" ] && command -v kscreen-doctor >/dev/null; then
    scale="$(timeout 5 kscreen-doctor -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | awk '
        /^Output:/          { on = 0; main = 0 }
        /^[[:space:]]+enabled$/ { on = 1 }
        /priority 1$/       { main = 1 }
        /Scale:/            { if (on && main) { print $2; exit }
                              if (on && first == "") first = $2 }
        END                 { if (first != "") print first }' | head -n 1)"
fi
# Or KWin's saved settings, outside a running Plasma session.
config="${XDG_CONFIG_HOME:-$HOME/.config}/kwinoutputconfig.json"
if [ -z "$scale" ] && [ -f "$config" ]; then
    scale="$(grep -o '"scale": *[0-9.]*' "$config" | head -n 1 | grep -o '[0-9.]*$' || true)"
fi
if [ -z "$scale" ]; then
    echo "Could not read the display scale; using 1 (100%). Pass --scale to set it." >&2
    scale=1
fi

# The sharp sizes: one font pixel (an eleventh of the em) to n screen pixels.
# n x 11 screen pixels is that over the scale in logical pixels, 0.75 pt each.
read -r sharp near list < <(awk -v s="$scale" -v want="$size" 'BEGIN {
    gap = 1e9
    for (n = 1; n <= 10; n++) {
        pt = n * 11 / s * 0.75
        if (pt >= 7 && pt <= 24) list = list (list ? "," : "") sprintf("%.2f", pt)
        d = pt > want ? pt - want : want - pt
        if (d < gap) { gap = d; best = pt }
    }
    printf "%.2f %s %s\n", best, (gap <= 1.5 ? "yes" : "no"), list }')

if [ "$near" = yes ]; then pt="$sharp"; why="sharp at this scale"; else pt="$size"; why="no sharp size near $size pt"; fi
small="$(awk -v p="$pt" 'BEGIN { s = p - 2; if (s < 8) s = 8; printf "%.1f", s }')"

echo "Display scale:       $(awk -v s="$scale" 'BEGIN { printf "%g%%", s * 100 }')"
echo "Sharp sizes:         $(echo "$list" | sed 's/,/ pt, /g') pt"
echo "Chosen:              $pt pt ($why), $small pt for the smallest text"
[ "$show" = yes ] && exit 0

if ! fc-list : family 2>/dev/null | grep -q 'Departure Mono'; then
    echo "Departure Mono is not installed; run ./install.sh first." >&2
    exit 1
fi

font() { printf 'Departure Mono,%s,-1,5,400,0,0,0,0,0,0,0,0,0,0,1' "$1"; }

for key in font fixed menuFont toolBarFont; do
    kwriteconfig6 --notify --file kdeglobals --group General --key "$key" "$(font "$pt")"
done
kwriteconfig6 --notify --file kdeglobals --group General --key smallestReadableFont "$(font "$small")"
kwriteconfig6 --notify --file kdeglobals --group WM --key activeFont "$(font "$pt")"

# Konsole: the default profile, and the theme's own if it is installed.
profiles="${XDG_DATA_HOME:-$HOME/.local/share}/konsole"
default="$(kreadconfig6 --file konsolerc --group 'Desktop Entry' --key DefaultProfile 2>/dev/null || true)"
for p in "$default" Retrograde.profile; do
    if [ -n "$p" ] && [ -f "$profiles/$p" ]; then
        kwriteconfig6 --file "$profiles/$p" --group Appearance --key Font "$(font "$pt")"
        echo "Konsole profile:     $p"
    fi
done

echo "Done. Open new windows, or log out and in, to see it everywhere."
