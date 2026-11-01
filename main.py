import sys
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from keychat.database import Database, DB_PATH
from keychat.security import Crypto
from keychat.theme import QSS, PALETTE, app_icon_path
from keychat.login import LoginWindow
from keychat.main_window import MainWindow


class KeyChatApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("KeyChat")
        self.app.setStyle("Fusion")
        self._set_app_icon("dark")
        self.crypto = Crypto(DB_PATH)
        self.db = Database(DB_PATH, crypto=self.crypto)
        self.login = LoginWindow(self.db)
        self.login.login_success.connect(self._start_main)
        self.login.show()

    def _set_app_icon(self, theme="dark"):
        """Ставит иконку приложения под текущую тему (окно + панель задач)."""
        path = app_icon_path(theme)
        if path:
            self.app.setWindowIcon(QIcon(path))

    def _start_main(self, user):
        self.user = user
        self.main = MainWindow(self.db, user)
        self.main.logout_requested.connect(self._back_to_login)
        self.main.theme_changed.connect(self._on_theme_changed)
        self.main.show()
        self.login.hide()

    def _on_theme_changed(self, theme):
        self._set_app_icon(theme)

    def _back_to_login(self):
        self.main.close()
        self.login.show()

    def run(self):
        return self.app.exec()


if __name__ == "__main__":
    app = KeyChatApp()
    sys.exit(app.run())