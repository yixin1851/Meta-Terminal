# serial_worker.py

import serial
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal, QTimer, Slot



class SerialWorker(QThread):
    data_received = Signal(bytes)
    error = Signal(str)

    # 1. 新增一个内部信号，用于中转发送请求
    _internal_send_request = Signal(bytes)


    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.running = False
        # 2. 关键：将信号连接到实际执行发送的方法
        # QueuedConnection 确保 send 会在 SerialWorker 的子线程中执行
        self._internal_send_request.connect(self._do_send)


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

    def send_async(self, data: bytes):
        """供外部调用，触发信号"""
        self._internal_send_request.emit(data)

    def run(self):
        """线程入口：替代原来的 while 循环"""
        # 创建定时器进行轮询读取，这样不会阻塞事件循环
        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self._check_read)
        self.read_timer.setInterval(10)  # 10ms 检查一次，响应极快
        self.read_timer.start()

        # 开启事件循环：使得 _internal_send_request 信号能被处理
        self.exec()

        # 退出后清理
        self.read_timer.stop()

    def _check_read(self):
        """原 run 循环里的读取逻辑搬到这里"""
        if not self.running:
            self.quit()  # 停止事件循环
            return

        try:
            if self.serial_port and self.serial_port.is_open:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    self.data_received.emit(data)
        except Exception as e:
            self.close()
            self.running = False
            self.error.emit(str(e))  #这一定要写在最后，因为要先停止线程后发送异常


    @Slot(bytes)
    def _do_send(self, data: bytes):
        """真正的发送动作，运行在子线程"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(data)
                self.serial_port.flush()
        except Exception as e:
            self.error.emit(f"Send Error: {e}")

    # --- 兼容性封装 API ---

    def send(self, data: bytes):
        """
        兼容旧代码：现在它是异步的了。
        直接调用这个函数，它会发信号给子线程去执行发送。
        """
        if not self.is_open():
            return False
        self._internal_send_request.emit(data)
        return True

    def open(self, port, baud, bytesize=8, parity='N', stopbits=1):
        """保持原样，内部逻辑不变"""
        try:
            # 这里的解析逻辑保持你原来的即可
            p = {'N': serial.PARITY_NONE, 'E': serial.PARITY_EVEN, 'O': serial.PARITY_ODD}.get(parity,
                                                                                               serial.PARITY_NONE)
            s = {1.0: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2.0: serial.STOPBITS_TWO}.get(
                float(stopbits), serial.STOPBITS_ONE)

            self.serial_port = serial.Serial(
                port=port, baudrate=baud, bytesize=bytesize,
                parity=p, stopbits=s, timeout=0.1
            )
            self.running = True
            self.start()  # 启动线程，执行 run()
            return True
        except Exception as e:
            self.serial_port = None
            self.running = False
            raise e

    def close(self):
        self.running = False

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        if hasattr(self, "read_timer"):
            self.read_timer.stop()

        self.quit()
        self.wait()  # ✅ 等线程彻底退出



    def is_open(self):
        return self.serial_port is not None and self.serial_port.is_open

    @staticmethod
    def list_ports():
        return [p.device for p in serial.tools.list_ports.comports()]