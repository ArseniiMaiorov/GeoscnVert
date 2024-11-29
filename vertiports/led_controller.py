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
        # Инициализация подключения и основных параметров
        self.ip = ip
        self.port = port
        self.connect_timeout = 1
        self.communicator = self._create_client(ip=self.ip, port=self.port)
        self.connected = self.communicator is not None
        if self.connected:
            self._who_i_am()

        # Инициализация команд для каждого порта
        self.vertiports_command = [self.VertiportCommand() for _ in range(6)]
        self.last_command = None
        self.last_vertiport_id = None

        # Таймер для восстановления соединения
        self.reconnect_timer = None
        self.start_reconnect_timer()

    def start_reconnect_timer(self):
        if self.reconnect_timer is None or not self.reconnect_timer.is_alive():
            self.reconnect_timer = threading.Timer(1, self.reconnect)
            self.reconnect_timer.start()

    def stop_reconnect_timer(self):
        if self.reconnect_timer:
            self.reconnect_timer.cancel()

    def _create_client(self, ip, port):
        communicator = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            communicator.connect((ip, port))
            return communicator
        except (OSError, ConnectionRefusedError):
            return None

    def _send_message(self, msg):
        if not self.communicator:
            self.reconnect(msg)
            return
        try:
            self.communicator.sendall(msg)
        except (OSError, ConnectionResetError):
            self.communicator = None
            self.reconnect(msg)

    def _read(self):
        if not self.communicator:
            return -1
        try:
            self.communicator.settimeout(self.connect_timeout)
            data = self.communicator.recv(1024)
            return data if data else -1
        except (OSError, TimeoutError):
            return -1

    def _who_i_am(self):
        if not self.communicator:
            return -1
        self._send_message(bytes([0x42, 0x42, 0x00, 0xff]))
        response = self._read()
        return response[0] if response != -1 else -1

    def change_vertiport(self, id, status, r, g, b):
        self.last_command = (id, status, r, g, b)
        self.last_vertiport_id = id
        self._send_message(bytes([0x7e, id, status, r, g, b]))

    def reconnect(self, msg=None):
        if self.communicator:
            return
        self.communicator = self._create_client(self.ip, self.port)
        if self.communicator:
            self.stop_reconnect_timer()
            if self.last_command:
                self.change_vertiport(*self.last_command)
            if msg:
                self._send_message(msg)
        else:
            self.start_reconnect_timer()

    def disconnect(self):
        if self.communicator:
            self.communicator.close()
        self.communicator = None
        self.stop_reconnect_timer()

    def test_connection(self):
        if not self.communicator:
            return False
        try:
            self.communicator.sendall(b'\x00')
            return True
        except (OSError, ConnectionResetError):
            return False
