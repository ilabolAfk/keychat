from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from .theme import PALETTE


def text_color_for_hex(hex_color):
    lum = (
        int(hex_color[1:3], 16) * 299
        + int(hex_color[3:5], 16) * 587
        + int(hex_color[5:7], 16) * 114
    ) / 1000
    return "#1A0F00" if lum > 150 else "#FFFFFF"


class Avatar(QFrame):
    """Круглый аватар с инициалами на оранжевой палитре."""

    def __init__(self, name, color=None, size=44, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.label)
        self._name = name
        self._color = color or PALETTE["orange"]
        self.set_size(size)
        self.set_name(name)

    def set_name(self, name):
        self._name = name
        self.label.setText(name.strip()[:1].upper() if name.strip() else "?")

    def set_size(self, size):
        self.setFixedSize(size, size)
        font_size = max(12, int(size * 0.42))
        self.label.setStyleSheet(
            f"font-size: {font_size}px; font-weight: 700; background: transparent;"
        )
        self._apply()

    def set_color(self, color):
        self._color = color
        self._apply()

    def _apply(self):
        self.setStyleSheet(
            f"border-radius: {self.width() // 2}px;"
            f"border: 2px solid {PALETTE['orange_light']};"
            f"background-color: {self._color};"
        )
        self.label.setStyleSheet(
            f"font-size: {max(12, int(self.width() * 0.42))}px;"
            f"font-weight: 700; color: {text_color_for_hex(self._color)};"
            "background: transparent;"
        )