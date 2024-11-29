import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import QtQuick.Layouts 1.15

Window {
    id: mainWindow
    width: 640
    height: 400
    visible: true
    title: qsTr("Управление RGB-подсветкой вертипортов")

    property color color1: "white"
    property color color2: "white"
    property color color3: "white"
    property color color4: "white"
    property color color5: "white"
    property color color6: "white"

    Rectangle {
        id: topPanel
        width: parent.width
        height: 100
        color: "#5a5a5a"

        Text {
            text: "Установите соединение"
            font.family: "Roboto"
            font.pixelSize: 15
            font.bold: true
            color: "white"
            anchors {
                top: parent.top
                left: parent.left
                leftMargin: 20
                topMargin: 20
            }
        }

        Rectangle {
            width: parent.width
            height: 30
            color: "#5a5a5a"
            anchors {
                bottom: parent.bottom
                bottomMargin: 20
                left: parent.left
                leftMargin: 20
                right: parent.right
                rightMargin: 20
            }

            Button {
                id: connectButton
                width: 120
                height: parent.height
                font.family: "Roboto"
                text: "подключиться"
                font.pixelSize: 13
                font.bold: true

                anchors {
                    verticalCenter: parent.verticalCenter
                    right: parent.right
                    rightMargin: 40
                }

                onClicked: {
                    var ipAddress = enterIPAdress.text.trim();

                    # Проверяем, есть ли подстановочные символы или поле пустое
                    if (ipAddress === "" || ipAddress.includes("_")) {
                        showErrorDialog("Поле IP не может быть пустым.");
                    } else if (!ledController.is_valid_ip(ipAddress)) {
                        showErrorDialog("Неверный формат IP-адреса");
                    } else {
                        ledController.connect(ipAddress, 502); # Устанавливаем соединение
                    }
                }
            }

            Button {
                id: scanButton
                width: 120
                height: parent.height
                font.family: "Roboto"
                text: "автопоиск"
                font.pixelSize: 13
                font.bold: true

                anchors {
                    verticalCenter: parent.verticalCenter
                    right: connectButton.left
                    rightMargin: 10
                }

                onClicked: {
                    ledController.start_scan();
                }
            }

            Rectangle {
                id: connectionIndicator
                width: 20
                height: 20
                radius: width / 2
                color: "grey"
                border.color: "#3e3e3e"
                border.width: 2
                anchors {
                    verticalCenter: connectButton.verticalCenter
                    left: connectButton.right
                    leftMargin: 10
                }

                Connections {
                    target: ledController
                    onConnectionStatusChanged: (newStatus) => {
                        connectionIndicator.color = newStatus === "connected" ? "green" : "red";
                        if (newStatus === "device_found") {
                            enterIPAdress.text = newStatus;
                        } else if (newStatus === "no_devices_found") {
                            showErrorDialog("Устройства не найдены.");
                        } else if (newStatus.startsWith("auto_connected:")) {
                            var ip = newStatus.split(":")[1];
                            enterIPAdress.text = ip
                            showSuccessDialog("Автоподключение выполнено успешно!", ip);
                        }
                    }
                }
            }

            Text {
                id: labelIP
                text: "IP"
                font.family: "Roboto"
                font.pixelSize: 14
                font.bold: true
                color: "white"
                anchors {
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    leftMargin: 20
                }
            }

            TextField {
                id: enterIPAdress
                width: 200
                height: parent.height
                horizontalAlignment: TextField.AlignHCenter
                verticalAlignment: TextField.AlignVCenter
                inputMask: "000.000.000.000;_"
                anchors {
                    verticalCenter: parent.verticalCenter
                    left: labelIP.right
                    leftMargin: 40
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 2
            color: "#3e3e3e"
            anchors {
                bottom: parent.bottom
            }
        }
    }

    Rectangle {
        id: bottomLine
        width: parent.width
        height: 20
        color: "#3e3e3e"
        anchors {
            bottom: parent.bottom
        }
    }

    Rectangle {
        id: choiceVertiports
        width: parent.width
        color: "#aba9ab"
        anchors {
            top: topPanel.bottom
            bottom: bottomLine.top
        }

        Text {
            text: "Выберите вертипорт и режим работы"
            font.family: "Roboto"
            font.pixelSize: 15
            font.bold: true
            color: "white"
            anchors {
                top: parent.top
                left: parent.left
                leftMargin: 20
                topMargin: 20
            }
        }

        Row {
            spacing: 5
            anchors {
                fill: parent
                leftMargin: 7.5
                rightMargin: 7.5
                topMargin: 50
                bottomMargin: 10
            }

            Repeater {
                model: 6

                Rectangle {
                    width: parent.width / 6.25
                    height: parent.height
                    color: "#5a5a5a"
                    radius: 5

                    Text {
                        text: "Вертипорт " + (index + 1)
                        font.pixelSize: 14
                        font.bold: true
                        color: "white"
                        anchors {
                            horizontalCenter: parent.horizontalCenter
                            top: parent.top
                            topMargin: 10
                        }
                    }

                    Column {
                        id: columnRGB
                        spacing: 5
                        width: parent.width / 4
                        height: 90
                        anchors {
                            horizontalCenter: parent.horizontalCenter
                            verticalCenter: parent.verticalCenter
                            topMargin: 40
                            bottomMargin: 50
                        }
                    }

                    Rectangle {
                        id: selectedColorRectangle
                        width: parent.width
                        height: 25
                        color: mainWindow["color" + (index + 1)]
                        anchors {
                            top: columnRGB.bottom
                            topMargin: -95
                            left: parent.left
                            right: parent.right
                            leftMargin: 5
                            rightMargin: 5
                        }
                        border.color: "#3e3e3e"
                    }

                    Button {
                        text: "выбор цвета"
                        font.family: "Roboto"
                        onClicked: {
                            colorPickerDialog.open();
                            colorPickerDialog.activeColorProperty = "color" + (index + 1);
                            selectedColor = "white"; # Сброс цвета
                            point.x = 0; # Сброс позиции круга
                            point.y = 0; # Сброс позиции круга
                        }

                        height: 25
                        anchors {
                            top: columnRGB.bottom
                            topMargin: -65
                            left: parent.left
                            right: parent.right
                            leftMargin: 5
                            rightMargin: 5
                        }
                    }

                    ComboBox {
                        id: modeComboBox
                        width: parent.width
                        height: 25
                        anchors {
                            top: columnRGB.bottom
                            topMargin: -25
                            left: parent.left
                            right: parent.right
                            leftMargin: 5
                            rightMargin: 5
                        }
                        model: ["выключен", "статично", "мигание", "волна", "радуга"]
                    }

                    Button {
                        width: parent.width
                        height: 25
                        font.family: "Roboto"
                        text: "старт"
                        anchors {
                            bottom: parent.bottom
                            bottomMargin: 10
                            left: parent.left
                            right: parent.right
                            leftMargin: 5
                            rightMargin: 5
                        }

                        onClicked: {
                            # Получаем текущие значения RGB из палитры
                            var r = Math.round(selectedColor.r * 255);
                            var g = Math.round(selectedColor.g * 255);
                            var b = Math.round(selectedColor.b * 255);

                            var status = modeComboBox.currentIndex;
                            ledController.change_vertiport(index, status, r, g, b);

                        }
                    }
                }
            }
        }
    }

    Rectangle {
        id: errorDialog
        width: 300
        height: 150
        color: "#ffffff"
        radius: 10
        visible: false
        anchors.centerIn: parent

        Text {
            id: errorText
            text: "Поле IP не может быть пустым."
            font.family: "Roboto"
            font.pixelSize: 14
            font.bold: true
            color: "black"
            anchors {
                centerIn: parent
                topMargin: 20
            }
        }

        Button {
            text: "ОК"
            width: 50
            anchors {
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
                bottomMargin: 10
            }
            onClicked: {
                errorDialog.visible = false;
            }
        }
    }

    Rectangle {
        id: successDialog
        width: 300
        height: 150
        color: "#ffffff"
        radius: 10
        visible: false
        anchors.centerIn: parent

        Text {
            id: successText
            text: "Автоподключение выполнено успешно!"
            font.family: "Roboto"
            font.pixelSize: 14
            font.bold: true
            color: "black"
            anchors {
                centerIn: parent
                topMargin: 20
            }
        }

        Button {
            text: "ОК"
            width: 50
            anchors {
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
                bottomMargin: 10
            }
            onClicked: {
                successDialog.visible = false;
            }
        }
    }

    Dialog {
        id: colorPickerDialog
        property string activeColorProperty: ""

        modal: true
        width: 360
        height: 360

        Canvas {
            id: palette
            anchors.fill: parent

            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);

                for (var y = 0; y < height; y++) {
                    for (var x = 0; x < width; x++) {
                        var nx = x / width;
                        var ny = y / height;

                        var r = nx * (1 - ny);
                        var g = (1 - nx) * (1 - ny);
                        var b = ny;

                        var whiteFactor = nx * ny;
                        r += whiteFactor;
                        g += whiteFactor;
                        b += whiteFactor;

                        r = Math.min(1, Math.max(0, r));
                        g = Math.min(1, Math.max(0, g));
                        b = Math.min(1, Math.max(0, b));

                        ctx.fillStyle = `rgb(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)})`;
                        ctx.fillRect(x, y, 1, 1);
                    }
                }
            }
        }

        MouseArea {
            id: paletteArea
            anchors.fill: parent
            onPressed: updateColor(mouseX, mouseY)
            onPositionChanged: if (mouse.buttons & Qt.LeftButton) updateColor(mouseX, mouseY)
        }

        Rectangle {
            id: point
            width: 15
            height: 15
            radius: 10
            color: selectedColor
            x: Math.max(0, Math.min(palette.width - width, mouseX - width / 2))
            y: Math.max(0, Math.min(palette.height - height, mouseY - height / 2))
            border.color: "black"
            border.width: 2
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 20
            spacing: 10

            Button {
                text: "выбрать"
                font.family: "Roboto"
                onClicked: {
                    mainWindow[colorPickerDialog.activeColorProperty] = selectedColor;
                    colorPickerDialog.close();
                }
            }

            Button {
                text: "отмена"
                font.family: "Roboto"
                onClicked: {
                    colorPickerDialog.close();
                }
            }
        }
    }

    property color selectedColor: "white"
    function updateColor(x, y) {
        x = Math.max(0, Math.min(x, palette.width));
        y = Math.max(0, Math.min(y, palette.height));

        let normalizedX = x / palette.width;
        let normalizedY = y / palette.height;

        let red = normalizedX * (1 - normalizedY);
        let green = (1 - normalizedX) * (1 - normalizedY);
        let blue = normalizedY;

        let whiteFactor = normalizedX * normalizedY;
        red += whiteFactor;
        green += whiteFactor;
        blue += whiteFactor;

        red = Math.min(1, Math.max(0, red));
        green = Math.min(1, Math.max(0, green));
        blue = Math.min(1, Math.max(0, blue));

        selectedColor = Qt.rgba(red, green, blue, 1);

        point.x = x - point.width / 2;
        point.y = y - point.height / 2;
    }

    # Функция для отображения диалогового окна с ошибкой
    function showErrorDialog(message) {
        errorText.text = message;
        errorDialog.visible = true;
    }

    # Функция для отображения диалогового окна с успешным подключением
    function showSuccessDialog(message, ip) {
        successText.text = message + "\nIP: " + ip;
        successDialog.visible = true;
    }
}
