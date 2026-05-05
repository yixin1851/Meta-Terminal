import os
import time
import ctypes
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread, Slot

# ================= SDK 结构体与常量定义 =================
DEVICE_HANDLE = ctypes.c_void_p
SUCCESS = 0
CL_CALIBMEAS_FINISH = 2
CL_MEAS_FINISH = 2
CL_COLORSPACE_EVXY = 1
CL_COLORSPACE_EVTCPDUV = 3


class EvxyData(ctypes.Structure):
    _fields_ = [("Ev", ctypes.c_float), ("x", ctypes.c_float), ("y", ctypes.c_float)]


class CL_MEASDATA(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("Evxy", EvxyData), ("padding", ctypes.c_byte * 512)]


# ================= 照度计 Worker 逻辑 =================
class IlluminanceWorker(QObject):
    """
    负责与 CL-500A SDK 交互的业务逻辑
    """
    log_signal = Signal(str)  # 日志信号
    result_signal = Signal(float, float)  # 测量结果 (Lux, TCP)
    finished_init = Signal(bool)  # 初始化结果信号

    def __init__(self, dll_folder):
        super().__init__()
        self.dll_folder = dll_folder
        self.handle = DEVICE_HANDLE()
        self.cl_api = None
        self.is_initialized = False
        self._is_measuring = False

    def sync_measure(self):
        """供 CalibrationThread 同步调用的测量方法"""
        if not self.is_initialized:
            return None, None

        # 执行测量逻辑（去掉信号，直接返回结果）
        exposure = ctypes.c_int32(0)
        if self.cl_api.CLDoMeasurement(self.handle, ctypes.byref(exposure)) == SUCCESS:
            m_status = ctypes.c_int(0)
            while m_status.value != CL_MEAS_FINISH:
                time.sleep(0.05)
                self.cl_api.CLPollingMeasure(self.handle, ctypes.byref(m_status))

            color_data = CL_MEASDATA()
            self.cl_api.CLGetMeasData(self.handle, CL_COLORSPACE_EVXY, ctypes.byref(color_data))
            return color_data.Evxy.Ev, color_data.Evxy.x  # Lux, TCP
        return None, None
    
    @Slot()
    def init_sdk(self):
        """初始化设备并执行远程校准"""
        if self.is_initialized:
            self.log_signal.emit("SDK 已初始化，无需重复操作。")
            return

        try:
            # 兼容 Windows DLL 目录加载
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(self.dll_folder)

            dll_path = os.path.join(self.dll_folder, "libclapi.dll")
            if not os.path.exists(dll_path):
                self.log_signal.emit(f"错误：未找到 DLL 文件 {dll_path}")
                self.finished_init.emit(False)
                return

            self.cl_api = ctypes.CDLL(dll_path)

            # 1. 打开设备
            if self.cl_api.CLOpenDevice(ctypes.byref(self.handle)) == SUCCESS:
                # 2. 设置远程控制模式
                self.cl_api.CLSetRemoteMode(self.handle, 1)
                # 3. 开始零校准
                self.cl_api.CLDoCalibration(self.handle)

                # 4. 轮询校准状态
                c_status = ctypes.c_int(0)
                while c_status.value != CL_CALIBMEAS_FINISH:
                    time.sleep(0.1)
                    self.cl_api.CLPollingCalibration(self.handle, ctypes.byref(c_status))

                self.is_initialized = True
                self.finished_init.emit(True)
                self.log_signal.emit("照度计 SDK 初始化及校准成功！")
            else:
                self.log_signal.emit("错误：无法通过 USB 打开照度计设备。")
                self.finished_init.emit(False)

        except Exception as e:
            self.log_signal.emit(f"SDK 初始化异常: {str(e)}")
            self.finished_init.emit(False)

    @Slot()
    def start_measure(self):
        """单次测量逻辑"""
        if self._is_measuring:
            return

        if not self.is_initialized:
            self.log_signal.emit("错误：设备尚未初始化。")
            return

        self._is_measuring = True
        try:
            exposure = ctypes.c_int32(0)
            # 1. 执行测量指令
            if self.cl_api.CLDoMeasurement(self.handle, ctypes.byref(exposure)) == SUCCESS:
                m_status = ctypes.c_int(0)
                # 2. 轮询等待测量完成
                while m_status.value != CL_MEAS_FINISH:
                    self.cl_api.CLPollingMeasure(self.handle, ctypes.byref(m_status))
                    time.sleep(0.05)

                # 3. 获取 Ev, x, y 数据
                color_data = CL_MEASDATA()
                self.cl_api.CLGetMeasData(self.handle, CL_COLORSPACE_EVXY, ctypes.byref(color_data))
                lux = color_data.Evxy.Ev

                # 4. 获取 TCP (相关色温) 数据
                # SDK 中获取 TCP 通常复用 Evxy 结构体，具体取决于坐标空间定义
                self.cl_api.CLGetMeasData(self.handle, CL_COLORSPACE_EVTCPDUV, ctypes.byref(color_data))
                tcp = color_data.Evxy.x  # 假设 SDK 此时将 TCP 映射在 x 字段

                self.result_signal.emit(lux, tcp)
                self.log_signal.emit(f"测量完成: {lux:.2f} Lux, {tcp:.2f} K")
            else:
                self.log_signal.emit("指令发送失败：设备未响应测量命令")

        except Exception as e:
            self.log_signal.emit(f"测量过程中出现异常: {e}")
        finally:
            self._is_measuring = False

    def close_device(self):
        """释放设备句柄"""
        if self.cl_api and self.handle:
            self.cl_api.CLCloseDevice(self.handle)
            self.log_signal.emit("设备连接已关闭")