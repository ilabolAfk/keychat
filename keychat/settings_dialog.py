from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QColorDialog, QMessageBox, QFrame,
)
from .theme import QSS, PALETTE
from .widgets import Avatar, text_color_for_hex
from .login import avatar_color_for


class SettingsDialog(QDialog):
    """Настройки профиля: username, контакт, акцентный цвет, данные.*"""

    settings_saved = Signal(dict)

    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self._user = dict(user)
        self.setWindowTitle("Настройки · KeyChat")
        self.setFixedSize(460, 460)
        self.setStyleSheet(QSS)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel("Настройки")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        # Avatar preview
        self.preview = Avatar(
            self._user["username"], self._user["avatar_color"], size=88
        )
        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(self.preview)
        center.addStretch(1)
        root.addLayout(center)

        def _form(label_text, edit):
            lay = QVBoxLayout()
            lay.setSpacing(6)
            lab = QLabel(label_text)
            lab.setObjectName("UserStatus")
            lay.addWidget(lab)
            lay.addWidget(edit)
            return lay

        self.name_edit = QLineEdit(self._user["username"])
        root.addLayout(_form("Имя пользователя (username)", self.name_edit))
        self.name_edit.textChanged.connect(self._preview_name)
        self.name_edit.setMaxLength(24)

        self.contact_edit = QLineEdit(self._user.get("contact", ""))
        self.contact_edit.setPlaceholderText("e-mail или телефон (необязательно)")
        root.addLayout(_form("Контакт", self.contact_edit))

        # Color row
        color_lay = QHBoxLayout()
        color_lab = QLabel("Акцентный цвет")
        color_lab.setObjectName("UserStatus")
        color_lay.addWidget(color_lab, 1)
        self.color_swatch = QPushButton(self._user["avatar_color"])
        self.color_swatch.setFixedSize(110, 36)
        self.color_swatch.setStyleSheet(
            f"background-color: {self._user['avatar_color']};"
            f"color: {text_color_for_hex(self._user['avatar_color'])};"
            "border: none; border-radius: 8px; font-weight: 700;"
        )
        self.color_swatch.clicked.connect(self._pick_color)
        color_lay.addWidget(self.color_swatch)
        root.addLayout(color_lay)

        # Danger zone
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {PALETTE['border']};")
        root.addWidget(sep)
        self.clear_all_btn = QPushButton("Очистить всю историю сообщений")
        self.clear_all_btn.setObjectName("Danger")
        self.clear_all_btn.clicked.connect(self._clear_all)
        root.addWidget(self.clear_all_btn)

        root.addStretch(1)

        btns = QHBoxLayout()
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Сохранить")
        save.setObjectName("Accent")
        save.clicked.connect(self._save)
        btns.addWidget(cancel)
        btns.addWidget(save)
        root.addLayout(btns)

    def _preview_name(self, name):
        name = name.strip()
        if not name:
            return
        self.preview.set_name(name)
        if name != self._user["username"]:
            self.preview.set_color(avatar_color_for(name))

    def _pick_color(self):
        col = QColorDialog.getColor(
            QColor(self._user["avatar_color"]), self, "Акцентный цвет"
        )
        if col.isValid():
            self._user["avatar_color"] = col.name().upper()
            self.preview.set_color(self._user["avatar_color"])
            self.color_swatch.setStyleSheet(
                f"background-color: {self._user['avatar_color']};"
                f"color: {text_color_for_hex(self._user['avatar_color'])};"
                "border: none; border-radius: 8px; font-weight: 700;"
            )
            self.color_swatch.setText(self._user["avatar_color"])

    def _clear_all(self):
        ret = QMessageBox.question(
            self,
            "Сброс истории",
            "Удалить ВСЕ сообщения во всех чатах? Действие необратимо.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.db.clear_all_messages()
            self.settings_saved.emit(dict(self._user))

    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "KeyChat", "Username не может быть пустым.")
            return
        other = self.db.get_user_by_name(name)
        if other and other["id"] != self._user["id"]:
            QMessageBox.warning(
                self, "KeyChat", f"Username «{name}» уже занят другим профилем."
            )
            return
        self._user["username"] = name
        self._user["contact"] = self.contact_edit.text().strip()
        self.db.update_username(self._user["id"], name)
        self.db.update_avatar_color(self._user["id"], self._user["avatar_color"])
        if self._user.get("contact"):
            self.db.set_setting(f"contact:{self._user['id']}", self._user["contact"])
        self.settings_saved.emit(dict(self._user))
        self.accept()

    def result_user(self):
        return dict(self._user)