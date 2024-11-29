import socket
import threading
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

class DeviceScanner(QObject):
    deviceFound = pyqtSignal(str)
    scanCompleted = pyqtSignal(bool)

    def __init__(self, port=502, parent=None):
        super().__init__(parent)
        self.port = port

    def send_request(self, ip):
        try:
            # Создаем сокет и устанавливаем таймаут
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((ip, self.port))
                # Отправляем запрос на устройство
                s.sendall(bytes([0x42, 0x42, 0x00, 0xff]))
                data = s.recv(1024)
                if data:
                    return ip
        except (socket.timeout, socket.error):
            pass
        return None

    def scan_network(self):
        found_devices = []
        threads = []

        def scan_ip(ip):
            device_ip = self.send_request(ip)
            if device_ip:
                found_devices.append(device_ip)

        # Получаем локальный IP-адрес
        local_ip = self.get_local_ip()
        if not local_ip:
            self.scanCompleted.emit(False)
            return

        base_ip = '.'.join(local_ip.split('.')[:-1])

        # Сканируем IP-адреса в диапазоне от 1 до 254
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            thread = threading.Thread(target=scan_ip, args=(ip,))
            threads.append(thread)
            thread.start()

        # Ожидаем завершения всех потоков
        for thread in threads:
            thread.join()

        # Если найдены устройства, отправляем сигнал
        if found_devices:
            self.deviceFound.emit(found_devices[0])
        self.scanCompleted.emit(bool(found_devices))

    def get_local_ip(self):
        try:
            # Получаем локальный IP-адрес через сокет
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except socket.error:
            return None

    @pyqtSlot()
    def start_scan(self):
        # Запускаем сканирование сети в отдельном потоке
        threading.Thread(target=self.scan_network).start()

# Пример использования
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QVBoxLayout()

    scanner = DeviceScanner()
    button = QPushButton("Start Scan")
    button.clicked.connect(scanner.start_scan)

    layout.addWidget(button)
    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())
