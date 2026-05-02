def on_data_received(self, data, is_send=False):
    try:
        if self.cb_hex.isChecked():
            # Hex 模式保持原样，加空格区分
            text = data.hex(' ').upper() + " "
        else:
            # --- 核心修复逻辑 ---
            # 1. 解码并忽略非法字符
            # 2. 将 \r\n 替换为 \n (防止重复换行)
            # 3. 将残余的 \r 彻底删掉 (这是导致多出一行的元凶)
            text = data.decode('utf-8', errors='ignore').replace('\r\n', '\n').replace('\r', '')
    except Exception as e:
        # 遇到不确定的事实，必须回答“我不知道”，此处仅打印错误以供调试
        print(f"Decode error: {e}")
        text = str(data)

    # 确保操作在末尾进行
    self.terminal.moveCursor(QTextCursor.End)

    if is_send:
        # 本地回显颜色设置
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#569CD6"))  # 蓝色
        # 针对本地发送，也需要确保格式紧凑
        fmt.setLineHeight(100.0, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)

        self.terminal.setCurrentCharFormat(fmt)
        self.terminal.insertPlainText(text)
        # 恢复默认颜色和格式
        self.terminal.setCurrentCharFormat(QTextCharFormat())
    else:
        # 接收数据：直接插入清洗后的文本
        self.terminal.insertPlainText(text)

    # 保持滚动条在最下方
    self.terminal.moveCursor(QTextCursor.End)
    # 强制界面立即滚动（处理长数据流）
    self.terminal.ensureCursorVisible()