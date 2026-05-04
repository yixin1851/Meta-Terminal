from PySide6.QtCore import QThread, Signal
import time
import re
import json


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
                    if "lux" in data:
                        organized_data[data["lux"]] = data
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

    def run_calibration_algorithm(self, item):
        """
        校准核心比对逻辑
        """
        target_lux = item["lux"]  # UI/JSON 设定的标准点位
        b_ref = item["getlux"]  # 理想参考值 B (来自 JSON)
        l_up = item.get("Lup", -1)  # 允许的上限
        l_down = item.get("Ldown", -1)  # 允许的下限

        self.log_signal.emit(f"开始校验点位 {target_lux}: 目标参考值 B={b_ref}")

        # 1. 初始测试：直接设置目标 Lux
        self.send_cmd(f"set_lux 0")
        time.sleep(2)
        self.send_cmd("get_lux")
        a_val_0 = self.wait_for_response()  # 获取实测值 A
        self.send_cmd(f"set_lux {target_lux:.2f}")
        time.sleep(0.8)
        self.send_cmd("get_lux")
        a_val = self.wait_for_response() - a_val_0  # 获取实测值 A
        self.log_signal.emit(f"set_lux {target_lux} 归零值为: {a_val:.2f}")

        if a_val is None:
            return False, "设备无响应"

        # 打印当前 A 和 B 的状态
        self.log_signal.emit(f"初始读取: 实测 A={a_val:.2f}, 参考 B={b_ref:.2f}")

        # 2. 范围判定：检查 A 是否落在 [Ldown, Lup] 区间内
        in_range = True
        if l_up != -1 and a_val > l_up: in_range = False
        if l_down != -1 and a_val < l_down: in_range = False

        if in_range:
            self.log_signal.emit(f"结果: A 在 [{l_down}, {l_up}] 范围内，无需校准。")
            return True, a_val,None

        # 3. 步进微调：如果不在区间内，则寻找使 A 逼近 B 的输入值
        self.log_signal.emit(f"提示: A 超出范围，进入 1% 误差微调模式...")

        # 搜索偏置：从 -20% 到 +20%
        search_offsets = [x for x in range(-10, 11) if x != 0]

        for pct in search_offsets:
            test_input = target_lux * (1 + pct / 100.0)
            self.send_cmd(f"set_lux {test_input:.2f}")
            time.sleep(1)
            self.send_cmd("get_lux")
            a_val = self.wait_for_response()

            if a_val is not None:
                # 计算 A 与 B 的相对误差
                diff_pct = abs(a_val - b_ref) / b_ref
                # print(f"微调中: 输入={test_input:.2f}, 得到 A={a_val:.2f}, 误差={diff_pct:.2%}")

                if diff_pct <= 0.01:  # 1% 误差内
                    self.log_signal.emit(f"微调成功: 输入 {test_input:.2f} 时，实测 get_lux={a_val:.2f} 逼近 getlux={b_ref:.2f}")
                    return True, a_val,test_input

        return False, f"微调结束，未能将数值调整至目标的 1% 误差内 (最后 getlux={a_val})"

    def run(self):
        try:
            # 1 & 2. 获取并截取数据 (代码省略，保持你原有的即可)
            self._is_collecting_file = True
            self._file_buffer = ""
            self.send_cmd("cat yod_calib.jsonl")
            raw_text = self.wait_for_file_content(timeout=10)
            self._is_collecting_file = False
            any_changed = False

            if not raw_text:
                self.log_signal.emit(">>> [ERROR] 未能读取到配置文件内容")
                return

            # 3. 整理数据 (将 Key 强制处理为字符串，增加匹配成功率)
            organized_data = self.parse_and_organize_configs(raw_text)
            self.log_signal.emit(f">>> [SYS] 配置文件加载成功，共 {len(organized_data)} 组数据")

            # 4. 执行校准逻辑
            # 注意：这里我们遍历 UI 传来的 self.values
            if not self.values:
                self.log_signal.emit(">>> [WARN] UI 未传入任何待校准点位")
                return

            for val in self.values:
                # 关键修复：统一匹配格式。将 UI 的 10.0 转为字符串 "10"
                # 如果你的 JSON key 是数字，这里可以使用 int(float(val))
                try:
                    search_key = int(float(val))
                except:
                    search_key = val

                item = organized_data.get(search_key)

                if not item:
                    self.log_signal.emit(f">>> [SKIP] 点位 {val} 不在配置文件中，跳过")
                    continue

                # 执行算法 - 获取三个返回值
                # 在 run 方法中调用
                success, a_val, test_input = self.run_calibration_algorithm(item)

                if success:
                    if test_input is None:
                        # 情况 A：在范围内，无需改写 JSON
                        self.log_signal.emit(f"✅ 点位 {val} 状态良好，跳过修改")
                    else:
                        # 情况 B：执行了微调，需要改写 JSON
                        lk_factor = test_input / item["lux"]
                        item["getlux"] = round(a_val, 2)
                        item["Lk"] = round(lk_factor, 4)
                        any_changed = True
                        self.log_signal.emit(f"📝 点位 {val} 校准成功，已更新内存数据")
                else:
                    # 这里的 a_val 是错误描述字符串
                    self.log_signal.emit(f"❌ 点位 {item['lux']} 校准失败: {a_val}")
            # --- 第四阶段：统一写入本地文件 ---
            if not any_changed:
                import os
                from datetime import datetime

                file_name = "yod_calib.jsonl"

                try:
                    # 1. 检查是否存在旧文件，如果存在则备份
                    if os.path.exists(file_name):
                        # 生成时间戳后缀，例如：yod_calib_20260504_203015.jsonl
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_name = f"yod_calib_{timestamp}.jsonl"

                        os.rename(file_name, backup_name)
                        self.log_signal.emit(f"📦 已备份旧配置为: {backup_name}")

                    # 2. 新建并写入最新的校准数据
                    with open(file_name, "w", encoding="utf-8") as f:
                        # 按 lux 大小排序写入
                        sorted_keys = sorted(organized_data.keys())
                        for k in sorted_keys:
                            line = json.dumps(organized_data[k], ensure_ascii=False)
                            f.write(line + "\n")

                    self.log_signal.emit(f"💾 [成功] 新配置已写入 {file_name}")

                except Exception as e:
                    self.log_signal.emit(f"⚠️ [错误] 文件操作失败: {str(e)}")
            else:
                self.log_signal.emit("ℹ️ [信息] 没有数据变动，跳过文件更新")

            self.finished_signal.emit("所有校准任务处理完毕")

        except Exception as e:
            import traceback
            print(traceback.format_exc())  # 打印详细报错到控制台
            self.finished_signal.emit(f"运行时错误: {str(e)}")