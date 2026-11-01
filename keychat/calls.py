from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

import qtawesome as qta

from .theme import PALETTE, current_qss
from .widgets import Avatar


class CallDialog(QDialog):
    """Окно звонка: исходящий/входящий, приём/отклонение, таймер.

    Управляется из главного окна; голос идёт отдельной подсистемой.
    """

    accepted_call = Signal()
    rejected_call = Signal()
    hangup_clicked = Signal()

    state = "calling"  # calling | active | ended

    def __init__(self, peer_name, is_outgoing=True, parent=None):
        super().__init__(parent)
        self.peer_name = peer_name
        self.is_outgoing = is_outgoing
        self.seconds = 0
        self.state = "calling"
        self.setWindowTitle("Звонок")
        self.setFixedSize(320, 460)
        self.setStyleSheet(current_qss())
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        if is_outgoing:
            self.timer_label.setText("Ожидание ответа…")
        else:
            self.timer_label.setText("Входящий вызов…")

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.phone-alt" if self.is_outgoing else "fa5s.phone-square-alt", color=PALETTE["orange"]).pixmap(40, 40))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon)

        av = Avatar(self.peer_name, PALETTE["orange"], size=96)
        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(av)
        center.addStretch(1)
        lay.addLayout(center)

        name = QLabel(self.peer_name)
        name.setObjectName("BrandTitle")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(name)

        self.timer_label = QLabel("")
        self.timer_label.setObjectName("BrandSub")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.timer_label)

        self.state_label = QLabel("")
        self.state_label.setObjectName("BrandSub")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.state_label)

        lay.addStretch(1)

        if self.is_outgoing:
            # Только завершение
            self.end_btn = self._make_end_btn("Завершить")
            btn_center = QHBoxLayout()
            btn_center.addStretch(1)
            btn_center.addWidget(self.end_btn)
            btn_center.addStretch(1)
            lay.addLayout(btn_center)
        else:
            # Принять / Отклонить
            accept_btn = QPushButton()
            accept_btn.setObjectName("Accent")
            accept_btn.setIcon(qta.icon("fa5s.phone", color=PALETTE["text_on_orange"]))
            accept_btn.setIconSize(QSize(20, 20))
            accept_btn.setText("  Принять")
            accept_btn.setFixedSize(150, 46)
            accept_btn.clicked.connect(self._on_accept)

            reject_btn = self._make_end_btn("Отклонить")
            reject_btn.setFixedWidth(150)
            btn_row = QHBoxLayout()
            btn_row.addStretch(1)
            btn_row.addWidget(reject_btn)
            btn_row.addWidget(accept_btn)
            btn_row.addStretch(1)
            lay.addLayout(btn_row)
            self.end_btn = reject_btn

    def _make_end_btn(self, text):
        btn = QPushButton()
        btn.setObjectName("Danger")
        btn.setIcon(qta.icon("fa5s.phone-slash", color=PALETTE["danger"]))
        btn.setIconSize(QSize(20, 20))
        btn.setText("  " + text)
        btn.setFixedSize(180, 46)
        btn.clicked.connect(self._on_hangup_or_reject)
        return btn

    def _on_accept(self):
        self.state = "active"
        self.state_label.setText("Соединение установлено")
        self.timer_label.setText("00:00")
        self._timer.start(1000)
        self.accepted_call.emit()

    def _on_hangup_or_reject(self):
        if self.state == "calling":
            self.rejected_call.emit()
        else:
            self.hangup_clicked.emit()
        self._finish()

    def _tick(self):
        self.seconds += 1
        m, s = divmod(self.seconds, 60)
        self.timer_label.setText(f"{m:02d}:{s:02d}")

    def show_hangup(self):
        """После принятия меняем UI на завершение (для входящих кнопок не нужно)."""
        pass

    def _finish(self):
        self.state = "ended"
        self._timer.stop()
        self.state_label.setText("Звонок завершён")
        QTimer.singleShot(600, self.accept)

    def complete_remote_hangup(self):
        """Вызывается при завершении со стороны собеседника."""
        self.state = "ended"
        self._timer.stop()
        self.state_label.setText("Собеседник завершил звонок")
        QTimer.singleShot(800, self.accept)