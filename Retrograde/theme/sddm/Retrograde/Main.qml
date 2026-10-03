/*
    Retrograde login screen (SDDM): the wallpaper, the splash's orrery over a
    clock, and a pixel login card in the theme's pixel font.
    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#0A0913"

    // Departure Mono is drawn eleven pixels to the em and is sharp only at
    // whole multiples of that, on whole pixels.
    readonly property int em: 11
    // The unstretched edge of the card's frame and of the small frames.
    readonly property int border: 12
    readonly property bool primary: typeof primaryScreen === "undefined" || primaryScreen

    property int sessionIndex: sessionModel.lastIndex
    property var sessionNames: []
    property string message: ""
    property color messageColour: "#FF4F6A"

    FontLoader { id: pixelFont; source: "fonts/DepartureMono-Regular.otf" }
    readonly property string family: pixelFont.status === FontLoader.Ready
                                     ? pixelFont.font.family : "monospace"

    component PixelText: Text {
        font.family: root.family
        font.pixelSize: 2 * root.em
        font.hintingPreference: Font.PreferNoHinting
        renderType: Text.NativeRendering
        color: "#E7E4F6"
    }

    component Frame: BorderImage {
        property int cut: 8
        border { left: cut; top: cut; right: cut; bottom: cut }
        horizontalTileMode: BorderImage.Stretch
        verticalTileMode: BorderImage.Stretch
        smooth: false
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            password.text = ""
            root.messageColour = "#FF4F6A"
            root.message = "Login failed"
            password.forceActiveFocus()
        }
        function onInformationMessage(message) {
            root.messageColour = "#FFAE5C"
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
    readonly property var arts: [ { w: 860, h: 360, file: "images/sky-860x360.png" }, { w: 854, h: 360, file: "images/sky-854x360.png" }, { w: 1280, h: 360, file: "images/sky-1280x360.png" }, { w: 640, h: 360, file: "images/sky-640x360.png" }, { w: 640, h: 400, file: "images/sky-640x400.png" }, { w: 683, h: 384, file: "images/sky-683x384.png" } ]

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
            width: 112 * root.pixel
            height: 64 * root.pixel
            source: "images/orrery.png"
            frameWidth: 112
            frameHeight: 64
            frameCount: 72
            frameDuration: 45
            interpolate: false
            smooth: false
            loops: AnimatedSprite.Infinite
            running: true
        }

        PixelText {
            id: clock
            anchors.horizontalCenter: parent.horizontalCenter
            font.pixelSize: 8 * root.em
            text: Qt.formatTime(new Date(), "HH:mm")
        }

        PixelText {
            id: date
            anchors.horizontalCenter: parent.horizontalCenter
            color: "#AAA5CA"
            text: Qt.formatDate(new Date(), "dddd d MMMM")
        }

        Timer {
            interval: 1000; repeat: true; running: true
            onTriggered: {
                var now = new Date()
                clock.text = Qt.formatTime(now, "HH:mm")
                date.text = Qt.formatDate(now, "dddd d MMMM")
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
            x: 3 * 2; y: 3 * 2
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
                color: "#7E78A2"
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
                    color: keyboard.capsLock ? "#FFAE5C" : root.messageColour
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
                    color: sessionMouse.containsMouse || session.activeFocus ? "#E7E4F6" : "#AAA5CA"
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
                        color: layoutMouse.containsMouse ? "#E7E4F6" : "#AAA5CA"
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

            Rectangle { width: parent.width; height: 2; color: "#312D4A" }

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 2 * root.em
                PixelButton {
                    visible: sddm.canSuspend
                    icon: "images/suspend.png"
                    text: "Suspend"
                    onClicked: sddm.suspend()
                }
                PixelButton {
                    visible: sddm.canReboot
                    icon: "images/reboot.png"
                    text: "Restart"
                    onClicked: sddm.reboot()
                }
                PixelButton {
                    visible: sddm.canPowerOff
                    icon: "images/shutdown.png"
                    text: "Shut down"
                    onClicked: sddm.powerOff()
                }
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
            color: "#7E78A2"
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
            color: "#E7E4F6"
            selectionColor: "#FF5C8A"
            selectedTextColor: "#100E1C"
            echoMode: field.secret ? TextInput.Password : TextInput.Normal
            passwordCharacter: "•"
            cursorDelegate: Rectangle {
                width: 2 * 2
                color: "#FF5C8A"
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
            width: 48; height: 48
            x: Math.round((parent.width - width) / 2)
            y: root.em
        }
        PixelText {
            id: label
            text: button.text
            color: button.accent ? "#100E1C" : "#AAA5CA"
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
