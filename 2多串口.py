import sys
import json
import os
import serial
import serial.tools.list_ports
from core.serial_worker import SerialWorker
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# --- 样式常量 ---
STYLE_DARK = """
QMainWindow { background-color: #121212; }
QPlainTextEdit { 
    background-color: #1E1E1E; 
    color: #D4D4D4; 
    font-family: 'Consolas', 'Monaco', monospace; 
    font-size: 13px;
    border: none;
    selection-background-color: #264F78;
}
#SidePanel { 
    background-color: #252526; 
    border: 1px solid #333;
}
#TopMenu { 
    background-color: #2D2D2D; 
    border-bottom: 1px solid #3E3E3E;
}
QLabel { color: #CCCCCC; font-size: 12px; }
QPushButton { 
    background-color: #333333; 
    color: white; 
    border: 1px solid #444; 
    padding: 5px 15px;
    border-radius: 3px;
}
QPushButton:hover { background-color: #444444; border: 1px solid #007ACC; }
QPushButton#IconButton { background: transparent; border: none; font-size: 18px; }
QLineEdit { background-color: #3C3C3C; color: white; border: 1px solid #555; padding: 3px; }
"""


# --- 核心组件 ---

class AnimatedPanel(QFrame):
    def __init__(self, parent, width, direction="left"):
        super().__init__(parent)
        self.setObjectName("SidePanel")
        self.panel_width = width
        self.direction = direction
        self.setFixedWidth(width)
        self.is_expanded = False

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutQuint)

    def hide_instantly(self):
        """完全隐藏，只留1像素感应区"""
        parent_w = self.parent().width() if self.parent() else 1100
        y_pos = self.y()
        # 这里关键：隐藏时要躲到视线外
        x_pos = -self.panel_width if self.direction == "left" else parent_w
        self.move(x_pos, y_pos)
        self.is_expanded = False

    def toggle(self):
        parent_w = self.parent().width()
        y_pos = self.y()
        self.animation.stop()

        if self.is_expanded:
            # 缩回逻辑：完全出界
            end_x = -self.panel_width if self.direction == "left" else parent_w
        else:
            # 展开逻辑
            end_x = 0 if self.direction == "left" else parent_w - self.panel_width

        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(end_x, y_pos))
        self.animation.start()
        self.is_expanded = not self.is_expanded


class TerminalView(QPlainTextEdit):
    """支持直接输入的终端"""
    send_data = Signal(bytes)

    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Connected... Type here to send commands directly.")

    def keyPressEvent(self, event):
        # 模拟 Xshell：捕获按键直接通过串口发送
        text = event.text()
        if text:
            self.send_data.emit(text.encode('utf-8'))
        super().keyPressEvent(event)


