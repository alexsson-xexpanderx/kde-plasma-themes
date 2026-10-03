#!/usr/bin/env bash
#
# Report whether updates are waiting, one "Name: Status" line per checker.
#
# The status wording is a contract with lua/dashboard.lua, which keys off it:
#   "<Name>: Updates available"      -> red dot, counted as pending
#   "<Name>: No updates available"   -> green dot
#   "<Name>: Unknown"                -> amber dot; the check could not run
#
# A checker that cannot reach the network must report Unknown rather than
# guessing, otherwise a flaky connection shows up as a phantom update.

set -u

readonly PROGNAME="${0##*/}"

OUTPUT=""
SBO_TREE=""                    # --sbo-tree overrides tree discovery
LIST_SBO=0                     # --sbo-pending: print the list and exit
CHECK_SBOPKG=0
CHECK_KERNEL=0
CHECK_NVIDIA=0
CHECK_CHROME=0
CHECK_SKYPE=0

###############################
# Helpers
###############################

_die() {
    printf '%s: %s\n' "$PROGNAME" "$1" >&2
    exit 1
}

_need_value() {
    # $1 = flag, $2 = the value that followed it (may be unset)
    if [[ -z "${2:-}" || "${2:-}" == -* ]]; then
        _die "$1 requires an argument."
    fi
}

_report() {
    printf '%s: %s\n' "$1" "$2"
}

# One EXIT trap for both the lock and the temp file; setting two would mean
# the second silently replacing the first.
_cleanup() {
    [[ -n "${TMPFILE:-}" ]] && rm -f "$TMPFILE"
    [[ -n "${LOCKDIR:-}" ]] && rm -rf "$LOCKDIR"
    return 0
}

# The panel re-runs this on a timer, so a slow network check must not get a
# second copy stacked on top of it.  mkdir is atomic on every filesystem worth
# caring about; the pid inside lets a crashed run be cleaned up rather than
# wedging the lock forever.
_acquire_lock() {
    local dir="${TMPDIR:-/tmp}/slackware_updates-$(id -u).lock" owner

    if mkdir "$dir" 2>/dev/null; then
        LOCKDIR="$dir"; echo $$ >"$dir/pid"; return 0
    fi

    owner="$(cat "$dir/pid" 2>/dev/null)"
    if [[ -n "$owner" ]] && kill -0 "$owner" 2>/dev/null; then
        return 1                       # a live run holds it
    fi

    rm -rf "$dir" 2>/dev/null
    if mkdir "$dir" 2>/dev/null; then
        LOCKDIR="$dir"; echo $$ >"$dir/pid"; return 0
    fi
    return 1
}

_printhelp() {
    cat <<EOF
Report pending updates for Slackware and a few out-of-tree packages.

Usage: $PROGNAME [options]

  -o, --output <file>           Write to <file> atomically instead of stdout,
                                so a reader never sees a half-written file.
      --sbo-tree <dir>          Use this SlackBuilds tree instead of looking
                                for the one with the newest ChangeLog.txt
                                under sbopkg.conf's REPO_ROOT.
      --sbo-pending             Print the installed _SBo packages that are
                                behind the tree, one per line, and exit.
                                Exits 1 if the tree could not be read.

Optional checks (all off by default):
      --sbopkg                  An installed _SBo package is behind the local
                                SlackBuilds tree
  -k, --kernel                  A newer kernel exists on kernel.org
      --nvidia                  NVIDIA driver is behind
      --google-chrome           Google Chrome is behind
      --skype                   Skype is behind

  -h, --help                    This text.

slackpkg is always checked.  check-updates itself works as a normal user;
only clearing a stale /var/lock/slackpkg.* needs root, and that step is
skipped when not running as root.
EOF
}

###############################
# Checkers
###############################

_check_slackpkg() {
    local out

    # check-updates only reads, so it works as a normal user.  Clearing a
    # stale lock does need root, so skip it rather than failing noisily.
    if [[ $EUID -eq 0 ]]; then
        rm -f /var/lock/slackpkg.* 2>/dev/null
    fi

    if ! command -v /usr/sbin/slackpkg >/dev/null 2>&1; then
        _report Slackpkg "Unknown"
        return
    fi

    out="$(/usr/sbin/slackpkg check-updates 2>/dev/null)" || true

    if [[ -z "$out" ]]; then
        _report Slackpkg "Unknown"
    elif grep -q "AVAILABLE UPDATES" <<<"$out"; then
        _report Slackpkg "Updates available"
    else
        _report Slackpkg "No updates available"
    fi

    if [[ $EUID -eq 0 ]]; then
        rm -f /var/lock/slackpkg.* 2>/dev/null
    fi
}

