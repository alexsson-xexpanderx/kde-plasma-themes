#!/usr/bin/env bash
# Install Retrograde for the current user.
#
#   ./install.sh            copy the theme into ~/.local/share
#   ./install.sh --apply    and switch to it (same as picking it in System Settings)
#
# Only paths named Retrograde under ~/.local/share are written; nothing else is
# touched.  Run ./uninstall.sh to take them out again.
set -eu

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
src="$here/theme"
data="${XDG_DATA_HOME:-$HOME/.local/share}"

apply=no
for arg in "$@"; do
    case "$arg" in
        --apply) apply=yes ;;
        -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done

if [ ! -d "$src/plasma/look-and-feel/Retrograde" ]; then
    echo "theme/ is missing; build it first: python3 src/build.py" >&2
    exit 1
fi

# Each entry: path under theme/ and under ~/.local/share alike.
parts=(
    aurorae/themes/Retrograde
    color-schemes/Retrograde.colors
    konsole/Retrograde.colorscheme
    konsole/Retrograde.profile
    icons/Retrograde
    icons/Retrograde-cursors
    plasma/desktoptheme/Retrograde
    plasma/look-and-feel/Retrograde
    wallpapers/Retrograde
)

for part in "${parts[@]}"; do
    dest="$data/$part"
    mkdir -p "$(dirname -- "$dest")"
    rm -rf -- "$dest"
    cp -r -- "$src/$part" "$dest"
    echo "  $dest"
done

# Pixel versions of the icons of apps installed here that the icon theme has
# none of.  They are made from those apps' own icons, so they are made on this
# machine and not shipped; skipped if Python's numpy and Pillow or
# rsvg-convert are missing.  Run again after installing new apps.
if command -v rsvg-convert >/dev/null && python3 -c "import numpy, PIL" 2>/dev/null; then
    python3 "$here/src/build_icons.py" --local "$data/icons/Retrograde"
else
    echo "  (skipped pixel icons for installed apps: needs python3-numpy, python3-pillow, rsvg-convert)"
fi

echo
if [ "$apply" = yes ]; then
    plasma-apply-lookandfeel --apply Retrograde
    echo "Retrograde is applied.  Window decorations and the cursor take full"
    echo "effect in newly opened windows; log out and in to see the splash."
else
    echo "Installed.  Pick Retrograde in System Settings > Colors & Themes >"
    echo "Global Theme, or run:  plasma-apply-lookandfeel --apply Retrograde"
fi
