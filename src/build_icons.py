#!/usr/bin/env python3
"""Icon theme: pixel icons in the wallpaper's colours.

Two kinds of icon go in:

* Made here (icons_art.py): folders, file pages, the trash and the launcher's
  sun -- what Dolphin and the panel show most, drawn cell by cell.
* Converted: every icon of candy-icons, and the coloured icons of Breeze that
  candy has no version of, drawn onto a grid of cells.  Each icon goes onto
  the nearest of the wallpaper's ramps (palette.py) to its commonest colour --
  blues go violet, greens and cyans go sky blue, everything warm lands on the
  sunset -- and is drawn in two colours of it.  Candy draws in lines, so what
  an icon's outline encloses is filled with the dark one and the lines are
  the bright one (see body and recolour).  Then the hard shadow.

Each icon is drawn twice: 24 cells across for 24 px and up, 16 across for 16
and 22 px.  They are written as SVG -- one path per colour, every cell a
square -- so they stay crisp at fractional display scales, over a solid
underlay so that they do not go see-through along the seams between colours
there either (see svgkit.Group.grid).

Toolbar actions are left to Breeze Dark, which the theme inherits: they are
monochrome and follow the colour scheme, as every toolbar expects.  The
exceptions are the power and session actions -- shut down, restart, lock, log
out -- which the launcher and the logout screen show large.

One thing makes that harder than leaving them out.  KIconLoader looks a name
up in this theme first under its full name and then under ever shorter ones
(kdenlive-add-clip, then kdenlive) before it tries Breeze Dark at all, so a
name of ours that is the start of one of Breeze's hides Breeze's: Kdenlive's
toolbar would show Kdenlive's logo forty times over.  So every Breeze icon a
name of ours would hide is shipped here as well, unchanged, under breeze/.

The build also converts the icons of the apps installed on the machine it
runs on that neither candy nor Breeze has, so the theme in the repository
covers this machine's apps too.

    python3 src/build_icons.py               build theme/icons/Retrograde
    python3 src/build_icons.py --local DIR   add the icons of apps installed
                                             since to an installed copy in DIR
"""

import colorsys
import glob
import io
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
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import icons_art as A  # noqa: E402
import palette as P    # noqa: E402

CANDY = Path(os.environ.get("CANDY_ICONS", Path.home() / ".local/share/icons/candy-icons"))
BREEZE = Path("/usr/share/icons/breeze")
BREEZE_DARK = Path("/usr/share/icons/breeze-dark")
MIME = Path("/usr/share/mime")

# Cells across, and how many of them an icon's content may fill: the rest is
# margin and the shadow's one cell.
GRIDS = {24: 21, 16: 14}
# How much of a cell an icon must cover for the cell to be drawn.  Lower on
# the small grid, where candy's strokes are barely a cell wide.
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


# Gaps an outline may have and still count as closed, as a share of the icon's
# size: candy leaves its frames open at a corner or a side.
FILL_GAP = 0.09
FILL_RES = 192


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def body(crop):
    """The inside of an outline icon: what its strokes enclose once gaps up to
    FILL_GAP are bridged, less the strokes themselves; and, everywhere, the
    colour of the nearest stroke, which the inside is filled in a shade of.
    Candy draws nearly everything as a line, which pixelated is a thin hollow
    ring; filled, it reads as a solid object at 16 and 24 px."""
    h, w = crop.shape[:2]
    s = FILL_RES / max(h, w)
    sw, sh = max(1, round(w * s)), max(1, round(h * s))
    small = np.asarray(Image.fromarray(crop[..., 3].astype(np.float32), "F").resize((sw, sh), Image.BOX))
    ink = small > 0.3
    r = max(1, round(FILL_GAP * FILL_RES / 2))
    pad = np.pad(ink, r + 1)
    closed = ndimage.binary_closing(pad, structure=disk(r))[r + 1:-r - 1, r + 1:-r - 1]
    inside = ndimage.binary_fill_holes(closed | ink)
    # Frames open along a whole side, like a terminal's [>_ : a point with
    # line on three of its four sides is inside too.
    sides = (np.maximum.accumulate(ink, axis=0).astype(int)
             + np.maximum.accumulate(ink[::-1], axis=0)[::-1]
             + np.maximum.accumulate(ink, axis=1)
             + np.maximum.accumulate(ink[:, ::-1], axis=1)[:, ::-1])
    inside = (inside | (sides >= 3)) & ~ink
    inside = ndimage.binary_opening(inside, structure=disk(2))
    # The nearest stroke's colour, from the full-size icon's colours.
    rgb = np.stack([np.asarray(Image.fromarray((crop[..., c] * crop[..., 3]).astype(np.float32), "F")
                               .resize((sw, sh), Image.BOX)) for c in range(3)], -1)
    rgb = rgb / np.maximum(small[..., None], 1e-6)
    _, (iy, ix) = ndimage.distance_transform_edt(~ink, return_indices=True)
    near = np.clip(rgb[iy, ix], 0, 1)
    return inside.astype(np.float32), near.astype(np.float32)


