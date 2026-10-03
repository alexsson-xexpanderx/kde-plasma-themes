import QtQuick
import QtQuick.VirtualKeyboard

InputPanel {
    property bool activated: false
    active: activated && Qt.inputMethod.visible
    visible: active
}
