import socket
import threading
import logging
import platform



try:
    import psutil  # Для получения IP-адреса на Windows
except ImportError:
    psutil = None

try:
    import netifaces  # Для получения IP-адреса на Linux
except ImportError:
    netifaces = None

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class DeviceScanner:
    def __init__(self, port=502):
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
                    logging.info(f"Device found at {ip}:{self.port}")
                    return ip
        except (socket.timeout, socket.error):
            pass
        return None

    def get_local_ip(self):
        """Получает локальный IP-адрес с учетом ОС."""
        if psutil:  # Для Windows
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                        return addr.address
        if netifaces:  # Для Linux
            for interface in netifaces.interfaces():
                addresses = netifaces.ifaddresses(interface)
                ipv4 = addresses.get(netifaces.AF_INET)
                if ipv4:
                    for addr in ipv4:
                        ip = addr['addr']
                        if not ip.startswith('127.'):
                            return ip
        # Резервный метод
        return socket.gethostbyname(socket.gethostname())

    def get_local_ip_base(self):
        """Возвращает базовую часть IP-адреса."""
        local_ip = self.get_local_ip()
        if not local_ip:
            logging.error("Unable to determine local IP address.")
            return None
        return '.'.join(local_ip.split('.')[:-1])

    def scan_network(self):
        found_devices = []
        threads = []

        def scan_ip(ip):
            device_ip = self.send_request(ip)
            if device_ip:
                found_devices.append(device_ip)

        base_ip = self.get_local_ip_base()
        if not base_ip:
            logging.error("No valid network base for scanning.")
            return

        logging.info(f"Scanning network base: {base_ip}.x")
        # Сканируем IP-адреса в диапазоне от 1 до 254
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            thread = threading.Thread(target=scan_ip, args=(ip,))
            threads.append(thread)
            thread.start()

        # Ожидаем завершения всех потоков
        for thread in threads:
            thread.join()

        # Вывод результатов
        if found_devices:
            print("Found devices:")
            for device in found_devices:
                print(f" - {device}")
        else:
            print("No devices found.")

    def start_scan(self):
        """Запускает сканирование сети."""
        threading.Thread(target=self.scan_network).start()


# Запуск сканера
if __name__ == "__main__":
    scanner = DeviceScanner(port=502)
    print("Starting network scan...")
    scanner.scan_network()
    print("Network scan completed.")
