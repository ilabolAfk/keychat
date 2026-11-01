#!/usr/bin/env python3
"""
KeyChat relay — центральный узел-ретранслятор (WebSocket hub).

Роль: бесплатный туннель без проброса портов. Оба клиента подключаются
к этому узлу, а он маршрутизирует сообщения, файлы, звонки и голос
между ними по `user_id`. Сам узел НЕ хранит содержимое — только
перенаправляет (relay). Шифрование end-to-end остаётся на клиентах.

Запуск:
    pip install websockets
    python relay.py              # слушает порт 8765
    # затем пробросить наружу, например:
    ngrok http 8765    => для ws:  ws://<ngrok-host>

Протокол (JSON-текст или бинарный релей):
  {"type":"register","user_id":"<id>"}          — клиент сообщает свой id
  {"type":"online_updates", ...}                — кому онлайн
  {"type":"chat","to":"<id>","payload":{...}}   — доставка сообщения/файла/стикера
  {"type":"call","to":"<id>","payload":{...}}   — сигнал звонка
  {"type":"relay","to":"<id>","data":<base64 или бинарь>}  — голос/поток
  Бинарные фреймы: 1 байт длина id, id, затем данные.
"""

import asyncio
import json
import logging
import os

from websockets.connection import State

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("keychat-relay")

# user_id -> websocket
clients: dict[str, object] = {}


async def handler(ws, path=None):
    user_id = None
    try:
        async for raw in ws:
            if not isinstance(raw, (str, bytes)):
                continue
            if isinstance(raw, str):
                user_id = await handle_text(ws, raw, user_id)
            else:
                # бинарный релей звука/файлов: [1b len][id][data]
                if len(raw) < 3:
                    continue
                n = raw[0]
                target = raw[1:1 + n].decode("utf-8")
                payload = raw[1 + n:]
                if not user_id:
                    continue
                await route(target, b"__relay__", user_id, {"bin": payload})
    except Exception as e:
        log.warning("disconnect %s: %s", user_id, e)
    finally:
        if user_id and clients.get(user_id) is ws:
            del clients[user_id]
            log.info("offline: %s", user_id)
            await broadcast_online()


async def handle_text(ws, raw, user_id):
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        return user_id
    mtype = msg.get("type")
    if mtype == "register":
        user_id = str(msg.get("user_id", "")).strip()
        if not user_id:
            await ws.send(json.dumps({"type": "error", "code": "bad_register"}))
            return None
        # старый сокет того же id отключим
        for k, v in list(clients.items()):
            if k == user_id and v is not ws and v.state is not State.CLOSED:
                await v.close()
        clients[user_id] = ws
        log.info("online: %s", user_id)
        await ws.send(json.dumps({"type": "registered", "user_id": user_id}))
        await broadcast_online()
        return user_id
    if user_id is None:
        return None
    to = msg.get("to")
    if mtype == "chat":
        await route(to, "chat", user_id, msg.get("payload"))
    elif mtype == "call":
        await route(to, "call", user_id, msg.get("payload"))
    elif mtype == "call_answer":
        await route(to, "call_answer", user_id, msg.get("payload"))
    elif mtype == "audio":
        # голос поверх канала: пересылаем на указанного получателя
        await route_audio(to, user_id, msg.get("payload"))
    elif mtype == "typing":
        await route(to, "typing", user_id, None)
    return user_id


async def route(target, kind, sender, payload):
    sock = clients.get(target)
    if sock is None or sock.state is State.CLOSED:
        return  # собеседник офлайн — просто отбрасываем (клиент увидит это)
    try:
        await sock.send(json.dumps({"type": kind, "from": sender, "payload": payload}))
    except Exception as e:
        log.warning("route fail to %s: %s", target, e)


async def route_audio(target, sender, payload):
    """Голосовой фрейм от активного звонка -> получателю."""
    sock = clients.get(str(target))
    if sock is None or sock.state is State.CLOSED:
        return
    try:
        await sock.send(json.dumps({"type": "audio", "from": sender, "payload": payload}))
    except Exception as e:
        log.warning("audio route fail to %s: %s", target, e)


async def broadcast_online():
    online = list(clients.keys())
    for ws in list(clients.values()):
        try:
            await ws.send(json.dumps({"type": "online", "ids": online}))
        except Exception:
            pass


async def _serve(port):
    import websockets
    log.info("KeyChat relay listening on ws://0.0.0.0:%d", port)
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()  # держим сервер живым


def main():
    port = int(os.environ.get("KEYCHAT_RELAY_PORT", "8765"))
    asyncio.run(_serve(port))


if __name__ == "__main__":
    main()