# Sbopkg asks one question: is an installed _SBo package behind the local
# SlackBuilds tree?
#
# What it used to ask instead was whether the tree's ChangeLog.txt matched a
# remote one -- a different question, and wrong for this row in both
# directions.  A genuinely pending package upgrade read as "No updates
# available" whenever the tree happened to be in sync, which is the case most
# of the time.  And the remote it compared against was a hardcoded
# Ponce/slackbuilds *master*, while sbopkg's own definition for -current tracks
# the *current* branch (/etc/sbopkg/repos.d/60-SBo-current.repo), so the two
# lines never matched and the row sat on "Updates available" forever.
#
# Note the tree is compared as it stands: if you have not synced it, an upgrade
# that exists upstream but not locally is not reported, because it genuinely is
# not available to build yet.  `sbopkg -r` syncs it.
#
# sbopkg's own `sbopkg -c` cannot be reused here: it exits
# unless run by root (/usr/sbin/sbopkg:4639), and dir_init exits again when
# the repository is not writable.  This script runs as the desktop user, so
# the comparison below is a read-only reimplementation of sbopkg's
# check_for_updates -- same package list, same version sources, same numeric
# comparison -- minus the `sh`-eval of each SlackBuild's makepkg line.  On 293
# installed packages here that eval changes no verdict: the .info VERSION
# agrees with the installed version everywhere except the one genuine update.

