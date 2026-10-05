#!/usr/bin/env bash
# Start the pixel conkies (Orrery and dashboard) when you log in to KDE.
#
#   ./install-conky.sh           add them to autostart
#   ./install-conky.sh --start   and start them now
#   ./install-conky.sh --remove  take them out of autostart
set -eu

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
extras="$here/extras"
autostart="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
orrery="$extras/conky-orrery-pixel"
dashboard="$extras/conky-dashboard-pixel"

start=no remove=no
for arg in "$@"; do
    case "$arg" in
        --start) start=yes ;;
        --remove) remove=yes ;;
        -h|--help) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done

if [ "$remove" = yes ]; then
    rm -f -- "$autostart/conky-orrery-pixel.desktop" "$autostart/conky-dashboard-pixel.desktop"
    echo "Removed from autostart. They stop when you log out."
    exit 0
fi

if ! command -v conky >/dev/null; then
    echo "conky is not installed. Install it from your distribution (on Slackware" >&2
    echo "it is on SlackBuilds.org), then run this again." >&2
    exit 1
fi
if ! conky -v 2>/dev/null | grep -q 'Cairo'; then
    echo "warning: this conky looks built without Lua and Cairo; the conkies need both." >&2
fi

mkdir -p -- "$autostart"

cat > "$autostart/conky-orrery-pixel.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Conky Orrery (pixel)
Comment=Retrograde's pixel Orrery
Icon=utilities-system-monitor
Exec=conky --pause=5 --config="$orrery/start_conky_orrery"
Path=$orrery
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

# The dashboard waits 10 seconds so Plasma has its panel up first.
cat > "$autostart/conky-dashboard-pixel.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Conky Dashboard (pixel)
Comment=Retrograde's pixel dashboard
Icon=utilities-system-monitor
Exec="$dashboard/start_conky.sh" --delay 10
Path=$dashboard
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo "Added to autostart:"
echo "  $autostart/conky-orrery-pixel.desktop"
echo "  $autostart/conky-dashboard-pixel.desktop"

# Plasma's session restore brings back what was open at logout. The Orrery's
# window is plain "conky", which Plasma matches to conky's own menu entry and
# starts at login with no config: a third conky, the default one. Keep both
# out of the saved session; autostart starts them anyway.
if command -v kreadconfig6 >/dev/null && command -v kwriteconfig6 >/dev/null; then
    excluded="$(kreadconfig6 --file ksmserverrc --group General --key excludeApps)"
    list="$excluded"
    for app in conky conky-dashboard; do
        case ",$list," in *",$app,"*) ;; *) list="${list:+$list,}$app" ;; esac
    done
    if [ "$list" != "$excluded" ]; then
        kwriteconfig6 --file ksmserverrc --group General --key excludeApps "$list"
        echo "Left conky out of Plasma's saved session (excludeApps in ksmserverrc)."
    fi
fi

# Other conkies starting at login would land on top of these.
for f in "$autostart"/*.desktop; do
    case "$(basename -- "$f")" in conky-orrery-pixel.desktop|conky-dashboard-pixel.desktop) continue ;; esac
    if grep -q '^Exec=.*conky' "$f" 2>/dev/null; then
        echo "note: $f also starts a conky; disable it if it is the original Orrery or dashboard."
    fi
done

if [ ! -e "$dashboard/.owm_key" ] && [ ! -e "$HOME/git/conky-dashboard/.owm_key" ]; then
    echo "note: for the weather, put an OpenWeatherMap API key in $dashboard/.owm_key"
fi

# Is a conky running this config file, by whatever path it was started with?
running() {
    local want pid cfg
    want="$(readlink -f -- "$1")"
    for pid in $(pgrep -x conky 2>/dev/null || true); do
        cfg="$(tr '\0' '\n' < "/proc/$pid/cmdline" 2>/dev/null \
               | sed -n 's/^--config=//p; /^-c$/{n;p;}; /^--config$/{n;p;}' | head -n 1)"
        [ -n "$cfg" ] || continue
        case "$cfg" in /*) ;; *) cfg="$(readlink "/proc/$pid/cwd")/$cfg" ;; esac
        [ "$(readlink -f -- "$cfg")" = "$want" ] && return 0
    done
    return 1
}

if [ "$start" = yes ]; then
    if running "$orrery/start_conky_orrery"; then
        echo "The Orrery is already running."
    else
        (cd -- "$orrery" && setsid -f conky --config="$orrery/start_conky_orrery" </dev/null >/dev/null 2>&1)
        echo "Started the Orrery."
    fi
    # start_conky.sh replaces a dashboard already running from this folder.
    (cd -- "$dashboard" && setsid -f ./start_conky.sh </dev/null >/dev/null 2>&1)
    echo "Started the dashboard."
fi