class Session:
    def __init__(self, port, baud, worker, terminal):
        self.port = port
        self.baud = baud
        self.worker = worker
        self.terminal = terminal


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setWindowTitle("YOD")
        self.resize(1100, 750)
        self.config_file = "config/config.json"

        self.setup_ui()
        self.load_config()
        self.setStyleSheet(STYLE_DARK)

    def setup_ui(self):
        # 1. 中央容器
        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 2. 顶部菜单栏 (可收起)
        self.top_menu = QFrame()
        self.top_menu.setObjectName("TopMenu")
        self.top_menu.setFixedHeight(50)
        top_layout = QHBoxLayout(self.top_menu)

        self.top_menu.setStyleSheet("""
        #TopMenu {
            background-color: #2b2b2b;
            border-bottom: 1px solid #444;
        }
        QPushButton {
            border: none;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #444;
        }
        """)

        self.btn_left_toggle = QPushButton("☰")
        self.btn_left_toggle.setObjectName("IconButton")
        self.btn_left_toggle.clicked.connect(lambda: self.left_panel.toggle())

        title_label = QLabel("YOD TERMINAL")
        title_label.setStyleSheet("font-weight: bold; color: #007ACC;")

        self.btn_script = QPushButton("Python 脚本")
        self.btn_script.clicked.connect(self.run_custom_script)

        self.btn_right_toggle = QPushButton("⚙")
        self.btn_right_toggle.setObjectName("IconButton")
        self.btn_right_toggle.clicked.connect(lambda: self.right_panel.toggle())

        self.btn_min = QPushButton("—")
        self.btn_max = QPushButton("□")
        self.btn_close = QPushButton("✕")

        self.btn_close.setStyleSheet("""
        QPushButton {
            color: white;
        }
        QPushButton:hover {
            background-color: red;
        }
        """)

        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self.toggle_max_restore)
        self.btn_close.clicked.connect(self.close)

        top_layout.addWidget(self.btn_left_toggle)
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_script)
        top_layout.addWidget(self.btn_right_toggle)

        top_layout.addWidget(self.btn_min)
        top_layout.addWidget(self.btn_max)
        top_layout.addWidget(self.btn_close)

        self.main_layout.addWidget(self.top_menu)

        # 3. 中间核心区 (终端)
        # self.terminal = TerminalView()
        # self.terminal.send_data.connect(self.write_serial)
        # self.main_layout.addWidget(self.terminal)

        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        self.sessions = {}

        # 4. 底部发送栏 (SSCOM 风格)
        self.bottom_bar = QFrame()
        self.bottom_bar.setFixedHeight(40)
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        self.bottom_layout.setContentsMargins(5, 0, 5, 0)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入命令...")
        self.btn_send = QPushButton("发送")
        self.btn_send.clicked.connect(lambda: self.write_serial(self.input_line.text().encode()))

        self.cb_hex = QCheckBox("Hex发送")
        self.bottom_layout.addWidget(self.input_line)
        self.bottom_layout.addWidget(self.cb_hex)
        self.bottom_layout.addWidget(self.btn_send)
        self.main_layout.addWidget(self.bottom_bar)

        # 5. 悬浮侧边栏 (后创建以保证在顶层)
        self.left_panel = AnimatedPanel(self, 220, "left")
        self.init_left_panel()

        self.right_panel = AnimatedPanel(self, 280, "right")
        self.init_right_panel()

        self.serial_worker = SerialWorker()
        self.serial_worker.data_received.connect(self.on_data_received)
        self.serial_worker.error.connect(self.on_serial_error)

        self.combo_port.currentIndexChanged.connect(self.on_port_changed)

    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_max.setText("□")
        else:
            self.showMaximized()
            self.btn_max.setText("❐")

    def init_left_panel(self):
        layout = QVBoxLayout(self.left_panel)
        layout.addWidget(QLabel("会话管理器"))
        self.session_list = QListWidget()
        self.session_list.addItem("Default Session")
        self.session_list.setStyleSheet("background: transparent; border: none; color: white;")
        layout.addWidget(self.session_list)
        layout.addStretch()

    def init_right_panel(self):
        layout = QVBoxLayout(self.right_panel)
        layout.setContentsMargins(15, 15, 15, 15)  # 让内容离边缘远一点，更好看
        layout.addWidget(QLabel("串口设置 (SSCOM)"))

        self.combo_port = QComboBox()
        self.refresh_ports()

        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200", "921600"])
        self.combo_baud.setCurrentText("19200")

        self.btn_connect = QPushButton("打开串口")
        self.btn_connect.clicked.connect(self.toggle_serial)

        layout.addWidget(QLabel("端口:"))
        layout.addWidget(self.combo_port)
        layout.addWidget(QLabel("波特率:"))
        layout.addWidget(self.combo_baud)
        layout.addWidget(self.btn_connect)

        # --- 修复后的分割线 ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("margin: 10px 0; background-color: #444;")
        layout.addWidget(line)
        # ---------------------

        layout.addWidget(QLabel("快捷指令"))
        for i in range(3):
            btn = QPushButton(f"自定义指令 {i + 1}")
            layout.addWidget(btn)

        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()

    def sync_ui_state(self):
        is_open = self.serial_worker.running
        self.btn_connect.setText("关闭串口" if is_open else "打开串口")
        self.combo_port.setEnabled(not is_open)
        self.combo_baud.setEnabled(not is_open)

    # --- 逻辑实现 ---

    def refresh_ports(self):
        self.combo_port.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            text = f"{p.device} - {p.description}"
            self.combo_port.addItem(text, p.device)

    def toggle_serial(self):
        port = self.combo_port.currentData()
        baud = int(self.combo_baud.currentText())

        if not port:
            QMessageBox.warning(self, "错误", "未选择串口")
            return

        # 如果已存在，直接切换
        if port in self.sessions:
            index = self.tabs.indexOf(self.sessions[port].terminal)
            self.tabs.setCurrentIndex(index)
            return

        # 1. worker
        worker = SerialWorker()
        worker.open(port, baud)

        # 2. terminal
        terminal = TerminalView()

        # 3. 绑定数据
        worker.data_received.connect(terminal.insertPlainText)
        terminal.send_data.connect(worker.send)

        # 4. 加入 tab
        self.tabs.addTab(terminal, port)

        # 5. 保存 session
        self.sessions[port] = Session(port, baud, worker, terminal)

    # def write_serial(self, data):
    #     self.serial_worker.send(data)

    def write_serial(self, data):
        current = self.tabs.currentWidget()

        for session in self.sessions.values():
            if session.terminal == current:
                session.worker.send(data)
                return

    def on_data_received(self, data):
        try:
            text = data.decode('utf-8')
        except:
            text = str(data)

        self.terminal.insertPlainText(text)
        self.terminal.moveCursor(QTextCursor.End)

    def on_serial_error(self, msg):
        QMessageBox.critical(self, "串口错误", msg)
        self.sync_ui_state()

    def run_custom_script(self):
        """Python 脚本支持"""
        script, ok = QInputDialog.getMultiLineText(self, "运行 Python 脚本", "输入脚本 (使用 'send(bytes)')",
                                                   "import time\nfor i in range(5):\n    send(b'Hello\\r\\n')\n    time.sleep(0.5)")
        if ok and script:
            try:
                # 注入 API 环境
                safe_env = {"send": self.write_serial, "time": __import__('time')}
                exec(script, safe_env)
            except Exception as e:
                QMessageBox.warning(self, "脚本错误", str(e))

    def resizeEvent(self, event):
        # 修正侧边栏高度
        menu_h = self.top_menu.height()
        panel_h = self.height() - menu_h

        self.left_panel.setFixedHeight(panel_h)
        self.right_panel.setFixedHeight(panel_h)

        # 调整 y 坐标，让侧边栏从菜单栏下方开始，这样就不会挡住顶部的 ☰ 按钮
        self.left_panel.move(self.left_panel.x(), menu_h)
        self.right_panel.move(self.right_panel.x(), menu_h)

        # 如果面板还没展开，确保它躲在屏幕外面
        if not self.left_panel.is_expanded:
            self.left_panel.hide_instantly()
        if not self.right_panel.is_expanded:
            self.right_panel.hide_instantly()

        super().resizeEvent(event)

    def save_config(self):
        config = {
            "port": self.combo_port.currentText(),
            "baud": self.combo_baud.currentText()
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f)

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                config = json.load(f)
                self.combo_port.setCurrentText(config.get("port", ""))
                self.combo_baud.setCurrentText(config.get("baud", "19200"))

    def on_port_changed(self):
        if self.serial_worker.running:
            self.serial_worker.close()

            port = self.combo_port.currentData()
            baud = int(self.combo_baud.currentText())

            self.serial_worker.open(port, baud)

        self.sync_ui_state()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局字体以增强现代感
    app.setFont(QFont("Segoe UI", 9))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())