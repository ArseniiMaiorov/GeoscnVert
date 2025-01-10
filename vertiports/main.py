import sys
import re
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtGui import QIcon
from led_controller import STMLedController
from device_scanner import DeviceScanner
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class LedController(QObject):
    connectionStatusChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.led = None
        self.deviceScanner = DeviceScanner()
        self.deviceScanner.deviceFound.connect(self.onDeviceFound)
        self.deviceScanner.scanCompleted.connect(self.onScanCompleted)
        self.foundDevices = []

    @pyqtSlot(str, int)
    def connect(self, ip, port):
        """Установка соединения с контроллером."""
        self.connectionStatusChanged.emit("connecting")
        validIp, formattedIp = self.validateAndFormatIp(ip)
        if not validIp:
            logging.error(f"Invalid IP address: {ip}")
            self.connectionStatusChanged.emit("disconnected")
            return
        try:
            self.led = STMLedController(formattedIp, port)
            status = "connected" if self.led.connected else "disconnected"
            self.connectionStatusChanged.emit(status)
            logging.info(f"Connection status: {status}")
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            self.connectionStatusChanged.emit("disconnected")

    @pyqtSlot(int, int, int, int, int)
    def changeVertiport(self, id, status, r, g, b):
        """Изменение параметров порта."""
        if self.led:
            self.led.changeVertiport(id, status, r, g, b)

    @pyqtSlot(str, result=bool)
    def isValidIp(self, ip):
        """Проверка корректности IP-адреса."""
        pattern = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
        return bool(pattern.match(ip)) and all(0 <= int(octet) <= 255 for octet in ip.split("."))

    def validateAndFormatIp(self, ip):
        """Проверяет и приводит IP к стандартному виду."""
        if not self.isValidIp(ip):
            return False, ""
        return True, ".".join(str(int(octet)) for octet in ip.split("."))

    @pyqtSlot()
    def startScan(self):
        """Запуск сканирования сети."""
        self.foundDevices.clear()
        self.deviceScanner.startScan()

    @pyqtSlot(str)
    def onDeviceFound(self, ip):
        """Обработка события нахождения устройства."""
        self.foundDevices.append(ip)
        self.connectionStatusChanged.emit(f"auto_connected:{ip}")
        logging.info(f"Device found at {ip}")
        self.updateDeviceList()

    @pyqtSlot(bool)
    def onScanCompleted(self, found):
        """Обработка события завершения сканирования."""
        if not found:
            self.connectionStatusChanged.emit("no_devices_found")
            logging.info("No devices found.")

    def updateDeviceList(self):
        """Обновление списка найденных устройств."""
        deviceModel = self.parent().findChild(QObject, "deviceModel")
        if deviceModel:
            deviceModel.clear()
            for device in self.foundDevices:
                deviceModel.appendRow({"text": device})

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon('pictures/Geo_Logo.jpg'))

    engine = QQmlApplicationEngine()
    engine.load('qml/main.qml')
    ledController = LedController()
    engine.rootContext().setContextProperty("ledController", ledController)

    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())
