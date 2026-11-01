import os
import sys

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QToolButton, QScrollArea, QVBoxLayout,
)

# Папка со стикерами ищется рядом со запускаемым файлом (exe или корнем),
# а не хардкодится.
def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


STICKERS_DIR = os.path.join(_app_dir(), "stickers")


def find_stickers():
    """Возвращает список путей к PNG-стикерам из папки рядом с проектом."""
    d = STICKERS_DIR
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if name.lower().endswith(".png"):
            out.append(os.path.join(d, name))
    return out


def _preview_path(sticker_path, cache_dir):
    """Заранее сгенерированный превью-файл стикера (никогда не трогает оригинал)."""
    os.makedirs(cache_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(sticker_path))[0]
    prev = os.path.join(cache_dir, base + "_preview.png")
    fresh = os.path.exists(prev) and os.path.getmtime(prev) >= os.path.getmtime(sticker_path)
    if fresh:
        return prev
    pm = QPixmap(sticker_path)
    if pm.isNull():
        return sticker_path
    scaled = pm.scaled(
        96, 96,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return prev if scaled.save(prev, "PNG") else sticker_path


class StickerPicker(QWidget):
    """Панель выбора стикеров: сетка превью, клик по стикеру = emit(path)."""

    sticker_selected = Signal(str)

    def __init__(self, cache_dir, parent=None):
        super().__init__(parent)
        self._cache_dir = cache_dir
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(6)
        self.stickers = find_stickers()
        if not self.stickers:
            hint = QToolButton()
            hint.setText("Стикеры не найдены\n(папка /stickers пуста)")
            hint.setEnabled(False)
            grid.addWidget(hint, 0, 0)
        else:
            cols = 4
            for i, path in enumerate(self.stickers):
                btn = QToolButton()
                btn.setStyleSheet(
                    "QToolButton { background: transparent; border: none; border-radius: 8px; }"
                    "QToolButton:hover { background: rgba(255,122,26,0.15); }"
                )
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setToolTip(os.path.basename(path))
                btn.clicked.connect(lambda _=False, p=path: self.sticker_selected.emit(p))
                btn.setIcon(QPixmap(_preview_path(path, self._cache_dir)))
                btn.setIconSize(QSize(96, 96))
                grid.addWidget(btn, i // cols, i % cols)
        scroll.setWidget(grid_widget)
        lay.addWidget(scroll)