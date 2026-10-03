#!/bin/bash
#
# Opened in a terminal when the dashboard's Sbopkg row is clicked.
#
# The row means "an installed _SBo package is behind the local SlackBuilds
# tree", so what clears it is rebuilding those packages.  Syncing the tree
# (`sbopkg -r`) does not: the upgrade is already in the tree, and the row
# stays exactly where it was.  So this asks slackware_updates.bash which
# packages are behind and prepares the one command that rebuilds them.
#
# sbopkg needs root, but it is interactive and wants a real terminal, so this
# does not try to elevate on your behalf -- it hands you a shell with the
# command spelled out and already in the history.  It is a single `su -c`
# rather than `su` followed by sbopkg: after a plain `su` the root shell reads
# root's own history, so a second prepared entry was never there to recall.

here="$(dirname "$(readlink -f "$0")")"

# Names only, and only ones that look like package names, since they end up
# inside a quoted command line.
pending="$("$here/slackware_updates.bash" --sbo-pending 2>/dev/null)"
status=$?
names="$(awk '$1 ~ /^[A-Za-z0-9._+-]+$/ { print $1 }' <<<"$pending" | tr '\n' ' ')"
names="${names% }"

if (( status != 0 )); then
    printf '\n  \033[1mThe local SlackBuilds tree could not be read.\033[0m\n\n'
    printf '  sbopkg can check it itself:\n\n'
    cmd="su -c '/usr/sbin/sbopkg -c'"
elif [[ -n "$names" ]]; then
    printf '\n  \033[1mBehind the local SlackBuilds tree:\033[0m\n\n'
    printf '    %s\n' "${pending//$'\n'/$'\n'    }"
    printf '\n  Rebuild them (sbopkg needs root):\n\n'
    cmd="su -c '/usr/sbin/sbopkg -i \"$names\"'"
else
    printf '\n  \033[1mNothing is behind the local SlackBuilds tree.\033[0m\n\n'
    printf '  To look for newer SlackBuilds, sync it (sbopkg needs root):\n\n'
    cmd="su -c '/usr/sbin/sbopkg -r'"
fi

printf '    \033[38;5;204m%s\033[0m\n\n' "$cmd"
printf '  It is in the shell history -- press Up.\n\n'

# Fixed name per user, so repeated runs overwrite rather than accumulate.
hist="${TMPDIR:-/tmp}/.sbopkg-dashboard-history.$(id -u)"
printf '%s\n' "$cmd" > "$hist" 2>/dev/null || hist=""

if [ -n "$hist" ]; then
    HISTFILE="$hist" exec bash -i
fi
exec bash -i
