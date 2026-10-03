#!/usr/bin/env bash
# Install the Retrograde login screen (SDDM) for the whole system.  SDDM
# reads its themes from /usr/share/sddm/themes, so this needs root.
#
#   sudo ./install-sddm.sh           copy it to /usr/share/sddm/themes/Retrograde
#   sudo ./install-sddm.sh --remove  take it out again
#
# Then pick Retrograde in System Settings > Colors & Themes > Login Screen
# (SDDM).  Installing changes no setting by itself.
set -eu

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
src="$here/theme/sddm/Retrograde"
dest=/usr/share/sddm/themes/Retrograde

remove=no
for arg in "$@"; do
    case "$arg" in
        --remove) remove=yes ;;
        -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done

if [ "$(id -u)" -ne 0 ]; then
    echo "SDDM's themes are system-wide; run it as root:  sudo $0 $*" >&2
    exit 1
fi

if [ "$remove" = yes ]; then
    rm -rf -- "$dest"
    echo "  removed $dest"
    echo "If it was the login screen, pick another in System Settings first."
    exit 0
fi

if [ ! -f "$src/Main.qml" ]; then
    echo "theme/sddm/Retrograde is missing; build it first: python3 src/build.py sddm" >&2
    exit 1
fi

rm -rf -- "$dest"
cp -r -- "$src" "$dest"
chmod -R a+rX "$dest"
echo "  $dest"
echo
echo "Installed.  Pick Retrograde in System Settings > Colors & Themes >"
echo "Login Screen (SDDM).  To look at it first, without logging out:"
echo "  sddm-greeter-qt6 --test-mode --theme $dest"
