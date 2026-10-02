/*
    Retrograde splash: a pixel-art orrery over the night sky.
    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    color: "#0A0913"

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
            width: 112 * content.pixel
            height: 64 * content.pixel
            source: "images/orrery.png"
            frameWidth: 112
            frameHeight: 64
            frameCount: 72
            frameDuration: 45
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
            color: "#E7E4F6"
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
                    color: index < root.stage ? ["#C3A6FF", "#FF5C8A", "#FF8266", "#FFAE5C", "#FFD685"][index % 5] : "#312D4A"
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
