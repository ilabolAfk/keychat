from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame,
)
from .theme import QSS, PALETTE, FONT_FAMILY

import qtawesome as qta
import hashlib


def avatar_color_for(name):
    """Стабильный оранжевый-нейтральный цвет из username."""
    h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16)
    r = 210 + (h & 0x2F)
    g = 130 + ((h >> 8) & 0x2F)
    b = 40 + ((h >> 15) & 0x2F)
    return "#{:02X}{:02X}{:02X}".format(r % 256, g % 256, b % 256)


class LoginWindow(QWidget):
    """Вход в KeyChat: новый пользователь или возврат под существующим username."""

    login_success = Signal(dict)  # emits user dict

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("KeyChat · вход")
        self.setFixedSize(420, 520)
        self.setStyleSheet(QSS)
        self._seed_selected = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 30)
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
        root.addSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите username")
        self.name_edit.setText(self.db.get_setting("last_username", ""))
        self.name_edit.returnPressed.connect(self._on_enter)
        root.addWidget(self.name_edit)

        self.avatar_preview = QFrame()
        self.avatar_preview.setFixedSize(64, 64)
        avatar_l = QVBoxLayout(self.avatar_preview)
        avatar_l.setContentsMargins(0, 0, 0, 0)
        self.avatar_label = QLabel(self._seed_selected or "?")
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet(
            "font-size: 26px; font-weight: 700; color: #1A0F00; background: transparent;"
        )
        avatar_l.addWidget(self.avatar_label)
        self.avatar_preview.setStyleSheet(
            f"border-radius: 32px; background-color: {PALETTE['orange']};"
        )
        av_row = QHBoxLayout()
        av_row.addStretch(1)
        av_row.addWidget(self.avatar_preview)
        av_row.addStretch(1)
        root.addLayout(av_row)
        self.name_edit.textChanged.connect(self._update_avatar_preview)
        self._update_avatar_preview(self.name_edit.text())

        self.enter_btn = QPushButton("Войти в KeyChat")
        self.enter_btn.setObjectName("Accent")
        self.enter_btn.clicked.connect(self._on_enter)
        self.enter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        root.addWidget(self.enter_btn)

        self.hint = QLabel("")
        self.hint.setObjectName("BrandSub")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)

    def _update_avatar_preview(self, name):
        name = name.strip()
        if not name:
            self.avatar_label.setText("?")
            self.avatar_preview.setStyleSheet(
                f"border-radius: 32px; background-color: {PALETTE['border']};"
            )
            return
        self.avatar_label.setText(name[0].upper())
        color = avatar_color_for(name)
        # контрастный текст
        lum = (int(color[1:3], 16) * 299 + int(color[3:5], 16) * 587 + int(color[5:7], 16) * 114) / 1000
        txt = "#1A0F00" if lum > 150 else "#FFFFFF"
        self.avatar_label.setStyleSheet(
            f"font-size: 26px; font-weight: 700; color: {txt}; background: transparent;"
        )
        self.avatar_preview.setStyleSheet(
            f"border-radius: 32px; border: 2px solid {PALETTE['orange_light']}; background-color: {color};"
        )

    def _on_enter(self):
        name = self.name_edit.text().strip()
        if not name:
            self.hint.setText("Введите username, он же — адрес для входа")
            return
        user = self.db.get_user_by_name(name)
        if user is None:
            color = avatar_color_for(name)
            uid = self.db.create_user(name, color)
            user = {"id": uid, "username": name, "avatar_color": color}
            self.hint.setText(f"Создан новый профиль «{name}»")
        else:
            self.hint.setText(f"С возвращением, {user['username']}")
        self.db.set_setting("last_username", user["username"])
        self.login_success.emit(user)