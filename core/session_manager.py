from PySide6.QtCore import QObject, Signal
from core.session import SerialSession


class SessionManager(QObject):
    session_added = Signal(str)
    session_removed = Signal(str)

    def __init__(self):
        super().__init__()
        self.sessions = {}   # port -> session

    def create_session(self, port, baud):
        if port in self.sessions:
            return self.sessions[port]

        session = SerialSession(port, baud)
        session.open()

        self.sessions[port] = session
        self.session_added.emit(port)

        return session

    def close_session(self, port):
        if port not in self.sessions:
            return

        self.sessions[port].close()
        del self.sessions[port]
        self.session_removed.emit(port)

    def get(self, port):
        return self.sessions.get(port)