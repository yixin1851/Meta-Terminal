# protocol.py
import re

class LineProtocol:
    def __init__(self, max_buffer_size=65536):
        self.buffer = bytearray()
        self.max_buffer_size = max_buffer_size

        # ✔ ANSI 正确匹配
        # self.ansi_escape = re.compile(rb'\x1b\[[0-9;?]*[a-zA-Z]')
        self.ansi_escape = re.compile(rb'\x1b\[[0-9;?]*[ -/]*[@-~]')

        # ✔ 只保留换行（tab也不显示，但可以选择是否保留）
        self.keep = {0x0D, 0x0A}

    def _handle_backspace_sequence(self, data: bytes) -> bytes:
        i = 0
        out = bytearray()

        while i < len(data):
            # 识别 \b \b
            if (
                    i + 2 < len(data)
                    and data[i] == 0x08
                    and data[i + 1] == 0x20
                    and data[i + 2] == 0x08
            ):
                if out:
                    out.pop()  # 删除前一个字符
                i += 3
                continue

            # 单独的 \b
            if data[i] == 0x08:
                if out:
                    out.pop()
                i += 1
                continue

            out.append(data[i])
            i += 1

        return bytes(out)

    # =========================
    # 1. UI显示过滤（最严格）
    # =========================
    def _ui_filter(self, data: bytes) -> str:
        data = self._handle_backspace_sequence(data)  # ⭐关键  处理设备因删除键而返回的空格键
        data = self.ansi_escape.sub(b'', data)

        out = bytearray()

        for b in data:
            if b in (0x0D, 0x0A) or 32 <= b <= 126:
                out.append(b)

        return out.decode("utf-8", errors="ignore")

    # =========================
    # 2. 仅用于“业务数据解析”（不丢任何原始信息）
    # =========================
    def _raw_buffer_append(self, data: bytes):
        self.buffer.extend(data)

        # 防止溢出
        if len(self.buffer) > self.max_buffer_size:
            self.buffer = self.buffer[-self.max_buffer_size:]

    # =========================
    # 主入口
    # =========================
    def feed(self, data: bytes, mode="text"):
        self._raw_buffer_append(data)

        outputs = []

        # =========================
        # HEX模式（原样）
        # =========================
        if mode == "hex":
            return [{
                "hex": data.hex(" ").upper(),
                "mode": "hex"
            }]

        # =========================
        # 1. 实时流显示（逐字符）
        # =========================
        stream_text = self._ui_filter(data)

        outputs.append({
            "render": stream_text,
            "mode": "text_stream",
            "eol": False
        })

        # =========================
        # 2. 按行解析（业务层）
        # =========================
        while b"\r\n" in self.buffer:
            pos = self.buffer.find(b"\r\n")

            chunk = bytes(self.buffer[:pos])
            del self.buffer[:pos + 2]

            # ✔ 这里也可以选择：是否保留 ANSI
            clean = self._ui_filter(chunk)

            outputs.append({
                "data": clean,
                "mode": "data_line",
                "eol": True
                # "raw": chunk   # ⭐关键：原始数据也保留
            })

        return outputs