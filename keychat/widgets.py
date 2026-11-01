from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
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
    """Круглый аватар: показывает фото (PNG/JPG), иначе инициал на цветном фоне.

    Без рамки вокруг — только круг с изображением либо заливкой цветом.
    """

    def __init__(self, name, color=None, size=44, image_path=None, parent=None):
        super().__init__(parent)
        self._image_path = image_path or ""
        self._size = size
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.label)
        self._name = name
        self._color = color or PALETTE["orange"]
        self.set_name(name)

    def set_name(self, name):
        self._name = name
        if not self._image_path:
            self.label.setText(name.strip()[:1].upper() if name.strip() else "?")
        else:
            self.label.setText("")

    def set_color(self, color):
        self._color = color
        self._apply()

    def set_image(self, image_path):
        """Устанавливает фото аватара (путь или пустая строка — вернуть инициал)."""
        self._image_path = image_path or ""
        if self._image_path:
            self.label.setText("")
        self._apply()

    def image_path(self):
        return self._image_path

    def set_size(self, size):
        self._size = size
        self.setFixedSize(size, size)
        self._apply()

    def _apply(self):
        size = self._size
        radius = size // 2
        self.setFixedSize(size, size)
        if self._image_path:
            pm = QPixmap(self._image_path)
            if not pm.isNull():
                pm = pm.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                # кроп до квадрата по центру
                pm = pm.copy((pm.width() - size) // 2, (pm.height() - size) // 2, size, size)
                self.label.setPixmap(pm)
                self.setStyleSheet(
                    f"border-radius: {radius}px; background: transparent;"
                )
                return
        # без фото — цветной круг с инициалом
        self.label.setText(self._name.strip()[:1].upper() if self._name.strip() else "?")
        self.label.setStyleSheet(
            f"font-size: {max(12, int(size * 0.42))}px;"
            f"font-weight: 700; color: {text_color_for_hex(self._color)};"
            "background: transparent;"
        )
        self.setStyleSheet(
            f"border-radius: {radius}px; background-color: {self._color};"
        )