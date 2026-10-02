"""The global theme package: what each part of the theme is, and the splash.

The splash is a pixel-art orrery -- a striped sun with three planets on
tilted orbits, each trailing a short comet tail the way Conky Orrery's cores
do -- over the wallpaper's own sky, dimmed, so the desktop arriving afterwards
looks like the lights coming up on the same scene.
"""

import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

import palette as P
import build_wallpaper as W

FRAMES = 72            # one loop; the planets go round 3, 2 and 1 times in it
FRAME_MS = 45
ART_W, ART_H = 112, 64

ORBITS = [
    # semi-axis a, flattening, tilt (rad), revolutions per loop, radius, colour, phase
    (20, 0.36, -0.20, 3, 2, P.PINK, 0.0),
    (34, 0.34, -0.20, 2, 3, P.MAUVE, 2.1),
    (50, 0.32, -0.20, 1, 2, P.SKY, 4.0),
]


def disc(img, cx, cy, r, colour, shade=None, alpha=1.0):
    """Pixel disc; with `shade`, the lower right is drawn in the shade colour."""
    c = np.array(P.rgb(colour), dtype=float)
    s = np.array(P.rgb(shade), dtype=float) if shade else c
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if dx * dx + dy * dy <= r * r + 0.3 and 0 <= x < ART_W and 0 <= y < ART_H:
                col = s if (dx + dy) > r * 0.55 else c
                img[y, x, :3] = img[y, x, :3] * (1 - alpha) + col * alpha
                img[y, x, 3] = max(img[y, x, 3], 255 * alpha)


def orbit_point(a, flat, tilt, angle):
    x, y = a * math.cos(angle), a * flat * math.sin(angle)
    ct, st = math.cos(tilt), math.sin(tilt)
    return x * ct - y * st, x * st + y * ct, math.sin(angle)   # depth: >0 is near


def frame(n):
    img = np.zeros((ART_H, ART_W, 4))
    cx, cy = ART_W / 2, ART_H / 2

    # orbits as dotted ellipses, brighter on the near side
    for a, flat, tilt, *_ in ORBITS:
        steps = int(a * 2.6)
        for i in range(steps):
            ang = 2 * math.pi * i / steps
            if i % 2:
                continue
            x, y, depth = orbit_point(a, flat, tilt, ang)
            px, py = int(round(cx + x)), int(round(cy + y))
            if 0 <= px < ART_W and 0 <= py < ART_H:
                col = P.SURFACE2 if depth < 0 else P.OVERLAY0
                img[py, px, :3] = P.rgb(col)
                img[py, px, 3] = 255

    bodies = []
    for a, flat, tilt, revs, r, colour, phase in ORBITS:
        ang = phase + 2 * math.pi * revs * n / FRAMES
        x, y, depth = orbit_point(a, flat, tilt, ang)
        trail = []
        for k in range(1, 5):
            tx, ty, _ = orbit_point(a, flat, tilt, ang - k * 0.11 * (4 - revs))
            trail.append((tx, ty, k))
        bodies.append((depth, x, y, r, colour, trail))

    def draw_body(x, y, r, colour, trail):
        for tx, ty, k in trail:
            px, py = int(round(cx + tx)), int(round(cy + ty))
            if 0 <= px < ART_W and 0 <= py < ART_H:
                a = 0.75 - k * 0.16
                img[py, px, :3] = img[py, px, :3] * (1 - a) + np.array(P.rgb(colour)) * a
                img[py, px, 3] = max(img[py, px, 3], 255 * a)
        disc(img, cx + x, cy + y, r + 0.5, colour, P.mix(colour, P.VOID, 0.45))
        if r >= 2:
            hx, hy = int(cx + x - r * 0.4), int(cy + y - r * 0.4)
            if 0 <= hx < ART_W and 0 <= hy < ART_H:
                img[hy, hx, :3] = P.rgb(P.mix(colour, "#FFFFFF", 0.6))

    # far bodies, the sun, then near bodies
    for depth, x, y, r, colour, trail in sorted(bodies):
        if depth < 0:
            draw_body(x, y, r, colour, trail)
    sun(img, cx, cy, n)
    for depth, x, y, r, colour, trail in sorted(bodies):
        if depth >= 0:
            draw_body(x, y, r, colour, trail)
    return img


def sun(img, cx, cy, n):
    r = 9.5
    ramp = [P.rgb(c) for c in ("#FFE08A", "#FFC46A", "#FFA05E", "#FF7A62", "#FF5C78")]
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if dx * dx + dy * dy > r * r:
                continue
            rel = (dy + r) / (2 * r)
            # slats across the lower half, drifting slowly downwards
            if rel > 0.5:
                k = (y - cy + n * 0.25) % 4
                if k < 1:
                    continue
            t = min(len(ramp) - 1, int(rel * len(ramp)))
            img[y, x, :3] = ramp[t]
            img[y, x, 3] = 255


def sprite_sheet():
    frames = [frame(n) for n in range(FRAMES)]
    sheet = np.concatenate(frames, axis=1).clip(0, 255).astype(np.uint8)
    return Image.fromarray(sheet, "RGBA")


def backdrop(width, height, scale):
    """The wallpaper's sky, dimmed and cooled for the splash."""
    _, art = W.render(width, height, scale)
    a = np.asarray(art).astype(float)
    grey = a.mean(axis=2, keepdims=True)
    a = (a * 0.75 + grey * 0.25) * 0.38
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB")


