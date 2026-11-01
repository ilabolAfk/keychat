import sys
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from keychat.database import Database, DB_PATH
from keychat.security import Crypto
from keychat.theme import QSS, PALETTE
from keychat.login import LoginWindow
from keychat.main_window import MainWindow


class KeyChatApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("KeyChat")
        self.app.setStyle("Fusion")
        self.crypto = Crypto(DB_PATH)
        self.db = Database(DB_PATH, crypto=self.crypto)
        self.login = LoginWindow(self.db)
        self.login.login_success.connect(self._start_main)
        self.login.show()

    def _start_main(self, user):
        self.user = user
        self.main = MainWindow(self.db, user)
        self.main.logout_requested.connect(self._back_to_login)
        self.main.show()
        self.login.hide()

    def _back_to_login(self):
        self.main.close()
        self.login.show()

    def run(self):
        return self.app.exec()


if __name__ == "__main__":
    app = KeyChatApp()
    sys.exit(app.run())