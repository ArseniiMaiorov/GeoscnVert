import socket
import threading
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class STMLedController:
    """Класс для управления RGB лентами через TCP-контроллер."""

    class VertiportCommand:
        """Команда управления одним портом."""
        def __init__(self, status=0, r=0, g=0, b=0):
            self.status = status
            self.r = r
            self.g = g
            self.b = b

    def __init__(self, ip=None, port=None):
        # Инициализация подключения и основных параметров
        self.ip = ip
        self.port = port
        self.connectTimeout = 2  # Сократили время для подключения
        self.communicator = self._createClient(ip=self.ip, port=self.port)
        self.connected = self.communicator is not None
        if self.connected:
            logging.info("Connected to device: %s", hex(self._whoIAm()))

        # Инициализация команд для каждого порта
        self.vertiportsCommand = [self.VertiportCommand() for _ in range(6)]
        self.lastCommand = None
        self.lastVertiportId = None

        # Таймер для восстановления соединения
        self.reconnectTimer = None
        self.startReconnectTimer()

    def startReconnectTimer(self):
        """Запуск таймера повторного подключения."""
        if self.reconnectTimer is None or not self.reconnectTimer.is_alive():  # Исправил имя метода на is_alive
            self.reconnectTimer = threading.Timer(5, self.reconnect)
            self.reconnectTimer.start()

    def stopReconnectTimer(self):
        """Остановка таймера повторного подключения."""
        if self.reconnectTimer:
            self.reconnectTimer.cancel()

    def _createClient(self, ip, port):
        """Создание TCP-клиента для подключения к контроллеру."""
        logging.info(f"Creating connection to {ip}:{port}")
        communicator = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            communicator.connect((ip, port))
            return communicator
        except (OSError, ConnectionRefusedError) as e:
            logging.error(f"Failed to connect to {ip}:{port}: {e}")
            return None

    def _write(self, msg):
        """Отправка сообщения на контроллер."""
        if not self.communicator:
            logging.warning("Connection lost, initiating reconnect...")
            self.startReconnectTimer()
            return
        try:
            self.communicator.sendall(msg)
        except (OSError, ConnectionResetError) as e:
            logging.error(f"Error sending data: {e}")
            self.communicator = None
            self.startReconnectTimer()

    def _read(self):
        """Чтение данных с контроллера."""
        if not self.communicator:
            return -1
        try:
            self.communicator.settimeout(self.connectTimeout)
            data = self.communicator.recv(1024)
            return data if data else -1
        except (OSError, TimeoutError):
            return -1

    def _whoIAm(self):
        """Определение устройства по уникальному идентификатору."""
        if not self.communicator:
            return -1
        self._write(bytes([0x42, 0x42, 0x00, 0xff]))
        response = self._read()
        return response[0] if response != -1 else -1

    def changeVertiport(self, id, status, r, g, b):
        """Изменение состояния и цвета для указанного порта."""
        self.lastCommand = (id, status, r, g, b)
        self.lastVertiportId = id
        self._write(bytes([0x7e, id, status, r, g, b]))
        logging.info(f"Changed vertiport {id} to status={status}, color=({r}, {g}, {b})")

    def reconnect(self):
        """Попытка восстановления подключения."""
        if self.communicator:
            return
        logging.info(f"Attempting to reconnect to {self.ip}:{self.port}")
        self.communicator = self._createClient(self.ip, self.port)
        if self.communicator:
            logging.info("Reconnected successfully.")
            self.stopReconnectTimer()
            if self.lastCommand:
                self.changeVertiport(*self.lastCommand)
        else:
            logging.warning("Reconnect failed. Retrying...")
            self.startReconnectTimer()

    def disconnect(self):
        """Отключение от контроллера."""
        if self.communicator:
            self.communicator.close()
        self.communicator = None
        self.stopReconnectTimer()

    def testConnection(self):
        """Тестирование соединения."""
        if not self.communicator:
            logging.warning("No active connection.")
            return False
        try:
            self.communicator.sendall(b'\x00')
            return True
        except (OSError, ConnectionResetError) as e:
            logging.error(f"Connection test failed: {e}")
            return False
