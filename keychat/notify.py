import os
import sys

from PySide6.QtCore import QObject
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def notification_sound_path() -> str:
    """Путь к message.mp3 рядом с main.py (или пусто, если файла нет)."""
    p = os.path.join(_app_dir(), "message.mp3")
    return p if os.path.exists(p) else ""


class NotificationPlayer(QObject):
    """Проигрывает message.mp3 при получении нового сообщения."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = None
        self._output = None

    def play_received(self):
        path = notification_sound_path()
        if not path:
            return
        # Переиспользуем плеер, чтобы не плодить экземпляры.
        if self._player is None:
            from PySide6.QtCore import QUrl
            self._output = QAudioOutput(self)
            self._player = QMediaPlayer(self)
            self._player.setAudioOutput(self._output)
        self._player.setSource(QUrl.fromLocalFile(path))
        self._output.setVolume(0.8)
        self._player.play()