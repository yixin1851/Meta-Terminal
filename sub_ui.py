import json
import os
import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from CL500_thread import IlluminanceWorker


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
    # 定义控制信号
    sig_do_init = Signal()
    sig_do_measure = Signal(int)

    def __init__(self, parent, width=320, serial_worker=None):  # 增加基础宽度至 320
        super().__init__(parent, width, direction="left")
        self.main_window = parent
        self.cl500_worker = None
        self.cl500_thread = None

        self.rows = []
        self.loop_timer = QTimer()
        self.loop_timer.timeout.connect(self._handle_loop_send)
        self.current_loop_index = 0
        self.serial_worker = serial_worker

        # 在 __init__ 中添加 定时器触发保存cmd_config.json
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)  # 只触发一次
        self.save_timer.timeout.connect(self._execute_save)  # 真正的写入逻辑

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
        layout.setContentsMargins(2, 5, 2, 5)
        layout.setSpacing(10)

        # 修改：增加一个“Add Row”按钮在顶部
        top_layout = QHBoxLayout()
        self.check_loop = QCheckBox("Loop Send")
        self.check_loop.stateChanged.connect(self._toggle_loop)

        self.btn_init_cl500 = QPushButton("初始化")
        self.btn_init_cl500.setFixedWidth(70)
        # 样式美化（可选）：让按钮看起来更有科技感
        self.btn_init_cl500.setStyleSheet(
            "QPushButton { background-color: #007ACC; color: white; border-radius: 2px; }")


        self.btn_init_cl500.clicked.connect(self.on_init_cl500_clicked)


        self.btn_read_cl500 = QPushButton("读取CL500")
        self.btn_read_cl500.setFixedWidth(100)
        self.btn_read_cl500.setStyleSheet(
            "QPushButton { background-color: #007ACC; color: white; border-radius: 2px; }")

        self.btn_read_cl500.clicked.connect(self.on_read_cl500_clicked)

        # 1. 使用 QLineEdit 代替 QTextEdit
        self.times_edit = QLineEdit()
        self.times_edit.setPlaceholderText("次数")  # 使用占位符，而不是直接填文字
        self.times_edit.setFixedWidth(35)
        # 2. 限制高度，使其与按钮对齐
        self.times_edit.setFixedHeight(25)
        # 3. 设置深色样式，使其融入背景
        self.times_edit.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding-left: 2px;
            }
        """)

        top_layout.addWidget(self.check_loop)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_init_cl500)
        top_layout.addWidget(self.btn_read_cl500)
        top_layout.addWidget(self.times_edit)

        layout.addLayout(top_layout)

        # 定义按钮样式，包含：默认、悬停、按下 三种状态
        btn_style = """
            QPushButton {
                background-color: #007ACC; 
                color: white; 
                border-radius: 3px;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #1A91FF; /* 鼠标悬停时：颜色变亮一点 */
            }
            QPushButton:pressed {
                background-color: #005A9E; /* 鼠标按下时：颜色变深一点 */
            }
            QPushButton:disabled {
                background-color: #555555; /* 禁用状态：灰色 */
                color: #888888;
            }
        """

        # 应用到控件
        self.btn_init_cl500.setStyleSheet(btn_style)
        self.btn_read_cl500.setStyleSheet(btn_style)

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
        # for i in range(1, 36):
        #     self.add_command_row(i)
        # 不再手动循环 range(1, 16)
        # 而是调用加载函数
        self.load_settings()

        # 如果加载后行数太少，可以补齐到 36 行（保持界面美观）
        while len(self.rows) < 36:
            self.add_command_row(len(self.rows) + 1)

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


        # --- 新增：悬停显示全名逻辑 ---
        def update_tooltip():
            text = edit_ctx.text()
            if not text:
                edit_ctx.setToolTip("")
                return

            # 如果勾选了 HEX 模式，额外显示字节数
            if chk_hex.isChecked():
                import re
                hex_len = len(re.sub(r'[^0-9a-fA-F]', '', text)) // 2
                edit_ctx.setToolTip(f"Full Data: {text}\nLength: {hex_len} Bytes")
            else:
                edit_ctx.setToolTip(f"Full Cmd: {text}\nLength: {len(text)} Chars")
        # 初始加载时跑一遍
        update_tooltip()
        # 绑定信号：文本一变，悬停提示跟着变
        edit_ctx.textChanged.connect(update_tooltip)


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

        # --- 新增：绑定自动保存信号 ---
        # 1. 当文本框内容改变时 (Context 和 ms)
        row_obj["ctx"].textChanged.connect(self.save_settings)
        row_obj["ms"].textChanged.connect(self.save_settings)
        row_obj["order"].textChanged.connect(self.save_settings)

        # 2. 当 HEX 勾选状态改变时
        row_obj["hex"].stateChanged.connect(self.save_settings)

        def on_hex_toggled(state):
            """
            state: 2 代表 Checked (Qt.CheckState.Checked), 0 代表 Unchecked
            """
            # 1. 获取当前文本并去空格
            current_text = edit_ctx.text().strip()
            if not current_text:
                return

            # 2. 暂时屏蔽信号，防止 setText 触发 textChanged 导致重复保存
            edit_ctx.blockSignals(True)

            try:
                if state == 2:  # 切换到 HEX 模式
                    # 逻辑：字符串 -> 十六进制字符串 (e.g., "help" -> "68 65 6C 70")
                    # 使用 upper() 保持 Meta Term 的专业感
                    hex_content = current_text.encode('utf-8').hex(' ').upper()
                    edit_ctx.setText(hex_content)

                else:  # 切换回 文本 模式
                    # 逻辑：十六进制字符串 -> 字符串 (e.g., "68 65 6C 70" -> "help")
                    # 移除所有空格
                    clean_hex = "".join(current_text.split())

                    # 检查长度是否为偶数，若不是则补0（简单容错）
                    if len(clean_hex) % 2 != 0:
                        clean_hex = '0' + clean_hex

                    raw_bytes = bytes.fromhex(clean_hex)

                    try:
                        # 尝试解码回文本
                        decoded_text = raw_bytes.decode('utf-8')
                        edit_ctx.setText(decoded_text)
                    except UnicodeDecodeError:
                        # 关键：如果包含 0xAA/0xFF 等不可见字符，解码会失败
                        # 此时我们不做转换，保持 HEX 原样，并在状态栏提示（可选）
                        print("Meta Term: 包含非文本字节，保持 HEX 格式。")
                        # 强制把勾选框勾回去，防止 UI 状态与内容不符
                        chk_hex.blockSignals(True)
                        chk_hex.setChecked(True)
                        chk_hex.blockSignals(False)

            except Exception as e:
                print(f"转换异常: {e}")

            # 3. 恢复信号并更新 ToolTip
            edit_ctx.blockSignals(False)
            update_tooltip()
            # 手动触发一次保存，确保 config 目录下的 cmd_config.json 实时更新
            self.save_settings()
        # 绑定勾选框状态改变信号
        chk_hex.stateChanged.connect(on_hex_toggled)

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

    def save_settings(self):
        """
        所有的控件更新都会触发这个函数，
        但它只是重置定时器，不会立即写硬盘。
        """
        self.save_timer.start(1000)  # 1000ms 后执行 _execute_save

    def _execute_save(self):
        """
        真正的 JSON 写入逻辑
        """
        config_dir = "config"
        file_path = os.path.join(config_dir, "cmd_config.json")

        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config_data = []
        for row in self.rows:
            # 即使内容为空，我们也保存结构，确保下次加载行数一致
            config_data.append({
                "order": row["order"].text(),
                "hex": row["hex"].isChecked(),
                "ctx": row["ctx"].text(),
                "ms": row["ms"].text()
            })

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            # 调试用，稳定后可以删掉这行 print
            # print("Meta Term: 配置已自动同步。")
        except Exception as e:
            print(f"自动保存失败: {e}")

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




    def load_settings(self):
        config_path = os.path.join("config", "cmd_config.json")

        # 1. 检查文件是否存在
        if not os.path.exists(config_path):
            print(f"未找到配置文件: {config_path}，将使用默认空白行。")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            if not config_data:
                return

            # 2. 清理现有的行（可选，取决于你是在构造函数还是之后调用）
            # 如果初始化时已经加了 15 行，可以先清理 self.rows 和 self.list_layout

            # 3. 按照配置重新生成行
            # 先清空旧数据结构
            for row in self.rows:
                row["widget"].deleteLater()
            self.rows.clear()

            for item in config_data:
                self.add_command_row(item)

            print(f"成功加载 {len(config_data)} 条指令配置。")

        except Exception as e:
            print(f"加载配置失败: {e}")

    def _setup_cl500_for_sub_ui(self):
        """仅在子 UI 需要时初始化"""
        # 如果线程已经在跑，且 worker 存在，说明环境是好的，直接返回
        if (hasattr(self, 'cl500_thread') and self.cl500_thread and
                self.cl500_thread.isRunning() and self.cl500_worker):
            return

        # 1. 确定 DLL 路径 (保留你原有的逻辑)
        if getattr(sys, 'frozen', False):
            BASE_DIR = os.path.dirname(sys.executable)
        else:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DLL_RELATIVE_PATH = os.path.join(BASE_DIR, "CL500A", "bin")

        self.cl500_thread = QThread()
        # 2. 尝试创建 Worker
        try:
            temp_worker = IlluminanceWorker(DLL_RELATIVE_PATH)

            # 检查 Worker 内部的路径检查是否通过
            if not temp_worker.is_valid:
                self.main_window.log_to_terminal("CL500 初始化失败：DLL 路径无效", "#E06C75")
                return

            self.cl500_worker = temp_worker

        except Exception as e:
            self.main_window.log_to_terminal(f"创建 Worker 失败: {e}", "#E06C75")
            return
        cl500_worker = IlluminanceWorker(DLL_RELATIVE_PATH)

        # 3. 只有成功创建并验证后，才开始配置线程
        self.cl500_worker.moveToThread(self.cl500_thread)

        # 【关键】监听初始化结果
        self.cl500_worker.finished_init.connect(self._on_cl500_init_result)
        self.cl500_worker.log_signal.connect(self._handle_worker_log)

        self.sig_do_init.connect(self.cl500_worker.init_sdk_not_calib)
        self.sig_do_measure.connect(self.cl500_worker.start_measure_task)

        # # 【核心】绑定日志到主 UI 的黑框
        # self.cl500_worker.log_signal.connect(
        #     lambda msg: self.main_window.log_to_terminal(f"[子功能] {msg}", "#E5C07B")
        # )
        # self.main_window.log_to_terminal("CL500 线程已安全启动", "#61AFEF")
        self.cl500_thread.start()


    def _on_cl500_init_result(self, success):
        """当初始化返回结果时调用"""
        if not success:
            self.main_window.log_to_terminal("检测到初始化失败，正在释放 CL500 线程资源...", "#E06C75")
            # 优雅地退出线程
            if self.cl500_thread:
                self.cl500_thread.quit()
                self.cl500_thread.wait()
            self.cl500_worker = None
            self.cl500_thread = None
            self.main_window.log_to_terminal("释放 CL500 线程资源完毕", "#E06C75")
        else:
            self.main_window.log_to_terminal("CL500 环境准备就绪，线程持续运行中。", "#98C379")

    def on_init_cl500_clicked(self):
        self._setup_cl500_for_sub_ui()
        # 如果已经初始化成功了，就不要重复初始化
        if self.cl500_worker.is_initialized:
            self.main_window.log_to_terminal("CL500 已在线，无需重复初始化。", "#98C379")
            return
        # 直接发射信号，Qt 会自动处理跨线程投递，不需要 invokeMethod
        self.sig_do_init.emit()

    def on_read_cl500_clicked(self):
        """点击读取按钮时的逻辑"""
        # 1. 在点击的瞬间获取最新的输入框内容
        raw_text = self.times_edit.text().strip()

        # 2. 处理默认值逻辑
        # 如果用户没填，或者是占位符文字，则默认为 1
        if not raw_text or raw_text == '次数':
            n = 1
        else:
            try:
                n = int(raw_text)
            except ValueError:
                self.main_window.log_to_terminal("次数格式错误，请输入数字", "#E06C75")
                return

        # 3. 检查 Worker 状态并执行
        if self.cl500_worker and self.cl500_worker.is_initialized:
            self.main_window.log_to_terminal(f"开始读取 CL500A，共 {n} 次...", "#D19A66")
            self.sig_do_measure.emit(n)
        else:
            self.main_window.log_to_terminal("请先完成初始化！", "#E06C75")

    # 在 MultiSendPanel 类中添加这个函数
    def _handle_worker_log(self, msg):
        """
        处理来自 CL500 Worker 的日志信号
        msg: Worker 传过来的字符串内容
        """
        if hasattr(self, 'main_window') and self.main_window:
            # 调用主窗口的打印函数，将信息显示在黑框
            # 这里建议加个前缀，方便分辨是子面板发出的信息
            self.main_window.log_to_terminal(f"[CL500] {msg}", "#E5C07B")
        else:
            # 如果找不到主窗口引用，就先打印到控制台保底
            print(f"Worker Log (No UI): {msg}")