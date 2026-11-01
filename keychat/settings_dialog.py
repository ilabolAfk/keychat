from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QColorDialog, QMessageBox, QFrame, QComboBox,
)
from .theme import PALETTE, DEFAULT_ACCENT, current_qss
from .widgets import Avatar, text_color_for_hex
from .login import avatar_color_for


class SettingsDialog(QDialog):
    """Настройки профиля: имя, контакт, тема и акцентный цвет, пароль, данные."""

    settings_saved = Signal(dict)

    def __init__(self, db, user, theme_apply=None):
        super().__init__()
        self.db = db
        self._user = dict(user)
        self.theme_apply = theme_apply  # callable(accent, theme) для смены темы на лету
        self.setWindowTitle("Настройки · KeyChat")
        self.setFixedSize(460, 540)
        self.setStyleSheet(current_qss())
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        title = QLabel("Настройки")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        self.preview = Avatar(self._user["username"], self._user["avatar_color"], size=84)
        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(self.preview)
        center.addStretch(1)
        root.addLayout(center)

        def _form(label_text, widget):
            lay = QVBoxLayout()
            lay.setSpacing(6)
            lab = QLabel(label_text)
            lab.setObjectName("UserStatus")
            lay.addWidget(lab)
            lay.addWidget(widget)
            return lay

        self.name_edit = QLineEdit(self._user["username"])
        self.name_edit.setMaxLength(24)
        self.name_edit.textChanged.connect(self._preview_name)
        root.addLayout(_form("Имя пользователя (username)", self.name_edit))

        self.contact_edit = QLineEdit(self._user.get("contact", ""))
        self.contact_edit.setPlaceholderText("e-mail или телефон (необязательно)")
        root.addLayout(_form("Контакт", self.contact_edit))

        # Тема и акцент
        theme_row = QHBoxLayout()
        theme_lab = QLabel("Тема")
        theme_lab.setObjectName("UserStatus")
        theme_row.addWidget(theme_lab, 1)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Тёмная", "dark")
        self.theme_combo.addItem("Светлая", "light")
        idx = self.theme_combo.findData(self._user.get("theme", "dark"))
        self.theme_combo.setCurrentIndex(max(0, idx))
        self.theme_combo.currentIndexChanged.connect(self._preview_theme)
        theme_row.addWidget(self.theme_combo)
        root.addLayout(theme_row)

        accent_row = QHBoxLayout()
        accent_lab = QLabel("Акцентный цвет")
        accent_lab.setObjectName("UserStatus")
        accent_row.addWidget(accent_lab, 1)
        self.color_swatch = QPushButton()
        self.color_swatch.setFixedSize(120, 36)
        self.color_swatch.clicked.connect(self._pick_color)
        accent_row.addWidget(self.color_swatch)
        root.addLayout(accent_row)
        self._refresh_swatch()

        # Пароль
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_edit.setPlaceholderText("Новый пароль (мин. 6 символов)")
        self.pwd_confirm = QLineEdit()
        self.pwd_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_confirm.setPlaceholderText("Повторите пароль")
        root.addLayout(_form("Смена пароля", self.pwd_edit))
        root.addWidget(self.pwd_confirm)

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

    def _preview_theme(self):
        theme = self.theme_combo.currentData()
        accent = self._user["avatar_color"]
        if not _is_hex(accent):
            accent = DEFAULT_ACCENT
        if self.theme_apply:
            self.theme_apply(accent, theme)
        self.setStyleSheet(current_qss())

    def _refresh_swatch(self):
        accent = self._user["avatar_color"]
        if not _is_hex(accent):
            accent = DEFAULT_ACCENT
        self.color_swatch.setText(accent)
        self.color_swatch.setStyleSheet(
            f"background-color: {accent}; color: {text_color_for_hex(accent)};"
            "border: none; border-radius: 8px; font-weight: 700;"
        )

    def _pick_color(self):
        col = QColorDialog.getColor(
            QColor(self._user["avatar_color"]), self, "Акцентный цвет"
        )
        if col.isValid():
            self._user["avatar_color"] = col.name().upper()
            self.preview.set_color(self._user["avatar_color"])
            self._refresh_swatch()
            self._preview_theme()

    def _clear_all(self):
        ret = QMessageBox.question(
            self, "Сброс истории",
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
            QMessageBox.warning(self, "KeyChat", f"Username «{name}» уже занят.")
            return
        pwd, confirm = self.pwd_edit.text(), self.pwd_confirm.text()
        if pwd or confirm:
            if len(pwd) < 6:
                QMessageBox.warning(self, "KeyChat", "Пароль должен быть не короче 6 символов.")
                return
            if pwd != confirm:
                QMessageBox.warning(self, "KeyChat", "Пароли не совпадают.")
                return
            from .security import hash_password
            self.db.set_password(self._user["id"], hash_password(pwd))

        self._user["username"] = name
        self._user["contact"] = self.contact_edit.text().strip()
        self._user["theme"] = self.theme_combo.currentData()
        self.db.update_username(self._user["id"], name)
        self.db.update_avatar_color(self._user["id"], self._user["avatar_color"])
        self.db.update_theme(self._user["id"], self._user["theme"])
        if self._user.get("contact"):
            self.db.set_setting(f"contact:{self._user['id']}", self._user["contact"])
        self.settings_saved.emit(dict(self._user))
        self.accept()

    def result_user(self):
        return dict(self._user)


def _is_hex(s):
    return isinstance(s, str) and len(s) == 7 and s[0] == "#"