import serial.tools.list_ports
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from core.session_manager import SessionManager
from ui.terminal_view import TerminalView
from ui.tab_widget import SessionTabWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.resize(1200, 800)

        self.session_manager = SessionManager()
        self.sessions_ui = {}  # port -> terminal

        self.setup_ui()

    def setup_ui(self):
        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.layout = QVBoxLayout(self.container)

        # ---- toolbar ----
        top = QHBoxLayout()

        self.combo_port = QComboBox()
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["9600","115200","921600"])

        self.btn_open = QPushButton("打开串口")
        self.btn_open.clicked.connect(self.open_session)

        self.refresh_ports()

        top.addWidget(self.combo_port)
        top.addWidget(self.combo_baud)
        top.addWidget(self.btn_open)

        self.layout.addLayout(top)

        # ---- tabs ----
        self.tabs = SessionTabWidget()
        self.layout.addWidget(self.tabs)

    def refresh_ports(self):
        self.combo_port.clear()
        for p in serial.tools.list_ports.comports():
            self.combo_port.addItem(p.device, p.device)

    # ===== 核心：打开新Session =====
    def open_session(self):
        port = self.combo_port.currentData()
        baud = int(self.combo_baud.currentText())

        if not port:
            return

        # 1. 创建 session
        session = self.session_manager.create_session(port, baud)

        # 2. UI terminal
        terminal = TerminalView()

        # 3. 绑定
        session.data_received.connect(terminal.append_data)
        terminal.send_data.connect(session.send)

        # 4. 加入tab
        self.tabs.add_session(port, terminal)

        self.sessions_ui[port] = terminal