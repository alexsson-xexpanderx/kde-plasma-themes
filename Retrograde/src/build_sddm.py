"""The login screen: an SDDM greeter theme.

The wallpaper fills the screen, enlarged by a whole number so its pixels stay
square; the splash's little orrery turns in the sky above a clock; and the
login card is a Plasma popup -- stepped corners, outline, the sunset stripe
across its top, a hard shadow -- drawn by the Plasma style's own frame_grid()
and shipped as nine-patch images.  The greeter runs as its own user and
cannot see ~/.local/share, so the font, the icons and the art all travel
inside the theme.

SDDM's greeter on X11 is not scaled, so text is set in whole multiples of the
font's 11-pixel em, and every frame pixel is FRAME_PX screen pixels.
"""

import shutil
import subprocess
from pathlib import Path

from PIL import Image

import palette as P
import build_fonts as FN
import build_lookandfeel as LF
import build_plasma as BP
import build_wallpaper as W
import icons_tray as TR

HERE = Path(__file__).resolve().parent
ICONS = HERE.parent / "theme" / "icons" / P.NAME / "apps" / "scalable"

FRAME_PX = 2         # screen pixels to one pixel of a frame
ICON_PX = 48         # the power icons: their 24-cell grid at two pixels a cell

# One piece of art per screen shape; the greeter picks the nearest shape.
ARTS = [(3440, 1440, 4), (2560, 1080, 3), (5120, 1440, 4), (1920, 1080, 3),
        (1920, 1200, 3), (1366, 768, 2)]

SMALL = dict(corner=4, steps=list(BP.STEPS_SMALL))
RAISED = dict(bevel_top=("#FFFFFF", 0.07), bevel_bottom=(P.VOID, 0.55, 1))

FRAMES = {
    "card": BP.Frame(corner=6, fill=(P.MANTLE, 0.94), outline=BP.OUTLINE, band=list(P.SUNSET)),
    "card-shadow": BP.Frame(corner=6, fill=(P.VOID, 0.55)),
    "field": BP.Frame(fill=(P.CRUST, 1.0), outline=(P.SURFACE1, 1.0),
                      bevel_top=(P.VOID, 0.8), **SMALL),
    "field-focus": BP.Frame(fill=(P.CRUST, 1.0), outline=(P.PINK, 1.0),
                            bevel_top=(P.VOID, 0.8), **SMALL),
    "button": BP.Frame(fill=(P.BASE, 1.0), outline=(P.SURFACE2, 1.0), **RAISED, **SMALL),
    "button-hover": BP.Frame(fill=(P.BASE, 1.0), outline=(P.PINK, 1.0), **RAISED, **SMALL),
    "button-pressed": BP.Frame(fill=(P.CRUST, 1.0), outline=(P.SURFACE2, 1.0),
                               bevel_top=(P.VOID, 0.7), **SMALL),
    "accent": BP.Frame(fill=(P.PINK, 1.0), outline=(P.mix(P.PINK, P.VOID, 0.45), 1.0),
                       bevel_top=("#FFFFFF", 0.25), bevel_bottom=(P.VOID, 0.35, 1), **SMALL),
    "accent-hover": BP.Frame(fill=(P.mix(P.PINK, "#FFFFFF", 0.18), 1.0),
                             outline=(P.mix(P.PINK, P.VOID, 0.45), 1.0),
                             bevel_top=("#FFFFFF", 0.25), bevel_bottom=(P.VOID, 0.35, 1), **SMALL),
}

POWER = [("suspend", "system-suspend", "Suspend", "canSuspend", "suspend"),
         ("reboot", "system-reboot", "Restart", "canReboot", "reboot"),
         ("shutdown", "system-shutdown", "Shut down", "canPowerOff", "powerOff")]


def frame_image(f):
    """A frame's sample as an image, FRAME_PX screen pixels to a cell, and the
    border (in screen pixels) a BorderImage keeps unstretched."""
    grid, n = BP.frame_grid(f)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell is not None:
                colour, alpha = cell
                im.putpixel((x, y), P.rgb(colour) + (round(alpha * 255),))
    return im.resize((n * FRAME_PX, n * FRAME_PX), Image.NEAREST), f.corner * FRAME_PX


