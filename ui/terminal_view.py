from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import Signal, Qt


class TerminalView(QPlainTextEdit):
    send_data = Signal(bytes)

    def __init__(self):
        super().__init__()
        self.setReadOnly(False)
        self.setPlaceholderText("Terminal ready...")

    def keyPressEvent(self, event):
        text = event.text()
        if text:
            self.send_data.emit(text.encode("utf-8"))
        super().keyPressEvent(event)

    def append_data(self, data: bytes):
        try:
            text = data.decode()
        except:
            text = str(data)

        self.insertPlainText(text)
        self.moveCursor(self.textCursor().End)