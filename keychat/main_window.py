import os
import shutil

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap, QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QTextEdit, QFrame, QScrollBar, QDialog, QLineEdit,
    QMessageBox, QSizePolicy, QSplitter, QScrollArea, QApplication,
    QFileDialog, QToolButton,
)
from .theme import QSS, PALETTE
from .widgets import Avatar
from .settings_dialog import SettingsDialog
from .security import files_dir_for, random_stored_name
from .stickers import StickerPicker, find_stickers

import qtawesome as qta


class ChatListWidget(QListWidget):
    chat_selected = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setObjectName("ChatList")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        vbar = self.verticalScrollBar()
        vbar.setSingleStep(16)
        self.currentItemChanged.connect(self._on_current)

    def _on_current(self, current, _prev):
        if current is not None:
            self.chat_selected.emit(current.data(Qt.ItemDataRole.UserRole))

    def set_chats(self, chats, active_id):
        self.blockSignals(True)
        self.clear()
        for chat in chats:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, chat)
            item.setSizeHint(QSize(0, 66))
            w = ChatRow(chat)
            self.addItem(item)
            self.setItemWidget(item, w)
            if chat["id"] == active_id:
                self.setCurrentItem(item)
        self.blockSignals(False)


class ChatRow(QWidget):
    def __init__(self, chat):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(12)
        self.avatar = Avatar(chat["username"], chat["avatar_color"], size=44)
        lay.addWidget(self.avatar)

        mid = QVBoxLayout()
        mid.setSpacing(3)
        name = QLabel(chat["username"])
        name.setStyleSheet(f"font-size: 14px; font-weight: 600; background: transparent;")
        self.preview = QLabel(chat["last_message"] or "Нет сообщений")
        self.preview.setStyleSheet(
            f"font-size: 12px; color: {PALETTE['text_dim']}; background: transparent;"
        )
        self.preview.setMaximumWidth(180)
        self.preview.setWordWrap(True)
        mid.addWidget(name)
        mid.addWidget(self.preview)
        lay.addLayout(mid, 1)

        self.time = QLabel(chat.get("last_seen") or "")
        self.time.setStyleSheet(
            f"font-size: 11px; color: {PALETTE['text_dim']}; background: transparent;"
        )
        lay.addWidget(self.time, alignment=Qt.AlignmentFlag.AlignTop)


def _parse_file_meta(meta):
    """Из meta формата 'stored_name|name=имя' возвращает (stored_name, filename)."""
    stored = meta
    name = "файл"
    if "|name=" in meta:
        stored, _, name = meta.partition("|name=")
    if not stored:
        stored = meta
    return stored, name


