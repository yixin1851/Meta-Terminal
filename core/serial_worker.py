# serial_worker.py

import serial
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal


class SerialWorker(QThread):
    data_received = Signal(bytes)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.running = False


    import serial

    def _parse_parity(self, p):
        return {
            'N': serial.PARITY_NONE,
            'E': serial.PARITY_EVEN,
            'O': serial.PARITY_ODD
        }.get(p, serial.PARITY_NONE)

    def _parse_stopbits(self, s):
        return {
            1.0: serial.STOPBITS_ONE,
            1.5: serial.STOPBITS_ONE_POINT_FIVE,
            2.0: serial.STOPBITS_TWO
        }.get(float(s), serial.STOPBITS_ONE)

    def open(self, port, baud, bytesize=8, parity='N', stopbits=1):
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=bytesize,
                parity=self._parse_parity(parity),
                stopbits=self._parse_stopbits(stopbits),
                timeout=0.1
            )

            self.running = True
            self.start()  # <--- 关键！启动 QThread 的 run() 循环
            print("[OPEN OK]", self.serial_port)

        except Exception as e:
            self.serial_port = None
            self.running = False
            print("[OPEN FAIL]", e)
            raise

    def close(self):
        self.running = False
        if hasattr(self, "serial_port") and self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None

    def send(self, data: bytes):
        print("DEBUG serial_port:", self.serial_port)
        print("DEBUG type:", type(self.serial_port))
        if not self.serial_port:
            print("[SEND FAIL] no serial_port")
            return False

        if not self.serial_port.is_open:
            print("[SEND FAIL] port not open")
            return False

        try:
            self.serial_port.write(data)
            self.serial_port.flush()
            return True

        except Exception as e:
            print("[SEND ERROR]", e)
            return False


    def run(self):
        while self.running:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    self.data_received.emit(data)
            except Exception as e:
                self.error.emit(str(e))
                self.running = False

    def is_open(self):
        return self.serial_port is not None and self.serial_port.is_open

    @staticmethod
    def list_ports():
        return [p.device for p in serial.tools.list_ports.comports()]