def to_cells(arr, n, room):
    """Average the icon's content onto an n-cell grid: how much of each cell it
    covers, and its colour there; and the same for the inside its outline
    encloses (see body).  The content is scaled to fit `room` cells and
    centred together with the cell of shadow it will get."""
    a = arr[..., 3]
    ys, xs = np.nonzero(a > 0.02)
    if len(ys) == 0:
        return None, None, None, None
    crop = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    bh, bw = crop.shape[:2]
    s = room / max(bw, bh)
    wc, hc = max(1, round(bw * s)), max(1, round(bh * s))

    def box(channel):
        return np.asarray(Image.fromarray(channel.astype(np.float32), "F").resize((wc, hc), Image.BOX))
    cover = box(crop[..., 3])
    colour = np.stack([box(crop[..., c] * crop[..., 3]) for c in range(3)], -1)
    colour = np.clip(colour / np.maximum(cover[..., None], 1e-6), 0, 1)
    inside, near = body(crop)
    fill = box(inside)
    fill_rgb = np.stack([box(near[..., c]) for c in range(3)], -1)
    C, F = np.zeros((n, n)), np.zeros((n, n))
    RGB, FRGB = np.zeros((n, n, 3)), np.zeros((n, n, 3))
    ox, oy = (n - wc - 1) // 2, (n - hc - 1) // 2
    C[oy:oy + hc, ox:ox + wc] = cover
    RGB[oy:oy + hc, ox:ox + wc] = colour
    F[oy:oy + hc, ox:ox + wc] = fill
    FRGB[oy:oy + hc, ox:ox + wc] = fill_rgb
    return C, RGB, F, FRGB


