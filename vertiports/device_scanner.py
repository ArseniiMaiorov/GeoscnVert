import socket
import threading
import logging
import platform
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from concurrent.futures import ThreadPoolExecutor

try:
    import psutil
except ImportError:
    psutil = None

try:
    import netifaces
except ImportError:
    netifaces = None

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DeviceScanner(QObject):
    deviceFound = pyqtSignal(str)
    scanCompleted = pyqtSignal(bool)

    def __init__(self, port=502, parent=None):
        super().__init__(parent)
        self.port = port

    def sendRequest(self, ip):
        """Отправляет запрос на указанный IP-адрес и возвращает его, если устройство найдено."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((ip, self.port))
                s.sendall(bytes([0x42, 0x42, 0x00, 0xff]))
                data = s.recv(1024)
                if data:
                    logging.info(f"Device found at {ip}:{self.port}")
                    return ip
        except (socket.timeout, socket.error):
            pass
        return None

    def _getLocalIp(self):
        """Определяет локальный IP-адрес на основе ОС."""
        if psutil:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                        return addr.address
        if netifaces:
            for interface in netifaces.interfaces():
                addresses = netifaces.ifaddresses(interface)
                ipv4 = addresses.get(netifaces.AF_INET)
                if ipv4:
                    for addr in ipv4:
                        ip = addr['addr']
                        if not ip.startswith('127.'):
                            return ip
        return socket.gethostbyname(socket.gethostname())

    def _getLocalIpBase(self):
        """Возвращает базовую часть локального IP-адреса."""
        localIp = self._getLocalIp()
        if not localIp:
            logging.error("Unable to determine local IP address.")
            return None
        return '.'.join(localIp.split('.')[:-1])

    def scanNetwork(self):
        """Сканирует сеть в поисках устройств."""
        foundDevices = []

        def scanIp(ip):
            deviceIp = self.sendRequest(ip)
            if deviceIp:
                foundDevices.append(deviceIp)
                self.deviceFound.emit(deviceIp)

        baseIp = self._getLocalIpBase()
        if not baseIp:
            logging.error("No valid network base for scanning.")
            self.scanCompleted.emit(False)
            return

        logging.info(f"Scanning network base: {baseIp}.x")
        with ThreadPoolExecutor(max_workers=254) as executor:
            futures = [executor.submit(scanIp, f"{baseIp}.{i}") for i in range(1, 255)]
            for future in futures:
                future.result()

        self.scanCompleted.emit(bool(foundDevices))

    @pyqtSlot()
    def startScan(self):
        """Запускает сканирование в отдельном потоке."""
        threading.Thread(target=self.scanNetwork).start()
