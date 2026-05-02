import time
import re
import os
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QEventLoop, QTimer, QThread, Slot


class CalibrationResult:
    """对应 C++ 的 CalibrationResult 结构体"""

    def __init__(self):
        self.k = 1.0
        self.b = 0.0
        self.r2 = 0.0
        self.data_points = []  # List of (set_lux, measured_lux)
        self.calib_points = []  # List of (target_lux, real_set_lux)


class CalibrationEngine(QObject):
    # 定义信号
    calibrationStarted = Signal()
    calibrationFinished = Signal(object)
    calibrationFailed = Signal(str)
    progressUpdated = Signal(int, int, float, float)
    logMessage = Signal(str)
    eepromSaved = Signal()

    def __init__(self, light, meter, parent=None):
        super().__init__(parent)
        self.m_light = light
        self.m_meter = meter
        self.m_result = CalibrationResult()

    def start_calibration(self, set_points, measure_count=5):
        """核心校准逻辑"""
        if not self.m_light or not self.m_meter:
            self.calibrationFailed.emit("光源或照度计未初始化")
            return
        if not set_points:
            self.calibrationFailed.emit("标定点列表为空")
            return

        self.calibrationStarted.emit()
        self.logMessage.emit(f"[CalibEngine] 开始校准，共 {len(set_points)} 个点")

        data_points = []
        total = len(set_points)

        for i, set_lux in enumerate(set_points):
            self.logMessage.emit(f"[CalibEngine] 标定点 {i + 1}/{total}: 设定 {set_lux:.2f} lux")

            # 1. 设定光源
            self.m_light.set_lux(set_lux)

            # 2. 等待光源稳定 (相当于 QThread.msleep)
            # 注意：如果在主线程运行，建议改用 QTimer 避免 UI 卡死
            # 这里演示使用子线程中的 sleep 逻辑
            QThread.msleep(500)

            # 3. 照度计测量 (使用局部事件循环模拟同步等待结果)
            measured_lux = 0.0
            self.got_result = False

            loop = QEventLoop()

            # 定义内部回调
            def on_measure_done(avg_result):
                nonlocal measured_lux
                measured_lux = avg_result  # 假设返回的是数值
                self.got_result = True
                loop.quit()

            # 连接信号
            self.m_meter.allMeasurementsDone.connect(on_measure_done)
            # 超时处理
            QTimer.singleShot(10000, loop.quit)

            # 触发测量
            self.m_meter.do_measurement(measure_count)
            loop.exec()  # 阻塞当前线程直到 loop.quit()

            # 断开连接防止干扰下一次
            self.m_meter.allMeasurementsDone.disconnect(on_measure_done)

            if not self.got_result:
                self.calibrationFailed.emit(f"标定点 {set_lux} lux 测量超时")
                return

            # 记录数据
            data_points.append((set_lux, measured_lux))
            self.progressUpdated.emit(i + 1, total, set_lux, measured_lux)
            self.logMessage.emit(f"[CalibEngine] 实测: {measured_lux:.3f} lux")

        # 4. 线性回归拟合
        k, b, r2 = self.fit_linear(data_points)
        self.m_result.k = k
        self.m_result.b = b
        self.m_result.r2 = r2
        self.m_result.data_points = data_points

        self.logMessage.emit(f"[CalibEngine] 拟合完成: y = {k:.4f}x + {b:.4f} (R²={r2:.4f})")
        self.calibrationFinished.emit(self.m_result)

    def target_to_cmd(self, target_lux):
        """反算：目标光强 -> 指令值"""
        if abs(self.m_result.k) < 1e-6:
            return target_lux
        return (target_lux - self.m_result.b) / self.m_result.k

    def fit_linear(self, pts):
        """最小二乘法线性拟合"""
        n = len(pts)
        if n < 2:
            return 1.0, 0.0, 0.0

        sum_x = sum(p[0] for p in pts)
        sum_y = sum(p[1] for p in pts)
        sum_xy = sum(p[0] * p[1] for p in pts)
        sum_x2 = sum(p[0] ** 2 for p in pts)

        denom = n * sum_x2 - sum_x ** 2
        if abs(denom) < 1e-9:
            return 1.0, 0.0, 0.0

        k = (n * sum_xy - sum_x * sum_y) / denom
        b = (sum_y - k * sum_x) / n

        # 计算 R²
        y_mean = sum_y / n
        ss_tot = sum((p[1] - y_mean) ** 2 for p in pts)
        ss_res = sum((p[1] - (k * p[0] + b)) ** 2 for p in pts)
        r2 = 1.0 if abs(ss_tot) < 1e-9 else 1.0 - (ss_res / ss_tot)

        return k, b, r2

    def save_csv_file(self, save_dir, file_name, header, content):
        """保存校准结果到 CSV"""
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        full_path = os.path.join(save_dir, f"{file_name}_{timestamp}.csv")

        try:
            with open(full_path, 'a', encoding='utf-8') as f:
                f.write(header + "\n")
                f.write(content + "\n")
            self.logMessage.emit(f"[CalibEngine] CSV已保存: {full_path}")
        except Exception as e:
            self.logMessage.emit(f"[CalibEngine] CSV保存失败: {e}")