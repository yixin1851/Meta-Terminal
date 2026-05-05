import json
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class AnimatedPanel(QFrame):
    def __init__(self, parent, width, direction="left"):
        super().__init__(parent)
        self.setObjectName("SidePanel")
        self.panel_width = width
        self.direction = direction
        self.is_expanded = False

        self.setFixedWidth(0)
        self.setVisible(False)  # 初始隐藏，防止占位残留

        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)  # 缩短时间能显著减少视觉残留
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        # 核心：动画结束后的清理工作
        self.animation.finished.connect(self._on_animation_finished)

    def toggle(self):
        self.animation.stop()

        if not self.is_expanded:
            # --- 展开动作 ---
            # 1. 先显示面板
            self.setVisible(True)
            # 2. 设置目标宽度
            end_val = self.panel_width
        else:
            # --- 收缩动作 ---
            # 1. 关键：收缩时立即隐藏内部子控件，防止它们干扰边缘渲染
            # 如果你不想逐个隐藏，可以直接在动画结束前关闭绘制
            end_val = 0

        self.animation.setEndValue(end_val)
        self.animation.start()
        self.is_expanded = not self.is_expanded

    def _on_animation_finished(self):
        """动画结束后的回调"""
        if not self.is_expanded:
            self.setVisible(False)
        else:
            # 展开完成后，确保面板是完全可见的
            self.setVisible(True)

    def _sync_max_width(self, val):
        self.setMaximumWidth(val)