SPLASH_QML = r'''/*
    Retrograde splash: a pixel-art orrery over the night sky.
    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    color: "%(void)s"

    property int stage

    onStageChanged: {
        if (stage == 2) {
            introAnimation.running = true;
        }
    }

    Image {
        id: backdrop
        anchors.fill: parent
        // Pixel art: enlarge with nearest neighbour, never smooth it.
        smooth: false
        fillMode: Image.PreserveAspectCrop
        source: root.width / root.height > 2.0 ? "images/backdrop-wide.png" : "images/backdrop.png"
    }

    Item {
        id: content
        anchors.fill: parent
        opacity: 0

        // One art pixel is this many screen pixels.
        readonly property int pixel: Math.max(2, Math.round(root.height / 240))

        AnimatedSprite {
            id: orrery
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -content.pixel * 6
            width: %(art_w)d * content.pixel
            height: %(art_h)d * content.pixel
            source: "images/orrery.png"
            frameWidth: %(art_w)d
            frameHeight: %(art_h)d
            frameCount: %(frames)d
            frameDuration: %(frame_ms)d
            interpolate: false
            smooth: false
            loops: AnimatedSprite.Infinite
            running: Kirigami.Units.longDuration > 1
        }

        Text {
            id: wordmark
            anchors.top: orrery.bottom
            anchors.topMargin: content.pixel * 6
            anchors.horizontalCenter: parent.horizontalCenter
            text: "RETROGRADE"
            color: "%(text)s"
            font.family: "Noto Sans"
            font.weight: Font.Light
            font.pixelSize: content.pixel * 7
            font.letterSpacing: content.pixel * 3
            renderType: Text.QtRendering
        }

        // Six blocks that fill in as Plasma starts.
        Row {
            anchors.top: wordmark.bottom
            anchors.topMargin: content.pixel * 6
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: content.pixel * 2
            Repeater {
                model: 6
                Rectangle {
                    width: content.pixel * 3
                    height: content.pixel * 3
                    color: index < root.stage ? %(sunset)s[index %% 5] : "%(dim)s"
                    Behavior on color { ColorAnimation { duration: Kirigami.Units.longDuration } }
                }
            }
        }
    }

    OpacityAnimator {
        id: introAnimation
        running: false
        target: content
        from: 0
        to: 1
        duration: Kirigami.Units.veryLongDuration * 2
        easing.type: Easing.InOutQuad
    }
}
'''


def splash_qml():
    return SPLASH_QML % {
        "void": P.VOID, "text": P.TEXT, "dim": P.SURFACE1,
        "art_w": ART_W, "art_h": ART_H, "frames": FRAMES, "frame_ms": FRAME_MS,
        "sunset": json.dumps(P.SUNSET),
    }


FONT = "Noto Sans,12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
FONT_SMALL = "Noto Sans,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
FONT_BOLD = "Noto Sans,12,-1,5,700,0,0,0,0,0,0,0,0,0,0,1"


def defaults():
    return "\n".join([
        "[kdeglobals][KDE]",
        "widgetStyle=Breeze",
        "",
        "[kdeglobals][General]",
        "ColorScheme=%s" % P.NAME,
        "font=%s" % FONT,
        "menuFont=%s" % FONT,
        "toolBarFont=%s" % FONT_SMALL,
        "smallestReadableFont=%s" % FONT_SMALL,
        "",
        "[kdeglobals][WM]",
        "activeFont=%s" % FONT_BOLD,
        "",
        "[kdeglobals][Icons]",
        "Theme=%s" % P.NAME,
        "",
        "[plasmarc][Theme]",
        "name=%s" % P.NAME,
        "",
        "[Wallpaper]",
        "Image=%s" % P.NAME,
        "",
        "[kcminputrc][Mouse]",
        "cursorTheme=%s-cursors" % P.NAME,
        "",
        "[kwinrc][org.kde.kdecoration2]",
        "library=org.kde.kwin.aurorae",
        "theme=__aurorae__svg__%s" % P.NAME,
        "",
        "[ksplashrc][KSplash]",
        "Theme=%s" % P.NAME,
        "",
    ])


def metadata():
    return json.dumps({
        "KPackageStructure": "Plasma/LookAndFeel",
        "KPlugin": {
            "Authors": [{"Name": P.AUTHOR}],
            "Category": "",
            "Description": "Dark retro theme: a pixel-art dusk, pixel planets for window "
                           "buttons and a sunset stripe. Made to sit behind Conky Orrery.",
            "Id": P.NAME,
            "License": "GPL-3.0-or-later",
            "Name": P.NAME,
            "Version": P.VERSION,
            "Website": "https://github.com/alexsson-xexpanderx/kde-plasma-themes",
        },
        "X-Plasma-APIVersion": "2",
    }, indent=4) + "\n"


def build(out):
    root = Path(out) / "plasma" / "look-and-feel" / P.NAME
    previews = root / "contents" / "previews"
    kept = {}
    if previews.exists():                     # screenshots are made separately; keep them
        for f in previews.iterdir():
            kept[f.name] = f.read_bytes()
    if root.exists():
        shutil.rmtree(root)
    (root / "contents" / "splash" / "images").mkdir(parents=True)
    previews.mkdir(parents=True)
    for name, data in kept.items():
        (previews / name).write_bytes(data)
    (root / "metadata.json").write_text(metadata())
    (root / "contents" / "defaults").write_text(defaults())
    (root / "contents" / "splash" / "Splash.qml").write_text(splash_qml())
    images = root / "contents" / "splash" / "images"
    sprite_sheet().save(images / "orrery.png", optimize=True)
    backdrop(1920, 1080, 3).save(images / "backdrop.png", optimize=True)
    backdrop(3440, 1440, 4).save(images / "backdrop-wide.png", optimize=True)


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "theme")