def family(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.22 or v < 0.12:
        return "grey"
    d = h * 360
    if 200 <= d < 290:
        return "violet"
    if 290 <= d < 340:
        return "rose"
    if d >= 340 or d < 18:
        return "red"
    if d < 42:
        return "orange"
    if d < 75:
        return "gold"
    return "sky"


# Each icon is drawn in one ramp, its commonest: candy's gradients run through
# two or three, which cell by cell is a patchwork that hides what the icon
# shows.  And in two colours of it: a bright one for every line -- outline and
# the symbol inside alike -- and a dark one for what the outline encloses.
LINE_SHADE = 3
FILL_SHADE = {"orange": 0, "gold": 0}   # the warm ramps start a shade brighter
FILL_RAMP = {"gold": "brown"}           # gold's darkest is too light to fill with
FILL_DEFAULT = 1
# An icon its outline does not enclose (a solid one, from Breeze or an app)
# keeps its light and dark: two shades, picked by brightness.
SOLID_SHADES = (1, 3)
# Over the fill a line needs less of a cell to be drawn, so that the thin
# details inside an icon -- a terminal's prompt, a page's lines -- show.
INNER_THRESHOLD = 0.28
LINE_ART = 0.25


def fill_colour(fam):
    fam = FILL_RAMP.get(fam, fam)
    return RAMPS[fam][FILL_SHADE.get(fam, FILL_DEFAULT)]


def recolour(C, RGB, F, FRGB, n):
    """The covered cells in two colours of one wallpaper ramp: lines bright,
    what they enclose dark (see LINE_SHADE)."""
    on = (C >= THRESHOLD[n]) | ((C >= INNER_THRESHOLD) & (C + F >= 0.75))
    # A faint cell on its own over the fill is a speck, not a detail.
    faint = on & (C < THRESHOLD[n])
    lonely = ndimage.convolve(on.astype(int), np.ones((3, 3), int), mode="constant") <= 1
    on &= ~(faint & lonely)
    inside = ~on & (C + F >= 0.5)
    inside |= ndimage.binary_fill_holes(on | inside) & ~on
    # Fill showing at the outside is a gap in candy's outline: close it, so
    # the border is one unbroken line.
    outside = ~np.pad(on | inside, 1)
    gap = inside & ndimage.binary_dilation(outside)[1:-1, 1:-1]
    on, inside = on | gap, inside & ~gap
    counts = Counter(family(*RGB[y, x]) for y, x in zip(*np.nonzero(on)))
    if not counts:
        return A.blank(n)
    ramp = RAMPS[counts.most_common(1)[0][0]]
    fill = fill_colour(counts.most_common(1)[0][0])
    line_art = inside.sum() >= LINE_ART * (on | inside).sum()
    grid = A.blank(n)
    for y, x in zip(*np.nonzero(on | inside)):
        if inside[y, x]:
            grid[y][x] = (fill, 1.0)
        elif line_art:
            grid[y][x] = (ramp[LINE_SHADE], 1.0)
        else:
            bright = int(max(RGB[y, x]) >= 0.6)
            grid[y][x] = (ramp[SOLID_SHADES[bright]], 1.0)
    return A.add_shadow(grid)


def convert(path):
    """Both grids of one source icon, or None if it cannot be read."""
    try:
        arr = load(path)
    except (subprocess.CalledProcessError, OSError, ValueError):
        return path, None
    grids = {}
    for n, room in GRIDS.items():
        C, RGB, F, FRGB = to_cells(arr, n, room)
        if C is None:
            return path, None
        grids[n] = recolour(C, RGB, F, FRGB, n)
    return path, grids


# ---------------------------------------------------------------- sources

def symbolic(name):
    return name.endswith("-symbolic") or name.endswith("-symbolic-rtl")


def candy_icons():
    """{context: {name: file}} -- candy's own contexts, symbolic names left out."""
    out = defaultdict(dict)
    if not CANDY.is_dir():
        print("  candy-icons not found at %s; converting Breeze only" % CANDY, file=sys.stderr)
        return out
    for d in sorted(CANDY.glob("*/*")):
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix == ".svg" and not symbolic(f.stem) and f.exists():
                out[d.parent.name].setdefault(f.stem, f)
    return out


# Toolbar actions this theme draws after all (see the top of the file).
KEEP_ACTION = re.compile(r"^(system-(shutdown|reboot|lock-screen|log-out|suspend|suspend-hibernate"
                         r"|hibernate|switch-user)|notifications?(-|$)|notification-)")


def breeze_actions():
    """Breeze's toolbar action names, less the ones drawn here anyway."""
    names = set()
    for root in (BREEZE, BREEZE_DARK):
        names |= {f.stem for f in (root / "actions").glob("*/*.svg")}
    return {n for n in names if not KEEP_ACTION.match(n)}


# Names candy has no icon under but draws under another name; candy's beats
# converting Breeze's, which for these is mostly grey and comes out dull.
CANDY_ALIASES = {
    "systemsettings": "preferences-system",
    "org.kde.systemsettings": "preferences-system",
}


def breeze_icons():
    """{context: {name: file}} -- Breeze's coloured icons, each at the largest
    size it comes in.  Only devices and status drawn 32 px and up are coloured;
    their smaller ones are monochrome and stay Breeze's."""
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
            if ctx in ("devices", "status") and size < 32:
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
    "home": ["user-home", "folder-home"],
    "desktop": ["user-desktop", "folder-desktop", "desktop", "cs-desktop"],
    "templates": ["folder-templates"],
    "people": ["folder-publicshare", "folder-public"],
    "globe": ["folder-remote", "folder-network", "folder-language", "folder-html", "folder_html"],
    "cloud": ["folder-cloud", "folder-gdrive", "folder-dropbox", "folder-nextcloud",
              "folder-owncloud", "folder-onedrive"],
    "code": ["folder-development", "folder-script", "folder-java", "folder-build"],
    "games": ["folder-games"],
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
            "folder-deb", "folder-extension"],
    "gear": ["folder-root"],
}
PLAIN_FOLDERS = ["folder", "inode-directory", "gtk-directory", "stock_folder", "folder-activities"]
SUN = ["start-here", "start-here-kde", "start-here-kde-plasma", "distributor-logo"]
TRASH = {"user-trash": False, "user-trash-full": True, "trash-empty": False, "trash-full": True}


