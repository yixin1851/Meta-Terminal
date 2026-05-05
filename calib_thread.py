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

    def __init__(self, mode, values, serial_worker, sdk_workers=None):
        super().__init__()
        self.mode = mode
        self.values = values  # 目标 lux 列表 (B值)
        self.serial_worker = serial_worker
        self._response_buffer = None
        self._is_running = True
        # 读取cat文件
        self._is_collecting_file = False  # 控制开关
        self._file_buffer = ""  # 原始数据缓存
        self.sdk_workers = sdk_workers or {}  # 存放各家 SDK 实例
        """
        :param sdk_workers: 字典形式，例如 {"CL500": cl500_worker, "DN": dn_worker}
        """


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
        worker = self.sdk_workers.get("CL500")
        if not worker or not worker.is_initialized:
            self.log_signal.emit("错误：CL500 SDK 未初始化或实例不存在")
            return None

        try:
            # 由于我们已经在校准线程（子线程）中，
            # 如果 SDK Worker 也在它自己的线程，我们这里需要同步获取结果。
            # 简单做法是直接调用 worker 的测量方法（如果该方法是线程安全的）
            # 或者通过信号槽等待。为了逻辑简单，这里演示直接调用：

            self.log_signal.emit("正在通过 SDK 读取 CL500A 数据...")

            # 注意：此处应确保 worker.start_measure() 不会弹出 UI，
            # 并且能直接返回或通过变量更新结果。
            # 建议在 IlluminanceWorker 中增加一个同步测量方法：
            lux, tcp = worker.sync_measure()
            return lux
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

    def get_u_disk_path(self, target_keyword="YOD"):
        """
        终极扫描方案：同时匹配卷标 (Label) 和 硬件设备名称 (Device Name)
        """
        import psutil
        import ctypes
        import wmi  # 新增依赖

        # --- 方法 A: 扫描卷标 (Label) ---
        partitions = psutil.disk_partitions()
        for p in partitions:
            if 'cdrom' in p.opts or p.fstype == "":
                continue
            try:
                path = p.device
                volumeNameBuffer = ctypes.create_unicode_buffer(1024)
                ctypes.windll.kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(path),
                    volumeNameBuffer, ctypes.sizeof(volumeNameBuffer),
                    None, None, None, None, 0
                )
                if target_keyword.upper() in volumeNameBuffer.value.upper():
                    return path
            except:
                continue

        # --- 方法 B: 扫描硬件名称 (匹配截图 image_10e83a.png 中的 YOD USB Disk) ---
        try:
            c = wmi.WMI()
            # 寻找硬件描述中包含关键字的物理磁盘
            for drive in c.Win32_DiskDrive():
                if target_keyword.upper() in drive.Caption.upper() or \
                        target_keyword.upper() in drive.Model.upper():

                    # 找到物理磁盘后，需要关联到逻辑盘符 (如 G:)
                    for partition in drive.associators("Win32_DiskDriveToDiskPartition"):
                        for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                            # 返回盘符 (需加上斜杠确保 os.path.join 正确)
                            return logical_disk.DeviceID + "\\"
        except Exception as e:
            self.log_signal.emit(f"WMI 硬件扫描异常: {e}")

        return None

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
            if not any_changed:
                import os
                import json
                from datetime import datetime
                import shutil  # 用于文件复制

                # 1. 路径初始化
                u_disk_path = self.get_u_disk_path("YOD")
                local_root = os.getcwd()  # 程序根目录
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                local_file_path = os.path.join(local_root, "yod_calib.jsonl")

                try:
                    # --- 第一步：处理本地文件的备份 ---
                    if os.path.exists(local_file_path):
                        local_backup = os.path.join(local_root, f"yod_calib_{timestamp}.jsonl")
                        os.rename(local_file_path, local_backup)
                        self.log_signal.emit(f"📦 本地既有文件已备份: {os.path.basename(local_backup)}")

                    # --- 第二步：处理 U 盘逻辑 ---
                    if u_disk_path:
                        u_file_path = os.path.join(u_disk_path, "yod_calib.jsonl")

                        # 如果 U 盘里也有老文件，先在 U 盘备份
                        if os.path.exists(u_file_path):
                            u_backup = os.path.join(u_disk_path, f"yod_calib_{timestamp}.jsonl")
                            os.rename(u_file_path, u_backup)
                            self.log_signal.emit(f"📦 U 盘既有文件已备份: {os.path.basename(u_backup)}")

                        # 将新数据写入 U 盘
                        with open(u_file_path, "w", encoding="utf-8") as f:
                            sorted_keys = sorted(organized_data.keys(), key=lambda x: float(x))
                            for k in sorted_keys:
                                line = json.dumps(organized_data[k], ensure_ascii=False)
                                f.write(line + "\n")
                        self.log_signal.emit(f"💾 新配置已成功写入 U 盘: {u_file_path}")

                        # 从 U 盘同步回本地
                        shutil.copy2(u_file_path, local_file_path)
                        self.log_signal.emit(f"🚀 已从 U 盘同步更新至本地根目录")

                    else:
                        # 如果没插 U 盘，则直接写入本地
                        self.log_signal.emit("⚠️ 未检测到 U 盘，直接更新本地配置文件")
                        with open(local_file_path, "w", encoding="utf-8") as f:
                            sorted_keys = sorted(organized_data.keys(), key=lambda x: float(x))
                            for k in sorted_keys:
                                line = json.dumps(organized_data[k], ensure_ascii=False)
                                f.write(line + "\n")
                        self.log_signal.emit(f"💾 新配置已写入本地: {local_file_path}")

                except Exception as e:
                    self.log_signal.emit(f"⚠️ [错误] 流程执行失败: {str(e)}")
            else:
                self.log_signal.emit("ℹ️ [信息] 所有点位均在范围内，配置文件未做改动")

            self.finished_signal.emit("所有校准任务处理完毕")

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            self.finished_signal.emit(f"运行时错误: {str(e)}")