class MessageBubble(QFrame):
    """Выровненный «пузырь» сообщения."""

    file_download_requested = Signal(str, str)  # (stored_name, filename)

    def __init__(self, msg, mine, avatar_color):
        super().__init__()
        self.stored_name = msg.get("meta") or ""
        self.file_name = "файл"
        self._downloadable = False
        bubble_bg = PALETTE["bubble_me"] if mine else PALETTE["bubble_peer"]
        align = Qt.AlignmentFlag.AlignRight if mine else Qt.AlignmentFlag.AlignLeft

        outer = QHBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)
        outer.setSpacing(8)
        if not mine:
            av = Avatar("", color=avatar_color, size=30)
            outer.addWidget(av, alignment=Qt.AlignmentFlag.AlignBottom)

        inner = QVBoxLayout()
        inner.setSpacing(2)
        head = QHBoxLayout()
        head.setSpacing(8)
        sender = QLabel(msg.get("sender_name", "Вы" if mine else ""))
        sender.setStyleSheet(
            f"font-size: 11px; font-weight: 600;"
            f"color: {'#7A4A00' if mine else PALETTE['orange_light']};"
            "background: transparent;"
        )
        ts = QLabel(msg.get("sent_at", ""))
        ts.setStyleSheet(
            f"font-size: 10px; color: {'#5C3A00' if mine else PALETTE['text_dim']};"
            "background: transparent;"
        )
        head.addWidget(sender)
        head.addStretch(1)
        head.addWidget(ts)
        inner.addLayout(head)

        msg_type = msg.get("msg_type", "text")
        if msg_type == "sticker":
            from .stickers import STICKERS_DIR
            import os as _os
            sticker_path = msg.get("meta") or ""
            if not _os.path.isabs(sticker_path):
                sticker_path = _os.path.join(STICKERS_DIR, sticker_path)
            pm = QPixmap(sticker_path)
            if not pm.isNull():
                scaled = pm.scaled(
                    140, 140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                img = QLabel()
                img.setPixmap(scaled)
                inner.addWidget(img)
            else:
                empty = QLabel()
                empty.setPixmap(qta.icon("fa5s.smile", color="#1A0F00" if mine else PALETTE["orange"]).pixmap(28, 28))
                empty.setStyleSheet("background: transparent;")
                inner.addWidget(empty, alignment=Qt.AlignmentFlag.AlignHCenter)
        elif msg_type == "file":
            meta = msg.get("meta") or ""
            stored_name, name = _parse_file_meta(meta)
            self.stored_name = stored_name
            self.file_name = name
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            bubble_bg = bubble_bg  # фон как у обычного пузыря
            row = QHBoxLayout()
            row.setSpacing(8)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon("fa5s.file", color="#1A0F00" if mine else PALETTE["orange"]).pixmap(20, 20))
            row.addWidget(icon_lbl)
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(
                f"font-size: 14px; font-weight: 600; background: transparent;"
                f"color: {'#1A0F00' if mine else PALETTE['text']};"
            )
            row.addWidget(name_lbl, 1)
            dl = QLabel()
            dl.setPixmap(qta.icon("fa5s.download", color="#1A0F00" if mine else PALETTE["orange_dark"]).pixmap(18, 18))
            row.addWidget(dl)
            inner.addLayout(row)
            self._downloadable = True
        else:
            text = QLabel(msg.get("text", ""))
            text.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            text.setWordWrap(True)
            text.setStyleSheet(
                f"font-size: 14px; background: transparent;"
                f"color: {'#1A0F00' if mine else PALETTE['text']};"
            )
            inner.addWidget(text)
        outer.addLayout(inner, 1)

        if mine:
            outer.addSpacing(34)
        self.setStyleSheet(
            f"background-color: {bubble_bg}; border-radius: 14px;"
            + ("; border-top-right-radius: 4px;" if mine else "; border-top-left-radius: 4px;")
        )
        self.setMaximumWidth(560)

    def mouseReleaseEvent(self, event):
        if self._downloadable and event.button() == Qt.MouseButton.LeftButton:
            self.file_download_requested.emit(self.stored_name, self.file_name)
            return
        super().mouseReleaseEvent(event)


