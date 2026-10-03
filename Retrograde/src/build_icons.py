#!/usr/bin/env python3
"""Icon theme: filled pixel-art icons in the wallpaper's colours.

Every icon is solid -- outlined, filled, lit along its top and left and shaded
along its bottom and right, with the theme's hard shadow -- like a sprite in an
old game -- except the tray's, which are one colour.  Four kinds go in:

* Drawn by hand (icons_art.py): folders, file pages, the trash, the
  launcher's sun.
* Designed from shapes (icons_apps.py, with the kit in icons_draw.py): the
  apps, devices, launcher categories, dialogs and power buttons people see
  most, each under every name it is asked for by.
* The system tray's (icons_tray.py): volume, networks, battery, Bluetooth,
  notifications and the rest, in every state, as one-colour pixel glyphs on an
  11-cell grid that Plasma colours from the scheme, as it does Breeze's.
* Converted, for everything else: Breeze's coloured icons and the apps'
  own, which are solid shapes too, averaged onto the grid, each cell moved to
  the nearest shade of the nearest wallpaper ramp, outlined in that ramp's
  darkest shade and given the shadow.  Thin-line icon sets are not used:
  their strokes fall apart on a grid this coarse.

Each sprite is drawn twice: 24 cells across for 24 px and up, 16 across for 16
and 22 px.  They are written as SVG -- one path per colour, every cell a
square -- so they stay crisp at fractional display scales, over a solid
underlay so that they do not go see-through along the seams between colours
there either (see svgkit.Group.grid).

Toolbar actions are left to Breeze Dark, which the theme inherits: they are
monochrome and follow the colour scheme, as every toolbar expects.  The
exceptions are the power and session actions -- shut down, restart, lock, log
out -- which the launcher and the logout screen show large, and the few the
tray and panel use (notifications, brightness, im-user, the colour
picker's pipette), which are its glyphs.

One thing makes that harder than leaving them out.  KIconLoader looks a name
up in this theme first under its full name and then under ever shorter ones
(kdenlive-add-clip, then kdenlive), and for an application-, audio-, image-,
inode-, text- or video- name under that kind's generic file icon, before it
tries Breeze Dark at all.  So a name of ours can hide Breeze's: Kdenlive's
toolbar would show Kdenlive's logo forty times over, and every app's Quit
(application-exit) a blank page.  So every Breeze icon a name of ours would
hide is shipped here as well, unchanged, under breeze/.

The build also converts the icons of the apps installed on the machine it
runs on that have no icon here otherwise, so the theme in the repository
covers this machine's apps too.

    python3 src/build_icons.py               build theme/icons/Retrograde
    python3 src/build_icons.py --local DIR   add the icons of apps installed
                                             since to an installed copy in DIR
"""

import colorsys
import glob
import io
import math
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import icons_apps     # noqa: E402
import icons_art as A  # noqa: E402
import icons_tray      # noqa: E402
import palette as P    # noqa: E402

BREEZE = Path("/usr/share/icons/breeze")
BREEZE_DARK = Path("/usr/share/icons/breeze-dark")
MIME = Path("/usr/share/mime")

# Cells across, and how many of them an icon's content may fill: the rest is
# margin and the shadow's one cell.
GRIDS = {24: 21, 16: 14}
# How much of a cell an icon must cover for the cell to be drawn.  Lower on
# the small grid, where thin parts are barely a cell wide.
THRESHOLD = {24: 0.5, 16: 0.42}
DIRS = {24: "scalable", 16: "16"}

CONTEXTS = {
    "apps": "Applications", "preferences": "Applications", "applets": "Applications",
    "categories": "Categories", "devices": "Devices", "status": "Status",
    "places": "Places", "mimetypes": "MimeTypes",
}

RAMPS = {
    "violet": P.RAMP_VIOLET, "rose": P.RAMP_ROSE, "red": P.RAMP_RED, "orange": P.RAMP_ORANGE,
    "gold": P.RAMP_GOLD, "brown": P.RAMP_BROWN, "sky": P.RAMP_SKY, "grey": P.RAMP_GREY,
    "mint": P.RAMP_MINT,
}


# ---------------------------------------------------------------- SVG

def merge(cells):
    """Boxes (x0, y0, x1, y1, key) covering equal cells: runs along each row,
    grown down the rows while they repeat."""
    n = len(cells)
    out, open_runs = [], {}
    for y in range(n):
        row_runs = {}
        x = 0
        while x < n:
            k = cells[y][x]
            if k is None:
                x += 1
                continue
            e = x
            while e < n and cells[y][e] == k:
                e += 1
            box = open_runs.get((x, e, k))
            if box is None:
                box = [x, y, e, y + 1, k]
                out.append(box)
            else:
                box[3] = y + 1
            row_runs[(x, e, k)] = box
            x = e
        open_runs = row_runs
    return out


def path_data(boxes):
    return "".join("M%d %dh%dv%dh-%dz" % (x0, y0, x1 - x0, y1 - y0, x1 - x0)
                   for x0, y0, x1, y1, _ in boxes)


