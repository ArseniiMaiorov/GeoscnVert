import sys
import re
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtGui import QIcon
from led_controller import STMLedController
from device_scanner import DeviceScanner

class LedController(QObject):
    connectionStatusChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.led = None
        self.device_scanner = DeviceScanner()
        self.device_scanner.deviceFound.connect(self._handle_device_found)
        self.device_scanner.scanCompleted.connect(self._handle_scan_completed)

    @pyqtSlot(str, int)
    def connect(self, ip, port):
        """Установка соединения с контроллером."""
        self.connectionStatusChanged.emit("connecting")
        valid_ip, formatted_ip = self._validate_and_format_ip(ip)
        if not valid_ip:
            self.connectionStatusChanged.emit("disconnected")
            return
        
        try:
            self.led = STMLedController(formatted_ip, port)
            self.connectionStatusChanged.emit("connected" if self.led.connected else "disconnected")
        except Exception:
            self.connectionStatusChanged.emit("disconnected")

    @pyqtSlot(int, int, int, int, int)
    def change_vertiport(self, id, status, r, g, b):
        """Изменение параметров порта."""
        if self.led:
            self.led.change_vertiport(id, status, r, g, b)

    @pyqtSlot(str, result=bool)
    def is_valid_ip(self, ip):
        """Проверка корректности IP-адреса."""
        pattern = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
        return bool(pattern.match(ip)) and all(0 <= int(octet) <= 255 for octet in ip.split("."))

    def _validate_and_format_ip(self, ip):
        """Проверка и приведение IP-адреса к стандартному виду."""
        if not self.is_valid_ip(ip):
            return False, ""
        return True, ".".join(str(int(octet)) for octet in ip.split("."))

    @pyqtSlot()
    def start_scan(self):
        """Запуск сканирования сети."""
        self.device_scanner.start_scan()

    @pyqtSlot(str)
    def _handle_device_found(self, ip):
        """Обработка события нахождения устройства."""
        self.connectionStatusChanged.emit(f"auto_connected:{ip}")
        self.connect(ip, 502)

    @pyqtSlot(bool)
    def _handle_scan_completed(self, found):
        """Обработка завершения сканирования."""
        if not found:
            self.connectionStatusChanged.emit("no_devices_found")

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('pictures/Geo_Logo.jpg'))

    engine = QQmlApplicationEngine()
    engine.load('main.qml')
    
    if not engine.rootObjects():
        sys.exit(-1)

    led_controller = LedController()
    engine.rootContext().setContextProperty("ledController", led_controller)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