# Echo an sbopkg.conf variable, honouring the ${NAME:-default} form the
# shipped file uses.  Sourcing the file would be shorter and would also run
# whatever else happens to be in it.
#
# Read it the way bash would: the *last* assignment wins, so an override
# appended below the shipped line is the one sbopkg uses, and quotes and a
# trailing comment are not part of the value.
_sbopkg_conf_var() {
    local line
    line="$(grep -E "^[[:space:]]*(export[[:space:]]+)?$1=" \
                 /etc/sbopkg/sbopkg.conf 2>/dev/null | tail -n1)"
    [[ -n "$line" ]] || return 0
    line="${line#*=}"
    line="${line%%[[:space:]]#*}"
    line="${line%"${line##*[![:space:]]}"}"
    if [[ "$line" == \"*\" || "$line" == \'*\' ]]; then
        line="${line:1:${#line}-2}"
    fi
    line="${line#"\${$1:-"}"
    line="${line%\}}"
    printf '%s\n' "$line"
}

# Print the SlackBuilds tree sbopkg is actually using, or nothing.
#
# Which repository is selected cannot be read: sbopkg saves it in root's
# ~/.sbopkg.conf (see its select_repository) and /root is not readable by the
# desktop user, while /etc/sbopkg/sbopkg.conf keeps its shipped SBo/15.0
# defaults whatever you really sync -- here that names an empty directory
# while the tree in use is SBo-git.  So look for trees rather than trust the
# config: every populated tree has a ChangeLog.txt at its root, and the one
# being synced is the one whose ChangeLog is newest.  Depth 1 is a git
# repository (sbopkg's REPO_DIR is $REPO_ROOT/$REPO_NAME), depth 2 an rsync
# one (checkout_rsync_branch appends the branch).
_sbo_tree() {
    local root candidate newest="" newest_time=0 t

    # A bad --sbo-tree fails this one check rather than the whole run, so the
    # other rows keep updating while the path is being fixed.
    if [[ -n "$SBO_TREE" ]]; then
        if [[ -d "$SBO_TREE" ]]; then
            printf '%s\n' "$SBO_TREE"
        else
            printf '%s: --sbo-tree %s is not a directory.\n' \
                "$PROGNAME" "$SBO_TREE" >&2
        fi
        return 0
    fi

    root="$(_sbopkg_conf_var REPO_ROOT)"
    root="${root:-/var/lib/sbopkg}"

    # Trailing slash so the globs match directories only: REPO_ROOT also holds
    # queues/, which is thousands of files and none of them a tree.
    for candidate in "$root"/*/ "$root"/*/*/; do
        candidate="${candidate%/}"
        [[ -f "$candidate/ChangeLog.txt" ]] || continue
        t="$(stat -c %Y "$candidate/ChangeLog.txt" 2>/dev/null)" || continue
        if (( t > newest_time )); then
            newest_time=$t
            newest="$candidate"
        fi
    done

    [[ -n "$newest" ]] && printf '%s\n' "$newest"
    return 0
}

# Print one line per installed _SBo package the tree has a newer version or
# build of.  $1 = tree.  Nothing is printed for a package the tree does not
# carry at all, which is the safe direction: 21 of the 293 installed here are
# locally built or long gone from SBo, and sbopkg stays quiet about those too
# unless DEBUG_UPDATES is raised.
#
# Returns non-zero when the tree could not really be compared against, since
# an empty list would otherwise read as "nothing to update": no package
# directories in it at all (a wrong or unreadable path), none of the installed
# packages in it (a wrong tree -- far likelier than every _SBo package having
# left SBo), or none of their .info files readable.
_sbo_pending() {
    local tree="$1" blacklist

    blacklist="$(_sbopkg_conf_var BLACKLISTFILE)"
    blacklist="${blacklist:-/etc/sbopkg/blacklist}"

    # One tagged stream into one awk, so an absent renames or blacklist file
    # does not shift which input is which.
    {
        # R: old=new.  An installed package may be called something else in
        # the tree by now; same source as sbopkg's get_new_name.
        # First match wins, as with sbopkg's `grep | head -n1`.
        grep -h '^[^#]' /etc/sbopkg/renames.d/*.renames 2>/dev/null |
            awk -F= 'NF == 2 && $1 != "" && $2 != "" { print "R", $1, $2 }'

        # K: blacklisted.  sbopkg drops a package whose filename contains one
        # of these lines; matched literally here, since the entries are names.
        grep -h '^[^#]' "$blacklist" 2>/dev/null |
            awk 'NF { print "K", $1 }'

        # D: package name -> its path inside the tree, "category/name".  Two
        # cheap directory reads beat globbing ~9800 package directories per
        # lookup.  The path is printed relative to the tree (%P) because awk
        # splits on whitespace, and an absolute %h under a directory with a
        # space in it would be cut at the space -- every lookup then misses
        # and the row reads all clear.  -name tests only an entry's own name,
        # so pruning dot-directories cannot catch the tree's own ancestors.
        # Depth-1 entries are the categories; awk keeps the ones with a slash.
        find "$tree" -mindepth 1 -maxdepth 2 -name '.*' -prune -o \
            -type d -printf 'D %f %P\n' 2>/dev/null

        # I: installed.  find rather than ls, because /var/log/packages is a
        # symlink and an $LS_OPTIONS carrying -F prints "packages@" instead of
        # following it -- which silently reports every package up to date.
        find -L /var/log/packages/ -maxdepth 1 -name '*_SBo' \
            -printf 'I %f\n' 2>/dev/null
    } | SBO_TREE_DIR="$tree" awk '
        # Digit groups of a version string, as sbopkg does it: comparing those
        # rather than the string keeps a 1.45 -> 1.47 bump apart from the
        # "-" -> "_" rewrites some SlackBuilds do to their VERSION.
        function numtok(s, out,   n, i, c, tok) {
            n = 0; tok = ""
            for (i = 1; i <= length(s); i++) {
                c = substr(s, i, 1)
                if (c ~ /[0-9]/)      tok = tok c
                else if (tok != "") { out[++n] = tok + 0; tok = "" }
            }
            if (tok != "") out[++n] = tok + 0
            return n
        }

        BEGIN { tree = ENVIRON["SBO_TREE_DIR"] }

        $1 == "R" { if (!($2 in rename)) rename[$2] = $3; next }
        $1 == "K" { black[++nblack] = $2; next }
        $1 == "D" { if ($3 ~ /\//) { dir[$2] = $3; ndir++ }; next }

        $1 == "I" {
            pkg = $2
            for (i = 1; i <= nblack; i++)
                if (index(pkg, black[i])) next

            # NAME-VERSION-ARCH-BUILD_SBo, split from the right because a
            # name may itself contain dashes.
            base = pkg
            sub(/_SBo$/, "", base)
            n = split(base, f, "-")
            if (n < 4) next
            # The build is the leading digits of the last field, as sbopkg
            # takes it: a tag in front of _SBo ("1alien_SBo") is not a
            # reason to skip the package.
            if (!match(f[n], /^[0-9]+/)) next
            ibld = substr(f[n], 1, RLENGTH)
            iver = f[n - 2]
            ninst++
            name = f[1]
            for (i = 2; i <= n - 3; i++) name = name "-" f[i]

            tname = (name in rename) ? rename[name] : name
            if (!(tname in dir) && tname != name) tname = name
            if (!(tname in dir)) next          # not carried by this tree
            matched++

            d = tree "/" dir[tname] "/" tname
            nver = ""
            while ((getline line < (d ".info")) > 0)
                if (line ~ /^VERSION=/) {
                    nver = line
                    sub(/^VERSION=/, "", nver)
                    gsub(/"/, "", nver)
                    break
                }
            close(d ".info")
            if (nver == "") next
            readok++

            nbld = ""
            while ((getline line < (d ".SlackBuild")) > 0)
                if (line ~ /^BUILD=/) {
                    nbld = line
                    gsub(/[^0-9]/, "", nbld)
                    break
                }
            close(d ".SlackBuild")
            if (nbld == "") nbld = 1

            delete A; delete B
            na = numtok(iver, A)
            nb = numtok(nver, B)
            while (na < nb) A[++na] = 0
            while (nb < na) B[++nb] = 0
            # The build number sorts as one more, least significant component.
            A[na + 1] = ibld + 0
            B[nb + 1] = nbld + 0

            for (i = 1; i <= na + 1; i++) {
                if (A[i] < B[i]) { print tname, iver "-" ibld, "->", nver "-" nbld; break }
                if (A[i] > B[i]) break          # installed is newer than the tree
            }
        }

        END {
            if (ndir == 0) exit 2
            if (ninst > 0 && matched == 0) exit 3
            if (matched > 0 && readok == 0) exit 4
        }
    '
}

_check_sbopkg() {
    local tree pending

    tree="$(_sbo_tree)"
    if [[ -z "$tree" || ! -d /var/log/packages ]]; then
        _report Sbopkg "Unknown"
        return
    fi

    if ! pending="$(_sbo_pending "$tree")"; then
        _report Sbopkg "Unknown"
    elif [[ -n "$pending" ]]; then
        _report Sbopkg "Updates available"
    else
        _report Sbopkg "No updates available"
    fi
}

_check_kernel() {
    local running series latest

    running="$(uname -r)"
    series="${running%%.*}"

    if ! command -v w3m >/dev/null 2>&1; then
        _report Linux "Unknown"
        return
    fi

    # The index lists ChangeLog-<version> files; the highest is the newest.
    latest="$(w3m -dump "https://cdn.kernel.org/pub/linux/kernel/v${series}.x/" 2>/dev/null \
        | grep -o "ChangeLog-${series}\.[0-9.]*" \
        | sed 's/ChangeLog-//' \
        | sort -V \
        | tail -n1)"

    if [[ -z "$latest" ]]; then
        _report Linux "Unknown"
    elif [[ "$running" == "$latest"* ]]; then
        _report Linux "No updates available"
    else
        _report Linux "Updates available"
    fi
}

_check_nvidia() {
    local installed web

    if ! command -v nvidia-smi >/dev/null 2>&1; then
        _report Nvidia "Unknown"
        return
    fi

    installed="$(nvidia-smi 2>/dev/null | grep -o 'Driver Version: [0-9.]*' | awk '{print $3}')"

    # NOTE: this reads NVIDIA's *Vulkan beta* page, which is normally ahead of
    # the stable driver, so a match is unlikely even when fully up to date.
    # Kept as-is to preserve the original behaviour; point it at whichever
    # channel you actually track.
    web="$(curl --silent --fail --max-time 20 "https://developer.nvidia.com/vulkan-driver" 2>/dev/null \
        | grep -o 'Linux driver version [0-9.]*' \
        | head -n1 \
        | awk '{print $4}')"

    if [[ -z "$installed" || -z "$web" ]]; then
        _report Nvidia "Unknown"
    elif [[ "$installed" == "$web" ]]; then
        _report Nvidia "No updates available"
    else
        _report Nvidia "Updates available"
    fi
}

# Both Chrome and Skype ship RPMs whose version is readable from the first few
# hundred bytes, which avoids downloading the whole package just to compare.
_rpm_lead_version() {
    wget --quiet --timeout=20 --tries=2 -O- "$1" 2>/dev/null \
        | head -c 96 \
        | strings \
        | grep -oE "$2"'-[0-9][0-9A-Za-z.]*' \
        | head -n1 \
        | sed "s/^$2-//"
}

_check_installed_version() {
    # $1 = display name, $2 = /var/log/packages prefix, $3 = upstream version
    local name="$1" prefix="$2" version="$3"

    if [[ -z "$version" ]]; then
        _report "$name" "Unknown"
    elif compgen -G "${prefix}${version}-*" >/dev/null; then
        _report "$name" "No updates available"
    else
        _report "$name" "Updates available"
    fi
}

_check_google_chrome() {
    local version
    version="$(_rpm_lead_version \
        "https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm" \
        "google-chrome-stable")"
    version="${version%%-*}"
    _check_installed_version "Google-Chrome" "/var/log/packages/google-chrome-" "$version"
}

_check_skype() {
    local version
    version="$(_rpm_lead_version "https://repo.skype.com/latest/skypeforlinux-64.rpm" \
        "skypeforlinux")"
    version="${version%%-*}"
    _check_installed_version "Skype" "/var/log/packages/skypeforlinux-" "$version"
}

###############################
# Arguments
###############################

while (( $# )); do
    case "$1" in
        -h|--help)       _printhelp; exit 0 ;;
        -o|--output)     _need_value "$1" "${2:-}"; OUTPUT="$2";  shift 2 ;;
        --sbo-tree)      _need_value "$1" "${2:-}"; SBO_TREE="$2"; shift 2 ;;
        --sbo-pending)   LIST_SBO=1; shift ;;
        # Gone: the Sbopkg check no longer depends on a release.  Still
        # accepted, and ignored, because a panel started before the change
        # keeps the old Lua in memory and passes it on every refresh -- and
        # dying on it would silently stop .updates.txt from updating.
        -r|--release)    _need_value "$1" "${2:-}"; shift 2 ;;
        -k|--kernel)     CHECK_KERNEL=1; shift ;;
        --nvidia)        CHECK_NVIDIA=1; shift ;;
        --sbopkg)        CHECK_SBOPKG=1; shift ;;
        --google-chrome) CHECK_CHROME=1; shift ;;
        --skype)         CHECK_SKYPE=1;  shift ;;
        --)              shift; break ;;
        # Without these two arms an unrecognised word matches nothing, never
        # shifts, and the loop spins forever.
        -*)              _die "unknown option '$1' (try --help)." ;;
        *)               _die "unexpected argument '$1' (try --help)." ;;
    esac
done

if (( LIST_SBO )); then
    tree="$(_sbo_tree)"
    [[ -n "$tree" ]] || _die "no SlackBuilds tree found (try --sbo-tree)."
    [[ -d /var/log/packages ]] || _die "/var/log/packages is missing."
    _sbo_pending "$tree" || _die "could not compare against the tree at $tree."
    exit 0
fi

###############################
# Main
###############################

run_all() {
    _check_slackpkg
    (( CHECK_SBOPKG )) && _check_sbopkg
    (( CHECK_KERNEL )) && _check_kernel
    (( CHECK_NVIDIA )) && _check_nvidia
    (( CHECK_CHROME )) && _check_google_chrome
    (( CHECK_SKYPE  )) && _check_skype
    return 0
}

trap _cleanup EXIT INT TERM

if [[ -n "$OUTPUT" ]]; then
    # Only the automated path locks; a manual run to stdout should always work
    # even while the panel's own refresh is in flight.
    if ! _acquire_lock; then
        exit 0                         # a run is already under way: not an error
    fi

    # Write somewhere else and rename, so the panel never reads a file that is
    # half-written or empty because the checks are still running.
    TMPFILE="$(mktemp "${OUTPUT}.XXXXXX")" || _die "cannot create a temporary file."
    run_all >"$TMPFILE"
    mv -f "$TMPFILE" "$OUTPUT"
    TMPFILE=""
else
    run_all
fi
