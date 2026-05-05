import sys
import json
import os
import re
import serial
import serial.tools.list_ports
from core.serial_worker import SerialWorker
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from protocol import LineProtocol
from calib_thread import CalibrationThread # 导入新线程

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


# class TerminalView(QPlainTextEdit):
#     send_data = Signal(bytes)
#
#     def keyPressEvent(self, event):
#         # 如果按下的是回车键
#         if event.key() in (Qt.Key_Return, Qt.Key_Enter):
#             self.send_data.emit(b'\r\n')
#             return  # 阻止回车符输入到文本框里，或者去掉 return 让它也显示在屏幕上
#
#         # 原有的即时发送逻辑
#         text = event.text()
#         if text:
#             self.send_data.emit(text.encode('utf-8'))
#             return
#         super().keyPressEvent(event)

class TerminalView(QPlainTextEdit):
    send_data = Signal(bytes)

    def __init__(self):
        super().__init__()
        self.setPlaceholderText("终端按键输入不完美，慎用！")
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        # 1. 字体与外观（使用等宽字体是基础）
        font = QFont("Consolas", 10.5)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        # 2. 初始紧凑格式设置
        self.document().setDocumentMargin(0)
        self._apply_compact_format()

        # 3. 强力 ANSI 过滤正则：匹配所有 ESC [ 开头的序列
        # self.ansi_escape = re.compile(
        #     r'\x09(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'
        # )

    def _apply_compact_format(self):
        block_format = QTextBlockFormat()
        block_format.setLineHeight(100.0, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        block_format.setTopMargin(0)
        block_format.setBottomMargin(0)
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(block_format)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        key = event.key()
        # 处理粘贴
        if event.matches(QKeySequence.Paste):
            clip = QGuiApplication.clipboard().text()
            if clip: self.send_data.emit(clip.encode('utf-8'))
            return

        mapping = {
            Qt.Key_Up: b'\x1b[A',
            Qt.Key_Down: b'\x1b[B',
            # Qt.Key_Right: b'\x1b[C',
            # Qt.Key_Left: b'\x1b[D',
            # 尝试更改为 \x7f 如果 \x08 无效
            Qt.Key_Backspace: b'\x08',
            Qt.Key_Delete: b'\x1b[3~',
        }

        if key in mapping:
            if key == Qt.Key_Backspace:
                cursor = self.textCursor()
                if cursor.position() > 0:
                    cursor.deletePreviousChar()
                    self.setTextCursor(cursor)

            self.send_data.emit(mapping[key])
            return

        # 回车逻辑：大部分嵌入式终端只识别 \r 或 \n
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.send_data.emit(b'\r')  # 很多 msh 只需 \r
            return

        text = event.text()
        if text and not event.modifiers() & (Qt.ControlModifier | Qt.AltModifier):
            self.send_data.emit(text.encode('utf-8'))
            return

        super().keyPressEvent(event)

    # def insert_text(self, text):
    #     cursor = self.textCursor()
    #     # cursor.movePosition(QTextCursor.End)  # 必须保证在末尾
    #
    #     # 将文本转为字符流处理，而不是整体 replace
    #     for char in text:
    #         if char == '\r':
    #             continue  # 忽略 \r，只靠 \n 换行
    #         elif char == '\n':
    #             cursor.insertText('\n')
    #         else:
    #             # 只有可打印字符才插入
    #             if ord(char) >= 32:
    #                 # 如果当前位置已经有字符（比如回显覆盖），先删再插
    #                 # 这种简单的逻辑足以应付 msh 的基本交互
    #                 cursor.insertText(char)
    #
    #     self.setTextCursor(cursor)
    #     self.ensureCursorVisible()


class CalibrationLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 1. 基础校验：只允许输入数字、英文逗号和中文逗号
        # 允许中文逗号是为了能在 fix_content 中捕捉并转换它
        reg_ex = QRegularExpression(r"[0-9,,，]*")
        self.setValidator(QRegularExpressionValidator(reg_ex, self))

        self.setStyleSheet("background-color: #EEE; color: #000; border-radius: 4px; padding: 2px;")

        # 2. 绑定内容清洗逻辑
        self.textChanged.connect(self.fix_content)

    def fix_content(self, text):
        # 记录原始光标位置
        pos = self.cursorPosition()

        # --- 核心清洗逻辑 ---
        # 1. 替换中文逗号为英文逗号
        fixed = text.replace("，", ",")

        # 2. 消除连续逗号：将多个 , 替换为单个 ,
        # 使用正则表达式替换更高效，避免 while 循环可能带来的性能隐患
        fixed = re.sub(r',+', ',', fixed)

        # 3. 禁止以逗号开头
        if fixed.startswith(","):
            fixed = fixed.lstrip(",")

        # --- 应用清洗结果 ---
        if fixed != text:
            # 暂时阻塞信号，防止 setText 触发重复调用逻辑（虽然有 if 判断，但这是好习惯）
            self.blockSignals(True)
            self.setText(fixed)
            self.blockSignals(False)

            # 恢复光标位置
            # 如果是因为去重导致文本变短，pos 可能会越界，需取最小值
            self.setCursorPosition(min(pos, len(fixed)))

    def enterEvent(self, event):
        """鼠标悬停逻辑保持不变"""
        text_width = self.fontMetrics().horizontalAdvance(self.text())
        if text_width > (self.width() - 10):
            self.setToolTip(self.text())
        else:
            self.setToolTip("")
        super().enterEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.key_buffer = ""
        self.secret_key = "YOD001"
        # 关键：给整个窗口安装监视器
        self.installEventFilter(self)

        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setWindowTitle("YOD")
        self.resize(1100, 750)
        self.config_file = "config/config.json"
        self._last_ports = [] #  关键：缓存上一次端口

        self.setup_ui()
        self.load_config()
        self.setStyleSheet(STYLE_DARK)

        self.start_port_monitor()  #  启动监听

        self.protocol = LineProtocol()  # 实例化协议处理器

        self._waiting_for_echo = False

    def eventFilter(self, watched, event):
        # 监控所有的键盘按下事件
        if event.type() == QEvent.KeyPress:
            key_text = event.text().upper()
            if key_text:
                self.key_buffer += key_text
                # 只保留最后 6 位
                self.key_buffer = self.key_buffer[-len(self.secret_key):]

                # 检查匹配
                if self.key_buffer == self.secret_key:
                    self.log_to_terminal("工程模式已激活", "#98C379")
                    self.set_hidden_calib_enabled(True)
                    self.statusBar().showMessage("Special mode activated!", 3000)
                    self.key_buffer = ""  # 匹配后清空
                    # return True # 如果不想让 YOD001 这几个字发给串口，就取消注释这一行
        # 其他事件交给系统默认处理
        return super().eventFilter(watched, event)

    def log_to_terminal(self, msg, color="#569CD6"):
        """向终端插入带颜色的系统日志"""
        # 确保 terminal 已经初始化
        if not hasattr(self, 'terminal'):
            return

        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 检查当前行是否已经有内容（比如 msh />），如果有则先换行
        if cursor.columnNumber() != 0:
            cursor.insertText("\n")

        # 创建字符格式并设置颜色
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))

        # 应用格式并插入文本
        cursor.setCharFormat(fmt)
        cursor.insertText(f"\n>>> [SYS] {msg}\n")

        # 关键：恢复默认格式，否则后续收到的串口数据也会变色
        cursor.setCharFormat(QTextCharFormat())

        # 滚动到底部
        self.terminal.setTextCursor(cursor)
        self.terminal.ensureCursorVisible()

    def start_port_monitor(self):
        self.port_timer = QTimer(self)
        self.port_timer.timeout.connect(self.check_ports)
        self.port_timer.start(1500)  # 1.5秒

    def check_ports(self):
        ports = serial.tools.list_ports.comports()
        current = [p.device for p in ports]

        # 没变化就不刷新（避免UI闪烁）
        if current == self._last_ports:
            return

        self._last_ports = current
        self.refresh_ports()

        # UX提示（可选）
        self.statusBar().showMessage("串口设备已更新", 2000)

        # ⭐ 如果当前串口被拔掉
        if self.serial_worker.is_open():
            if self.serial_worker.serial_port.port not in current:
                self.serial_worker.close()
                self.sync_ui_state()
                self.statusBar().showMessage("设备已断开", 3000)

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

        title_label = QLabel("ALP")
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
        self.terminal = TerminalView()
        self.terminal.send_data.connect(self.write_serial)
        self.main_layout.addWidget(self.terminal)

        # 4. 底部发送栏 (SSCOM 风格)
        self.bottom_bar = QFrame()
        self.bottom_bar.setFixedHeight(40)
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        self.bottom_layout.setContentsMargins(5, 0, 5, 0)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入命令...")
        self.btn_send = QPushButton("发送")
        self.input_line.returnPressed.connect(self.write_serial)
        self.btn_send.clicked.connect(self.write_serial)

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
        self.combo_baud.addItems(["1200","2400","4800","9600", "19200","38400", "57600","115200", "921600"])
        self.combo_baud.setCurrentText("19200")

        self.btn_connect = QPushButton("打开串口")
        self.btn_connect.clicked.connect(self.toggle_serial)

        self.combo_databits = QComboBox()
        self.combo_databits.addItems(["5", "6", "7", "8"])
        self.combo_databits.setCurrentText("8")

        self.combo_parity = QComboBox()
        self.combo_parity.addItems(["None", "Even", "Odd"])
        self.combo_parity.setCurrentText("None")

        self.combo_stopbits = QComboBox()
        self.combo_stopbits.addItems(["1", "1.5", "2"])
        self.combo_stopbits.setCurrentText("1")



        layout.addWidget(QLabel("端口:"))
        layout.addWidget(self.combo_port)
        layout.addWidget(QLabel("波特率:"))
        layout.addWidget(self.combo_baud)

        layout.addWidget(QLabel("数据位:"))
        layout.addWidget(self.combo_databits)

        layout.addWidget(QLabel("校验:"))
        layout.addWidget(self.combo_parity)

        layout.addWidget(QLabel("停止位:"))
        layout.addWidget(self.combo_stopbits)

        # layout.addWidget(self.btn_connect)

        # 建议放在“串口设置”按钮上方或“快捷指令”下方
        self.cb_local_echo = QCheckBox("本地回显 (Local Echo)")
        self.cb_local_echo.setToolTip("开启后，发送的数据将直接显示在终端界面")
        self.cb_local_echo.setStyleSheet("color: #AAA;")
        layout.addWidget(self.cb_local_echo)

        layout.addWidget(self.btn_connect)


        # --- 修复后的分割线 ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("margin: 10px 0; background-color: #444;")
        layout.addWidget(line)
        # ---------------------

        # --- 统一校准 UI 区域 ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("margin: 15px 0; background-color: #444;")
        layout.addWidget(line)

        # 1. 总开关 Checkbox
        self.cb_calibration = QCheckBox("量产校准模式")
        self.cb_calibration.setStyleSheet("font-weight: bold; color: #569CD6; font-size: 13px;")
        layout.addWidget(self.cb_calibration)

        # 2. 模式选择 ComboBox
        self.combo_calib_mode = QComboBox()
        # 这里填入你在 MODE_CONFIG 中定义的 Key
        self.combo_calib_mode.addItems(["Lux", "PD", "CL500", "DN", "Other"])
        layout.addWidget(QLabel("选择校准维度:"))
        layout.addWidget(self.combo_calib_mode)

        # 3. 点位输入 LineEdit (使用你自定义的 CalibrationLineEdit)
        self.edit_calib_points = CalibrationLineEdit()
        self.edit_calib_points.setPlaceholderText("例如: 10, 50, 100")
        layout.addWidget(QLabel("校准点位 (逗号分隔):"))
        layout.addWidget(self.edit_calib_points)

        # 4. 开始按钮
        self.btn_start_calib = QPushButton("开始校准")
        self.btn_start_calib.setFixedHeight(40)
        self.btn_start_calib.setStyleSheet("""
                    QPushButton:enabled { background-color: #007ACC; color: white; font-weight: bold; }
                    QPushButton:disabled { background-color: #333; color: #666; }
                """)
        layout.addWidget(self.btn_start_calib)

        # --- 逻辑绑定 ---
        self.cb_calibration.toggled.connect(self.sync_calib_ui_state)
        # 关键：监听下拉框切换模式 (必须加这一行，否则切换 Lux 到 CL500 时没反应)
        self.combo_calib_mode.currentIndexChanged.connect(self.sync_calib_ui_state)
        self.btn_start_calib.clicked.connect(self.on_start_calibration_clicked)

        # 初始状态同步
        self.sync_calib_ui_state()
        layout.addStretch()

        # --- 新增：隐藏的校准区域 ---
        self.hidden_calib_widget = QWidget()
        hidden_layout = QVBoxLayout(self.hidden_calib_widget)
        hidden_layout.setContentsMargins(0, 0, 0, 0)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("margin: 10px 0; background-color: #444;")
        hidden_layout.addWidget(line)

        # 光源内校准按钮
        self.btn_internal_calib = QPushButton("光源内校准")
        self.btn_internal_calib.setFixedHeight(30)
        self.btn_internal_calib.setStyleSheet("background-color: #3e4e5e;")  # 给个不一样的颜色区分
        hidden_layout.addWidget(self.btn_internal_calib)

        # 光源外校准按钮
        self.btn_external_calib = QPushButton("光源外校准")
        self.btn_external_calib.setFixedHeight(30)
        self.btn_external_calib.setStyleSheet("background-color: #3e4e5e;")
        hidden_layout.addWidget(self.btn_external_calib)

        layout.addWidget(self.hidden_calib_widget)

        # 初始状态
        self.hidden_calib_widget.setVisible(True)
        self.set_hidden_calib_enabled(False)  # 初始禁用

        # 绑定按钮事件（你可以根据需要实现对应的逻辑）
        self.btn_internal_calib.clicked.connect(lambda: self.log_to_terminal("执行光源内校准...", "#E06C75"))
        self.btn_external_calib.clicked.connect(lambda: self.log_to_terminal("执行光源外校准...", "#E06C75"))

        layout.addStretch()

    def set_hidden_calib_enabled(self, enabled: bool):
        """控制隐藏校准区域是否可用（灰/亮）"""
        for widget in self.hidden_calib_widget.findChildren(QWidget):
            widget.setEnabled(enabled)

        # 可选：视觉效果更明显
        if enabled:
            self.hidden_calib_widget.setStyleSheet("")
        else:
            self.hidden_calib_widget.setStyleSheet("""
                QWidget {
                    color: #666;
                }
                QPushButton {
                    background-color: #333;
                    color: #666;
                }
            """)

    def sync_calib_ui_state(self):
        """量产校准模式 Checkbox 切换逻辑"""
        master_on = self.cb_calibration.isChecked()

        if master_on:
            # --- 阶段 A：发起握手，UI 必须变灰并锁定 ---
            self.log_to_terminal("正在检测设备连接 (发送 set_lux 0)...", "#D19A66")

            self._waiting_for_echo = True

            # 强制所有组件禁用并变灰
            self.combo_calib_mode.setEnabled(False)
            self.edit_calib_points.setEnabled(False)
            self.btn_start_calib.setEnabled(False)
            self.btn_start_calib.setText("正在匹配设备...")

            # 视觉变灰处理
            self.edit_calib_points.setStyleSheet("background-color: #333; color: #666; border: 1px solid #444;")
            self.edit_calib_points.setPlaceholderText("正在等待设备回显...")

            # 发送指令
            self.write_serial("set_lux 0".encode('utf-8'))

            # 超时处理
            QTimer.singleShot(3000, self.check_handshake_timeout)
        else:
            # --- 阶段 B：完全关闭状态 ---
            self._waiting_for_echo = False
            self.combo_calib_mode.setEnabled(False)
            self.edit_calib_points.setEnabled(False)
            self.edit_calib_points.clear()
            self.edit_calib_points.setPlaceholderText("请开启量产校准模式")
            self.edit_calib_points.setStyleSheet("background-color: #333; color: #666;")

            self.btn_start_calib.setEnabled(False)
            self.btn_start_calib.setText("开始校准")

    def finalize_ui_unlock(self):
        """回显成功后，真正根据模式逻辑解锁 UI 并变亮"""
        current_mode = self.combo_calib_mode.currentText()
        placeholder_modes = ["CL500", "DN", "Other"]
        is_placeholder = current_mode in placeholder_modes

        # 1. 基础组件解锁
        self.combo_calib_mode.setEnabled(True)
        self.edit_calib_points.setEnabled(True)
        self.btn_start_calib.setText("开始校准")

        # 2. 根据模式决定具体样式
        if is_placeholder:
            # 模式不支持：虽然解锁了外壳，但内部锁定显示红色警告
            self.edit_calib_points.setReadOnly(True)
            self.edit_calib_points.clear()
            self.edit_calib_points.setPlaceholderText("该功能暂无，请联系作者！")
            self.edit_calib_points.setStyleSheet("background-color: #444; color: #FF5555; font-weight: bold;")
            self.btn_start_calib.setEnabled(False)
        else:
            # 模式正常：彻底变亮 (白色背景)
            self.edit_calib_points.setReadOnly(False)
            self.edit_calib_points.setPlaceholderText("例如: 10, 50, 100")
            self.edit_calib_points.setStyleSheet("background-color: #EEE; color: #000; border: 1px solid #CCC;")
            self.btn_start_calib.setEnabled(True)

    def check_handshake_timeout(self):
        """超时处理"""
        if hasattr(self, '_waiting_for_echo') and self._waiting_for_echo:
            self._waiting_for_echo = False
            self.log_to_terminal("连接超时：请检查串口端口是否选择正确、波特率或是否已经连接串口等!", "#E06C75")

            # 自动取消勾选并复位
            self.cb_calibration.blockSignals(True)
            self.cb_calibration.setChecked(False)
            self.cb_calibration.blockSignals(False)
            self.btn_start_calib.setText("开始校准")

    def sync_calibration_edits(self):
        """统一管理校准区域的启用/禁用逻辑"""
        master_on = self.cb_calibration.isChecked()
        # 检查单选按钮组中是否有任何一个被选中
        any_rb_checked = self.calibration_group.checkedButton() is not None

        for rb, edit in self.calib_rows:
            # 1. 单选框只有在“校准”勾选时才可用
            rb.setEnabled(master_on)

            # 2. 输入框只有在“校准”开启 且 “对应单选被选中”时才可用
            edit_enabled = master_on and rb.isChecked()
            edit.setEnabled(edit_enabled)

            # 3. 如果总开关关闭，清理状态
            if not master_on:
                # 阻止信号环路，暂时屏蔽信号处理
                rb.blockSignals(True)
                rb.setChecked(False)
                rb.blockSignals(False)
                edit.clear()

            # 4. 样式辅助：禁用的输入框变暗（可选，也可写在 QSS 里）
            if not edit_enabled:
                edit.setStyleSheet("background-color: #333; color: #666;")
            else:
                edit.setStyleSheet("background-color: #EEE; color: #000;")
            # --- 核心逻辑：只有校准勾选 且 选择了其中一个单选，按钮才生效 ---
            self.btn_start_calib.setEnabled(master_on and any_rb_checked)

    def on_start_calibration_clicked(self):
        """点击开始校准后的逻辑"""
        # 1. 获取当前选择的模式
        mode = self.combo_calib_mode.currentText()

        # 2. 获取并清洗点位数据
        raw_text = self.edit_calib_points.text().strip(',')
        if not raw_text:
            QMessageBox.critical(self, "错误", "请输入校准点位！")
            return

        try:
            # 转换为 float 列表
            val_list = [float(x) for x in raw_text.split(',') if x.strip()]
        except ValueError:
            QMessageBox.warning(self, "格式错误", "点位列表包含非法字符，请检查数字格式")
            return

        # 3. 锁定 UI 防止二次点击
        self.cb_calibration.setEnabled(False)
        self.btn_start_calib.setEnabled(False)
        self.btn_start_calib.setText("校准中...")

        # 4. 创建并启动线程
        self.calib_thread = CalibrationThread(mode, val_list, self.serial_worker)

        # 信号绑定
        self.calib_thread.log_signal.connect(lambda msg: self.log_to_terminal(msg, "#98C379"))
        self.calib_thread.finished_signal.connect(self.on_calibration_finished)

        self.log_to_terminal(f"启动 {mode} 模式校准，目标点位: {val_list}", "#D19A66")
        self.calib_thread.start()

    def on_calibration_finished(self, result_msg):
        """校准结束的回调"""
        QMessageBox.information(self, "任务结束", f"<b>校准结果:</b><br>{result_msg}")

        # 恢复 UI 状态
        self.cb_calibration.setEnabled(True)
        self.cb_calibration.setChecked(False)  # 自动关闭校准开关
        self.btn_start_calib.setText("开始校准")
        self.sync_calib_ui_state()

        self.log_to_terminal("校准任务已结束", "#5DADE2")

    def get_serial_config(self):
        parity_map = {
            "None": serial.PARITY_NONE,
            "Even": serial.PARITY_EVEN,
            "Odd": serial.PARITY_ODD
        }

        stopbits_map = {
            "1": serial.STOPBITS_ONE,
            "1.5": serial.STOPBITS_ONE_POINT_FIVE,
            "2": serial.STOPBITS_TWO
        }

        return {
            "port": self.combo_port.currentData(),
            "baud": int(self.combo_baud.currentText()),
            "bytesize": int(self.combo_databits.currentText()),
            "parity": parity_map[self.combo_parity.currentText()],
            "stopbits": stopbits_map[self.combo_stopbits.currentText()]
        }


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()

    def set_ui_locked(self, locked: bool):
        self.combo_port.setEnabled(not locked)
        self.combo_baud.setEnabled(not locked)
        self.combo_databits.setEnabled(not locked)
        self.combo_parity.setEnabled(not locked)
        self.combo_stopbits.setEnabled(not locked)

    def sync_ui_state(self):
        is_open = self.serial_worker.running
        self.btn_connect.setText("关闭串口" if is_open else "打开串口")
        self.set_ui_locked(is_open)
        if is_open:
            self.btn_connect.setStyleSheet("background:#c0392b;")
        else:
            self.btn_connect.setStyleSheet("")


    # --- 逻辑实现 ---

    def refresh_ports(self):
        self.combo_port.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            text = f"{p.device} - {p.description}"
            self.combo_port.addItem(text, p.device)

    def toggle_serial(self):
        # === 关闭逻辑 ===
        if self.serial_worker.running:
            self.serial_worker.close()
            self.sync_ui_state()
            self.save_config()
            return
        # === 打开逻辑 ===
        cfg = self.get_serial_config()

        if not cfg["port"]:
            QMessageBox.warning(self, "错误", "未选择串口")
            return
        try:
            self.serial_worker.open(
                port=cfg["port"],
                baud=cfg["baud"],
                bytesize=cfg["bytesize"],
                parity=cfg["parity"],
                stopbits=cfg["stopbits"]
            )
        except Exception as e:
            QMessageBox.critical(self, "串口错误", str(e))
            return
        # === 统一刷新 UI 状态 ===
        self.sync_ui_state()
        self.save_config()

    def write_serial(self, data=None):
        # data 为 None 或 bool 通常意味着点击了“发送”按钮
        if data is None or isinstance(data, bool):
            text = self.input_line.text()
            if not text: return
            if self.cb_hex.isChecked():
                try:
                    # Hex 模式下，通常协议是严格的，不建议自动加 \r\n
                    send_bytes = bytes.fromhex(text.replace(" ", ""))
                except:
                    QMessageBox.warning(self, "错误", "Hex 格式非法")
                    return
            else:
                # --- 自动补全回车换行 ---
                # \r 是回车 (Carriage Return), \n 是换行 (Line Feed)
                send_bytes = (text + "\r\n").encode('utf-8')
            # 发送后可以考虑清空输入框，方便下次输入
            # self.input_line.clear()
        else:
            # data 已经是 bytes（例如来自终端直接输入）
            send_bytes = data

        # 1. 执行发送
        if self.serial_worker.running:
            # success = self.serial_worker.send(send_bytes)
            # 使用我们新写的异步发送方法
            self.serial_worker.send_async(send_bytes)

            # 2. 如果发送成功且开启了本地回显，则将其显示在终端
            if self.cb_local_echo.isChecked():
                # 为了区分是“发的”还是“收的”，可以加个颜色，或者直接调用显示函数
                self.on_data_received(send_bytes, is_send=True)

    def on_data_received(self, data, is_send=False):
        mode = "hex" if self.cb_hex.isChecked() else "text"

        try:
            results = self.protocol.feed(data, mode=mode)

            cursor = self.terminal.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.terminal.setTextCursor(cursor)

            if is_send:
                fmt = QTextCharFormat()
                fmt.setForeground(QColor("#569CD6"))
                self.terminal.setCurrentCharFormat(fmt)
                self.terminal.setCurrentCharFormat(QTextCharFormat())

            for packet in results:
                if mode == "hex":
                    self.terminal.insertPlainText(packet["hex"] + " ")
                if packet["mode"] == "text_stream" :
                    # 现在的 packet["render"] 可能是单个字符，也可能是带换行的字符串
                    content = packet.get("render", "")
                    # 无论哪种，insertPlainText 都会立即渲染，实现实时回显
                    self.terminal.insertPlainText(content)

                    # --- 握手匹配：检查回显内容 ---
                    if hasattr(self, '_waiting_for_echo') and self._waiting_for_echo:
                        # 匹配设备返回的指令回显
                        if "set_lux 0" in content:
                            self._waiting_for_echo = False
                            self.log_to_terminal("收到设备回显，软件与硬件握手成功！", "#98C379")
                            self.finalize_ui_unlock()  # 执行解锁
                            return

                    # --- 核心改进：根据线程状态决定是否发原始数据 发送cat数据---
                    if self.cb_calibration.isChecked() and hasattr(self, 'calib_thread') and self.calib_thread.isRunning():
                        if getattr(self.calib_thread, '_is_collecting_file', False):
                            # 只有开关打开时，才通过 is_raw=True 发送原始字符串
                            # print("DEBUG: 正在向线程传输原始数据...")
                            self.calib_thread.receive_answer(packet["render"], is_raw=True)

                # 3. 新增：处理 data 模式 (对应你协议里的 mode: "data")
                if packet.get("mode") == "data_line":
                    clean_data = packet.get("data", "")

                    # 只有在界面上勾选了“校准”复选框，且线程正在运行时，才分发数据
                    if self.cb_calibration.isChecked() and hasattr(self,'calib_thread') and self.calib_thread.isRunning():
                        # 将清洗后的字符串数据（如 "100.5"）喂给线程
                        self.calib_thread.receive_answer(clean_data)

                    # 如果你希望 data 模式的数据也显示在黑框里，可以取消下面这一行的注释
                    # self.terminal.insertPlainText(clean_data + "\n")

            self.terminal.ensureCursorVisible()

        except Exception as e:
            print(f"UI渲染异常: {e}")

    def write_to_serial(self, data: bytes):
        """全局统一发送接口"""
        if self.serial_worker and self.serial_worker.is_open():
            # 这里直接调用 worker 的封装
            self.serial_worker.send(data)

            # 处理本地回显逻辑
            if self.cb_local_echo.isChecked():
                self.on_data_received(data, is_send=True)

    def on_serial_error(self, msg):
        # # 只提示一次 + 状态同步
        QMessageBox.critical(self, "设备已断开", msg)
        self.serial_worker.close()
        self.sync_ui_state()

    def run_custom_script(self):
        """Python 脚本支持"""
        script, ok = QInputDialog.getMultiLineText(self, "运行 Python 脚本", "输入脚本 (使用 'send(bytes)')",
                                                   "import time\nfor i in range(5):\n    send(b'set_lux 1000\\r\\n')\n    time.sleep(1)\n    send(b'set_lux 10000\\r\\n')\n")
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
            "baud": self.combo_baud.currentText(),
            "databits": self.combo_databits.currentText(),
            "parity": self.combo_parity.currentText(),
            "stopbits": self.combo_stopbits.currentText(),
            "local_echo": self.cb_local_echo.isChecked()
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f)

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                config = json.load(f)

            self.combo_port.setCurrentText(config.get("port", ""))
            self.combo_baud.setCurrentText(config.get("baud", "19200"))
            self.combo_databits.setCurrentText(config.get("databits", "8"))
            self.combo_parity.setCurrentText(config.get("parity", "None"))
            self.combo_stopbits.setCurrentText(config.get("stopbits", "1"))
            self.cb_local_echo.setChecked(config.get("local_echo", False))

    def on_port_changed(self):
        if self.serial_worker.running:
            self.serial_worker.close()

            cfg = self.get_serial_config()

            try:
                self.serial_worker.open(
                    port=cfg["port"],
                    baud=cfg["baud"],
                    bytesize=cfg["bytesize"],
                    parity=cfg["parity"],
                    stopbits=cfg["stopbits"]
                )
            except Exception as e:
                QMessageBox.critical(self, "串口错误", str(e))

        self.sync_ui_state()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局字体以增强现代感
    app.setFont(QFont("Segoe UI", 9))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())