def glyph_image(rows, colour):
    """A tray glyph, two screen pixels to a cell, in one colour."""
    im = Image.new("RGBA", (TR.N, TR.N), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in TR.STYLE:
                im.putpixel((x, y), P.rgb(colour) + (round(TR.STYLE[ch][1] * 255),))
    return im.resize((TR.N * FRAME_PX, TR.N * FRAME_PX), Image.NEAREST)


# SDDM sets QT_IM_MODULE=qtvirtualkeyboard when sddm.conf asks for it, and
# with no panel of the theme's own Qt then docks its keyboard across half the
# screen whenever a field has focus.  This panel, loaded so that a missing
# module costs only the button, stays shut until the button opens it.
KEYBOARD_QML = r'''import QtQuick
import QtQuick.VirtualKeyboard

InputPanel {
    property bool activated: false
    active: activated && Qt.inputMethod.visible
    visible: active
}
'''


def arts_js():
    return ", ".join('{ w: %d, h: %d, file: "images/sky-%dx%d.png" }' % (w, h, w, h)
                     for w, h in ((-(-wd // sc), -(-ht // sc)) for wd, ht, sc in ARTS))


MAIN_QML = r'''/*
    Retrograde login screen (SDDM): the wallpaper, the splash's orrery over a
    clock, and a pixel login card in the theme's pixel font.
    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "{{VOID}}"

    // Departure Mono is drawn eleven pixels to the em and is sharp only at
    // whole multiples of that, on whole pixels.
    readonly property int em: 11
    // The unstretched edge of the card's frame and of the small frames.
    readonly property int border: {{CARD_CUT}}
    readonly property bool primary: typeof primaryScreen === "undefined" || primaryScreen

    property int sessionIndex: sessionModel.lastIndex
    property var sessionNames: []
    property string message: ""
    property color messageColour: "{{RED}}"

    FontLoader { id: pixelFont; source: "fonts/DepartureMono-Regular.otf" }
    readonly property string family: pixelFont.status === FontLoader.Ready
                                     ? pixelFont.font.family : "monospace"

    component PixelText: Text {
        font.family: root.family
        font.pixelSize: 2 * root.em
        font.hintingPreference: Font.PreferNoHinting
        renderType: Text.NativeRendering
        color: "{{TEXT}}"
    }

    component Frame: BorderImage {
        property int cut: {{SMALL_CUT}}
        border { left: cut; top: cut; right: cut; bottom: cut }
        horizontalTileMode: BorderImage.Stretch
        verticalTileMode: BorderImage.Stretch
        smooth: false
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            password.text = ""
            root.messageColour = "{{RED}}"
            root.message = "Login failed"
            password.forceActiveFocus()
        }
        function onInformationMessage(message) {
            root.messageColour = "{{AMBER}}"
            root.message = message
        }
    }

    // Session names, read once from the model for the selector.
    Repeater {
        model: sessionModel
        delegate: Item {
            Component.onCompleted: {
                var names = root.sessionNames.slice()
                names[index] = model.name
                root.sessionNames = names
            }
        }
    }

    // ---- The sky: the wallpaper's art enlarged by a whole number, the shape
    // nearest the screen's, cropped at the top and sides.
    readonly property var arts: [ {{ARTS}} ]

    function nearestArt() {
        var best = arts[0], gap = 1e9, shape = Math.log(width / Math.max(1, height))
        for (var i = 0; i < arts.length; i++) {
            var g = Math.abs(Math.log(arts[i].w / arts[i].h) - shape)
            if (g < gap) { gap = g; best = arts[i] }
        }
        return best
    }

    readonly property var art: nearestArt()
    // One pixel of the wallpaper's art, in screen pixels.
    readonly property int pixel: Math.max(1, Math.ceil(Math.max(width / art.w, height / art.h)))

    Image {
        source: root.art.file
        smooth: false
        width: root.art.w * root.pixel
        height: root.art.h * root.pixel
        x: Math.round((root.width - width) / 2)
        y: root.height - height
    }

    // How far the sky and the card move up while the on-screen keyboard is
    // open, so the card stays clear of it.
    readonly property int lift: keyboard_.open
        ? Math.max(0, cardArea.baseY + cardArea.height + root.em - (root.height - keyboard_.height)) : 0

    // ---- The orrery and the clock, in the calm sky the conky Orrery uses.
    Column {
        id: sky
        visible: root.primary
        spacing: 3 * root.pixel
        x: Math.round((root.width - width) / 2)
        y: Math.round(root.height * 0.10) - root.lift

        AnimatedSprite {
            anchors.horizontalCenter: parent.horizontalCenter
            width: {{ART_W}} * root.pixel
            height: {{ART_H}} * root.pixel
            source: "images/orrery.png"
            frameWidth: {{ART_W}}
            frameHeight: {{ART_H}}
            frameCount: {{FRAMES}}
            frameDuration: {{FRAME_MS}}
            interpolate: false
            smooth: false
            loops: AnimatedSprite.Infinite
            running: true
        }

        PixelText {
            id: clock
            anchors.horizontalCenter: parent.horizontalCenter
            font.pixelSize: 8 * root.em
            text: Qt.formatTime(new Date(), "{{TIME_FORMAT}}")
        }

        PixelText {
            id: date
            anchors.horizontalCenter: parent.horizontalCenter
            color: "{{SUBTEXT}}"
            text: Qt.formatDate(new Date(), "{{DATE_FORMAT}}")
        }

        Timer {
            interval: 1000; repeat: true; running: true
            onTriggered: {
                var now = new Date()
                clock.text = Qt.formatTime(now, "{{TIME_FORMAT}}")
                date.text = Qt.formatDate(now, "{{DATE_FORMAT}}")
            }
        }
    }

    // ---- The card.
    Item {
        id: cardArea
        visible: root.primary
        width: 52 * root.em
        height: content.height + 2 * root.border + 12 + 2 * root.em
        readonly property int baseY: Math.round(root.height * 0.10) + sky.height + 4 * root.pixel
        x: Math.round((root.width - width) / 2)
        y: baseY - root.lift

        Frame {
            source: "images/card-shadow.png"
            cut: root.border
            x: 3 * {{FRAME_PX}}; y: 3 * {{FRAME_PX}}
            width: parent.width; height: parent.height
        }
        Frame { source: "images/card.png"; cut: root.border; anchors.fill: parent }

        Column {
            id: content
            x: 2 * root.em
            y: root.border + 12 + root.em
            width: parent.width - 4 * root.em
            spacing: root.em

            PixelText {
                text: sddm.hostName
                color: "{{OVERLAY1}}"
            }

            Field {
                id: user
                label: "user"
                text: userModel.lastUser
                onAccepted: password.forceActiveFocus()
            }

            Field {
                id: password
                label: "password"
                secret: true
                onAccepted: root.login()
            }

            Item {
                width: parent.width
                height: loginButton.height

                PixelText {
                    anchors.verticalCenter: parent.verticalCenter
                    color: keyboard.capsLock ? "{{AMBER}}" : root.messageColour
                    text: keyboard.capsLock ? "Caps Lock is on" : root.message
                }

                PixelButton {
                    id: loginButton
                    anchors.right: parent.right
                    accent: true
                    text: "log in"
                    onClicked: root.login()
                }
            }

            // Session, cycled with a click or the arrow keys; keyboard layout.
            Item {
                width: parent.width
                height: 3 * root.em

                PixelText {
                    id: session
                    anchors.verticalCenter: parent.verticalCenter
                    color: sessionMouse.containsMouse || session.activeFocus ? "{{TEXT}}" : "{{SUBTEXT}}"
                    text: "< " + (root.sessionNames[root.sessionIndex] || "session") + " >"
                    activeFocusOnTab: true
                    Keys.onLeftPressed: root.cycleSession(-1)
                    Keys.onRightPressed: root.cycleSession(1)
                    MouseArea {
                        id: sessionMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: function(mouse) {
                            root.cycleSession(mouse.button === Qt.RightButton ? -1 : 1)
                        }
                    }
                }

                Row {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 2 * root.em

                    PixelText {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: keyboard.layouts.length > 1
                        color: layoutMouse.containsMouse ? "{{TEXT}}" : "{{SUBTEXT}}"
                        text: keyboard.layouts.length > 0
                              ? keyboard.layouts[keyboard.currentLayout].shortName : ""
                        MouseArea {
                            id: layoutMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: keyboard.currentLayout =
                                       (keyboard.currentLayout + 1) % keyboard.layouts.length
                        }
                    }

                    // The on-screen keyboard, when the system has one.
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: keyboard_.status === Loader.Ready
                        smooth: false
                        source: keyboard_.activated || keyboardMouse.containsMouse
                                ? "images/keyboard-on.png" : "images/keyboard.png"
                        MouseArea {
                            id: keyboardMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                keyboard_.item.activated = !keyboard_.item.activated
                                password.forceActiveFocus()
                            }
                        }
                    }
                }
            }

            Rectangle { width: parent.width; height: {{FRAME_PX}}; color: "{{SURFACE1}}" }

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 2 * root.em
{{POWER}}
            }
        }
    }

    Loader {
        id: keyboard_
        source: "Keyboard.qml"
        z: 10
        readonly property bool activated: item ? item.activated : false
        readonly property bool open: item ? item.active : false
        width: Math.min(root.width, 140 * root.em)
        x: Math.round((root.width - width) / 2)
        y: root.height - height
    }

    function login() {
        root.message = ""
        sddm.login(user.text, password.text, root.sessionIndex)
    }

    function cycleSession(step) {
        var n = sessionModel.rowCount()
        if (n > 0) root.sessionIndex = (root.sessionIndex + step + n) % n
    }

    // ---- Controls.

    component Field: Item {
        id: field
        property string label
        property bool secret: false
        property alias text: input.text
        signal accepted()
        width: parent.width
        height: 4 * root.em
        onActiveFocusChanged: if (activeFocus) input.forceActiveFocus()

        Frame {
            anchors.fill: parent
            source: input.activeFocus ? "images/field-focus.png" : "images/field.png"
        }
        PixelText {
            id: caption
            x: root.em
            anchors.verticalCenter: parent.verticalCenter
            color: "{{OVERLAY1}}"
            text: field.label
        }
        TextInput {
            id: input
            x: 12 * root.em
            width: parent.width - x - root.em
            anchors.verticalCenter: parent.verticalCenter
            clip: true
            activeFocusOnTab: true
            font.family: root.family
            font.pixelSize: 2 * root.em
            font.hintingPreference: Font.PreferNoHinting
            renderType: Text.NativeRendering
            color: "{{TEXT}}"
            selectionColor: "{{PINK}}"
            selectedTextColor: "{{CRUST}}"
            echoMode: field.secret ? TextInput.Password : TextInput.Normal
            passwordCharacter: "•"
            cursorDelegate: Rectangle {
                width: 2 * {{FRAME_PX}}
                color: "{{PINK}}"
                visible: input.activeFocus && blink.on
            }
            Timer {
                id: blink
                property bool on: true
                interval: 530; repeat: true; running: input.activeFocus
                onTriggered: on = !on
            }
            onAccepted: field.accepted()
            Keys.onEscapePressed: text = ""
        }
    }

    component PixelButton: Item {
        id: button
        property string text
        property bool accent: false
        property string icon: ""
        signal clicked()
        width: icon ? Math.max(glyph.width, label.implicitWidth) + 2 * root.em
                    : label.implicitWidth + 4 * root.em
        height: icon ? glyph.height + label.implicitHeight + 3 * root.em : 4 * root.em
        activeFocusOnTab: true
        Keys.onReturnPressed: clicked()
        Keys.onEnterPressed: clicked()
        Keys.onSpacePressed: clicked()

        Frame {
            anchors.fill: parent
            visible: !button.icon || mouse.containsMouse || button.activeFocus
            source: button.accent
                    ? (mouse.containsMouse || button.activeFocus ? "images/accent-hover.png" : "images/accent.png")
                    : mouse.pressed ? "images/button-pressed.png"
                    : mouse.containsMouse || button.activeFocus ? "images/button-hover.png" : "images/button.png"
        }
        Image {
            id: glyph
            visible: button.icon !== ""
            source: button.icon
            smooth: false
            width: {{ICON_PX}}; height: {{ICON_PX}}
            x: Math.round((parent.width - width) / 2)
            y: root.em
        }
        PixelText {
            id: label
            text: button.text
            color: button.accent ? "{{CRUST}}" : "{{SUBTEXT}}"
            x: Math.round((parent.width - implicitWidth) / 2)
            y: button.icon ? glyph.y + glyph.height + Math.round(root.em / 2)
                           : Math.round((parent.height - implicitHeight) / 2)
        }
        MouseArea {
            id: mouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: button.clicked()
        }
    }

    Component.onCompleted: {
        if (user.text === "") user.forceActiveFocus()
        else password.forceActiveFocus()
    }
}
'''

POWER_QML = '''                PixelButton {
                    visible: sddm.%(can)s
                    icon: "images/%(key)s.png"
                    text: "%(label)s"
                    onClicked: sddm.%(call)s()
                }'''


def main_qml(card_cut, small_cut):
    power = "\n".join(POWER_QML % dict(key=k, label=label, can=can, call=call)
                      for k, _, label, can, call in POWER)
    subs = {
        "VOID": P.VOID, "CRUST": P.CRUST, "TEXT": P.TEXT, "SUBTEXT": P.SUBTEXT,
        "OVERLAY1": P.OVERLAY1, "SURFACE1": P.SURFACE1, "PINK": P.PINK, "RED": P.RED,
        "AMBER": P.AMBER, "CARD_CUT": card_cut, "SMALL_CUT": small_cut, "FRAME_PX": FRAME_PX, "ICON_PX": ICON_PX,
        "ART_W": LF.ART_W, "ART_H": LF.ART_H, "FRAMES": LF.FRAMES, "FRAME_MS": LF.FRAME_MS,
        "ARTS": arts_js(), "POWER": power,
        "TIME_FORMAT": "HH:mm", "DATE_FORMAT": "dddd d MMMM",
    }
    qml = MAIN_QML
    for key, value in subs.items():
        qml = qml.replace("{{%s}}" % key, str(value))
    assert "{{" not in qml
    return qml


def metadata():
    return "\n".join([
        "[SddmGreeterTheme]",
        "Name=%s" % P.NAME,
        "Description=Pixel-art dusk, the theme's orrery and a pixel login card",
        "Author=%s" % P.AUTHOR,
        "License=GPL-3.0-or-later",
        "Type=sddm-theme",
        "Version=%s" % P.VERSION,
        "Website=https://github.com/alexsson-xexpanderx/kde-plasma-themes/tree/main/Retrograde",
        "Screenshot=preview.png",
        "MainScript=Main.qml",
        "ConfigFile=theme.conf",
        "Theme-Id=%s" % P.NAME,
        "Theme-API=2.0",
        "QtVersion=6",
        "",
    ])


def build(out):
    root = Path(out) / "sddm" / P.NAME
    preview = root / "preview.png"
    kept = preview.read_bytes() if preview.exists() else None   # a screenshot; made separately
    if root.exists():
        shutil.rmtree(root)
    images = root / "images"
    images.mkdir(parents=True)
    (root / "fonts").mkdir()
    if kept:
        preview.write_bytes(kept)

    cuts = {}
    for name, f in FRAMES.items():
        im, cuts[name] = frame_image(f)
        im.save(images / (name + ".png"), optimize=True)
    for wd, ht, sc in ARTS:
        _, art = W.render(wd, ht, sc)
        art.save(images / ("sky-%dx%d.png" % art.size), optimize=True)
    LF.sprite_sheet().save(images / "orrery.png", optimize=True)
    for key, icon, *_ in POWER:
        subprocess.run(["rsvg-convert", "-w", str(ICON_PX), "-h", str(ICON_PX),
                        "-o", str(images / (key + ".png")), str(ICONS / (icon + ".svg"))],
                       check=True)
    glyph_image(TR.KEYBOARD, P.SUBTEXT).save(images / "keyboard.png", optimize=True)
    glyph_image(TR.KEYBOARD, P.PINK).save(images / "keyboard-on.png", optimize=True)
    for name in FN.FILES:
        shutil.copy2(HERE / "fonts" / name, root / "fonts" / name)

    (root / "Main.qml").write_text(main_qml(cuts["card"], cuts["field"]))
    (root / "Keyboard.qml").write_text(KEYBOARD_QML)
    (root / "metadata.desktop").write_text(metadata())
    (root / "theme.conf").write_text("[General]\n")


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "theme")