def lifted_symbol(path):
    """The white symbol off one of candy's folders, as rows for a 24-cell
    folder; None if there is not enough of one to draw."""
    try:
        arr = load(path)
    except (subprocess.CalledProcessError, OSError):
        return None
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    hi, lo = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    white = (a > 0.5) & (hi > 0.82) & ((hi - lo) < 0.22)
    if white.sum() < 200:
        return None
    ys, xs = np.nonzero(white)
    crop = white[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
    bh, bw = crop.shape
    s = min(9 / bw, 7 / bh)
    wc, hc = max(1, round(bw * s)), max(1, round(bh * s))
    cover = np.asarray(Image.fromarray(crop, "F").resize((wc, hc), Image.BOX))
    rows = ["".join("#" if v >= 0.42 else "." for v in row) for row in cover]
    filled = sum(r.count("#") for r in rows)
    return rows if 6 <= filled <= 0.8 * wc * hc else None


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


def mime_names(candy, breeze, generic):
    names = set(candy.get("mimetypes", {})) | set(breeze.get("mimetypes", {})) | set(GENERIC)
    names |= set(SPECIFIC) | set(generic) | set(generic.values())
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


def protect_breeze(theme):
    """Ship every Breeze icon that a shorter name of ours would hide (see the
    top of the file).  A -symbolic name hidden by the plain name is left
    alone: that is this theme's icon, asked for in its symbolic form."""
    index = breeze_index()
    ours = set(theme.names)
    written = {}
    for name, files in sorted(breeze_files().items()):
        if name in ours:
            continue
        parts = name.split("-")
        hidden_by = next(("-".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)
                          if "-".join(parts[:i]) in ours), None)
        if hidden_by is None or name in (hidden_by + "-symbolic", hidden_by + "-symbolic-rtl"):
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
    return len({n for n in written.values()})


def both(fn, *args, **kw):
    return {n: fn(n, *args, **kw) for n in DIRS}


def converted(paths):
    """Convert source files in parallel: {resolved path: grids}."""
    unique = sorted({os.path.realpath(p) for p in paths})
    with multiprocessing.Pool() as pool:
        return {p: g for p, g in pool.imap_unordered(convert, unique, chunksize=8) if g}


def build(out):
    root = Path(out) / "icons" / P.NAME
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    theme = Theme(root, skip=breeze_actions())
    candy, breeze = candy_icons(), breeze_icons()
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
    place_names = set(candy.get("places", {})) | set(breeze.get("places", {}))
    for name in sorted(n for n in place_names if n.startswith("folder")):
        if name in theme.names:
            continue
        rows = lifted_symbol(candy["places"][name]) if name in candy.get("places", {}) else None
        theme.put("places", name, {24: A.folder(24, symbol_mask=rows), 16: A.folder(16)},
                  key=None if rows else "folder")

    # File types: a page per kind of file, every name of that kind linked to it.
    for name in sorted(mime_names(candy, breeze, generic)):
        if name.startswith("inode-directory"):
            theme.put("mimetypes", name, both(A.folder), key="folder")
            continue
        ramp, symbol = file_type(name, generic)
        theme.put("mimetypes", name, both(A.page, RAMPS[ramp], symbol), key=(ramp, symbol))

    # Everything else: converted, candy's version first.
    wanted, seen = [], set(theme.names)
    candy_files = {name: f for icons in candy.values() for name, f in icons.items()}
    for name, target in CANDY_ALIASES.items():
        if target in candy_files:
            seen.add(name)
            wanted.append(("apps", name, candy_files[target]))
    for source in (candy, breeze):
        for ctx in ("apps", "preferences", "categories", "applets", "devices", "status", "places"):
            for name, f in sorted(source.get(ctx, {}).items()):
                if name not in seen:
                    seen.add(name)
                    wanted.append((ctx, name, f))
    grids = converted(f for _, _, f in wanted)
    for ctx, name, f in wanted:
        g = grids.get(os.path.realpath(f))
        if g:
            theme.put(ctx, name, g, key=os.path.realpath(f))
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


def add_installed_apps(theme):
    """Pixel versions of the icons of the apps installed here that the theme
    has none of (Steam games, KDE's games, Qt's tools...), converted from the
    apps' own icons.  Returns how many were added."""
    wanted = {}
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
            if name.startswith("/") or name in theme.names or name in theme.skip or name in wanted:
                continue
            src = find_app_icon(name)
            if src:
                wanted[name] = src
    grids = converted(wanted.values())
    added = 0
    for name, src in sorted(wanted.items()):
        g = grids.get(os.path.realpath(src))
        if g:
            theme.put("apps", name, g, key=os.path.realpath(src))
            added += 1
    return added


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
    added = add_installed_apps(theme)
    protect_breeze(theme)
    theme.index()
    print("  %d installed apps' icons added to %s" % (added, dest))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--local":
        local(sys.argv[2])
    elif len(sys.argv) == 1:
        build(Path(__file__).resolve().parent.parent / "theme")
    else:
        sys.exit(__doc__)
