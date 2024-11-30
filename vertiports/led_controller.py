import socket
import threading

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
        self.ip = ip
        self.port = port
        self.connect_timeout = 1
        self.communicator = self._create_client()
        self.connected = self.communicator is not None
        self.last_command = None
        self.last_vertiport_id = None

        self.vertiports_command = [self.VertiportCommand() for _ in range(6)]

        self.reconnect_timer = None
        if self.connected:
            self._send_identification_request()
        else:
            self.start_reconnect_timer()

    def _create_client(self):
        """Создает TCP-клиент и пытается подключиться."""
        try:
            communicator = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            communicator.connect((self.ip, self.port))
            return communicator
        except (OSError, ConnectionRefusedError):
            return None

    def _send_message(self, msg):
        """Отправляет сообщение или инициирует переподключение."""
        if self.communicator:
            try:
                self.communicator.sendall(msg)
                return
            except (OSError, ConnectionResetError):
                self.communicator = None
        self.reconnect(msg)

    def _read_response(self):
        """Читает ответ от контроллера."""
        if not self.communicator:
            return -1
        try:
            self.communicator.settimeout(self.connect_timeout)
            data = self.communicator.recv(1024)
            return data if data else -1
        except (OSError, TimeoutError):
            return -1

    def _send_identification_request(self):
        """Отправляет запрос идентификации."""
        self._send_message(bytes([0x42, 0x42, 0x00, 0xff]))
        response = self._read_response()
        return response[0] if response != -1 else -1

    def change_vertiport(self, id, status, r, g, b):
        """Изменяет параметры порта."""
        self.last_command = (id, status, r, g, b)
        self._send_message(bytes([0x7e, id, status, r, g, b]))

    def reconnect(self, msg=None):
        """Переподключается к контроллеру и отправляет последнее сообщение."""
        if self.communicator:
            return
        self.communicator = self._create_client()
        if self.communicator:
            self.stop_reconnect_timer()
            if self.last_command:
                self.change_vertiport(*self.last_command)
            if msg:
                self._send_message(msg)
        else:
            self.start_reconnect_timer()

    def start_reconnect_timer(self):
        """Запускает таймер переподключения."""
        if not self.reconnect_timer or not self.reconnect_timer.is_alive():
            self.reconnect_timer = threading.Timer(1, self.reconnect)
            self.reconnect_timer.start()

    def stop_reconnect_timer(self):
        """Останавливает таймер переподключения."""
        if self.reconnect_timer:
            self.reconnect_timer.cancel()

    def disconnect(self):
        """Отключается от контроллера."""
        if self.communicator:
            self.communicator.close()
        self.communicator = None
        self.stop_reconnect_timer()

    def test_connection(self):
        """Тестирует текущее соединение."""
        if not self.communicator:
            return False
        try:
            self.communicator.sendall(b'\x00')
            return True
        except (OSError, ConnectionResetError):
            return False

