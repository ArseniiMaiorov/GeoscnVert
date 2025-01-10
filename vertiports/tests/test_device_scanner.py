import unittest
from device_scanner import DeviceScanner

class TestDeviceScanner(unittest.TestCase):
    def testGetLocalIp(self):
        scanner = DeviceScanner()
        ip = scanner._getLocalIp()  # Используем приватный метод для тестирования
        self.assertIsNotNone(ip)
        self.assertNotEqual(ip, "")

if __name__ == '__main__':
    unittest.main()
