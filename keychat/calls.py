from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

import qtawesome as qta

from .theme import PALETTE, current_qss, DEFAULT_ACCENT
from .widgets import Avatar


class CallDialog(QDialog):
    """Каркас звонка (заглушка): показывает инициатора, таймер и кнопку завершения.

    Реальная передача голоса/видео — отдельная подсистема (WebRTC/сеть);
    здесь зафиксирован UI-контракт: initiator, peer, state.
    """

    state = "calling"  # calling | active | ended

    def __init__(self, peer_name, is_outgoing=True, parent=None):
        super().__init__(parent)
        self.peer_name = peer_name
        self.is_outgoing = is_outgoing
        self.seconds = 0
        self.setWindowTitle("Звонок")
        self.setFixedSize(320, 420)
        self.setStyleSheet(current_qss())
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        # Имитация: через 1.2 с «соединяемся» и запускаем таймер.
        if is_outgoing:
            self.timer_label.setText("Ожидание ответа…")
        else:
            self.timer_label.setText("Входящий вызов…")
        QTimer.singleShot(1200, self._answer)

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

        self.end_btn = QPushButton()
        self.end_btn.setObjectName("Danger")
        self.end_btn.setIcon(qta.icon("fa5s.phone-slash", color=PALETTE["danger"]))
        self.end_btn.setIconSize(QSize(22, 22))
        self.end_btn.setText("  Завершить")
        self.end_btn.setFixedSize(180, 48)
        self.end_btn.clicked.connect(self.hangup)
        btn_center = QHBoxLayout()
        btn_center.addStretch(1)
        btn_center.addWidget(self.end_btn)
        btn_center.addStretch(1)
        lay.addLayout(btn_center)

    def _answer(self):
        self.state = "active"
        self.state_label.setText("Соединение установлено")
        self.timer_label.setText("00:00")
        self._timer.start(1000)

    def _tick(self):
        self.seconds += 1
        m, s = divmod(self.seconds, 60)
        self.timer_label.setText(f"{m:02d}:{s:02d}")

    def hangup(self):
        self.state = "ended"
        self._timer.stop()
        self.state_label.setText("Звонок завершён")
        QTimer.singleShot(800, self.accept)