class MainWindow(QWidget):
    logout_requested = Signal()

    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.active_chat = None
        self.history = []
        self.setWindowTitle("KeyChat")
        self.setMinimumSize(820, 560)
        self.resize(1024, 680)
        self.setStyleSheet(QSS)
        self._build()
        self._load_chats()

    # ---------- build ----------
    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(290)
        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(14, 20, 14, 14)
        sb.setSpacing(12)
        root.addWidget(self.sidebar)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        brand_icon = QLabel()
        brand_icon.setPixmap(qta.icon("fa5s.link", color=PALETTE["orange"]).pixmap(22, 22))
        brand_row.addWidget(brand_icon)
        brand = QLabel("KeyChat")
        brand.setObjectName("BrandTitle")
        brand_row.addWidget(brand)
        brand_row.addStretch(1)
        sb.addLayout(brand_row)

        # Профиль
        self.profile = QFrame()
        self.profile.setObjectName("Sidebar")
        pl = QHBoxLayout(self.profile)
        pl.setContentsMargins(4, 4, 4, 4)
        pl.setSpacing(12)
        self.profile_avatar = Avatar(self.user["username"], self.user["avatar_color"], size=48)
        pl.addWidget(self.profile_avatar)
        pinfo = QVBoxLayout()
        pinfo.setSpacing(2)
        self.name_label = QLabel(self.user["username"])
        self.name_label.setObjectName("UserName")
        self.name_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_label = QLabel("В сети")
        self.status_label.setObjectName("UserStatus")
        pinfo.addWidget(self.name_label)
        pinfo.addWidget(self.status_label)
        pl.addLayout(pinfo, 1)
        settings_btn = QPushButton()
        settings_btn.setObjectName("IconBtn")
        settings_btn.setFixedSize(38, 38)
        settings_btn.setIcon(qta.icon("fa5s.cog", color=PALETTE["text_dim"]))
        settings_btn.setIconSize(QSize(20, 20))
        settings_btn.setToolTip("Настройки")
        settings_btn.clicked.connect(self._open_settings)
        pl.addWidget(settings_btn)
        sb.addWidget(self.profile)

        self.section = QLabel("  ЧАТЫ")
        self.section.setObjectName("SectionTitle")
        sb.addWidget(self.section)

        self.chat_list = ChatListWidget()
        self.chat_list.chat_selected.connect(self._select_chat)
        sb.addWidget(self.chat_list, 1)

        self.friend_btn = QPushButton("  Новый чат")
        self.friend_btn.setObjectName("Accent")
        self.friend_btn.setIcon(qta.icon("fa5s.plus", color=PALETTE["text_on_orange"]))
        self.friend_btn.setIconSize(QSize(16, 16))
        self.friend_btn.clicked.connect(self._add_friend)
        sb.addWidget(self.friend_btn)

        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.setObjectName("Ghost")
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        sb.addWidget(self.logout_btn)

        # ----- main panel -----
        self.panel = QWidget()
        self.panel.setObjectName("Root")
        self.stack = QVBoxLayout(self.panel)
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.stack.setSpacing(0)
        root.addWidget(self.panel, 1)

        self._build_chat_area()

    def _build_chat_area(self):
        # Header
        self.header = QFrame()
        self.header.setObjectName("Sidebar")
        self.header.setFixedHeight(70)
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(20, 10, 20, 10)
        hl.setSpacing(12)
        self.header_avatar = Avatar("", PALETTE["orange"], size=44)
        hl.addWidget(self.header_avatar)
        self.header_peer = QLabel("Выберите чат")
        self.header_peer.setObjectName("HeaderPeer")
        hl.addWidget(self.header_peer, 1)
        self.clear_btn = QPushButton("Очистить историю")
        self.clear_btn.setObjectName("Ghost")
        self.clear_btn.clicked.connect(self._clear_history)
        hl.addWidget(self.clear_btn)
        self.stack.addWidget(self.header)

        # History area (scrollable)
        self.history_area = QScrollArea()
        self.history_area.setObjectName("Root")
        self.history_area.setWidgetResizable(True)
        self.history_area.setFrameShape(QFrame.Shape.NoFrame)
        self.history_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.history_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.history_area.verticalScrollBar().setSingleStep(20)
        history_content = QWidget()
        history_content.setObjectName("Root")
        self.history_container = QVBoxLayout(history_content)
        self.history_container.setContentsMargins(18, 14, 18, 14)
        self.history_container.setSpacing(4)
        self.history_container.addStretch(1)
        self.history_area.setWidget(history_content)
        self.stack.addWidget(self.history_area, 1)
        self.history_area.setVisible(False)

        self.empty_state = QWidget()
        el = QVBoxLayout(self.empty_state)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon = QLabel()
        empty_icon.setPixmap(qta.icon("fa5s.comments", color=PALETTE["orange"]).pixmap(64, 64))
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.addWidget(empty_icon)
        empty_title = QLabel("Начните общение")
        empty_title.setObjectName("BrandTitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.addWidget(empty_title)
        empty_sub = QLabel("Выберите чат слева или создайте новый")
        empty_sub.setObjectName("BrandSub")
        empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.addWidget(empty_sub)
        self.stack.addWidget(self.empty_state, 1)

        # Input
        self.input_bar = QFrame()
        self.input_bar.setObjectName("Sidebar")
        il = QVBoxLayout(self.input_bar)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(0)

        self.sticker_panel = QFrame()
        self.sticker_panel.setObjectName("Sidebar")
        spinner_l = QVBoxLayout(self.sticker_panel)
        spinner_l.setContentsMargins(12, 10, 12, 6)
        self.picker = StickerPicker(os.path.join(os.path.dirname(self.db.path), "_sticker_cache"))
        self.picker.setFixedHeight(150)
        self.picker.sticker_selected.connect(self._send_sticker)
        spinner_l.addWidget(self.picker)
        il.addWidget(self.sticker_panel)
        self.sticker_panel.setVisible(False)

        bar_row = QHBoxLayout()
        bar_row.setContentsMargins(18, 10, 18, 10)
        bar_row.setSpacing(8)

        self.file_btn = QToolButton()
        self.file_btn.setIcon(qta.icon("fa5s.paperclip"))
        self.file_btn.setIconSize(QSize(22, 22))
        self.file_btn.setToolTip("Прикрепить файл")
        self.file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.file_btn.setStyleSheet(
            "QToolButton { background: transparent; border: none; border-radius: 8px; padding: 8px; }"
            "QToolButton:hover { background: rgba(255,122,26,0.2); }"
        )
        self.file_btn.clicked.connect(self._attach_file)
        bar_row.addWidget(self.file_btn)

        self.sticker_btn = QToolButton()
        self.sticker_btn.setIcon(qta.icon("fa5s.smile", color=PALETTE["orange"]))
        self.sticker_btn.setIconSize(QSize(22, 22))
        self.sticker_btn.setToolTip("Стикеры")
        self.sticker_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sticker_btn.setStyleSheet(
            "QToolButton { background: transparent; border: none; border-radius: 8px; padding: 8px; }"
            "QToolButton:hover { background: rgba(255,122,26,0.2); }"
        )
        self.sticker_btn.clicked.connect(self._toggle_stickers)
        bar_row.addWidget(self.sticker_btn)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Сообщение…")
        self.input_edit.setFixedHeight(56)
        self.input_edit.setObjectName("MessageInput")
        bar_row.addWidget(self.input_edit, 1)

        self.send_btn = QPushButton()
        self.send_btn.setObjectName("Accent")
        self.send_btn.setFixedSize(48, 48)
        self.send_btn.setIcon(qta.icon("fa5s.paper-plane", color=PALETTE["text_on_orange"]))
        self.send_btn.setIconSize(QSize(20, 20))
        self.send_btn.setToolTip("Отправить")
        self.send_btn.clicked.connect(self._send)
        bar_row.addWidget(self.send_btn)

        il.addLayout(bar_row)
        self.stack.addWidget(self.input_bar)
        self.input_bar.setVisible(False)

    # ---------- data flow ----------
    def _load_chats(self):
        chats = self.db.list_chats()
        self.chat_list.set_chats(chats, self.active_chat)

    def _select_chat(self, chat):
        self.active_chat = chat
        self.header_peer.setText(chat["username"])
        self.header_avatar.set_name(chat["username"])
        self.header_avatar.set_color(chat["avatar_color"])
        self.header_avatar.set_size(44)
        self.empty_state.setVisible(False)
        self.history_area.setVisible(True)
        self.input_bar.setVisible(True)
        self.clear_btn.setEnabled(True)
        self._reload_history()

    def _reload_history(self):
        if self.active_chat is None:
            return
        chat_id = self.active_chat["id"]
        rows = self.db.get_history(chat_id)
        my_color = self.user["avatar_color"]
        while self.history_container.count() > 1:
            it = self.history_container.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        for row in rows:
            mine = row["sender_id"] == self.user["id"]
            peer_color = self.active_chat["avatar_color"]
            bubble = MessageBubble(row, mine, my_color if mine else peer_color)
            bubble.file_download_requested.connect(self._download_file)
            self.history_container.insertWidget(
                self.history_container.count() - 1, bubble
            )
        self._scroll_to_bottom()

    def _send(self):
        text = self.input_edit.toPlainText().strip()
        if not text or self.active_chat is None:
            return
        self.input_edit.clear()
        msg = self.db.send_message(
            self.active_chat["id"], self.user["id"], text
        )
        msg["sender_name"] = self.user["username"]
        peer_color = self.active_chat["avatar_color"]
        bubble = MessageBubble(msg, True, peer_color)
        self.history_container.insertWidget(self.history_container.count() - 1, bubble)
        self._scroll_to_bottom()
        self._load_chats()

    def _toggle_stickers(self):
        if self.active_chat is None:
            return
        self.sticker_panel.setVisible(not self.sticker_panel.isVisible())

    def _send_sticker(self, path):
        self.sticker_panel.setVisible(False)
        if self.active_chat is None:
            return
        msg = self.db.send_message(
            self.active_chat["id"], self.user["id"], "",
            msg_type="sticker", meta=path,
        )
        msg["sender_name"] = self.user["username"]
        bubble = MessageBubble(msg, True, self.active_chat["avatar_color"])
        self.history_container.insertWidget(self.history_container.count() - 1, bubble)
        self._scroll_to_bottom()
        self._load_chats()

    def _attach_file(self):
        if self.active_chat is None:
            return
        src, _ = QFileDialog.getOpenFileName(self, "Выберите файл")
        if not src:
            return
        name = os.path.basename(src)
        rel_path = self._store_file(src)
        msg = self.db.send_message(
            self.active_chat["id"], self.user["id"], "",
            msg_type="file", meta=rel_path + "|name=" + name,
        )
        msg["sender_name"] = self.user["username"]
        bubble = MessageBubble(msg, True, self.active_chat["avatar_color"])
        bubble.file_download_requested.connect(self._download_file)
        self.history_container.insertWidget(self.history_container.count() - 1, bubble)
        self._scroll_to_bottom()
        self._load_chats()

    def _store_file(self, src):
        """Переносит файл в папку хранилища в зашифрованном виде."""
        stored_name = random_stored_name()
        stored_path = os.path.join(files_dir_for(self.db.path), stored_name)
        with open(src, "rb") as f:
            data = f.read()
        enc = self.db.crypto.encrypt_file(data) if self.db.crypto else data
        with open(stored_path, "wb") as f:
            f.write(enc)
        return stored_name

    def _download_file(self, stored_name, filename):
        """Скачивает зашифрованный файл в выбранную папку, расшифровывая его."""
        if self.db.crypto is None:
            return
        src = os.path.join(files_dir_for(self.db.path), stored_name)
        if not os.path.exists(src):
            QMessageBox.warning(self, "KeyChat", "Файл не найден на диске.")
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл", os.path.join(os.path.expanduser("~"), filename)
        )
        if not dest:
            return
        with open(src, "rb") as f:
            data = f.read()
        plain = self.db.crypto.decrypt_file(data)
        with open(dest, "wb") as f:
            f.write(plain)
        QMessageBox.information(self, "KeyChat", "Файл сохранён: " + dest)

    def _clear_history(self):
        if self.active_chat is None:
            return
        ret = QMessageBox.question(
            self,
            "Очистить историю",
            f"Удалить все сообщения с {self.active_chat['username']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.db.clear_history(self.active_chat["id"])
            self._reload_history()
            self._load_chats()

    def _add_friend(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Новый чат")
        dlg.setFixedSize(380, 200)
        dlg.setStyleSheet(QSS)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)
        title = QLabel("Новый чат")
        title.setObjectName("DialogTitle")
        lay.addWidget(title)
        sub = QLabel("Введите username собеседника для создания чата.")
        sub.setObjectName("BrandSub")
        sub.setWordWrap(True)
        lay.addWidget(sub)
        edit = QLineEdit()
        edit.setPlaceholderText("username")
        lay.addWidget(edit)
        btn_row = QHBoxLayout()
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(dlg.reject)
        ok = QPushButton("Создать")
        ok.setObjectName("Accent")
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        lay.addLayout(btn_row)

        def do_add():
            name = edit.text().strip()
            if not name:
                return
            user = self.db.add_friend(name)
            if user is None:
                QMessageBox.information(
                    self, "Не найден", f"Пользователь «{name}» не найден."
                )
                return
            dlg.accept()
            self.active_chat = {
                "id": self.db.get_or_create_chat(user["id"]),
                "peer_id": user["id"],
                "username": user["username"],
                "avatar_color": user["avatar_color"],
                "last_message": None,
                "last_seen": None,
            }
            self._load_chats()
            self._select_chat(self.active_chat)

        ok.clicked.connect(do_add)
        edit.returnPressed.connect(do_add)
        dlg.exec()

    def _open_settings(self):
        dlg = SettingsDialog(self.db, self.user)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.user = dlg.result_user()
            self.name_label.setText(self.user["username"])
            self.profile_avatar.set_name(self.user["username"])
            self.profile_avatar.set_color(self.user["avatar_color"])
            self._load_chats()
            if self.active_chat:
                self._reload_history()

    def _scroll_to_bottom(self):
        scrollbar = self.history_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())