def svg(grid):
    """One path per colour.  First, under them all, the icon's solid cells as
    one path in its commonest colour: a single path has no seams of its own,
    so at a fractional scale it fills the pixels where two colours meet, which
    neither covers fully, and which would otherwise be partly transparent."""
    n = len(grid)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
           % (n, n, n, n)]
    counts = Counter(c[0] for row in grid for c in row if c and c[1] >= 1)
    if counts:
        solid = [[1 if c and c[1] >= 1 else None for c in row] for row in grid]
        out.append('<path fill="%s" d="%s"/>' % (counts.most_common(1)[0][0], path_data(merge(solid))))
    by_cell = defaultdict(list)
    for box in merge(grid):
        by_cell[box[4]].append(box)
    for (colour, alpha), boxes in by_cell.items():
        opacity = "" if alpha >= 1 else ' fill-opacity="%g"' % alpha
        out.append('<path fill="%s"%s d="%s"/>' % (colour, opacity, path_data(boxes)))
    out.append("</svg>\n")
    return "\n".join(out)


# ---------------------------------------------------------------- converting

def load(path, px=768):
    """An icon file as float RGBA, at least px across."""
    path = Path(path)
    if path.suffix in (".svg", ".svgz"):
        png = subprocess.run(["rsvg-convert", "-a", "-w", str(px), "-h", str(px), str(path)],
                             check=True, capture_output=True).stdout
        img = Image.open(io.BytesIO(png))
    else:
        img = Image.open(path)
        img.load()
    img = img.convert("RGBA")
    if img.width < px // 2:
        f = max(1, px // max(img.width, img.height))
        img = img.resize((img.width * f, img.height * f), Image.NEAREST)
    return np.asarray(img, dtype=np.float64) / 255


# Colours a source icon is reduced to before it is laid on the grid.
COLOURS = 16
SUPERSAMPLE = 8


def to_cells(arr, n, room):
    """Lay an icon on an n-cell grid: how much of each cell it covers, and the
    one colour that covers most of the cell.

    The icon is first reduced to its few real colours, at high resolution
    where they are still clean.  Averaging each cell's colour instead invents
    in-between ones -- half a dark stroke over green comes out a muddy third
    colour -- and a gradient that straddles two of the theme's ramps comes out
    speckled with both.  Here a cell can only be one of the logo's own
    colours.  The content is scaled to fit `room` cells and centred together
    with the cell of shadow it will get.  Returns (cover, counts, colours):
    how many of each cell's pixels are each colour."""
    a = arr[..., 3]
    ys, xs = np.nonzero(a > 0.02)
    if len(ys) == 0:
        return None, None, None
    crop = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    bh, bw = crop.shape[:2]
    s = room / max(bw, bh)
    wc, hc = max(1, round(bw * s)), max(1, round(bh * s))
    S = SUPERSAMPLE

    def resample(channel, w, h):
        return np.asarray(Image.fromarray(channel.astype(np.float32), "F").resize((w, h), Image.BOX))
    alpha = resample(crop[..., 3], wc * S, hc * S)
    rgb = np.stack([resample(crop[..., c] * crop[..., 3], wc * S, hc * S) for c in range(3)], -1)
    rgb = np.clip(rgb / np.maximum(alpha[..., None], 1e-6), 0, 1)

    # The opaque pixels' colours, reduced to a few.
    opaque = alpha > 0.5
    labels = np.full(alpha.shape, -1)
    pts = (rgb[opaque] * 255).astype(np.uint8)
    if len(pts) == 0:
        return None, None, None
    q = Image.fromarray(pts.reshape(-1, 1, 3), "RGB").quantize(COLOURS, Image.Quantize.MEDIANCUT)
    labels[opaque] = np.asarray(q).reshape(-1)
    colours = np.array(q.getpalette()[:3 * COLOURS]).reshape(-1, 3) / 255

    C = np.zeros((n, n))
    counts = np.zeros((n, n, len(colours)))
    ox, oy = (n - wc - 1) // 2, (n - hc - 1) // 2
    for y in range(hc):
        for x in range(wc):
            block = labels[y * S:(y + 1) * S, x * S:(x + 1) * S]
            C[oy + y, ox + x] = alpha[y * S:(y + 1) * S, x * S:(x + 1) * S].mean()
            mine = block[block >= 0]
            if len(mine):
                counts[oy + y, ox + x] = np.bincount(mine, minlength=len(colours))
    return C, counts, colours


def family_of_hue(d):
    if 210 <= d < 290:
        return "violet"
    if 290 <= d < 340:
        return "rose"
    if d >= 340 or d < 18:
        return "red"
    if d < 42:
        return "orange"
    if d < 75:
        return "gold"
    if d < 165:
        return "mint"
    return "sky"


def chromatic(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return s >= 0.22 and v >= 0.12


def family(r, g, b):
    if not chromatic(r, g, b):
        return "grey"
    return family_of_hue(colorsys.rgb_to_hsv(r, g, b)[0] * 360)


def families(colours, weights):
    """The ramp for each of a logo's colours, decided for the logo as a whole.
    Colours within 25 degrees of hue of each other are taken as one gradient
    and given the ramp of their weighted mean hue: deciding each on its own
    splits a gradient that straddles a boundary between two ramps (Zoom's blue
    came out half violet, half sky blue)."""
    hues = [colorsys.rgb_to_hsv(*c)[0] * 360 for c in colours]
    live = [i for i, c in enumerate(colours) if chromatic(*c) and weights[i] > 0]

    def near(i, j):
        d = abs(hues[i] - hues[j]) % 360
        return min(d, 360 - d) < 25

    # Every member of a group is near every other, so a wide gradient (Firefox's
    # red to yellow) stays two groups rather than chaining into one.
    groups = []
    for i in sorted(live, key=lambda i: -weights[i]):
        for g in groups:
            if all(near(i, j) for j in g):
                g.append(i)
                break
        else:
            groups.append([i])
    out = {i: "grey" for i in range(len(colours))}
    for idx in groups:
        x = sum(weights[i] * math.cos(math.radians(hues[i])) for i in idx)
        y = sum(weights[i] * math.sin(math.radians(hues[i])) for i in idx)
        fam = family_of_hue(math.degrees(math.atan2(y, x)) % 360)
        for i in idx:
            out[i] = fam
    return out


def shade_of(rgb):
    """The shade one of a logo's colours takes in its ramp, by how light it
    really is (luminance, not HSV value, which calls a dark brown "bright"
    and loses a smiley's eyes on its face): the darkest for near black, darker
    ones for dark, the lightest only for near white (or the logo turns
    pastel), and the middle one for the rest, as the hand-made icons are."""
    r, g, b = rgb
    lum = P.luminance(P.hexc(r * 255, g * 255, b * 255))
    v = max(r, g, b)
    sat = (v - min(r, g, b)) / v if v else 0
    if lum < 0.05:
        return 0
    if lum < 0.13:
        return 1
    if lum < 0.3:
        return 2
    return 4 if (lum > 0.75 and sat < 0.25) else 3


def despeckle(colour, cells):
    """A cell with no neighbour of its own colour, even diagonally, takes the
    colour most of its neighbours have: one stray cell reads as a mistake.
    Unless it stands out from them at 3:1 or more -- then it is a detail, a
    smiley's eye, and stays."""
    def hexed(key):
        return RAMPS[key[0]][key[1]]
    for _ in range(2):
        for x, y in sorted(cells):
            mine = colour[(x, y)]
            around = [colour.get((x + dx, y + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      if (dx, dy) != (0, 0)]
            if mine in around:
                continue
            side = [colour[p] for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if p in colour]
            if side:
                common, count = Counter(side).most_common(1)[0]
                if count >= 2 and P.contrast(hexed(mine), hexed(common)) < 3:
                    colour[(x, y)] = common


def recolour(C, counts, colours, n):
    """A converted icon in the theme's sprite style: each covered cell in the
    theme colour most of it is -- counted after the logo's colours are moved
    to the theme's, so a face's several yellows add up against its eye --
    flat, stray cells absorbed, and the cells along the icon's edge in their
    ramp's darkest shade, which outlines it.  Then the hard shadow."""
    cells = {(x, y) for y in range(n) for x in range(n)
             if C[y, x] >= THRESHOLD[n] and counts[y, x].sum() > 0}
    weights = counts.sum(axis=(0, 1))
    fams = families(colours, list(weights))
    keys = [(fams[i], shade_of(c)) for i, c in enumerate(colours)]
    # A gradient's gentle steps come out as one shade, the shade of its
    # commonest colour: two shades a step apart read as a seam (Telegram's
    # blue grew a lighter cap).  A real detail differs far more than 1.6:1.
    hexes = [P.hexc(*(c * 255)) for c in colours]
    for i in sorted(range(len(colours)), key=lambda i: -weights[i]):
        for j in range(len(colours)):
            if (j != i and weights[j] and keys[j][0] == keys[i][0] and weights[j] < weights[i]
                    and P.contrast(hexes[i], hexes[j]) < 1.6):
                keys[j] = keys[i]
    colour = {}
    for x, y in cells:
        votes = Counter()
        for i, k in enumerate(counts[y, x]):
            if k:
                votes[keys[i]] += k
        colour[(x, y)] = votes.most_common(1)[0][0]
    despeckle(colour, cells)
    edge = A.outline_cells(cells)
    grid = A.blank(n)
    for (x, y), (fam, shade) in colour.items():
        grid[y][x] = (RAMPS[fam][0 if (x, y) in edge else shade], 1.0)
    return A.add_shadow(grid)


# A conversion is kept only if, inside its outline, it has at most this many
# islands of one or two cells: more, and it reads as noise rather than as the
# logo (the user's word was artifacts).  Clean logos have 0 to 5.
MAX_ISLANDS = {24: 5, 16: 4}


def islands(grid):
    """Islands of one or two cells of a colour inside the icon's outline."""
    n = len(grid)
    solid = {(x, y) for y in range(n) for x in range(n) if grid[y][x] and grid[y][x][1] >= 1}
    inner = solid - A.outline_cells(solid)
    seen, count = set(), 0
    for start in inner:
        if start in seen:
            continue
        colour, stack, size = grid[start[1]][start[0]], [start], 0
        seen.add(start)
        while stack:
            x, y = stack.pop()
            size += 1
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in inner and q not in seen and grid[q[1]][q[0]] == colour:
                    seen.add(q)
                    stack.append(q)
        count += size <= 2
    return count


def smooth(grid):
    """Each cell inside the outline takes the colour most of its 3 x 3
    neighbourhood has, which rounds off ragged edges and drops specks."""
    n = len(grid)
    solid = {(x, y) for y in range(n) for x in range(n) if grid[y][x] and grid[y][x][1] >= 1}
    inner = solid - A.outline_cells(solid)
    out = [row[:] for row in grid]
    for x, y in inner:
        votes = Counter(grid[y + dy][x + dx] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                        if (x + dx, y + dy) in inner)
        best, count = votes.most_common(1)[0]
        if count >= 5:
            out[y][x] = best
    return out


def main_ramp(grid):
    """The ramp most of an icon is in, greys aside."""
    ramps = {c: name for name, ramp in RAMPS.items() for c in ramp if name != "grey"}
    found = Counter(ramps[c[0]] for row in grid for c in row if c and c[0] in ramps)
    return found.most_common(1)[0][0] if found else None


def convert(path):
    """Both grids of one source icon, cleaned up: (path, {"grids": ...,
    "ramp": ...}).  "grids" is None if the icon is still noisy after smoothing
    (or cannot be read); "ramp" is its main colour, for a letter tile."""
    try:
        arr = load(path)
    except (subprocess.CalledProcessError, OSError, ValueError):
        return path, {"grids": None, "ramp": None}
    grids = {}
    for n, room in GRIDS.items():
        C, counts, colours = to_cells(arr, n, room)
        if C is None:
            return path, {"grids": None, "ramp": None}
        grids[n] = recolour(C, counts, colours, n)
    ramp = main_ramp(grids[24])
    for n in grids:
        if islands(grids[n]) > MAX_ISLANDS[n]:
            grids[n] = smooth(grids[n])
            if islands(grids[n]) > MAX_ISLANDS[n]:
                return path, {"grids": None, "ramp": ramp}
    return path, {"grids": grids, "ramp": ramp}


# ---------------------------------------------------------------- sources

def symbolic(name):
    return name.endswith("-symbolic") or name.endswith("-symbolic-rtl")


# Toolbar actions this theme draws after all (see the top of the file).
KEEP_ACTION = re.compile(r"^(system-(shutdown|reboot|lock-screen|log-out|suspend|suspend-hibernate"
                         r"|hibernate|switch-user)|notifications?(-|$)|notification-)")


def breeze_actions():
    """Breeze's toolbar action names, less the ones drawn here anyway."""
    names = set()
    for root in (BREEZE, BREEZE_DARK):
        names |= {f.stem for f in (root / "actions").glob("*/*.svg")}
    return {n for n in names if not KEEP_ACTION.match(n)}


def breeze_icons():
    """{context: {name: file}} -- Breeze's coloured icons, each at the largest
    size it comes in."""
    out = defaultdict(dict)
    for ctx in ("apps", "preferences", "devices", "status", "categories", "applets",
                "places", "mimetypes"):
        best = {}
        root = BREEZE / ctx
        if not root.is_dir():
            continue
        for d in root.iterdir():
            if d.is_symlink() or not d.name.isdigit():
                continue
            size = int(d.name)
            for f in d.iterdir():
                if f.suffix == ".svg" and not symbolic(f.stem) and f.exists():
                    if size > best.get(f.stem, (0, None))[0]:
                        best[f.stem] = (size, f)
        for name, (size, f) in best.items():
            # Small devices and status icons are monochrome; status icons
            # below 64 px are the tray's (battery levels and the like).
            if (ctx == "devices" and size < 32) or (ctx == "status" and size < 64):
                continue
            out[ctx][name] = f
    return out


# ---------------------------------------------------------------- places

FOLDER_SYMBOLS = {
    "documents": ["folder-documents", "folder-notes", "folder-text", "folder-txt", "folder-log"],
    "download": ["folder-download", "folder-downloads"],
    "music": ["folder-music", "folder-sound", "folder-podcast", "library-music"],
    "pictures": ["folder-pictures", "folder-picture", "folder-image", "folder-images",
                 "folder-image-people", "folder-photos"],
    "videos": ["folder-videos", "folder-video", "folder-movies"],
    "home": ["user-home", "folder-home", "gnome-fs-home", "folder_home"],
    "desktop": ["user-desktop", "folder-desktop", "desktop", "cs-desktop", "gnome-fs-desktop"],
    "templates": ["folder-templates"],
    "people": ["folder-publicshare", "folder-public"],
    "globe": ["folder-remote", "folder-network", "folder-language", "folder-html", "folder_html",
              "gnome-fs-network"],
    "cloud": ["folder-cloud", "folder-gdrive", "folder-dropbox", "folder-nextcloud",
              "folder-owncloud", "folder-onedrive"],
    "code": ["folder-development", "folder-script", "folder-java", "folder-build"],
    "games": ["folder-games", "folder-godot"],
    "recent": ["folder-recent"],
    "star": ["folder-favorites", "favorites", "folder-bookmark", "folder-important"],
    "locked": ["folder-locked", "folder-encrypted"],
    "unlocked": ["folder-unlocked", "folder-decrypted"],
    "mail": ["folder-mail"],
    "git": ["folder-git"],
    "book": ["folder-book", "folder-library", "folder-comic"],
    "temp": ["folder-temp"],
    "trash": ["folder-trash"],
    "print": ["folder-print"],
    "chart": ["folder-chart", "folder-presentation"],
    "grid": ["folder-table", "folder-calculate"],
    "pen": ["folder-drawing", "folder-paint", "folder-design", "folder-sign"],
    "box": ["folder-tar", "folder-snap", "folder-flatpak", "folder-appimage", "folder-rpm",
            "folder-deb", "folder-extension", "folder-docker"],
    "gear": ["folder-root"],
    "database": ["folder-database"],
    "window": ["folder-windows"],
    "important": ["folder-crash"],
}
PLAIN_FOLDERS = ["folder", "inode-directory", "gtk-directory", "stock_folder", "folder-activities",
                 "gnome-folder", "gnome-fs-directory", "folder-android", "folder-blender", "folder-mac"]
SUN = ["start-here", "start-here-kde", "start-here-kde-plasma", "distributor-logo"]
TRASH = {"user-trash": False, "user-trash-full": True, "trash-empty": False, "trash-full": True,
         "gnome-fs-trash-empty": False, "gnome-fs-trash-full": True, "xfce-trash_empty": False,
         "xfce-trash_full": True}


# ---------------------------------------------------------------- file types

SPECIFIC = {
    "application-pdf": ("red", "pdf"), "application-x-pdf": ("red", "pdf"),
    "text-markdown": ("violet", "markdown"), "text-x-markdown": ("violet", "markdown"),
    "application-json": ("gold", "braces"), "text-x-json": ("gold", "braces"),
    "text-html": ("sky", "globe"), "application-xhtml+xml": ("sky", "globe"),
    "application-epub+zip": ("violet", "book"), "application-x-desktop": ("violet", "window"),
    "application-x-bittorrent": ("sky", "download"), "image-svg+xml": ("rose", "pen"),
    "image-svg+xml-compressed": ("rose", "pen"), "application-x-trash": ("grey", "trash"),
    "application-octet-stream": ("grey", "question"), "unknown": ("grey", "question"),
    "text-plain": ("grey", "text"), "text-x-log": ("grey", "text"),
    "text-csv": ("sky", "grid"), "text-x-csv": ("sky", "grid"),
    "text-calendar": ("gold", "calendar"), "text-vcard": ("violet", "person"),
    "text-x-vcard": ("violet", "person"), "text-directory": ("violet", "person"),
}
PATTERNS = [
    (r"presentation|powerpoint|impress|keynote|slide", ("orange", "chart")),
    (r"spreadsheet|excel|[-.]calc|numbers|lotus-1-2-3|gnumeric", ("sky", "grid")),
    (r"epub|ebook|mobipocket|fictionbook|djvu|comicbook|cbz|cbr", ("violet", "book")),
    (r"debian|redhat|rpm|flatpak|appimage|snap|msi|msix|android.package|x-apk|apple-diskimage"
     r"|arch.?package|x-xz-compressed-tar.*pkg", ("orange", "box")),
    (r"iso9660|cd-image|disk-image|raw-disk|x-cue|qemu|vhd|vmdk|vdi", ("brown", "disc")),
    (r"zip|tar|rar|7z|compress|gzip|bzip|-xz|lzma|lzip|lzop|zstd|archive|cpio|arj|lha|lzh"
     r"|ace|cab|squashfs|stuffit|java-archive", ("brown", "zip")),
    (r"x509|pkcs|pgp|pem|-key|certificate|gpg|ssh|keyring|keystore|keepass", ("gold", "key")),
    (r"wordprocessing|msword|opendocument.text|rtf|abiword|richtext|wordperfect|kword"
     r"|document$", ("violet", "documents")),
    (r"sqlite|sql|database|x-dbf|msaccess|mdb", ("sky", "database")),
    (r"font|ttf|otf|woff|x-bdf|x-pcf", ("violet", "font")),
    (r"executable|sharedlib|x-object|x-elf|dosexec|ms-dos|msdownload|x-core|x-shellscript-exec",
     ("grey", "gear")),
    (r"shellscript|x-sh$|x-csh|x-zsh|x-fish|x-bat|powershell|x-makefile|x-cmake", ("sky", "terminal")),
    (r"javascript|ecmascript|typescript", ("gold", "braces")),
    (r"html|xhtml|-web|x-mswinurl|x-url", ("sky", "globe")),
    (r"calendar|ical|vcalendar", ("gold", "calendar")),
    (r"vcard|contact|addressbook", ("violet", "person")),
    (r"illustrator|x-eps|xfig|drawing|inkscape|coreldraw|graphics|x-sk|x-kontour", ("rose", "pen")),
    (r"message|rfc822|mbox|x-mail|email", ("violet", "mail")),
]
GENERIC = {
    "text-x-generic": ("grey", "text"), "text-x-generic-template": ("grey", "text"),
    "text-x-script": ("sky", "code"), "image-x-generic": ("gold", "pictures"),
    "audio-x-generic": ("rose", "music"), "video-x-generic": ("red", "videos"),
    "package-x-generic": ("brown", "zip"), "x-office-document": ("violet", "documents"),
    "x-office-document-template": ("violet", "documents"),
    "x-office-spreadsheet": ("sky", "grid"), "x-office-spreadsheet-template": ("sky", "grid"),
    "x-office-presentation": ("orange", "chart"), "x-office-presentation-template": ("orange", "chart"),
    "x-office-drawing": ("rose", "pen"), "x-office-drawing-template": ("rose", "pen"),
    "x-office-address-book": ("violet", "person"), "x-office-calendar": ("gold", "calendar"),
    "font-x-generic": ("violet", "font"), "application-x-executable": ("grey", "gear"),
    "application-x-generic": ("grey", None), "inode-x-generic": ("grey", None),
}


def generic_icons():
    """{icon name: generic icon name}, from the shared MIME database."""
    out = {}
    f = MIME / "generic-icons"
    if f.exists():
        for line in f.read_text().splitlines():
            if ":" in line:
                mime, icon = line.split(":", 1)
                out[mime.replace("/", "-")] = icon
    return out


MIME_NAME = re.compile(r"^(application|audio|chemical|font|image|inode|message|model|multipart|text"
                       r"|video|x-office|x-content|x-scheme-handler|package|unknown)-")


def mime_names(breeze, generic):
    # Breeze files a few app icons (cantor...) under mimetypes too; only real
    # file-type names become pages, or an app comes out as a blank one.
    names = {n for n in breeze.get("mimetypes", {}) if MIME_NAME.match(n) or n in GENERIC}
    names |= set(GENERIC)
    names |= set(SPECIFIC) | set(generic) | {g for g in generic.values() if MIME_NAME.match(g) or g in GENERIC}
    f = MIME / "types"
    if f.exists():
        names |= {t.replace("/", "-") for t in f.read_text().split()}
    f = MIME / "aliases"          # old names apps still ask for, e.g. x-iso9660-image
    if f.exists():
        names |= {t.replace("/", "-") for t in f.read_text().split()}
    return {n for n in names if not symbolic(n)}


def file_type(name, generic):
    """(ramp, symbol) for a file type's icon name; symbol may be None."""
    if name in SPECIFIC:
        return SPECIFIC[name]
    if name in GENERIC:
        return GENERIC[name]
    for pattern, kind in PATTERNS:
        if re.search(pattern, name):
            return kind
    if generic.get(name) in GENERIC:
        return GENERIC[generic[name]]
    for prefix, kind in (("text-x-", ("sky", "code")), ("text-", ("grey", "text")),
                         ("image-", ("gold", "pictures")), ("audio-", ("rose", "music")),
                         ("video-", ("red", "videos")), ("font-", ("violet", "font")),
                         ("model-", ("brown", "box"))):
        if name.startswith(prefix):
            return kind
    return ("grey", None)


# ---------------------------------------------------------------- writing

class Theme:
    def __init__(self, root, skip=()):
        self.root = Path(root)
        self.by_key = {}        # (context, key) -> canonical name, for symlinks
        self.names = set()
        self.skip = set(skip)   # names never drawn here
        self.drawn = set()      # names drawn by hand rather than converted
        self.breeze_dirs = {}   # breeze/<ctx>/<size> -> its index entry

    def put(self, ctx, name, grids, key=None):
        """Write both grids of an icon, or a symlink to an identical one."""
        if name in self.names or name in self.skip:
            return
        self.names.add(name)
        canon = self.by_key.get((ctx, key)) if key is not None else None
        for n, sub in DIRS.items():
            path = self.root / ctx / sub / (name + ".svg")
            path.parent.mkdir(parents=True, exist_ok=True)
            if canon:
                path.symlink_to(canon + ".svg")
            else:
                path.write_text(svg(grids[n]))
        if key is not None and not canon:
            self.by_key[(ctx, key)] = name

    def put_glyph(self, name, text):
        """A tray glyph (icons_tray): one drawing for every size, in status/,
        drawn even where Breeze files the name under actions."""
        if name in self.names:
            return
        self.names.add(name)
        canon = self.by_key.get(("glyph", text))
        for sub in DIRS.values():
            path = self.root / "status" / sub / (name + ".svg")
            path.parent.mkdir(parents=True, exist_ok=True)
            if canon:
                path.symlink_to(canon + ".svg")
            else:
                path.write_text(text)
        if not canon:
            self.by_key[("glyph", text)] = name

    def index(self):
        ctxs = sorted({p.parent.parent.name for p in self.root.glob("*/*/*.svg")})
        dirs = ["%s/%s" % (c, s) for c in ctxs for s in ("16", "scalable")]
        lines = [
            "[Icon Theme]",
            "Name=%s" % P.NAME,
            "Comment=Pixel icons in the colours of the %s sunset" % P.NAME,
            "Inherits=breeze-dark,hicolor",
            "Example=folder",
            "FollowsColorScheme=true",
            "DisplayDepth=32",
            "Directories=%s" % ",".join(dirs),
            "",
        ]
        for d in dirs:
            ctx, sub = d.split("/")
            small = sub == "16"
            lines += [
                "[%s]" % d,
                "Size=%d" % (16 if small else 48),
                "Context=%s" % CONTEXTS[ctx],
                "Type=Scalable",
                "MinSize=%d" % (8 if small else 23),
                "MaxSize=%d" % (22 if small else 512),
                "",
            ]
        for d, entry in sorted(self.breeze_dirs.items()):
            lines += ["[%s]" % d] + entry + [""]
        if self.breeze_dirs:
            i = lines.index("Directories=%s" % ",".join(dirs))
            lines[i] += "," + ",".join(sorted(self.breeze_dirs))
        (self.root / "index.theme").write_text("\n".join(lines))


def breeze_index():
    """{"<ctx>/<size>": [its index.theme lines]} from Breeze Dark."""
    out, cur = {}, None
    for line in (BREEZE_DARK / "index.theme").read_text().splitlines():
        m = re.match(r"^\[(.+)\]$", line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur and "=" in line and line.split("=")[0] in (
                "Size", "Context", "Type", "MinSize", "MaxSize", "Threshold"):
            out[cur].append(line)
    return out


def breeze_files():
    """{name: {(ctx, size): file}} for every icon in Breeze Dark's fixed-size
    directories, and Breeze's for names Dark does not have."""
    out = {}
    for root in (BREEZE_DARK, BREEZE):
        found = {}
        for ctx in root.iterdir():
            if not ctx.is_dir():
                continue
            for d in ctx.iterdir():
                if d.is_symlink() or not d.name.isdigit():
                    continue
                for f in d.iterdir():
                    if f.suffix == ".svg" and f.exists():
                        found.setdefault(f.stem, {})[(ctx.name, d.name)] = f
        for name, files in found.items():
            out.setdefault(name, files)
    return out


# KIconLoader, failing to find a name starting with one of these in a theme,
# tries "<that>-x-generic" there before it moves on to the next theme: an
# unknown application-exit comes out as this theme's blank page, and the
# tray's audio-volume-high-symbolic as its music page.
GENERIC_PREFIXES = ("application", "audio", "image", "inode", "text", "video")


def hidden_by(name, ours):
    """The name of ours KIconLoader would settle for when asked for `name`,
    if it is not ours itself: a shorter form of it, or its kind's generic."""
    parts = name.split("-")
    for i in range(len(parts) - 1, 0, -1):
        if "-".join(parts[:i]) in ours:
            return "-".join(parts[:i])
    generic = parts[0] + "-x-generic"
    if parts[0] in GENERIC_PREFIXES and generic in ours:
        return generic
    return None


def protect_breeze(theme, only=None):
    """Ship every Breeze icon a name of ours would hide (see the top of the
    file).  A -symbolic name hidden by the plain one is left alone when that
    is drawn by hand -- it is this theme's icon, asked for in its symbolic
    form -- but not when it is converted: then the symbolic one is usually the
    tray's, which stays Breeze's.  With `only`, just the icons those names
    would hide."""
    index = breeze_index()
    ours = set(theme.names)
    written = {}
    for name, files in sorted(breeze_files().items()):
        if name in ours:
            continue
        by = hidden_by(name, ours)
        if by is None or (only is not None and by not in only):
            continue
        if by in theme.drawn and name in (by + "-symbolic", by + "-symbolic-rtl"):
            continue
        for (ctx, size), f in files.items():
            d = "breeze/%s/%s" % (ctx, size)
            if "%s/%s" % (ctx, size) not in index:
                continue
            dest = theme.root / d / (name + ".svg")
            dest.parent.mkdir(parents=True, exist_ok=True)
            theme.breeze_dirs[d] = index["%s/%s" % (ctx, size)]
            real = os.path.realpath(f)
            if dest.exists() or dest.is_symlink():
                continue
            if (d, real) in written:
                dest.symlink_to(written[(d, real)])
            else:
                shutil.copyfile(real, dest)
                written[(d, real)] = dest.name
    return len(set(written.values()))


def both(fn, *args, **kw):
    return {n: fn(n, *args, **kw) for n in DIRS}


def converted(paths):
    """Convert source files in parallel: {resolved path: verdict}."""
    unique = sorted({os.path.realpath(p) for p in paths})
    with multiprocessing.Pool() as pool:
        return dict(pool.imap_unordered(convert, unique, chunksize=8))


def initial(label):
    """The letter for a tile: the first of the app's name, past "KDE " or
    "GNOME ", and past the K of a KDE-style name (KGoldrunner is G)."""
    words = label.replace("_", " ").replace("-", " ").split()
    if len(words) > 1 and words[0] in ("KDE", "GNOME"):
        words = words[1:]
    w = words[0] if words else "x"
    if len(w) > 2 and w[0] == "K" and w[1].isupper() and w[2].islower():
        w = w[1:]
    return next((ch.upper() for ch in w if ch.isalnum()), "X")


def label_of(name):
    """A readable name for an icon with no app to name it: its last part."""
    return name.split(".")[-1].split("-")[-1] or name


def tile(name, label, ramp):
    """Both grids of a letter tile."""
    if ramp is None:
        ramp = list(icons_apps.TILE_RAMPS)[sum(map(ord, name)) % len(icons_apps.TILE_RAMPS)]
    else:
        ramp = RAMPS[ramp]
    letter = initial(label)
    return {n: icons_apps.letter_tile(n, letter, ramp) for n in DIRS}


def put_converted(theme, ctx, name, verdict, label, key):
    """A conversion if it has been looked at and approved (icons_apps.
    CONVERT_OK) and still passes the noise check, else a letter tile."""
    if verdict and verdict["grids"] and name in icons_apps.CONVERT_OK:
        theme.put(ctx, name, verdict["grids"], key=key)
    elif verdict:
        theme.put(ctx, name, tile(name, label, verdict["ramp"]), key=("tile", name))


DEVICE = re.compile(r"^(drive-|media-|input-|audio-|camera-|computer|video-display|monitor$"
                    r"|display$|printer|phone$|smartphone|multimedia-player|pda$|network-server)")


def context_of(name):
    """The directory a hand-made icon goes in.  KIconLoader finds a name in
    any of them; the context only tells other tools what the icon is."""
    if name.startswith("applications-"):
        return "categories"
    if name.startswith(("dialog-", "security-")):
        return "status"
    if name.startswith("preferences-"):
        return "preferences"
    if DEVICE.match(name):
        return "devices"
    if name.startswith("network-workgroup"):
        return "places"
    return "apps"


def build(out):
    root = Path(out) / "icons" / P.NAME
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    theme = Theme(root, skip=breeze_actions())
    breeze = breeze_icons()
    generic = generic_icons()

    # Places: the launcher's sun, the trash, and folders.
    for name in SUN:
        theme.put("places", name, both(A.sun), key="sun")
    for name, full in TRASH.items():
        theme.put("places", name, both(A.trash, full=full), key=("trash", full))
    for name in PLAIN_FOLDERS:
        theme.put("places", name, both(A.folder), key="folder")
    theme.put("places", "folder-open", both(A.folder, open_=True))
    for colour, colours in A.FOLDER_COLOURS.items():
        theme.put("places", "folder-" + colour, both(A.folder, colours))
    for symbol, names in FOLDER_SYMBOLS.items():
        for name in names:
            theme.put("places", name, both(A.folder, symbol=symbol), key=("folder", symbol))
    for name in sorted(n for n in breeze.get("places", {}) if n.startswith("folder")):
        theme.put("places", name, both(A.folder), key="folder")

    # File types: a page per kind of file, every name of that kind linked to it.
    for name in sorted(mime_names(breeze, generic)):
        if name.startswith("inode-directory"):
            theme.put("mimetypes", name, both(A.folder), key="folder")
            continue
        ramp, symbol = file_type(name, generic)
        theme.put("mimetypes", name, both(A.page, RAMPS[ramp], symbol), key=(ramp, symbol))

    # The tray's one-colour icons, ahead of the designs: Night Light's moon
    # and KDE Connect's phone are glyphs there, not the coloured sprites.
    for name, glyph in sorted(icons_tray.icons().items()):
        theme.put_glyph(name, icons_tray.svg(glyph, icons_tray.margin(name)))

    # An installed app's own logo, where it converts cleanly, beats the design
    # standing in for it; where it does not, the design is used.
    apps = installed_apps()
    brands = {name: apps[name][0] for name in icons_apps.brand_names() & set(apps)}
    verdicts = converted(brands.values())
    for name, src in sorted(brands.items()):
        verdict = verdicts.get(os.path.realpath(src))
        if verdict and verdict["grids"] and name in icons_apps.CONVERT_OK:
            theme.put("apps", name, verdict["grids"], key=os.path.realpath(src))

    # Apps, devices, categories, dialogs and power buttons designed here.
    for name, design in sorted(icons_apps.names().items()):
        ctx = context_of(name)
        theme.put(ctx, name, {n: icons_apps.render(design, n) for n in DIRS}, key=("design", design))

    theme.drawn = set(theme.names)

    # Everything else Breeze draws in colour, converted.
    wanted = [(ctx, name, f) for ctx in ("apps", "preferences", "categories", "applets", "devices",
                                         "status", "places")
              for name, f in sorted(breeze.get(ctx, {}).items()) if name not in theme.names]
    verdicts = converted(f for _, _, f in wanted)
    for ctx, name, f in wanted:
        label = apps[name][1] if name in apps else label_of(name)
        put_converted(theme, ctx, name, verdicts.get(os.path.realpath(f)), label, os.path.realpath(f))
    add_installed_apps(theme)
    protect_breeze(theme)
    theme.index()


# ---------------------------------------------------------------- local apps

ICON_ROOTS = [Path.home() / ".local/share/icons/hicolor", Path("/usr/share/icons/hicolor"),
              Path("/var/lib/flatpak/exports/share/icons/hicolor"),
              Path.home() / ".local/share/flatpak/exports/share/icons/hicolor"]
PIXMAPS = [Path("/usr/share/pixmaps"), Path.home() / ".local/share/icons"]
APP_DIRS = ["/usr/share/applications", str(Path.home() / ".local/share/applications"),
            "/var/lib/flatpak/exports/share/applications",
            str(Path.home() / ".local/share/flatpak/exports/share/applications")]


def find_app_icon(name):
    """The best file for an app's icon name: an SVG if there is one, else the
    largest PNG, else anything in pixmaps."""
    best = (0, None)
    for root in ICON_ROOTS:
        for f in glob.glob(str(root / "*" / "apps" / (name + ".*"))):
            size = 10000 if f.endswith((".svg", ".svgz")) else \
                int(re.match(r"(\d+)", Path(f).parent.parent.name).group(1)) \
                if re.match(r"\d+", Path(f).parent.parent.name) else 1
            best = max(best, (size, f), key=lambda t: t[0])
    if best[1]:
        return best[1]
    for d in PIXMAPS:
        for ext in (".svg", ".png", ".xpm"):
            if (d / (name + ext)).is_file():
                return str(d / (name + ext))
    return None


def installed_apps():
    """{icon name: (its file, the app's name)} for the apps installed here, as
    their .desktop files give them; absolute paths and names with no file
    found left out."""
    found = {}
    for d in APP_DIRS:
        for f in glob.glob(d + "/*.desktop"):
            try:
                text = open(f, errors="ignore").read()
            except OSError:
                continue
            m = re.search(r"^Icon=(.+)$", text, re.M)
            if not m:
                continue
            name = m.group(1).strip()
            if name.startswith("/") or name in found:
                continue
            src = find_app_icon(name)
            if src:
                label = re.search(r"^Name=(.+)$", text, re.M)
                found[name] = (src, label.group(1).strip() if label else label_of(name))
    return found


def installed_icons():
    return {name: src for name, (src, _) in installed_apps().items()}


def add_installed_apps(theme):
    """Pixel versions of the icons of the apps installed here that the theme
    has none of (Steam games, KDE's games...), converted from the apps' own
    icons, or a letter tile where that comes out noisy.  Returns how many were
    added."""
    wanted = {name: app for name, app in installed_apps().items()
              if name not in theme.names and name not in theme.skip}
    verdicts = converted(src for src, _ in wanted.values())
    for name, (src, label) in sorted(wanted.items()):
        put_converted(theme, "apps", name, verdicts.get(os.path.realpath(src)), label,
                      os.path.realpath(src))
    return len(wanted)


def local(dest):
    """Add the icons of apps installed since the theme was built to an
    installed copy of it."""
    dest = Path(dest)
    theme = Theme(dest, skip=breeze_actions())
    theme.names = {p.stem for p in dest.rglob("*.svg")}
    index = breeze_index()
    for d in dest.glob("breeze/*/*"):
        theme.breeze_dirs["breeze/%s/%s" % (d.parent.name, d.name)] = index.get(
            "%s/%s" % (d.parent.name, d.name), [])
    before = set(theme.names)
    added = add_installed_apps(theme)
    protect_breeze(theme, only=theme.names - before)
    theme.index()
    print("  %d installed apps' icons added to %s" % (added, dest))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--local":
        local(sys.argv[2])
    elif len(sys.argv) == 1:
        build(Path(__file__).resolve().parent.parent / "theme")
    else:
        sys.exit(__doc__)
