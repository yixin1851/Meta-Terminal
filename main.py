
# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。

import sys
import serial
import threading
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class SerialWorker(QObject):
    """串口通信后台线程"""
    data_received = Signal(bytes)

    def __init__(self, port, baud):
        super().__init__()
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.running = True

    def run(self):
        while self.running:
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting)
                self.data_received.emit(data)

    def send(self, data):
        if self.ser and self.ser.is_open:
            self.ser.write(data)


class XSerialTerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("X-Serial Pro")
        self.resize(1000, 700)
        self.init_ui()
        self.apply_xshell_style()

    def init_ui(self):
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # 1. 左侧会话列表 (Xshell 风格)
        self.session_list = QListWidget()
        self.session_list.setFixedWidth(150)
        self.session_list.addItem("STM32_Dev_01")

        # 2. 中间终端 (类似 Xshell)
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background-color: #1E1E1E; color: #D4D4D4; font-family: 'Consolas';")

        # 3. 底部发送区 (SSCOM 风格)
        self.input_area = QLineEdit()
        self.send_btn = QPushButton("发送")
        self.script_btn = QPushButton("运行脚本")
        self.script_btn.clicked.connect(self.run_python_script)

        # 组装
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.terminal)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_area)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.script_btn)

        right_layout.addLayout(input_layout)

        layout.addWidget(self.session_list)
        layout.addLayout(right_layout)

    def apply_xshell_style(self):
        # 简单的 QSS 模拟 Xshell 深色主题
        self.setStyleSheet("""
            QMainWindow { background-color: #2D2D2D; }
            QListWidget { background-color: #252526; color: #CCCCCC; border: none; }
            QPushButton { background-color: #3E3E3E; color: white; border: 1px solid #555; padding: 5px; }
            QPushButton:hover { background-color: #505050; }
        """)

    def run_python_script(self):
        """支持外部 Python 脚本自动化控制"""
        script_content = """
# 示例脚本内容
import time
for i in range(3):
    terminal.append_text(f"Auto-Sending Command {i}...")
    # 这里可以调用底层的 send 函数
    time.sleep(1)
        """
        # 注入局部变量让脚本可以操作 UI 或串口
        local_vars = {"terminal": self}
        try:
            exec(script_content, {}, local_vars)
        except Exception as e:
            self.terminal.appendPlainText(f"脚本执行错误: {str(e)}")

    def append_text(self, text):
        self.terminal.appendPlainText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = XSerialTerminal()
    window.show()
    sys.exit(app.exec())