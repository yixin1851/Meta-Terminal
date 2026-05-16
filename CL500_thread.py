import os
import time
import ctypes
import logging
from PySide6.QtCore import QObject, Signal, Slot, QThread,Qt

# ================= SDK 常量定义 =================
SUCCESS = 0
CL_CALIBMEAS_FINISH = 2
CL_MEAS_FINISH = 2
CL_COLORSPACE_EVTCPDUV = 3

# SDK 可能会返回的无效值/超量程值 (根据 KM SDK 手册补充)
INVALID_VAL = 9.9e37


# ================= 日志系统集成 =================

class SignalHandler(logging.Handler):
    """将 logging 输出转发到 Qt Signal"""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)


# ================= SDK 结构体定义 =================

class CL_EvxyDATA(ctypes.Structure):
    _fields_ = [("Ev", ctypes.c_float), ("x", ctypes.c_float), ("y", ctypes.c_float)]

class CL_EvTduvDATA(ctypes.Structure):
    _fields_ = [("Ev", ctypes.c_float), ("Tcp", ctypes.c_float), ("duv", ctypes.c_float)]

# 使用 ctypes.Union 来完美还原 C++ 的定义
class CL_MEASDATA(ctypes.Union):
    _fields_ = [
        ("Evxy", CL_EvxyDATA),
        ("EvTduv", CL_EvTduvDATA),
        # 如果需要其他成员，可以在此继续添加
        ("padding", ctypes.c_byte * 8192) # 这里写512程序老奔溃，写2048以上就没问题，当一个CL500的经验教训吧
    ]



# ================= 业务逻辑线程类 =================

