#!/usr/bin/env bash
# Remove what install.sh put in ~/.local/share.
#
# Switch to another global theme first (System Settings > Colors & Themes >
# Global Theme); this only deletes files, it does not change your settings.
set -eu

data="${XDG_DATA_HOME:-$HOME/.local/share}"
parts=(
    aurorae/themes/Retrograde
    color-schemes/Retrograde.colors
    fonts/Retrograde
    konsole/Retrograde.colorscheme
    konsole/Retrograde.profile
    icons/Retrograde
    icons/Retrograde-cursors
    plasma/desktoptheme/Retrograde
    plasma/look-and-feel/Retrograde
    wallpapers/Retrograde
)

for part in "${parts[@]}"; do
    if [ -e "$data/$part" ]; then
        rm -rf -- "${data:?}/$part"
        echo "  removed $data/$part"
    fi
done

if command -v fc-cache >/dev/null && [ -d "$data/fonts" ]; then
    fc-cache "$data/fonts"
fi
