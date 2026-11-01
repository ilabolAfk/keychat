import os
import shutil

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QColorDialog, QMessageBox, QFrame, QComboBox, QFormLayout, QScrollArea,
    QWidget, QFileDialog,
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
        self.resize(480, 620)
        self.setMinimumSize(440, 520)
        self.setStyleSheet(current_qss())
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(10)

        title = QLabel("Настройки")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        # Прокручиваемая область, чтобы подписи и поля не наползали друг на друга
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        form = QFormLayout(body)
        form.setContentsMargins(4, 4, 4, 4)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.preview = Avatar(
            self._user["username"], self._user["avatar_color"],
            size=84, image_path=self._user.get("avatar_path") or "",
        )
        preview_row = QHBoxLayout()
        preview_row.addStretch(1)
        preview_row.addWidget(self.preview)
        preview_row.addStretch(1)

        self.avatar_btn = QPushButton("Выбрать фото…")
        self.avatar_btn.setObjectName("Ghost")
        self.avatar_btn.clicked.connect(self._pick_avatar)
        self.clear_avatar_btn = QPushButton("Сбросить")
        self.clear_avatar_btn.setObjectName("Ghost")
        self.clear_avatar_btn.clicked.connect(self._clear_avatar)
        avatar_btns = QHBoxLayout()
        avatar_btns.addStretch(1)
        avatar_btns.addWidget(self.avatar_btn)
        avatar_btns.addWidget(self.clear_avatar_btn)
        avatar_btns.addStretch(1)
        preview_col = QVBoxLayout()
        preview_col.addLayout(preview_row)
        preview_col.addLayout(avatar_btns)

        def _field_label(text):
            lab = QLabel(text)
            lab.setObjectName("UserStatus")
            lab.setWordWrap(True)
            return lab

        self.name_edit = QLineEdit(self._user["username"])
        self.name_edit.setMaxLength(24)
        self.name_edit.textChanged.connect(self._preview_name)
        self.name_edit.setMinimumHeight(36)

        self.contact_edit = QLineEdit(self._user.get("contact", ""))
        self.contact_edit.setPlaceholderText("e-mail или телефон (необязательно)")
        self.contact_edit.setMinimumHeight(36)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Тёмная", "dark")
        self.theme_combo.addItem("Светлая", "light")
        idx = self.theme_combo.findData(self._user.get("theme", "dark"))
        self.theme_combo.setCurrentIndex(max(0, idx))
        self.theme_combo.currentIndexChanged.connect(self._preview_theme)

        self.color_swatch = QPushButton()
        self.color_swatch.setFixedSize(130, 36)
        self.color_swatch.clicked.connect(self._pick_color)
        self._refresh_swatch()

        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_edit.setPlaceholderText("Новый пароль (мин. 6 символов)")
        self.pwd_edit.setMinimumHeight(36)
        self.pwd_confirm = QLineEdit()
        self.pwd_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_confirm.setPlaceholderText("Повторите пароль")
        self.pwd_confirm.setMinimumHeight(36)

        form.addRow(preview_col)
        form.addRow(_field_label("Имя пользователя (username)"), self.name_edit)
        form.addRow(_field_label("Контакт"), self.contact_edit)
        form.addRow(_field_label("Тема"), self.theme_combo)
        form.addRow(_field_label("Акцентный цвет"), self.color_swatch)
        form.addRow(_field_label("Смена пароля"), self.pwd_edit)
        form.addRow(_field_label("Повторите пароль"), self.pwd_confirm)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {PALETTE['border']};")
        form.addRow(sep)

        self.clear_all_btn = QPushButton("Очистить всю историю сообщений")
        self.clear_all_btn.setObjectName("Danger")
        self.clear_all_btn.clicked.connect(self._clear_all)
        clear_row = QHBoxLayout()
        clear_row.addWidget(self.clear_all_btn, 1)
        form.addRow(clear_row)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        btns = QHBoxLayout()
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Сохранить")
        save.setObjectName("Accent")
        save.clicked.connect(self._save)
        btns.addWidget(cancel)
        btns.addStretch(1)
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

    def _pick_avatar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать фото аватара", "", "Изображения (*.png *.jpg *.jpeg *.webp)"
        )
        if not path:
            return
        dest = self._copy_avatar_to_store(path)
        self._user["avatar_path"] = dest
        self.preview.set_image(dest)

    def _clear_avatar(self):
        self._user["avatar_path"] = ""
        self.preview.set_image("")

    def _copy_avatar_to_store(self, src):
        """Копирует фото в хранилище аватаров рядом с БД (без хардкода пути)."""
        store = os.path.join(os.path.dirname(self.db.path), "avatars")
        os.makedirs(store, exist_ok=True)
        ext = os.path.splitext(src)[1].lower() or ".png"
        dest = os.path.join(store, f"avatar_{self._user['id']}{ext}")
        shutil.copyfile(src, dest)
        return dest

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
        self.db.update_avatar_path(self._user["id"], self._user.get("avatar_path") or "")
        self.db.update_theme(self._user["id"], self._user["theme"])
        if self._user.get("contact"):
            self.db.set_setting(f"contact:{self._user['id']}", self._user["contact"])
        self.settings_saved.emit(dict(self._user))
        self.accept()

    def result_user(self):
        return dict(self._user)


def _is_hex(s):
    return isinstance(s, str) and len(s) == 7 and s[0] == "#"