class IlluminanceWorker(QObject):
    # 数据信号
    result_signal = Signal(float, float)  # 单次 Lux, Tcp
    avg_result_signal = Signal(float, float)  # 平均 Lux, Tcp
    sync_measure_done = Signal(object)  # 校准线程同步等待的单次测量结果
    # 状态信号
    log_signal = Signal(str)  # 统一的日志信号
    finished_init = Signal(bool) # 未校准初始化
    measure_done_signal = Signal()
    finished_init_cl500_calib = Signal(bool) #校准初始化



    def __init__(self, dll_folder):
        super().__init__()
        self.dll_folder = dll_folder
        self.handle = ctypes.c_void_p(0)
        self.cl_api = None
        self._dll_dir_cookie = None
        self.is_initialized = False
        self._is_running = False
        # 如果通过了初步检查
        self.is_valid = False

        # 在初始化时，把信号连到自己的函数上
        # self.sig_do_init.connect(self.init_sdk_not_calib)
        # self.sig_do_measure.connect(self.start_measure_task)
        # self.sig_do_measure.connect(self.start_measure_task, Qt.QueuedConnection)

        # 配置专属于该类的 Logger，避免污染全局 logging
        self.logger = logging.getLogger(f"CL500A_{id(self)}")
        self.logger.handlers.clear()  # 清空旧的处理器
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # 防止重复打印

        # 绑定信号处理器
        handler = SignalHandler(self.log_signal)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # 初步检查：文件夹是否存在
        if not os.path.exists(dll_folder):
            print(f"Critial Error: DLL folder not found: {dll_folder}")
            return

        # 如果通过了初步检查
        self.is_valid = True

    def _ensure_sdk_loaded(self):
        """加载 CL500A SDK，避免切换全局工作目录影响主程序路径。"""
        if self.cl_api is not None:
            return True

        dll_path = os.path.join(self.dll_folder, "libclapi.dll")
        if not os.path.exists(dll_path):
            self.logger.error(f"找不到 DLL 文件: {dll_path}")
            return False

        if hasattr(os, 'add_dll_directory') and self._dll_dir_cookie is None:
            self._dll_dir_cookie = os.add_dll_directory(self.dll_folder)

        self.cl_api = ctypes.CDLL(dll_path)
        return True

    @Slot()
    def init_sdk(self):
        """初始化 SDK 并进行零校准 (支持重用已打开的设备)"""
        try:
            # --- 1. 基础环境加载 (仅在初次运行时执行) ---
            if not self._ensure_sdk_loaded():
                self.finished_init_cl500_calib.emit(False)
                return False

            # --- 2. 设备连接逻辑 ---
            # 如果 handle 为空或者为 0，说明设备还没打开
            if not self.handle or self.handle.value == 0:
                if self.cl_api.CLOpenDevice(ctypes.byref(self.handle)) == SUCCESS:
                    self.cl_api.CLSetRemoteMode(self.handle, 1)
                    self.logger.info("CL500A设备连接成功。")
                else:
                    self.logger.error("错误：未检测到CL500A设备，请检查 USB 连接。")
                    self.finished_init_cl500_calib.emit(False)
                    return False

            else:
                self.logger.info("设备已处于连接状态，准备开始重新校准...")

            # --- 3. 执行零校准 (无论设备是刚开还是之前开的) ---
            # 确保处于远程模式
            self.cl_api.CLSetRemoteMode(self.handle, 1)

            self.logger.info("开始零校准 (约需 10-30 秒)...")
            self.cl_api.CLDoCalibration(self.handle)

            # 轮询校准状态
            c_status = ctypes.c_int(0)
            start_cal = time.time()
            timeout = 40  # 设定超时阈值

            self.logger.info("零校准进行中，请勿遮挡传感器...")

            while c_status.value != CL_CALIBMEAS_FINISH:
                elapsed = time.time() - start_cal

                # 每隔约 1 秒打印一次进度 (0.2s * 5)
                # 或者直接每次循环都更新（如果你希望进度条更丝滑）
                if elapsed > timeout:
                    raise TimeoutError(f"CL500A设备零校准响应超时 (已耗时 {elapsed:.1f}s)")

                # 打印当前进度
                # \r 实现原地刷新（仅限控制台），logger 则会逐行记录
                print(f"校准中... 已耗时: {elapsed:.1f}s / {timeout}s", end='\r')

                # 如果你想在 UI 的 log_to_terminal 看到跳动，可以每隔 2 秒发一次
                if int(elapsed * 5) % 10 == 0:  # 约每 2 秒进入一次
                    self.logger.info(f"校准进度：已耗时 {elapsed:.1f} 秒...")

                time.sleep(0.2)
                self.cl_api.CLPollingCalibration(self.handle, ctypes.byref(c_status))

            self.is_initialized = True
            self.finished_init_cl500_calib.emit(True)
            self.logger.info("CL500A照度计零校准完成。")
            return True


        except Exception as e:
            self.logger.exception(f"CL500A初始化/校准异常: {str(e)}")
            self.finished_init_cl500_calib.emit(False)
            return False


    @Slot()
    def init_sdk_not_calib(self):
        """仅初始化 SDK (如果设备已打开则直接返回成功)"""
        try:
            # 如果已经初始化过且句柄有效，直接报成功
            if self.is_initialized and self.handle and self.handle.value != 0:
                self.logger.info("设备已连接，无需重复初始化。")
                self.finished_init.emit(True)
                return True

            if not self._ensure_sdk_loaded():
                self.finished_init.emit(False)
                return False

            if self.cl_api.CLOpenDevice(ctypes.byref(self.handle)) == SUCCESS:
                self.cl_api.CLSetRemoteMode(self.handle, 1)
                self.is_initialized = True
                self.logger.info("CL500A设备连接成功...")
                self.finished_init.emit(True)
                return True
            else:
                self.logger.error("错误：未检测到CL500A设备。")
                self.finished_init.emit(False)
                return False

        except Exception as e:
            self.logger.exception(f"CL500A连接异常: {str(e)}")
            self.finished_init.emit(False)
            return False




    @Slot()
    def measure_once_for_calibration(self):
        """在 CL500 工作线程中执行单次同步测量，并把结果发回等待方。"""
        self.sync_measure_done.emit(self.sync_measure())


    @Slot(int)
    def start_measure_task(self, n):
        """执行 n 次测量并计算平均值"""
        if not self.is_initialized:
            self.logger.warning("CL500A设备未就绪，请先执行初始化。")
            return

        self._is_running = True
        measurements = []  # 使用列表记录有效数据

        self.logger.info(f">>> 开始CL500A测量任务 (次数: {n})")

        for i in range(n):
            if not self._is_running:
                self.logger.info("检测到停止信号，CL500A测量任务提前结束。")
                break

            exposure = ctypes.c_int32(0)
            ret = self.cl_api.CLDoMeasurement(self.handle, ctypes.byref(exposure))

            if ret == SUCCESS:
                success = False
                start_p = time.time()
                # 轮询状态，增加 self._is_running 判断实现快速退出
                while self._is_running:
                    # 检查是否超过了 60 秒
                    if (time.time() - start_p) > 60:
                        self.logger.error(f"[{i + 1}/{n}] 错误: CL500A测量响应超时 (已等待 {60}s)。")
                        break
                    status = ctypes.c_int(0)
                    self.cl_api.CLPollingMeasure(self.handle, ctypes.byref(status))
                    if status.value == CL_MEAS_FINISH:
                        success = True
                        break
                    time.sleep(0.1)

                if success:
                    # print("准备GetData")
                    data = CL_MEASDATA()
                    # print("结构体大小:", ctypes.sizeof(self._measure_data_buffer))
                    ret_get = self.cl_api.CLGetMeasData(self.handle, CL_COLORSPACE_EVTCPDUV,
                                                        ctypes.byref(data))

                    if ret_get == SUCCESS:
                        # 3. 提取值
                        lux = data.Evxy.Ev
                        tcp = data.EvTduv.Tcp

                        # 数据合法性基本过滤
                        # CL500A 的测量上限通常不会超过 1,00,000 Lux，色温不会超过 100,000K
                        if 0 <= lux < 100000 and 0 <= tcp < 100000:
                            measurements.append((lux, tcp))
                            self.logger.info(f"[{i + 1}/{n}] 成功: {lux:.2f} Lux | {tcp:.0f} K")
                            self.result_signal.emit(lux, tcp)
                        else:
                            self.logger.warning(f"[{i + 1}/{n}] 警告: 读数超出CL500A设备量程。")
                    else:
                        self.logger.error(f"CLGetMeasData 失败，代码: {ret_get}")
                else:
                    self.logger.error(f"[{i + 1}/{n}] 错误: 测量响应超时。")
            else:
                self.logger.error(f"[{i + 1}/{n}] 错误: 触发指令失败 (Code: {ret})。")

            time.sleep(0.1)

        # --- 最终统计逻辑 ---
        if measurements:
            avg_lux = sum(m[0] for m in measurements) / len(measurements)
            avg_tcp = sum(m[1] for m in measurements) / len(measurements)
            self.logger.info(f"任务完成！有效样本: {len(measurements)}/{n}")
            self.logger.info(f"平均照度: {avg_lux:.2f} Lux, 平均色温: {avg_tcp:.0f} K")
            self.avg_result_signal.emit(avg_lux, avg_tcp)
        else:
            self.logger.warning("任务结束，但未采集到任何有效数据。")

        self.measure_done_signal.emit()
        self._is_running = False

    def sync_measure(self):
        """
        提供给校准线程调用的同步测量方法。
        直接返回 (lux, tcp)，如果失败返回 (None, None)
        """
        started_here = False
        try:
            if not self.is_initialized or not self.handle or self.handle.value == 0 or self.cl_api is None:
                self.logger.warning("CL500A设备未就绪，请先执行初始化。")
                return None, None

            if self._is_running:
                self.logger.warning("CL500A正在执行其他测量任务，请稍后重试。")
                return None, None

            self._is_running = True
            started_here = True
            exposure = ctypes.c_int32(0)
            ret = self.cl_api.CLDoMeasurement(self.handle, ctypes.byref(exposure))

            if ret == SUCCESS:
                success = False
                start_p = time.time()
                # 轮询状态，增加 self._is_running 判断实现快速退出
                while self._is_running:
                    # 检查是否超过了 60 秒
                    if (time.time() - start_p) > 60:
                        self.logger.error(f"错误: CL500A测量响应超时 (已等待 {60}s)。")
                        break
                    status = ctypes.c_int(0)
                    self.cl_api.CLPollingMeasure(self.handle, ctypes.byref(status))
                    if status.value == CL_MEAS_FINISH:
                        success = True
                        break
                    time.sleep(0.1)

                if success:
                    # print("准备GetData")
                    data = CL_MEASDATA()
                    # print("结构体大小:", ctypes.sizeof(self._measure_data_buffer))
                    ret_get = self.cl_api.CLGetMeasData(self.handle, CL_COLORSPACE_EVTCPDUV,
                                                        ctypes.byref(data))

                    if ret_get == SUCCESS:
                        # 3. 提取值
                        lux = data.Evxy.Ev
                        tcp = data.EvTduv.Tcp

                        # 数据合法性基本过滤
                        # CL500A 的测量上限通常不会超过 1,00,000 Lux，色温不会超过 100,000K
                        if 0 <= lux < 100000 and 0 <= tcp < 100000:
                            self.result_signal.emit(lux, tcp)
                            return lux, tcp
                        else:
                            self.logger.warning("警告: 读数超出CL500A设备量程。")
                    else:
                        self.logger.error(f"CLGetMeasData 失败，代码: {ret_get}")
                else:
                    self.logger.error("错误: 测量响应超时。")
            else:
                self.logger.error(f"错误: 触发指令失败 (Code: {ret})。")
        except Exception as e:
            print(f"SDK内部测量错误: {e}")
            return None, None
        finally:
            if started_here:
                self._is_running = False

        return None, None

    def stop_task(self):
        """用于从外部强制中断测量循环"""
        self._is_running = False

    def close_device(self):
        """释放设备句柄并清理"""
        self.stop_task()
        if self.handle and self.cl_api:
            try:
                self.cl_api.CLCloseDevice(self.handle)
                self.handle = ctypes.c_void_p(0)
                self.is_initialized = False
                self.logger.info("CL500A设备连接已断开。")
            except Exception as e:
                self.logger.error(f"CL500A关闭设备时出错: {e}")



