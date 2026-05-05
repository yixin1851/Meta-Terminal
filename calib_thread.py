from PySide6.QtCore import QThread, Signal
import time
import re
import json

# 模式配置映射表
MODE_CONFIG = {
    "Lux": {
        "cmd": "get_lux",
        "ref": "getlux",
        "up": "Lup",
        "down": "Ldown",
        "k_factor": "LK",
        "b_factor": "LB",
        "val_field": "getlux"
    },
    "PD": {
        "cmd": "get_opt_lux",
        "ref": "PD_value",
        "up": "PDup",
        "down": "PDdown",
        "k_factor": "PDK",
        "b_factor": "PDB",
        "val_field": "PD_value"
    },
    "CL500": {
        "cmd": "CL500_SDK",
        "ref": "CL500_value",
        "up": "CL500up",
        "down": "CL500down",
        "k_factor": "CL500K",
        "b_factor": "CL500B",
        "val_field": "CL500_value"
    },
    "DN": {
        "cmd": "DN_SDK",  # 修改为 SDK 模式
        "ref": "DN_value",
        "up": "DNup",
        "down": "DNdown",
        "k_factor": "DNK",
        "b_factor": "DNB",
        "val_field": "DN_value"
    },
    "other": {
        "cmd": "OTHER_SDK", # 修改为 SDK 模式
        "ref": "other_value",
        "up": "otherup",
        "down": "otherdown",
        "k_factor": "otherK",
        "b_factor": "otherB",
        "val_field": "other_value"
    }
}

