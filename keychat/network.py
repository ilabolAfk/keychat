import json

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtWebSockets import QWebSocket

# Узел-ретранслятор туннеля. Заполняется адресом ngrok/локального relay.
# Пример: ws://xxxx.ngrok.io  (для http-туннеля ngrok ставим ws://)
RELAY_URL = "ws://127.0.0.1:8765"


class NetClient(QObject):
    """WebSocket-клиент к relay-узлу: онлайн, доставка сообщений/файлов и звонков.

    Поток данных идёт через узел (relay) — это «прокси без проброса портов».
    Содержимое шифруется на клиентах (Fernet), узел видит только маршрут.
    """

    # сигналы в UI
    connected = Signal()
    disconnected = Signal()
    online_changed = Signal(list)          # list of user_ids
    message_received = Signal(dict, str)   # payload, from_user
    call_received = Signal(dict, str)      # payload, from_user
    call_answer_received = Signal(dict, str)
    audio_received = Signal(str, str)      # base64 chunk, from_user

    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = str(user_id)
        self.socket = QWebSocket()
        self.socket.connected.connect(self._on_connected)
        self.socket.disconnected.connect(self.disconnected)
        self.socket.textMessageReceived.connect(self._on_text)
        self.socket.errorOccurred.connect(lambda _e: None)
        self._connected = False

    # ---------- lifecycle ----------
    def connect_to_relay(self, url=RELAY_URL):
        self.socket.open(QUrl(url))

    def _on_connected(self):
        self._connected = True
        self.socket.sendTextMessage(
            json.dumps({"type": "register", "user_id": self.user_id})
        )
        self.connected.emit()

    def close(self):
        self.socket.close()

    # ---------- работа с каналом ----------
    def _send_text(self, obj):
        if self.socket.isValid():
            self.socket.sendTextMessage(json.dumps(obj))

    def send_chat(self, to_user, payload):
        self._send_text({"type": "chat", "to": str(to_user), "payload": payload})

    def send_file(self, to_user, payload):
        self._send_text({"type": "chat", "to": str(to_user), "payload": payload})

    def send_call(self, to_user, payload):
        self._send_text({"type": "call", "to": str(to_user), "payload": payload})

    def send_call_answer(self, to_user, payload):
        self._send_text({"type": "call_answer", "to": str(to_user), "payload": payload})

    def send_audio(self, to_user, base64_chunk):
        self._send_text({"type": "audio", "to": str(to_user), "payload": base64_chunk})

    # ---------- приём ----------
    def _on_text(self, text):
        try:
            msg = json.loads(text)
        except json.JSONDecodeError:
            return
        mtype = msg.get("type")
        if mtype == "online":
            self.online_changed.emit(msg.get("ids", []))
        elif mtype == "chat":
            self.message_received.emit(msg.get("payload") or {}, msg.get("from") or "")
        elif mtype == "call":
            self.call_received.emit(msg.get("payload") or {}, msg.get("from") or "")
        elif mtype == "call_answer":
            self.call_answer_received.emit(msg.get("payload") or {}, msg.get("from") or "")
        elif mtype == "audio":
            self.audio_received.emit(msg.get("payload") or "", msg.get("from") or "")