class MultiSendPanel(AnimatedPanel):
    # 定义一个信号，用于将指令发送给串口逻辑层
    data_ready_to_send = Signal(dict)

    def __init__(self, parent, width=320, serial_worker=None):  # 增加基础宽度至 320
        super().__init__(parent, width, direction="left")

        self.rows = []
        self.loop_timer = QTimer()
        self.loop_timer.timeout.connect(self._handle_loop_send)
        self.current_loop_index = 0
        self.serial_worker = serial_worker

        self.setStyleSheet("""
            QWidget#SidePanel { background-color: #252526; border-right: 1px solid #333333; }
            QLabel { color: #AAAAAA; font-size: 11px; }
            QLineEdit { 
                background-color: #3c3c3c; color: #CCCCCC; border: 1px solid #3c3c3c; 
                border-radius: 2px; padding: 2px; font-family: 'Consolas';
            }
            QLineEdit:focus { border: 1px solid #007acc; background-color: #1e1e1e; }
            QPushButton { 
                background-color: #0e639c; color: white; border: none; 
                border-radius: 2px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:pressed { background-color: #094771; }
            QCheckBox { spacing: 5px; color: #CCCCCC; }
            QScrollArea { border: none; background: transparent; }
            #ListWidget { background-color: #252526; }
        """)
        self.setup_multi_send_ui()

    def setup_multi_send_ui(self):
        # 1. 内胆锁定固定宽度
        self.content_container = QWidget()
        self.content_container.setFixedWidth(self.panel_width)

        layout = QVBoxLayout(self.content_container)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(12)

        # --- Top Options ---
        top_layout = QHBoxLayout()
        self.check_loop = QCheckBox("Loop Send")
        top_layout.addWidget(self.check_loop)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # 修改：增加一个“Add Row”按钮在顶部
        top_layout = QHBoxLayout()
        self.check_loop = QCheckBox("Loop Send")
        self.check_loop.stateChanged.connect(self._toggle_loop)

        self.btn_add = QPushButton("+ Add")
        self.btn_add.setFixedWidth(60)
        self.btn_add.clicked.connect(lambda: self.add_command_row())

        self.btn_save = QPushButton("Save")
        self.btn_save.setFixedWidth(60)
        self.btn_save.clicked.connect(self.save_settings)

        top_layout.addWidget(self.check_loop)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_save)

        # --- Table Header ---
        # 重新分配列宽: Order(35), Hex(20), Context(Stretch), Send(50), Delay(40)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 0, 2, 0)

        self.col_widths = {"order": 35, "hex": 20, "send": 55, "ms": 45}

        headers = [("Order", self.col_widths["order"]),
                   ("Hex", self.col_widths["hex"]),
                   ("Context", 0),
                   ("Action", self.col_widths["send"]),
                   ("ms", self.col_widths["ms"])]

        for text, w in headers:
            lbl = QLabel(text)
            if w > 0: lbl.setFixedWidth(w)
            header_layout.addWidget(lbl, 0 if w > 0 else 1)

        layout.addLayout(header_layout)

        # --- Scroll Area ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.list_widget = QWidget()
        self.list_widget.setObjectName("ListWidget")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setContentsMargins(0, 0, 2, 0)
        self.list_layout.setSpacing(6)

        # 生成 15 条指令行
        for i in range(1, 36):
            self.add_command_row(i)

        self.scroll_area.setWidget(self.list_widget)
        layout.addWidget(self.scroll_area)

        # 挂载
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.content_container)

    def add_command_row(self, data=None):
        """
        功能 3: 动态增加命令框
        兼容 data 为 None (新增), int (初始化), dict (加载配置)
        """
        # 1. 数据预处理层：统一提取出 UI 需要的值
        current_idx = len(self.rows) + 1

        # 默认值
        order_val = current_idx
        is_hex = False
        ctx_content = ""
        delay_ms = "100"

        # 根据 data 类型进行分发
        if isinstance(data, dict):
            # 场景：从 JSON 加载配置
            order_val = data.get('order', current_idx)
            is_hex = data.get('hex', False)
            ctx_content = data.get('ctx', '')
            delay_ms = str(data.get('ms', "100"))
        elif isinstance(data, int):
            # 场景：setup_ui 里的循环初始化
            order_val = ""

        # 2. UI 构建层
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Order (功能 4)
        edit_order = QLineEdit(str(order_val))
        edit_order.setFixedWidth(35)
        edit_order.setAlignment(Qt.AlignCenter)

        # HEX Checkbox (功能 2)
        chk_hex = QCheckBox()
        chk_hex.setFixedWidth(20)
        chk_hex.setChecked(is_hex)

        # Context (核心内容)
        edit_ctx = QLineEdit(ctx_content)
        edit_ctx.setPlaceholderText(f"Cmd {order_val}")

        # Send Button (功能 1)
        btn_send = QPushButton("Send")
        btn_send.setFixedWidth(55)
        btn_send.setFixedHeight(22)
        # 注意：这里改用直接传递 row_obj 的引用，避免 lambda 闭包陷阱

        # ms (延迟)
        edit_ms = QLineEdit(delay_ms)
        edit_ms.setFixedWidth(45)
        edit_ms.setAlignment(Qt.AlignCenter)

        layout.addWidget(edit_order)
        layout.addWidget(chk_hex)
        layout.addWidget(edit_ctx, 1)
        layout.addWidget(btn_send)
        layout.addWidget(edit_ms)

        # 3. 存储与绑定层
        row_obj = {
            "widget": row_widget,
            "order": edit_order,
            "hex": chk_hex,
            "ctx": edit_ctx,
            "send": btn_send,
            "ms": edit_ms
        }

        # 修正：将信号绑定放在 row_obj 创建之后，确保能正确引用自身
        btn_send.clicked.connect(lambda: self.send_cmd(row_obj))
        chk_hex.stateChanged.connect(lambda state: self._handle_hex_toggle(state, edit_ctx))

        self.rows.append(row_obj)
        self.list_layout.addWidget(row_widget)

    # --- 功能 1: 发送逻辑 ---
    def _send_single_row(self, row_idx_in_list):
        # 找到触发信号的行数据
        for row in self.rows:
            if row["send"] == self.sender():
                data = {
                    "content": row["ctx"].text(),
                    "is_hex": row["hex"].isChecked(),
                    "order": row["order"].text()
                }
                self.data_ready_to_send.emit(data)
                print(f"Sending: {data}")  # 调试输出

    # --- 功能 2: HEX 显示转换 ---
    def _handle_hex_toggle(self, state, edit_field):
        content = edit_field.text().strip()
        if not content: return
        try:
            if state == Qt.Checked:  # 转为 HEX 格式
                hex_str = ' '.join([f'{ord(c):02X}' for c in content])
                edit_field.setText(hex_str)
            else:  # 从 HEX 转回字符串
                bytes_obj = bytes.fromhex(content.replace(' ', ''))
                edit_field.setText(bytes_obj.decode('ascii', errors='replace'))
        except Exception:
            pass  # 转换失败不强求

    # --- 功能 4: Loop Send 逻辑 ---
    def _toggle_loop(self, state):
        if state == Qt.Checked:
            # 排序：根据 Order 字段从小到大执行
            self.sorted_rows = sorted(
                [r for r in self.rows if r["ctx"].text().strip()],
                key=lambda x: int(x["order"].text() if x["order"].text().isdigit() else 999)
            )
            if self.sorted_rows:
                self.current_loop_index = 0
                self._handle_loop_send()
        else:
            self.loop_timer.stop()

    def _handle_loop_send(self):
        if not self.check_loop.isChecked() or not self.sorted_rows:
            return

        row = self.sorted_rows[self.current_loop_index]
        # 执行发送信号
        self._send_single_row_by_obj(row)

        # 获取当前行的延时，并设置下一次定时器
        delay = int(row["ms"].text() if row["ms"].text().isdigit() else 100)
        self.loop_timer.start(delay)

        # 索引递增
        self.current_loop_index = (self.current_loop_index + 1) % len(self.sorted_rows)

    def _send_single_row_by_obj(self, row):
        data = {"content": row["ctx"].text(), "is_hex": row["hex"].isChecked()}
        self.data_ready_to_send.emit(data)

    # --- 功能 5: 保存设置 ---
    def save_settings(self):
        config_data = []
        for row in self.rows:
            config_data.append({
                "order": row["order"].text(),
                "hex": row["hex"].isChecked(),
                "ctx": row["ctx"].text(),
                "ms": row["ms"].text()
            })
        with open("multi_send_config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        print("Settings Saved.")

    def send_cmd(self, row_obj):
        # 提取输入框文本
        edit_ctx = row_obj.get("ctx")
        raw_text = edit_ctx.text().strip()
        if not raw_text:
            return

        try:
            # 获取该行 HEX 勾选框的状态
            is_hex_mode = row_obj["hex"].isChecked()

            if is_hex_mode:
                # --- HEX 模式 ---
                # 过滤掉空格，确保只剩下十六进制字符
                hex_str = raw_text.replace(" ", "")
                # 简单校验：长度必须是偶数且字符合法
                data_to_send = bytes.fromhex(hex_str)
            else:
                # --- 文本模式 ---
                # 直接转成字节流，并加上换行符（嵌入式 Shell 必需）
                data_to_send = f"{raw_text}\r\n".encode('utf-8')

            # 执行物理发送
            if self.serial_worker and self.serial_worker.running:
                self.serial_worker.send_async(data_to_send)
            else:
                print("串口未连接")

        except ValueError as e:
            # 专门捕获 HEX 格式错误并给出友好提示
            print(f"HEX 格式错误: 请检查输入是否包含非 0-9/A-F 字符。详情: {e}")
        except Exception as e:
            print(f"发送异常: {e}")