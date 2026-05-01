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

    def open(self, port, baud):
        try:
            self.serial_port = serial.Serial(port, baud, timeout=0.1)
            self.running = True
            if not self.isRunning():
                self.start()
        except Exception as e:
            self.error.emit(str(e))

    def close(self):
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

    def send(self, data: bytes):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(data)

    def run(self):
        while self.running:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    self.data_received.emit(data)
            except Exception as e:
                self.error.emit(str(e))
                self.running = False

    @staticmethod
    def list_ports():
        return [p.device for p in serial.tools.list_ports.comports()]