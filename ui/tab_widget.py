from PySide6.QtWidgets import QTabWidget


class SessionTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)

        self.tabs_map = {}  # port -> widget

    def add_session(self, port, widget):
        self.tabs_map[port] = widget
        self.addTab(widget, port)

    def close_tab(self, index):
        widget = self.widget(index)
        self.removeTab(index)

        # 清理映射
        for k, v in list(self.tabs_map.items()):
            if v == widget:
                del self.tabs_map[k]