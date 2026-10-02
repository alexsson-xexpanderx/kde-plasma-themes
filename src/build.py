#!/usr/bin/env python3
"""Build every part of the theme into ../theme, laid out the way
~/.local/share expects, so installing is a copy.

    python3 src/build.py            everything
    python3 src/build.py wallpaper  one part (colors, aurorae, plasma,
                                    lookandfeel, cursors, icons, wallpaper,
                                    extras)
"""

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_aurorae      # noqa: E402
import build_colors       # noqa: E402
import build_cursors      # noqa: E402
import build_extras       # noqa: E402
import build_icons        # noqa: E402
import build_lookandfeel  # noqa: E402
import build_plasma       # noqa: E402
import build_wallpaper    # noqa: E402

PARTS = {
    "colors": build_colors.build,
    "aurorae": build_aurorae.build,
    "plasma": build_plasma.build,
    "wallpaper": build_wallpaper.build,
    "lookandfeel": build_lookandfeel.build,   # after plasma: both live under plasma/
    "cursors": build_cursors.build,
    "icons": build_icons.build,
    "extras": build_extras.build,
}


def main():
    out = HERE.parent / "theme"
    wanted = sys.argv[1:] or list(PARTS)
    for name in wanted:
        if name not in PARTS:
            sys.exit("unknown part %r; choose from %s" % (name, ", ".join(PARTS)))
        t = time.time()
        PARTS[name](out)
        print("%-12s %.1fs" % (name, time.time() - t))


if __name__ == "__main__":
    main()
