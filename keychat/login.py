from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QStackedWidget, QTabBar,
)
from .theme import QSS, PALETTE, build_styles
from .widgets import Avatar

import qtawesome as qta
import hashlib


def avatar_color_for(name):
    """Стабильный нейтральный цвет аватара из username."""
    h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16)
    r = 210 + (h & 0x2F)
    g = 130 + ((h >> 8) & 0x2F)
    b = 40 + ((h >> 15) & 0x2F)
    return "#{:02X}{:02X}{:02X}".format(r % 256, g % 256, b % 256)


class _AuthFrame(QFrame):
    """Блок с формой: пароль, подтверждение и кнопкой действия."""

    def __init__(self, submit_text, is_register, parent=None):
        super().__init__(parent)
        self.is_register = is_register
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.password_edit = self._make_password()
        self.password_edit.setPlaceholderText("Пароль")
        lay.addWidget(self.password_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText("Повторите пароль")
        lay.addWidget(self.confirm_edit)
        self.confirm_edit.setVisible(is_register)

        self.submit_btn = QPushButton(submit_text)
        self.submit_btn.setObjectName("Accent")
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self.submit_btn)

    @staticmethod
    def _make_password():
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.EchoMode.Password)
        return edit


class LoginWindow(QWidget):
    """Настоящий вход/регистрация по username + пароль."""

    login_success = Signal(dict)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("KeyChat · вход")
        self.setFixedSize(420, 560)
        _, login_qss = build_styles()
        self.setStyleSheet(login_qss)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 26, 36, 28)
        root.setSpacing(14)

        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.link", color=PALETTE["orange"]).pixmap(44, 44))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(icon)

        title = QLabel("KeyChat")
        title.setObjectName("BrandTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        sub = QLabel("Ваш личный мессенджер")
        sub.setObjectName("BrandSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(sub)
        root.addSpacing(6)

        # Переключатель Вход / Регистрация
        self.tabbar = QTabBar()
        self.tabbar.addTab("Вход")
        self.tabbar.addTab("Регистрация")
        self.tabbar.currentChanged.connect(self._switch_tab)
        root.addWidget(self.tabbar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self.login_frame = _AuthFrame("Войти", is_register=False)
        self.reg_frame = _AuthFrame("Создать аккаунт", is_register=True)
        self.stack.addWidget(self.login_frame)
        self.stack.addWidget(self.reg_frame)

        # Username общий для обеих вкладок, держим в верхнем поле
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Username")
        self.name_edit.returnPressed.connect(self._auth_current)
        root.insertWidget(4, self.name_edit)

        self.login_frame.submit_btn.clicked.connect(lambda: self._submit_login())
        self.reg_frame.submit_btn.clicked.connect(lambda: self._submit_register())
        self.login_frame.password_edit.returnPressed.connect(self._submit_login)
        self.reg_frame.password_edit.returnPressed.connect(self._submit_register)
        self.reg_frame.confirm_edit.returnPressed.connect(self._submit_register)

        self.avatar_preview = Avatar("", color=PALETTE["border"], size=64)
        av_row = QHBoxLayout()
        av_row.addStretch(1)
        av_row.addWidget(self.avatar_preview)
        av_row.addStretch(1)
        root.addLayout(av_row)

        self.name_edit.textChanged.connect(self._preview)

        self.hint = QLabel("")
        self.hint.setObjectName("BrandSub")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)

        if self.db.get_setting("last_username"):
            self.name_edit.setText(self.db.get_setting("last_username"))

    def _switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        self.hint.clear()

    def _preview(self, name):
        name = name.strip()
        if not name:
            self.avatar_preview.set_name("")
            self.avatar_preview.set_color(PALETTE["border"])
            return
        self.avatar_preview.set_name(name)
        self.avatar_preview.set_color(avatar_color_for(name))

    def _auth_current(self):
        if self.stack.currentIndex() == 0:
            self._submit_login()
        else:
            self._submit_register()

    def _submit_login(self):
        name = self.name_edit.text().strip()
        pwd = self.login_frame.password_edit.text()
        if not name or not pwd:
            self.hint.setText("Введите username и пароль")
            return
        user = self.db.verify_login(name, pwd)
        if user is None:
            self.hint.setText("Неверный username или пароль")
            return
        self.db.set_setting("last_username", user["username"])
        self.login_success.emit(user)

    def _submit_register(self):
        name = self.name_edit.text().strip()
        pwd = self.reg_frame.password_edit.text()
        confirm = self.reg_frame.confirm_edit.text()
        if not name or not pwd:
            self.hint.setText("Введите username и придумайте пароль")
            return
        if len(pwd) < 6:
            self.hint.setText("Пароль должен быть не короче 6 символов")
            return
        if pwd != confirm:
            self.hint.setText("Пароли не совпадают")
            return
        existing = self.db.get_user_by_name(name)
        if existing:
            self.hint.setText("Этот username уже занят — войдите или выберите другой")
            return
        from .security import hash_password
        uid = self.db.create_user(name, avatar_color_for(name), hash_password(pwd))
        user = self.db.public_user({"id": uid, "username": name, "avatar_color": avatar_color_for(name), "theme": "dark"})
        self.db.set_setting("last_username", user["username"])
        self.hint.setText(f"Аккаунт «{name}» создан")
        self.login_success.emit(user)