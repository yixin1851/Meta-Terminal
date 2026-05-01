from PySide6.QtCore import QObject, Signal
from core.serial_worker import SerialWorker


class SerialSession(QObject):
    data_received = Signal(bytes)

    def __init__(self, port: str, baud: int):
        super().__init__()
        self.port = port
        self.baud = baud

        self.worker = SerialWorker()
        self.worker.data_received.connect(self.data_received)

    def open(self):
        self.worker.open(self.port, self.baud)

    def close(self):
        self.worker.close()

    def send(self, data: bytes):
        self.worker.send(data)

    def is_running(self):
        return self.worker.running