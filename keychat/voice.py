import io
import wave

from PySide6.QtCore import QObject, QIODevice, QBuffer
from PySide6.QtMultimedia import (
    QAudioSource, QAudioSink, QAudioFormat, QMediaDevices, QAudio,
)

# Формат записи: моно, 16 кГц, 16 бит (поддерживается повсеместно).
SAMPLE_RATE = 16000
CHANNELS = 1


def _make_format():
    fmt = QAudioFormat()
    fmt.setSampleRate(SAMPLE_RATE)
    fmt.setChannelCount(CHANNELS)
    fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
    return fmt


class VoiceRecorder(QObject):
    """Запись голоса с микрофона в WAV (bytes) кнопкой «удерживай, чтобы говорить»."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = None
        self._buffer = bytearray()
        self.recording = False

    def start(self):
        if self.recording:
            return
        fmt = _make_format()
        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            raise RuntimeError("Нет микрофона")
        self._source = QAudioSource(device, fmt)
        self._buffer = bytearray()
        self._io = self._source.start()
        if self._io is not None:
            self._io.readyRead.connect(self._read_chunk)
        self._source.stateChanged.connect(self._on_state)
        self.recording = True

    def _read_chunk(self):
        data = self._io.readAll()
        if len(data) > 0:
            self._buffer.extend(data)

    def _on_state(self, state):
        if state == QAudio.State.StoppedState:
            self.recording = False

    def stop(self) -> bytes:
        """Останавливает запись и возвращает WAV-данные (или b'' если пусто)."""
        if self._source is not None:
            self._source.stop()
        self.recording = False
        pcm = bytes(self._buffer)
        if len(pcm) < 512:
            return b""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(CHANNELS)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(pcm)
        return buf.getvalue()


class VoicePlayer(QObject):
    """Воспроизведение WAV-голосового сообщения."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sink = None
        self._playing = False

    def play(self, wav_bytes: bytes):
        self.stop()
        fmt = _make_format()
        self._sink = QAudioSink(fmt)
        self._sink.stateChanged.connect(self._on_state)
        self._buf = QBuffer(self)
        self._buf.setData(wav_bytes)
        self._buf.open(QIODevice.OpenModeFlag.ReadOnly)
        self._sink.start(self._buf)
        self._playing = True

    def _on_state(self, state):
        if state in (QAudio.State.IdleState, QAudio.State.StoppedState):
            self._playing = False

    def stop(self):
        if self._sink is not None:
            self._sink.stop()
            self._sink = None
        self._playing = False

    @property
    def is_playing(self):
        return self._playing


def wav_duration_ms(wav_bytes: bytes) -> int:
    """Длительность WAV в миллисекундах (для подписи на пузыре)."""
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
            return int(frames * 1000 / rate) if rate else 0
    except Exception:
        return 0