class CalibrationThread(QThread):
    # 定义信号，用于把进度或结果传回主界面
    finished_signal = Signal(str)
    log_signal = Signal(str)

    def __init__(self, mode, values, serial_worker):
        super().__init__()
        self.mode = mode
        self.values = values  # 目标 lux 列表 (B值)
        self.serial_worker = serial_worker
        self._response_buffer = None
        self._is_running = True
        # 读取cat文件
        self._is_collecting_file = False  # 控制开关
        self._file_buffer = ""  # 原始数据缓存

    def parse_and_organize_configs(self, raw_text):
        """
        将 cat 拿到的原始文本整理为结构化字典
        """
        organized_data = {}
        # splitlines() 自动处理 \r\n，strip() 去除首尾空格
        for line in raw_text.splitlines():
            line = line.strip()
            # 只处理符合 JSON 特征的行
            if line.startswith('{') and line.endswith('}'):
                try:
                    data = json.loads(line)
                    # 以 lux 值作为索引存入字典，方便后续直接查找使用
                    if "Lux" in data:
                        # organized_data[data["Lux"]] = data
                        search_key = format(float(data["Lux"]), '.2f')
                        organized_data[search_key] = data
                except json.JSONDecodeError:
                    continue
        return organized_data

    def execute_logic_with_config(self, ui_lux, organized_data):
        """
        使用整理好的数据执行业务逻辑
        """
        # 直接根据 UI 传入的数字从字典里取数
        config_item = organized_data.get(ui_lux)

        if not config_item:
            self.log_signal.emit(f"错误：配置中未找到 Lux {ui_lux}")
            return False

        # 此时你可以直接使用 config_item 里的任意字段
        # 例如：target_b = config_item["get_lux"]
        self.log_signal.emit(f"正在使用点位 {ui_lux} 的配置: {config_item}")

        # 在这里编写你需要的发送指令或其他逻辑...
        return True

    def wait_for_file_content(self, timeout=5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 只要缓冲区包含提示符，说明传输可能已完成
            if "msh />" in self._file_buffer:
                # 1. 寻找最后一个 "msh />" 的位置作为结束点
                # 使用 rfind 是为了处理连续出现多个 msh /> 的情况
                end_pos = self._file_buffer.rfind("msh />")

                # 2. 截取从开头到最后一个提示符之前的内容
                raw_data = self._file_buffer[:end_pos]

                # 3. 剔除第一行的命令回显 (cat yod_calib.jsonl)
                # 寻找第一个换行符的位置
                first_newline = raw_data.find('\n')
                if first_newline != -1:
                    # 截取第一行之后的所有内容并修整空白
                    final_content = raw_data[first_newline:].strip()
                    if final_content:
                        return final_content
            time.sleep(0.1)
        self.log_signal.emit("读取配置文件超时或内容为空")
        return None

    def send_cmd(self, cmd_str):
        """
        统一发送字符串命令的函数
        :param cmd_str: 命令字符串，如 "set_lux 100.0"
        """
        if not cmd_str:
            return

        # 拼接换行符并转为字节流
        full_cmd = f"{cmd_str}\r\n".encode('utf-8')

        # 调用 serial_worker 发送
        if self.serial_worker and self.serial_worker.running:
            self.serial_worker.send_async(full_cmd)
            # 在日志中记录发出的指令
            # self.log_signal.emit(f"TX -> {cmd_str}")

    def receive_answer(self, data_str, is_raw=False):
        """
        由 MainWindow 调用，将从串口解析出的数字喂给线程
        """
        if is_raw:
            self._file_buffer += data_str
        try:
            # 提取字符串中的浮点数
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", data_str)
            if nums:
                self._response_buffer = float(nums[0])
        except Exception as e:
            print(f"解析返回值异常: {e}")

    def wait_for_response(self, timeout=5):
        """
        同步阻塞等待串口返回 A 值
        """
        start_time = time.time()
        self._response_buffer = None
        while time.time() - start_time < timeout:
            if self._response_buffer is not None:
                val = self._response_buffer
                self._response_buffer = None  # 用完清空
                return val
            time.sleep(0.01)
        return None

    def read_cl500_sdk_data(self):
        """
        对接 Konica Minolta CL-500A 照度计的 SDK
        """
        try:
            self.log_signal.emit("正在通过 SDK 读取 CL500A 照度数据...")
            # 真实逻辑示例：
            # 1. 检查 SDK 对象是否初始化
            # 2. 调用 SDK 的测量方法：self.cl500.measure()
            # 3. 获取勒克斯值：val = self.cl500.get_illuminance()
            # return float(val)

            # 暂时返回模拟值用于测试
            return 0.0
        except Exception as e:
            self.log_signal.emit(f"CL500 SDK 读取异常: {e}")
            return None

    def read_dn_sdk_data(self):
        """
        对接 DN 传感器的 SDK
        """
        try:
            self.log_signal.emit("正在通过 SDK 读取 DN 数据...")
            # 真实逻辑：调用对应的 DLL 或 Python 包装类
            return 0.0
        except Exception as e:
            self.log_signal.emit(f"DN SDK 读取异常: {e}")
            return None

    def read_other_sdk_data(self):
        """
        对接三方 generic 传感器的 SDK
        """
        try:
            self.log_signal.emit("正在通过 SDK 读取 Other 传感器数据...")
            return 0.0
        except Exception as e:
            self.log_signal.emit(f"Other SDK 读取异常: {e}")
            return None

    def get_current_sensor_value(self):
        cfg = MODE_CONFIG.get(self.mode)
        if not cfg:
            return None

        cmd_type = cfg["cmd"]

        # --- SDK 模式分发 ---
        if cmd_type == "CL500_SDK":
            return self.read_cl500_sdk_data()

        elif cmd_type == "DN_SDK":
            # 调用你定义的 DN SDK 读取函数
            return self.read_dn_sdk_data()

        elif cmd_type == "OTHER_SDK":
            # 调用你定义的 Other SDK 读取函数
            return self.read_other_sdk_data()

        # 传统的串口发送与等待模式 (Lux, PD)
        else:
            self.send_cmd(cmd_type)
            return self.wait_for_response()

    def run_calibration_algorithm(self, item):
        """
            校准核心比对逻辑 - 支持各模式独立 Up/Down 判断
            """
        cfg = MODE_CONFIG.get(self.mode)
        if not cfg:
            return False, "未知模式", None

        # --- 动态获取当前模式的上下限和参考值 ---
        target_lux = item["Lux"]
        b_ref = item.get(cfg["ref"], -1)
        current_up = item.get(cfg["up"], -1)  # 独立判断：读取当前模式的 Up
        current_down = item.get(cfg["down"], -1)  # 独立判断：读取当前模式的 Down

        self.log_signal.emit(f"[{self.mode}校准] 点位:{target_lux}, 范围:[{current_down}, {current_up}]")

        self.log_signal.emit(f"校验点位 {target_lux}: 目标参考值 = {b_ref}")

        # 1. 初始测试：直接设置目标 Lux
        self.send_cmd(f"set_lux 0")
        time.sleep(2)
        a_val_0 = self.get_current_sensor_value() # 自动切换读取方式
        self.send_cmd(f"set_lux {target_lux:.2f}")
        time.sleep(1)
        if a_val_0 is None:
            return False, "传感器读取超时", None
        a_val = self.get_current_sensor_value() - a_val_0 # 自动切换读取方式
        self.log_signal.emit(f"set_lux {target_lux} 归零值为: {a_val:.2f}")

        # 打印当前 A 和 B 的状态
        self.log_signal.emit(f"初始读取: 实测值 = {a_val:.2f}, 目标值 = {b_ref:.2f}")

        # 2. 独立判定逻辑：使用当前模式对应的上下限
        in_range = True
        # 只有当 JSON 里的值不为 -1 时才执行判断
        if current_up != -1 and a_val > current_up:
            in_range = False
        if current_down != -1 and a_val < current_down:
            in_range = False

        if in_range:
            self.log_signal.emit(f"✅ 判定合格: {a_val:.2f} 落在 {self.mode} 专属区间内")
            return True, a_val, None

        # --- 定向步进微调 ---
        self.log_signal.emit(f"提示: {self.mode} 实测值超限，开始定向搜索微调...")

        # 根据偏离方向决定搜索范围，优化效率
        if a_val < current_down:
            # 实测偏低，向上微调 (1% 到 10%)
            search_offsets = list(range(1, 11))
            direction_msg = "实测偏低 ⬆️ 向上微调"
        elif a_val > current_up:
            # 实测偏高，向下微调 (-1% 到 -10%)
            search_offsets = list(range(-1, -11, -1))
            direction_msg = "实测偏高 ⬇️ 向下微调"
        else:
            # 兜底逻辑
            search_offsets = [x for x in range(-10, 11) if x != 0]
            direction_msg = "全范围微调"

        self.log_signal.emit(f"诊断结果: {direction_msg}")

        for pct in search_offsets:
            # 计算微调后的光源输出值 (target_lux 始终是物理标准参考)
            test_input = target_lux * (1 + pct / 100.0)
            self.send_cmd(f"set_lux {test_input:.2f}")
            time.sleep(1)

            # 自动根据模式读取实测值 (串口或各家 SDK)
            raw_a = self.get_current_sensor_value()

            if raw_a is not None:
                # 减去环境底噪得到实际测量值
                a_val_test = raw_a - a_val_0

                # 计算实测值与当前模式理想参考值 B 的相对误差
                # b_ref 已经在函数开头根据模式动态获取 (如 item["PD_value"])
                diff_pct = abs(a_val_test - b_ref) / b_ref

                if diff_pct <= 0.01:  # 进入 1% 误差内
                    # 动态格式化日志：显示当前模式的字段名
                    self.log_signal.emit(
                        f"✨ {self.mode} 微调成功: 光源设为 {test_input:.2f} 时, "
                        f"实测 {cfg['val_field']}={a_val_test:.2f} 成功逼近参考值 {b_ref:.2f}"
                    )
                    return True, a_val_test, test_input

        return False, f"微调结束，未能将 {self.mode} 数值调整至目标的 1% 误差内", None

    def run(self):
        try:
            # 1 & 2. 获取并截取数据 (保持原有逻辑)
            self._is_collecting_file = True
            self._file_buffer = ""
            self.send_cmd("cat yod_calib.jsonl")
            raw_text = self.wait_for_file_content(timeout=10)
            self._is_collecting_file = False
            any_changed = False

            if not raw_text:
                self.log_signal.emit(">>> [ERROR] 未能读取到配置文件内容")
                self.finished_signal.emit("失败：配置文件不存在")  # 必须发送完成信号，否则 UI 会一直卡在“校准中”
                return

            # 3. 整理数据
            organized_data = self.parse_and_organize_configs(raw_text)
            self.log_signal.emit(f">>> [SYS] 配置文件加载成功，共 {len(organized_data)} 组数据")

            # 获取当前模式配置映射
            cfg = MODE_CONFIG.get(self.mode)
            if not cfg:
                self.log_signal.emit(f">>> [ERROR] 未定义模式: {self.mode}")
                return

            # 4. 执行校准逻辑
            if not self.values:
                self.log_signal.emit(">>> [WARN] UI 未传入任何待校准点位")
                return

            for val in self.values:
                try:
                    search_key = format(float(val), '.2f')
                except:
                    search_key = val

                item = organized_data.get(search_key)

                if not item:
                    self.log_signal.emit(f">>> [SKIP] 点位 {val} 不在配置文件中，跳过")
                    continue

                # 执行算法
                success, a_val_result, test_input = self.run_calibration_algorithm(item)

                if success:
                    if test_input is None:
                        # 情况 A：在范围内，无需改写 JSON
                        self.log_signal.emit(f"✅ 点位 {val} 的 {self.mode} 状态良好，无需修改")
                    else:
                        # 情况 B：执行了微调，需要根据当前模式改写 JSON 对应字段
                        # 计算 K 系数：微调后的输入 / 原始标准值
                        k_factor = test_input / item["Lux"]
                        b_factor = test_input - item["Lux"]

                        # 动态更新字段：如 getlux/Lk 或 PD_value/PDK 等
                        item[cfg["val_field"]] = round(a_val_result, 2)
                        item[cfg["k_factor"]] = round(k_factor, 4)
                        item[cfg["b_factor"]] = round(b_factor, 4)

                        any_changed = True
                        self.log_signal.emit(f"📝 点位 {val} 校准成功，更新字段: {cfg['val_field']}, {cfg['k_factor']}")
                else:
                    # 这里的 a_val_result 在失败时是错误描述
                    self.log_signal.emit(f"❌ 点位 {val} 校准失败: {a_val_result}")

            # --- 第五阶段：统一写入本地文件 ---
            # 修正逻辑：只有当 any_changed 为 True 时才写入文件
            if any_changed:
                import os
                import json
                from datetime import datetime

                file_name = "yod_calib.jsonl"
                try:
                    # 1. 备份旧配置
                    if os.path.exists(file_name):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_name = f"yod_calib_{timestamp}.jsonl"
                        os.rename(file_name, backup_name)
                        self.log_signal.emit(f"📦 数据已变动，备份旧配置为: {backup_name}")

                    # 2. 写入新配置
                    with open(file_name, "w", encoding="utf-8") as f:
                        # 按 lux 大小排序写入，确保文件整齐
                        sorted_keys = sorted(organized_data.keys(), key=lambda x: float(x))
                        for k in sorted_keys:
                            line = json.dumps(organized_data[k], ensure_ascii=False)
                            f.write(line + "\n")

                    self.log_signal.emit(f"💾 [成功] 新配置已写入 {file_name}")

                except Exception as e:
                    self.log_signal.emit(f"⚠️ [错误] 文件操作失败: {str(e)}")
            else:
                self.log_signal.emit("ℹ️ [信息] 所有点位均在范围内，配置文件未做改动")

            self.finished_signal.emit("所有校准任务处理完毕")

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            self.finished_signal.emit(f"运行时错误: {str(e)}")