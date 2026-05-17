# protocol.py
import re

class LineProtocol:
    def __init__(self, max_buffer_size=65536):
        self.buffer = bytearray()
        self.max_buffer_size = max_buffer_size
        self._ui_pending_cr = False
        self._ansi_pending = b""

        # ✔ ANSI 正确匹配
        # self.ansi_escape = re.compile(rb'\x1b\[[0-9;?]*[a-zA-Z]')
        self.ansi_escape = re.compile(rb'\x1b\[[0-9;?]*[ -/]*[@-~]')

    def _strip_ansi(self, data: bytes, stream=False) -> bytes:
        """
        去除 ANSI/VT 控制序列。
        串口会把 ESC[2K 这类序列拆包，所以实时显示流需要保留半截 ESC。
        """
        if stream and self._ansi_pending:
            data = self._ansi_pending + data
            self._ansi_pending = b""

        out = bytearray()
        i = 0
        data_len = len(data)

        while i < data_len:
            b = data[i]

            if b == 0x1B:  # ESC
                if i + 1 >= data_len:
                    if stream:
                        self._ansi_pending = data[i:]
                    break

                nxt = data[i + 1]

                if nxt == 0x5B:  # CSI: ESC [
                    j = i + 2
                    while j < data_len:
                        if 0x40 <= data[j] <= 0x7E:
                            j += 1
                            break
                        j += 1
                    else:
                        if stream:
                            self._ansi_pending = data[i:]
                        break

                    i = j
                    continue

                if nxt == 0x5D:  # OSC: ESC ] ... BEL / ESC \
                    j = i + 2
                    while j < data_len:
                        if data[j] == 0x07:
                            j += 1
                            break
                        if data[j] == 0x1B and j + 1 < data_len and data[j + 1] == 0x5C:
                            j += 2
                            break
                        j += 1
                    else:
                        if stream:
                            self._ansi_pending = data[i:]
                        break

                    i = j
                    continue

                i += 2
                continue

            out.append(b)
            i += 1

        return bytes(out)

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
    def _ui_filter(self, data: bytes, stream=False) -> str:
        data = self._handle_backspace_sequence(data)  # ⭐关键  处理设备因删除键而返回的空格键
        data = self._strip_ansi(data, stream=stream)

        chars = []
        pending_cr = self._ui_pending_cr if stream else False

        for b in data:
            if b == 0x0D:
                chars.append("\n")
                pending_cr = True
                continue

            if b == 0x0A:
                if pending_cr:
                    pending_cr = False
                    continue
                chars.append("\n")
                continue

            pending_cr = False
            if 32 <= b <= 126:
                chars.append(chr(b))

        if stream:
            self._ui_pending_cr = pending_cr

        return "".join(chars)

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
        stream_text = self._ui_filter(data, stream=True)

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
