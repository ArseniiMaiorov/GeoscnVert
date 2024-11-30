import socket
import threading
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

class DeviceScanner(QObject):
    deviceFound = pyqtSignal(str)
    scanCompleted = pyqtSignal(bool)

    def __init__(self, port=502, parent=None):
        super().__init__(parent)
        self.port = port

    def _send_request(self, ip):
        """Попытка подключения к устройству и отправки запроса."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((ip, self.port))
                s.sendall(bytes([0x42, 0x42, 0x00, 0xff]))  # Отправка тестового пакета
                if s.recv(1024):  # Проверка ответа
                    return ip
        except (socket.timeout, socket.error):
            return None

    def _scan_ip(self, ip, found_devices):
        """Сканирование одного IP-адреса."""
        device_ip = self._send_request(ip)
        if device_ip:
            found_devices.append(device_ip)

    def _scan_network_range(self, base_ip, found_devices):
        """Сканирование диапазона IP-адресов в сети."""
        threads = []
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            thread = threading.Thread(target=self._scan_ip, args=(ip, found_devices))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def scan_network(self):
        """Основная функция для сканирования сети."""
        found_devices = []

        # Получаем базовый IP-адрес
        local_ip = self.get_local_ip()
        if not local_ip:
            self.scanCompleted.emit(False)
            return

        base_ip = '.'.join(local_ip.split('.')[:-1])
        self._scan_network_range(base_ip, found_devices)

        # Обработка результатов сканирования
        if found_devices:
            self.deviceFound.emit(found_devices[0])  # Отправляем первый найденный IP
        self.scanCompleted.emit(bool(found_devices))

    def get_local_ip(self):
        """Получение локального IP-адреса устройства."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except socket.error:
            return None

    @pyqtSlot()
    def start_scan(self):
        """Запуск сканирования сети в отдельном потоке."""
        threading.Thread(target=self.scan_network, daemon=True).start()

# Пример использования
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QVBoxLayout()

    scanner = DeviceScanner()

    # Обработка сигналов
    scanner.deviceFound.connect(lambda ip: print(f"Device found: {ip}"))
    scanner.scanCompleted.connect(lambda success: print("Scan completed." if success else "No devices found."))

    button = QPushButton("Start Scan")
    button.clicked.connect(scanner.start_scan)

    layout.addWidget(button)
    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())

